from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
import cv2
import numpy as np
import tensorflow as tf
import traceback
import os
import mediapipe as mp

app = Flask(__name__)
CORS(app)

# Crear carpeta debug_images con ruta absoluta
current_dir = os.path.dirname(os.path.abspath(__file__))
debug_dir = os.path.join(current_dir, 'debug_images')
os.makedirs(debug_dir, exist_ok=True)
print(f"✅ Carpeta de debug creada en: {debug_dir}")

# Conexión a MongoDB
try:
    client = MongoClient('mongodb+srv://josuecalabran:23803400.@ia.ebtrt.mongodb.net/', 
                         serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['Lenguaje-señas']
    gestures_collection = db['gestures']
    print("✅ MongoDB conectado exitosamente")
except Exception as e:
    print(f"❌ Error de MongoDB: {e}")
    client = None
    db = None
    gestures_collection = None

# Cargar modelo TFLite
try:
    interpreter = tf.lite.Interpreter(model_path="models/modelo_gestos.tflite")
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    print("✅ Modelo TFLite cargado exitosamente")
    print(f"📊 Detalles de entrada: {input_details}")
    print(f"📊 Detalles de salida: {output_details}")
except Exception as e:
    print(f"❌ Error cargando modelo: {e}")
    interpreter = None

# Configuración MediaPipe Pose
mp_pose = mp.solutions.pose
pose = mp_pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# Buffer para acumular secuencias de landmarks
frame_buffer = []

@app.route('/')
def home():
    return "Sign Language Translator API Running!"

@app.route('/gestures', methods=['GET'])
def get_gestures():
    try:
        print("⌛ Obteniendo lista de gestos...")
        gestures = []
        
        if gestures_collection is not None:
            gestures = list(gestures_collection.distinct('label'))
        
        if not gestures:
            print("❌ No se encontraron gestos")
            return jsonify({'error': 'No se encontraron gestos'}), 404
            
        print(f"✅ Gestos encontrados: {gestures}")
        return jsonify({'gestures': gestures}), 200
        
    except Exception as e:
        print(f"❌ Error en /gestures: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/predict', methods=['POST'])
def predict():
    try:
        data = request.get_json()
        if not data or 'landmarks_sequence' not in data:
            print("❌ No se proporcionaron landmarks")
            return jsonify({'error': 'No se proporcionaron landmarks'}), 400

        try:
            # Obtener la secuencia de landmarks
            landmarks_sequence = data['landmarks_sequence']
            
            # Verificar que tenemos 5 frames
            if len(landmarks_sequence) != 5:
                print(f"❌ Número incorrecto de frames: {len(landmarks_sequence)}")
                return jsonify({
                    'gesture': 'INVALID_SEQUENCE',
                    'confidence': 0.0,
                }), 400

            # Verificar que cada frame tiene los landmarks correctos
            for frame in landmarks_sequence:
                if len(frame) != 63:
                    print(f"❌ Número incorrecto de landmarks: {len(frame)}")
                    return jsonify({
                        'gesture': 'INVALID_LANDMARKS',
                        'confidence': 0.0,
                    }), 400

            # Convertir a formato numpy para el modelo
            input_data = np.array([landmarks_sequence], dtype=np.float32)
            
            print("✅ Forma de entrada:", input_data.shape)

            # Hacer predicción
            interpreter.set_tensor(input_details[0]['index'], input_data)
            interpreter.invoke()
            output_data = interpreter.get_tensor(output_details[0]['index'])
            
            idx = np.argmax(output_data[0])
            confidence = float(output_data[0][idx])

            print("✅ Predicción realizada")
            print(f"📊 Índice predicho: {idx}")
            print(f"📊 Confianza: {confidence}")

            # Obtener gestos disponibles
            gestures = []
            try:
                if gestures_collection is not None:
                    gestures = list(gestures_collection.distinct('label'))
                    print(f"✅ Gestos disponibles: {gestures}")
            except Exception as e:
                print(f"❌ Error obteniendo gestos: {e}")

            if gestures and idx < len(gestures):
                gesture = gestures[idx]
                print(f"✅ Gesto detectado: {gesture} con confianza: {confidence}")
                return jsonify({
                    'gesture': gesture,
                    'confidence': confidence,
                }), 200

            return jsonify({
                'gesture': 'UNKNOWN',
                'confidence': confidence,
            }), 200

        except Exception as e:
            print(f"❌ Error procesando landmarks: {str(e)}")
            print(f"Stack trace: {traceback.format_exc()}")
            return jsonify({
                'error': f'Error procesando landmarks: {str(e)}'
            }), 500

    except Exception as e:
        print(f"❌ Error en /predict: {str(e)}")
        print(f"Stack trace: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 Iniciando servidor...")
    app.run(host='0.0.0.0', port=5000, debug=True)