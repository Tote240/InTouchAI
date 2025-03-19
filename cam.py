import cv2

def listar_camaras_disponibles(max_dispositivos=10):
    dispositivos_disponibles = []
    for i in range(max_dispositivos):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            dispositivos_disponibles.append(i)
            cap.release()
    return dispositivos_disponibles

camaras = listar_camaras_disponibles()
print("Cámaras disponibles:", camaras)
