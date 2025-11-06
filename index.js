const express = require('express');
const axios = require('axios');

const app = express();
const PORT = process.env.PORT || 3000;
const TOKEN = '8521848365:AAG8G68Z2R0MWg1CjPUY2eSwpF6gCsb6fA'; // TU TOKEN
const WEBHOOK_PATH = '/webhook';

app.use(express.json());

// Ruta raíz (para que no muestre solo guiones)
app.get('/', (req, res) => {
  res.send('Bot de gastos activo 🟢');
});

// === WEBHOOK: RECIBE MENSAJES DE TELEGRAM ===
app.post(WEBHOOK_PATH, async (req, res) => {
  try {
    const update = req.body;
    console.log('Update recibido:', JSON.stringify(update, null, 2)); // LOG IMPORTANTE

    if (update.message) {
      const chatId = update.message.chat.id;
      const text = update.message.text || '';

      let reply = '';

      if (text === '/start') {
        reply = `
¡Bienvenido al *Bot de Gastos del Hogar*! 🏡💰

Envía gastos así:
> Gasto 300 en luz
> Gasto 150 en supermercado

Comandos:
• /start → esta plantilla
• /total → ver gastos del mes
        `.trim();
      } 
      else if (text.toLowerCase().startsWith('gasto ')) {
        reply = '✅ Gasto registrado (próximamente con DB)';
      }
      else {
        reply = 'Escribe /start para ver cómo usarme';
      }

      // ENVIAR RESPUESTA A TELEGRAM
      await axios.post(`https://api.telegram.org/bot${TOKEN}/sendMessage`, {
        chat_id: chatId,
        text: reply,
        parse_mode: 'Markdown'
      });
    }

    res.sendStatus(200); // Siempre responde OK
  } catch (error) {
    console.error('Error:', error.message);
    res.sendStatus(200);
  }
});

app.listen(PORT, () => {
  console.log(`Bot escuchando en puerto ${PORT}`);
  console.log(`Webhook: https://gastos-hogar-bot.onrender.com${WEBHOOK_PATH}`);
})*
