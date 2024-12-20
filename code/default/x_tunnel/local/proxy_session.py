import os
import time
import json
import threading
import xstruct as struct
import hashlib

from xlog import getLogger, keep_log
xlog = getLogger("x_tunnel")

import utils
from . import base_container
import encrypt
from . import global_var as g
from gae_proxy.local import check_local_network
from .upload_logs import upload_logs_thread

current_path = os.path.dirname(os.path.abspath(__file__))
root_path = os.path.abspath(os.path.join(current_path, os.pardir, os.pardir))


def encrypt_data(data):
    if g.config.encrypt_data:
        return encrypt.Encryptor(g.config.encrypt_password, g.config.encrypt_method).encrypt(data)
    else:
        return data


def decrypt_data(data):
    if g.config.encrypt_data:
        if isinstance(data, memoryview):
            data = data.tobytes()
        return encrypt.Encryptor(g.config.encrypt_password, g.config.encrypt_method).decrypt(data)
    else:
        return data


def traffic_readable(num, units=('B', 'KB', 'MB', 'GB')):
    for unit in units:
        if num >= 1024:
            num /= 1024.0
        else:
            break
    return '{:.1f} {}'.format(num, unit)


def sleep(t):
    end_time = time.time() + t
    while g.running:
        if time.time() > end_time:
            return

        sleep_time = min(5, end_time - time.time())
        if sleep_time > 0.01:
            time.sleep(sleep_time)


class ProxySession(object):
    def __init__(self):
        self.config = g.config
        self.wait_queue = base_container.WaitQueue()
        self.send_buffer = base_container.SendBuffer(max_payload=g.config.max_payload)
        self.receive_process = base_container.BlockReceivePool(self.download_data_processor, xlog)
        self.connection_pipe = base_container.ConnectionPipe(self, xlog)
        self.lock = threading.Lock()  # lock for conn_id, sn generation, on_road_num change,

        self.send_delay = g.config.send_delay / 1000.0
        self.ack_delay = g.config.ack_delay / 1000.0
        self.resend_timeout = g.config.resend_timeout / 1000.0

        self.running = False
        self.round_trip_thread = {}
        self.session_id = utils.generate_random_lowercase(8)
        self.last_conn_id = 0
        self.last_transfer_no = 0
        self.conn_list = {}
        self.transfer_list = {}
        self.on_road_num = 0
        self.last_receive_time = 0
        self.last_send_time = 0
        self.server_send_buf_size = 0
        self.target_on_roads = 0

        # speed calculation
        self.traffic_upload = 0
        self.traffic_download = 0
        self.last_traffic_upload = 0
        self.last_traffic_download = 0
        self.last_traffic_reset_time = time.time()
        self.upload_speed = 0.0
        self.download_speed = 0.0

        # server time logic like NTP
        self.server_time_offset = 0
        self.server_time_deviation = 9999

        # the receive time of the tail of the socket receive buffer
        # if now - oldest_received_time > delay, then send.
        # set only no data in receive buffer
        # if no data left, set to 0
        self.oldest_received_time = 0

        self.last_state = {
            "timeout": 0,
        }
        if g.config.enable_tls_relay:
            threading.Thread(target=self.reporter, name="reporter").start()

        if g.config.upload_logs:
            threading.Thread(target=upload_logs_thread, name="upload_logs").start()

        self.timeout_check_th = threading.Thread(target=self.timeout_checker, name="timeout_check")
        self.timeout_check_th.start()

    def start(self):
        with self.lock:
            if self.running is True:
                xlog.warn("session try to run but is running.")
                return True

            self.session_id = utils.to_bytes(utils.generate_random_lowercase(8))
            self.last_conn_id = 0
            self.last_transfer_no = 0
            self.conn_list = {}
            self.transfer_list = {}
            self.last_send_time = time.time()
            self.last_receive_time = 0

            # speed calculation
            self.traffic_upload = 0
            self.traffic_download = 0
            self.last_traffic_upload = 0
            self.last_traffic_download = 0
            self.last_traffic_reset_time = time.time()

            # sn => (payload, send_time)
            # sn => ack
            self.wait_ack_send_list = dict()
            self.ack_send_continue_sn = 0

            self.received_sn = []
            self.receive_next_sn = 1
            self.target_on_roads = 0
            self.server_time_offset = 0
            self.server_time_deviation = 9999

            if not self.login_session():
                xlog.warn("x-tunnel login_session fail, session not start")
                return False

            self.running = True

            for i in range(0, g.config.concurent_thread_num):
                if i in self.round_trip_thread:
                    continue

                self.round_trip_thread[i] = threading.Thread(target=self.normal_round_trip_worker, args=(i,),
                                                             name="roundtrip_%d" % i)
                self.round_trip_thread[i].start()

            self.connection_pipe.start()
            xlog.info("session started.")
            return True

    def timeout_checker(self):
        while self.running:
            timeout_num = 0
            with self.lock:
                time_now = time.time()
                for sn, data_info in self.transfer_list.items():
                    if data_info["stat"] != "timeout" and time_now - (data_info["start_time"] + data_info["server_timeout"]) > g.config.send_timeout_retry:
                        data_info["stat"] = "timeout"
                        xlog.warn("timeout_checker found transfer_no:%d timeout:%f", sn, time_now - data_info["start_time"])
                        timeout_num += 1

            if timeout_num:
                self.target_on_roads = \
                    min(g.config.concurent_thread_num - g.config.min_on_road, self.target_on_roads + timeout_num)
                self.trigger_more()

            time.sleep(1)

    def traffic_speed_calculation(self):
        now = time.time()
        time_go = now - self.last_traffic_reset_time
        if time_go > 0.5:
            self.upload_speed = (self.traffic_upload - self.last_traffic_upload) / time_go
            self.download_speed = (self.traffic_download - self.last_traffic_download) / time_go

            self.last_traffic_reset_time = now
            self.last_traffic_upload = self.traffic_upload
            self.last_traffic_download = self.traffic_download

            # xlog.debug("upload speed:%s download speed:%s",
            #            convert_data_size_easy_read(self.upload_speed),
            #            convert_data_size_easy_read(self.download_speed)
            #            )

    def stop(self):
        if not self.running:
            # xlog.warn("session stop but not running")
            return

        self.running = False
        self.session_id = ""
        self.target_on_roads = 0
        with self.lock:
            for i in range(0, g.config.concurent_thread_num):
                self.wait_queue.notify()

            self.close_all_connection()
            self.send_buffer.reset()
            self.receive_process.reset()
            self.wait_queue.stop()
            self.connection_pipe.stop()

            xlog.debug("session stopped.")

    def reset(self):
        xlog.debug("session reset")
        self.stop()
        return self.start()

    def is_idle(self):
        return time.time() - self.last_send_time > 60

    def check_upload(self):
        # xlog.debug("check_upload send_buffer.pool_size:%d", self.send_buffer.pool_size)
        if self.send_buffer.pool_size > 0:
            # xlog.debug("wait_queue notify")
            self.wait_queue.notify()
            return True

    def reporter(self):
        sleep(5)
        while g.running:
            if not g.running:
                break

            self.check_report_status()
            sleep(g.config.report_interval)

    def check_report_status(self):
        if self.is_idle() or not g.config.api_server:
            return

        good_ip_num = 0
        for ip in g.tls_relay_front.ip_manager.ip_dict:
            ip_state = g.tls_relay_front.ip_manager.ip_dict[ip]
            fail_times = ip_state["fail_times"]
            if fail_times == 0:
                good_ip_num += 1
        if good_ip_num:
            return

        stat = self.get_stat("minute")
        stat["version"] = g.xxnet_version
        stat["client_uuid"] = g.client_uuid
        timeout_count = g.stat["timeout_roundtrip"] - self.last_state["timeout"]
        if timeout_count == 0:
            return

        stat["global"]["timeout"] = timeout_count
        stat["global"]["ipv6"] = check_local_network.IPv6.is_ok()
        stat["tls_relay_front"]["ip_dict"] = g.tls_relay_front.ip_manager.ip_dict

        report_dat = {
            "account": str(g.config.login_account),
            "password": str(g.config.login_password),
            "stat": stat,
        }
        xlog.debug("start report_stat")
        status, info = call_api("/report_stat", report_dat)
        if not status:
            xlog.warn("report fail.")
            return

        self.last_state["timeout"] = g.stat["timeout_roundtrip"]
        data = info["data"]
        g.tls_relay_front.set_ips(data["ips"])

    def get_stat(self, type="second"):
        self.traffic_speed_calculation()

        res = {}
        rtt = 0
        recent_sent = 0
        recent_received = 0
        total_sent = 0
        total_received = 0
        for front in g.http_client.all_fronts:
            if not front:
                continue
            name = front.name
            dispatcher = front.get_dispatcher(g.server_host)
            if not dispatcher:
                res[name] = {
                    "score": "False",
                    "rtt": 9999,
                    "success_num": 0,
                    "fail_num": 0,
                    "worker_num": 0,
                    "total_traffics": "Up: 0 / Down: 0"
                }
                continue
            score = dispatcher.get_score()
            if score is None:
                score = "False"
            else:
                score = int(score)

            if type == "second":
                stat = dispatcher.second_stat
            elif type == "minute":
                stat = dispatcher.minute_stat
            else:
                raise Exception()

            rtt = max(rtt, stat["rtt"])
            recent_sent += stat["sent"]
            recent_received += stat["received"]
            total_sent += dispatcher.total_sent
            total_received += dispatcher.total_received
            res[name] = {
                "score": score,
                "rtt": stat["rtt"],
                "success_num": dispatcher.success_num,
                "fail_num": dispatcher.fail_num,
                "worker_num": dispatcher.worker_num(),
                "total_traffics": "Up: %s / Down: %s" % (
                    traffic_readable(dispatcher.total_sent), traffic_readable(dispatcher.total_received))
            }

        res["global"] = {
            "handle_num": g.socks5_server.handler.handle_num,
            "rtt": int(rtt),
            "roundtrip_num": g.stat["roundtrip_num"],
            "slow_roundtrip": g.stat["slow_roundtrip"],
            "timeout_roundtrip": g.stat["timeout_roundtrip"],
            "resend": g.stat["resend"],
            "speed": "Up: %s/s / Down: %s/s" % (traffic_readable(self.upload_speed), traffic_readable(self.download_speed)),
            "total_traffics": "Up: %s / Down: %s" % (traffic_readable(self.traffic_upload), traffic_readable(self.traffic_download))
        }
        return res

    def status(self):
        self.traffic_speed_calculation()

        out_string = "session_id: %s\n" % utils.to_str(self.session_id)
        out_string += "server: %s\n" % g.server_host
        out_string += "extra_info: %s\n" % json.dumps(json.loads(self.get_login_extra_info()), indent=2)
        out_string += "thread num: %d\n" % threading.active_count()
        out_string += "running: %d\n" % self.running
        out_string += "last_send_time: %f\n" % (time.time() - self.last_send_time)
        out_string += "last_receive_time: %f ago\n" % (time.time() - self.last_receive_time)
        out_string += "last_conn: %d\n" % self.last_conn_id
        out_string += "last_transfer_no: %d\n" % self.last_transfer_no
        out_string += "traffic_upload: %d\n" % self.traffic_upload
        out_string += "traffic_download: %d\n" % self.traffic_download
        out_string += "last_traffic_upload: %d\n" % self.last_traffic_upload
        out_string += "last_traffic_download: %d\n" % self.last_traffic_download
        out_string += "upload_speed: %f\n" % self.upload_speed
        out_string += "download_speed: %f\n" % self.download_speed
        out_string += "last_traffic_reset_time %f ago\n" % (time.time() - self.last_traffic_reset_time )
        out_string += "server_time_offset: %f\n" % self.server_time_offset
        out_string += "server_time_deviation: %f\n" % self.server_time_deviation
        out_string += "target_on_roads: %d\n" % self.target_on_roads
        out_string += "on_road_num:%d\n" % self.on_road_num
        out_string += "transfer_list: %d\n" % len(self.transfer_list)
        for sn in sorted(self.transfer_list.keys()):
            data_info = self.transfer_list[sn]
            time_way = " t:" + str((time.time() - self.transfer_list[sn]["start_time"]))
            out_string += f'[{sn}] stat:{data_info["stat"]} server_timeout:{data_info["server_timeout"]} retry:{data_info["retry"]} {time_way}\n'

        out_string += "\n" + self.wait_queue.status()
        out_string += "\n" + self.send_buffer.status()
        out_string += "\n" + self.receive_process.status()
        out_string += "\n" + self.connection_pipe.status()

        for conn_id in self.conn_list:
            out_string += "\n" + self.conn_list[conn_id].status()

        return out_string

    @staticmethod
    def get_login_extra_info():
        data = {
            "version": g.xxnet_version,
            "system": g.system,
            "device": g.client_uuid
        }
        return json.dumps(data)

    def login_session(self):
        if not g.server_host or len(g.server_host) == 0:
            return False

        start_time = time.time()
        while time.time() - start_time < 30:
            try:
                magic = b"P"
                pack_type = 1
                upload_data_head = struct.pack("<cBB8sIHIIHH", magic, g.protocol_version, pack_type,
                                               self.session_id,
                                               g.config.max_payload, g.config.send_delay, g.config.windows_size,
                                               int(g.config.windows_ack), g.config.resend_timeout, g.config.ack_delay)
                upload_data_head += struct.pack("<H", len(g.config.login_account)) + utils.to_bytes(g.config.login_account)
                upload_data_head += struct.pack("<H", len(g.config.login_password)) + utils.to_bytes(g.config.login_password)
                extra_info = self.get_login_extra_info()
                upload_data_head += struct.pack("<H", len(extra_info)) + utils.to_bytes(extra_info)

                upload_post_data = encrypt_data(upload_data_head)

                content, status, response = g.http_client.request(method="POST", host=g.server_host, path="/data",
                                                                  data=upload_post_data,
                                                                  timeout=g.config.network_timeout)

                time_cost = time.time() - start_time

                if status == 521:
                    g.last_api_error = "session server is down."
                    xlog.warn("login session server is down, try get new server.")
                    g.server_host = None
                    return False

                if status != 200:
                    g.last_api_error = "session server login fail:%r" % status
                    xlog.warn("login session fail, status:%r", status)
                    continue

                if len(content) < 6:
                    g.last_api_error = "session server protocol fail, login res len:%d" % len(content)
                    xlog.error("login data len:%d fail", len(content))
                    continue

                info = decrypt_data(content)
                magic, protocol_version, pack_type, res, message_len = struct.unpack("<cBBBH", info[:6])
                message = info[6:]
                if isinstance(message, memoryview):
                    message = message.tobytes()

                if magic != b"P" or protocol_version != g.protocol_version or pack_type != 1:
                    xlog.error("login_session time:%d head error:%s", 1000 * time_cost, utils.str2hex(info[:6]))
                    return False

                if res != 0:
                    g.last_api_error = "session server login fail, code:%d msg:%s" % (res, message)
                    xlog.warn("login_session time:%d fail, res:%d msg:%s", 1000 * time_cost, res, message)
                    return False

                try:
                    msg_info = json.loads(message)
                    if msg_info.get("full_log"):
                        xlog.debug("keep full log")
                        keep_log(temp=True)
                except Exception as e:
                    xlog.warn("login_session %s json error:%r", message, e)
                    msg_info = {}

                g.last_api_error = ""
                xlog.info("login_session %s time:%d msg:%s", self.session_id, 1000 * time_cost, message)
                return True
            except Exception as e:
                xlog.exception("login_session e:%r", e)
                time.sleep(1)

        return False

    def create_conn(self, sock, host, port, log=False):
        if not self.running:
            xlog.debug("session not running, try to connect")
            time.sleep(1)
            return None

        with self.lock:
            self.last_conn_id += 2
            conn_id = self.last_conn_id

        if isinstance(host, str):
            host = host.encode("ascii")

        seq = 0
        cmd_type = 0  # create connection
        sock_type = 0  # TCP
        data = struct.pack("<IBBH", seq, cmd_type, sock_type, len(host)) + host + struct.pack("<H", port)
        self.send_conn_data(conn_id, data)

        self.conn_list[conn_id] = base_container.Conn(self, conn_id, sock, host, port, g.config.windows_size,
                                                      g.config.windows_ack, True, xlog)

        self.target_on_roads = \
            min(g.config.concurent_thread_num - g.config.min_on_road, self.target_on_roads + 10)
        self.trigger_more()

        if log:
            xlog.info("Connect to %s:%d conn:%d", host, port, conn_id)
        return conn_id

    # Called by stop
    def close_all_connection(self):
        xlog.info("start close all connection")
        conn_list = dict(self.conn_list)
        for conn_id in conn_list:
            try:
                # xlog.debug("stopping conn:%d", conn_id)
                self.conn_list[conn_id].stop(reason="system reset")
            except Exception as e:
                xlog.warn("stopping conn:%d fail:%r", conn_id, e)
                pass
        # self.conn_list = {}
        xlog.debug("stop all connection finished")

    def remove_conn(self, conn_id):
        try:
            if conn_id in self.conn_list:
                conn = self.conn_list[conn_id]
                # xlog.debug("remove conn:%d %s:%d", conn_id, conn.host, conn.port)
                del self.conn_list[conn_id]
        except Exception as e:
            xlog.warn("remove conn:%d except:%r", conn_id, e)

        if len(self.conn_list) == 0:
            self.target_on_roads = 0

    def send_conn_data(self, conn_id, data):
        if not self.running:
            xlog.warn("send_conn_data but not running")
            return

        # xlog.debug("upload conn:%d, len:%d", conn_id, len(data))
        buf = base_container.WriteBuffer()
        buf.append(struct.pack("<II", conn_id, len(data)))
        buf.append(data)
        self.send_buffer.put(buf)

        if self.oldest_received_time == 0:
            self.oldest_received_time = time.time()
        elif self.send_buffer.pool_size > g.config.max_payload:
            # xlog.debug("notify on send conn data")
            self.wait_queue.notify()

    @staticmethod
    def sn_payload_head(sn, payload):
        return struct.pack("<II", sn, len(payload))

    def get_data(self, work_id):
        time_now = time.time()
        buf = base_container.WriteBuffer()

        with self.lock:
            for sn in self.wait_ack_send_list:
                pk = self.wait_ack_send_list[sn]
                if isinstance(pk, str):
                    continue

                payload, send_time = pk
                if time_now - send_time > self.resend_timeout:
                    g.stat["resend"] += 1
                    buf.append(self.sn_payload_head(sn, payload))
                    buf.append(payload)
                    self.wait_ack_send_list[sn] = (payload, time_now)
                    if len(buf) > g.config.max_payload:
                        return buf

            if self.send_buffer.pool_size > g.config.max_payload or \
                    (self.send_buffer.pool_size > 0 and
                     time.time() - self.oldest_received_time > self.send_delay
                    ):
                payload, sn = self.send_buffer.get()
                self.wait_ack_send_list[sn] = (payload, time_now)
                buf.append(self.sn_payload_head(sn, payload))
                buf.append(payload)

                if self.send_buffer.pool_size == 0:
                    self.oldest_received_time = 0

                if len(buf) > g.config.max_payload:
                    return buf
            # else:
            #     xlog.debug("pool_size:%d work_id:%d target_on_road:%d",
            #                self.send_buffer.pool_size, work_id, self.target_on_roads)

        return buf

    def get_ack(self, force=False):
        time_now = time.time()
        # xlog.debug("get_ack force:%d, last_receive_time:%f, last_send_time:%f, time_now - self.last_send_time:%f",
        #           force, self.last_receive_time, self.last_send_time, time_now - self.last_send_time)

        if force or \
                (self.last_receive_time > self.last_send_time and
                 time_now - self.last_receive_time > self.ack_delay):

            buf = base_container.WriteBuffer()
            buf.append(struct.pack("<I", self.receive_process.next_sn - 1))
            for sn in self.receive_process.block_list:
                buf.append(struct.pack("<I", sn))
            return buf

        return ""

    def get_down_sn_timeout_list_pack(self):
        buf = base_container.WriteBuffer()
        if self.server_time_deviation > g.config.server_time_max_deviation:
            return buf

        server_time = int(time.time() + self.server_time_offset)
        timeout_list = self.receive_process.get_timeout_list(server_time, g.config.server_download_timeout_retry)
        for sn in timeout_list:
            buf.append(struct.pack("<I", sn))
        buf.insert(struct.pack("<I", len(timeout_list)))
        return buf

    def get_send_data(self, work_id):
        force = False
        while self.running:
            data = self.get_data(work_id)
            down_sn_timeout_list_pack = self.get_down_sn_timeout_list_pack()
            # xlog.debug("get_send_data work_id:%d len:%d", work_id, len(data))
            if data or len(down_sn_timeout_list_pack) > 4 or self.on_road_num < self.target_on_roads:
                # xlog.debug("got data, force get ack")
                force = True

            ack = self.get_ack(force=force)
            if force or ack:
                # xlog.debug("get_send_data work_id:%d data_len:%d ack_len:%d force:%d", work_id, len(data), len(ack), force)
                return data, ack, down_sn_timeout_list_pack

            self.wait_queue.wait(work_id)

        xlog.debug("get_send_data on stop")
        return b"", b"", b""

    def ack_process(self, ack):
        self.lock.acquire()
        try:
            last_ack = struct.unpack("<I", ack.get(4))[0]

            while len(ack):
                sn = struct.unpack("<I", ack.get(4))[0]
                # xlog.debug("ack: %d", sn)
                if sn in self.wait_ack_send_list:
                    self.wait_ack_send_list[sn] = "acked"

            for sn in self.wait_ack_send_list:
                if sn > last_ack:
                    continue
                if self.wait_ack_send_list[sn] == "acked":
                    continue

                # xlog.debug("last_ack:%d sn:%d", last_ack, sn)
                self.wait_ack_send_list[sn] = "acked"

            while (self.ack_send_continue_sn + 1) in self.wait_ack_send_list and \
                    self.wait_ack_send_list[self.ack_send_continue_sn + 1] == "acked":
                self.ack_send_continue_sn += 1
                del self.wait_ack_send_list[self.ack_send_continue_sn]

        except Exception as e:
            xlog.exception("ack_process:%r", e)
        finally:
            self.lock.release()

    def download_data_processor(self, data):
        try:
            while len(data):
                conn_id, payload_len = struct.unpack("<II", data.get(8))
                payload = data.get_buf(payload_len)

                # xlog.debug("conn:%d upload data len:%d", conn_id, len(payload))
                if conn_id not in self.conn_list:
                    xlog.debug("conn:%d not exist", conn_id)
                    continue
                self.conn_list[conn_id].put_cmd_data(payload)
        except Exception as e:
            xlog.exception("download_data_processor:%r", e)

    def check_upload_not_acked(self, server_time):
        server_local_time = server_time - self.server_time_offset
        if self.server_time_deviation > g.config.server_time_max_deviation:
            return

        timeout_num = 0
        entry_time = time.time()
        with self.lock:
            now = time.time()
            if now - entry_time > 0.1:
                xlog.error("check_upload_not_acked lock time:%f", now - entry_time)
                return

            for no, data_info in self.transfer_list.items():
                if data_info["stat"] == "timeout":
                    continue

                if data_info["server_received"] == False and server_local_time - data_info["start_time"] > g.config.send_timeout_retry:
                    data_info["stat"] = "timeout"
                    xlog.warn("check_upload_not_acked found transfer_no:%d upload timeout:%f", no,
                              server_local_time - data_info["start_time"])
                    timeout_num += 1
                    continue

                if data_info["server_sent"] and server_time - data_info["server_sent"] > g.config.send_timeout_retry:
                    data_info["stat"] = "timeout"
                    xlog.warn("check_upload_not_acked found transfer_no:%d down timeout:%f", no,
                              server_time - data_info["server_sent"])
                    timeout_num += 1
                    continue

        if timeout_num:
            self.target_on_roads = \
                min(g.config.concurent_thread_num - g.config.min_on_road, self.target_on_roads + timeout_num)
            self.trigger_more()

    def process_server_received_transfer_no(self, server_received_no_list, server_sent_no_list, server_time):
        server_received_next_no = struct.unpack("<I", server_received_no_list.get(4))[0]
        server_sent_next_no = struct.unpack("<I", server_sent_no_list.get(4))[0]
        with self.lock:
            for no, info in self.transfer_list.items():
                if no < server_received_next_no:
                    info["server_received"] = True

                if no < server_sent_next_no:
                    info["server_sent"] = server_time

            server_unordered_received_no_num = struct.unpack("<I", server_received_no_list.get(4))[0]
            for i in range(0, server_unordered_received_no_num):
                no, t = struct.unpack("<Id", server_received_no_list.get(12))
                if no in self.transfer_list:
                    # xlog.debug("server unordered confirmed transfer_no:%d", sn)
                    self.transfer_list[no]["server_received"] = t

            server_unordered_sent_no_num = struct.unpack("<I", server_sent_no_list.get(4))[0]
            for i in range(0, server_unordered_sent_no_num):
                no, t = struct.unpack("<Id", server_sent_no_list.get(12))
                if no in self.transfer_list:
                    # xlog.debug("server unordered confirmed transfer_no:%d", sn)
                    self.transfer_list[no]["server_sent"] = t

    def process_server_unacked_sent_sn(self, data):
        if self.server_time_deviation > g.config.server_time_max_deviation:
            return

        server_time = time.time() + self.server_time_offset

        sn_num = struct.unpack("<I", data.get(4))[0]
        timeout_num = 0
        for i in range(0, sn_num):
            sn, t = struct.unpack("<Id", data.get(12))
            if self.receive_process.is_received(sn):
                continue

            if server_time - t > g.config.server_download_timeout_retry:
                # xlog.warn("server unacked sn:%d timeout:%f", sn, server_time - t)
                self.receive_process.mark_sn_timeout(sn, t, server_time)
                timeout_num += 1

    def round_trip_process(self, data, ack, server_rcvd_no_list, server_sent_no_list, server_unack_snd_sn, server_time):
        while len(data):
            sn, plen = struct.unpack("<II", data.get(8))
            pdata = data.get_buf(plen)
            if g.config.show_debug:
                xlog.debug("download sn:%d len:%d", sn, plen)

            self.receive_process.put(sn, pdata)

        self.ack_process(ack)

        self.process_server_received_transfer_no(server_rcvd_no_list, server_sent_no_list, server_time)

        self.process_server_unacked_sent_sn(server_unack_snd_sn)

    def get_transfer_no(self):
        with self.lock:
            self.last_transfer_no += 1
            transfer_no = self.last_transfer_no

        return transfer_no

    def trigger_more(self):
        running_num = g.config.concurent_thread_num - len(self.wait_queue.waiters)
        action_num = self.target_on_roads - running_num
        if action_num <= 0:
            return

        # xlog.debug("running_num:%d on_road:%d target:%d action:%d",
        #            running_num, self.on_road_num,
        #            self.target_on_roads, action_num)
        for _ in range(0, action_num):
            self.wait_queue.notify()

    def normal_round_trip_worker(self, work_id):
        try:
            while self.running:
                self.roundtrip_task(work_id)
        finally:
            del self.round_trip_thread[work_id]
            xlog.info("roundtrip thread %d exit", work_id)

    def get_upload_data(self, work_id):
        if not self.running:
            return

        # Get a timeout request to retry
        time_now = time.time()
        with self.lock:
            wrong_sn = []
            for sn, data_info in self.transfer_list.items():
                if data_info["session_id"] != self.session_id:
                    wrong_sn.append(sn)
                    continue

                if data_info["stat"] == "timeout":
                    xlog.warn("retry transfer_no:%d t:%f", sn, time_now - data_info["start_time"])
                    data_info["stat"] = "retry"
                    data_info["retry"] += 1
                    data_info["start_time"] = time_now

                    return data_info

            for sn in wrong_sn:
                del self.transfer_list[sn]

        # Generate a new request
        data, ack, download_timeout = self.get_send_data(work_id)
        transfer_no = self.get_transfer_no()
        # xlog.debug("trip:%d no:%d send data:%s", work_id, transfer_no, parse_data(data))

        start_time = time.time()
        info = {
            "session_id": self.session_id,
            "transfer_no": transfer_no,
            "stat": "request",
            "server_received": False,
            "server_sent": False,
            "start_time": start_time,
            "server_timeout": g.config.roundtrip_timeout,
            "send_data": data,
            "send_ack": ack,
            "download_timeout": download_timeout,
            "request_session_id": self.session_id,
            "retry": 0,
        }

        with self.lock:
            self.transfer_list[transfer_no] = info

        return info

    def roundtrip_task(self, work_id):
        data_info = self.get_upload_data(work_id)
        request_session_id = data_info["request_session_id"]
        if request_session_id != self.session_id:
            return

        transfer_no = data_info["transfer_no"]
        start_time = data_info["start_time"]
        send_data = data_info["send_data"]
        send_ack = data_info["send_ack"]
        download_timeout = data_info["download_timeout"]
        request_session_id = data_info["request_session_id"]

        # Generate upload data package
        send_data_len = len(send_data)
        send_ack_len = len(send_ack)
        download_timeout_len = len(download_timeout)

        if self.send_buffer.pool_size > g.config.max_payload or \
                len(self.wait_queue.waiters) < g.config.min_on_road or \
                self.server_time_deviation > g.config.server_time_max_deviation or \
                data_info["stat"] == "retry":
            # xlog.debug("pool_size:%s waiters:%d", self.send_buffer.pool_size, len(self.wait_queue.waiters))
            server_timeout = 0
        else:
            server_timeout = g.config.roundtrip_timeout

        with self.lock:
            if transfer_no not in self.transfer_list:
                xlog.warn("roundtrip transfer_no not found:%d", transfer_no)
                return

            self.on_road_num += 1
            self.transfer_list[transfer_no]["server_timeout"] = server_timeout

        magic = b"P"
        pack_type = 2
        upload_data_head = struct.pack("<cBB8sIBIHH", magic, g.protocol_version, pack_type,
                                       utils.to_bytes(self.session_id), transfer_no,
                                       server_timeout, send_data_len, send_ack_len, download_timeout_len)
        upload_post_buf = base_container.WriteBuffer(upload_data_head)
        upload_post_buf.append(send_data)
        upload_post_buf.append(send_ack)
        upload_post_buf.append(download_timeout)
        upload_post_data = upload_post_buf.to_bytes()
        upload_post_data = encrypt_data(upload_post_data)
        self.last_send_time = time.time()

        if g.config.show_debug:
            self.traffic_speed_calculation()
            xlog.debug("start trip, tid:%d target:%d running:%d timeout:%d send:%d",
                       transfer_no, self.target_on_roads, self.on_road_num, server_timeout,
                       len(upload_post_data))

        sleep_time = 1
        # Use one time loop for easy quit and clean up.
        for _ in range(1):
            upload_post_data2 = bytearray(upload_post_data)
            try:
                content, status, response = g.http_client.request(method="POST", host=g.server_host,
                                                                  path="/data?tid=%d" % transfer_no,
                                                                  data=upload_post_data2,
                                                                  headers={
                                                                      "Content-Length": str(len(upload_post_data2)),
                                                                  },
                                                                  timeout=server_timeout + g.config.network_timeout)

                traffic = len(upload_post_data2) + len(content) + 645
                self.traffic_upload += len(upload_post_data2) + 645
                self.traffic_download += len(content)
                g.quota -= traffic
                if g.quota < 0:
                    g.quota = 0
            except Exception as e:
                if self.running:
                    xlog.exception("request except:%r ", e)

                data_info["stat"] = "timeout"
                time.sleep(sleep_time)
                continue
            finally:
                with self.lock:
                    self.on_road_num -= 1

            g.stat["roundtrip_num"] += 1
            time_now = time.time()
            roundtrip_time = (time_now - start_time)

            if status == 521:
                xlog.warn("X-tunnel server is down, try get new server.")
                g.server_host = None
                self.stop()
                login_process()
                return

            if status != 200:
                head = upload_post_data2[:3]
                xlog.warn("roundtrip time:%f transfer_no:%d send:%d head:%s status:%r ",
                          roundtrip_time, transfer_no, send_data_len, utils.str2hex(head), status)
                data_info["stat"] = "timeout"
                time.sleep(sleep_time)
                continue

            content_length = int(response.headers.get(b"Content-Length", b"0"))
            content_len = len(content)
            if content_len < 6 or (content_length and content_length != content_len):
                xlog.warn("roundtrip time:%f transfer_no:%d send:%d recv:%d Head:%d",
                          roundtrip_time, transfer_no, send_data_len, content_len, content_length)

                data_info["stat"] = "timeout"
                continue

            try:
                content = decrypt_data(content)
                payload = base_container.ReadBuffer(content)

                magic, version, pack_type = struct.unpack("<cBB", payload.get(3))
                if magic != b"P" or version != g.protocol_version or pack_type not in [2, 3]:
                    xlog.warn("get data head:%s", utils.str2hex(content[:2]))
                    data_info["stat"] = "timeout"
                    time.sleep(sleep_time)
                    continue

                if pack_type == 3:  # error report
                    error_code, message_len = struct.unpack("<BH", payload.get(3))
                    message = payload.get(message_len)
                    # xlog.warn("report code:%d, msg:%s", error_code, message)
                    if error_code == 1:
                        # no quota
                        xlog.warn("x_server error:no quota")
                        self.stop()
                        return
                    elif error_code == 2:
                        # unpack error
                        xlog.warn("roundtrip time:%f transfer_no:%d send:%d recv:%d unpack_error:%s",
                                  roundtrip_time, transfer_no, send_data_len, len(content), message)
                        data_info["stat"] = "timeout"
                        continue
                    elif error_code == 3:
                        # session not exist
                        if self.session_id == request_session_id:
                            xlog.warn("server session_id:%s not exist, reset session.", request_session_id)
                            self.reset()
                        return
                    else:
                        xlog.error("unknown error code:%d, message:%s", error_code, message)
                        time.sleep(sleep_time)
                        continue

                server_time, time_cost, server_send_pool_size, data_len, ack_len, rcvd_no_len, sent_no_len, unack_snd_sn_len, ext_len \
                    = struct.unpack("<dIIIIIIII", payload.get(40))
                head_len = (content_len - data_len - ack_len - rcvd_no_len - sent_no_len - unack_snd_sn_len - ext_len)
                if head_len < 3 + 40:
                    xlog.warn("no:%d recv_len:%d data:%d ack:%d head:%d",
                              transfer_no, content_len, data_len, ack_len, head_len)
                    data_info["stat"] = "timeout"
                    continue

                rtt = roundtrip_time * 1000 - time_cost
                rtt = max(100, rtt)
                speed = (send_data_len + len(content) + 400) / rtt

                if roundtrip_time < self.server_time_deviation:
                    new_offset = server_time - time_now
                    xlog.info("adjust server time offset:%f->%f, deviation:%f->%f", self.server_time_offset, new_offset,
                               self.server_time_deviation, roundtrip_time)
                    self.server_time_offset = new_offset
                    self.server_time_deviation = roundtrip_time

                xlog.debug(
                    "no:%d %s "
                    "road_time:%f "
                    "snd:%d rcv:%d "
                    "s_pool:%d on_road:%d target_worker:%d speed:%d "
                    "roundtrip_time:%f server_timeout:%d ",
                    transfer_no, response.worker.ip_str,
                    roundtrip_time - time_cost / 1000.0,
                    send_data_len, len(content),
                    server_send_pool_size,
                    self.on_road_num,
                    self.target_on_roads,
                    speed, roundtrip_time, server_timeout
                )
                if g.config.show_debug:
                    xlog.debug("data:%d ack:%d rcvd_no:%d sent_no:%d unack_sent_no:%d", data_len, ack_len, rcvd_no_len, sent_no_len, unack_snd_sn_len)

                if len(self.conn_list) == 0:
                    self.target_on_roads = 0
                elif len(content) >= g.config.max_payload:
                    self.target_on_roads = \
                        min(g.config.concurent_thread_num - g.config.min_on_road, self.target_on_roads + 10)
                elif data_len <= 200:
                    self.target_on_roads = max(g.config.min_on_road, self.target_on_roads - 5)
                self.trigger_more()
                # xlog.debug("target roundtrip: %d, on_road: %d", self.target_on_roads, self.on_road_num)

                response.worker.update_debug_data(rtt, send_data_len, len(content), speed)
                if rtt > 8000:
                    xlog.warn("rtt:%d speed:%d trace:%s", rtt, speed, response.worker.get_trace())
                    xlog.warn("task trace:%s", response.task.get_trace())
                    g.stat["slow_roundtrip"] += 1

                data = payload.get_buf(data_len)
                ack = payload.get_buf(ack_len)
                rcvd_no_list = payload.get_buf(rcvd_no_len)
                sent_no_list = payload.get_buf(sent_no_len)
                unack_snd_sn = payload.get_buf(unack_snd_sn_len)
                ext = payload.get_buf(ext_len)

                checksum_str = utils.to_str(payload.get(32).tobytes())
                checksum = hashlib.md5(bytes(content[:-32])).hexdigest()
                if checksum != checksum_str:
                    xlog.warn("checksum error:%s %s", checksum_str, checksum)

                    data_info["stat"] = "timeout"
                    continue

                self.last_receive_time = time.time()

                with self.lock:
                    if transfer_no in self.transfer_list:
                        del self.transfer_list[transfer_no]

                self.round_trip_process(data, ack, rcvd_no_list, sent_no_list, unack_snd_sn, server_time)
                self.check_upload_not_acked(server_time)

                return
            except Exception as e:
                xlog.exception("trip:%d no:%d data not enough %r", work_id, transfer_no, e)

                data_info["stat"] = "timeout"
                continue

                # xlog.debug("trip:%d no:%d recv data:%s", work_id, transfer_no, parse_data(data))

        xlog.warn("roundtrip failed, no:%d target:%d on_road:%d timeout:%d send:%d",
                   transfer_no, self.target_on_roads, self.on_road_num, server_timeout,
                   len(upload_post_data))


def parse_data(data):
    if len(data) == 0:
        return ""

    o = ""

    data = bytes(data)
    data = base_container.ReadBuffer(data)
    while len(data):

        sn, block_len = struct.unpack("<II", data.get(8))
        block = data.get_buf(block_len)

        o += "sn:%d {" % sn

        while len(block):
            conn_id, payload_len = struct.unpack("<II", block.get(8))

            o += "conn:%d [" % conn_id
            conn_data = block.get_buf(payload_len)

            seq = struct.unpack("<I", conn_data.get(4))[0]
            cmd_id = struct.unpack("<B", conn_data.get(1))[0]
            conn_payload = conn_data.get_buf()
            if cmd_id == 0:  # create connection
                sock_type = struct.unpack("<B", conn_payload.get(1))[0]
                host_len = struct.unpack("<H", conn_payload.get(2))[0]
                host = str(bytes(conn_payload.get(host_len)))
                port = struct.unpack("<H", conn_payload.get(2))[0]
                o += "%d|Connect:%s:%d" % (seq, host, port)
            elif cmd_id == 1:  # data
                o += "%d|D:%d" % (seq, len(conn_payload))
            elif cmd_id == 2:  # closed
                o += "%d|Closed:%s" % (seq, conn_payload)
            elif cmd_id == 3:  # ack
                position = struct.unpack("<Q", conn_payload.get())[0]
                o += "%d|Ack:%d" % (seq, position)

            o += "],"
        o += "},"

    return o


def calculate_quota_left(quota_list):
    time_now = int(time.time())
    quota_left = 0

    try:
        if "current" in quota_list:
            c_q_end_time = quota_list["current"]["end_time"]
            if c_q_end_time > time_now:
                quota_left += quota_list["current"]["quota"]

        if "backup" in quota_list:
            for qt in quota_list["backup"]:
                b_q_quota = qt["quota"]
                b_q_end_time = qt["end_time"]
                if b_q_end_time < time_now:
                    continue

                quota_left += b_q_quota

    except Exception as e:
        xlog.exception("calculate_quota_left %s %r", quota_list, e)

    return quota_left


def call_api(path, req_info):
    if not path.startswith("/"):
        path = "/" + path

    try:
        upload_post_data = json.dumps(req_info)
        upload_post_data = encrypt_data(upload_post_data)

        start_time = time.time()
        while time.time() - start_time < 30:
            content, status, response = g.http_client.request(method="POST", host=g.config.api_server, path=path,
                                                              headers={"Content-Type": "application/json"},
                                                              data=upload_post_data, timeout=5)
            if status >= 400:
                time.sleep(1)
                continue
            else:
                break

        time_cost = time.time() - start_time
        if status != 200:
            reason = "status:%r" % status
            xlog.warn("api:%s fail:%s t:%d", path, reason, time_cost)
            g.last_api_error = reason
            return False, reason

        content = decrypt_data(content)
        if isinstance(content, memoryview):
            content = content.tobytes()

        content = utils.to_str(content)
        try:
            info = json.loads(content)
        except Exception as e:
            g.last_api_error = "parse json fail"
            xlog.warn("api:%s parse json:%s fail:%r", path, content, e)
            return False, "parse json fail"

        res = info["res"]
        if res != "success":
            g.last_api_error = info["reason"]
            xlog.warn("api:%s fail:%s", path, info["reason"])
            return False, info["reason"]

        xlog.info("api:%s success t:%d", path, time_cost * 1000)
        g.last_api_error = ""
        return True, info
    except Exception as e:
        xlog.exception("order e:%r", e)
        g.last_api_error = "%r" % e
        return False, "except:%r" % e


center_login_process = False


def get_app_name():
    app_info_file = os.path.join(root_path, os.path.pardir, "app_info.json")
    try:
        with open(app_info_file, "r") as fd:
            dat = json.load(fd)
        return dat["app_name"]
    except Exception as e:
        xlog.exception("get version fail:%r", e)
    return "XX-Net"


def request_balance(account=None, password=None, is_register=False, update_server=True, promoter=""):
    global center_login_process
    if not g.config.api_server:
        g.server_host = str("%s:%d" % (g.config.server_host, g.config.server_port))
        xlog.info("not api_server set, use server:%s specify in config.", g.server_host)
        return True, "success"

    if is_register:
        login_path = "/register"
        xlog.info("request_balance register:%s", account)
    else:
        login_path = "/login"

    if account is None:
        if not (g.config.login_account and g.config.login_password):
            xlog.debug("request_balance no account")
            return False, "no default account"

        account = g.config.login_account
        password = g.config.login_password

    app_name = get_app_name()
    req_info = {
        "account": account,
        "password": password,
        "protocol_version": "2",
        "promoter": promoter,
        "app_id": app_name,
        "client_version": g.xxnet_version,
        "sys_info": g.system,
    }

    try:
        center_login_process = True
        if g.tls_relay_front:
            g.tls_relay_front.set_x_tunnel_account(account, password)
        if g.seley_front:
            g.seley_front.set_x_tunnel_account(account, password)

        res, info = call_api(login_path, req_info)
        if not res:
            return False, info

        g.quota_list = info["quota_list"]
        g.quota = calculate_quota_left(g.quota_list)
        g.paypal_button_id = info["paypal_button_id"]
        g.plans = info["plans"]
        if g.quota <= 0:
            xlog.warn("no quota")

        if g.config.server_host:
            xlog.info("use server:%s specify in config.", g.config.server_host)
            g.server_host = str(g.config.server_host)
        elif update_server or not g.server_host:
            g.server_host = str(info["host"])
            g.server_port = info["port"]
            xlog.info("update xt_server %s:%d", g.server_host, g.server_port)

        g.selectable = info["selectable"]

        if g.config.update_cloudflare_domains:
            g.http_client.save_cloudflare_domain(info.get("cloudflare_domains"))

        g.promote_code = utils.to_str(info["promote_code"])
        g.promoter = info["promoter"]
        g.balance = info["balance"]
        g.openai_balance = info["openai_balance"]
        g.openai_proxies = info["openai_proxies"]
        g.tls_relays = info["tls_relays"]
        seleys = info.get("seleys", {})
        if g.tls_relay_front:
            g.tls_relay_front.set_ips(g.tls_relays["ips"])
        if g.seley_front:
            g.seley_front.set_hosts(seleys.get("hosts", {}))
        xlog.info("request_balance host:%s port:%d balance:%f quota:%f", g.server_host, g.server_port,
                  g.balance, g.quota)
        return True, "success"
    except Exception as e:
        g.last_api_error = "login center except: %r" % e
        xlog.exception("request_balance e:%r", e)
        return False, e
    finally:
        center_login_process = False


def jwt_login(account, password, node):
    global center_login_process
    g.server_host = str("%s:%d" % (g.config.server_host, g.config.server_port))
    xlog.info("not api_server set, use server:%s specify in config.", g.server_host)
    return True, "success"


login_lock = threading.Lock()


def login_process():
    if not g.session:
        return

    with login_lock:
        if not (g.config.login_account and g.config.login_password):
            xlog.debug("x-tunnel no account")
            return False

        if not g.server_host:
            xlog.debug("session not running, try login..")
            res, reason = request_balance(g.config.login_account, g.config.login_password)
            if not res:
                xlog.warn("x-tunnel request_balance fail when create_conn:%s", reason)
                return False

        if time.time() - g.session.last_send_time > 5 * 60 - 5:
            xlog.info("session timeout, reset it.")
            g.session.stop()

        if g.tls_relay_front:
            g.tls_relay_front.set_x_tunnel_account(g.config.login_account, g.config.login_password)
        if g.seley_front:
            g.seley_front.set_x_tunnel_account(g.config.login_account, g.config.login_password)

        if not g.session.running:
            return g.session.start()

    return True


def create_conn(sock, host, port, log=False):
    if not (g.config.login_account and g.config.login_password):
        time.sleep(1)
        return False

    for _ in range(0, 3):
        if login_process():
            break
        else:
            time.sleep(1)

    return g.session.create_conn(sock, host, port, log)


def update_quota_loop():
    xlog.debug("update_quota_loop start.")

    start_time = time.time()
    last_quota = g.quota
    while g.running and time.time() - start_time < 10 * 60:
        if not g.config.login_account:
            xlog.info("update_quota_loop but logout.")
            return

        request_balance(
            g.config.login_account, g.config.login_password,
            is_register=False, update_server=False)

        if g.quota - last_quota > 1024 * 1024 * 1024:
            xlog.info("update_quota_loop quota updated")
            return

        time.sleep(60)

    xlog.warn("update_quota_loop timeout fail.")
