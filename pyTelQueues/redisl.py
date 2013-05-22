#Redis Thread
#Does not handle multiple subscriptions to the same queue name
import threading, redis, platform, json, Queue, datetime, hashlib
import logging

class Redis():
    log = logging.getLogger('Redis')
    def __init__(self):
        #message queue
        self._sub_queue = {}
        #map
        self._channelmap = {}
        #message thread state
        self._threadstarted = False
        #internal messaging channel
        self._intmessaging = hashlib.md5('%s' % datetime.datetime.now()).hexdigest()
        #int messaging ok?
        self._intmessaging_ready = threading.Event()

        #redis connection for lib
        #TODO: move parameters to config, also missing is catching errors
        self._redis = redis.StrictRedis(host=Globals.config.redishost, port=Globals.config.redisport, db=0)
        self.log.debug('Connected to redis')

        self._sub_thread = RedisSubscriberThread(self._sub_queue, Globals.config, self._intmessaging, self._intmessaging_ready, self._channelmap)
        self._sub_thread.daemon = True;
        self._sub_thread.start()

    def subscriber_pop_nowait(self, id):
        try:
            return self._sub_queue[id].get_nowait()
        except (Queue.Empty, KeyError):
            return False

    def subscriber_pop(self, id):
        try:
            return self._sub_queue[id].get()
        except (KeyError):
            return False

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
    def __init__(self, sub_queue, config, intmessaging, intmessagingready, channelmap):
        threading.Thread.__init__(self)
        self._sub_queue, Globals.config, self._intmessaging, self._intmessaging_ready, self._channelmap = (sub_queue, config, intmessaging, intmessagingready, channelmap)

    def run(self):
        self.log.debug('Redis subscriber thread started')

        #set up redis
        self._redis = redis.StrictRedis(host=Globals.config.redishost, port=Globals.config.redisport, db=0)
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
                    self.log.debug('Invalid json message')
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
                        self.log.debug('No queue for ID: %s' % data['id'])

    def subscribe(self, channel, id, pattern = False):
        #implement parsing a channel list to properly build our mapping
        if pattern:
            self._ps.psubscribe(channel)
        else:
            self._ps.subscribe(channel)
        self._sub_queue[id] = Queue.Queue()
        self._channelmap[channel]=id
        self.log.debug('ID: %s Subscribed to: %s' % (id, channel))

    def unsubscribe(self, channel, id, pattern = False):
        if pattern:
            self._ps.punsubscribe(channel)
        else:
            self._ps.unsubscribe(channel)
        if id in self._sub_queue: del self._sub_queue[id]
        if channel in self._channelmap: del self._channelmap[channel]
        self.log.debug('ID: %s Unsubscribed from: %s' % (id, channel))
