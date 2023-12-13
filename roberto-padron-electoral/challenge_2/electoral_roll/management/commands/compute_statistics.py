import time
from django.core.management.base import BaseCommand, CommandError
from electoral_roll.models import Elector, DistritoElectoral, VotantesPorProvincia, VotantesPorCanton, VotantesPorDistrito
from electoral_roll.database_manager.connection_producer import DBConnectionProducer
from challenge_2.settings import DB_ENGINE
# import bson
# from datetime import datetime


class Command(BaseCommand):
    help = 'Compute statistics for each province and canton and load them into a databse. No arguments needed'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # For each list the indexes are:
        # [0] => total voters
        # [1] => total male voters
        # [2] => total female voters
        self.province_voter_counter = [0, 0, 0]
        self.canton_voter_counter = [0, 0, 0]
        self.district_voter_counter = [0, 0, 0]

        self.canton_statistics = []
        self.provinces_statistics = []
        self.district_statistics = []

        self.province = ""
        self.canton = ""
        self.distric = ""

        self.connection = DBConnectionProducer.get_connection(DB_ENGINE)

    def handle(self, *args, **kwargs):
        self.clean_statistics()
        
        print("--- Starting statistics process.... ---")

        start_time = time.time()

        self.compute_statistics()

        print("--- The entire process took %s seconds ---" %
              (time.time() - start_time))

    ############################## MY FUNCTIONS  ###########################

    def compute_statistics(self):
        
        # Gets all the districts and their information
        data = self.connection.get_districts_information()
        print("--- Districts obtained ---")

        # The last district in the list
        last_element = len(data) - 1
        last_canton = data[last_element].canton

        # The first province and canton in the list
        self.province = data[0].provincia
        self.canton = data[0].canton

        print("--- Calculating stats ---")
        for district in data:
            #Creates each district tuple
            total_voters = district.total_hombres + district.total_mujeres
            district_tuple_data = self.assign_tuple_values('distrito', district.distrito, total_voters, district.total_hombres, district.total_mujeres, district.provincia,district.canton)
            self.district_statistics.append(district_tuple_data)
            
            if(district.canton == last_canton):
                # Creates the last canton tuple and adds it to a list
                total_voters_last_canton = district.total_hombres + district.total_mujeres
                canton_tuple_data = self.assign_tuple_values('canton', district.canton, total_voters_last_canton, district.total_hombres, district.total_mujeres, district.provincia)
                self.canton_statistics.append(canton_tuple_data)

                # Creates the last province tuple and adds it to a list
                self.add_province(district.provincia)

            if(district.canton != self.canton):
                # Creates each canton tuple and adds it to a list
                self.add_canton(district.canton)

            if(district.provincia != self.province):
                # Creates each province tuple and adds it to a list
                self.add_province(district.provincia)

            self.manage_statistic_counters('canton', 'increase', district.total_hombres, district.total_mujeres)

        print("--- Stats done ---")

        self.bulk_insert()

    def add_province(self, new_province):
        self.province_voter_counter[0] = self.province_voter_counter[1] + self.province_voter_counter[2]
        province_tuple_data = self.assign_tuple_values('provincia', self.province, self.province_voter_counter[0], self.province_voter_counter[1], self.province_voter_counter[2])
        self.provinces_statistics.append(province_tuple_data )
        self.province = new_province
        self.manage_statistic_counters('province', 'reset')

    def add_canton(self, new_canton):
        self.canton_voter_counter[0] = self.canton_voter_counter[1] + self.canton_voter_counter[2]
        canton_tuple_data = self.assign_tuple_values('canton', self.canton, self.canton_voter_counter[0], self.canton_voter_counter[1], self.canton_voter_counter[2], self.province)
        self.canton_statistics.append(canton_tuple_data)
        self.manage_statistic_counters('province', 'increase')
        self.canton = new_canton
        self.manage_statistic_counters('canton', 'reset')

    def assign_tuple_values(self, attribute, attribute_value, total_voters, total_male_voters, total_female_voters, province="", canton=""):

        tuple_data = {attribute: attribute_value,
                      'total_votantes': total_voters,
                      'total_votantes_hombres': total_male_voters,
                      'total_votantes_mujeres': total_female_voters
                      }

        if(attribute == 'canton'):
            tuple_data.update({'provincia': province})
          
        elif(attribute == 'distrito'):
            tuple_data.update({'provincia': province, 'canton': canton})

        return tuple_data

    def manage_statistic_counters(self, counter_type, action, canton_male_count=0, canton_female_count=0):

        if(action == 'reset'):

            if(counter_type == "province"):
                self.province_voter_counter[1] = 0
                self.province_voter_counter[2] = 0

            elif (counter_type == 'canton'):
                self.canton_voter_counter[1] = 0
                self.canton_voter_counter[2] = 0

        elif (action == 'increase'):

            if(counter_type == "province"):
                self.province_voter_counter[1] += self.canton_voter_counter[1]
                self.province_voter_counter[2] += self.canton_voter_counter[2]

            elif (counter_type == 'canton'):
                self.canton_voter_counter[1] += canton_male_count
                self.canton_voter_counter[2] += canton_female_count


    def bulk_insert(self):
        self.connection.bulk_insert(next(self.data_set_generator(self.provinces_statistics ,'province')),'province_stats')
        self.connection.bulk_insert(next(self.data_set_generator(self.canton_statistics ,'canton')),'canton_stats')
        self.connection.bulk_insert(next(self.data_set_generator(self.district_statistics ,'district')),'district_stats')

    def clean_statistics(self):
        self.connection.clean_database('stats')

    def data_set_generator(self,data, option):
        elements_to_insert = []

        for element in data:

            new_element = self.connection.generate_data(element,option)
            elements_to_insert.append(next(new_element))

        yield elements_to_insert


    # def update_all_dates(self):
    #     for i in self.connection.db['electoral_roll_elector'].distinct('fecha_caducidad'):
    #         myquery = { "fecha_caducidad": i}
    #         date = i.split('-')
    #         newvalues = { "$set": { "fecha_caducidad": datetime(int(date[0]),int(date[1]), int(date[2]),18) } }

    #         self.connection.db['electoral_roll_elector'].update_many(myquery, newvalues)


