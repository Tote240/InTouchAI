import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler
import joblib
from imblearn.over_sampling import SMOTE
import seaborn as sns
import matplotlib.pyplot as plt

# Ruta de los archivos CSV
csv_directory = 'gestos_csv'

# Lista para almacenar los datos
gesture_data = []

# Obtener la lista de archivos CSV en el directorio gestos_csv
gestures = [f.replace('_gesture_data.csv', '') for f in os.listdir(csv_directory) if f.endswith('_gesture_data.csv')]

# Cargar los archivos CSV específicos
for gesture in gestures:
    filepath = os.path.join(csv_directory, f"{gesture}_gesture_data.csv")
    if os.path.exists(filepath):
        print(f"Cargando datos de {gesture}...")
        data = pd.read_csv(filepath)
        print(f"Número de muestras para {gesture}: {len(data)}")
        gesture_data.append(data)
    else:
        print(f"Archivo {filepath} no encontrado.")

if len(gesture_data) > 0:
    # Concatenar todos los datos de los CSV
    gesture_data = pd.concat(gesture_data, ignore_index=True)

    # Mostrar distribución de clases
    print("\nDistribución de clases antes del balanceo:")
    print(gesture_data["gesture"].value_counts())

    # Separar las características y las etiquetas
    X = gesture_data.drop("gesture", axis=1)
    y = gesture_data["gesture"]

    # Normalizar los datos
    scaler = StandardScaler()
    X = scaler.fit_transform(X)

    # Aplicar SMOTE para balancear las clases
    smote = SMOTE(random_state=42)
    X_balanced, y_balanced = smote.fit_resample(X, y)

    print("\nDistribución de clases después del balanceo:")
    print(pd.Series(y_balanced).value_counts())

    # Dividir los datos en entrenamiento y prueba
    X_train, X_test, y_train, y_test = train_test_split(
        X_balanced, y_balanced, test_size=0.2, random_state=42, stratify=y_balanced
    )

    # Crear y entrenar el modelo con parámetros ajustados
    clf = RandomForestClassifier(
        n_estimators=200,  # Más árboles
        max_depth=15,      # Limitar profundidad para evitar sobreajuste
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight='balanced',  # Dar peso igual a todas las clases
        random_state=42
    )

    # Entrenar el modelo
    clf.fit(X_train, y_train)

    # Evaluar el modelo
    y_pred = clf.predict(X_test)
    
    # Mostrar métricas detalladas
    print("\nReporte de clasificación:")
    print(classification_report(y_test, y_pred))

    # Realizar validación cruzada
    cv_scores = cross_val_score(clf, X_balanced, y_balanced, cv=5)
    print("\nPuntuaciones de validación cruzada:", cv_scores)
    print("Media de validación cruzada: {:.4f} (+/- {:.4f})".format(
        cv_scores.mean(), cv_scores.std() * 2))

    # Crear matriz de confusión
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(10,7))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues',
                xticklabels=gestures,
                yticklabels=gestures)
    plt.title('Matriz de Confusión')
    plt.ylabel('Verdadero')
    plt.xlabel('Predicho')
    plt.savefig('confusion_matrix.png')
    plt.close()

    # Guardar el modelo y el scaler
    joblib.dump(clf, 'entrenamiento_modelo.joblib')
    joblib.dump(scaler, 'scaler.joblib')
    print("\nModelo y scaler guardados correctamente.")

else:
    print("No se encontraron datos para entrenar el modelo.")
