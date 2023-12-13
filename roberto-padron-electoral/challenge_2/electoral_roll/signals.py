from django.db.models import F
from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete

from .models import Elector, VotantesPorCanton, VotantesPorDistrito, VotantesPorProvincia

# Will be execute everytime when an elector is created
@receiver(post_save, sender=Elector)
def update_statistics_create(sender, instance, created, **kwargs):
    if created:
        province = instance.codigo_electoral.provincia
        canton = instance.codigo_electoral.canton
        district = instance.codigo_electoral.distrito
        gender = instance.relleno
        
        update_statistics(province= province, canton = canton,district= district, new_gender=gender,operation='increase')

# Will be execute everytime when an elector is deleted
@receiver(post_delete, sender=Elector)
def update_statistics_delete(sender, instance, **kwargs):
    province = instance.codigo_electoral.provincia
    canton = instance.codigo_electoral.canton
    district = instance.codigo_electoral.distrito
    gender = instance.relleno

    update_statistics(province= province, canton = canton,district= district, new_gender=gender,operation='decrease')

#######################################################################################################################3

def update_statistics(province, canton, district, new_gender, operation):
    province_info = VotantesPorProvincia.objects.get(provincia=province)
    canton_info = VotantesPorCanton.objects.get(codigo_provincia__provincia=province, canton=canton)
    district_info = VotantesPorDistrito.objects.get(codigo_canton__codigo_provincia__provincia=province,
                                                    codigo_canton__canton=canton, distrito=district)

    attribute =  'total_votantes_hombres' if new_gender == '1' else 'total_votantes_mujeres'

    # Is it possible to generalize the operation? The increasing and decreasing code is basically the same. The difference is the operation to be perfmormed
    if (operation == 'increase'):
        setattr(province_info,attribute, (getattr(province_info,attribute) + 1))
        setattr(canton_info,attribute, (getattr(canton_info,attribute) + 1))
        setattr(district_info,attribute, (getattr(district_info,attribute) + 1))

        province_info.total_votantes = F('total_votantes') + 1
        canton_info.total_votantes = F('total_votantes') + 1
        district_info.total_votantes = F('total_votantes') + 1

    elif (operation == 'decrease'):
        setattr(province_info,attribute, (getattr(province_info,attribute) - 1))
        setattr(canton_info,attribute, (getattr(canton_info,attribute) - 1))
        setattr(district_info,attribute, (getattr(district_info,attribute) - 1))

        province_info.total_votantes = F('total_votantes') - 1
        canton_info.total_votantes = F('total_votantes') - 1
        district_info.total_votantes = F('total_votantes') - 1
                                  
    province_info.save()
    canton_info.save()
    district_info.save()

