import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import fitz  # PyMuPDF
import openai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
openai.api_key = os.getenv("OPENAI_API_KEY")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Lütfen bir PDF dosyası gönderin ve ardından /sor komutuyla sorunuzu yazın.")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("pdf_text"):
        await update.message.reply_text("Lütfen önce bir PDF dosyası yükleyin.")
        return

    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Lütfen bir soru girin. Örnek: /sor Yaş sınırı nedir?")
        return

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Aşağıdaki metne göre soruyu cevapla."},
            {"role": "user", "content": f'''Metin:
{context.user_data["pdf_text"]}

Soru: {question}'''}
        ]
    )

    await update.message.reply_text(response['choices'][0]['message']['content'])

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    path = f"/tmp/{file.file_unique_id}.pdf"
    await file.download_to_drive(path)

    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()

    context.user_data["pdf_text"] = text
    await update.message.reply_text("PDF başarıyla alındı. Şimdi /sor komutuyla sorunuzu yazabilirsiniz.")

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.run_polling()

if __name__ == "__main__":
    main()
