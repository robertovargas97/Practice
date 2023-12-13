from rest_framework import routers
from .views import TransactionViewSet


router = routers.DefaultRouter()
router.register(r'transactions/(?P<project_id>\d+)', TransactionViewSet, base_name='transactions')

urlpatterns = router.urls
