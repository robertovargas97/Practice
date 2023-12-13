from pymongo import MongoClient
from django.db import connection
from django.db.models import Q, Count


from challenge_2.settings import MONGO_URI
from challenge_2.settings import DB_NAME
from electoral_roll.models import Elector, DistritoElectoral, VotantesPorProvincia, VotantesPorCanton, VotantesPorDistrito
from .connection import Connection


class PostgreConnection(Connection):
    """
        It is a concrete type of postgre databse connection
    """

    def __init__(self, engine):
        super().__init__(engine)
        self.connection = connection

    def clean_database(self, option):
        """
        Cleans the database before to start the insertion process
        """
        if (option == 'electoral_roll'):
            DistritoElectoral.objects.all().delete()
            Elector.objects.all().delete()

        elif (option == 'stats'):
            VotantesPorDistrito.objects.all().delete()
            VotantesPorCanton.objects.all().delete()
            VotantesPorProvincia.objects.all().delete()

    def handle_row_to_insert(self, data_row, option_file):
        """
        Handles each row of the file to create the correct object that will be inserted in the database
        """
        data = ()

        if(option_file == 'distelec'):
            data = (data_row[0], data_row[1].strip(),
                    data_row[2].strip(), data_row[3].strip())

        elif (option_file == 'padron'):
            data = (data_row[0], data_row[1], data_row[2], data_row[3], data_row[4],
                    data_row[5].strip(), data_row[6].strip(), data_row[7].strip())

        return data

    def bulk_insert(self, data, insert_option):
        """
        Performs a bulk insert for the database in the table or collection given as a parameter
        """
        try:
            if insert_option == 'province_stats':
                VotantesPorProvincia.objects.bulk_create(data)

            elif (insert_option == 'canton_stats'):
                VotantesPorCanton.objects.bulk_create(data)

            elif (insert_option == 'district_stats'):
                VotantesPorDistrito.objects.bulk_create(data)

            else:

                if (insert_option == 'distelec'):
                    sql = f"INSERT INTO {self.distelect_table_or_collection} (codigo_electoral, provincia, canton, distrito)  VALUES (%s,%s,%s,%s)"

                elif (insert_option == 'padron'):
                    sql = f"INSERT INTO {self.elector_table_or_collection} (cedula, codigo_electoral_id, relleno,fecha_caducidad, junta,nombre, primer_apellido, segundo_apellido) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"

                with self.connection.cursor() as cursor:
                    cursor.executemany(sql, data)
                    self.connection.commit()

            print(f"--- The data was inserted ---")

        except Exception as error:
            print(error)

    def get_list_of_values(self):
        """ Returns a list of the necessary values to show in the query result"""
        return ['nombre', 'primer_apellido', 'segundo_apellido', 'cedula', 'codigo_electoral__provincia', 'codigo_electoral__canton', 'codigo_electoral__distrito', 'codigo_electoral', 'fecha_caducidad']

    def verify_result(self, result):
        """ Verifies if the result has an element to retunrs it"""
        if len(result) > 0:
            result = result[0]
        else:
            result = []

        return result

    def search_by_name(self, name, surname, second_surname):
        """Allows to search in the database an element that matches with the name,surname and second surname given as a parameters"""
        result = Elector.objects.filter(nombre=name, primer_apellido=surname,
                                        segundo_apellido=second_surname).values(*self.get_list_of_values())
        searching_result = self.verify_result(result)
        return searching_result

    def search_by_id_card(self, id_card):
        """Allows to search in the database an element that matches with the id card given as a parameter"""
        result = Elector.objects.filter(
            cedula=id_card).values(*self.get_list_of_values())
        searching_result = self.verify_result(result)
        return searching_result

    def get_districts_information(self):
        data = DistritoElectoral.objects.annotate(total_hombres=Count('elector', filter=Q(elector__relleno='1')),
                                                  total_mujeres=Count('elector', filter=Q(elector__relleno='2')))
        return data

    def get_province_id(self, province):
        return VotantesPorProvincia.objects.values('codigo_provincia').filter(provincia=province)[0]['codigo_provincia']

    def get_canton_id(self, province, canton):
        return VotantesPorCanton.objects.values('codigo_canton').filter(codigo_provincia__provincia=province, canton=canton)[0]['codigo_canton']

    def generate_data(self, element, option):
        new_element = ()

        if (option == 'province'):
            new_element = (VotantesPorProvincia(provincia=element['provincia'], total_votantes=element['total_votantes'], total_votantes_hombres=element[
                'total_votantes_hombres'], total_votantes_mujeres=element['total_votantes_mujeres']))

        elif(option == 'canton'):
            new_element = (VotantesPorCanton(canton=element['canton'], total_votantes=element['total_votantes'], total_votantes_hombres=element[
                'total_votantes_hombres'], total_votantes_mujeres=element['total_votantes_mujeres'], codigo_provincia_id=self.get_province_id(element['provincia'])))

        elif (option == 'district'):
            new_element = (VotantesPorDistrito(distrito=element['distrito'], total_votantes=element['total_votantes'], total_votantes_hombres=element[
                'total_votantes_hombres'], total_votantes_mujeres=element['total_votantes_mujeres'], codigo_canton_id=self.get_canton_id(element['provincia'], element['canton'])))

        yield new_element

    def get_statistics_from_database(self, expiration_date, province, canton, district):
        """Gets all stats of provinces, cantons, districts and id card expiration dates from the database"""

        statistics_names = [
            'total_votantes',
            'total_votantes_hombres',
            'total_votantes_mujeres'
        ]
        province_statistics = VotantesPorProvincia.objects.filter(
            provincia=province).values(*statistics_names)

        canton_statistics = VotantesPorCanton.objects.filter(
            codigo_provincia__provincia=province,
            canton=canton).values(*statistics_names)

        district_statistics = VotantesPorDistrito.objects.filter(
            distrito=district,
            codigo_canton__canton=canton,
            codigo_canton__codigo_provincia__provincia=province).values(*statistics_names)

        identification_statistics = {
            'same_id_count': Elector.objects.filter(fecha_caducidad=expiration_date).count()
        }

        return {'province_statistics': province_statistics[0],
                'canton_statistics': canton_statistics[0],
                'district_statistics': district_statistics[0],
                'id_statistics': identification_statistics}
