from django.urls import path

from .views import TeamMemberDetailView, TeamMemberListView

app_name = "team_api"

urlpatterns = [
    path("", TeamMemberListView.as_view(), name="list"),
    path("<slug:slug>/", TeamMemberDetailView.as_view(), name="detail"),
]
