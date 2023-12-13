from django.shortcuts import render,  redirect ,HttpResponseRedirect , reverse
from django.views.generic import CreateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Elector
from .forms import PollingPlaceForm
from .queries import Queries
from.statistics import Statistics

from challenge_2.settings import DB_ENGINE
from electoral_roll.database_manager.mongo_connection import MongoConnection

connection =  MongoConnection(DB_ENGINE)


def home(request):
    form = PollingPlaceForm()
    template = 'electoral_roll/polling_place_form.html'

    return render(request, template, {'form': form})

def voting_info(request):
    template = 'electoral_roll/voting_information.html'
    polling_statistics = {}

    if(request.method == 'POST'):
        # form = PollingPlaceForm(request.POST)
        # print(form)
        # if(form.is_valid()): #Con cedula no valida :\
        #     print('jajajaja')

        statistics_object = Statistics()

        query_object = Queries(elector_name=request.POST['nombre'],
                               elector_first_surname=request.POST['primer_apellido'],
                               elector_second_surname=request.POST['segundo_apellido'],
                               elector_id=request.POST['cedula'],
                               elector_option=request.POST['option'])

        elector_information = query_object.search_polling_information()

        if(len(elector_information)):
            params = [elector_information['fecha_caducidad'],
                      elector_information['codigo_electoral__provincia'],
                      elector_information['codigo_electoral__canton'],
                      elector_information['codigo_electoral__distrito']]

            polling_statistics = statistics_object.get_polling_statistics(*params)

    return render(request, template, {'elector_information': elector_information, "statistics": polling_statistics})


@login_required
def manage_home(request):
    template = 'electoral_roll/manage_electors_form.html'
    return render(request, template)


class ElectorCreateView(LoginRequiredMixin, CreateView):
    model = Elector
    fields = ['cedula',
              'codigo_electoral',
              'relleno',
              'fecha_caducidad',
              'junta',
              'nombre',
              'primer_apellido',
              'segundo_apellido']

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Elector agregado satisfactoriamente")
        return response


class ElectorDeleteView(LoginRequiredMixin,DeleteView):
    model = Elector
    success_url = '/'

    
    def delete(self, request, *args, **kwargs):
        messages.info(self.request, "Elector eliminado satisfactoriamente")

        if connection.engine == 'mongo':
            connection.delete_elector(kwargs['pk'])
            return HttpResponseRedirect(reverse('electoral_roll-home')) 

        else:
            response = super().delete(request, *args, **kwargs)
            return response

    def get(self, request, *args, **kwargs):

        if connection.engine == 'mongo':
            id_card = kwargs['pk']
            elector = connection.search_by_id_card(id_card)
            return render(request, 'electoral_roll/elector_confirm_delete.html' , {'object':elector})

        return super().get(request, *args, **kwargs)
