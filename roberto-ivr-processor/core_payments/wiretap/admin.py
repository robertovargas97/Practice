from django.contrib import admin
from wiretap.models import Message, Tap

# Register your models here.

admin.site.register(Message)
admin.site.register(Tap)
