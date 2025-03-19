import tensorflow as tf

# Cargar el modelo LSTM
model = tf.keras.models.load_model('modelo_lstm.h5')

# Configurar el convertidor
converter = tf.lite.TFLiteConverter.from_keras_model(model)

# Optimizaciones
converter.optimizations = [tf.lite.Optimize.DEFAULT]
converter.target_spec.supported_ops = [
    tf.lite.OpsSet.TFLITE_BUILTINS,
    tf.lite.OpsSet.SELECT_TF_OPS
]
converter._experimental_lower_tensor_list_ops = False
converter.experimental_enable_resource_variables = True

# Convertir el modelo
tflite_model = converter.convert()

# Guardar el modelo convertido
with open('traductor_senas/assets/models/modelo_gestos.tflite', 'wb') as f:
    f.write(tflite_model)

print("Modelo convertido a TensorFlow Lite y guardado.")