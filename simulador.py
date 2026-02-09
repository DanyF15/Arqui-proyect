import requests
import time

# URL de tu servidor Django (IP de tu WiFi)
URL_API = "http://10.44.179.46:8000/api/rfid/"

def simular_lectura():
    print("--- SIMULADOR ESP32 INICIADO ---")
    print("Escribe un UID y presiona Enter para 'escanear'")
    print("Escribe 'salir' para terminar")
    
    while True:
        uid = input("\nSimular tarjeta (UID): ").strip()
        
        if uid.lower() == 'salir':
            break
            
        if not uid:
            continue

        print(f"📡 Enviando UID {uid} al servidor...")
        
        try:
            # Enviamos el dato como FORM DATA, igual que la ESP32
            payload = {'uid': uid}
            respuesta = requests.post(URL_API, data=payload)
            
            print(f"✅ Respuesta Servidor [{respuesta.status_code}]: {respuesta.text}")
            
        except requests.exceptions.ConnectionError:
            print("❌ Error: No se puede conectar a Django. ¿Está corriendo el servidor?")

if __name__ == "__main__":
    simular_lectura()