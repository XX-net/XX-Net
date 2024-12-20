import sys
import os

import env_info
data_path = env_info.data_path
data_xtunnel_path = os.path.join(data_path, 'x_tunnel')

import xconfig
from xlog import getLogger
xlog = getLogger("x_tunnel")


def load_config():
    if len(sys.argv) > 2 and sys.argv[1] == "-f":
        config_path = sys.argv[2]
    else:
        config_path = os.path.join(data_xtunnel_path, 'client.json')

    xlog.info("use config_path:%s", config_path)

    config = xconfig.Config(config_path)

    config.set_var("log_level", "DEBUG")
    config.set_var("upload_logs", True)
    config.set_var("write_log_file", 0)
    config.set_var("save_start_log", 1500)
    config.set_var("show_debug", 0)
    config.set_var("delay_collect_log", 3 * 60)
    config.set_var("delay_collect_log2", 30)

    config.set_var("encrypt_data", 0)
    config.set_var("encrypt_password", "encrypt_pass")
    config.set_var("encrypt_method", "aes-256-cfb")

    config.set_var("api_server", "center.xx-net.org")
    config.set_var("scan_servers", ["scan1"])
    config.set_var("server_host", "")
    config.set_var("server_port", 443)
    config.set_var("use_https", 1)
    config.set_var("port_range", 1)

    config.set_var("login_account", "")
    config.set_var("login_password", "")

    config.set_var("conn_life", 30)

    config.set_var("socks_host", "127.0.0.1")
    config.set_var("socks_port", 1080)
    config.set_var("update_cloudflare_domains", True)

    # performance parameters
    # range 2 - 100
    config.set_var("concurent_thread_num", 20)

    # min roundtrip on road if connectoin exist
    config.set_var("min_on_road", 3)

    config.set_var("server_time_max_deviation", 0.6)

    config.set_var("send_timeout_retry", 4)

    config.set_var("server_download_timeout_retry", 4)

    # range 1 - 1000, ms
    config.set_var("send_delay", 10)

    # range 1 - 20000, ms
    config.set_var("resend_timeout", 5000)

    # range 1 - resend_timeout, ms
    config.set_var("ack_delay", 300)

    # max 10M
    config.set_var("max_payload", 256 * 1024)

    # range 1 - 30
    config.set_var("roundtrip_timeout", 25)

    config.set_var("network_timeout", 10)

    config.set_var("windows_size", 10 * 1024 * 1024)  # will recalulate based on: max_payload * concurent_thread_num *2

    # reporter
    config.set_var("timeout_threshold", 2)
    config.set_var("report_interval", 5 * 60)

    config.set_var("enable_gae_proxy", 0)
    config.set_var("enable_cloudflare", 1)
    config.set_var("enable_cloudfront", 0)
    config.set_var("enable_seley", 1)
    config.set_var("enable_tls_relay", 1)
    config.set_var("enable_direct", 0)
    config.set_var("local_auto_front", 1)

    config.load()

    config.windows_ack = 0.05 * config.windows_size
    config.windows_size = config.max_payload * config.concurent_thread_num * 2
    xlog.info("X-Tunnel window:%d", config.windows_size)

    if config.local_auto_front:
        if "localhost" in config.server_host or "127.0.0.1" in config.server_host:
            config.enable_cloudflare = 0
            config.enable_tls_relay = 0
            config.enable_seley = 0
            config.enable_direct = 1
            xlog.info("Only enable Direct front for localhost")

    if config.write_log_file:
        xlog.log_to_file(os.path.join(data_path, "client.log"))

    xlog.setLevel(config.log_level)
    xlog.set_buffer(200)
    xlog.save_start_log = config.save_start_log
    return config
