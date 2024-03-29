import re
from .core import prettyPrint, Config, parseTime
from PyInquirer import prompt
from datetime import datetime, timezone, timedelta
from beautifultable import BeautifulTable
from termcolor import colored, COLORS

class PeppermintButler():
    """
    #TODO go through: 
    ask for task or find existing, 
    check if there need for status transition,
    ask for comments
    """

    STATUSES = {
            "inwork" : "3",
            "done" : "5",
            "To do" : "10000",
            "Finished" : "10001",
            "Бэклог" : "10100",
            "Code-review" : "10300",
            "Agreed" : "10469"
            }

    def __init__(self, connector):
        self.con = connector
        self.config = Config()
        self.statuses_groups = DataContainer(self.config.get("statuses_groups"))

    def showKanban(self):
        """
        render kanban
        https://beautifultable.readthedocs.io/en/latest/quickstart.html
        """
        table = BeautifulTable()
        table.set_style(BeautifulTable.STYLE_COMPACT)
        project = self.config.get("project")

        rows_qnt = 0

        groups_list = {}
        for group in self.statuses_groups.getKeys():
            groups_list[group] = []

        for group in self.statuses_groups.getKeys():
            status_list = self.statuses_groups[group]
            statuses_str = ','.join(str(e) for e in status_list)
            jql = "project = "+ project +" and assignee=currentUser() and status in ("+ statuses_str +")"
            tasks_list = []
            for task in self.searchIssues(jql)['issues']:
                task_color = task['fields']['status']['statusCategory']['colorName']
                if task_color not in COLORS.keys():
                    task_color = 'white'
                tasks_list.append(colored(task['key'], task_color, attrs=['bold']))

            groups_list[group] = tasks_list
            if len(tasks_list) > rows_qnt:
                rows_qnt = len(tasks_list)

        for index, group in enumerate(self.statuses_groups.getKeys()):
            tasks_list = groups_list[group]
            rows = []
            r = 0
            while r <= rows_qnt:
                task = tasks_list[r] if r < len(tasks_list) else ''
                rows.append(task)
                r += 1
           
            group = colored(group, 'white', attrs=['bold'])

            table.insert_column(index, group, rows)

        print(table)



    def searchIssues(self, jql):
        """ 
        jql search
        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/search-search
        """
        url = 'rest/api/2/search'
        payload = {
                    "jql": jql, 
                    "startAt": 0,
                    "maxResults": 5,
                }
        return self.con.post(url, payload)

    #TODO when whould i check parent if i transit task to new status?
    def giveMeTask(self):
        task = None
        while not task:
            group = self.askForTaskGroup()
            if not group:
                return

            task_name = self.askForTask(self.statuses_groups[group])
            if task_name == 'none':
                continue 

            if not task_name:
                continue

            task = Issue(self.con, task_name)
            if not task:
                print('not a task')

        task.verboseTransition()

        return task


    def askForTaskGroup(self):
        options = ['none'] + self.statuses_groups.getKeys()
        questions = [
                {
                    'type': 'list',
                    'name': 'group',
                    'message': 'select group',
                    'choices': options 
                    }
                ]
        group = prompt(questions)['group']
        return None if group == 'none' else group


    def askForTask(self, status_list = [3,5]):
        tasks_list = ['none','custom']
        statuses_str = ','.join(str(e) for e in status_list)
        project = self.config.get("project")

        jql = "project = "+ project +" and assignee=currentUser() and status in ("+ statuses_str +")"
        for task in self.searchIssues(jql)['issues']:
            tasks_list.append(task['key'])

        questions = [
                {
                    'type': 'list',
                    'name': 'task_name',
                    'message': 'select task',
                    'choices': tasks_list
                    },
                {
                    'type': 'input',
                    'name': 'task_name',
                    'message': 'type the name',
                    'when': lambda answers: answers['task_name'] == 'custom'
                    }
                ]
        return prompt(questions)['task_name']


class Issue():
    def __new__(cls, connector, name):
        r = connector.get('rest/api/2/issue/'+name)
        if 'errorMessages' in r and 'ЗАПРОС НЕ СУЩЕСТВУЕТ' in r['errorMessages']:
            return None

        return super(Issue, cls).__new__(cls)

    def __init__(self, connector, name):
        self.con = connector
        self.config = Config()
        url = 'rest/api/2/issue/'+name
        data = self.con.get(url)
        
        #TODO Mhe..
        self.meta = {
                'id' : data['id'], 
                'key' : data['key'], 
                'self' : data['self'],
                }

        self.meta['transitions'] = self.getTransitions()
        self.__data = DataContainer(data['fields'])

    def __getitem__(self, key):
        if key in self.meta:
            return self.meta[key]

        return self.__data[key]

    def __setitem__(self, key, value):
        self.__data[key] = value
        return self

    def sync(self):
        """
        sync data with server
        """
        url = 'rest/api/2/issue/'+self['key']
        try:
            data = self.con.get(url)
            self.__data = DataContainer(data['fields'])
            self.meta['transitions'] = self.getTransitions()
        except Exception:
            print("Can't sync")

    def autoTransition(self):
        # By default transit status automatically from Agreed to Inwork
        if self['status']['name'] in self.config.get('autotransitions'):
            self.doTransition(self.config.get('autotransitions')[self['status']['name']])
            self.checkParent()

    def getParent(self):
        return Issue(self.con, self['customfield_10005']) if self['customfield_10005'] else None 
    
    def checkParent(self):
        parent = self.getParent()
        if parent and parent['status']['statusCategory']['id'] != self['status']['statusCategory']['id']:
            print('Parent issue '+parent['key']+' have different status')
            parent.verboseTransition()

    def getParams(self):
        return self.__data.getKeys()

    def getTransitions(self):
        """
        Get a list of the transitions possible for this issue by the current user, 
        along with fields that are required and their types.
        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/issue-getTransitions
        """
        result = []
        raw_list = self.con.get('rest/api/2/issue/'+self.meta['key']+'/transitions')
        return raw_list['transitions']

    def doTransition(self, name, comment = False):
        """
        Perform a transition on an issue. 
        When performing the transition you can update or set other issue fields.
        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/issue-doTransition
        """
        url = 'rest/api/2/issue/'+self['key']+'/transitions'
        next_trans = False
        for trans in self['transitions']:
            if trans['name'] == name:
                next_trans = trans

        if not next_trans:
            return False

        payload = {
                "transition": {
                    "id": next_trans['id']
                    }
                }

        if comment:
            payload['update'] = {
                    'comment' : [
                        {
                            "add": {
                                "body": comment 
                                }
                            }
                        ]
                    }

        #r = self.con.post(url, payload, debug = True)
        #prettyPrint(r)
        self.con.post(url, payload)
        self.sync()
        self.autoTransition()

    def addComment(self, msg):
        """
        Adds a new comment to an issue
        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/issue-addComment
        """
        url = 'rest/api/2/issue/'+ self['key'] +'/comment'
        payload = {
                "body" : msg
                }
        self.con.post(url, payload)
        self.sync()
    
    def addWorklog(self, time_spent, time_started = False, comment = False):
        """
        :time_spent: for example '2h 30m'
        :time_started: datetime object

        Adds a new worklog entry to an issue.
        I.e. the time that had been spended while working on an issue
        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/issue-addWorklog
        """
        url = 'rest/api/2/issue/'+ self['key'] +'/worklog'

        if not time_started:
            time_started = datetime.now(timezone.utc) - parseTime(time_spent)

        payload = {
                "started" : re.sub(r':(..)$', r'\1', time_started.isoformat(timespec = 'milliseconds')),
                "timeSpent" : time_spent
                }

        if comment:
            payload['comment'] = comment

        self.con.post(url, payload)
        self.sync()

# TODO remove this trash
#    def getStatus(self, name = False):
#        if name:
#            return self.con.get('rest/api/2/status/'+name)
#
#        status_list_all = self.con.get('rest/api/2/status')
#        result = []
#        for status in status_list_all:
#            result.append(status['name'])
#
#        return result
#
#    def setInwork(self):
#        new_status = self.getStatus('inwork')
#        self['status'] = new_status 
#        self.save()
#
#        parent = self.getParent()
#        if parent:
#            parent['status'] = new_status
#            parent.save()
#
#
#    def getEditMeta(self):
#        """ 
#        Returns the meta data for editing an issue.
#        The fields in the editmeta correspond to the fields in the edit screen for the issue. 
#        Fields not in the screen will not be in the editmeta.
#        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/issue-getEditIssueMeta 
#
#        :return: obj DataContainer
#        """
#        result = self.con.get('rest/api/2/issue/'+self.meta['key']+'/editmeta')
#        return DataContainer(result['fields'])

    def verboseTransition(self):

        transitions = ['no']
        for trans in self['transitions']:
            transitions.append(trans['name'])

        questions = [
            {
                'type': 'list',
                'name': 'next_transition',
                'message': 'Transit from '+self['status']['name'],
                'choices': transitions
            },
        ]
        
        answers = prompt(questions)

        if answers['next_transition'] != 'no':
            next_transition = answers['next_transition']
            questions = [
                    {
                        'type': 'input',
                        'name': 'comment',
                        'message': 'comment'
                        },
                    ]
            comment = prompt(questions)['comment']
            self.doTransition(next_transition, comment)
            self.checkParent()



    #pretty print params
    def print(self, key = False):
        if key:
            prettyPrint(self[key])
            return

        prettyPrint({'name':'meta','value':self.meta})
        for param in self.__data:
            prettyPrint(param)

    #TODO PUT /rest/api/2/issue/{issueIdOrKey}
    def save(self):
        #return self
        return self.__data.getUpdated()

class DataContainer():
    def __init__(self, parsed_json):
        self.__keys = []
        self.__data = {}
        self.__updated = []
        self.__first = {}
        self.__last = {}
        self.__i = 0
        self.__qnt = len(parsed_json)
        i = 0

        for key, value in parsed_json.items():
            i += 1
            self.__keys.append(key)
            self.__data[key] = {'old_value' : value, 'new_value' : None}
            if i == 1:
                self.__first = {
                        'key' : key,
                        'value' : self.__data[key]
                        }
            if i == self.__qnt:
                self.__last = {
                        'key' : key,
                        'value' : self.__data[key]
                        }

    def __iter__(self):
        return self
    
    def __next__(self):
        self.__i += 1
        if self.__i == self.__qnt:
            raise StopIteration
        key = self.__keys[self.__i - 1]
        return {'name' : key, 'value' : self[key]}

    def __getitem__(self, key):
        if key not in self.__data.keys():
            raise KeyError
        param = self.__data[key]
        value = param['new_value'] if key in self.__updated  else param['old_value']
        
        if type(value) is dict:
            return value.copy()
        
        return value

    def __setitem__(self, key, value):
        if key not in self.__data.keys():
            raise KeyError
        param = self.__data[key]
        param['new_value'] = value
        if key not in self.__updated:
            self.__updated.append(key)

    def len(self):
        return self.__qnt

    def getUpdated(self):
        """
        return params which had been chanched
        """
        result = {}
        for key in self.__updated:
            result[key] = self[key]
        return result

    def getKeys(self):
        return self.__keys

    def toDict(self):
        """
        return dictionary
        """
        return self.__data.copy() 

























