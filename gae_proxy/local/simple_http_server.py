import os
import urlparse
import datetime
import threading
import mimetools
import socket
import errno
import xlog
import sys
import select


class HttpServerHandler():
    default_request_version = "HTTP/1.1"
    MessageClass = mimetools.Message
    rbufsize = -1
    wbufsize = 0

    def __init__(self, sock, client, args):
        self.connection = sock
        self.rfile = socket._fileobject(self.connection, "rb", self.rbufsize)
        self.wfile = socket._fileobject(self.connection, "wb", self.wbufsize)
        self.client_address = client
        self.args = args
        self.setup()

    def setup(self):
        pass

    def handle(self):
        #xlog.info('Connected from %r', self.client_address)
        while True:
            try:
                self.close_connection = 1
                self.handle_one_request()
            except Exception as e:
                xlog.warn("handle err:%r close", e)
                self.close_connection = 1

            if self.close_connection:
                break
        self.connection.close()
        #xlog.debug("closed from %s:%d", self.client_address[0], self.client_address[1])

    def send_error(self, code, message=None):
        self.wfile.write('HTTP/1.1 %d\r\n' % code)
        self.wfile.write('Connection: close\r\n\r\n')
        if message:
            self.wfile.write(message)

    def parse_request(self):
        self.command = None  # set in case of error on the first line
        self.request_version = version = self.default_request_version

        requestline = self.raw_requestline
        requestline = requestline.rstrip('\r\n')
        self.requestline = requestline
        words = requestline.split()
        if len(words) == 3:
            command, path, version = words
            if version[:5] != 'HTTP/':
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            try:
                base_version_number = version.split('/', 1)[1]
                version_number = base_version_number.split(".")
                # RFC 2145 section 3.1 says there can be only one "." and
                #   - major and minor numbers MUST be treated as
                #      separate integers;
                #   - HTTP/2.4 is a lower version than HTTP/2.13, which in
                #      turn is lower than HTTP/12.3;
                #   - Leading zeros MUST be ignored by recipients.
                if len(version_number) != 2:
                    raise ValueError
                version_number = int(version_number[0]), int(version_number[1])
            except (ValueError, IndexError):
                self.send_error(400, "Bad request version (%r)" % version)
                return False
            if version_number >= (1, 1):
                self.close_connection = 0
            if version_number >= (2, 0):
                self.send_error(505,
                          "Invalid HTTP Version (%s)" % base_version_number)
                return False
        elif len(words) == 2:
            command, path = words
            self.close_connection = 1
            if command != 'GET':
                self.send_error(400,
                                "Bad HTTP/0.9 request type (%r)" % command)
                return False
        elif not words:
            return False
        else:
            self.send_error(400, "Bad request syntax (%r)" % requestline)
            return False
        self.command, self.path, self.request_version = command, path, version

        # Examine the headers and look for a Connection directive
        self.headers = self.MessageClass(self.rfile, 0)

        conntype = self.headers.get('Connection', "")
        if conntype.lower() == 'close':
            self.close_connection = 1
        elif conntype.lower() == 'keep-alive':
            self.close_connection = 0
        return True

    def handle_one_request(self):
        try:
            try:
                self.raw_requestline = self.rfile.readline(65537)
            except Exception as e:
                #xlog.warn("simple server handle except %r", e)
                return

            if len(self.raw_requestline) > 65536:
                xlog.warn("recv command line too large")
                return
            if not self.raw_requestline:
                #xlog.warn("closed")
                return

            self.parse_request()

            if self.command == "GET":
                self.do_GET()
            elif self.command == "POST":
                self.do_POST()
            elif self.command == "CONNECT":
                self.do_CONNECT()
            elif self.command == "HEAD":
                self.do_HEAD()
            elif self.command == "DELETE":
                self.do_DELETE()
            elif self.command == "OPTIONS":
                self.do_OPTIONS()
            elif self.command == "PUT":
                self.do_PUT()
            else:
                xlog.warn("unhandler cmd:%s", self.command)
                return

            self.wfile.flush() #actually send the response if not already done.
            self.close_connection = 0
        except socket.error as e:
            xlog.warn("socket error:%r", e)
        except IOError as e:
            if e.errno == errno.EPIPE:
                xlog.warn("PIPE error:%r", e)
            else:
                xlog.warn("IOError:%r", e)
        #except OpenSSL.SSL.SysCallError as e:
        #    xlog.warn("socket error:%r", e)
        except Exception as e:
            xlog.exception("handler:%r", e)

    def send_response_data(self, mimetype, data, heads="", status=200):
        self.wfile.write(('HTTP/1.1 %d\r\nContent-Type: %s\r\nContent-Length: %s\r\n%s\r\n' % (status, mimetype, len(data), heads)).encode())
        self.wfile.write(data)

    def do_GET(self):
        pass

    def do_PUT(self):
        pass

    def do_POST(self):
        pass

    def do_DELETE(self):
        pass

    def do_OPTIONS(self):
        pass

    def do_HEAD(self):
        pass

    def do_CONNECT(self):
        pass

class HTTPServer():
    def __init__(self, address, handler, args=()):
        self.running = True
        self.server_address = address
        self.handler = handler
        self.args = args
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind(self.server_address)
        self.socket.listen(200)
        xlog.info("server %s:%d started.", address[0], address[1])

    def serve_forever(self):
        fdset = [self.socket, ]
        while self.running:
            r, w, e = select.select(fdset, [], [], 1)
            if self.socket in r:
                (sock, address) = self.socket.accept()
                self.process_connect(sock, address)

    def process_connect(self, sock, address):
        #xlog.debug("connect from %s:%d", address[0], address[1])
        client_obj = self.handler(sock, address, self.args)
        client_thread = threading.Thread(target=client_obj.handle)
        client_thread.start()

    def shutdown(self):
        self.running = False

    def server_close(self):
        self.socket.close()

class test_http_server(HttpServerHandler):

    def __init__(self, sock, client, args):
        self.data_path = args
        HttpServerHandler.__init__(self, sock, client, args)

    def do_GET(self):
        url_path = urlparse.urlparse(self.path).path
        if url_path == '/':
            data = "OK\r\n"
            self.wfile.write('HTTP/1.1 200\r\nContent-Length: %d\r\n\r\n%s' %(len(data), data) )
        elif url_path == '/null':
            mimetype = "application/x-binary"
            file_size = 1024 * 1024 * 1024
            self.wfile.write('HTTP/1.1 200\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (mimetype, file_size))
            start = 0
            data = ''.join(chr(ord('a')+i) for i in xrange(65535))
            while start < file_size:
                left = file_size - start
                send_batch = min(left, 65535)
                self.wfile.write(data[:send_batch])
                start += send_batch
        else:
            target = os.path.abspath(os.path.join(self.data_path, url_path[1:]))
            if os.path.isfile(target):
                self.send_file(target, "application/x-binary")
            else:
                self.wfile.write('HTTP/1.1 404\r\nContent-Length: 0\r\n\r\n' )

    def send_file(self, filename, mimetype):
        file_size = os.path.getsize(filename)
        try:
            tme = (datetime.datetime.today()+datetime.timedelta(minutes=330)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            self.wfile.write(('HTTP/1.1 200\r\nAccess-Control-Allow-Origin: *\r\nCache-Control:public, max-age=31536000\r\nExpires: %s\r\nContent-Type: %s\r\nContent-Length: %s\r\n\r\n' % (tme, mimetype, file_size)).encode())


            with open(filename, 'rb') as fp:
                while True:
                    data = fp.read(65535)
                    if not data:
                        break
                    self.wfile.write(data)
        except:
            #self.wfile.write(b'HTTP/1.1 404\r\nContent-Type: text/plain\r\nConnection: close\r\n\r\n404 Open file fail')
            xlog.warn("download broken")

def main(data_path="."):
    httpd = HTTPServer(('', 8880), test_http_server, data_path)
    httpd.serve_forever()


if __name__ == "__main__":
    if len(sys.argv) > 2:
        data_path = sys.argv[1]
    else:
        data_path = "."
    main(data_path=data_path)