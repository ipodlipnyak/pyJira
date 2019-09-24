import requests
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

class Connector:
    def __init__(self):
        self.config = Config()
        if not self.checkConn():
            self.auth()

    def auth(self):
        payload = '{"username" : "'+self.config.get('username')+'", "password" : "'+self.config.get('password')+'"}'
        result = self.post("rest/auth/1/session",payload)
        self.config.set(result['session']['name'], result['session']['value'])

    def checkConn(self):
        if self.config.get('JSESSIONID'):
            result = self.get('rest/auth/1/session')
            return 'name' in result and result['name'] == self.config.get("username")
        return False

    def post(self, query, payload):
        url = self.config.get('host') + query
        headers = {
                'Content-type': 'application/json'
                }
        r = requests.post(url, headers=headers,data=payload)
        return json.loads(r.text)

    def get(self, query):
        url = self.config.get('host') + query
        cookies = {
                "JSESSIONID" : self.config.get('JSESSIONID')
                }
        r = requests.get(url, cookies=cookies)
        return json.loads(r.text)
