import cv2
import mediapipe as mp
import pandas as pd
import os
import time
from pymongo import MongoClient
import gridfs

# Inicializamos MediaPipe para la detección de manos
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Configuración de la cámarapip
cap = cv2.VideoCapture(1)  # Usa el índice 1 si tienes múltiples cámaras, si no, usa 0

# Solicita el nombre o etiqueta del gesto al usuario
gesture_label = input("Introduce el nombre o etiqueta del gesto: ")

# Lista para almacenar los datos de posiciones de las manos (secuencias de fotogramas)
data = []

# Conexión a MongoDB Atlas
client = MongoClient('mongodb+srv://josuecalabran:23803400.@ia.ebtrt.mongodb.net/')
db = client['Lenguaje-señas']
gestures_collection = db['gestures']
fs = gridfs.GridFS(db)

# Contador de imágenes
image_count = 0

# Tiempo de espera para preparar el gesto
print("Grabación iniciará en 3 segundos. Prepara tu gesto.")
time.sleep(3)

# Variable para capturar secuencia de fotogramas
frame_sequence = []

# Inicia la captura de imágenes y datos
while True:
    success, image = cap.read()
    if not success:
        break

    # Procesa la imagen para detección de manos
    image = cv2.flip(image, 1)  # Voltear la imagen horizontalmente para una vista en espejo
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    # Si se detectan manos
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            mp_drawing.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

            # Extrae las coordenadas de cada punto clave de la mano
            landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
            flattened_landmarks = [coord for point in landmarks for coord in point]  # Aplanamos la lista

            # Añadir la etiqueta y las posiciones al dataset (secuencias de fotogramas)
            frame_sequence.append([gesture_label] + flattened_landmarks)

            # Imprimir los puntos de referencia para cada fotograma (solo para depuración)
            print(f"Fotograma {image_count}: {flattened_landmarks}")  # Imprime las coordenadas del fotograma

            # Guardar la secuencia de fotogramas cada 5 fotogramas
            if len(frame_sequence) == 5:  # Guardar una secuencia de 5 fotogramas
                data.append(frame_sequence)
                print(f"Secuencia de 5 fotogramas guardada: {frame_sequence}")  # Imprime la secuencia de 5 fotogramas

                # Guardar una imagen cada 5 fotogramas
                image_id = fs.put(cv2.imencode('.png', image)[1].tobytes(), filename=f"{gesture_label}_{image_count}.png")
                print(f"Imagen guardada con ID: {image_id}")
                
                # Limpiar la secuencia para la siguiente captura
                frame_sequence = []

    # Mostrar la imagen en la pantalla
    cv2.imshow("Hand Gesture Capture", image)

    image_count += 1

    # Detener con la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Guardar los datos en MongoDB
gesture_data = {
    'label': gesture_label,
    'data': data
}
result = gestures_collection.insert_one(gesture_data)
print(f"Datos del gesto guardados con ID: {result.inserted_id}")

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
