from django.urls import path

from .views import ProjectDetailView, ProjectListView

app_name = "projects_api"

urlpatterns = [
    path("", ProjectListView.as_view(), name="list"),
    path("<slug:slug>/", ProjectDetailView.as_view(), name="detail"),
]
