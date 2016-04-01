

import json
import os



class Config(object):
    default_config = {}
    file_config = {}

    def __init__(self, config_path):
        self.config_path = config_path

    def load(self):
        if os.path.isfile(self.config_path):
            with file(self.config_path, 'r') as f:
                self.file_config = json.loads(f.read())

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

        with file(self.config_path, "w") as f:
            f.write(json.dumps(self.file_config, indent=2))

    def set_var(self, var_name, default_value):
        self.default_config[var_name] = default_value

