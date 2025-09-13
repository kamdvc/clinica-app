#!/bin/bash

# Script para actualizar contraseña de admin en servidor
# Uso: chmod +x update_password_server.sh && ./update_password_server.sh

echo "🔐 Actualizando contraseña de admin en clinica_..."
echo "==============================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "run.py" ] || [ ! -d "app" ]; then
    echo "❌ Error: No estás en el directorio del proyecto clinica_"
    echo "   Navega a la carpeta clinica_ primero: cd /ruta/hacia/clinica_"
    exit 1
fi

# Crear backup antes de modificar
backup_dir="backup_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$backup_dir"
echo "📁 Creando backup en: $backup_dir"

# Copiar archivos originales
cp setup_db.py "$backup_dir/" 2>/dev/null
cp setup_sqlite.py "$backup_dir/" 2>/dev/null
cp init_db.py "$backup_dir/" 2>/dev/null
cp reset_admin.py "$backup_dir/" 2>/dev/null

echo "✅ Backup creado exitosamente"

# Aplicar cambios
echo "🔄 Aplicando cambios..."

# Nueva contraseña segura
OLD_PASSWORD="admin123"
NEW_PASSWORD="M3d1c@lC1!n1c#2025\$Adm9&"

# Modificar archivos
files=("setup_db.py" "setup_sqlite.py" "init_db.py" "reset_admin.py")

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   📝 Modificando $file..."
        sed -i "s/$OLD_PASSWORD/$NEW_PASSWORD/g" "$file"
        echo "   ✅ $file actualizado"
    else
        echo "   ⚠️  $file no encontrado"
    fi
done

echo ""
echo "🔍 Verificando cambios aplicados:"
grep -l "M3d1c@lC1" *.py 2>/dev/null | while read file; do
    count=$(grep -c "M3d1c@lC1" "$file")
    echo "   ✅ $file: $count coincidencias"
done

echo ""
echo "🎉 ¡Actualización completada!"
echo "📋 Nueva contraseña: M3d1c@lC1!n1c#2025\$Adm9&"
echo "🔧 Para aplicar: python reset_admin.py"
echo "📁 Backup guardado en: $backup_dir"































