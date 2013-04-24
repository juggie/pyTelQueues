#Logging thread
import threading, datetime
from collections import deque

class LoggerStop():
	def __init__(self):
		self._logger_run = True
		
	def Stop(self):
		self._logger_run = False

	def Run(self):
		return self._logger_run

class Logger():
	def __init__(self):
		self._logger_lock = threading.Lock()
		self._logger_queue = deque()
		self._logger_thread_stop = LoggerStop()
		self._logger_thread = LoggerThread(self._logger_lock, self._logger_queue, self._logger_thread_stop)
		self._logger_thread.start()
		self.Message('Logging thread started', 'LOGGER')

	def Message(self, message, type, level = 0):
		self._logger_lock.acquire()
		self._logger_queue.append({'message' : message, 'type' : type, 'level' : 0})
		self._logger_lock.release()

	def Stop(self):
		self._logger_thread_stop.Stop()

class LoggerThread(threading.Thread):
	def __init__(self, logger_lock, logger_queue, thread_stop):
		self._logger_lock = logger_lock
		self._logger_queue = logger_queue
		threading.Thread.__init__(self)
		self._thread_stop = thread_stop

	def run(self):
		while self._thread_stop.Run():
			self._logger_lock.acquire()
			while True:
				try: 
					message = self._logger_queue.pop()
					print '%s [%s] %s' % (str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")), message['type'].ljust(7), message['message'])
				except IndexError:
					break
			self._logger_lock.release()