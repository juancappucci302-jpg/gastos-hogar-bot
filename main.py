from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)
TOKEN = "8521848365:AAG8G68Z2R0MWg1CjlPUY2eSwpF6gCsb6fA"  # Tu token
WEBHOOK_PATH = "/webhook"

@app.route('/')
def home():
    return "Bot de gastos activo 🟢"

@app.route(WEBHOOK_PATH, methods=['POST'])
def webhook():
    try:
        update = request.get_json()
        print("Update recibido:", update)  # Log para depurar

        if 'message' in update:
            chat_id = update['message']['chat']['id']
            text = update['message'].get('text', '')

            reply = ""
            if text == '/start':
                reply = """
¡Bienvenido al *Bot de Gastos del Hogar*! 🏡💰

Envía gastos así:
> Gasto 300 en luz
> Gasto 150 en supermercado

Comandos:
• /start → esta plantilla
• /total → ver gastos del mes
                """.strip()
            elif text.lower().startswith('gasto '):
                reply = "✅ Gasto registrado (próximamente con DB)"
            else:
                reply = "Escribe /start para ver cómo usarme"

            # Enviar respuesta
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
        return jsonify({"status": "error"}), 200

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
