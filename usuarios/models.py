from django.db import models
from django.contrib.auth.hashers import make_password
from datetime import datetime, date


# =========================================
# USUARIOS
# =========================================

class UsuarioPaciente(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    telefono = models.CharField(max_length=100, unique=True)
    correo = models.CharField(max_length=100, unique=True)
    edad = models.IntegerField()
    sexo = models.CharField(max_length=30)
    contrasena = models.CharField(max_length=100)

    def tipo_usuario(self):
        return "PAC"

    def __str__(self):
        return f"{self.nombre} {self.apellido}"


class UsuarioEstudiante(models.Model):
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100)
    correo = models.CharField(max_length=100, unique=True)
    codigo_estudiante = models.CharField(max_length=9, unique=True)
    semestre = models.IntegerField()
    contrasena = models.CharField(max_length=100)
    area = models.CharField(
        max_length=20,
        choices=[
            ("Diagnóstico", "Diagnóstico"),
            ("Especialidad", "Especialidad")
        ],
        blank=True,
        null=True
    )

    # Nuevos campos
    especialidad = models.CharField(max_length=100, blank=True, null=True)
    horario = models.TextField(blank=True, null=True, default='{}')
    direccion_consultorio = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        area = f" ({self.area})" if self.area else ""
        return f"{self.nombre} {self.apellido}{area}"


# =========================================
# ESTUDIOS Y CITAS
# =========================================

class TipoEstudio(models.Model):
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nombre


class CitaDiagnostico(models.Model):
    paciente = models.ForeignKey(
        UsuarioPaciente,
        on_delete=models.CASCADE,
        related_name='citas_diagnostico'
    )
    nombre_paciente = models.CharField(max_length=100)
    edad_paciente = models.IntegerField()
    fecha = models.DateField()
    hora = models.TimeField()
    descripcion = models.TextField(blank=True, null=True)
    codigo_tarjeton = models.CharField(max_length=20, blank=True, null=True)
    estudiante = models.ForeignKey(
        UsuarioEstudiante,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='citas_diagnostico_asignadas'
    )
    estudios_requeridos = models.ManyToManyField(
        TipoEstudio,
        blank=True,
        related_name='citas_diagnostico'
    )
    otros_estudios = models.TextField(blank=True, null=True)
    habilitada_especialidad = models.BooleanField(default=False)
    especialidad_asignada = models.CharField(max_length=50, blank=True, null=True)

    cancelada = models.BooleanField(default=False)

    def puede_eliminar(self):
        """Solo se puede eliminar si hoy es antes de la fecha de la cita."""
        return not self.cancelada and date.today() < self.fecha
    
    def __str__(self):
        return f"Diagnóstico - {self.nombre_paciente} ({self.fecha} {self.hora})"


class CitaEspecialidad(models.Model):
    paciente = models.ForeignKey(
        UsuarioPaciente,
        on_delete=models.CASCADE,
        related_name='citas_especialidad'
    )
    nombre_paciente = models.CharField(max_length=100)
    edad_paciente = models.IntegerField()
    sexo_paciente = models.CharField(max_length=10, blank=True, null=True)
    telefono_paciente = models.CharField(max_length=20, blank=True, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    especialidad = models.CharField(max_length=50)
    estudiante = models.ForeignKey(
        UsuarioEstudiante,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='citas_especialidad_asignadas'
    )
    habilitada_por = models.ForeignKey(
        CitaDiagnostico,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='citas_especialidad_derivadas'
    )
    descripcion = models.TextField(blank=True, null=True)
    codigo_tarjeton = models.CharField(max_length=20, blank=True, null=True)
    cancelada = models.BooleanField(default=False)

    def puede_eliminar(self):
        """Solo se puede eliminar si hoy es antes de la fecha de la cita."""
        return not self.cancelada and date.today() < self.fecha
    
    def __str__(self):
        return f"Especialidad - {self.nombre_paciente} ({self.fecha} {self.hora})"


class EspecialidadHabilitadaPorPaciente(models.Model):
    paciente = models.ForeignKey(UsuarioPaciente, on_delete=models.CASCADE)
    especialidad = models.CharField(max_length=100)
    cita_diagnostico = models.ForeignKey(CitaDiagnostico, on_delete=models.CASCADE)
    fecha_confirmacion = models.DateTimeField(auto_now_add=True)

class CitaFinalizada(models.Model):
    estudiante = models.ForeignKey(UsuarioEstudiante, on_delete=models.CASCADE)
    paciente = models.ForeignKey(UsuarioPaciente, on_delete=models.CASCADE, null=True, blank=True)
    nombre_paciente = models.CharField(max_length=100)
    edad_paciente = models.IntegerField()
    sexo_paciente = models.CharField(max_length=10, blank=True, null=True)
    telefono_paciente = models.CharField(max_length=20, blank=True, null=True)
    fecha = models.DateField()
    hora = models.TimeField()
    especialidad = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True, null=True)
    codigo_tarjeton = models.CharField(max_length=20, blank=True, null=True)
    fecha_finalizacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre_paciente} - {self.especialidad} ({self.fecha})"