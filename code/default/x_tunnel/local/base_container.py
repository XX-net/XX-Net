import os
import sys
import threading
import time
import socket
import xstruct as struct
from datetime import datetime

import selectors2 as selectors

import utils

from xlog import getLogger
xlog = getLogger("x_tunnel")


class WriteBuffer(object):
    def __init__(self, s=None):
        if isinstance(s, bytes):
            self.string_len = len(s)
            self.buffer_list = [s]
        elif s is None:
            self.reset()
        else:
            raise Exception("WriteBuffer init not bytes or StringBuffer")

    def reset(self):
        self.buffer_list = []
        self.string_len = 0

    def __len__(self):
        return self.string_len

    def __add__(self, other):
        self.append(other)
        return self

    def insert(self, s):
        if isinstance(s, WriteBuffer):
            self.buffer_list = s.buffer_list + self.buffer_list
            self.string_len += s.string_len
        elif isinstance(s, bytes):
            self.buffer_list.insert(0, s)
            self.string_len += len(s)
        else:
            raise Exception("WriteBuffer append not string or StringBuffer")

    def append(self, s):
        if isinstance(s, WriteBuffer):
            self.buffer_list.extend(s.buffer_list)
            self.string_len += s.string_len
        elif isinstance(s, bytes):
            self.buffer_list.append(s)
            self.string_len += len(s)
        else:
            raise Exception("WriteBuffer append not bytes or StringBuffer")

    def to_bytes(self):
        return b"".join(self.buffer_list)

    def __bytes__(self):
        return self.to_bytes()

    def __str__(self):
        return self.to_bytes().decode("ascii")


class ReadBuffer(object):
    def __init__(self, buf, begin=0, size=None):
        buf_len = len(buf)
        if size is None:
            if begin > buf_len:
                raise Exception("ReadBuffer buf_len:%d, start:%d" % (buf_len, begin))
            size = buf_len - begin
        elif begin + size > buf_len:
            raise Exception("ReadBuffer buf_len:%d, start:%d len:%d" % (buf_len, begin, size))

        self.size = size
        self.buf = memoryview(buf)
        self.begin = begin

    def __len__(self):
        return self.size

    def get(self, size=None):
        if size is None:
            size = self.size
        elif size > self.size:
            raise Exception("ReadBuffer get %d but left %d" % (size, self.size))

        data = self.buf[self.begin:self.begin + size]
        self.begin += size
        self.size -= size
        return data

    def get_buf(self, size=None):
        if size is None:
            size = self.size
        elif size > self.size:
            raise Exception("ReadBuffer get %d but left %d" % (size, self.size))

        buf = ReadBuffer(self.buf, self.begin, size)

        self.begin += size
        self.size -= size
        return buf

    def __bytes__(self):
        return bytes(self.buf[self.begin:self.begin+self.size])

    def __str__(self):
        return (bytes(self.buf[self.begin:self.begin+self.size])).decode("ascii")


class AckPool():
    def __init__(self):
        self.mutex = threading.Lock()
        self.reset()

    def reset(self):
        # xlog.info("Ack_pool reset")
        with self.mutex:
            self.ack_buffer = WriteBuffer()

        # xlog.info("Ack_pool reset finished")

    def put(self, data):
        # xlog.debug("Ack_pool put len:%d", len(data))
        with self.mutex:
            self.ack_buffer.append(data)

    def get(self):
        with self.mutex:
            data = self.ack_buffer
            self.ack_buffer = WriteBuffer()

        # xlog.debug("Ack_pool get len:%d", len(data))
        return data

    def status(self):
        out_string = "Ack_pool:len %d\r\n" % len(self.ack_buffer)
        return out_string


class WaitQueue():
    def __init__(self):
        self.lock = threading.Lock()
        self.waiters = []
        # (end_time, Lock())

        self.running = True

    def stop(self):
        self.running = False
        xlog.info("WaitQueue stop")
        for end_time, lock in self.waiters:
            lock.release()
        self.waiters = []
        xlog.info("WaitQueue stop finished")

    def notify(self):
        # xlog.debug("notify")
        if len(self.waiters) == 0:
            # xlog.debug("notify none.")
            return

        try:
            end_time, lock = self.waiters.pop(0)
            lock.release()
        except:
            pass

    def wait(self, wait_order):
        with self.lock:
            lock = threading.Lock()
            lock.acquire()

            if len(self.waiters) == 0:
                self.waiters.append((wait_order, lock))
            else:
                is_max = True
                for i in range(0, len(self.waiters)):
                    try:
                        i_wait_order, ilock = self.waiters[i]
                        if i_wait_order > wait_order:
                            is_max = False
                            break
                    except Exception as e:
                        if i >= len(self.waiters):
                            break
                        xlog.warn("get %d from size:%d fail.", i, len(self.waiters))
                        continue

                if is_max:
                    self.waiters.append((wait_order, lock))
                else:
                    self.waiters.insert(i, (wait_order, lock))

        lock.acquire()

    def status(self):
        out_string = "waiters[%d]:\n" % len(self.waiters)
        for i in range(0, len(self.waiters)):
            end_time, lock = self.waiters[i]
            out_string += "%d\r\n" % (end_time)

        return out_string


class SendBuffer():
    def __init__(self, max_payload):
        self.mutex = threading.Lock()
        self.max_payload = max_payload
        self.reset()

    def reset(self):
        xlog.debug("SendBuffer reset")
        self.pool_size = 0
        self.last_put_time = time.time()
        with self.mutex:
            self.head_sn = 1
            self.tail_sn = 1
            self.block_list = {}
            self.last_block = WriteBuffer()

    def put(self, data):
        dlen = len(data)
        # xlog.debug("SendBuffer len:%d", dlen)
        if dlen == 0:
            xlog.warn("SendBuffer put 0")
            return False

        # xlog.debug("SendBuffer put len:%d", len(data))
        self.last_put_time = time.time()
        with self.mutex:
            self.pool_size += dlen
            self.last_block.append(data)

            if len(self.last_block) > self.max_payload:
                self.block_list[self.head_sn] = self.last_block
                self.last_block = WriteBuffer()
                self.head_sn += 1
        return True

    def get(self):
        with self.mutex:
            if self.tail_sn < self.head_sn:
                data = self.block_list[self.tail_sn]
                del self.block_list[self.tail_sn]
                sn = self.tail_sn
                self.tail_sn += 1

                self.pool_size -= len(data)
                # xlog.debug("send_pool get, sn:%r len:%d ", sn, len(data))
                return data, sn

            if len(self.last_block) > 0:
                data = self.last_block
                sn = self.tail_sn
                self.last_block = WriteBuffer()
                self.head_sn += 1
                self.tail_sn += 1

                self.pool_size -= len(data)
                # xlog.debug("send_pool get, sn:%r len:%d ", sn, len(data))
                return data, sn

        #xlog.debug("Get:%s", utils.str2hex(data))
        # xlog.debug("SendBuffer get wake after no data, tail:%d", self.tail_sn)
        return "", 0

    def status(self):
        out_string = "SendBuffer:\n"
        out_string += " size:%d\n" % self.pool_size
        out_string += " last_put_time:%f\n" % (time.time() - self.last_put_time)
        out_string += " head_sn:%d\n" % self.head_sn
        out_string += " tail_sn:%d\n" % self.tail_sn
        out_string += "block_list:[%d]\n" % len(self.block_list)
        for sn in sorted(self.block_list.keys()):
            data = self.block_list[sn]
            out_string += "[%d] len:%d\r\n" % (sn, len(data))

        return out_string


class BlockReceivePool():
    def __init__(self, process_callback, logger):
        self.lock = threading.Lock()
        self.process_callback = process_callback
        self.logger = logger
        self.reset()

    def reset(self):
        # xlog.info("recv_pool reset")
        self.next_sn = 1
        self.block_list = []
        self.timeout_sn_list = {}

    def put(self, sn, data):
        # xlog.debug("recv_pool put sn:%d len:%d", sn, len(data))
        self.lock.acquire()
        try:
            if sn in self.timeout_sn_list:
                del self.timeout_sn_list[sn]

            if sn < self.next_sn:
                # xlog.warn("recv_pool put timeout sn:%d", sn)
                return False
            elif sn > self.next_sn:
                # xlog.debug("recv_pool put disorder sn:%d", sn)
                if sn in self.block_list:
                    # xlog.warn("recv_pool put sn:%d exist", sn)
                    return False
                else:
                    self.block_list.append(sn)
                    self.process_callback(data)
                    return True
            else:
                # xlog.debug("recv_pool put sn:%d in order", sn)
                self.process_callback(data)
                self.next_sn += 1

                while self.next_sn in self.block_list:
                    # xlog.debug("recv_pool sn:%d processed", sn)
                    self.block_list.remove(self.next_sn)
                    self.next_sn += 1
                return True
        except Exception as e:
            raise Exception("recv_pool put sn:%d len:%d error:%r" % (sn, len(data), e))
        finally:
            self.lock.release()

    def mark_sn_timeout(self, sn, t, server_time):
        # xlog.warn("mark_sn_timeout down_sn:%d", sn)
        with self.lock:
            if sn not in self.timeout_sn_list:
                self.logger.warn("mark_sn_timeout sn:%d t:%f", sn, server_time - t)
                self.timeout_sn_list[sn] = {
                    "server_send_time": t,
                }
            elif t > self.timeout_sn_list[sn]["server_send_time"]:
                self.logger.warn("mark_sn_timeout renew sn:%d t:%f", sn, server_time - t)
                self.timeout_sn_list[sn]["server_send_time"] = t

    def get_timeout_list(self, server_time, timeout):
        sn_list = []
        with self.lock:
            for sn, info in self.timeout_sn_list.items():
                if server_time - info["server_send_time"] < timeout:
                    continue

                if server_time - info.get("retry_time", server_time) < timeout:
                    continue

                self.logger.warn("get_timeout_list sn:%d sent:%f retry:%f", sn, server_time - info["server_send_time"],
                                 server_time - info.get("retry_time", server_time))
                info["retry_time"] = server_time
                sn_list.append(sn)

        return sn_list

    def is_received(self, sn):
        if sn < self.next_sn:
            return True

        if sn in self.block_list:
            return True

        return False

    def status(self):
        out_string = "Block_receive_pool:\r\n"
        out_string += " next_sn:%d\r\n" % self.next_sn
        for sn in sorted(self.block_list):
            out_string += "[%d] \r\n" % (sn)

        return out_string


class ConnectionPipe(object):
    def __init__(self, session, xlog):
        self.session = session
        self.xlog = xlog
        self.running = True
        self.th = None
        self.select2 = selectors.DefaultSelector()
        self.sock_conn_map = {}
        self._lock = threading.RLock()

        if sys.platform == "win32":
            self.slow_wait = 0.05
        else:
            self.slow_wait = 3
            # self.slow_wait = 0.05

    def status(self):
        out_string = "ConnectionPipe:\r\n"
        out_string += " running: %s\r\n" % self.running
        out_string += " thread: %s\r\n" % self.th
        out_string += " conn: "
        for conn in self.sock_conn_map.values():
            out_string += "%d," % (conn.conn_id)
        out_string += "\r\n"

        return out_string

    def start(self):
        self.running = True
        self.sock_conn_map = {}

    def stop(self):
        self.running = False
        self.xlog.debug("ConnectionPipe stop")

    def _debug_log(self, fmt, *args, **kwargs):
        if not self.session.config.show_debug:
            return
        self.xlog.debug(fmt, *args, **kwargs)

    def add_sock_event(self, sock, conn, event):
        # this function can repeat without through an error.

        if not sock:
            return

        with self._lock:
            self._debug_log("add_sock_event conn:%d event:%s", conn.conn_id, event)
            try:
                self.select2.register_event(sock, event, conn)
            except Exception as e:
                self.xlog.warn("add_sock_event %s conn:%d e:%r", sock, conn.conn_id, e)
                self.close_sock(sock, str(e) + "_when_add_sock_event")
                return

            # if sys.platform == "win32" and (sock not in self.sock_conn_map or event == selectors.EVENT_WRITE):
            #     self.notice_select()

            self.sock_conn_map[sock] = conn

            if not self.th:
                self.th = threading.Thread(target=self.pipe_worker, name="x_tunnel_pipe_worker")
                self.th.start()
                self.xlog.debug("ConnectionPipe start")

    def remove_sock_event(self, sock, event):
        # this function can repeat without through an error.

        with self._lock:
            if sock not in self.sock_conn_map:
                return

            try:
                conn = self.sock_conn_map[sock]
                self._debug_log("remove_sock_event conn:%d event:%s", conn.conn_id, event)
                res = self.select2.unregister_event(sock, event)
                if not res:
                    # self.xlog.debug("remove_sock_event %s conn:%d event:%s removed all", sock, conn.conn_id, event)
                    del self.sock_conn_map[sock]
            except Exception as e:
                self.xlog.exception("remove_sock_event %s event:%s e:%r", sock, event, e)

    def remove_sock(self, sock):
        with self._lock:
            if sock not in self.sock_conn_map:
                return

            try:
                conn = self.sock_conn_map[sock]
                self._debug_log("remove_sock all events conn:%d", conn.conn_id)
                del self.sock_conn_map[sock]
                self.select2.unregister(sock)
            except Exception as e:
                # error will happen when sock closed
                self.xlog.warn("ConnectionPipe remove sock e:%r", e)

    def close_sock(self, sock, reason):
        if sock not in self.sock_conn_map:
            return

        try:
            conn = self.sock_conn_map[sock]
            # self.xlog.info("close conn:%d", conn.conn_id)
            self.remove_sock(sock)

            conn.transfer_peer_close(reason)
            conn.do_stop(reason=reason)
        except Exception as e:
            self.xlog.exception("close_sock %s e:%r", sock, e)

    def reset_all_connections(self):
        for sock, conn in dict(self.sock_conn_map).items():
            self.close_sock(sock, "reset_all")

        self.sock_conn_map = {}
        self.select2 = selectors.DefaultSelector()

    def notice_select(self):
        self.xlog.debug("notice select")

    def read_notify(self):
        self.xlog.debug("read_notify")

    def pipe_worker(self):
        timeout = 0.001
        while self.running:
            if not self.sock_conn_map:
                break

            try:
                try:
                    events = self.select2.select(timeout=timeout)
                    if not events:
                        # self.xlog.debug("%s session check_upload", random_id)
                        has_data = self.session.check_upload()
                        if has_data:
                            timeout = 0.01
                        else:
                            timeout = self.slow_wait

                        # self.xlog.debug("%s recv select timeout switch to %f", random_id, timeout)
                        continue
                    else:
                        # self.xlog.debug("%s recv select timeout switch to 0.001", random_id)
                        timeout = 0.001
                except Exception as e:
                    self.xlog.exception("Conn session:%s select except:%r", self.session.session_id, e)
                    if "Invalid argument" in str(e):
                        self.reset_all_connections()
                    time.sleep(1)
                    continue

                now = time.time()
                for key, event in events:
                    sock = key.fileobj
                    conn = key.data
                    if not conn:
                        self.xlog.debug("get notice")
                        self.read_notify()
                        continue

                    if event & selectors.EVENT_READ:
                        try:
                            data = sock.recv(65535)
                        except Exception as e:
                            self._debug_log("conn:%d recv e:%r", conn.conn_id, e)
                            data = ""

                        data_len = len(data)
                        if data_len == 0:
                            # self.xlog.debug("Conn conn:%d recv zero", conn.conn_id)
                            self.close_sock(sock, "receive")
                            continue
                        else:
                            conn.last_active = now
                            self._debug_log("Conn session:%s conn:%d local recv len:%d pos:%d",
                                            self.session.session_id, conn.conn_id, data_len, conn.received_position)

                            conn.transfer_received_data(data)
                    elif event & selectors.EVENT_WRITE:
                        conn.blocked = False
                        conn.process_cmd()
                    else:
                        self.xlog.debug("no event for conn:%d", conn.conn_id)
                        self.close_sock(sock, "no_event")

            except Exception as e:
                xlog.exception("recv_worker e:%r", e)

        for sock in dict(self.sock_conn_map):
            try:
                self.select2.unregister(sock)
            except Exception as e:
                xlog.warn("unregister %s e:%r", sock, e)
        self.sock_conn_map = {}
        self.xlog.debug("ConnectionPipe stop")
        self.th = None
        self.session.check_upload()


class Conn(object):
    def __init__(self, session, conn_id, sock, host, port, windows_size, windows_ack, is_client, xlog):
        # xlog.info("session:%s conn:%d host:%s port:%d", session.session_id, conn_id, host, port)
        self.host = host
        self.port = port
        self.session = session
        self.conn_id = conn_id
        self.sock = sock
        self.windows_size = windows_size
        self.windows_ack = windows_ack
        self.is_client = is_client

        self.connection_pipe = session.connection_pipe
        self.xlog = xlog

        self.cmd_queue = {}
        self.running = True
        self.blocked = False
        self.send_buffer = b""
        self.received_position = 0
        self.remote_acked_position = 0
        self.sended_position = 0
        self.sent_window_position = 0
        self.create_time = time.time()
        self.last_active = time.time()
        self._lock = threading.Lock()

        self.transferred_close_to_peer = False
        if sock:
            self.next_cmd_seq = 1
            self._fd = sock.fileno()
            # self.xlog.debug("conn:%d init fd:%d", conn_id, self._fd)
        else:
            self.next_cmd_seq = 0

        self.next_recv_seq = 1

    def start(self, block):
        if self.sock:
            self.connection_pipe.add_sock_event(self.sock, self, selectors.EVENT_READ)

    def status(self):
        out_string = "Conn[%d]: %s:%d\n" % (self.conn_id, self.host, self.port)
        out_string += " received_position:%d/ Ack:%d \n" % (self.received_position, self.remote_acked_position)
        out_string += " sended_position:%d/ win:%d\n" % (self.sended_position, self.sent_window_position)
        out_string += " next_cmd_seq:%d\n" % self.next_cmd_seq
        out_string += " next_recv_seq:%d\n" % self.next_recv_seq
        out_string += " running:%r\n" % self.running
        out_string += " blocked: %s\n" % self.blocked
        if self.send_buffer:
            out_string += " send_buffer: %d\n" % len(self.send_buffer)
        out_string += " transferred_close_to_peer:%r\n" % self.transferred_close_to_peer
        out_string += " sock:%r\n" % (self.sock is not None)
        out_string += " cmd_queue.len:%d\n" % len(self.cmd_queue)
        out_string += " create time: %s\n" % datetime.fromtimestamp(self.create_time).strftime('%Y-%m-%d %H:%M:%S.%f')
        out_string += " last active: %s\n" % datetime.fromtimestamp(self.last_active).strftime('%Y-%m-%d %H:%M:%S.%f')
        for seq in self.cmd_queue:
            out_string += "[%d]," % seq
        out_string += "\n"

        return out_string

    def stop(self, reason=""):
        threading.Thread(target=self.do_stop, args=(reason,),
                         name="do_stop_%s:%d" % (self.host, self.port)).start()

    def do_stop(self, reason="unknown"):
        self.xlog.debug("Conn session:%s %s:%d conn:%d fd:%d stop:%s", utils.to_str(self.session.session_id),
                        self.host, self.port, self.conn_id, self._fd, reason)
        self.running = False

        self.connection_pipe.remove_sock(self.sock)

        self.cmd_queue = {}

        if self.sock is not None:
            try:
                self.sock.close()
            except:
                pass
            self.sock = None

        # self.xlog.debug("Conn session:%s conn:%d stopped", self.session.session_id, self.conn_id)
        self.session.remove_conn(self.conn_id)

    def do_connect(self, host, port):
        # self.xlog.info("session_id:%s create_conn conn:%d %s:%d", self.session.session_id, self.conn_id, host, port)
        connect_timeout = 30
        sock = None
        start_time = time.time()
        ip = ""
        try:
            if ':' in host:
                # IPV6
                ip = host
            elif utils.check_ip_valid4(host):
                # IPV4
                ip = host
            else:
                # self.xlog.debug("getting ip of %s", host)
                ip = socket.gethostbyname(host)
                # self.xlog.debug("resolve %s to %s", host, ip)
            sock = socket.socket(socket.AF_INET if ':' not in ip else socket.AF_INET6)
            # set reuseaddr option to avoid 10048 socket error
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            # resize socket recv buffer ->256K to improve browser releated application performance
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 262144)
            # disable negal algorithm to send http request quickly.
            sock.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, True)
            # set a short timeout to trigger timeout retry more quickly.
            sock.settimeout(connect_timeout)

            sock.connect((ip, port))

            # record TCP connection time
            # conn_time = time.time() - start_time
            # self.xlog.debug("tcp conn %s %s time:%d", host, ip, conn_time * 1000)

            return sock, True
        except Exception as e:
            conn_time = int((time.time() - start_time) * 1000)
            self.xlog.debug("tcp conn host:%s %s:%d fail t:%d %r", host, ip, port, conn_time, e)
            if sock:
                sock.close()
            return e, False

    def put_cmd_data(self, data):
        if not self.running:
            return

        seq = struct.unpack("<I", data.get(4))[0]
        if seq < self.next_cmd_seq:
            self.xlog.warn("put_send_data %s conn:%d seq:%d next:%d",
                           self.session.session_id, self.conn_id,
                           seq, self.next_cmd_seq)
            return

        self._debug_log("conn:%d put data seq:%d len:%d", self.conn_id, seq, len(data))

        with self._lock:
            self.cmd_queue[seq] = data.get_buf()
            if seq == self.next_cmd_seq:
                if self.sock:
                    self.connection_pipe.add_sock_event(self.sock, self, selectors.EVENT_WRITE)
                else:
                    self.process_cmd()

    def get_cmd_data(self):
        if self.next_cmd_seq not in self.cmd_queue:
            self._debug_log("get_cmd_data conn:%d no data, next_cmd_seq:%d", self.conn_id, self.next_cmd_seq)
            return None

        payload = self.cmd_queue[self.next_cmd_seq]
        del self.cmd_queue[self.next_cmd_seq]
        # self.xlog.debug("Conn session:%s conn:%d get data sn:%d len:%d ",
        #                self.session.session_id, self.conn_id, self.next_cmd_seq, len(payload))
        self.next_cmd_seq += 1
        return payload

    def _debug_log(self, fmt, *args, **kwargs):
        if not self.session.config.show_debug:
            return
        self.xlog.debug(fmt, *args, **kwargs)

    def process_cmd(self):
        while self.running:
            if self.blocked:
                return

            if self.send_buffer:
                if not self.send_to_sock(self.send_buffer):
                    return

            with self._lock:
                data = self.get_cmd_data()
                if not data:
                    self._debug_log("conn:%d no data", self.conn_id)
                    self.connection_pipe.remove_sock_event(self.sock, selectors.EVENT_WRITE)
                    break

            self.last_active = time.time()
            cmd_id = struct.unpack("<B", data.get(1))[0]
            if cmd_id == 1:  # data
                self._debug_log("conn:%d download len:%d pos:%d", self.conn_id, len(data), self.sended_position)
                self.send_to_sock(data.get())

            elif cmd_id == 3:  # ack:
                position = struct.unpack("<Q", data.get(8))[0]
                self._debug_log("Conn session:%s conn:%d ACK:%d", self.session.session_id, self.conn_id, position)
                if position > self.remote_acked_position:
                    self.remote_acked_position = position

                    self.connection_pipe.add_sock_event(self.sock, self, selectors.EVENT_READ)

            elif cmd_id == 2:  # Closed
                dat = data.get()
                if isinstance(dat, memoryview):
                    dat = dat.tobytes()
                self.xlog.debug("Conn session:%s conn:%d Peer Close:%s", self.session.session_id, self.conn_id, dat)
                if self.is_client:
                    self.transfer_peer_close("finish")
                    if b"exceed the max connection" in dat:
                        self.session.reset()
                self.stop("peer close")

            elif cmd_id == 0:  # Create connect
                if self.port or len(self.host) or self.next_cmd_seq != 1 or self.sock:
                    raise Exception("put_send_data %s conn:%d Create but host:%s port:%d next seq:%d" % (
                        self.session.session_id, self.conn_id,
                        self.host, self.port, self.next_cmd_seq))

                self.sock_type = struct.unpack("<B", data.get(1))[0]
                host_len = struct.unpack("<H", data.get(2))[0]
                self.host = data.get(host_len)
                self.port = struct.unpack("<H", data.get(2))[0]

                sock, res = self.do_connect(self.host, self.port)
                if res is False:
                    self.xlog.debug("Conn session:%s conn:%d %s:%d Create fail", self.session.session_id, self.conn_id,
                               self.host, self.port)
                    self.transfer_peer_close("connect fail")
                else:
                    self.xlog.info("Conn session:%s conn:%d %s:%d", self.session.session_id, self.conn_id, self.host,
                              self.port)
                    self.sock = sock
                    self.connection_pipe.add_sock_event(self.sock, self, selectors.EVENT_READ)
            else:
                self.xlog.error("Conn session:%s conn:%d unknown cmd_id:%d",
                                self.session.session_id, self.conn_id, cmd_id)
                raise Exception("put_send_data unknown cmd_id:%d" % cmd_id)

    def send_to_sock(self, data):
        # return True when not blocked, can send more data

        self._debug_log("Conn send_to_sock conn:%d len:%d", self.conn_id, len(data))
        sock = self.sock
        if not sock:
            return False

        payload_len = len(data)
        start = 0
        end = payload_len
        while start < end:
            send_size = min(end - start, 65535)
            try:
                sended = sock.send(data[start:start + send_size])
            except Exception as e:
                self.xlog.info("%s conn:%d send closed: %r", self.session.session_id, self.conn_id, e)
                if self.is_client:
                    self.transfer_peer_close("send fail.")
                    self.do_stop(reason="send fail.")
                return False

            start += sended

            if sended == 0:
                self.connection_pipe.add_sock_event(sock, self, selectors.EVENT_WRITE)
                self.send_buffer = data[start:]
                self.blocked = True
                break

        if start == end:
            self.send_buffer = None

        self.sended_position += start
        if self.sended_position - self.sent_window_position > self.windows_ack:
            self.sent_window_position = self.sended_position
            self.transfer_ack(self.sended_position)
            self._debug_log("Conn:%d ack:%d", self.conn_id, self.sent_window_position)

        return not self.blocked

    def transfer_peer_close(self, reason=""):
        if self.transferred_close_to_peer:
            return

        self.transferred_close_to_peer = True

        cmd = struct.pack("<IB", self.next_recv_seq, 2)
        if isinstance(reason, str):
            reason = reason.encode("utf-8")
        self.session.send_conn_data(self.conn_id, cmd + reason)
        self.next_recv_seq += 1

    def transfer_received_data(self, data):
        if self.transferred_close_to_peer:
            return

        buf = WriteBuffer(struct.pack("<IB", self.next_recv_seq, 1))
        buf.append(data)
        self.next_recv_seq += 1
        self.received_position += len(data)

        self.session.send_conn_data(self.conn_id, buf)

        if self.received_position > self.remote_acked_position + self.windows_size:
            self.xlog.debug("Conn session:%s conn:%d recv blocked, rcv:%d, ack:%d", self.session.session_id,
                            self.conn_id, self.received_position, self.remote_acked_position)
            self.connection_pipe.remove_sock_event(self.sock, selectors.EVENT_READ)

    def transfer_ack(self, position):
        if self.transferred_close_to_peer:
            return

        cmd_position = struct.pack("<IBQ", self.next_recv_seq, 3, position)
        self.session.send_conn_data(self.conn_id, cmd_position)
        self.next_recv_seq += 1
