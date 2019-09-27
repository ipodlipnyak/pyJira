from .core import prettyPrint

class Issue():
    def __init__(self, connector, name):
        self.con = connector
        url = 'rest/api/2/issue/'+name
        data = self.con.get(url)
        
        #TODO Mhe..
        self.meta = {'id' : data['id'], 'key' : data['key'], 'self' : data['self']}

        self.__data = DataContainer(data['fields'])

    def __getitem__(self, key):
        return self.__data[key]

    def __setitem__(self, key, value):
        self.__data[key] = value
        return self

    def getParent(self):
        return Issue(self.con, self['customfield_10005']) if self['customfield_10005'] else False

    def getParams(self):
        return self.__data.getParams()

    #pretty print params
    def print(self, key = False):
        if key == 'meta':
            prettyPrint(self.meta)
            return

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
























