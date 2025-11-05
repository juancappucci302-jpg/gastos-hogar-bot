import os
import json
import re
import logging
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

app = Flask(__name__)

# === CARGAR CREDENCIALES DE GOOGLE SHEETS DESDE VARIABLE DE ENTORNO ===
def get_google_credentials():
    creds_json_str = os.environ.get('GOOGLE_CREDS')
    if not creds_json_str:
        logger.error("Variable de entorno 'GOOGLE_CREDS' no encontrada.")
        raise ValueError("Falta la variable de entorno GOOGLE_CREDS. Configúrala en Render.")
    
    try:
        creds_dict = json.loads(creds_json_str)
    except json.JSONDecodeError as e:
        logger.error(f"Error al parsear GOOGLE_CREDS como JSON: {e}")
        raise ValueError("GOOGLE_CREDS no es un JSON válido.")
    
    # Scopes necesarios para Google Sheets y Drive
    scope = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    try:
        credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        return credentials
    except Exception as e:
        logger.error(f"Error al crear credenciales de Google: {e}")
        raise

# Inicializar cliente de Google Sheets
try:
    gc = gspread.authorize(get_google_credentials())
    logger.info("Conexión exitosa con Google Sheets.")
except Exception as e:
    logger.critical(f"No se pudo conectar a Google Sheets: {e}")
    gc = None  # Evita errores posteriores si falla

# === CONFIGURACIÓN DEL BOT DE TELEGRAM ===
TOKEN = os.environ.get('TELEGRAM_TOKEN')
if not TOKEN:
    raise ValueError("Falta la variable de entorno TELEGRAM_TOKEN")

application = Application.builder().token(TOKEN).build()

# === COMANDOS DEL BOT ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "¡Hola! Soy tu bot de gastos del hogar.\n"
        "Usa /add para registrar un gasto.\n"
        "Ejemplo: /add 1500 Comida - Supermercado"
    )

async def add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not gc:
        await update.message.reply_text("Error: No se pudo conectar a Google Sheets.")
        return

    try:
        text = update.message.text
        parts = text.split(' ', 3)  # /add monto categoría - descripción
        if len(parts) < 3:
            await update.message.reply_text("Formato: /add <monto> <categoría> [- descripción]")
            return

        monto = parts[1]
        categoria = parts[2]
        descripcion = parts[3] if len(parts) > 3 else ""

        # Validar monto
        if not re.match(r'^\d+(\.\d{1,2})?$', monto):
            await update.message.reply_text("El monto debe ser un número válido (ej: 1500 o 12.50)")
            return

        # Abrir hoja de cálculo (cambia 'NombreDeTuHoja' por el nombre real)
        sheet = gc.open("Gastos Hogar").sheet1

        # Agregar fila: [fecha, monto, categoría, descripción]
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
        row = [fecha, float(monto), categoria, descripcion]
        sheet.append_row(row)

        await update.message.reply_text(f"Gasto registrado:\n💸 ${monto} | {categoria} | {descripcion}")
    
    except Exception as e:
        logger.error(f"Error al registrar gasto: {e}")
        await update.message.reply_text("Ocurrió un error al guardar el gasto.")

# === REGISTRAR HANDLERS ===
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("add", add_expense))

# === WEBHOOK PARA RENDER (Flask) ===
@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        update = telegram.Update.de_json(request.get_json(force=True), application.bot)
        application.process_update(update)
        return 'OK', 200
    return 'Error', 400

@app.route('/')
def home():
    return "Bot de gastos activo. Usa Telegram para interactuar."

# === INICIAR BOT (solo si se ejecuta localmente) ===
if __name__ == '__main__':
    # Para pruebas locales
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
