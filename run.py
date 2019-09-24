import requests
import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from src import Config

class Connector:
    def __init__(self):
        if not self.checkConn():
            self.auth()

    def auth(self):
        url = config.get('host') + "rest/auth/1/session"
        headers = {
                'Content-type': 'application/json'
                }
        payload = '{"username" : "'+config.get('username')+'", "password" : "'+config.get('password')+'"}'
        r = requests.post(url, headers=headers,data=payload)
        parsed = json.loads(r.text)
        config.set(parsed['session']['name'], parsed['session']['value'])

    def checkConn(self):
        if config.get('JSESSIONID'):
            result = self.get('rest/auth/1/session')
            return 'name' in result and result['name'] == config.get("username")
        return False

    def post(self, query, payload):
        url = config.get('host') + query
        headers = {
                'Content-type': 'application/json'
                }
        r = requests.post(url, headers=headers,data=payload)
        return json.loads(r.text)

    def get(self, query):
        url = config.get('host') + query
        cookies = {
                "JSESSIONID" : config.get('JSESSIONID')
                }
        r = requests.get(url, cookies=cookies)
        return json.loads(r.text)

class JiraCon(Connector):

    def getParentName(self, child):
        return self.getTaskData(child)['fields']['customfield_10005']

    def getParentData(self, child):
        parent = self.getParentName(child)
        if parent:
            return self.getTaskData(parent)
        return False 

    def getTaskData(self, task):
        url = config.get('host')+'rest/api/2/issue/'+task
        cookies = {
                "JSESSIONID" : config.get('JSESSIONID') 
                }
        r = requests.get(url, cookies=cookies)
        return json.loads(r.text)

def prettyPrint(parsed_json):
    json_str = json.dumps(parsed_json, indent=4, sort_keys=True, ensure_ascii=False)
    print(highlight(json_str, JsonLexer(), TerminalFormatter()))

if __name__ == "__main__" :
    config = Config.Config()
    jira = JiraCon()

    prettyPrint(jira.getParentData('RND-8817'))
