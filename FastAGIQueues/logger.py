#Logging
import logging,inspect

#needs to be expanded to accomodate levels
class Logger():
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',level=logging.INFO)
        self.Message('Logger started', 'LOGGER')

    def __call__(self, message, type, level = 0):
        self.Message(self, message, type, level)

    def Message(self, message, type, level = 0):
        logging.info('[%s] %s' % (type.ljust(7),message))
