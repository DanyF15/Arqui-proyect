from django.contrib import admin
from .models import Profesor, Materia, Estudiante, Asistencia

@admin.register(Profesor)
class ProfesorAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rfid_uid', 'usuario')

@admin.register(Materia)
class MateriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'codigo', 'profesor', 'en_curso')
    list_editable = ('en_curso',) # Te permite activar/desactivar clases desde el admin rápido

@admin.register(Estudiante)
class EstudianteAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'rfid_uid')

@admin.register(Asistencia)
class AsistenciaAdmin(admin.ModelAdmin):
    list_display = ('identificar_persona', 'materia', 'fecha', 'hora_llegada')
    list_filter = ('fecha', 'materia')

    # Función auxiliar para mostrar si es Profe o Alumno en la lista
    def identificar_persona(self, obj):
        if obj.profesor:
            return f"🎓 PROFE: {obj.profesor.nombre}"
        elif obj.estudiante:
            return f"👤 {obj.estudiante.nombre}"
        return "Desconocido"
    
    identificar_persona.short_description = 'Asistente'