#Logging
import logging

#needs to be expanded to accomodate levels
class Logger():
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(message)s', datefmt='%m/%d/%Y %H:%M:%S',level=logging.INFO)

    def Message(self, message, type, level = 0):
        logging.info('[%s] %s' % (type.ljust(7),message))
