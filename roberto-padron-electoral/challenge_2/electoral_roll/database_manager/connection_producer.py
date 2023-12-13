from .mongo_connection import MongoConnection
from .postgresql_connection import PostgreConnection

class DBConnectionProducer:
    """ Returns a new db connection according to the setting.py information
        Uses the factory method to create instances of connection"""

    @staticmethod
    def get_connection(engine):
        """ Returns an instance of a concrete db connection that was specified in the settings.py"""
        if (engine.lower() == 'mongo'):
            return MongoConnection(engine)

        elif (engine.lower() == 'postgre'):
            return PostgreConnection(engine)








        

