from pymongo import MongoClient
from datetime import datetime
from challenge_2.settings import MONGO_URI
from challenge_2.settings import DB_NAME
from .connection import Connection


class MongoDistrictInformation:
    def __init__(self, electoral_code, province, canton, district, male_count, female_count):
        self.codigo_electoral = electoral_code
        self.provincia = province
        self.canton = canton
        self.distrito = district
        self.total_hombres = male_count
        self.total_mujeres = female_count


class MongoConnection(Connection):
    """
        It is a concrete type of mongo database connection
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.mongo_client = MongoClient(MONGO_URI)
        self.db = self.mongo_client[DB_NAME]

    def clean_database(self, option):
        """
        Cleans the database before to start the insertion process
        """

        if (option == 'electoral_roll'):
            self.db[self.distelect_table_or_collection].delete_many({})
            self.db[self.elector_table_or_collection].delete_many({})

        elif (option == 'stats'):
            self.db[self.district_stats_table_or_collection].delete_many({})
            self.db[self.canton_stats_table_or_collection].delete_many({})
            self.db[self.province_stats_table_or_collection].delete_many({})

    def handle_row_to_insert(self, data_row, option_file):
        """
        Handles each row of the file to create the correct object that will be inserted in the database
        """
        data_dict = {}

        if(option_file == 'distelec'):
            data_dict = {
                "codigo_electoral": data_row[0],
                "provincia": data_row[1].strip(),
                "canton": data_row[2].strip(),
                "distrito": data_row[3].strip()
            }

        elif (option_file == 'padron'):

            data_dict = {"cedula": data_row[0],
                         "codigo_electoral": data_row[1],
                         "relleno": data_row[2],
                         "fecha_caducidad": datetime(int(data_row[3][:4]), int(data_row[3][4:6]), int(data_row[3][6:]),18),
                         "junta": data_row[4],
                         "nombre": data_row[5].strip(),
                         "primer_apellido": data_row[6].strip(),
                         "segundo_apellido": data_row[7].strip()
                         }

                        

        return data_dict

    def bulk_insert(self, data, insert_option):
        """
        Performs a bulk insert for the database in the table or collection given as a parameter
        """
        try:
            if (insert_option == 'distelec'):
                self.db[self.distelect_table_or_collection].insert_many(data)

            elif (insert_option == 'padron'):
                self.db[self.elector_table_or_collection].insert_many(data)

            elif (insert_option == 'province_stats'):
                self.db[self.province_stats_table_or_collection].insert_many(
                    data)

            elif (insert_option == 'canton_stats'):
                self.db[self.canton_stats_table_or_collection].insert_many(
                    data)

            elif (insert_option == 'district_stats'):
                self.db[self.district_stats_table_or_collection].insert_many(
                    data)

            print(f"--- The data was inserted ---")

        except Exception as error:
            print(error)

    def build_searching_result(self, elector_query_filter):
        """ Builds a searching result with the elector and electoral districts information"""

        
        elector = self.db[self.elector_table_or_collection].find_one(
            elector_query_filter)

        if elector is not None:
            electoral_district = self.db[self.distelect_table_or_collection].find_one(
                {'codigo_electoral': elector['codigo_electoral']})

            return {'nombre': elector['nombre'],
                'primer_apellido': elector['primer_apellido'],
                'segundo_apellido': elector['segundo_apellido'],
                'cedula': elector['cedula'],
                'fecha_caducidad': elector['fecha_caducidad'],
                'codigo_electoral__provincia': electoral_district['provincia'],
                'codigo_electoral__canton': electoral_district['canton'],
                'codigo_electoral__distrito': electoral_district['distrito'],
                'codigo_electoral': electoral_district['codigo_electoral'],
                }

        else :
            return []
             

         

    def search_by_name(self, name, surname, second_surname):
        """Allows to search in the database an element that matches with the name,surname and second surname given as a parameters"""
        elector_query_filter = {"$and": [{'nombre': name}, {
            'primer_apellido': surname}, {'segundo_apellido': second_surname}]}
        searching_result = self.build_searching_result(elector_query_filter)
        return searching_result

    def search_by_id_card(self, id_card):
        """Allows to search in the database an element that matches with the id card given as a parameter"""
        elector_query_filter = {'cedula': id_card}
        searching_result = self.build_searching_result(elector_query_filter)
        return searching_result

    def get_districts_information(self):
        """ Returns a list of MongoDistrictInformation objects
            It uses a MongoDistrictInformation objects to handle the districts in the same way as 
            the query bbjects that the relational databases return
        """
        mongo_districts_list = []

        district = self.db[self.distelect_table_or_collection].find({}, {
                                                                    '_id': 0})

        # For each district calculate the total of men and women
        for district in district:
            male_count = self.db[self.elector_table_or_collection].count_documents(
                {"$and": [{'codigo_electoral': district['codigo_electoral']}, {
                    'relleno': '1'}]}
            )

            female_count = self.db[self.elector_table_or_collection].count_documents(
                {"$and": [{'codigo_electoral': district['codigo_electoral']}, {
                    'relleno': '2'}]}
            )

            new_district = MongoDistrictInformation(electoral_code=district['codigo_electoral'], province=district['provincia'],
                                                    canton=district['canton'], district=district['distrito'], male_count=male_count,
                                                    female_count=female_count)
            mongo_districts_list.append(new_district)

        return mongo_districts_list

    def get_canton_id(self, province, canton):
        canton = self.db[self.canton_stats_table_or_collection].find_one(
            {"$and": [{'provincia': province}, {'canton': canton}]})
        return canton['_id']

    def get_province_id(self, province):
        province = self.db[self.province_stats_table_or_collection].find_one(
            {'provincia': province})
        return province['_id']

    def generate_data(self, element, option):
        new_element = element

        if (option == 'canton'):
            new_element.update(
                {'codigo_provincia_id': self.get_province_id(element['provincia'])})

        elif (option == 'district'):
            new_element.update({'codigo_canton_id': self.get_canton_id(
                element['provincia'], element['canton'])})

        yield new_element

    def get_statistics_from_database(self, expiration_date, province, canton, district):
        """Gets all stats of provinces, cantons, districts and id card expiration dates from the database"""

        province_statistics = self.db[self.province_stats_table_or_collection].find_one(
            {'provincia': province}, {'_id': 0, 'provincia': 0}
        )

        canton_statistics = self.db[self.canton_stats_table_or_collection].find_one(
            {'$and': [{'provincia': province}, {'canton': canton}]},
            {'_id': 0, 'provincia': 0, 'canton': 0, 'codigo_provincia_id': 0}
        )

        district_filter = {'$and': [{'provincia': province}, {'canton': canton}, {'distrito': district}]}
        district_statistics = self.db[self.district_stats_table_or_collection].find_one(district_filter, {'_id': 0,
                                                                                                          'provincia': 0,
                                                                                                          'distrito': 0,
                                                                                                          'canton': 0,
                                                                                                          'codigo_canton_id': 0})

        identification_statistics = {'same_id_count': self.db[self.elector_table_or_collection].count_documents(
            {'fecha_caducidad': expiration_date}
        )}

        return {'province_statistics': province_statistics,
                'canton_statistics': canton_statistics,
                'district_statistics': district_statistics,
                'id_statistics': identification_statistics}

    def insert_new_elector(self,new_data):
        new_data[3] = new_data[3].strftime("%Y%m%d")
        new_doc = self.handle_row_to_insert(new_data, 'padron')
        self.db[self.elector_table_or_collection].insert_one(new_doc)
        self.update_statistics(new_data[1],new_data[2],'increase')

    def delete_elector(self, id_card):
        elector = self.db[self.elector_table_or_collection].find_one({'cedula': id_card})
        data = [elector['cedula'], elector['codigo_electoral'],elector['relleno']]
        
        self.db[self.elector_table_or_collection].delete_one({'cedula': data[0]})
        self.update_statistics(data[1], data[2], 'decrease')


    def update_statistics(self,code, new_gender, operation):

        gender = 'total_votantes_hombres' if new_gender == '1' else 'total_votantes_mujeres'
        quantity = 1 if operation == 'increase' else -1

        ubication = self.db[self.distelect_table_or_collection].find_one({'codigo_electoral': code },{'_id':0, 'codigo_electoral':0})

        province_filter = { 'provincia': ubication['provincia'] }
        canton_filter =  {'$and': [{'provincia': ubication['provincia']}, {'canton': ubication['canton']}]}
        district_filter = { '$and': [ {'provincia': ubication['provincia']} , {'canton': ubication['canton']} , {'distrito': ubication['distrito']}]}

        query_operation = { '$inc': { 'total_votantes': quantity, gender : quantity }}

        self.db[self.province_stats_table_or_collection].update_one(province_filter, query_operation )
        self.db[self.canton_stats_table_or_collection].update_one(canton_filter, query_operation )
        self.db[self.district_stats_table_or_collection].update_one(district_filter, query_operation )

    
      

