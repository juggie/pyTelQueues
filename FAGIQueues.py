## AGI Queues
## donnyk@gmail.com
import time, asyncore

#app level imports
from lib.config import Config
from lib.logger import Logger
from lib.redissubscriber import RedisSubscriber
from lib.fastagi import FAGIServer

if __name__=="__main__":
	logger = Logger()
	config = Config(logger)
	redissub = RedisSubscriber(logger, config)
	server = FAGIServer(logger, config)

	try:
		while True: #we attempt to handle one redis event and one socket event per loop
			redisevent = redissub.pop()
			if redisevent != False:
				#fire the received redis event into fastagi.. huzzah
				#add code to confirm clientMD5 exists
				try:
					server.getclient(redisevent['clientMD5']).handle_redis_event(redisevent)
				except KeyError:
					logger.Message("Received redis event for a non-existant channel", 'CORE')
			#poll the hell out of asyncore.. perhaps this is agressive?? unit testing will tell
			asyncore.loop(timeout=0.00001, count=1)
	except KeyboardInterrupt:
		logger.Message("Crtl+C pressed. Shutting down.", 'CORE')
		logger.Stop()