import cv2
import mediapipe as mp
import numpy as np
import joblib
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import sys
from PIL import Image, ImageTk

class TraductorLenguajeSeñas:
    def __init__(self, master):
        self.master = master
        master.title("InTouch AI - Traductor de Lenguaje de Señas")
        master.geometry("1024x768")
        master.configure(bg='#f0f0f0')

        # Cargar modelo y etiquetas
        try:
            self.modelo = joblib.load('modelo_lenguaje_señas.joblib')
            self.codificador_etiquetas = joblib.load('codificador_etiquetas.joblib')
            self.etiquetas_gestos = self.codificador_etiquetas.classes_
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el modelo: {e}")
            sys.exit(1)

        # Inicializar MediaPipe para detección de manos
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.2,
            min_tracking_confidence=0.2
        )
        self.mp_drawing = mp.solutions.drawing_utils

        # Crear pantalla de inicio
        self.crear_pantalla_inicio()

    def crear_pantalla_inicio(self):
        """Crear la pantalla de inicio con el título y botón de comenzar"""
        # Limpiar cualquier widget existente
        for widget in self.master.winfo_children():
            widget.destroy()

        # Marco principal
        marco_inicio = tk.Frame(self.master, bg='#f0f0f0')
        marco_inicio.pack(expand=True, fill='both')

        # Título
        titulo = tk.Label(
            marco_inicio, 
            text="InTouch AI", 
            font=('Arial', 48, 'bold'), 
            fg='#333333', 
            bg='#f0f0f0'
        )
        titulo.pack(pady=(100, 20))

        # Subtítulo
        subtitulo = tk.Label(
            marco_inicio, 
            text="Traductor de Lenguaje de Señas", 
            font=('Arial', 24), 
            fg='#666666', 
            bg='#f0f0f0'
        )
        subtitulo.pack(pady=(0, 50))

        # Botón de comenzar
        boton_comenzar = tk.Button(
            marco_inicio, 
            text="Comenzar", 
            font=('Arial', 20, 'bold'),
            command=self.iniciar_traduccion,
            bg='#4CAF50', 
            fg='white',
            padx=30,
            pady=15,
            relief=tk.FLAT
        )
        boton_comenzar.pack(pady=20)

    def iniciar_traduccion(self):
        """Iniciar la traducción de lenguaje de señas"""
        # Limpiar pantalla de inicio
        for widget in self.master.winfo_children():
            widget.destroy()

        # Crear marco principal
        marco_principal = tk.Frame(self.master, bg='#f0f0f0')
        marco_principal.pack(expand=True, fill='both', padx=20, pady=20)

        # Área de video
        self.etiqueta_video = tk.Label(marco_principal, bg='black')
        self.etiqueta_video.pack(expand=True, fill='both', side=tk.TOP, padx=10, pady=10)

        # Área de resultado
        marco_resultado = tk.Frame(marco_principal, bg='#f0f0f0')
        marco_resultado.pack(fill='x', padx=10, pady=10)

        self.etiqueta_resultado = tk.Label(
            marco_resultado, 
            text="Esperando gestos...", 
            font=('Arial', 24, 'bold'), 
            bg='#f0f0f0', 
            fg='#333333',
            padx=20,
            pady=10
        )
        self.etiqueta_resultado.pack(side=tk.LEFT, expand=True)

        # Botón de salir
        boton_salir = tk.Button(
            marco_resultado, 
            text="Volver", 
            font=('Arial', 16, 'bold'), 
            command=self.volver_inicio,
            bg='#f44336', 
            fg='white',
            padx=20,
            pady=10,
            relief=tk.FLAT
        )
        boton_salir.pack(side=tk.RIGHT, padx=20)

        # Iniciar captura de video en un hilo separado
        self.captura_activa = True
        self.hilo_captura = threading.Thread(target=self.capturar_video)
        self.hilo_captura.start()

    def capturar_video(self):
        """Capturar y procesar video en tiempo real"""
        # Abrir captura de video
        captura = cv2.VideoCapture(1)
        captura.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        captura.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        
        # Variables para control de predicciones
        historial_predicciones = []
        TAMANO_HISTORIAL = 5

        while self.captura_activa:
            # Leer fotograma
            exito, fotograma = captura.read()
            if not exito:
                break

            # Voltear fotograma horizontalmente
            fotograma = cv2.flip(fotograma, 1)
            fotograma_rgb = cv2.cvtColor(fotograma, cv2.COLOR_BGR2RGB)

            # Detectar manos
            resultados = self.hands.process(fotograma_rgb)

            # Dibujar área de detección
            altura, anchura = fotograma.shape[:2]
            margen_x = int(anchura * 0.1)
            margen_y = int(altura * 0.1)
            cv2.rectangle(
                fotograma, 
                (margen_x, margen_y), 
                (anchura - margen_x, altura - margen_y), 
                (0, 255, 0), 
                2
            )

            prediccion_actual = None

            if resultados.multi_hand_landmarks:
                for landmarks_mano in resultados.multi_hand_landmarks:
                    # Dibujar landmarks
                    self.mp_drawing.draw_landmarks(
                        fotograma, 
                        landmarks_mano, 
                        self.mp_hands.HAND_CONNECTIONS
                    )

                    # Extraer y procesar landmarks
                    landmarks = [(lm.x, lm.y, lm.z) for lm in landmarks_mano.landmark]
                    landmarks_aplanados = [coord for punto in landmarks for coord in punto]
                    
                    # Normalizar landmarks
                    landmarks_normalizados = np.array([landmarks_aplanados])

                    # Obtener predicción y probabilidades
                    prediccion = self.modelo.predict(landmarks_normalizados)[0]
                    probabilidades = self.modelo.predict_proba(landmarks_normalizados)[0]
                    max_probabilidad = max(probabilidades)

                    # Actualizar historial de predicciones
                    historial_predicciones.append((prediccion, max_probabilidad))
                    if len(historial_predicciones) > TAMANO_HISTORIAL:
                        historial_predicciones.pop(0)

                    # Verificar consistencia en el historial
                    if len(historial_predicciones) >= 3:
                        predicciones_recientes = [p[0] for p in historial_predicciones]
                        probabilidades_recientes = [p[1] for p in historial_predicciones]
                        prediccion_mas_comun = max(set(predicciones_recientes), key=predicciones_recientes.count)
                        probabilidad_promedio = sum(probabilidades_recientes) / len(probabilidades_recientes)

                        if (predicciones_recientes.count(prediccion_mas_comun) >= 2 and 
                            probabilidad_promedio > 0.6):
                            prediccion_actual = self.etiquetas_gestos[prediccion_mas_comun]

                            # Mostrar predicción
                            cv2.putText(
                                fotograma, 
                                f"Gesto Detectado: {prediccion_actual}", 
                                (10, 30), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                1, 
                                (0, 255, 0), 
                                2
                            )
                            cv2.putText(
                                fotograma, 
                                f"Confianza: {probabilidad_promedio:.2%}", 
                                (10, 70), 
                                cv2.FONT_HERSHEY_SIMPLEX, 
                                0.6, 
                                (255, 255, 0), 
                                2
                            )

            # Convertir fotograma para mostrar en Tkinter
            fotograma_tk = cv2.cvtColor(fotograma, cv2.COLOR_BGR2RGB)
            imagen_pil = Image.fromarray(fotograma_tk)
            imagen_tk = ImageTk.PhotoImage(imagen_pil)

            # Actualizar interfaz desde el hilo principal
            self.master.after(0, self.actualizar_interfaz, imagen_tk, prediccion_actual)

            # Salir con tecla 'q'
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        # Liberar recursos
        captura.release()

    def actualizar_interfaz(self, imagen, prediccion):
        """
        Actualizar la interfaz gráfica desde el hilo principal
        """
        # Actualizar imagen de video
        self.etiqueta_video.configure(image=imagen)
        self.etiqueta_video.image = imagen

        # Actualizar resultado
        if prediccion:
            self.etiqueta_resultado.configure(
                text=f"Gesto Detectado: {prediccion}", 
                fg='#4CAF50'
            )
        else:
            self.etiqueta_resultado.configure(
                text="Esperando gestos...", 
                fg='#333333'
            )

    def volver_inicio(self):
        """Volver a la pantalla de inicio"""
        # Detener captura de video
        self.captura_activa = False
        if hasattr(self, 'hilo_captura'):
            self.hilo_captura.join()

        # Volver a la pantalla de inicio
        self.crear_pantalla_inicio()

def main():
    # Crear ventana principal
    raiz = tk.Tk()
    
    # Establecer ícono de la aplicación (opcional)
    try:
        raiz.iconbitmap('icono.ico')  # Reemplaza con tu propio ícono
    except:
        pass

    # Crear aplicación
    app = TraductorLenguajeSeñas(raiz)
    
    # Iniciar bucle principal
    raiz.mainloop()

if __name__ == "__main__":
    main()