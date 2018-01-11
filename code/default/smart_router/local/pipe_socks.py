import threading
import select
import time

import utils

import global_var as g
from xlog import getLogger
xlog = getLogger("smart_router")


class Buf(object):
    def __init__(self):
        self.buf = []
        self.size = 0
        self.num = 0

    def add(self, data):
        self.buf.append(data)
        self.size += len(data)
        self.num += 1

    def get(self):
        if not self.buf:
            return ""
        dat = self.buf.pop(0)
        self.size -= len(dat)
        self.num -= 1
        return dat

    def restore(self, dat):
        self.buf.insert(0, dat)
        self.size += len(dat)
        self.num += 1


class PipeSocks(object):
    def __init__(self, buf_size=16*1024):
        self.buf_size = buf_size
        self.sock_dict = {}

        self.read_set = []
        self.write_set = []
        self.error_set = []

        # sock => Buf
        self.send_buf = {}

        self.running = True

    def __str__(self):
        outs = ["Pipe Sockets:"]
        outs.append("buf_size=%d" % self.buf_size)
        outs.append("running=%d" % self.running)
        outs.append("")
        outs.append("socket dict:")
        for s in self.sock_dict:
            outs.append(" %s =%s" % (s, self.sock_dict[s]))

        outs.append("read dict:")
        for s in self.read_set:
            outs.append(" %s" % s)

        outs.append("write dict:")
        for s in self.write_set:
            outs.append(" %s" % s)

        outs.append("error dict:")
        for s in self.error_set:
            outs.append(" %s" % s)

        outs.append("send buf:")
        for s in self.send_buf:
            buf = self.send_buf[s]
            outs.append(" %s size=%d num=%d" % (s, buf.size, buf.num))

        return "\n".join(outs)

    def run(self):
        self.down_th = threading.Thread(target=self.pipe)
        self.down_th.start()

    def stop(self):
        self.running = False

    def add_socks(self, s1, s2):
        s1.setblocking(0)
        s2.setblocking(0)

        self.read_set.append(s1)
        self.read_set.append(s2)
        self.error_set.append(s1)
        self.error_set.append(s2)

        self.sock_dict[s1] = s2
        self.sock_dict[s2] = s1

    def try_remove(self, l, s):
        try:
            l.remove(s)
        except:
            pass

    def close(self, s1, e):
        if s1 not in self.sock_dict:
            # xlog.warn("sock not in dict")
            return

        s2 = self.sock_dict[s1]
        if s1 in self.send_buf:
            left1 = self.send_buf[s1].size
        else:
            left1 = 0

        if utils.is_private_ip(s1.ip):
            local_sock = s1
            remote_sock = s2
        else:
            local_sock = s2
            remote_sock = s1

        create_time = time.time() - remote_sock.create_time
        xlog.debug("pipe close %s->%s run_time:%d upload:%d,%d download:%d,%d, by remote:%d, left:%d e:%r",
                   local_sock, remote_sock, create_time,
                   local_sock.recved_data, local_sock.recved_times,
                   remote_sock.recved_data, remote_sock.recved_times,
                   s1==remote_sock, left1, e)

        if local_sock.recved_data > 0 and local_sock.recved_times == 1 and remote_sock.port == 443 and \
                ((s1 == local_sock and create_time > 30) or (s1 == remote_sock)):
            host = remote_sock.host
            xlog.debug("SNI:%s fail.", host)
            #g.domain_cache.update_rule(host, 443, "gae")

        del self.sock_dict[s1]
        self.try_remove(self.read_set, s1)
        self.try_remove(self.write_set, s1)
        self.try_remove(self.error_set, s1)
        if s1 in self.send_buf:
            del self.send_buf[s1]
        s1.close()

        if s2 in self.send_buf and self.send_buf[s2].size:
            xlog.debug("pipe close %s e:%s, but s2:%s have data(%d) to send",
                       s1, e, s2, self.send_buf[s2].size)
            self.send_buf[s2].add("")
            return

        if s2 in self.sock_dict:
            self.try_remove(self.read_set, s2)
            self.try_remove(self.write_set, s2)
            self.try_remove(self.error_set, s2)
            del self.sock_dict[s2]
            if s2 in self.send_buf:
                del self.send_buf[s2]
            s2.close()

    def pipe(self):
        def flush_send_s(s2, d1):
            s2.setblocking(1)
            s2.settimeout(1)
            s2.sendall(d1)
            s2.setblocking(0)

        while self.running:
            if not self.error_set:
                time.sleep(1)
                continue

            try:
                r, w, e = select.select(self.read_set, self.write_set, self.error_set, 0.1)
                for s1 in list(r):
                    if s1 not in self.read_set:
                        continue

                    try:
                        d = s1.recv(65535)
                    except Exception as e:
                        self.close(s1, "r")
                        continue

                    if not d:
                        # socket closed by peer.
                        self.close(s1, "r")
                        continue

                    s1.recved_data += len(d)
                    s1.recved_times += 1

                    s2 = self.sock_dict[s1]
                    if s2.is_closed():
                        continue

                    if s2 not in self.send_buf:
                        self.send_buf[s2] = Buf()

                    if g.config.direct_split_SNI and\
                                    s1.recved_times == 1 and \
                                    s2.port == 443 and \
                                    d[0] == '\x16' and \
                            g.gfwlist.check(s2.host):
                        p1 = d.find(s2.host)
                        if p1 > 1:
                            if "google" in s2.host:
                                p2 = d.find("google") + 3
                            else:
                                p2 = p1 + len(s2.host) - 6

                            d1 = d[:p2]
                            d2 = d[p2:]

                            try:
                                flush_send_s(s2, d1)
                            except Exception as e:
                                xlog.warn("send split SNI:%s fail:%r", s2.host, e)
                                self.close(s2, "w")
                                continue

                            self.send_buf[s2].add(d2)
                            d = ""
                            xlog.debug("pipe send split SNI:%s", s2.host)

                    if d:
                        self.send_buf[s2].add(d)

                    if s2 not in self.write_set:
                        self.write_set.append(s2)
                    if self.send_buf[s2].size > self.buf_size:
                        self.read_set.remove(s1)

                for s1 in list(w):
                    if s1 not in self.write_set:
                        continue

                    if s1 not in self.send_buf or self.send_buf[s1].num == 0:
                        self.write_set.remove(s1)
                        continue

                    dat = self.send_buf[s1].get()
                    if not dat:
                        self.close(s1, "n")
                        continue

                    try:
                        sended = s1.send(dat)
                    except Exception as e:
                        self.close(s1, "w")
                        continue

                    if len(dat) - sended > 0:
                        self.send_buf[s1].restore(dat[sended:])
                        continue

                    if self.send_buf[s1].size == 0:
                        self.write_set.remove(s1)

                    if self.send_buf[s1].size < self.buf_size:
                        s2 = self.sock_dict[s1]
                        if s2 not in self.read_set and s2 in self.sock_dict:
                            self.read_set.append(s2)

                for s1 in list(e):
                    self.close(s1, "e")
            except Exception as e:
                xlog.exception("pipe except:%r", e)

        for s in list(self.error_set):
            self.close(s, "stop")

        xlog.info("pipe stopped.")