import threading
import time
import sys

from xx_six import BlockingIOError
import utils
import selectors2 as selectors

from . import global_var as g
from xlog import getLogger
xlog = getLogger("smart_router")


class PipeSocks(object):
    def __init__(self, buf_size=16*1024):
        self.buf_size = buf_size

        self.select2 = selectors.DefaultSelector()
        self.read_set = set([])
        self.write_set = set([])

        self.running = True
        self.sock_lock = threading.Lock()
        self.sock_notify = threading.Condition(self.sock_lock)

    def __str__(self):
        outs = ["Pipe Sockets:"]
        outs.append("buf_size=%d" % self.buf_size)
        outs.append("running=%d" % self.running)
        outs.append("")

        outs.append("read dict:")
        for s in self.read_set:
            outs.append(" %s" % s)

        outs.append("write dict:")
        for s in self.write_set:
            outs.append(" %s" % s)

        return "\n".join(outs)

    def run(self):
        self.down_th = threading.Thread(target=self.pipe)
        self.down_th.start()

    def stop(self):
        self.running = False

    def add_socks(self, s1, s2):
        for s in [s1, s2]:
            if hasattr(s._sock, "socket_closed") and s._sock.socket_closed:
                xlog.error("try to add_socks closed socket:%s %s", s1, s2)
                s1.close()
                s2.close()
                return

        s1.setblocking(0)
        s2.setblocking(0)

        with self.sock_notify:
            s1.pair_sock = s2
            s2.pair_sock = s1
            # self.select2.register(s1, selectors.EVENT_READ)
            # self.select2.register(s2, selectors.EVENT_READ)
            # self.read_set.add(s1)
            # self.read_set.add(s2)
            self.try_add("READ", s1)
            self.try_add("READ", s2)

            self.sock_notify.notify()

    def try_add(self, l, s):
        try:
            if l == "READ":
                if s in self.read_set:
                    # xlog.warn("%s already in read set", s)
                    pass
                else:
                    if s in self.write_set:
                        self.select2.modify(s, selectors.EVENT_WRITE | selectors.EVENT_READ)
                        # xlog.debug("change %s to read|write", s)
                    else:
                        self.select2.register(s, selectors.EVENT_READ)
                        # xlog.debug("change %s to read", s)
                    self.read_set.add(s)
            elif l == "WRITE":
                if s in self.write_set:
                    # xlog.warn("%s already in write set", s)
                    pass
                else:
                    if s in self.read_set:
                        self.select2.modify(s, selectors.EVENT_WRITE | selectors.EVENT_READ)
                        # xlog.debug("change %s to read|write", s)
                    else:
                        self.select2.register(s, selectors.EVENT_WRITE)
                        # xlog.debug("change %s to write", s)
                    self.write_set.add(s)
            else:
                xlog.error("unknown list %s", l)
        except Exception as e:
            xlog.exception("try_add e:%r", e)

    def try_remove(self, l, s):
        try:
            if l == "READ":
                if s in self.read_set:
                    if s in self.write_set:
                        self.select2.modify(s, selectors.EVENT_WRITE)
                        # xlog.debug("modify to write %s", s)
                    else:
                        self.select2.unregister(s)
                        # xlog.debug("unregister %s", s)
                    self.read_set.remove(s)
            elif l == "WRITE":
                if s in self.write_set:
                    if s in self.read_set:
                        self.select2.modify(s, selectors.EVENT_READ)
                        # xlog.debug("modify to read %s", s)
                    else:
                        self.select2.unregister(s)
                        # xlog.debug("unregister %s", s)
                    self.write_set.remove(s)
            else:
                xlog.error("unknown list %s", l)
        except Exception as e:
            xlog.exception("try_remove e:%r", e)

    def close(self, s1, e):
        xlog.debug("%s close", s1)

        s2 = s1.pair_sock

        if utils.is_private_ip(s1.ip):
            local_sock = s1
            remote_sock = s2
        else:
            local_sock = s2
            remote_sock = s1

        create_time = time.time() - remote_sock.create_time
        xlog.debug("pipe close %s->%s run_time:%.2f upload:%d(%d)->%d(%d) download:%d(%d)->%d(%d), by remote:%d, server left:%d client left:%d e:%r",
                   local_sock, remote_sock, create_time,
                   local_sock.recved_data, local_sock.recved_times, remote_sock.sent_data, remote_sock.sent_times,
                   remote_sock.recved_data, remote_sock.recved_times, local_sock.sent_data, local_sock.sent_times,
                   s1==remote_sock, remote_sock.buf_size, local_sock.buf_size, e)

        if local_sock.recved_data > 0 and local_sock.recved_times == 1 and remote_sock.port == 443 and \
                ((s1 == local_sock and create_time > 30) or (s1 == remote_sock)):
            host = remote_sock.host
            xlog.debug("SNI:%s fail.", host)
            #g.domain_cache.update_rule(host, 443, "gae")

        self.try_remove("READ", s1)
        self.try_remove("WRITE", s1)
        s1.close()

        if s2.buf_size:
            xlog.debug("pipe close %s e:%s, but s2:%s have data(%d) to send", s1, e, s2, s2.buf_size)
            s2.add_dat("")  # add empty block to close socket.
            return

        if not s2.is_closed():
            self.try_remove("READ", s2)
            self.try_remove("WRITE", s2)
            s2.close()

    def pipe(self):
        def flush_send_s(s2, d1):
            # xlog.debug("pipe flush_send_s %s %d", s2, len(d1))
            s2.setblocking(1)
            s2.settimeout(1)
            s2.sendall(d1)
            s2.setblocking(0)

        while self.running:
            if not self.read_set and not self.write_set:
                with self.sock_notify:
                    self.sock_notify.wait()
                continue

            try:
                # r, w, error_set = select.select(self.read_set, self.write_set, self.error_set, 0.1)
                events = self.select2.select(timeout=5)
            except ValueError as e:
                xlog.exception("pipe select except:%r", e)
                return

            read_list = []
            write_list = []
            error_list = []
            for key, event in events:
                s1 = key.fileobj
                if event & selectors.EVENT_READ:
                    s1.can_read = True
                    read_list.append(s1)
                    # xlog.debug("get read on %s", s1)
                elif event & selectors.EVENT_WRITE:
                    s1.can_write = True
                    write_list.append(s1)
                    # xlog.debug("get write on %s", s1)
                else:
                    error_list.append(s1)
                    xlog.error("get error on %s", s1)

            try:
                for s1 in read_list:
                    if s1.is_closed():
                        continue

                    try:
                        d = s1.recv(65535)
                    except Exception as e:
                        # xlog.debug("%s recv e:%r", s1, e)
                        self.close(s1, "r")
                        continue

                    if not d:
                        # socket closed by peer.
                        # xlog.debug("%s recv empty, close", s1)
                        self.close(s1, "r")
                        continue

                    # xlog.debug("direct received %d bytes from:%s", len(d), s1)
                    s1.recved_data += len(d)
                    s1.recved_times += 1

                    s2 = s1.pair_sock
                    if s2.is_closed():
                        # xlog.debug("s2:%s is closed", s2)
                        continue

                    if g.config.direct_split_SNI and\
                                    s1.recved_times == 1 and \
                                    s2.port == 443 and \
                                    d[0] == '\x16' and \
                            g.gfwlist.in_block_list(s2.host):
                        p1 = d.find(s2.host)
                        if p1 > 1:
                            if b"google" in s2.host:
                                p2 = d.find(b"google") + 3
                            else:
                                p2 = p1 + len(s2.host) - 6

                            d1 = d[:p2]
                            d2 = d[p2:]

                            try:
                                flush_send_s(s2, d1)
                                s2.sent_data += len(d1)
                                s2.sent_times += 1
                            except Exception as e:
                                xlog.warn("send split SNI:%s fail:%r", s2.host, e)
                                self.close(s2, "w")
                                continue

                            s2.add_dat(d2)
                            d = b""
                            xlog.debug("pipe send split SNI:%s", s2.host)

                    if s2.buf_size == 0:
                        try:
                            sent = s2.send(d)
                            s2.sent_data += sent
                            s2.sent_times += 1
                            # xlog.debug("direct send %d to %s from:%s total:%d", sent, s2, s1, len(d))
                        except Exception as e:
                            # xlog.debug("%s send e:%r", s2, e)
                            if sys.version_info[0] == 3 and isinstance(e, BlockingIOError):
                                # This error happened on upload large file or speed test
                                # Just ignore this error and will be fine
                                # xlog.warn("%s send BlockingIOError %r", s2, e)
                                sent = 0
                            else:
                                # xlog.warn("%s send except:%r", s2, e)
                                self.close(s2, "w")
                                continue

                        if sent == len(d):
                            # xlog.debug("direct send all from %s to %s", s1, s2)
                            continue
                        else:
                            # xlog.debug("direct send from %s to %s, total:%d left:%d", s1, s2, len(d), len(d)-sent)
                            d_view = memoryview(d)
                            d = d_view[sent:]

                    if d:
                        if not isinstance(d, memoryview):
                            d = memoryview(d)
                        s2.add_dat(d)

                    self.try_add("WRITE", s2)

                    if s2.buf_size > self.buf_size:
                        self.try_remove("READ", s1)

                for s1 in write_list:
                    if s1 not in self.write_set:
                        xlog.error("%s not in write list", s1)
                        continue

                    if s1.buf_num == 0:
                        xlog.error("%s write event but no buf", s1)
                        self.try_remove("WRITE", s1)
                        continue

                    while s1.buf_num:
                        dat = s1.get_dat()
                        if not dat:
                            xlog.error("%s get data fail", s1)
                            self.close(s1, "n")
                            break

                        try:
                            sent = s1.send(dat)
                            s1.sent_data += sent
                            s1.sent_times += 1
                            # xlog.debug("send buffered %d bytes to %s", sent, s1)
                        except Exception as e:
                            if sys.version_info[0] == 3 and isinstance(e, BlockingIOError):
                                # This error happened on upload large file or speed test
                                # Just ignore this error and will be fine
                                # xlog.debug("%s sent BlockingIOError %r", s1, e)
                                sent = 0
                            else:
                                # xlog.debug("%s sent e:%r", s1, e)
                                self.close(s1, "w")
                                break

                        if len(dat) - sent > 0:
                            s1.restore_dat(dat[sent:])
                            break

                    if s1.buf_size < self.buf_size:
                        if not s1.buf_size:
                            self.try_remove("WRITE", s1)

                        if s1.is_closed():
                            # xlog.debug("%s can send but removed", s1)
                            continue

                        s2 = s1.pair_sock
                        if s2.is_closed():
                            if s1.buf_size == 0:
                                self.close(s1, "n")
                            continue

                        self.try_add("READ", s2)

                for s1 in error_list:
                    xlog.error("close pipe %s in error list", s1)
                    self.close(s1, "e")
            except Exception as e:
                xlog.exception("pipe except:%r", e)

        for s in list(self.read_set) + list(self.write_set):
            self.close(s, "stop")

        xlog.info("pipe stopped.")