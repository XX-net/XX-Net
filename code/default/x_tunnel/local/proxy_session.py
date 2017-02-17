import time
import json
import threading
import struct
import urlparse

from xlog import getLogger
xlog = getLogger("x_tunnel")

from simple_http_client import HTTP_client
import utils
import base_container
import encrypt
import global_var as g


def encrypt_data(data):
    if g.config.encrypt_data:
        return encrypt.Encryptor(g.config.encrypt_password, g.config.encrypt_method).encrypt(data)
    else:
        return data


def decrypt_data(data):
    if g.config.encrypt_data:
        return encrypt.Encryptor(g.config.encrypt_password, g.config.encrypt_method).decrypt(data)
    else:
        return data


class ProxySession():
    def __init__(self):
        self.upload_task_queue = base_container.BlockSendPool(max_payload=g.config.block_max_size, send_delay=0)
        self.ack_pool = base_container.AckPool()
        self.mutex = threading.Lock()  # lock for conn_id, sn generation, on_road_num change,
        self.download_order_queue = base_container.BlockReceivePool(process_callback=self.download_data_processor)
        self.running = False
        self.start()

    def start(self):
        self.ack_pool.reset()
        self.download_order_queue.reset()

        self.roundtrip_thread = {}

        self.session_id = utils.generate_random_lowercase(8)
        self.last_conn_id = 0
        self.last_transfer_no = 0
        self.conn_list = {}
        self.transfer_list = {}
        self.last_roundtrip_time = 0
        self.on_road_num = 0
        self.last_download_data_time = 0
        self.traffic = 0

        if not self.login_session():
            xlog.warn("x-tunnel session not start")
            return False

        self.running = True
        self.upload_task_queue.start()

        server_port = g.server_port
        for i in range(0, g.config.concurent_thread_num):
            if g.config.port_range > 1:
                server_port += 1
                if server_port > g.server_port + g.config.port_range:
                    server_port = g.server_port
            server_address = (g.server_host, server_port)
            self.roundtrip_thread[i] = threading.Thread(target=self.normal_roundtrip_worker, args=(server_address,))
            self.roundtrip_thread[i].daemon = True
            self.roundtrip_thread[i].start()
        return True

    def stop(self):
        if not self.running:
            #xlog.warn("stop but not running")
            return

        self.running = False
        self.session_id = ""
        self.balance = 0
        self.close_all_connection()
        self.upload_task_queue.stop()

        #xlog.debug("begin join roundtrip_thread")
        for i in self.roundtrip_thread:
            # xlog.debug("begin join %d", i)
            rthead = self.roundtrip_thread[i]
            if rthead is threading.current_thread():
                # xlog.debug("%d is self", i)
                continue
            rthead.join()
            # xlog.debug("end join %d", i)
        #xlog.debug("end join roundtrip_thread")

    def reset(self):
        xlog.debug("session reset")
        self.stop()
        self.start()

    def status(self):
        out_string = "session_id:%s<br>\n" % self.session_id

        out_string += "running:%d<br>\n" % self.running
        out_string += "last_roundtrip_time:%d<br>\n" % (time.time() - self.last_roundtrip_time)
        out_string += "last_download_data_time:%d<br>\n" % (time.time() - self.last_download_data_time)
        out_string += "last_conn_id:%d<br>\n" % self.last_conn_id
        out_string += "last_transfer_no:%d<br>\n" % self.last_transfer_no

        out_string += "on_road_num:%d<br>\n" % self.on_road_num
        out_string += "transfer_list:<br>\r\n"
        for transfer_no in sorted(self.transfer_list.iterkeys()):
            transfer = self.transfer_list[transfer_no]
            if "start" in self.transfer_list[transfer_no]:
                time_way = " t:" + str((time.time() - self.transfer_list[transfer_no]["start"]))
            else:
                time_way = ""
            out_string += "[%d] %s %s<br>\r\n" % (transfer_no, json.dumps(transfer), time_way)

        out_string += "<br>\n" + self.upload_task_queue.status()
        out_string += "<br>\n" + self.download_order_queue.status()

        out_string += "<br>\n" + self.ack_pool.status()
        for conn_id in self.conn_list:
            out_string += "<br>\n" + self.conn_list[conn_id].status()

        return out_string

    def login_session(self):
        if len(g.server_host) == 0 or g.server_port == 0:
            return False

        try:
            start_time = time.time()

            magic = "P"
            pack_type = 1
            upload_data_head = struct.pack("<cBB8sIHII", magic, g.protocol_version, pack_type, str(self.session_id),
                                           g.config.block_max_size, g.config.send_delay, g.config.windows_size,
                                           g.config.windows_ack)
            upload_data_head += struct.pack("<H", len(g.config.login_account)) + str(g.config.login_account)
            upload_data_head += struct.pack("<H", len(g.config.login_password)) + str(g.config.login_password)

            upload_post_data = encrypt_data(upload_data_head)

            http_client = HTTP_client((g.server_host, g.server_port), g.proxy, g.config.use_https,
                                      g.config.conn_life, cert=g.cert)
            content, status, heads = http_client.request(method="POST", path="data", data=upload_post_data,
                                                         timeout=g.config.roundtrip_timeout)

            time_cost = time.time() - start_time
            if status != 200:
                g.last_api_error = "session server login fail:%r" % status
                xlog.warn("login session fail, status:%r", status)
                return False

            if len(content) < 6:
                xlog.error("login data len:%d fail", len(content))
                return False

            info = decrypt_data(content)
            magic, protocol_version, pack_type, res, message_len = struct.unpack("<cBBBH", info[:6])
            message = info[6:]
            if magic != "P" or protocol_version != 1 or pack_type != 1:
                xlog.error("login_session time:%d head error:%s", 1000 * time_cost, utils.str2hex(info[:6]))
                return False

            if res != 0:
                g.last_api_error = "session server login fail, code:%d msg:%s" % (res, message)
                xlog.warn("login_session time:%d fail, res:%d msg:%s", 1000 * time_cost, res, message)
                return False

            g.last_api_error = ""
            xlog.info("login_session time:%d msg:%s", 1000 * time_cost, message)
            return True
        except Exception as e:
            xlog.exception("login_session e:%r", e)
            return False

    def create_conn(self, sock, host, port):
        if not self.running:
            #xlog.warn("session not running, can't connect")
            if not self.start():
                return None

        self.mutex.acquire()
        self.last_conn_id += 1
        conn_id = self.last_conn_id
        self.mutex.release()

        seq = 0
        cmd_type = 0  # create connection
        sock_type = 0  # TCP
        data = struct.pack("<IBBH", seq, cmd_type, sock_type, len(host)) + host + struct.pack("<H", port)
        self.send_conn_data(conn_id, data)

        self.conn_list[conn_id] = base_container.Conn(self, conn_id, sock, host, port, g.config.windows_size,
                                                      g.config.windows_ack, True, xlog)
        return conn_id

    def close_all_connection(self):
        xlog.info("start close all connection")
        conn_list = dict(self.conn_list)
        for conn_id in conn_list:
            try:
                xlog.debug("stopping conn_id:%d", conn_id)
                self.conn_list[conn_id].stop(reason="system reset")
            except Exception as e:
                xlog.warn("stopping conn_id:%d fail:%r", conn_id, e)
                pass
        # self.conn_list = {}
        xlog.debug("stop all connection finished")

    def remove_conn(self, conn_id):
        xlog.debug("remove conn_id:%d", conn_id)
        try:
            del self.conn_list[conn_id]
        except:
            pass

    def send_conn_data(self, conn_id, data, no_delay=False):
        if not self.running:
            return

        # xlog.debug("upload conn_id:%d, len:%d", conn_id, len(data))
        buf = base_container.WriteBuffer()
        buf.append(struct.pack("<BII", 2, 4 + len(data), conn_id))
        buf.append(data)
        self.upload_task_queue.put(buf, no_delay)

    def download_data_processor(self, data):
        try:
            while len(data):
                data_type, data_len = struct.unpack("<BI", data.get(5))
                if data_type == 2:  # data:
                    conn_id = struct.unpack("<I", data.get(4))[0]
                    payload = data.get_buf(data_len - 4)
                    if conn_id not in self.conn_list:
                        xlog.debug("DATA conn_id %d not in list", conn_id)
                    else:
                        # xlog.debug("down conn:%d len:%d", conn_id, len(payload))
                        self.conn_list[conn_id].put_cmd_data(payload)
                else:
                    raise Exception("process_block, unknown type:%d" % data_type)
        except Exception as e:
            xlog.exception("download_data_processor:%r", e)

    def touch_roundtrip(self):
        self.upload_task_queue.put("")

    def get_transfer_no(self):
        with self.mutex:
            self.last_transfer_no += 1
            transfer_no = self.last_transfer_no

        return transfer_no

    def normal_roundtrip_worker(self, server_address):
        last_roundtrip_download_size = 0

        http_client = HTTP_client(server_address, g.proxy, g.config.use_https, g.config.conn_life, cert=g.cert)

        while self.running:

            if self.on_road_num > g.config.concurent_thread_num * 0.8:
                block = True
            elif last_roundtrip_download_size > g.config.block_max_size:
                block = False
            elif len(self.conn_list) > 0 and self.on_road_num < 1:
                # keep at least one pulling thread
                block = False
            elif len(self.conn_list) > 0 and time.time() - self.last_download_data_time < 120 and \
                            self.on_road_num < g.config.concurent_thread_num * 0.1:
                # busy, have data download
                block = False
            else:
                block = True

            if block:
                get_timeout = 24 * 3600
            else:
                get_timeout = 0

            # self.transfer_list[transfer_no]["stat"] = "get local data"
            upload_data, send_sn = self.upload_task_queue.get(get_timeout)
            transfer_no = self.get_transfer_no()
            self.transfer_list[transfer_no] = {}
            self.transfer_list[transfer_no]["sn"] = send_sn
            send_data_len = len(upload_data)
            upload_ack_data = self.ack_pool.get()
            send_ack_len = len(upload_ack_data)
            magic = "P"
            pack_type = 2

            if self.on_road_num > g.config.concurent_thread_num * 0.8:
                server_timeout = 0
            else:
                server_timeout = g.config.roundtrip_timeout / 2

            upload_data_head = struct.pack("<cBB8sIIBIH", magic, g.protocol_version, pack_type, str(self.session_id),
                                           transfer_no,
                                           send_sn, server_timeout, send_data_len, send_ack_len)
            upload_post_buf = base_container.WriteBuffer(upload_data_head)
            upload_post_buf.append(upload_data)
            upload_post_buf.append(upload_ack_data)
            upload_post_data = str(upload_post_buf)
            upload_post_data = encrypt_data(upload_post_data)
            try_no = 0
            while self.running:
                try_no += 1
                sleep_time = min(try_no, 30)

                self.last_roundtrip_time = time.time()
                start_time = time.time()

                with self.mutex:
                    self.on_road_num += 1

                # xlog.debug("start roundtrip transfer_no:%d send_data_len:%d ack_len:%d", transfer_no, send_data_len, send_ack_len)
                try:
                    self.transfer_list[transfer_no]["try"] = try_no
                    self.transfer_list[transfer_no]["stat"] = "request"
                    self.transfer_list[transfer_no]["start"] = time.time()
                    content, status, response = http_client.request(method="POST", path="data", data=upload_post_data,
                                                                    timeout=g.config.roundtrip_timeout)

                    traffic = len(upload_post_data) + len(content) + 645
                    self.traffic += traffic
                    g.quota -= traffic
                except Exception as e:
                    xlog.exception("request except:%r retry %d", e, try_no)

                    time.sleep(sleep_time)
                    if transfer_no not in self.transfer_list:
                        break
                    else:
                        continue
                finally:
                    with self.mutex:
                        self.on_road_num -= 1

                if status == 405:  # session_id not exist on server
                    if self.running:
                        xlog.warn("server session_id not exist, start reset session")
                        self.reset()
                    return
                elif status == 200:
                    recv_len = len(content)
                    if recv_len < 6:
                        xlog.error("roundtrip time:%d transfer_no:%d sn:%d send:%d len:%d status:%r retry:%d",
                                   (time.time() - start_time) * 1000, transfer_no, send_sn, send_data_len, len(content),
                                   status, try_no)
                        continue

                    content = decrypt_data(content)

                    data = base_container.ReadBuffer(content)

                    magic, version, pack_type = struct.unpack("<cBB", data.get(3))
                    if magic != "P" or version != g.protocol_version:
                        xlog.error("get data head:%s", utils.str2hex(content[:2]))
                        time.sleep(100)
                        break

                    if pack_type == 3:  # error report
                        error_code, message_len = struct.unpack("<BH", data.get(3))
                        message = data.get(message_len)
                        xlog.warn("error report code:%d, msg:%s", error_code, message)
                        if error_code == 1:  # no quota
                            xlog.warn("login x_server error:no quota")
                            self.stop()
                            return
                        else:
                            xlog.error("unknown error code:%d", error_code)
                            return

                    if pack_type != 2:  # normal download traffic pack
                        xlog.error("pack type:%d", pack_type)
                        time.sleep(100)
                        break

                    sn, time_cost = struct.unpack("<II", data.get(8))

                    xlog.debug(
                        "roundtrip time:%d cost:%d transfer_no:%d send_sn:%d send:%d recv_sn:%d rcv:%d status:%r",
                        (time.time() - start_time) * 1000, time_cost, transfer_no, send_sn, send_data_len, sn,
                        len(content), status)

                    data_len = len(data)
                    if (sn > 0 and data_len == 0) or (sn == 0 and data_len > 0):
                        xlog.warn("get sn:%d len:%d %s", sn, data_len, data)

                    if sn:
                        self.last_download_data_time = time.time()
                        last_roundtrip_download_size = data_len
                        # xlog.debug("get sn:%d len:%d", sn, data_len)
                        self.download_order_queue.put(sn, data)

                        ack_pak = struct.pack("<Q", transfer_no)
                        self.ack_pool.put(ack_pak)
                    else:
                        last_roundtrip_download_size = 0

                    if send_data_len == 0 and data_len > g.config.block_max_size:
                        need_more_thread_num = int(g.config.concurent_thread_num * 0.5 - self.on_road_num)
                        if need_more_thread_num > 0:
                            for j in range(0, need_more_thread_num):
                                if self.on_road_num > g.config.concurent_thread_num * 0.5:
                                    break
                                self.touch_roundtrip()

                    break
                else:
                    xlog.warn("roundtrip time:%d transfer_no:%d send_sn:%d send:%d status:%r retry:%d",
                              (time.time() - start_time) * 1000, transfer_no, send_sn, send_data_len, status, try_no)
                    time.sleep(sleep_time)

            del self.transfer_list[transfer_no]
        xlog.info("roundtrip port:%d thread exit", server_address[1])


def calculate_quota_left(quota_list):
    time_now = int(time.time())
    quota_left = 0

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

    return quota_left


def get_api_server_http_client():
    api_server = urlparse.urlparse(g.config.api_server)
    http_client = HTTP_client((api_server.hostname, api_server.port), g.proxy, g.config.use_https, g.config.conn_life,
                              cert=g.cert)
    return http_client


def call_api(path, req_info):
    try:
        start_time = time.time()
        upload_post_data = json.dumps(req_info)

        upload_post_data = encrypt_data(upload_post_data)
        http_client = get_api_server_http_client()

        content, status, heads = http_client.request(method="POST", path=path,
                                                     header={"Content-Type": "application/json"},
                                                     data=upload_post_data, timeout=g.config.roundtrip_timeout)

        time_cost = time.time() - start_time
        if status != 200:
            reason = "status:%r" % status
            xlog.warn("api:%s fail:%s t:%d", path, reason, time_cost)
            g.last_api_error = reason
            return False, reason


        content = decrypt_data(content)
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


def request_balance(account, password, is_register=False, update_server=True):
    if is_register:
        login_path = "register"
        xlog.info("request_balance register:%s", account)
    else:
        login_path = "login"

    req_info = {"account": account, "password": password}

    res, info = call_api(login_path, req_info)
    if not res:
        return False, info

    g.quota_list = info["quota_list"]
    g.quota = calculate_quota_left(g.quota_list)
    if g.quota <= 0:
        xlog.warn("no quota")

    if update_server:
        g.server_host = str(info["host"])
        g.server_port = info["port"]
        xlog.info("update xt_server %s:%d", g.server_host, g.server_port)

    g.balance = info["balance"]
    xlog.info("request_balance host:%s port:%d balance:%f quota:%f", g.server_host, g.server_port,
              g.balance, g.quota)
    return True, "success"
