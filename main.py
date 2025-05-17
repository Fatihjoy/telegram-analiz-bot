import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import fitz
import openai

# Kayıtlı içerikleri tutacak dosya
DATA_FILE = "documents_store.txt"

# Logging ayarı
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# OpenAI API anahtarı
openai.api_key = os.getenv("OPENAI_API_KEY")

# Yalnızca adminlerin PDF/metin eklemesine izin verelim
ADMIN_IDS = [7097093174]  # Buraya kendi Telegram user ID'ni gir

# PDF'ten metin çek
def extract_text_from_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

# Belleğe metin ekle
def append_to_knowledgebase(content: str):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(content + "\n\n")

# Başlangıç komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! Soru sormak için /sor yazın. Adminler bilgi eklemek için sadece PDF yükleyebilir.")

# PDF gönderildiğinde çalışır
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bu özelliği sadece admin kullanabilir.")
        return

    file = await update.message.document.get_file()
    path = f"/tmp/{file.file_unique_id}.pdf"
    await file.download_to_drive(path)
    text = extract_text_from_pdf(path)
    append_to_knowledgebase(text)
    await update.message.reply_text("PDF içeriği başarıyla kaydedildi.")

# Soru komutu
async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question = ' '.join(context.args)
    if not question:
        await update.message.reply_text("Lütfen bir soru girin. Örnek: /sor burs hangi şehirlerde var?")
        return

    if not os.path.exists(DATA_FILE):
        await update.message.reply_text("Henüz içerik eklenmemiş.")
        return

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        content = f.read()

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Aşağıdaki metne göre soruyu cevapla."},
            {"role": "user", "content": f"Metin:\n{content}\n\nSoru: {question}"}
        ]
    )

    await update.message.reply_text(response['choices'][0]['message']['content'])

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_document))
    app.run_polling()

if __name__ == "__main__":
    main()
