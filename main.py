from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8551964942:AAGeTM_YA5Z-lCa83ze295X_8E6CLpHMrrY")  # Usa env var!

# Opción 1: Handler en /webhook → necesitas setear webhook a /webhook
# @app.route('/webhook', methods=['POST'])

# Opción 2: Handler en raíz → más simple
@app.route('/', methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        print("Update recibido:", update)

        if 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '').strip()

            reply = ""

            if text == '/start':
                reply = """
¡Bienvenido al *Bot de Gastos del Hogar*!  
Envía gastos así:
> Gasto 300 en luz
> Gasto 150 en supermercado

Comandos:
• /start → esta plantilla
• /total → ver gastos del mes
                """.strip()
            elif text.lower().startswith('gasto '):
                reply = "Gasto registrado (próximamente con DB)"
            else:
                reply = "Escribe /start para ver cómo usarme"

            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": reply,
                    "parse_mode": "Markdown"
                }
            )
        return jsonify({"status": "ok"}), 200
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 400

@app.route('/')
def home():
    return "Bot de gastos activo"

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
