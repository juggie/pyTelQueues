#Redis Thread
import threading, redis, platform, json

class CallController():
	def __init__(self, logger, config):
		#some redis setup + start redis thread
		self._callcontroller_thread = CallControllerThread(logger)
		self._callcontroller_thread.daemon = True;
		self._callcontroller_thread.start()

class CallControllerThread(threading.Thread):
	def __init__(self, logger):
		threading.Thread.__init__(self)
		#save logger object
		self._logger = logger

		self._redis = redis.StrictRedis(host='192.168.99.20', port=6379, db=0)
		self._ps = self._redis.pubsub()
		self._redis_global = 'agiqueues.global'
		
		self._call_state = {}
		
	
	def run(self):
		self._ps.psubscribe([self._redis_global])
		self._logger.Message('Call Controller thread starting', 'CALLC')
		self._logger.Message('Subscribed to %s' % self._redis_global, 'CALLC')
		for m in self._ps.listen():
			if m['type'] == 'pmessage' or m['type'] == 'message':
				try:
					message = json.loads(m['data'])
				except (ValueError, UnboundLocalError):
					self._logger.Message('Invalid JSON request', 'CALLC')
					continue
				
				self._logger.Message('Event: %s, ClientMD5: %s, Instance Channel: %s' % (message['event'], message['clientMD5'], message['instance_channel']), 'CALLC')
				if message['event'] == 'ring':
					self._call_state[message['clientMD5']]=[]
					self._redis.publish(message['instance_channel'], json.dumps({'event' : 'answer', 'clientMD5' : message['clientMD5']}))
					self._call_state[message['clientMD5']]=1
				elif message['event'] == 'hangup':
					if message['clientMD5'] in self._call_state: del self._call_state[message['clientMD5']]
				else:
					if self._call_state[message['clientMD5']]==1:
						self._redis.publish(message['instance_channel'], json.dumps({'event' : 'playback', 'parameters': 'tt-monkeys', 'clientMD5' : message['clientMD5']}))
						self._call_state[message['clientMD5']]=2
					elif self._call_state[message['clientMD5']]==2:
						self._redis.publish(message['instance_channel'], json.dumps({'event' : 'hangup', 'clientMD5' : message['clientMD5']}))
						self._call_state[message['clientMD5']]=3
					else:
						pass