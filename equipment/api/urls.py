from django.urls import path

from .views import EquipmentCategoryListView

app_name = "equipment_api"

urlpatterns = [
    path("categories/", EquipmentCategoryListView.as_view(), name="categories"),
]
