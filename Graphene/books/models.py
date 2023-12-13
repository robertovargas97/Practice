from django.db import models


class Author(models.Model):
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    
    def __str__(self):
        return self.name


# Create your models here.
class Books(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    author = models.ForeignKey(to=Author, on_delete=models.CASCADE)

    def __str__(self):
        return self.title
