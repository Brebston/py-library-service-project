from django.urls import include, path
from rest_framework.routers import DefaultRouter

from borrowings.views import BorrowingViewSet

router = DefaultRouter()
router.register("", BorrowingViewSet, basename="borrowings")

urlpatterns = [path("", include(router.urls))]

app_name = "borrowings"
