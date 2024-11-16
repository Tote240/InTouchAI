import cv2
import mediapipe as mp
import pandas as pd
import os
import time

# Inicializamos MediaPipe para la detección de manos
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()
mp_drawing = mp.solutions.drawing_utils

# Configuración de la cámara
cap = cv2.VideoCapture(0)

# Solicita el nombre o etiqueta del gesto al usuario
gesture_label = input("Introduce el nombre o etiqueta del gesto: ")

# Lista para almacenar los datos de posiciones de las manos
data = []

# Crear una carpeta para almacenar las imágenes del gesto
output_dir = f"gestures/{gesture_label}"
os.makedirs(output_dir, exist_ok=True)

# Crear carpeta gestos_csv si no existe
csv_directory = 'gestos_csv'
os.makedirs(csv_directory, exist_ok=True)

# Contador de imágenes
image_count = 0

print("Grabación iniciará en 3 segundos. Prepara tu gesto.")
time.sleep(3)

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
            
            # Añadir la etiqueta y las posiciones al dataset
            data.append([gesture_label] + flattened_landmarks)
            
            # Guardar una imagen cada 5 fotogramas
            if image_count % 5 == 0:
                cv2.imwrite(f"{output_dir}/{gesture_label}_{image_count}.png", image)
                
    # Mostrar la imagen en la pantalla
    cv2.imshow("Hand Gesture Capture", image)
    
    image_count += 1
    
    # Detener con la tecla 'q'
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Guardamos los datos en un archivo CSV dentro de gestos_csv
df = pd.DataFrame(data, columns=["gesture"] + [f"point_{i}_{coord}" for i in range(21) for coord in ("x", "y", "z")])
df.to_csv(f"{csv_directory}/{gesture_label}_gesture_data.csv", index=False)

# Liberar recursos
cap.release()
cv2.destroyAllWindows()
