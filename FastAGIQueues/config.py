#Config
import ConfigParser, platform

class Config():
	def __init__(self, logger, configfile = 'FastAGIQueues.cfg'):
		#store class input
		self._logger, self._configfile = (logger, configfile)

		self._config = ConfigParser.ConfigParser()
		self._config.read(self._configfile)
		self.fastagi_port = self.read_config_var('fastagi', 'port', 4573, 'int')
		self.redisinstancechannel = self.read_config_var('redis', 'instancechannel', 'agiqueues.%s' % platform.node(), 'str')
		self.redisglobalchannel = self.read_config_var('redis', 'globalchannel', 'agiqueues.global', 'str')
		self.redisip = self.read_config_var('global', 'redisip', '192.168.99.20', 'str') #should be localhost 
		self.redisport = self.read_config_var('global', 'redisport', 6379, 'int')

		logger.Message('Config loaded', 'CONFIG')

	def defaulting(self, section, variable, default, quiet = False):
		if quiet == False:
			self._logger.Message(str(variable) + ' not set in ['+str(section)+'] defaulting to: \''+str(default)+'\'', 'CONFIG')

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