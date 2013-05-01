#Redis Thread
#Does not handle multiple subscriptions to the same queue name (yet)
import threading, redis, platform, json, Queue, datetime, hashlib

class Redis():
    def __init__(self, logger, config):
        #store class input
        self._logger, self._config = (logger, config)
        #message queue
        self._sub_queue = {}
        #map
        self._channelmap = {}
        #message thread state
        self._threadstarted = False
        #internal messaging channel
        self._intmessaging = hashlib.md5('%s%s' % (config.redisinstancechannel, datetime.datetime.now())).hexdigest()
        #int messaging ok?
        self._intmessaging_ready = threading.Event()

        #redis connection for lib
        #TODO: move parameters to config, also missing is catching errors
        self._redis = redis.StrictRedis(host=self._config.redisip, port=self._config.redisport, db=0)
        self._logger.Message('Connected to redis', 'REDIS')

        self._sub_thread = RedisSubscriberThread(self._sub_queue, self._logger, self._config, self._intmessaging, self._intmessaging_ready, self._channelmap)
        self._sub_thread.daemon = True;
        self._sub_thread.start()

    def subscriber_pop_nowait(self, id):
        try:
            event = self._sub_queue[id].get_nowait()
        except (Queue.Empty, KeyError):
            return False
        return event

    def subscriber_pop(self, id):
        try:
            event = self._sub_queue[id].get()
        except (KeyError):
            return False
        return event


    def _getId(self):
        return hashlib.md5('%s' % datetime.datetime.now()).hexdigest()

    def publish(self, channel, event):
        self._redis.publish(channel, event)

    def subscribe(self, channel, id = False, pattern = False):
        self._intmessaging_ready.wait()
        if id == False:
            id = self._getId()
        self.publish(self._intmessaging, json.dumps({'subscribe': channel, 'id': id, 'pattern': pattern}))
        return id

    def unsubscribe(self, channel, id, pattern = False):
        self._intmessaging_ready.wait()
        self.publish(self._intmessaging, json.dumps({'unsubscribe': channel, 'id': id, 'pattern': pattern}))

class RedisSubscriberThread(threading.Thread):
    def __init__(self, sub_queue, logger, config, intmessaging, intmessagingready, channelmap):
        threading.Thread.__init__(self)
        self._sub_queue, self._logger, self._config, self._intmessaging, self._intmessaging_ready, self._channelmap = (sub_queue, logger, config, intmessaging, intmessagingready, channelmap)

    def run(self):
        self._logger.Message('Redis subscriber thread started', 'REDIS')

        #set up redis
        self._redis = redis.StrictRedis(host=self._config.redisip, port=self._config.redisport, db=0)
        self._ps = self._redis.pubsub()
        self.subscribe(self._intmessaging, 'REDIS')

        #first loop
        self._firstloop = False

        for m in self._ps.listen():
            if self._firstloop == False:
                self._firstloop = True
                self._intmessaging_ready.set()
            if m['type'] == 'message' or m['type'] == 'pmessage':
                try:
                    data = json.loads(m['data'])
                except ValueError:
                    self._logger.Message('Invalid json message', 'REDIS')
                    continue

                if 'subscribe' in data:
                    self.subscribe(data['subscribe'], data['id'], data['pattern'])
                elif 'unsubscribe' in data:
                    self.unsubscribe(data['unsubscribe'], data['id'], data['pattern'])
                else: #data, fixme, cant use ID
                    if m['pattern'] == None:
                        channel=m['channel']
                    else:
                        channel=m['pattern']

                    try:
                        self._sub_queue[self._channelmap[channel]].put_nowait(data)
                    except KeyError:
                        self._logger.Message('No queue for ID: %s' % data['id'], 'REDIS')

    def subscribe(self, channel, id, pattern = False):
        #implement parsing a channel list to properly build our mapping
        if pattern:
            self._ps.psubscribe(channel)
        else:
            self._ps.subscribe(channel)
        self._sub_queue[id] = Queue.Queue()
        self._channelmap[channel]=id
        self._logger.Message('ID: %s Subscribed to: %s' % (id, channel), 'REDIS')

    def unsubscribe(self, channel, id, pattern = False):
        if pattern:
            self._ps.punsubscribe(channel)
        else:
            self._ps.unsubscribe(channel)
        if id in self._sub_queue: del self._sub_queue[id]
        if channel in self._channelmap: del self._channelmap[channel]
        self._logger.Message('ID: %s Unsubscribed from: %s' % (id, channel), 'REDIS')
