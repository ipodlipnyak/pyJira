import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from src import core 

class JiraCon(core.Connector):
    def getParentName(self, child):
        return self.getTaskData(child)['fields']['customfield_10005']

    def getParentData(self, child):
        parent = self.getParentName(child)
        if parent:
            return self.getTaskData(parent)
        return False 

    def getTaskData(self, task):
        return self.get('rest/api/2/issue/'+task)

def prettyPrint(parsed_json):
    json_str = json.dumps(parsed_json, indent=4, sort_keys=True, ensure_ascii=False)
    print(highlight(json_str, JsonLexer(), TerminalFormatter()))

if __name__ == "__main__" :
    jira = JiraCon()

    prettyPrint(jira.getParentData('RND-8817'))
