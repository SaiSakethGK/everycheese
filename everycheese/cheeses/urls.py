"""
URL configuration for the EveryCheese cheese catalogue.

Author: Sai Saketh Gooty Kase
"""

from django.urls import path

from . import views

app_name = "cheeses"

urlpatterns = [
    path(
        "",
        views.CheeseListView.as_view(),
        name="list",
    ),
    path(
        "add/",
        views.CheeseCreateView.as_view(),
        name="add",
    ),
    path(
        "<slug:slug>/",
        views.CheeseDetailView.as_view(),
        name="detail",
    ),
    path(
        "update/<slug:slug>/",
        views.CheeseUpdateView.as_view(),
        name="update",
    ),
    path(
        "delete/<slug:slug>/",
        views.CheeseDeleteView.as_view(),
        name="delete",
    ),
    path(
        "rate/<slug:slug>/",
        views.RateCheeseView.as_view(),
        name="rate",
    ),
]
