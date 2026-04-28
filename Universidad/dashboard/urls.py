from django.urls import path
from . import views

urlpatterns = [
    # Vistas principales
    path('', views.index, name='index'),
    path('carga/', views.carga_excel, name='carga'),
    path('kpis/', views.dashboard_kpis, name='kpis'),
    
    # APIs JSON
    path('api/resumen/', views.api_resumen, name='api_resumen'),
    path('api/servicios-por-dia/', views.api_servicios_por_dia, name='api_servicios_dia'),
    path('api/kpis/', views.api_kpis, name='api_kpis'),
    path('api/filtros/', views.api_filtros, name='api_filtros'),
]