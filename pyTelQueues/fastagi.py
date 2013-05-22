import asyncore, asynchat, socket, json, hashlib
import logging

class FastAGIServer(asyncore.dispatcher):
    log = logging.getLogger('FastAGIServer')

    def __init__(self, pytelqueues):
        asyncore.dispatcher.__init__(self)
        #store class input
        self._pytelqueues = pytelqueues

        #clients
        self._clients = {}

        #asynccore
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind(("", self._pytelqueues.config().fastagi_port))
        self.listen(5)
        self.log.debug('FASTAGI thread started')
        self.log.debug('AGI Queue Server listening on port: %i' %
                self._pytelqueues.config().fastagi_port)

    def handle_accept(self):
        pair = self.accept()
        if pair is None:
            pass
        else:
            sock, addr = pair
            handler = FAGIChannel(sock, addr, self._pytelqueues, self._clients)

    def numclients(self):
        return len(self._clients)

    def getclient(self, clientMD5):
        return self._clients[clientMD5]

class FAGIChannel(asynchat.async_chat):
    log = logging.getLogger('FAGIChannel')

    def __init__(self, sock, addr, pytelqueues, clients):
        #store class input
        self._pytelqueues, self._clients = (pytelqueues, clients)

        asynchat.async_chat.__init__(self, sock)
        #fagi terminator
        self.set_terminator("\n")
        #buffer for asynchat
        self._buffer = []
        #ip/port in string
        self._straddr = str(addr)
        #did we complete the initial agi connection
        self._connected = False
        #is moh enabled
        self._moh = False

        #set md5 id of connected client
        self._clientMD5 = hashlib.md5(str(addr)).hexdigest()

        self._clients[self._clientMD5]=self

        self.log.debug('Incoming FastAGI connection from %s' % repr(addr))

    def handle_callcontroller_event(self, event):
        self.log.debug('Event %s' % event)
        if event['event']=='answer':
            self.AGI_Answer()
        elif event['event']=='playback':
            self.AGI_Playback(str(event['parameters'])) #confused as to why str() is necessairy 
        elif event['event']=='mohon':
            self.AGI_MusicOnHold(True)
        elif event['event']=='mohoff':
            self.AGI_MusicOnHold(False)
        elif event['event']=='hangup':
            self.AGI_Hangup()

    def send_callcontroller_event(self, event):
        tosend = {'event' : event, 'clientMD5' : self._clientMD5, 'channeltype' : 'fastagi'}
        self._pytelqueues.callcontroller().put(tosend)
        self.log.debug('Sent %s to call controller' % tosend)

    def send_command(self, data):
        self.log.debug('SENT: %s' % data)
        self.push(data+'\n')

    def collect_incoming_data(self, data):
        # Append incoming data to the buffer
        self._buffer.append(data)

    def found_terminator(self):
        line = "".join(self._buffer)
        self._buffer = []
        self.handle_line(line)

    def handle_line(self, line):
        if self._connected == False:
            if line == '':
                self._connected = True
                self.log.debug('Initial Variables Received')
                self.send_callcontroller_event('ring')
            else:
                self.log.debug('Variable -> %s' % line)
        else:
            self.log.debug('Received %s' % line)
            self.HandleCall(line)

    def handle_close(self):
        self.log.debug('FastAGI connection from %s closed' % self._straddr)
        if self._clientMD5 in self._clients: del self._clients[self._clientMD5]
        self.close()

    def handle_errorr(self):
        self.log.error('FastAGI connection from %s closed' % self._straddr)
        if self._clientMD5 in self._clients: del self._clients[self._clientMD5]
        self.close()

    #parsing of agi responses goes here
    def HandleCall(self,line):
        if line[:3] == '200':
            self.send_callcontroller_event('ok')
        elif line[:3] == '510':
            self.send_callcontroller_event('invalid')
        elif line[:3] == '511':
            self.send_callcontroller_event('dead')
        elif line == 'HANGUP':
            self.send_callcontroller_event('hangup')
            self.handle_close()
        else:
            self.log.debug('Unknown event: %s' % line)

    def AGI_Answer(self):
        self.send_command('ANSWER')

    def AGI_Playback(self, file='beep'):
        self.send_command('STREAM FILE %s \'\' 0' % file)

    def AGI_MusicOnHold(self, moh_state, moh_class = ''):
        if moh_state == True:
            self._moh = True
            self.send_command('SET MUSIC ON %s' % moh_class)
        else:
            self._moh = False
            self.send_command('SET MUSIC OFF')

    def AGI_Hangup(self):
        self.send_command('HANGUP')
