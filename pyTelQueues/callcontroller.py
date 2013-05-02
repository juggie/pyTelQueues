#Call Controller
import threading, platform, json, Queue

class CallController():
    def __init__(self, pytelqueues):
        #store class input
        self._pytelqueues = pytelqueues
        
        #Queue for thread
        self._queue = Queue.Queue()

        #start call controller thread
        self._callcontroller_thread = CallControllerThread(self._pytelqueues)
        self._callcontroller_thread.daemon = True;
        self._callcontroller_thread.start()
        
    def put(self, item):
        self._queue.put_nowait(item)
    
    def get(self):
        return self._queue.get()

class CallControllerThread(threading.Thread):
    def __init__(self, pytelqueues):
        threading.Thread.__init__(self)
        #save class input
        self._pytelqueues = pytelqueues

        #call state
        self._call_state = {}
        
    def run(self):
        self._pytelqueues.logger().Message('Call controller thread started', 'CALLC')
        while True:
            message = self._pytelqueues.callcontroller().get()
            self._pytelqueues.logger().Message('Event: %s, ClientMD5: %s, Channel Type: %s' % (message['event'], message['clientMD5'], message['channeltype']), 'CALLC')
            if message['event'] == 'ring':
                self._call_state[message['clientMD5']]=[]
                self._pytelqueues.telephonyserver().put({'channeltype': message['channeltype'], 'event' : 'answer', 'clientMD5' : message['clientMD5']})
                self._call_state[message['clientMD5']]=1
            elif message['event'] == 'hangup':
                if message['clientMD5'] in self._call_state: del self._call_state[message['clientMD5']]
            else:
                if self._call_state[message['clientMD5']]==1:
                    self._pytelqueues.telephonyserver().put({'channeltype': message['channeltype'], 'event' : 'playback', 'parameters': 'tt-monkeys', 'clientMD5' : message['clientMD5']})
                    self._call_state[message['clientMD5']]=2
                elif self._call_state[message['clientMD5']]==2:
                    self._pytelqueues.telephonyserver().put({'channeltype': message['channeltype'], 'event' : 'hangup', 'clientMD5' : message['clientMD5']})
                    self._call_state[message['clientMD5']]=3
                else:
                    pass
