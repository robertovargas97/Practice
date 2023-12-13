# import memory_profiler
import time
import threading

from django.core.management.base import BaseCommand, CommandError
from electoral_roll.models import DistritoElectoral, Elector
from electoral_roll.database_manager.connection_producer import DBConnectionProducer
from challenge_2.settings import DB_ENGINE

class Command(BaseCommand):
    help = 'Load two files to a database. Example to use : <file_name_1> <file_name_2> <files_encoding>\n It is necessary to type the file name with its extension : data.txt'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threads = list()
        self.connection = DBConnectionProducer.get_connection(DB_ENGINE)


    def add_arguments(self, parser):
        parser.add_argument('file_1', type=str,
                            help='Indicates the name of the largest file')
        parser.add_argument('file_2', type=str,
                            help='Indicates the name of the smallest file')
        parser.add_argument('files_encoding', type=str,
                            help='Indicates the encoding of the files')

    def handle(self, *args, **kwargs):

        # Encoding => ANSI
        encoding = kwargs['files_encoding']
        
        # Variables that take the file names from kargs
        electoral_roll = kwargs['file_1']
        electoral_district = kwargs['file_2']

        # Variables used to identify how to handle the rows of the files and where will be inserted the data
        key_file_1 = "padron"
        key_file_2 = "distelec"

        chunk_size = 600000 
        print(f"--- Starting the process to clean the database")
        self.clean_database()

        print(f"--- Starting the process with {self.connection.engine}")
        start_time = time.time()

        self.import_file_to_database(electoral_district, encoding, chunk_size,key_file_2)
        self.import_file_to_database(electoral_roll, encoding, chunk_size,key_file_1)

        for thread in self.threads:
            thread.join()

        print(f"--- The entire process took %s seconds with {self.connection.engine} ---" % (time.time() - start_time))

    ############################## MY FUNCTIONS TO HANDLE THE FILES ###########################
    
    # @profile
    def clean_database(self):
        """
            Cleans the database to start the process.
            No matters what is the engine of the database
        """
        self.connection.clean_database('electoral_roll')

    # @profile
    def process_file_in_chunks(self,file_name, encoding, chunk_size , option_file):
        """
            Processes the file in chunks and yields a chunk according to the chunk_size parameter.
            No matters what is the engine of the database this method handle each row to each specific type of db
        """
        data_list = []
        count = 0

        with open(file=file_name, mode='r', encoding=encoding) as file:
            for row in file:
                row = row.split(',')
                data_row = self.connection.handle_row_to_insert(row,option_file)
                data_list.append(data_row)

                if(count == chunk_size):
                    yield data_list
                    print(f"{count} elements were yielded")
                    count = 0
                    data_list = []
                
                count += 1
            
        yield data_list
        print(f"{count} elements were yielded")
        data_list = []

    # @profile        
    def import_file_to_database(self,file_name, encoding, chunk_size,option_file):
        """ Loop through the file and sends a thread to insert the data into the database"""
        for data in self.process_file_in_chunks(file_name, encoding, chunk_size,option_file):
            self.execute_thread(data, option_file)

    
    # @profile
    def execute_thread(self, data, option_file):
        """Activate a thread to insert the data into the database"""
        t = threading.Thread(target=self.insert_data ,args=(data,option_file))
        self.threads.append(t)
        t.start()

    # @profile
    def insert_data( self, data, option_file):
        """Performs a bulk insert to the database with each thread"""
        print(f"--- Starting to insert data with {threading.current_thread().getName()}---")
        self.connection.bulk_insert(data,option_file)



###################################################################################################################

