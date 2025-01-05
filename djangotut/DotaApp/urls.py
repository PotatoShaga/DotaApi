from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index") #"" denotes the root url, shows the index() function from views
]