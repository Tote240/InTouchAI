import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, confusion_matrix
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from imblearn.over_sampling import SMOTE
import seaborn as sns
import matplotlib.pyplot as plt
from pymongo import MongoClient

# Conexión a MongoDB Atlas
client = MongoClient('mongodb+srv://nombre+contraseña.@ia.ebtrt.mongodb.net/')
db = client['Lenguaje-señas']
gestures_collection = db['gestures']

# Lista para almacenar los datos
gesture_data_frames = []

# Obtener la lista de gestos únicos en la colección
gestures = gestures_collection.distinct('label')

def procesar_datos(data):
    """Aplana las secuencias de datos en fotogramas individuales"""
    filas = []
    for secuencia in data:
        for fotograma in secuencia:
            filas.append(fotograma)
    return filas

for gesture in gestures:
    print(f"Cargando datos de {gesture}...")
    total_samples = gestures_collection.count_documents({'label': gesture})
    print(f"Número de muestras para {gesture}: {total_samples}")
    
    gesture_data = list(gestures_collection.find({'label': gesture}))
    for data in gesture_data:
        fotogramas = procesar_datos(data['data'])
        df = pd.DataFrame(fotogramas, columns=["gesture"] + [f"point_{i}_{coord}" for i in range(21) for coord in ("x", "y", "z")])
        gesture_data_frames.append(df)

if len(gesture_data_frames) > 0:
    # Concatenar todos los datos
    gesture_data = pd.concat(gesture_data_frames, ignore_index=True)
    print("Datos cargados desde MongoDB:")
    print(gesture_data.head())
    
    # Separar las características y las etiquetas
    X = gesture_data.drop("gesture", axis=1)
    y = gesture_data["gesture"]
    
    print(f"Forma de X: {X.shape}")
    print(f"Forma de y: {y.shape}")

    # Normalizar los datos
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    # Aplicar SMOTE para balancear las clases
    smote = SMOTE(random_state=42)
    X_balanced, y_balanced = smote.fit_resample(X, y)
    
    print(f"Forma de X después de SMOTE: {X_balanced.shape}")
    print(f"Forma de y después de SMOTE: {y_balanced.shape}")
    print("\nDistribución de clases después del balanceo:")
    print(pd.Series(y_balanced).value_counts())
    
    # Dividir los datos
    X_train, X_test, y_train, y_test = train_test_split(
        X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
    )

    print(f"Forma de X_train: {X_train.shape}")
    print(f"Forma de y_train: {y_train.shape}")

    def reshape_to_sequences(data, labels, sequence_length=5):
        # Convertir a numpy arrays
        data = np.array(data)
        labels = np.array(labels)
        
        sequences = []
        label_sequences = []
        
        # Procesar solo múltiplos completos de sequence_length
        n_sequences = len(data) // sequence_length
        
        for i in range(n_sequences):
            start_idx = i * sequence_length
            end_idx = start_idx + sequence_length
            sequences.append(data[start_idx:end_idx])
            label_sequences.append(labels[end_idx - 1])
        
        return np.array(sequences), np.array(label_sequences)

    # Convertir a arrays numpy
    y_train = np.array(y_train)
    y_test = np.array(y_test)
    
    # Reshape los datos
    X_train, y_train = reshape_to_sequences(X_train, y_train)
    X_test, y_test = reshape_to_sequences(X_test, y_test)
    
    print(f"Forma de X_train después del reshape: {X_train.shape}")
    print(f"Forma de X_test después del reshape: {X_test.shape}")
    
    # Convertir etiquetas de cadena a números
    from sklearn.preprocessing import LabelEncoder
    label_encoder = LabelEncoder()
    y_train = label_encoder.fit_transform(y_train)
    y_test = label_encoder.transform(y_test)
    
    # Crear el modelo LSTM
    model = Sequential([
        LSTM(128, activation='relu', input_shape=(5, 63), return_sequences=True),
        Dropout(0.2),
        LSTM(64, activation='relu'),
        Dropout(0.2),
        Dense(len(gestures), activation='softmax')
    ])

    # Compilar
    model.compile(optimizer='adam', loss='sparse_categorical_crossentropy', metrics=['accuracy'])
    
    # Entrenar
    history = model.fit(X_train, y_train, epochs=50, batch_size=32, 
                       validation_split=0.2, verbose=1)
    
    # Evaluar
    y_pred = model.predict(X_test)
    y_pred = np.argmax(y_pred, axis=1)
    
    # Convertir predicciones numéricas a etiquetas originales
    y_test_labels = label_encoder.inverse_transform(y_test)
    y_pred_labels = label_encoder.inverse_transform(y_pred)

    # Métricas
    print("\nReporte de clasificación:")
    print(classification_report(y_test_labels, y_pred_labels))
    
    # Matriz de confusión
    cm = confusion_matrix(y_test_labels, y_pred_labels)
    plt.figure(figsize=(10,7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=gestures,
                yticklabels=gestures)
    plt.title('Matriz de Confusión')
    plt.ylabel('Verdadero')
    plt.xlabel('Predicho')
    plt.savefig('confusion_matrix.png')
    plt.close()
    
    # Gráfica de pérdida y precisión
    plt.figure(figsize=(12,4))
    
    plt.subplot(1,2,1)
    plt.plot(history.history['loss'], label='Entrenamiento')
    plt.plot(history.history['val_loss'], label='Validación')
    plt.title('Pérdida del modelo')
    plt.xlabel('Época')
    plt.ylabel('Pérdida')
    plt.legend()
    
    plt.subplot(1,2,2)
    plt.plot(history.history['accuracy'], label='Entrenamiento')
    plt.plot(history.history['val_accuracy'], label='Validación')
    plt.title('Precisión del modelo')
    plt.xlabel('Época')
    plt.ylabel('Precisión')
    plt.legend()
    
    plt.tight_layout()
    plt.savefig('training_history.png')
    plt.close()
    
    # Guardar el modelo
    model.save('modelo_lstm.h5')
    print("\nModelo LSTM guardado correctamente.")

else:
    print("No se encontraron datos para entrenar el modelo.")
