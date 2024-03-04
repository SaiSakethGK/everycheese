# everycheese/cheeses/urls.py
from django.urls import path
from . import views

app_name = "cheeses"
urlpatterns = [
    path(
        route='',
        view=views.CheeseListView.as_view(),
        name='list'
    ),
    path(
        route='add/',
        view=views.CheeseCreateView.as_view(),
        name='add'
    ),
    path(
        route='<slug:slug>/',
        view=views.CheeseDetailView.as_view(),
        name='detail'
    ),
    path('delete/<slug:slug>/', views.CheeseDeleteView.as_view(), name='delete'),
    path('confirm_delete/<slug:slug>/', views.ConfirmCheeseDeleteView.as_view(), name='confirm_delete'),
    path('update/<slug:slug>/', views.CheeseUpdateView.as_view(), name='update'),
]