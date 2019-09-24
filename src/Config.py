import json

class Config:
    def __init__(self):
        self._file_name = "config.json"
        config_f = open(self._file_name,'r')
        self._config = json.load(config_f)
        config_f.close()

    def get(self, key):
        return self._config[key] if key in self._config else False

    def set(self, key, value):
        self._config[key] = value
        self.refreshFile()

    def refreshFile(self):
        config_f = open(self._file_name,'w')
        config_f.truncate()
        json.dump(self._config, config_f, sort_keys=True, indent=2)
        config_f.close()
