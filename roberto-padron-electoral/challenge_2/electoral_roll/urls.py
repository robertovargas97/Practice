from django.urls import path
from . import views
from .views import ElectorCreateView,ElectorDeleteView

urlpatterns = [
    path('', views.home, name='electoral_roll-home'),
    path('voting_info', views.voting_info, name='voting-information'), 
    path('manage_electors', views.manage_home, name='manage-home'), 
    path('manage_electors/new/', ElectorCreateView.as_view(), name='elector-create'),
    path('voting_info/<str:pk>/delete', ElectorDeleteView.as_view(), name='elector-delete'),

]