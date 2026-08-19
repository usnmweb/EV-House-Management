from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("services/", views.services, name="services"),
    path("gallery/", views.gallery, name="gallery"),
    path("contact/", views.contact, name="contact"),
    path("privacy/", views.privacy, name="privacy"),
    path("cookies/", views.cookies, name="cookies"),
]
