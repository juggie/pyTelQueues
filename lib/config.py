#Config
import ConfigParser, platform

class Config():
	def __init__(self, logger, configfile = 'FAGIqueues.cfg'):
		#save logger object
		self._logger = logger
		
		self._config = ConfigParser.ConfigParser()
		self._config.read(configfile)
		self.fastagi_port = self.read_config_var('fastagi', 'port', 4573, 'int')
		self.instancename = self.read_config_var('global', 'instancename', platform.node(), 'str') #platform.node gets hostname

	def defaulting(self, section, variable, default, quiet = False):
		if quiet == False:
			self._logger.Message(str(variable) + ' not set in ['+str(section)+'] defaulting to: \''+str(default)+'\'', 'Config')
		
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