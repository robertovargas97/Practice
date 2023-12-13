import time
# import psycopg2
import pandas as pd
# import memory_profiler
import threading
from io import StringIO

from django.core.management.base import BaseCommand, CommandError
from django.db import connection


class Command(BaseCommand):
    help = 'Load two files to a database. Example to use : <file_name_1> <file_name_2> <files_encoding>\n It is necessary to type the file name with its extension : data.txt'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.threads = list()

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

        table_1 = 'electoral_roll_elector'
        file_name_1 = kwargs['file_1']
        header_names_1 = ["cedula", "codigo_electoral", "relleno", "fecha_caduc",
                          "junta", "nombre", "primer_apellido", "segundo_apellido"]

        table_2 = 'electoral_roll_distritoelectoral'
        file_name_2 = kwargs['file_2']
        header_names_2 = ["codigo_electoral",
                          "provincia", "canton", "distrito"]

        chunk_size = 250000  # Rows that you want to get from  the files in each loop
        start_time = time.time()

        self.process_file(file_name_2, encoding,
                          header_names_2, chunk_size, table_2, 2)
        self.process_file(file_name_1, encoding,
                          header_names_1, chunk_size, table_1, 1)

        for thread in self.threads:
            thread.join()

        print("---The entire process took %s seconds---" %
              (time.time() - start_time))

    ############################## MY FUNCTIONS TO HANDLE THE FILES ###########################

    def process_file(self, file_name, encoding, header_names, chunk_size, table, file_option):
        for chunk in pd.read_csv(file_name, chunksize=chunk_size, encoding=encoding, skipinitialspace=True, sep=',', names=header_names):
            data = StringIO()
            print("Starting the process...")
            # If the file has specific columns ,remove blanks just there (to avoid database problems)
            if file_option == 1:
                # header_names[5] => nombre
                # header_names[6] => primer_apellido
                # header_names[7] => segundo_apellido
                chunk[header_names[5]] = chunk[header_names[5]].str.strip()
                chunk[header_names[6]] = chunk[header_names[6]].str.strip()
                chunk[header_names[7]] = chunk[header_names[7]].str.strip()
            else:
                # header_names[3] => distrito
                chunk[header_names[3]] = chunk[header_names[3]].str.strip()

            chunk.to_csv(data, index=False, encoding=encoding, header=None)
            data.seek(0)
            self.execute_thread(data, table, encoding)

###################################################################################################################

    # @profile
    def execute_thread(self, data, table, encoding):
        t = threading.Thread(target=self.copy_to_database, args=(data, table, encoding))
        self.threads.append(t)
        t.start()

###################################################################################################################

    # @profile
    def copy_to_database(self, data, table, encoding):
        # Using the django connection is slower than the psycopg2
        with connection.cursor() as cursor:
            try:
                cursor.copy_from(data, table, sep=",")
                connection.commit()

            except (Exception) as error:
                print("Error: %s" % error)
                return 1

        print("Data inserted in %s" % table)
