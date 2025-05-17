import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO)
DATA_FILE = "knowledge.txt"
ADMIN_IDS = [1568041366]  # Recep'in Telegram user ID'si

def extract_text_from_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def append_to_knowledgebase(text: str):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(text + "\n")

def search_knowledgebase(query: str):
    if not os.path.exists(DATA_FILE):
        return "Henüz veri eklenmemiş."

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    query_lower = query.lower()
    for line in lines:
        if any(word in line.lower() for word in query_lower.split()):
            return line.strip()

    return "Bu soruya dair bilgi bulunamadı."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Sorularınızı /sor komutuyla sorabilirsiniz.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bu özelliği sadece admin kullanabilir.")
        return

    file = await update.message.document.get_file()
    path = f"/tmp/{file.file_unique_id}.pdf"
    await file.download_to_drive(path)
    text = extract_text_from_pdf(path)
    append_to_knowledgebase(text)
    await update.message.reply_text("PDF başarıyla kaydedildi!")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Lütfen bir soru girin. Örnek: /sor yaş sınırı nedir?")
        return

    response = search_knowledgebase(query)
    await update.message.reply_text(response)

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.run_polling()

if __name__ == "__main__":
    main()
