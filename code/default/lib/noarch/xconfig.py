
import time
import json
import os
import xlog


class Config(object):
    def __init__(self, config_path):
        self.last_load_time = time.time()
        self.default_config = {}
        self.file_config = {}
        self.config_path = config_path
        self.set_default()

    def set_default(self):
        pass

    def check_change(self):
        if os.path.getmtime(self.config_path) > self.last_load_time:
            self.load()
            xlog.info("reload config %s", self.config_path)

    def load(self):
        self.last_load_time = time.time()
        if os.path.isfile(self.config_path):
            with open(self.config_path, 'r') as f:
                content = f.read()
                self.file_config = json.loads(content)

        for var_name in self.default_config:
            if self.file_config and var_name in self.file_config:
                setattr(self, var_name, self.file_config[var_name])
            else:
                setattr(self, var_name, self.default_config[var_name])

    # only save var not same with default
    def save(self):
        for var_name in self.default_config:
            if getattr(self, var_name, None) == self.default_config[var_name]:
                if var_name in self.file_config:
                    del self.file_config[var_name]
            else:
                self.file_config[var_name] = getattr(self, var_name)

        with open(self.config_path, "w") as f:
            f.write(json.dumps(self.file_config, indent=2))

    def set_var(self, var_name, default_value):
        self.default_config[var_name] = default_value
