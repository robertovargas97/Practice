from rest_framework import routers
from .views import SingleInteractionReportViewSet, PaymentsReportViewSet, LookupsReportViewSet


router = routers.DefaultRouter()
router.register(r'single/(?P<project_id>\d+)', SingleInteractionReportViewSet, base_name='report_single_interaction')
router.register(r'payments/(?P<project_id>\d+)', PaymentsReportViewSet, base_name='report_payments')
router.register(r'lookups/(?P<project_id>\d+)', LookupsReportViewSet, base_name='report_lookups')

urlpatterns = router.urls
