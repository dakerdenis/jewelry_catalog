from django.urls import path
from . import views

app_name = "catalog"

urlpatterns = [
    path("", views.landing_view, name="landing"),                 # /
    path("catalog/", views.product_list_view, name="list"),       # /catalog/
    path("collections/", views.collections_view, name="collections"),  # /collections/
    path("product/<slug:slug>/", views.product_detail_view, name="detail"),  # /product/<slug>/
]
