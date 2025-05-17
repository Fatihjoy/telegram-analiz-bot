import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

logging.basicConfig(level=logging.INFO)
DATA_FILE = "knowledge.txt"
ADMIN_IDS = [1568041366]

def append_to_knowledgebase(text: str):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(text.strip() + "\n")

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
    await update.message.reply_text("Merhaba! Bilgi eklemek için /ekle yazın. Soru sormak için /sor kullanın.")

async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bu komutu sadece admin kullanabilir.")
        return

    text = ' '.join(context.args)
    if not text:
        await update.message.reply_text("Eklemek istediğiniz metni de yazmalısınız.")
        return

    append_to_knowledgebase(text)
    await update.message.reply_text("Bilgi başarıyla kaydedildi.")

async def handle_txt_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bu özelliği sadece admin kullanabilir.")
        return

    file = await update.message.document.get_file()
    if not update.message.document.file_name.endswith(".txt"):
        await update.message.reply_text("Sadece .txt dosyaları kabul ediliyor.")
        return

    path = f"/tmp/{file.file_unique_id}.txt"
    await file.download_to_drive(path)

    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    append_to_knowledgebase(content)
    await update.message.reply_text(f"{update.message.document.file_name} başarıyla hafızaya kaydedildi.")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Lütfen bir soru girin.")
        return

    result = search_knowledgebase(query)
    await update.message.reply_text(result)

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(MessageHandler(filters.Document.TEXT, handle_txt_file))
    app.run_polling()

if __name__ == "__main__":
    main()
