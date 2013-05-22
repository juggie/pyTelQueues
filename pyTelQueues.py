## AGI Queues
## donnyk@gmail.com

## TODO: Properly signal threads to quit rather then running them in daemon mode
## and killing them without warning
## TODO #2: pytelqueues is being used all over in several threads.  Locking
## must be applied where necessairy.

import time #add wrapper for input
import logging

#app level imports
from pyTelQueues.pytelqueues import pyTelQueues

if __name__=="__main__":
    log = logging.getLogger('Main')
    logging.basicConfig(level=logging.DEBUG)
    #pytelqueues core object
    pytelqueues = pyTelQueues()

    #loop and wait for cli input, needs to be wrapped in a class supporting
    #windows and unix
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        log.debug("Crtl+C pressed. Shutting down.")
