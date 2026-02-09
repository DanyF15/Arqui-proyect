from django.db import models
from django.utils import timezone
from django.contrib.auth.models import User

# 1. MODELO PROFESOR (El puente entre Login y RFID)
class Profesor(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE) # Link al login (User/Pass)
    rfid_uid = models.CharField(max_length=20, unique=True) # Su tarjeta física
    nombre = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Prof. {self.nombre}"

# 2. MODELO MATERIA (Ahora vinculada al modelo Profesor)
class Materia(models.Model):
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=20, unique=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE) # <--- CAMBIO AQUÍ
    en_curso = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.nombre} ({self.profesor.nombre})"

# 3. MODELO ESTUDIANTE (Ya no necesita el campo 'es_profesor')
class Estudiante(models.Model):
    nombre = models.CharField(max_length=100)
    rfid_uid = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.nombre

# 4. MODELO ASISTENCIA
class Asistencia(models.Model):
    estudiante = models.ForeignKey(Estudiante, on_delete=models.CASCADE, null=True, blank=True)
    profesor = models.ForeignKey(Profesor, on_delete=models.CASCADE, null=True, blank=True)
    materia = models.ForeignKey(Materia, on_delete=models.CASCADE)
    fecha = models.DateField(default=timezone.now)
    hora_llegada = models.TimeField(auto_now_add=True)
    
    # NUEVO CAMPO:
    chequeo_salida = models.BooleanField(default=False) 

    def __str__(self):
        quien = self.profesor.nombre if self.profesor else self.estudiante.nombre
        return f"{quien} - {self.materia.nombre}"