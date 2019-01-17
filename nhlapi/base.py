from nhlapi import config

class BaseEndpoint(object):

    def __init__(self):
        self.url_template = "/".join([config.BASE_URL,
                                      "v" + str(config.VERSION)])
        self.headers = {}
        self.params = {}
        self.data = None
