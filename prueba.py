import tensorflow as tf
import numpy as np

def test_modelo():
    try:
        print("⌛ Intentando cargar el modelo...")
        
        # Cargar el modelo
        interpreter = tf.lite.Interpreter(model_path="traductor_senas/assets/models/modelo_gestos.tflite")
        interpreter.allocate_tensors()
        
        # Obtener detalles del modelo
        input_details = interpreter.get_input_details()
        output_details = interpreter.get_output_details()
        
        print("\n✅ Detalles de entrada:")
        for detail in input_details:
            print(f"  - Forma: {detail['shape']}")
            print(f"  - Tipo: {detail['dtype']}")
            print(f"  - Nombre: {detail['name']}")
            print(f"  - Cuantización: {detail['quantization']}")
        
        print("\n✅ Detalles de salida:")
        for detail in output_details:
            print(f"  - Forma: {detail['shape']}")
            print(f"  - Tipo: {detail['dtype']}")
            print(f"  - Nombre: {detail['name']}")
            print(f"  - Cuantización: {detail['quantization']}")
        
        # Probar con datos de ejemplo
        input_shape = input_details[0]['shape']
        print(f"\n📊 Forma de entrada requerida: {input_shape}")
        
        # Crear datos de prueba
        dummy_input = np.zeros(input_shape, dtype=np.float32)
        
        # Establecer el tensor de entrada
        interpreter.set_tensor(input_details[0]['index'], dummy_input)
        
        # Realizar la inferencia
        print("\n⌛ Probando inferencia...")
        interpreter.invoke()
        
        # Obtener los resultados
        output_data = interpreter.get_tensor(output_details[0]['index'])
        print("\n✅ Prueba de inferencia exitosa")
        print(f"📊 Forma de salida: {output_data.shape}")
        
    except Exception as e:
        print(f"\n❌ Error al probar el modelo: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    test_modelo()