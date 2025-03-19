import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score, GridSearchCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.pipeline import Pipeline
from imblearn.over_sampling import SMOTE
import joblib
import seaborn as sns
import matplotlib.pyplot as plt
from pymongo import MongoClient

class EntrenadorModeloLenguajeSeñas:
    def __init__(self, uri_mongodb='mongodb+srv://josuecalabran:23803400.@ia.ebtrt.mongodb.net/'):
        """
        Inicializar el entrenador con conexión a MongoDB
        """
        # Conexión a MongoDB
        self.cliente = MongoClient(uri_mongodb)
        self.bd = self.cliente['Lenguaje-señas']
        self.coleccion_gestos = self.bd['gestures']
        
        # Componentes de aprendizaje automático
        self.escalador = StandardScaler()
        self.codificador_etiquetas = LabelEncoder()
        self.modelo = None
        
    def cargar_datos(self):
        """
        Cargar datos de gestos desde MongoDB y preparar para entrenamiento
        """
        # Obtener gestos únicos
        gestos = self.coleccion_gestos.distinct('label')
        
        # Recopilar datos para cada gesto
        marcos_datos_gestos = []
        for gesto in gestos:
            print(f"Cargando datos para {gesto}...")
            
            # Obtener documentos de gesto
            documentos_gesto = list(self.coleccion_gestos.find({'label': gesto}))
            
            # Procesar cada documento
            for doc in documentos_gesto:
                df = pd.DataFrame(
                    doc['data'], 
                    columns=['gesture'] + [f"point_{i}_{coord}" for i in range(21) for coord in ("x", "y", "z")]
                )
                marcos_datos_gestos.append(df)
        
        # Combinar todos los datos de gestos
        if not marcos_datos_gestos:
            raise ValueError("No se encontraron datos de gestos para entrenar")
        
        self.datos_gestos = pd.concat(marcos_datos_gestos, ignore_index=True)
        
        # Mostrar distribución de clases
        print("\nDistribución de Clases:")
        print(self.datos_gestos['gesture'].value_counts())
        
        return self
    
    def preparar_datos(self, tamano_prueba=0.2, estado_aleatorio=42):
        """
        Preparar datos para entrenamiento con preprocesamiento avanzado
        """
        # Separar características y etiquetas
        X = self.datos_gestos.drop("gesture", axis=1)
        y = self.datos_gestos["gesture"]
        
        # Codificar etiquetas
        y_codificado = self.codificador_etiquetas.fit_transform(y)
        
        # Dividir datos
        X_entrenamiento, X_prueba, y_entrenamiento, y_prueba = train_test_split(
            X, y_codificado, 
            test_size=tamano_prueba, 
            random_state=estado_aleatorio, 
            stratify=y_codificado
        )
        
        # Aplicar SMOTE para balancear
        smote = SMOTE(random_state=estado_aleatorio)
        X_entrenamiento_balanceado, y_entrenamiento_balanceado = smote.fit_resample(X_entrenamiento, y_entrenamiento)
        
        # Almacenar datos para uso posterior
        self.X_entrenamiento = X_entrenamiento_balanceado
        self.X_prueba = X_prueba
        self.y_entrenamiento = y_entrenamiento_balanceado
        self.y_prueba = y_prueba
        
        print("\nDistribución de Clases Después de Balancear:")
        print(pd.Series(self.codificador_etiquetas.inverse_transform(y_entrenamiento_balanceado)).value_counts())
        
        return self
    
    def entrenar_modelo(self):
        """
        Entrenar clasificador RandomForest con ajuste de hiperparámetros
        """
        # Definir rejilla de parámetros para ajuste
        rejilla_parametros = {
            'clasificador__n_estimators': [100, 200, 300],
            'clasificador__max_depth': [10, 15, 20, None],
            'clasificador__min_samples_split': [2, 5, 10],
            'clasificador__min_samples_leaf': [1, 2, 4]
        }
        
        # Crear pipeline con escalado
        pipeline = Pipeline([
            ('escalador', self.escalador),
            ('clasificador', RandomForestClassifier(
                random_state=42, 
                class_weight='balanced'
            ))
        ])
        
        # Realizar búsqueda de cuadrícula con validación cruzada
        busqueda_cuadricula = GridSearchCV(
            pipeline, 
            rejilla_parametros, 
            cv=5, 
            scoring='accuracy', 
            n_jobs=-1
        )
        
        # Ajustar la búsqueda
        busqueda_cuadricula.fit(self.X_entrenamiento, self.y_entrenamiento)
        
        # Obtener mejor modelo
        self.modelo = busqueda_cuadricula.best_estimator_
        
        # Imprimir mejores parámetros
        print("\nMejores Parámetros:")
        print(busqueda_cuadricula.best_params_)
        
        return self
    
    def evaluar_modelo(self):
        """
        Evaluación integral del modelo
        """
        # Predicciones
        y_predicho = self.modelo.predict(self.X_prueba)
        y_predicho_decodificado = self.codificador_etiquetas.inverse_transform(y_predicho)
        y_prueba_decodificado = self.codificador_etiquetas.inverse_transform(self.y_prueba)
        
        # Informe de clasificación
        print("\nInforme de Clasificación:")
        print(classification_report(y_prueba_decodificado, y_predicho_decodificado))
        
        # Matriz de confusión
        matriz_confusion = confusion_matrix(self.y_prueba, y_predicho)
        plt.figure(figsize=(10, 8))
        etiquetas_unicas = self.codificador_etiquetas.classes_
        sns.heatmap(
            matriz_confusion, 
            annot=True, 
            fmt='d', 
            cmap='Blues',
            xticklabels=etiquetas_unicas,
            yticklabels=etiquetas_unicas
        )
        plt.title('Matriz de Confusión')
        plt.xlabel('Etiqueta Predicha')
        plt.ylabel('Etiqueta Verdadera')
        plt.tight_layout()
        plt.savefig('matriz_confusion.png')
        plt.close()
        
        # Validación cruzada
        puntuaciones_cv = cross_val_score(self.modelo, self.X_entrenamiento, self.y_entrenamiento, cv=5)
        print("\nPuntuaciones de Validación Cruzada:", puntuaciones_cv)
        print(f"Puntuación Media de Validación Cruzada: {puntuaciones_cv.mean():.4f} (+/- {puntuaciones_cv.std() * 2:.4f})")
        
        return self
    
    def guardar_modelo(self, ruta_modelo='modelo_lenguaje_señas.joblib', ruta_codificador='codificador_etiquetas.joblib'):
        """
        Guardar modelo entrenado y codificador de etiquetas
        """
        # Guardar modelo
        joblib.dump(self.modelo, ruta_modelo)
        
        # Guardar codificador de etiquetas
        joblib.dump(self.codificador_etiquetas, ruta_codificador)
        
        print("\nModelo y codificador de etiquetas guardados correctamente.")
        
        return self
    
    def __del__(self):
        """
        Asegurar cierre de conexión de MongoDB
        """
        if hasattr(self, 'cliente'):
            self.cliente.close()

def main():
    # Crear entrenador
    entrenador = EntrenadorModeloLenguajeSeñas()
    
    try:
        # Ejecutar pipeline de entrenamiento completo
        (entrenador.cargar_datos()
                 .preparar_datos()
                 .entrenar_modelo()
                 .evaluar_modelo()
                 .guardar_modelo())
    except Exception as e:
        print(f"Ocurrió un error durante el entrenamiento: {e}")
    finally:
        # Asegurar liberación de recursos
        del entrenador

if __name__ == "__main__":
    main()