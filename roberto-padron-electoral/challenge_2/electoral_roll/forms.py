from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Elector


class PollingPlaceForm(forms.ModelForm):

    # nombre = forms.CharField(required=False)
    # primer_apellido = forms.CharField(required=False)
    # segundo_apellido = forms.CharField(required=False)
    # cedula = forms.CharField(required=False,max_length=9)
    
    # Gives us a namespace
    class Meta:
        model = Elector  # Model that will be afected
        fields = ['nombre', 'primer_apellido','segundo_apellido', 'cedula']  # The fields to show
