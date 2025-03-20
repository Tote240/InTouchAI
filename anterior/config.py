from azure.storage.blob import BlobServiceClient
import os

class AzureConfig:
    # Cadena de conexión correcta
    STORAGE_CONNECTION_STRING = ""
    CONTAINER_NAME = "gestures-data"

def test_connection():
    try:
        # Crear cliente de blob storage
        blob_service_client = BlobServiceClient.from_connection_string(AzureConfig.STORAGE_CONNECTION_STRING)
        
        # Crear el contenedor si no existe
        container_client = blob_service_client.get_container_client(AzureConfig.CONTAINER_NAME)
        if not container_client.exists():
            container_client.create_container()
            print(f"Contenedor {AzureConfig.CONTAINER_NAME} creado exitosamente")
        
        # Listar contenedores existentes
        containers = blob_service_client.list_containers()
        print("\nContenedores disponibles:")
        for container in containers:
            print(f"- {container.name}")
            
        print("\n¡Conexión exitosa!")
        return True
    except Exception as e:
        print(f"\nError de conexión: {e}")
        return False

if __name__ == "__main__":
    print("Probando conexión con Azure Storage...")
    test_connection()
