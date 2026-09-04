from django.urls import path

from . import views

app_name = "contact"

urlpatterns = [
    path("", views.contact_page, name="page"),
    path("submit/", views.contact_submit, name="submit"),
]
