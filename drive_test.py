from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

# Autenticación
gauth = GoogleAuth()
gauth.LocalWebserverAuth()

drive = GoogleDrive(gauth)

# Crear un archivo de prueba
file1 = drive.CreateFile({'title': 'test.txt'})
file1.SetContentString('Hola, este es un archivo de prueba')
file1.Upload()

print("Archivo subido con éxito a Google Drive")
