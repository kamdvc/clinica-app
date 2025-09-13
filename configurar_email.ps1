# Script para configurar email en Windows PowerShell
# Ejecutar: .\configurar_email.ps1

Write-Host "=== Configuración de Email para Sistema Clínica ===" -ForegroundColor Green
Write-Host ""

Write-Host "Para habilitar el envío de correos, necesitas configurar las siguientes variables:" -ForegroundColor Yellow
Write-Host ""

# Solicitar datos del usuario
$mailServer = Read-Host "Servidor SMTP (presiona Enter para Gmail: smtp.gmail.com)"
if ([string]::IsNullOrWhiteSpace($mailServer)) {
    $mailServer = "smtp.gmail.com"
}

$mailPort = Read-Host "Puerto SMTP (presiona Enter para 587)"
if ([string]::IsNullOrWhiteSpace($mailPort)) {
    $mailPort = "587"
}

$mailUsername = Read-Host "Tu email completo (ej: tu_email@gmail.com)"
$mailPassword = Read-Host "Contraseña de aplicación (NO tu contraseña normal)" -AsSecureString
$mailPasswordPlain = [System.Runtime.InteropServices.Marshal]::PtrToStringAuto([System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($mailPassword))

$mailSender = Read-Host "Email remitente (presiona Enter para noreply@clinica.com)"
if ([string]::IsNullOrWhiteSpace($mailSender)) {
    $mailSender = "noreply@clinica.com"
}

Write-Host ""
Write-Host "Configurando variables de entorno..." -ForegroundColor Blue

# Configurar variables de entorno para la sesión actual
$env:MAIL_SERVER = $mailServer
$env:MAIL_PORT = $mailPort
$env:MAIL_USE_TLS = "true"
$env:MAIL_USERNAME = $mailUsername
$env:MAIL_PASSWORD = $mailPasswordPlain
$env:MAIL_DEFAULT_SENDER = $mailSender

Write-Host "✅ Variables configuradas para esta sesión:" -ForegroundColor Green
Write-Host "   MAIL_SERVER = $mailServer"
Write-Host "   MAIL_PORT = $mailPort"
Write-Host "   MAIL_USE_TLS = true"
Write-Host "   MAIL_USERNAME = $mailUsername"
Write-Host "   MAIL_PASSWORD = ****" 
Write-Host "   MAIL_DEFAULT_SENDER = $mailSender"
Write-Host ""

Write-Host "=== INSTRUCCIONES IMPORTANTES ===" -ForegroundColor Red
Write-Host ""
if ($mailServer -eq "smtp.gmail.com") {
    Write-Host "📧 Para Gmail:" -ForegroundColor Yellow
    Write-Host "1. Ve a tu cuenta de Google > Seguridad"
    Write-Host "2. Activa la verificación en 2 pasos"
    Write-Host "3. Genera una 'Contraseña de aplicación' específica para esta app"
    Write-Host "4. Usa ESA contraseña, NO tu contraseña normal de Gmail"
    Write-Host ""
}

Write-Host "🚀 Para aplicar la configuración:" -ForegroundColor Cyan
Write-Host "1. Ejecuta este script: .\configurar_email.ps1"
Write-Host "2. En la MISMA ventana de PowerShell, ejecuta: python run.py"
Write-Host "3. Prueba la recuperación de contraseña"
Write-Host ""

Write-Host "⚠️  NOTA: Las variables solo funcionan en esta sesión de PowerShell." -ForegroundColor Yellow
Write-Host "   Si cierras la ventana, tendrás que ejecutar el script otra vez."
Write-Host ""

# Crear archivo .env para facilidad futura
Write-Host "💾 Creando archivo .env para referencia futura..." -ForegroundColor Blue
$envContent = @"
# Configuración de Email - NO SUBIR A GIT
MAIL_SERVER=$mailServer
MAIL_PORT=$mailPort
MAIL_USE_TLS=true
MAIL_USERNAME=$mailUsername
MAIL_PASSWORD=$mailPasswordPlain
MAIL_DEFAULT_SENDER=$mailSender
"@

$envContent | Out-File -FilePath ".env" -Encoding UTF8
Write-Host "✅ Archivo .env creado (recuerda agregarlo a .gitignore)"
Write-Host ""

Write-Host "🎉 ¡Configuración completada! Ahora ejecuta 'python run.py' en esta misma ventana." -ForegroundColor Green





























