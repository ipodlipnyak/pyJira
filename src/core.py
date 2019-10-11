import requests
import json
import re
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from PyInquirer import prompt
from os.path import isfile
from urllib.parse import urlencode, urlparse
from datetime import timedelta

def prettyPrint(parsed_json):
    json_str = json.dumps(parsed_json, indent=4, sort_keys=True, ensure_ascii=False)
    print(highlight(json_str, JsonLexer(), TerminalFormatter()))

def parseTime(time_str):
    """
    Parse a time string e.g. (2h 13m) into a timedelta object.

    https://stackoverflow.com/a/51916936/851699

    :param time_str: A string identifying a duration.  (eg. 2h 13m)
    :return datetime.timedelta: A datetime.timedelta object
    """
    regex = re.compile(r'^((?P<days>[\.\d]+?)d)?((?P<hours>[\.\d]+?)h)?\s*((?P<minutes>[\.\d]+?)m)?\s*((?P<seconds>[\.\d]+?)s)?$')
    parts = regex.match(time_str)
    assert parts is not None, "Could not parse any time information from '{}'.  Examples of valid strings: '8h', '2d 8h 5m 20s', '2m4s'".format(time_str)
    time_params = {name: float(param) for name, param in parts.groupdict().items() if param}
    return timedelta(**time_params)

class Config:
    def __init__(self):
        self._file_name = "config.json"

        if not isfile(self._file_name):
            config_f = open(self._file_name,'w+')
            json.dump({}, config_f, sort_keys=True, indent=4)
            config_f.close()

        config_f = open(self._file_name,'r')
        self._config = json.load(config_f)
        config_f.close()
        self.initParams()

    def initParams(self):
        questions_list = [
            {
                'type': 'input',
                'name': 'host',
                'message': 'What\'s jira host url',
            },
            {
                'type': 'input',
                'name': 'username',
                'message': 'What\'s your username',
            },
            {
                'type': 'password',
                'name': 'password',
                'message': 'What\'s your password',
            },
            {
                'type': 'input',
                'name': 'project',
                'message': 'What\'s your project name',
            }
        ]

        for question in questions_list:
            if not self.get(question['name']):
                answers = prompt([question])
                #TODO ugly
                self.set(question['name'],answers[question['name']])

        if not self.get('statuses_groups'):
            self.set('statuses_groups', {"inwork":[3],"finished":[5]})
       
        # Automatically transit status of issue from Agreed to Inwork
        if not self.get('autotransitions'):
            self.set('autotransitions', {"Agreed": "Inwork"})

    def get(self, key):
        return self._config[key] if key in self._config else False

    def set(self, key, value):
        self._config[key] = value
        self.refreshFile()

    def refreshFile(self):
        config_f = open(self._file_name,'w', encoding='utf-8')
        config_f.truncate()
        json.dump(self._config, config_f, sort_keys=True, indent=4, ensure_ascii=False)
        config_f.close()

class Connector:
    def __init__(self):
        self.config = Config()
        if not self.checkConn():
            self.auth()

    def auth(self):
        payload = {
                "username" : self.config.get('username'),
                "password" : self.config.get('password')
                }
        result = self.post("rest/auth/1/session",payload, auth = False)
        self.config.set(result['session']['name'], result['session']['value'])

    def checkConn(self):
        if self.config.get('JSESSIONID'):
            result = self.get('rest/auth/1/session')
            return 'name' in result and result['name'] == self.config.get("username")
        return False

    def post(self, query, payload, auth = True, debug = False):
        url = self.config.get('host') + query
        headers = {
                'Content-type': 'application/json'
                }

        data = json.dumps(payload)

        if debug:
            prettyPrint({
                'url' : url,
                'headers' : headers,
                'data' : payload
                })
            return

        if auth:
            cookies = {
                    "JSESSIONID" : self.config.get('JSESSIONID')
                    }
            r = requests.post(url, headers=headers, data=data, cookies=cookies)
        else:
            r = requests.post(url, headers=headers, data=data)

        try:
            result = None if r.status_code == 204 else json.loads(r.text)
        except ValueError:
            print(r)
            print(r.text)
            return

        if r.status_code >= 400:
            print(r)
            prettyPrint(r.text)
            if payload:
                prettyPrint(payload)

        return result

    def get(self, query, payload = False, debug = False):
        url = self.config.get('host') + query
        cookies = {
                "JSESSIONID" : self.config.get('JSESSIONID')
                }
        
        if debug:
            prettyPrint({
                'url' : url,
                'cookies' : cookies
                })
            return

        if payload:
            #r = requests.get(url, cookies=cookies, params = urlencode(params))
            r = requests.get(url, cookies=cookies, params=payload)
        else:
            r = requests.get(url, cookies=cookies)

        try:
            result = None if r.status_code == 204 else json.loads(r.text)
        except ValueError:
            print(r)
            print(r.text)
            return
        
        if r.status_code >= 400:
            print(r)
            prettyPrint(r.text)
            if payload:
                prettyPrint(payload)

        return result
