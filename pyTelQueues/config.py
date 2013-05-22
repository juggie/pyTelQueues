#Config
import ConfigParser, platform
import logging

class Config():
    log = logging.getLogger('Config')

    def __init__(self, pytelqueues, configfile = 'pyTelQueues.cfg'):
        self._pytelqueues, self._configfile = (pytelqueues, configfile)

        self._config = ConfigParser.ConfigParser()
        self._config.read(self._configfile)
        self.fastagi_port = self.read_config_var('fastagi', 'port', 4573, 'int')
        self.redishost = self.read_config_var('redis', 'host', '127.0.0.1', 'str') #should be localhost 
        self.redisport = self.read_config_var('redis', 'port', 6379, 'int')
        self.log.debug('Config loaded')

    def defaulting(self, section, variable, default, quiet = False):
        if quiet == False:
            self.log.debug("%s not set in [%s] defaulting to: %s" %
                    (variable, section, default))

    def read_config_var(self, section, variable, default, type = 'str', quiet = False):
        try:
            if type == 'str':
                return self._config.get(section,variable)
            elif type == 'bool':
                return self._config.getboolean(section,variable)
            elif type == 'int':
                return int(self._config.get(section,variable))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.defaulting(section, variable, default, quiet)
            return default
