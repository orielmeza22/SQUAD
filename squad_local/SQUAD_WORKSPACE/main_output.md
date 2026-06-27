# Usa la imagen base de Python para Flask
FROM python:3.8-slim

# Establece el directorio de trabajo como /app
WORKDIR /app

# Copia el archivo app.py y las dependencias del sistema de archivos host al contenedor
COPY . .

# Instala las dependencias necesarias
RUN pip install flask sqlite3

# Exponga la puerta 5000 para Flask
EXPOSE 5000

# Ejecuta el servidor web
CMD ["python", "app.py"]
