
from front_base.http2_connection import Http2Worker


class GaeHttp2Worker(Http2Worker):
    def __init__(self, logger, ip_manager, config, ssl_sock, close_cb, retry_task_cb, idle_cb, log_debug_data,
                 stream_class=None):
        super(GaeHttp2Worker, self).__init__(logger, ip_manager, config, ssl_sock, close_cb, retry_task_cb, idle_cb,
                                             log_debug_data)

    def get_host(self, task_host):
        return self.ssl_sock.host