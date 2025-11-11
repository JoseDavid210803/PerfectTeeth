from django import forms
from usuarios.models import UsuarioPaciente, UsuarioEstudiante
from usuarios.models import CitaDiagnostico
from datetime import date, timedelta

class UsuarioPacienteForm(forms.ModelForm):
    contrasena = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UsuarioPaciente
        fields = ['nombre', 'apellido', 'telefono', 'correo', 'edad', 'sexo', 'contrasena']


class UsuarioEstudianteForm(forms.ModelForm):
    contrasena = forms.CharField(widget=forms.PasswordInput)

    class Meta:
        model = UsuarioEstudiante
        fields = ['nombre', 'apellido', 'correo', 'codigo_estudiante', 'semestre', 'contrasena']


class LoginPacienteForm(forms.Form):
    identificador = forms.CharField(label="Correo o Teléfono")
    contrasena = forms.CharField(widget=forms.PasswordInput)


class LoginEstudianteForm(forms.Form):
    identificador = forms.CharField(label="Correo o Código de estudiante")
    contrasena = forms.CharField(widget=forms.PasswordInput)
