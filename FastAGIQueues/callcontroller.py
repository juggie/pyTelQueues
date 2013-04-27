#Redis Thread
import threading, redis, platform, json

class CallController():
	def __init__(self, logger, config, redis):
		#store class input
		self._logger, self._config, self._redis = (logger, config, redis)

		#start call controller thread
		self._callcontroller_thread = CallControllerThread(self._logger, self._config, self._redis)
		self._callcontroller_thread.daemon = True;
		self._callcontroller_thread.start()

		self._logger.Message('Call controller started', 'CALLC')

class CallControllerThread(threading.Thread):
	def __init__(self, logger, config, redis):
		threading.Thread.__init__(self)
		#save logger object
		self._logger, self._config, self._redis = (logger, config, redis)

		#call state
		self._call_state = {}
		
		#redis
		self._redis = redis
		self._redis_subid = self._redis.subscribe(self._config.redisglobalchannel)
	
	def run(self):
		while True:
			message = self._redis.subscriber_pop(self._redis_subid)
			if message == False:
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
