import base64

# Ruta de la imagen
with open("2.jpg", "rb") as img_file:
    base64_string = base64.b64encode(img_file.read()).decode("utf-8")
    print(base64_string)
