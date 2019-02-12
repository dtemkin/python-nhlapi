from nhlapi import config
from abc import abstractmethod


class BaseEndpoint(object):

    def __init__(self):
        self.url_template = "/".join([config.BASE_URL,
                                      "v" + str(config.VERSION)])
        self.request_headers = {}
        self.request_params = {}
        self.data = {"copyright": "NHL and the NHL Shield are "
                                  "registered trademarks of "
                                  "the National Hockey League. "
                                  "NHL and NHL team marks are "
                                  "the property of the NHL and its teams. "
                                  "© NHL 2019. All Rights Reserved."}

    @abstractmethod
    def get(self, *args, **kwargs):
        raise NotImplementedError()

    def __dict__(self):
        return self.data
