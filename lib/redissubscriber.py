#Redis Thread
import threading, redis, platform, json
from collections import deque

class RedisSubscriber():
	def __init__(self, logger, config):
		#lock and deque
		self._redissub_lock = threading.Lock()
		self._redissub_queue = deque()
		
		#some redis setup + start redis thread
		self._redissub_instance_channel = 'agiqueues.%s' % config.instancename #get instance name from config, default to hostname
		self._redissub_thread = RedisSubscriberThread(self._redissub_lock, self._redissub_queue, self._redissub_instance_channel, logger)
		self._redissub_thread.daemon = True;
		self._redissub_thread.start()

	def pop(self):
		self._redissub_lock.acquire()
		try: 
			event = self._redissub_queue.pop()
		except IndexError:
			self._redissub_lock.release()
			return False
		self._redissub_lock.release()
		return event	

class RedisSubscriberThread(threading.Thread):
	def __init__(self, redissub_lock, redissub_queue, instancechannelname, logger):
		threading.Thread.__init__(self)
		#save logger object
		self._logger = logger

		self._redissub_lock = redissub_lock
		self._redissub_queue = redissub_queue
		self._redis = redis.StrictRedis(host='192.168.99.20', port=6379, db=0)
		self._ps = self._redis.pubsub()
		self._redis_client = instancechannelname
		self._redis_global = 'agiqueues.global'
		
	
	#add code to fire off events into a queue to be serviced
	def run(self):
		self._ps.psubscribe([self._redis_client])
		self._logger.Message('Redis subscriber thread starting', 'RTHREAD')
		self._logger.Message('Subscribed to %s' % self._redis_client, 'RTHREAD')
		for m in self._ps.listen():
			if m['type'] == 'pmessage' or m['type'] == 'message':
				self._redissub_lock.acquire()
				#modify this to ensure it does not fail if json is invalid.
				self._redissub_queue.append(json.loads(m['data']))
				self._redissub_lock.release()