
from front_base.config import ConfigBase


class Config(ConfigBase):
    def __init__(self, fn):
        super(Config, self).__init__(fn)

        # front
        self.set_var("front_continue_fail_num", 10)
        self.set_var("front_continue_fail_block", 180)
        self.set_var("allow_set_hosts", 1)

        # http_dispatcher
        # self.set_var("dispather_min_idle_workers", 0)
        self.set_var("dispather_work_min_idle_time", 0)
        self.set_var("dispather_work_max_score", 20000)
        self.set_var("dispather_max_workers", 20)

        # http1
        self.set_var("http1_first_ping_wait", 0)
        self.set_var("http1_ping_interval", 0)
        self.set_var("http1_idle_time", 230)
        self.set_var("http1_max_process_tasks", 999999)
        self.set_var("http2_max_process_tasks", 999999)
        self.set_var("http2_status_to_close", [404])

        # connect_manager
        self.set_var("connection_pool_min", 1)
        self.set_var("max_links_per_ip", 20)
        self.set_var("connect_create_interval", 0)

        self.load()