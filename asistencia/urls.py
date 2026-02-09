# asistencia/urls.py
from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Login y Logout
    path('accounts/login/', auth_views.LoginView.as_view(template_name='asistencia/login.html'), name='login'),
    path('logout/', views.cerrar_sesion, name='logout'),

    # Flujo del Profesor
    path('seleccionar/', views.seleccionar_materia, name='seleccionar_materia'),
    path('', views.dashboard_profesor, name='dashboard'), # El dashboard es el Home
    path('historial/', views.historial_asistencias, name='historial'),
    path('registro/', views.pagina_registro, name='registro'),
    path('carga-manual/', views.carga_masiva, name='carga_manual'),
    path('api/check-salida/<int:asistencia_id>/', views.confirmar_salida, name='check_salida'),

    # APIs (Para ESP32 y JS)
    path('api/rfid/', views.recibir_rfid, name='api_rfid'),
    path('api/get-uid/', views.obtener_uid_temporal, name='get_uid'),
    path('api/guardar-estudiante/', views.guardar_nuevo_estudiante, name='guardar_estudiante'),
]