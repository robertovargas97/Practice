from abc import ABC, abstractmethod

class Connection(ABC):
    """ Is the common class to all connections.
        Each concrete connection must implement the abstract methods that are specific for it.
        The abstract methods in this class are the methods that the app will execute regardless of the database
    """

    def __init__(self, engine):
        self.engine = engine
        self.distelect_table_or_collection = 'electoral_roll_distritoelectoral'
        self.elector_table_or_collection = 'electoral_roll_elector'
        self.province_stats_table_or_collection = 'electoral_roll_votantesporprovincia'
        self.canton_stats_table_or_collection = 'electoral_roll_votantesporcanton'
        self.district_stats_table_or_collection = 'electoral_roll_votantespordistrito'


    @abstractmethod
    def handle_row_to_insert(self):
        """
        Handles each row of the file to create the correct object that will be inserted in the database
        """
        pass

    @abstractmethod
    def bulk_insert(self, table_or_collection):
        """
        Performs a bulk insert for the database in the table or collection given as a parameter
        """
        pass

    @abstractmethod
    def clean_database(self, option):
        """
        Cleans the database according with the option given as a parameter before to start the insertion process
        """
        pass

    @abstractmethod
    def search_by_name(self,name,surname,second_surname):
        """Allows to search in the database an element that matches with the name,surname and second surname given as a parameters"""
        pass

    @abstractmethod
    def search_by_id_card(self,id_card):
        """Allows to search in the database an element that matches with the id card given as a parameter"""
        pass

    @abstractmethod
    def get_districts_information(self):
        """Returns a list of districts and its information according with the database engine indicated in settings.py"""
        pass

    @abstractmethod
    def get_statistics_from_database(self,expiration_date, province, canton, district):
        """Gets all stats of provinces, cantons, districts and id card expiration dates from the database"""
        pass


         
