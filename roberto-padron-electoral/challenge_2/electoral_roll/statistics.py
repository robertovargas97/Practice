from .models import Elector, VotantesPorProvincia, VotantesPorCanton , VotantesPorDistrito, DistritoElectoral

from electoral_roll.database_manager.connection_producer import DBConnectionProducer
from challenge_2.settings import DB_ENGINE


class Statistics:

    def __init__(self):
        self.connection = DBConnectionProducer.get_connection(DB_ENGINE)
      
    def get_polling_statistics(self, expiration_date, province, canton, district):
        return self.connection.get_statistics_from_database(expiration_date, province, canton, district)



