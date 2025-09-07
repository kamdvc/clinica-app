#!/usr/bin/env python3
"""
Script para generar hash de contraseña segura
Uso: python generate_password_hash.py
"""

from werkzeug.security import generate_password_hash

# Nueva contraseña segura
new_password = 'M3d1c@lC1!n1c#2025$Adm9&'

# Generar hash
password_hash = generate_password_hash(new_password)

print("=" * 60)
print("🔐 NUEVA CONTRASEÑA SEGURA PARA ADMIN")
print("=" * 60)
print(f"Contraseña: {new_password}")
print(f"Hash generado: {password_hash}")
print("=" * 60)
print("\n📋 COMANDO SQL PARA ACTUALIZAR:")
print(f"UPDATE usuario SET password_hash = '{password_hash}' WHERE usuario = 'admin';")
print("\n✅ Guarda esta información en un lugar seguro!")















