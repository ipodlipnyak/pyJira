class Issue():
    def __init__(self, connector, name):
        self.con = connector
        url = 'rest/api/2/issue/'+name
        self.__data = DataContainer(self.con.get(url))

    def get(self, key):
        return self.__data.get(key)

    def set(self, key, value):
        self.__data.set(key, value)
        return self

    def getParent(self):
        return Issue(self.con, self.get('customfield_10005')) if self.get('customfield_10005') else False

    def getParams(self):
        return self.__data.getParams()

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

        for key, value in parsed_json['fields'].items():
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
        return self.__data[key]

    def len(self):
        return self.__qnt

    def get(self, key):
        param = self.__data[key]
        return param['new_value'] if key in self.__updated  else param['old_value']

    #TODO FUCK setter had no sense if getter return reference to param
    def set(self, key, value):
        param = self.__data[key]
        param['new_value'] = value
        if key not in self.__updated:
            self.__updated.append(key)

    def getUpdated(self):
        result = {}
        for key in self.__updated:
            result[key] = self.__data[key]
        return result

    def getParams(self):
        return self.__keys























