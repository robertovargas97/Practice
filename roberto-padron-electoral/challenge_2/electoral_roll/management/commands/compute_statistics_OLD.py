import time
# import threading
from django.db.models import Q, Count
from django.core.management.base import BaseCommand, CommandError
from electoral_roll.models import Elector, DistritoElectoral, VotantesPorProvincia, VotantesPorCanton , VotantesPorDistrito


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

    def handle(self, *args, **kwargs):
        print("Starting statistics process....")

        start_time = time.time()

        self.compute_statistics()

        print("---The entire process took %s seconds---" %
              (time.time() - start_time))

    ############################## MY FUNCTIONS  ###########################

    def compute_statistics(self):
        data = DistritoElectoral.objects.annotate(male_count=Count('elector', filter=Q(elector__relleno='1')),
                                                  female_count=Count('elector', filter=Q(elector__relleno='2')))

        last_element = len(data) - 1
        last_canton = data[last_element].canton

        self.province = data[0].provincia
        self.canton = data[0].canton

        for place in data:
            #Creates each district tuple
            total_voters = place.male_count + place.female_count
            district_tuple_data = self.asign_tuple_values('distrito', place.distrito, total_voters, place.male_count, place.female_count, place.provincia,place.canton)
            self.district_statistics.append(district_tuple_data)

            if(place.canton == last_canton):
                # Creates the last canton tuple and adds it to a list
                total_voters_last_canton = place.male_count + place.female_count
                canton_tuple_data = self.asign_tuple_values('canton', place.canton, total_voters_last_canton, place.male_count, place.female_count, place.provincia)
                self.canton_statistics.append(canton_tuple_data)

                # Creates the last province tuple and adds it to a list
                self.add_province(place.provincia)

            if(place.canton != self.canton):
                # Creates each canton tuple and adds it to a list
                self.add_canton(place.canton)
              
            if(place.provincia != self.province):
                # Creates each province tuple and adds it to a list
                self.add_province(place.provincia)

            self.manage_statistic_counters('canton', 'increase', place.male_count, place.female_count)

        self.bulk_insert()

    def add_province(self, new_province):
        self.province_voter_counter[0] = self.province_voter_counter[1] + self.province_voter_counter[2]
        province_tuple_data = self.asign_tuple_values('provincia', self.province, self.province_voter_counter[0], self.province_voter_counter[1], self.province_voter_counter[2])
        self.provinces_statistics.append(VotantesPorProvincia(**province_tuple_data))
        self.province = new_province
        self.manage_statistic_counters('province', 'reset')

    def add_canton(self, new_canton):
        self.canton_voter_counter[0] = self.canton_voter_counter[1] + self.canton_voter_counter[2]
        canton_tuple_data = self.asign_tuple_values('canton',self.canton, self.canton_voter_counter[0], self.canton_voter_counter[1], self.canton_voter_counter[2], self.province)
        self.canton_statistics.append(canton_tuple_data)
        self.manage_statistic_counters('province', 'increase')
        self.canton = new_canton
        self.manage_statistic_counters('canton', 'reset')

    def asign_tuple_values(self, attribute, attribute_value, total_voters, total_male_voters, total_female_voters, province="",canton=""):
        tuple_data = {attribute: attribute_value,
                      'total_votantes': total_voters,
                      'total_votantes_hombres': total_male_voters,
                      'total_votantes_mujeres': total_female_voters
                      }

        if(attribute == 'canton'):
            tuple_data.update({'provincia':province})
         
        elif(attribute == 'distrito'):
            tuple_data.update({'provincia':province,'canton': canton})

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


    def get_province_id(self, province):
        return VotantesPorProvincia.objects.values('codigo_provincia').filter(provincia=province)[0]['codigo_provincia']

    def get_canton_id(self, province,canton):
        return VotantesPorCanton.objects.values('codigo_canton').filter(codigo_provincia__provincia=province,canton=canton)[0]['codigo_canton']

    def bulk_insert(self):
        VotantesPorProvincia.objects.bulk_create(self.provinces_statistics)
        VotantesPorCanton.objects.bulk_create(next(self.cantons_generator()))
        VotantesPorDistrito.objects.bulk_create(next(self.districts_generator()))

    def cantons_generator(self):
        cantons_to_insert = []
        for canton in self.canton_statistics:
            cantons_to_insert.append(VotantesPorCanton(canton = canton['canton'], total_votantes= canton['total_votantes'], total_votantes_hombres=canton['total_votantes_hombres'], total_votantes_mujeres= canton['total_votantes_mujeres'],codigo_provincia_id= self.get_province_id(canton['provincia'])))

        yield cantons_to_insert
    
    def districts_generator(self):
        districts_to_insert = []
        for district in self.district_statistics:
            districts_to_insert.append(VotantesPorDistrito(distrito = district['distrito'], total_votantes= district['total_votantes'], total_votantes_hombres=district['total_votantes_hombres'], total_votantes_mujeres= district['total_votantes_mujeres'],codigo_canton_id= self.get_canton_id(district['provincia'],district['canton'])))

        yield districts_to_insert