## AGI Queues
## donnyk@gmail.com
import time, asyncore

#app level imports
from lib.config import Config
from lib.logger import Logger
from lib.redissubscriber import RedisSubscriber
from lib.fastagi import FAGIServer
from lib.callcontroller import CallController

if __name__=="__main__":
	logger = Logger()
	config = Config(logger)
	redissub = RedisSubscriber(logger, config)
	fagiserver = FAGIServer(logger, config)
	callcontroller = CallController(logger, config)

	try:
		while True:
			#I dont like this loop much and I am investigating using another approach. 
			redisevent = redissub.pop()
			if redisevent != False:
				#fire the received redis event into fastagi.. huzzah
				try:
					fagiserver.getclient(redisevent['clientMD5']).handle_redis_event(redisevent)
				except KeyError:
					logger.Message("Received redis event for a non-existant channel", 'CORE')
			#poll the hell out of asyncore.. perhaps this is agressive?? unit testing will tell
			asyncore.loop(timeout=0.001, count=1)
	except KeyboardInterrupt:
		logger.Message("Crtl+C pressed. Shutting down.", 'CORE')
		
		#honestly, we should be signaling all threads to die and joining them here
		#to ensure they all end sucessfully.  However that is not the case today
		#so I sleep for 1 second to allow the logger to catch the final messages 
		time.sleep(1)