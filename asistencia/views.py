from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import logout
from .models import Estudiante, Asistencia, Materia, Profesor
from django.shortcuts import get_object_or_404

# --- VARIABLE GLOBAL ---
# Para guardar temporalmente UIDs desconocidos (para el registro)
ultimo_uid_desconocido = None

# =======================================================
# 1. SECCIÓN DEL PROFESOR (WEB)
# =======================================================

@login_required
def seleccionar_materia(request):
    """
    Página donde el profesor elige qué clase va a dar.
    """
    try:
        # Obtenemos el perfil de profesor del usuario logueado
        perfil_profesor = request.user.profesor
    except:
        # Si entra el 'admin' puro sin perfil de profesor, mostramos error
        return render(request, 'asistencia/error.html', {'mensaje': 'Este usuario no tiene perfil de Profesor asignado.'})

    # Filtramos solo las materias de ESTE profesor
    materias = Materia.objects.filter(profesor=perfil_profesor)

    if request.method == 'POST':
        materia_id = request.POST.get('materia_id')
        materia_seleccionada = get_object_or_404(Materia, id=materia_id)

        # Seguridad: Verificar que la materia sea de este profesor
        if materia_seleccionada.profesor != perfil_profesor:
            return redirect('seleccionar_materia')

        # 1. Apagamos todas sus clases anteriores
        Materia.objects.filter(profesor=perfil_profesor).update(en_curso=False)
        
        # 2. Encendemos la nueva
        materia_seleccionada.en_curso = True
        materia_seleccionada.save()

        return redirect('dashboard')

    return render(request, 'asistencia/seleccionar_materia.html', {'materias': materias})


@login_required
def dashboard_profesor(request):
    """
    Pantalla principal donde aparecen los alumnos llegando.
    """
    try:
        perfil_profesor = request.user.profesor
        # Buscamos cuál es la materia que el profesor tiene ACTIVA
        materia_activa = Materia.objects.get(profesor=perfil_profesor, en_curso=True)
    except:
        # Si no ha seleccionado ninguna, lo mandamos a seleccionar
        return redirect('seleccionar_materia')

    hoy = timezone.now().date()
    
    # Filtramos asistencias de HOY y de la MATERIA ACTIVA
    asistencias = Asistencia.objects.filter(
        fecha=hoy, 
        materia=materia_activa
    ).order_by('-hora_llegada')

    return render(request, 'asistencia/dashboard.html', {
        'asistencias': asistencias,
        'materia': materia_activa
    })


def cerrar_sesion(request):
    """
    Cierra la sesión y 'apaga' la clase activa.
    """
    if request.user.is_authenticated:
        try:
            # Apagamos las clases de este profesor al salir
            perfil_profesor = request.user.profesor
            Materia.objects.filter(profesor=perfil_profesor).update(en_curso=False)
        except:
            pass
    
    logout(request)
    return redirect('login') # Asegúrate de tener configurada la URL 'login'


@login_required
def historial_asistencias(request):
    fecha_busqueda = request.GET.get('fecha')
    asistencias = []
    materia_nombre = "Todas"

    if fecha_busqueda:
        # Opcional: Filtrar también por las materias de este profesor
        asistencias = Asistencia.objects.filter(
            fecha=fecha_busqueda,
            profesor__isnull=True # Solo alumnos
            # Aquí podrías agregar filtro por profesor si quisieras privacidad total
        ).order_by('estudiante__nombre')

    return render(request, 'asistencia/historial.html', {
        'asistencias': asistencias,
        'fecha_seleccionada': fecha_busqueda
    })


# =======================================================
# 2. SECCIÓN LÓGICA RFID (ESP32)
# =======================================================

@csrf_exempt
def recibir_rfid(request):
    global ultimo_uid_desconocido
    
    if request.method == 'POST':
        uid = request.POST.get('uid')
        hoy = timezone.now().date()

        # -----------------------------------------------
        # PASO 1: ¿ES EL PROFESOR?
        # -----------------------------------------------
        try:
            profe = Profesor.objects.get(rfid_uid=uid)
            
            # Buscamos qué materia activó en la web
            try:
                materia_activa = Materia.objects.get(profesor=profe, en_curso=True)
                
                # Registramos su asistencia (Esto "ABRE" la puerta a los alumnos)
                if not Asistencia.objects.filter(profesor=profe, materia=materia_activa, fecha=hoy).exists():
                    Asistencia.objects.create(profesor=profe, materia=materia_activa)
                    return JsonResponse({
                        "status": "ok", 
                        "mensaje": f"Hola {profe.nombre}. Clase de {materia_activa.nombre} INICIADA."
                    })
                else:
                    return JsonResponse({"status": "ok", "mensaje": "Profesor ya presente."})

            except Materia.DoesNotExist:
                return JsonResponse({
                    "status": "error", 
                    "mensaje": "⚠️ Profe, seleccione una materia en la Web primero."
                }, status=403)

        except Profesor.DoesNotExist:
            pass # No es profesor, seguimos...

        # -----------------------------------------------
        # PASO 2: ¿ES UN ESTUDIANTE?
        # -----------------------------------------------
        try:
            alumno = Estudiante.objects.get(rfid_uid=uid)
            
            # Buscamos CUALQUIER materia que esté ocurriendo ahora
            materia_en_curso = Materia.objects.filter(en_curso=True).first()
            
            if not materia_en_curso:
                return JsonResponse({"status": "error", "mensaje": "⛔ No hay clases activas."}, status=403)
            
            # VERIFICACIÓN: ¿El profesor de ESTA materia ya pasó su tarjeta?
            profe_presente = Asistencia.objects.filter(
                materia=materia_en_curso,
                profesor=materia_en_curso.profesor, # El dueño de la materia
                fecha=hoy
            ).exists()

            if not profe_presente:
                return JsonResponse({
                    "status": "error", 
                    "mensaje": f"⛔ Espere al Prof. {materia_en_curso.profesor.nombre}"
                }, status=403)

            # REGISTRAR ALUMNO
            if not Asistencia.objects.filter(estudiante=alumno, materia=materia_en_curso, fecha=hoy).exists():
                Asistencia.objects.create(estudiante=alumno, materia=materia_en_curso)
                return JsonResponse({
                    "status": "ok", 
                    "mensaje": f"Bienvenido a {materia_en_curso.nombre}"
                })
            else:
                return JsonResponse({"status": "error", "mensaje": "Ya registrado hoy."})

        except Estudiante.DoesNotExist:
            # -----------------------------------------------
            # PASO 3: TARJETA DESCONOCIDA
            # -----------------------------------------------
            ultimo_uid_desconocido = uid
            return JsonResponse({"status": "unknown", "mensaje": "Tarjeta desconocida"}, status=404)

    return JsonResponse({"status": "error"}, status=400)

@csrf_exempt
def confirmar_salida(request, asistencia_id):
    if request.method == 'POST':
        # Buscamos la asistencia por su ID único
        asistencia = get_object_or_404(Asistencia, id=asistencia_id)
        
        # Invertimos el valor (Si es False pasa a True, y viceversa)
        asistencia.chequeo_salida = not asistencia.chequeo_salida
        asistencia.save()
        
        return JsonResponse({
            'status': 'ok', 
            'chequeado': asistencia.chequeo_salida
        })
    
    return JsonResponse({'status': 'error'}, status=400)


# =======================================================
# 3. SECCIÓN DE REGISTRO Y EXTRAS
# =======================================================

def obtener_uid_temporal(request):
    global ultimo_uid_desconocido
    return JsonResponse({'uid': ultimo_uid_desconocido})

def guardar_nuevo_estudiante(request):
    global ultimo_uid_desconocido
    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        uid = request.POST.get('uid')
        if nombre and uid:
            Estudiante.objects.create(nombre=nombre, rfid_uid=uid)
            ultimo_uid_desconocido = None
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'})

@login_required
def pagina_registro(request):
    return render(request, 'asistencia/registro.html')

@login_required
def carga_masiva(request):
    mensaje = ""
    # Nota: Esta lógica requiere adaptaciones si quieres asignar materia automáticamente.
    # Por ahora, la dejaré sencilla.
    if request.method == 'POST' and request.FILES.get('archivo_sd'):
        archivo = request.FILES['archivo_sd']
        datos = archivo.read().decode('utf-8').splitlines()
        contador = 0
        hoy = timezone.now().date()
        
        # Intentamos obtener la materia activa del profesor logueado
        try:
            materia_activa = Materia.objects.get(profesor=request.user.profesor, en_curso=True)
        except:
            mensaje = "Error: Debes tener una clase activa para cargar asistencias."
            return render(request, 'asistencia/carga_manual.html', {'mensaje': mensaje})

        for linea in datos:
            if ',' in linea:
                uid_leido, hora_leida = linea.split(',')
                uid_leido = uid_leido.strip()
                try:
                    # Buscamos si es estudiante
                    estudiante = Estudiante.objects.get(rfid_uid=uid_leido)
                    if not Asistencia.objects.filter(estudiante=estudiante, fecha=hoy, materia=materia_activa).exists():
                        Asistencia.objects.create(estudiante=estudiante, materia=materia_activa)
                        contador += 1
                except Estudiante.DoesNotExist:
                    continue
        
        mensaje = f"Proceso completado. Se recuperaron {contador} alumnos en {materia_activa.nombre}."

    return render(request, 'asistencia/carga_manual.html', {'mensaje': mensaje})