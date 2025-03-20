import os
from pymongo import MongoClient
import gridfs

# Conexión a MongoDB
client = MongoClient('mongodb+srv://nombre+contraseña.@ia.ebtrt.mongodb.net/')
db = client['Lenguaje-señas']
gestures_collection = db['gestures']
fs = gridfs.GridFS(db)

def eliminar_gesto(nombre_gesto):
    """
    Elimina un gesto de la base de datos y sus archivos relacionados.
    
    Args:
        nombre_gesto (str): Nombre del gesto a eliminar.
    """
    # Buscar y eliminar el documento del gesto
    result = gestures_collection.delete_one({'label': nombre_gesto})
    if result.deleted_count > 0:
        print(f"Se eliminó el gesto '{nombre_gesto}' de la base de datos.")
    else:
        print(f"No se encontró el gesto '{nombre_gesto}' en la base de datos.")
    
    # Eliminar los archivos de imágenes relacionados
    cursor = fs.find({'filename': {'$regex': f'{nombre_gesto}_.*'}})
    for file in cursor:
        fs.delete(file._id)
        print(f"Se eliminó el archivo '{file.filename}' del GridFS.")

def main():
    # Solicitar el nombre del gesto a eliminar
    gesto_a_eliminar = input("Introduce el nombre del gesto a eliminar: ")
    
    # Eliminar el gesto
    eliminar_gesto(gesto_a_eliminar)

if __name__ == "__main__":
    main()