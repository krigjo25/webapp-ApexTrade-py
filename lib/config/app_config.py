#   Importing responsories

class DefaultConfig(object):
    TESTING = False
    #DATABASE_URI = 'sqlite:///finance.db'
    DEBUG = False
    SESSION_TYPE = None
    SESSION_PERMANENT = False

class DevelopmentConfig(DefaultConfig):
    TESTING = False
    #DATABASE_URI = 'sqlite:///finance.db'
    SESSION_TYPE = 'filesystem'
    DEBUG = True
