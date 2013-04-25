#Logging thread
import threading, datetime

from Queue import Queue

class Logger():
	def __init__(self):
		self._logger_queue = Queue()
		self._logger_thread = LoggerThread(self._logger_queue)
		self._logger_thread.daemon = True
		self._logger_thread.start()
		self.Message('Logging thread started', 'LOGGER')

	def Message(self, message, type, level = 0):
		self._logger_queue.put({'message' : message, 'type' : type, 'level' : 0})

class LoggerThread(threading.Thread):
	def __init__(self, logger_queue):
		threading.Thread.__init__(self)
		self._logger_queue = logger_queue

	def run(self):
		while True:
				message = self._logger_queue.get() #this code blocks
				print '%s [%s] %s' % (str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), message['type'].ljust(7), message['message'])