from .core import prettyPrint
from PyInquirer import prompt

class PeppermintButler():
    """
    #TODO go through: 
    ask for task or find existing, 
    check if there need for status transition,
    ask for comments
    """
    def __init__(self):
        pass

class Issue():
    def __new__(cls, connector, name):
        r = connector.get('rest/api/2/issue/'+name)
        if 'errorMessages' in r and 'ЗАПРОС НЕ СУЩЕСТВУЕТ' in r['errorMessages']:
            return None

        return super(Issue, cls).__new__(cls)

    def __init__(self, connector, name):
        self.con = connector
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

    def getParent(self):
        return Issue(self.con, self['customfield_10005']) if self['customfield_10005'] else False

    def getParams(self):
        return self.__data.getParams()

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

    def getStatus(self, name = False):
        if name:
            return self.con.get('rest/api/2/status/'+name)

        status_list_all = self.con.get('rest/api/2/status')
        result = []
        for status in status_list_all:
            result.append(status['name'])

        return result

    def setInwork(self):
        new_status = self.getStatus('inwork')
        self['status'] = new_status 
        self.save()

        parent = self.getParent()
        if parent:
            parent['status'] = new_status
            parent.save()


    def getEditMeta(self):
        """ 
        Returns the meta data for editing an issue.
        The fields in the editmeta correspond to the fields in the edit screen for the issue. 
        Fields not in the screen will not be in the editmeta.
        https://docs.atlassian.com/software/jira/docs/api/REST/8.2.2/#api/2/issue-getEditIssueMeta 

        :return: obj DataContainer
        """
        result = self.con.get('rest/api/2/issue/'+self.meta['key']+'/editmeta')
        return DataContainer(result['fields'])

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
        result = {}
        for key in self.__updated:
            result[key] = self[key]
        return result

    def getParams(self):
        return self.__keys

    def toDict(self):
        return self.__data.copy() 

























