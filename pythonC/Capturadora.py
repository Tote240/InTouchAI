import cv2
import mediapipe as mp
import pandas as pd
import time
import sys
import traceback
from pymongo import MongoClient
import gridfs
import numpy as np

class CapturadorGestos:
    def __init__(self):
        # Configuración de MediaPipe más flexible
        mp.solutions.hands.Hands.close = False  # Prevenir cierre prematuro
        
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.1,  # Umbral de confianza muy bajo
            min_tracking_confidence=0.1    # Umbral de seguimiento muy bajo
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # Conexión a MongoDB
        try:
            self.cliente = MongoClient('mongodb+srv://nombre+contraseña.@ia.ebtrt.mongodb.net/')
            self.bd = self.cliente['Lenguaje-señas']
            self.coleccion_gestos = self.bd['gestures']  # Usar la colección "gestures"
            self.fs = gridfs.GridFS(self.bd)
        except Exception as e:
            print(f"Error al conectar con MongoDB: {e}")
            sys.exit(1)
        
        # Inicializar cámara
        self.inicializar_camara()
        
    def inicializar_camara(self):
        """
        Inicializar la captura de video con múltiples backends
        """
        # Lista de backends a probar
        backends = [
            cv2.CAP_DSHOW,   # DirectShow (Windows)
            cv2.CAP_MSMF,    # Microsoft Media Foundation
            cv2.CAP_V4L2,    # Video4Linux2 (Linux)
            cv2.CAP_ANY      # Cualquier backend disponible
        ]
        
        # Intentar abrir la cámara con diferentes backends
        for backend in backends:
            try:
                self.cap = cv2.VideoCapture(0, backend)
                
                # Configuraciones adicionales de la cámara
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
                self.cap.set(cv2.CAP_PROP_FPS, 30)
                
                # Verificar si la cámara está abierta
                if not self.cap.isOpened():
                    print(f"No se pudo abrir la cámara con backend {backend}")
                    continue
                
                print(f"Cámara inicializada correctamente con backend {backend}")
                return
                
            except Exception as e:
                print(f"Error al intentar abrir cámara con backend {backend}: {e}")
        
        # Si ningún backend funciona
        print("Error crítico: No se pudo acceder a la cámara")
        sys.exit(1)
        
    def validar_landmarks(self, landmarks):
        """
        Validación más flexible de landmarks
        """
        try:
            # Convertir a numpy array
            landmarks_np = np.array(landmarks)
            
            # Reducir requisitos de validación
            # Verificar que hay suficientes puntos válidos
            coords_validos = landmarks_np[(landmarks_np >= 0) & (landmarks_np <= 1)]
            
            # Si al menos el 50% de los landmarks son válidos, aceptar
            return len(coords_validos) >= len(landmarks_np) * 0.5
        
        except Exception as e:
            print(f"Error en validación de landmarks: {e}")
            return False
    
    def capturar_gestos(self, etiqueta_gesto, num_muestras=200):
        """
        Capturar datos de gestos con validación muy permisiva
        """
        datos = []
        muestras_validas = 0
        frames_sin_mano = 0
        
        print(f"🤚 Capturando gesto: {etiqueta_gesto}")
        print("Prepara tu gesto. La grabación comenzará en 3 segundos.")
        time.sleep(3)
        
        tiempo_inicio = time.time()
        tiempo_limite = 240  # 4 minutos máximo
        
        # Configuraciones visuales
        cv2.namedWindow("Captura de Gestos", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Captura de Gestos", 1280, 720)
        
        while muestras_validas < num_muestras and time.time() - tiempo_inicio < tiempo_limite:
            try:
                # Capturar fotograma
                exito, imagen = self.cap.read()
                if not exito:
                    print("No se pudo capturar fotograma")
                    break
                
                # Voltear imagen
                imagen = cv2.flip(imagen, 1)
                imagen_rgb = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
                
                # Procesar imagen para detección de manos
                resultados = self.hands.process(imagen_rgb)
                
                # Dibujar área de captura
                altura, anchura = imagen.shape[:2]
                margen_x = int(anchura * 0.1)
                margen_y = int(altura * 0.1)
                cv2.rectangle(imagen, 
                             (margen_x, margen_y), 
                             (anchura - margen_x, altura - margen_y), 
                             (0, 255, 0), 3)
                
                # Añadir información de progreso
                cv2.putText(imagen, 
                           f"Gesto: {etiqueta_gesto} | Muestras: {muestras_validas}/{num_muestras}", 
                           (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 
                           1, (0, 255, 0), 2)
                
                # Verificar detección de manos
                if resultados.multi_hand_landmarks:
                    frames_sin_mano = 0
                    for landmarks_mano in resultados.multi_hand_landmarks:
                        # Dibujar landmarks
                        self.mp_drawing.draw_landmarks(
                            imagen, 
                            landmarks_mano, 
                            self.mp_hands.HAND_CONNECTIONS
                        )
                        
                        # Extraer landmarks
                        landmarks = [(lm.x, lm.y, lm.z) for lm in landmarks_mano.landmark]
                        landmarks_aplanados = [coord for punto in landmarks for coord in punto]
                        
                        # Validación más flexible
                        if self.validar_landmarks(landmarks_aplanados):
                            datos.append([etiqueta_gesto] + landmarks_aplanados)
                            muestras_validas += 1
                            
                            # Guardar imagen ocasionalmente
                            if muestras_validas % 20 == 0:
                                try:
                                    id_imagen = self.fs.put(
                                        cv2.imencode('.png', imagen)[1].tobytes(), 
                                        filename=f"{etiqueta_gesto}_{muestras_validas}.png"
                                    )
                                    print(f"💾 Imagen guardada con ID: {id_imagen}")
                                except Exception as e:
                                    print(f"Error al guardar imagen: {e}")
                            
                            # Salir si se alcanzan las muestras
                            if muestras_validas >= num_muestras:
                                break
                else:
                    frames_sin_mano += 1
                    # Mostrar mensaje si no se detecta mano
                    cv2.putText(imagen, 
                               "No se detecta mano. Asegúrate de estar dentro del rectángulo verde.", 
                               (50, altura - 50), 
                               cv2.FONT_HERSHEY_SIMPLEX, 
                               1, (0, 0, 255), 2)
                    
                    # Resetear si pasan muchos frames sin detectar mano
                    if frames_sin_mano > 30:
                        print("🚨 No se detecta mano. Reposicionándote...")
                        frames_sin_mano = 0
                
                # Mostrar imagen
                cv2.imshow("Captura de Gestos", imagen)
                
                # Salir con tecla 'q'
                tecla = cv2.waitKey(1) & 0xFF
                if tecla == ord('q'):
                    break
                
            except Exception as e:
                print("Error durante la captura:")
                print(traceback.format_exc())
                break
        
        # Guardar datos en MongoDB
        if datos:
            datos_gesto = {
                'label': etiqueta_gesto,  # Usar 'label' en lugar de 'etiqueta'
                'data': datos
            }
            try:
                resultado = self.coleccion_gestos.insert_one(datos_gesto)
                print(f"✅ Datos de gesto guardados con ID: {resultado.inserted_id}")
            except Exception as e:
                print(f"Error al guardar datos en MongoDB: {e}")
        else:
            print("❌ No se recopilaron datos de gesto.")
        
        # Limpiar
        cv2.destroyAllWindows()
        
        return len(datos)
    
    def __del__(self):
        """
        Liberar recursos
        """
        if hasattr(self, 'cap'):
            self.cap.release()
        if hasattr(self, 'cliente'):
            self.cliente.close()

def main():
    capturador = CapturadorGestos()
    
    while True:
        try:
            etiqueta_gesto = input("Introduce el nombre del gesto (o 'salir' para terminar): ")
            
            if etiqueta_gesto.lower() == 'salir':
                break
            
            muestras_recopiladas = capturador.capturar_gestos(etiqueta_gesto)
            print(f"🎉 Recopiladas {muestras_recopiladas} muestras para el gesto: {etiqueta_gesto}")
        
        except Exception as e:
            print("Ocurrió un error:")
            print(traceback.format_exc())

if __name__ == "__main__":
    main()