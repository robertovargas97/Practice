from django.db import models
from django.db.models import Index
from django.urls import reverse
from datetime import datetime
from challenge_2.settings import DB_ENGINE
from electoral_roll.database_manager.mongo_connection import MongoConnection

connection =  MongoConnection(DB_ENGINE)

class DistritoElectoral(models.Model):
    codigo_electoral = models.CharField(
        max_length=6, primary_key=True, unique=True)
    provincia = models.CharField(max_length=10)
    canton = models.CharField(max_length=26)
    distrito = models.CharField(max_length=36)

    def __str__(self):
        return "%s-%s-%s" % (self.provincia, self.canton, self.distrito)

    class Meta:
        indexes = [Index(fields=['codigo_electoral'])]
        ordering = ['codigo_electoral']


class Elector(models.Model):
    cedula = models.CharField(max_length=9, primary_key=True, unique=True)
    codigo_electoral = models.ForeignKey(
        'DistritoElectoral', on_delete=models.CASCADE)
    relleno = models.CharField(max_length=1)
    fecha_caducidad = models.DateTimeField()
    junta = models.CharField(max_length=5)
    nombre = models.CharField(max_length=30)
    primer_apellido = models.CharField(max_length=26)
    segundo_apellido = models.CharField(max_length=26)

    # Function to redirect when an elector is successfully created
    def get_absolute_url(self):
        return reverse('electoral_roll-home')

    # Function to upperCase the elector name
    def save(self, *args, **kwargs):

        if(DB_ENGINE == 'mongo'):
            new_data = [self.cedula, self.codigo_electoral.codigo_electoral, self.relleno,self.fecha_caducidad,self.junta,self.nombre.upper(),  self.primer_apellido.upper(), self.segundo_apellido.upper()]
            connection.insert_new_elector(new_data)

        else:
            self.nombre = self.nombre.upper()
            self.primer_apellido = self.primer_apellido.upper()
            self.segundo_apellido = self.segundo_apellido.upper()
            self.fecha_caducidad = datetime(self.fecha_caducidad.year,self.fecha_caducidad.month,self.fecha_caducidad.day,18)
            super().save(*args, **kwargs)

    
    class Meta:
        indexes = [Index(fields=['cedula']),
                   Index(fields=['nombre']),
                   Index(fields=['primer_apellido']),
                   Index(fields=['segundo_apellido']),
                   Index(fields=['fecha_caducidad']),
                   Index(fields=['codigo_electoral'])]

        ordering = ['codigo_electoral']

    def __str__(self):
        return "%s: %s %s" % (self.cedula, self.nombre, self.primer_apellido)


class VotantesPorProvincia(models.Model):
    codigo_provincia = models.AutoField(primary_key=True)
    provincia = models.CharField(max_length=10, unique=True)
    total_votantes = models.IntegerField()
    total_votantes_hombres = models.IntegerField()
    total_votantes_mujeres = models.IntegerField()

    class Meta:
        indexes = [Index(fields=['codigo_provincia']),
                   Index(fields=['provincia'])]

        ordering = ['codigo_provincia']

    def __str__(self):
        return "%s: %d" % (self.provincia, self.total_votantes)


class VotantesPorCanton(models.Model):
    codigo_canton = models.AutoField(primary_key=True)
    codigo_provincia = models.ForeignKey(
        'VotantesPorProvincia', on_delete=models.CASCADE)
    canton = models.CharField(max_length=26)
    total_votantes = models.IntegerField()
    total_votantes_hombres = models.IntegerField()
    total_votantes_mujeres = models.IntegerField()

    class Meta:
        indexes = [Index(fields=['codigo_canton']),
                   Index(fields=['canton']),
                   Index(fields=['codigo_provincia'])]

        ordering = ['codigo_provincia']

    def __str__(self):
        return "%s: %d" % (self.canton, self.total_votantes)


class VotantesPorDistrito(models.Model):
    codigo_distrito = models.AutoField(primary_key=True)
    codigo_canton = models.ForeignKey(
        'VotantesPorCanton', on_delete=models.CASCADE)
    distrito = models.CharField(max_length=36)
    total_votantes = models.IntegerField()
    total_votantes_hombres = models.IntegerField()
    total_votantes_mujeres = models.IntegerField()

    class Meta:
        indexes = [Index(fields=['codigo_canton'])]
        ordering = ['codigo_canton']

    def __str__(self):
        return "%s: %d" % (self.distrito, self.total_votantes)
