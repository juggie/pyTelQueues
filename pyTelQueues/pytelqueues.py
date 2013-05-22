#pyTelQueues core class

from pyTelQueues.config import Config
#from pyTelQueues.redisl import Redis - unused atm
from pyTelQueues.telephonyserver import TelephonyServer
from pyTelQueues.callcontroller import CallController
import logging

class pyTelQueues():
    def __init__(self):
        #config
        self._config = Config(self)

        #Telephony Server
        self._telephonyserver = TelephonyServer(self)

        #Telephony Call Controller
        self._callcontroller = CallController(self)

    def config(self):
        return self._config

    def telephonyserver(self):
        return self._telephonyserver

    def callcontroller(self):
        return self._callcontroller
