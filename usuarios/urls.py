from django.urls import path
from usuarios.views import *

urlpatterns = [
    # --- PACIENTE ---
    path('login_paciente/', login_paciente, name='login_paciente'),
    path('registro_paciente/', registrar_paciente, name='registro_paciente'),
    path('inicio_paciente/', inicio_paciente, name='inicio_paciente'),
    path('logout_paciente/', logout_paciente, name='logout_paciente'),
    path('eliminar_cita/<str:tipo>/<int:cita_id>/', eliminar_cita, name='eliminar_cita'),

    # --- ESTUDIANTE ---
    path('login_estudiante/', login_estudiante, name='login_estudiante'),
    path('registro_estudiante/', registrar_estudiante, name='registro_estudiante'),
    path('inicio_estudiante/', inicio_estudiante, name='inicio_estudiante'),
    path('asignar_cita/<int:cita_id>/', asignar_cita, name='asignar_cita'),
    path('actualizar_cita/<int:cita_id>/', actualizar_cita_estudiante, name='actualizar_cita_estudiante'),
    path('logout_estudiante/', logout_estudiante, name='logout_estudiante'),

    # --- ESPECIALIDAD ---
    path('habilitar_especialidad/<int:cita_id>/', habilitar_especialidad, name='habilitar_especialidad'),
    path('asignar_cita_especialidad/<int:cita_id>/', asignar_cita_especialidad, name='asignar_cita_especialidad'),
    path('confirmar_estudios/<int:cita_id>/', confirmar_estudios, name='confirmar_estudios'),
    path('agendar_cita_especialidad/<int:estudiante_id>/', agendar_cita_especialidad, name='agendar_cita_especialidad'),
    path('finalizar_cita_especialidad/<int:cita_id>/', finalizar_cita_especialidad, name='finalizar_cita_especialidad'),
    # --- PERFIL ---
    path('perfil-paciente/', perfil_paciente, name='perfil_paciente'),
    path('perfil-estudiante/', perfil_estudiante, name='perfil_estudiante'),
    path('descargar_historial_pdf/', descargar_historial_pdf, name='descargar_historial_pdf'),


]
