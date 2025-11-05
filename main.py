import os
import json
from google.oauth2 import service_account  # Asegúrate de que esta biblioteca esté instalada en tu requirements.txtimport logging
import re
from datetime import datetime
from flask import Flask, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import telegram
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# === CONFIGURACIÓN ===
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Token del bot (en Render: variable de entorno BOT_TOKEN)
BOT_TOKEN = os.environ['BOT_TOKEN']

# Google Sheets (credenciales en variable GOOGLE_CREDS o archivo creds.json)
try:
    # Intenta leer desde variable de entorno (recomendado en Render)
   creds_json_str = os.environ.get('GOOGLE_CREDS')
if creds_json_str:
    creds_dict = json.loads(creds_json_str)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
else:
    raise ValueError("La variable de entorno GOOGLE_CREDS no está configurada")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, 
        ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])
except:
    # Fallback: archivo local (solo para pruebas local, no en Render)
    creds = ServiceAccountCredentials.from_json_keyfile_name('creds.json', 
        ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive'])

client = gspread.authorize(creds)
sheet = client.open("Gastos").sheet1  # Cambia "Gastos" por el nombre de tu hoja

# Flask app para webhook
app = Flask(__name__)
bot = telegram.Bot(token=BOT_TOKEN)
application = Application.builder().token(BOT_TOKEN).build()

# === COMANDOS ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot de gastos.\n\n"
        "Envía: *Gasto 500 en luz*\n"
        "Usa: /resumen para ver el total",
        parse_mode='Markdown'
    )

async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        data = sheet.get_all_values()
        total = 0
        for row in data[1:]:  # Saltar encabezado
            if len(row) > 1 and row[1].strip().replace('.', '', 1).isdigit():
                total += float(row[1])
        await update.message.reply_text(f"Total de gastos: *${total:,.0f}*", parse_mode='Markdown')
    except Exception as e:
        logger.error(f"Error en resumen: {e}")
        await update.message.reply_text("Error al leer la hoja. Verifica permisos.")

# === MENSAJES DE TEXTO ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    logger.info(f"Mensaje recibido: {text}")

    # Regex: "Gasto 300 en luz" (insensible a mayúsculas)
    match = re.match(r'gasto\s+(\d+)\s+en\s+(.+)', text, re.IGNORECASE)
    if match:
        try:
            monto = match.group(1)
            categoria = match.group(2).strip().lower().capitalize()
            fecha = datetime.now().strftime('%Y-%m-%d')
            
            # Guardar en Google Sheets
            sheet.append_row([fecha, monto, categoria])
            
            await update.message.reply_text(
                f"Registrado:\n*{monto} en {categoria}*\nFecha: {fecha}",
                parse_mode='Markdown'
            )
        except Exception as e:
            logger.error(f"Error al guardar: {e}")
            await update.message.reply_text("No se pudo guardar. Revisa logs.")
    else:
        await update.message.reply_text(
            "Formato inválido.\nUsa: *Gasto 300 en luz*",
            parse_mode='Markdown'
        )

# === REGISTRAR HANDLERS ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("resumen", resumen))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# === WEBHOOK ROUTE (Render) ===
@app.route(f'/{BOT_TOKEN}', methods=['POST'])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    application.process_update(update)
    return '', 200

@app.route('/')
def index():
    return "Bot de Gastos Activo!"

# === INICIAR ===
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
