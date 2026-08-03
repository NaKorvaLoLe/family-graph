from django.urls import path

from . import views

app_name = 'family'

urlpatterns = [
    path('', views.index, name='index'),
    path('person/<int:pk>/', views.person_detail, name='person_detail'),
    path('api/graph/', views.graph_api, name='graph_api'),
    path('api/graph/positions/', views.save_positions, name='save_positions'),
]
