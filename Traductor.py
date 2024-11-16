import cv2
import mediapipe as mp
import numpy as np
import joblib
from datetime import datetime, timedelta

# Cargar el modelo entrenado y el scaler
model = joblib.load('entrenamiento_modelo.joblib')
scaler = joblib.load('scaler.joblib')

# Inicializar MediaPipe para la detección de manos
mp_hands = mp.solutions.hands
hands = mp_hands.Hands(
    static_image_mode=False,
    max_num_hands=2,  # Mantenemos la detección de dos manos
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)
mp_drawing = mp.solutions.drawing_utils
mp_drawing_styles = mp.solutions.drawing_styles

# Configuración de la cámara
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
cap.set(cv2.CAP_PROP_FPS, 30)

if not cap.isOpened():
    print("Error: No se pudo acceder a la cámara.")
    exit()

print("Cámara abierta correctamente.")

# Variables para el control de predicciones
prediction_history = []
HISTORY_SIZE = 5

# Función para dibujar el área de detección central
def draw_detection_area(image):
    height, width = image.shape[:2]
    margin_x = int(width * 0.1)  # 10% de margen en x
    margin_y = int(height * 0.1)  # 10% de margen en y
    
    # Dibujar rectángulo grande central
    cv2.rectangle(image, 
                 (margin_x, margin_y), 
                 (width - margin_x, height - margin_y), 
                 (0, 255, 0), 2)
    return image

while cap.isOpened():
    success, image = cap.read()
    if not success:
        print("Error: No se pudo capturar la imagen.")
        break

    # Volteamos la imagen horizontalmente para una vista tipo espejo
    image = cv2.flip(image, 1)
    
    # Procesar la imagen para detección de manos
    image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = hands.process(image_rgb)

    # Dibujar el área de detección
    image = draw_detection_area(image)

    # Estado actual de la detección
    current_prediction = None
    
    if results.multi_hand_landmarks:
        for hand_landmarks in results.multi_hand_landmarks:
            # Dibujar los landmarks con un estilo más visible
            mp_drawing.draw_landmarks(
                image, 
                hand_landmarks, 
                mp_hands.HAND_CONNECTIONS,
                mp_drawing_styles.get_default_hand_landmarks_style(),
                mp_drawing_styles.get_default_hand_connections_style()
            )

            # Extraer y procesar landmarks
            landmarks = [(lm.x, lm.y, lm.z) for lm in hand_landmarks.landmark]
            flattened_landmarks = [coord for point in landmarks for coord in point]
            normalized_landmarks = scaler.transform([flattened_landmarks])

            # Obtener predicción y probabilidades
            prediction = model.predict(normalized_landmarks)[0]
            probabilities = model.predict_proba(normalized_landmarks)[0]
            max_probability = max(probabilities)

            # Actualizar historial de predicciones
            prediction_history.append((prediction, max_probability))
            if len(prediction_history) > HISTORY_SIZE:
                prediction_history.pop(0)

            # Verificar consistencia en el historial
            if len(prediction_history) >= 3:
                recent_predictions = [p[0] for p in prediction_history]
                recent_probabilities = [p[1] for p in prediction_history]
                most_common = max(set(recent_predictions), key=recent_predictions.count)
                avg_probability = sum(recent_probabilities) / len(recent_probabilities)

                if recent_predictions.count(most_common) >= 2 and avg_probability > 0.6:
                    current_prediction = most_common
                    # Mostrar predicción con alta confianza
                    cv2.putText(image, f"Gesto: {current_prediction}", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    cv2.putText(image, f"Confianza: {avg_probability:.2%}", (10, 70),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
                else:
                    # Mostrar que está procesando
                    cv2.putText(image, "Procesando gesto...", (10, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 165, 0), 2)
    else:
        # Mostrar mensaje cuando no se detectan manos
        cv2.putText(image, "No se detectan manos", (10, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)

    # Mostrar instrucción simple en la parte inferior
    cv2.putText(image, "Realiza los gestos dentro del rectángulo verde", 
                (10, image.shape[0] - 20),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

    # Mostrar la imagen
    cv2.imshow("Traductor de Lenguaje de Señas", image)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
