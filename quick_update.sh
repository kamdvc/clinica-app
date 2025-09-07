#!/bin/bash
# Script rápido para actualizar contraseña en el servidor
# Ejecutar desde la carpeta clinica_

echo "🔐 Actualizando contraseña admin..."

# Backup rápido
cp setup_db.py setup_db.py.bak 2>/dev/null
cp setup_sqlite.py setup_sqlite.py.bak 2>/dev/null
cp init_db.py init_db.py.bak 2>/dev/null
cp reset_admin.py reset_admin.py.bak 2>/dev/null

# Cambiar contraseña
sed -i 's/admin123/M3d1c@lC1!n1c#2025$Adm9\&/g' *.py

echo "✅ Archivos actualizados. Ejecuta: python reset_admin.py"















