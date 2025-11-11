from usuarios.models import UsuarioPaciente, UsuarioEstudiante, CitaDiagnostico, TipoEstudio, CitaEspecialidad
from django.db import models
from usuarios.models import CitaDiagnostico, CitaEspecialidad, EspecialidadHabilitadaPorPaciente
from django.contrib.auth.hashers import make_password, check_password
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponse
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
from io import BytesIO
import os
from usuarios.forms import (
    UsuarioPacienteForm,
    LoginPacienteForm,
    UsuarioEstudianteForm,
    LoginEstudianteForm
)
from usuarios.models import (
    UsuarioPaciente,
    UsuarioEstudiante,
    CitaDiagnostico,
    TipoEstudio,
    CitaEspecialidad,
    CitaFinalizada
)
from django.db import models
from datetime import date, timedelta, datetime
import json

# ============================
# PACIENTES
# ============================

def registrar_paciente(request):
    if request.method == 'POST':
        form = UsuarioPacienteForm(request.POST)
        if form.is_valid():
            paciente = form.save(commit=False)
            paciente.contrasena = make_password(form.cleaned_data['contrasena'])
            paciente.save()
            return redirect('login_paciente')
    else:
        form = UsuarioPacienteForm()
    return render(request, 'registro_paciente.html', {'form': form})

def login_paciente(request):
    error = None
    form = LoginPacienteForm()

    if request.method == 'POST':
        form = LoginPacienteForm(request.POST)
        if form.is_valid():
            identificador = form.cleaned_data['identificador']
            contrasena = form.cleaned_data['contrasena']

            paciente = UsuarioPaciente.objects.filter(
                models.Q(correo=identificador) | models.Q(telefono=identificador)
            ).first()

            if paciente and check_password(contrasena, paciente.contrasena):
                request.session['paciente_id'] = paciente.id
                request.session['paciente_nombre'] = paciente.nombre
                return redirect('inicio_paciente')
            else:
                error = "Credenciales incorrectas"

    return render(request, 'login_paciente.html', {'form': form, 'error': error})

def inicio_paciente(request):
    # 1️⃣ Verificar sesión activa
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('login_paciente')

    paciente = UsuarioPaciente.objects.get(id=paciente_id)
    error = None

    # 🔹 Inicializar listas para evitar UnboundLocalError
    citas_diag = []
    citas_esp = []

    # 2️⃣ Si el paciente agenda una nueva cita desde aquí
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        if not fecha or not hora:
            messages.error(request, "Debes seleccionar fecha y hora.")
            return redirect('inicio_paciente')

        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            hora_dt = datetime.strptime(hora, "%H:%M").time()
        except Exception:
            messages.error(request, "Formato de fecha u hora inválido.")
            return redirect('inicio_paciente')

        hoy = date.today()

        # 3️⃣ Validaciones
        if not (hoy <= fecha_dt <= hoy + timedelta(days=30)):
            error = "La fecha debe estar dentro de los próximos 30 días."
        elif fecha_dt.weekday() >= 5:
            error = "Solo puedes agendar de lunes a viernes."
        elif not (8 <= hora_dt.hour <= 20):
            error = "El horario debe estar entre 8:00 y 20:00."
        elif CitaDiagnostico.objects.filter(paciente=paciente, cancelada=False).exists():
            error = "Ya tienes una cita activa. No puedes agendar otra hasta cancelarla."
        else:
            # 4️⃣ Guardar cita
            CitaDiagnostico.objects.create(
                paciente=paciente,
                nombre_paciente=paciente.nombre,
                edad_paciente=paciente.edad,
                fecha=fecha_dt,
                hora=hora_dt
            )
            messages.success(request, "Tu cita de diagnóstico fue agendada correctamente.")
            return redirect('inicio_paciente')

    # 5️⃣ Consultar citas existentes (solo activas)
    citas_diag = CitaDiagnostico.objects.filter(
        paciente=paciente, cancelada=False
    ).prefetch_related('estudios_requeridos')

    citas_esp = CitaEspecialidad.objects.filter(
        paciente=paciente, cancelada=False
    ).order_by('-fecha', '-hora')

    citas = list(citas_diag) + list(citas_esp)

    # 6️⃣ Verificar si tiene especialidad habilitada
    habilitada = EspecialidadHabilitadaPorPaciente.objects.filter(paciente=paciente).last()
    especialidad_habilitada = bool(habilitada)
    especialidad_nombre = habilitada.especialidad if habilitada else None

    # 🔹 Verificar si tiene una cita de especialidad activa (no cancelada)
    tiene_especialidad_activa = CitaEspecialidad.objects.filter(
        paciente=paciente,
        cancelada=False
    ).exists()
    cita_especialidad_finalizada = CitaFinalizada.objects.filter(
        paciente=paciente
    ).exists()
    # Mostrar mensaje si ya puede agendar su especialidad
    alerta_especialidad = (
        f"Tu diagnóstico fue completado. Ya puedes agendar tu cita de {especialidad_nombre}."
        if especialidad_habilitada and not tiene_especialidad_activa else None
    )

    # 7️⃣ Preparar datos de los estudiantes disponibles para agendar
    estudiantes_info = []
    if especialidad_habilitada and not tiene_especialidad_activa:
        estudiantes = UsuarioEstudiante.objects.filter(especialidad=especialidad_nombre)
        for est in estudiantes:
            try:
                horarios = json.loads(est.horario)
            except Exception:
                horarios = {}
            estudiantes_info.append({
                'nombre': est.nombre,
                'apellido': est.apellido,
                'especialidad': est.especialidad,
                'area': est.area,
                'id': est.id,
                'horarios': horarios
            })

    # 8️⃣ Fechas válidas próximas 15 días
    hoy = date.today()
    fechas_validas = []
    for i in range(15):
        dia = hoy + timedelta(days=i)
        if dia.weekday() < 6:  # lunes a viernes
            fechas_validas.append(dia.strftime("%Y-%m-%d"))

    # 🔹 Seguimiento clínico (solo citas activas)
    seguimientos = []

    # ---- Diagnóstico ----
    for c in citas_diag:
        seguimientos.append({
            'tipo': 'Diagnóstico',
            'fecha': c.fecha,
            'hora': c.hora,
            'especialidad': c.especialidad_asignada,
            'doctor': f"{c.estudiante.nombre} {c.estudiante.apellido}" if c.estudiante else "Pendiente",
            'recomendaciones': c.descripcion,
            'comentarios': c.otros_estudios or "",
        })

    # ---- Especialidad ----
    for c in citas_esp:
        seguimientos.append({
            'tipo': 'Especialidad',
            'fecha': c.fecha,
            'hora': c.hora,
            'especialidad': c.especialidad,
            'doctor': f"{c.estudiante.nombre} {c.estudiante.apellido}" if c.estudiante else "Pendiente",
            'recomendaciones': c.descripcion,
            'comentarios': "",
        })
    citas_finalizadas = CitaFinalizada.objects.filter(paciente=paciente).order_by('-fecha')

    # Ordenar (más recientes primero)
    seguimientos.sort(key=lambda x: (x['fecha'], x['hora']), reverse=True)

    # 9️⃣ Render final con TODO el contexto
    return render(request, 'inicio_paciente.html', {
        'paciente': paciente,
        'citas': citas,
        'error': error,
        'especialidad_habilitada': especialidad_habilitada,
        'tiene_especialidad_activa': tiene_especialidad_activa,  # ✅ flag principal
        'especialidad_nombre': especialidad_nombre,
        'citas_finalizadas': citas_finalizadas,
        'cita_especialidad_finalizada': cita_especialidad_finalizada,
        'alerta_especialidad': alerta_especialidad,
        'estudiantes_info': estudiantes_info,
        'fechas_validas': fechas_validas,
        'seguimientos': seguimientos,
    })

def confirmar_estudios(request, cita_id):
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('login_paciente')

    paciente = UsuarioPaciente.objects.get(id=paciente_id)
    cita = get_object_or_404(CitaDiagnostico, id=cita_id, paciente=paciente)

    if not cita.estudios_requeridos.exists():
        messages.error(request, "No puedes confirmar estudios si no tienes asignados.")
        return redirect('inicio_paciente')

    # Evita duplicados
    if not EspecialidadHabilitadaPorPaciente.objects.filter(paciente=paciente, cita_diagnostico=cita).exists():
        EspecialidadHabilitadaPorPaciente.objects.create(
            paciente=paciente,
            especialidad=cita.especialidad_asignada,
            cita_diagnostico=cita
        )

    messages.success(request, f"Confirmaste tus estudios. Ya puedes agendar tu cita de {cita.especialidad_asignada}.")
    return redirect('inicio_paciente')

def logout_paciente(request):
    request.session.flush()
    return redirect('login_paciente')

def eliminar_cita(request, tipo, cita_id):
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('login_paciente')

    if tipo == "diagnostico":
        cita = get_object_or_404(CitaDiagnostico, id=cita_id, paciente_id=paciente_id)
    elif tipo == "especialidad":
        cita = get_object_or_404(CitaEspecialidad, id=cita_id, paciente_id=paciente_id)
    else:
        return redirect('inicio_paciente')

    # Si ya no se puede eliminar, simplemente regresa sin mostrar error
    if not cita.puede_eliminar():
        return redirect('inicio_paciente')

    cita.cancelada = True
    cita.save()
    return redirect('inicio_paciente')

# ============================
# ESTUDIANTES
# ============================

def registrar_estudiante(request):
    if request.method == 'POST':
        form = UsuarioEstudianteForm(request.POST)
        if form.is_valid():
            estudiante = form.save(commit=False)
            estudiante.contrasena = make_password(form.cleaned_data['contrasena'])

            try:
                semestre = int(estudiante.semestre)
            except (ValueError, TypeError):
                return render(request, 'registro_estudiante.html', {
                    'form': form,
                    'error': "El semestre debe ser un número válido."
                })

            if semestre < 4:
                return render(request, 'registro_estudiante.html', {
                    'form': form,
                    'error': "Solo se pueden registrar alumnos de 4º semestre en adelante."
                })

            estudiante.area = "Diagnóstico" if semestre == 4 else "Especialidad"
            estudiante.save()
            return redirect('login_estudiante')

        else:
            return render(request, 'registro_estudiante.html', {
                'form': form,
                'error': "Revisa los campos. Puede que falte información o haya un dato duplicado."
            })
    else:
        form = UsuarioEstudianteForm()
    return render(request, 'registro_estudiante.html', {'form': form})

def login_estudiante(request):
    error = None
    form = LoginEstudianteForm()

    if request.method == 'POST':
        form = LoginEstudianteForm(request.POST)
        if form.is_valid():
            identificador = form.cleaned_data['identificador']
            contrasena = form.cleaned_data['contrasena']

            estudiante = UsuarioEstudiante.objects.filter(
                models.Q(correo=identificador) | models.Q(codigo_estudiante=identificador)
            ).first()

            if estudiante and check_password(contrasena, estudiante.contrasena):
                request.session['estudiante_id'] = estudiante.id
                request.session['estudiante_nombre'] = estudiante.nombre
                return redirect('inicio_estudiante')
            else:
                error = "Credenciales incorrectas"

    return render(request, 'login_estudiante.html', {'form': form, 'error': error})

def inicio_estudiante(request):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    estudiante = UsuarioEstudiante.objects.get(id=estudiante_id)

    if estudiante.semestre == 4:
        citas_disponibles = CitaDiagnostico.objects.filter(estudiante__isnull=True).order_by('fecha', 'hora')
        mis_citas = CitaDiagnostico.objects.filter(
            estudiante=estudiante,
            habilitada_especialidad=False  # Solo mostrar si no ha sido habilitada
        ).order_by('fecha', 'hora')
    else:
        citas_disponibles = CitaEspecialidad.objects.filter(estudiante__isnull=True).order_by('fecha', 'hora')
        mis_citas = CitaEspecialidad.objects.filter(estudiante=estudiante).order_by('fecha', 'hora')

    diagnosticos_finalizados = CitaDiagnostico.objects.filter(
        estudiante=estudiante,
        habilitada_especialidad=True
    ).order_by('-fecha')

    total_diagnosticos_finalizados = diagnosticos_finalizados.count()
    estudios = TipoEstudio.objects.all().order_by('nombre')
     # Contador de pacientes habilitados para especialidad
    pacientes_habilitados = CitaDiagnostico.objects.filter(
        estudiante_id=estudiante_id,
        habilitada_especialidad=True
    ).count()

    citas_finalizadas = CitaFinalizada.objects.filter(estudiante=estudiante).order_by('-fecha')
    consultas_finalizadas = citas_finalizadas.count()
    return render(request, 'inicio_estudiante.html', {
        'estudiante': estudiante,
        'citas_disponibles': citas_disponibles,
        'mis_citas': mis_citas,
        'estudios': estudios,
        'pacientes_habilitados': pacientes_habilitados,
        'consultas_finalizadas': consultas_finalizadas,
        'citas_finalizadas': citas_finalizadas,
        'diagnosticos_finalizados': diagnosticos_finalizados,
        'total_diagnosticos_finalizados': total_diagnosticos_finalizados

    })

def finalizar_cita_especialidad(request, cita_id):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    cita = get_object_or_404(CitaEspecialidad, id=cita_id, estudiante_id=estudiante_id)

    # Copiar datos a CitaFinalizada
    CitaFinalizada.objects.create(
        estudiante=cita.estudiante,
        paciente=cita.paciente,
        nombre_paciente=cita.nombre_paciente,
        edad_paciente=cita.edad_paciente,
        sexo_paciente=cita.sexo_paciente,
        telefono_paciente=cita.telefono_paciente,
        fecha=cita.fecha,
        hora=cita.hora,
        especialidad=cita.especialidad,
        descripcion=cita.descripcion,
        codigo_tarjeton=cita.codigo_tarjeton
    )

    # Eliminar la cita (pendiente)
    cita.delete()

    messages.success(request, "La cita fue finalizada correctamente.")
    return redirect('inicio_estudiante')

def asignar_cita(request, cita_id):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    estudiante = UsuarioEstudiante.objects.get(id=estudiante_id)
    cita = get_object_or_404(CitaDiagnostico, id=cita_id)

    conflicto = CitaDiagnostico.objects.filter(
        estudiante=estudiante,
        fecha=cita.fecha,
        hora=cita.hora
    ).exists()

    if conflicto:
        messages.error(request, f"Ya tienes una cita asignada el {cita.fecha} a las {cita.hora}.")
    elif cita.estudiante is not None:
        messages.error(request, "Esta cita ya fue tomada por otro estudiante.")
    else:
        cita.estudiante = estudiante
        cita.save()
        messages.success(request, f"Te asignaste la cita de {cita.nombre_paciente}.")

    return redirect('inicio_estudiante')

def actualizar_cita_estudiante(request, cita_id):
    """Permite que el estudiante agregue descripción, tarjetón y estudios requeridos."""
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    cita = get_object_or_404(CitaDiagnostico, id=cita_id, estudiante_id=estudiante_id)

    if request.method == 'POST':
        cita.descripcion = request.POST.get('descripcion', '').strip()
        cita.codigo_tarjeton = request.POST.get('codigo_tarjeton', '').strip()
        cita.otros_estudios = request.POST.get('otros_estudios', '').strip()

        # Guardar la cita primero para asegurar persistencia del tarjetón
        cita.save()

        # Guardar estudios seleccionados
        estudios_ids = request.POST.getlist('estudios_requeridos')
        cita.estudios_requeridos.set(estudios_ids)

        # Agregar nuevo estudio si fue escrito
        nuevo_estudio = request.POST.get('nuevo_estudio', '').strip()
        if nuevo_estudio:
            tipo, _ = TipoEstudio.objects.get_or_create(nombre=nuevo_estudio)
            cita.estudios_requeridos.add(tipo)

        messages.success(request, f"Cita actualizada correctamente. Tarjetón: {cita.codigo_tarjeton or 'Pendiente'}")
        return redirect('inicio_estudiante')

    return redirect('inicio_estudiante')

def logout_estudiante(request):
    request.session.flush()
    return redirect('login_estudiante')

# ============================
# ESPECIALIDADES
# ============================

def habilitar_especialidad(request, cita_id):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    cita = get_object_or_404(CitaDiagnostico, id=cita_id, estudiante_id=estudiante_id)
    if request.method == 'POST':
        cita.habilitada_especialidad = True
        cita.especialidad_asignada = request.POST.get('especialidad_asignada', '')
        cita.save()
        messages.success(request, f"El paciente {cita.nombre_paciente} fue habilitado para {cita.especialidad_asignada}.")
        return redirect('inicio_estudiante')

    especialidades = [
        "Endodoncia", "Ortodoncia", "Periodoncia", "Prótesis", "Cirugía Oral"
    ]

    # 🔹 Agregamos la especialidad seleccionada (si existe) para mostrarla en el título
    especialidad_nombre = cita.especialidad_asignada if cita.especialidad_asignada else None

    return render(request, 'habilitar_especialidad.html', {
        'cita': cita,
        'especialidades': especialidades,
        'especialidad_nombre': especialidad_nombre,
    })


def agendar_cita_especialidad(request, estudiante_id):
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('login_paciente')

    paciente = get_object_or_404(UsuarioPaciente, id=paciente_id)
    estudiante = get_object_or_404(UsuarioEstudiante, id=estudiante_id)
    habilitada = EspecialidadHabilitadaPorPaciente.objects.filter(paciente=paciente).last()
    cita_diag = CitaDiagnostico.objects.filter(paciente=paciente).last()

    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')

        if not fecha or not hora:
            messages.error(request, "Debes seleccionar fecha y hora.")
            return redirect('inicio_paciente')

        try:
            fecha_dt = datetime.strptime(fecha, "%Y-%m-%d").date()
            hora_dt = datetime.strptime(hora, "%H:%M").time()
        except Exception:
            messages.error(request, "Formato de fecha u hora inválido.")
            return redirect('inicio_paciente')

        # Validar disponibilidad del horario del estudiante
        if CitaEspecialidad.objects.filter(estudiante=estudiante, fecha=fecha_dt, hora=hora_dt, cancelada=False).exists():
            messages.error(request, "Ese horario ya está ocupado.")
            return redirect('inicio_paciente')

        # Verificar si el paciente ya tiene una cita de especialidad activa
        if CitaEspecialidad.objects.filter(paciente=paciente, cancelada=False).exists():
            messages.error(request, "Ya tienes una cita de especialidad activa.")
            return redirect('inicio_paciente')

        # Validar que la especialidad esté habilitada
        if not habilitada:
            messages.error(request, "Aún no tienes habilitada la especialidad para agendar esta cita.")
            return redirect('inicio_paciente')

        # Evitar fallos si el diagnóstico previo no existe (por seguridad)
        descripcion_diag = cita_diag.descripcion if cita_diag else ""
        codigo_diag = cita_diag.codigo_tarjeton if cita_diag else None
        cita_origen = cita_diag if cita_diag else None

        # ✅ Guardar la nueva cita
        CitaEspecialidad.objects.create(
            paciente=paciente,
            estudiante=estudiante,
            fecha=fecha_dt,
            hora=hora_dt,
            especialidad=habilitada.especialidad,
            descripcion=descripcion_diag,
            codigo_tarjeton=codigo_diag,
            habilitada_por=cita_origen,
            nombre_paciente=paciente.nombre,
            edad_paciente=paciente.edad,
            telefono_paciente=paciente.telefono,
            sexo_paciente=paciente.sexo
        )

        messages.success(request, "Tu cita de especialidad fue agendada correctamente.")
        return redirect('inicio_paciente')

    # Si entra por GET, redirigir
    return redirect('inicio_paciente')


def asignar_cita_especialidad(request, cita_id):
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    estudiante = UsuarioEstudiante.objects.get(id=estudiante_id)
    cita = get_object_or_404(CitaEspecialidad, id=cita_id)

    conflicto = CitaEspecialidad.objects.filter(
        estudiante=estudiante,
        fecha=cita.fecha,
        hora=cita.hora
    ).exists()

    if conflicto:
        messages.error(request, "Ya tienes otra cita asignada en ese horario.")
    elif cita.estudiante:
        messages.error(request, "Esta cita ya fue tomada.")
    else:
        cita.estudiante = estudiante
        cita.save()
        messages.success(request, f"Te asignaste la cita de {cita.nombre_paciente}.")

    return redirect('inicio_estudiante')

# PERFIL PACIENTE
def perfil_paciente(request):
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('login_paciente')

    paciente = get_object_or_404(UsuarioPaciente, id=paciente_id)

    # 🔹 Obtener el último código de tarjetón si el paciente tiene citas diagnósticas
    ultima_cita = (
        CitaDiagnostico.objects.filter(paciente=paciente)
        .order_by('-fecha', '-hora')
        .first()
    )
    codigo_tarjeton = ultima_cita.codigo_tarjeton if ultima_cita and ultima_cita.codigo_tarjeton else "No asignado"

    if request.method == 'POST':
        correo = request.POST.get('correo', '').strip()
        telefono = request.POST.get('telefono', '').strip()
        edad = request.POST.get('edad', '').strip()
        sexo = request.POST.get('sexo', '').strip()

        # Validamos que al menos uno cambie (opcional)
        if correo or telefono or edad or sexo:
            paciente.correo = correo or paciente.correo
            paciente.telefono = telefono or paciente.telefono
            paciente.edad = edad or paciente.edad
            paciente.sexo = sexo or paciente.sexo

            paciente.save()
            messages.success(request, "✅ Datos actualizados correctamente.")
        else:
            messages.warning(request, "⚠️ No se detectaron cambios.")

        return redirect('perfil_paciente')

    # 🔹 Pasamos también el código de tarjetón al template
    return render(request, 'perfil_paciente.html', {
        'paciente': paciente,
        'codigo_tarjeton': codigo_tarjeton
    })

# PERFIL ESTUDIANTE
def perfil_estudiante(request):
    """
    Vista para mostrar y actualizar los datos del estudiante.
    - Si el semestre es 4: Diagnóstico.
    - Si el semestre es >=5: Especialidad + horario de atención.
    """
    # Obtener el estudiante en sesión
    estudiante_id = request.session.get('estudiante_id')
    if not estudiante_id:
        return redirect('login_estudiante')

    estudiante = get_object_or_404(UsuarioEstudiante, id=estudiante_id)

    # Cargar horario existente (convertir texto a diccionario)
    try:
        horario = json.loads(estudiante.horario or '{}')
    except json.JSONDecodeError:
        horario = {}

    if request.method == 'POST':
        # Obtener campos del formulario
        correo = request.POST.get('correo', '').strip()
        codigo_estudiante = request.POST.get('codigo_estudiante', '').strip()
        semestre = request.POST.get('semestre', '').strip()
        area = request.POST.get('area', '').strip()
        especialidad = request.POST.get('especialidad', '').strip()
        direccion_consultorio = request.POST.get('direccion_consultorio', '').strip()

        # Validar semestre
        if not semestre:
            semestre = estudiante.semestre
        else:
            try:
                semestre = int(semestre)
            except ValueError:
                messages.error(request, "⚠️ El semestre debe ser un número válido.")
                return redirect('perfil_estudiante')

        # Actualizar campos generales
        estudiante.correo = correo or estudiante.correo
        estudiante.codigo_estudiante = codigo_estudiante or estudiante.codigo_estudiante
        estudiante.semestre = semestre or estudiante.semestre
        estudiante.direccion_consultorio = direccion_consultorio or estudiante.direccion_consultorio

        # --- Asignar área y especialidad automáticamente ---
        if semestre == 4:
            estudiante.area = "Diagnóstico"
            estudiante.especialidad = "Diagnóstico"
        elif semestre >= 5:
            estudiante.area = "Especialidad"
            if especialidad:
                estudiante.especialidad = especialidad
            else:
                messages.error(request, "⚠️ Debes seleccionar una especialidad.")
                return redirect('perfil_estudiante')
        else:
            estudiante.area = area or estudiante.area
            estudiante.especialidad = None

        # --- Guardar horario (solo si es de 5° o más) ---
        if semestre >= 5:
            dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]
            horario_data = {}
            for dia in dias:
                inicio = request.POST.get(f"{dia.lower()}_inicio")
                fin = request.POST.get(f"{dia.lower()}_fin")
                if inicio and fin:
                    horario_data[dia] = [inicio, fin]
            estudiante.horario = json.dumps(horario_data)
        else:
            estudiante.horario = '{}'

        # Guardar cambios
        estudiante.save()
        messages.success(request, "✅ Datos actualizados correctamente.")
        return redirect('perfil_estudiante')

    # Días para el calendario (evita el error .split() en el template)
    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado"]

    return render(request, 'perfil_estudiante.html', {
        'estudiante': estudiante,
        'horario': horario,
        'dias': dias
    })

def descargar_historial_pdf(request):
    paciente_id = request.session.get('paciente_id')
    if not paciente_id:
        return redirect('login_paciente')

    paciente = UsuarioPaciente.objects.get(id=paciente_id)
    citas_diag = CitaDiagnostico.objects.filter(paciente=paciente).prefetch_related('estudios_requeridos')
    citas_esp = CitaEspecialidad.objects.filter(paciente=paciente)

    # Crear buffer PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=70,
        bottomMargin=50
    )
    story = []

    # ======= ESTILOS =======
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SubTitulo', fontSize=14, leading=18, textColor=colors.HexColor("#0d6efd"), spaceAfter=8))
    styles.add(ParagraphStyle(name='NormalJust', fontSize=10, leading=14, alignment=4))  # Justificado
    styles.add(ParagraphStyle(name='FechaDerecha', fontSize=10, alignment=2))  # A la derecha

    # ======= ENCABEZADO (LOGO IZQUIERDA + FECHA DERECHA) =======
    logo_path = os.path.join('usuarios', 'static', 'imagenes', 'logo.png')
    fecha_actual = datetime.now().strftime("%d/%m/%Y")

    # Imagen del logo
    logo_img = None
    if os.path.exists(logo_path):
        logo_img = Image(logo_path, width=100, height=100)

    # Texto de la fecha (dos líneas)
    fecha_texto = Paragraph(f"<b>Fecha de emisión:</b><br/>{fecha_actual}", styles['FechaDerecha'])

    encabezado_data = [[logo_img or '', fecha_texto]]

    encabezado_table = Table(encabezado_data, colWidths=[80, 420])
    encabezado_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))

    story.append(encabezado_table)
    story.append(Spacer(1, 10))

    # ======= TÍTULOS =======
    story.append(Paragraph("<b>PerfectTeeth</b>", styles['Title']))
    story.append(Paragraph("<b>Reporte de Historial Clínico</b>", styles['SubTitulo']))
    story.append(Spacer(1, 10))

    # ======= DATOS DEL PACIENTE =======
    story.append(Paragraph(f"<b>Nombre:</b> {paciente.nombre} {paciente.apellido}", styles['Normal']))
    story.append(Paragraph(f"<b>Edad:</b> {paciente.edad} años", styles['Normal']))
    story.append(Paragraph(f"<b>Sexo:</b> {paciente.sexo}", styles['Normal']))
    story.append(Paragraph(f"<b>Teléfono:</b> {paciente.telefono}", styles['Normal']))
    story.append(Paragraph(f"<b>Correo:</b> {paciente.correo}", styles['Normal']))
    story.append(Spacer(1, 18))

    # ======= FUNCIONES AUXILIARES =======
    def limpiar_texto(texto):
        if not texto:
            return "N/A"
        return "<br/>".join([line.strip() for line in texto.splitlines() if line.strip()])

    def alternar_color_fila(idx):
        return colors.whitesmoke if idx % 2 == 0 else colors.lightgrey

    # ======= CITAS DE DIAGNÓSTICO =======
    story.append(Paragraph("Citas de Diagnóstico", styles['SubTitulo']))

    if citas_diag:
        data = [["Fecha", "Hora", "Descripción", "Código Tarjetón", "Estudiante", "Especialidad", "Estudios Requeridos"]]
        for i, c in enumerate(citas_diag, start=1):
            estudiante = f"{c.estudiante.nombre} {c.estudiante.apellido}" if c.estudiante else "Sin asignar"
            descripcion = limpiar_texto(c.descripcion)
            estudios_list = [e.nombre for e in c.estudios_requeridos.all()]
            estudios_text = "<br/>".join(estudios_list) if estudios_list else "N/A"

            data.append([
                str(c.fecha),
                str(c.hora),
                Paragraph(descripcion, styles['NormalJust']),
                c.codigo_tarjeton or "Pendiente",
                estudiante,
                c.especialidad_asignada or "N/A",
                Paragraph(estudios_text, styles['NormalJust']),
            ])

        table = Table(data, colWidths=[60, 50, 130, 70, 90, 80, 110])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0d6efd")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ]))

        for i in range(1, len(data)):
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), alternar_color_fila(i)),
            ]))

        story.append(table)
    else:
        story.append(Paragraph("No hay citas de diagnóstico registradas.", styles['Normal']))

    story.append(Spacer(1, 18))

    # ======= CITAS DE ESPECIALIDAD =======
    story.append(Paragraph("Citas de Especialidad", styles['SubTitulo']))

    if citas_esp:
        data = [["Fecha", "Hora", "Especialidad", "Descripción", "Código Tarjetón", "Estudiante"]]
        for i, c in enumerate(citas_esp, start=1):
            estudiante = f"{c.estudiante.nombre} {c.estudiante.apellido}" if c.estudiante else "Sin asignar"
            descripcion = limpiar_texto(c.descripcion)
            data.append([
                str(c.fecha),
                str(c.hora),
                c.especialidad,
                Paragraph(descripcion, styles['NormalJust']),
                c.codigo_tarjeton or "Pendiente",
                estudiante
            ])
        table = Table(data, colWidths=[65, 50, 100, 140, 80, 100])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#198754")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('GRID', (0, 0), (-1, -1), 0.25, colors.gray),
        ]))
        for i in range(1, len(data)):
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, i), (-1, i), alternar_color_fila(i)),
            ]))
        story.append(table)
    else:
        story.append(Paragraph("No hay citas de especialidad registradas.", styles['Normal']))

    story.append(Spacer(1, 20))
    story.append(Paragraph("<i>Reporte generado automáticamente por PerfectTeeth.</i>", styles['Normal']))

    # ======= GENERAR PDF =======
    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    filename = f"Historial_{paciente.nombre}_{paciente.apellido}.pdf"
    response['Content-Disposition'] = f'attachment; filename=\"{filename}\"'
    return response