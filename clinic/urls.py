from rest_framework_nested.routers import DefaultRouter
from .views import *


router = DefaultRouter()
router.register("categories", CategoryViewSet)
router.register("diseases", DiseaseViewSet)
router.register("doctors", DoctorViewSet)
router.register("treatments", TreatmentViewSet)
router.register("medicines", MedicineViewSet)
router.register("achievements", AchievementViewSet)

urlpatterns = router.urls
