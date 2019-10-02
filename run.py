import json
from pygments import highlight
from pygments.lexers import JsonLexer
from pygments.formatters import TerminalFormatter
from src.core import Connector, prettyPrint
from src.model import Issue
from PyInquirer import prompt

#TODO interactive select of issue and navigation over it params and action options. Like change status and comments edit

class JiraCon(Connector):
    def getParentName(self, child):
        return self.getTaskData(child)['fields']['customfield_10005']

    def getParentData(self, child):
        parent = self.getParentName(child)
        if parent:
            return self.getTaskData(parent)
        return False 

    #TODO filter possible statuses by current status
    def getNextStatuses(self, issue_type, issue_status):
        all_statuses = self.get('rest/api/2/project/RND/statuses')
        pass

    def getTaskData(self, task):
        return self.get('rest/api/2/issue/'+task)

    # Returns a list of all issue types visible to the user
    def getIssueTypesAll(self):
        return self.get('rest/api/2/issuetype')

if __name__ == "__main__" :
    jira = JiraCon()

    #i = Issue(jira, 'RND-8817')
    #i = Issue(jira, 'RND-8972')
    i = Issue(jira, 'RND-7019')
    i.verboseTransition()
