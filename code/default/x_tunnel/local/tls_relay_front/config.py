
from front_base.config import ConfigBase


class Config(ConfigBase):
    def __init__(self, fn):
        super(Config, self).__init__(fn)

        # front
        self.set_var("front_continue_fail_num", 10)
        self.set_var("front_continue_fail_block", 10)
        self.set_var("allow_set_ips", 1)

        # https_dispatcher
        self.set_var("dispather_min_idle_workers", 0)
        self.set_var("dispather_work_max_score", 20000)
        self.set_var("dispather_min_workers", 1)
        self.set_var("dispather_max_workers", 60)
        self.set_var("dispather_connect_all_workers_on_startup", 1)

        # connect_manager
        self.set_var("https_connection_pool_min", 0)
        self.set_var("max_links_per_ip", 1)
        self.set_var("https_connection_pool_max", 20)
        self.set_var("connect_create_interval", 0)

        # connect_creator
        self.set_var("socket_timeout", 2)
        self.set_var("connect_force_http2", 1)

        # http 2 worker
        self.set_var("http2_status_to_close", [500])
        self.set_var("http2_idle_ping_min_interval", 110)
        self.set_var("http2_max_process_tasks", 9900)

        self.load()
