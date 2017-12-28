import requests
from requests.exceptions import ConnectionError


class MycroftAPI(object):
    URL = "https://0.0.0.0:6712/"

    def __init__(self, api):
        self.api = api
        self.headers = {"Authorization": str(self.api)}

    def hello_world(self):
       try:
           response = requests.get(
               MycroftAPI.URL,
               headers=self.headers, verify=False
           )
           return response.text
       except ConnectionError as e:
           print e
           raise ConnectionError("Could not connect")

    def new_user(self, key, id, name):
        #
        try:
            response = requests.put(
                MycroftAPI.URL+"new_user/"+key+"/"+id+"/"+name,
                headers=self.headers, verify=False
            )
            try:
                return response.json()
            except:
                print response.text
                raise ValueError("Invalid admin api key")
        except ConnectionError as e:
            print e
            raise ConnectionError("Could not connect")

    def get_api(self):
        #
        try:
            response = requests.get(
                MycroftAPI.URL+"get_api",
                headers=self.headers, verify=False
            )
            try:
                return response.json()["api"]
            except:
                print response.text
                raise ValueError("Invalid admin api key")
        except ConnectionError as e:
            print e
            raise ConnectionError("Could not connect")

    def ask_mycroft(self, utterance):
        try:
            response = requests.get(
                MycroftAPI.URL+"ask/"+utterance,
                headers=self.headers, verify=False
            )
            try:
                return response.json()["echo"]
            except:
                print response.text
                raise ValueError("Invalid api key")
        except ConnectionError as e:
            print e
            raise ConnectionError("Could not connect")

ap = MycroftAPI("test_key")
#print ap.hello_world()
#try:
#    print ap.new_user("new_key", "0", "test")
#    print "whoa, anyone can make himself an user"
#except:
#    pass
#try:
#    print ap.get_api()
#    print "whoa, anyone can generate an api key"
#except:
#    pass

#ap = MycroftAPI("admin_key")
print ap.hello_world()
#print ap.new_user("new_key", "0", "test")
#print ap.get_api()
print ap.ask_mycroft("do you work?")
