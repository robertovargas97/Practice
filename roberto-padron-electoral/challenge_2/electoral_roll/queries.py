from .models import Elector, DistritoElectoral, VotantesPorProvincia, VotantesPorCanton
from electoral_roll.database_manager.connection_producer import DBConnectionProducer
from challenge_2.settings import DB_ENGINE


class Queries:

    def __init__(self, elector_id="", elector_name="", elector_first_surname="", elector_second_surname="", elector_option=""):
        self.elector_identification = elector_id
        self.elector_name = elector_name.upper()
        self.elector_first_surname = elector_first_surname.upper()
        self.elector_second_surname = elector_second_surname.upper()
        self.elector_option = elector_option
        self.connection = DBConnectionProducer.get_connection(DB_ENGINE)


    def search_polling_information(self):
        """ This method searches the information of the elector according to the user's election
            No matters what is the engine of the database this method performs the searching well
        """
        result = {}

        if(self.elector_option == '1'):  # Search by name
            result = self.connection.search_by_name(self.elector_name,self.elector_first_surname,self.elector_second_surname)

        elif self.elector_option == '2':  # Search by identification
            result  = self.connection.search_by_id_card(self.elector_identification )

        return result

