import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import fitz

logging.basicConfig(level=logging.INFO)
DATA_FILE = "knowledge.txt"
ADMIN_IDS = [1568041366]

def extract_text_from_pdf(path):
    text = ""
    with fitz.open(path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def append_pdf(filename, content):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"=== PDF: {filename} ===\n")
        f.write(content + "\n")
        f.write("=== SON ===\n\n")

def list_pdfs():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    pdfs = []
    for line in lines:
        if line.startswith("=== PDF:"):
            name = line.replace("=== PDF:", "").replace("===", "").strip()
            pdfs.append(name)
    return pdfs

def delete_pdf_section(filename):
    if not os.path.exists(DATA_FILE):
        return False

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    inside_target = False
    deleted = False

    for line in lines:
        if line.startswith(f"=== PDF: {filename} ==="):
            inside_target = True
            deleted = True
            continue
        if inside_target and line.strip() == "=== SON ===":
            inside_target = False
            continue
        if not inside_target:
            new_lines.append(line)

    if deleted:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            f.writelines(new_lines)
    return deleted

def search_knowledgebase(query: str):
    if not os.path.exists(DATA_FILE):
        return "Henüz veri eklenmemiş."

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()

    query_lower = query.lower()
    for line in lines:
        if line.startswith("===") or not line.strip():
            continue
        if any(word in line.lower() for word in query_lower.split()):
            return line.strip()

    return "Bu soruya dair bilgi bulunamadı."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Merhaba! PDF yüklemek için dosya gönderin. Soru sormak için /sor kullanın.")

async def handle_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bu özelliği sadece admin kullanabilir.")
        return

    file = await update.message.document.get_file()
    filename = update.message.document.file_name
    path = f"/tmp/{file.file_unique_id}.pdf"
    await file.download_to_drive(path)
    text = extract_text_from_pdf(path)
    append_pdf(filename, text)
    await update.message.reply_text(f"PDF yüklendi ve kaydedildi: {filename}")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = ' '.join(context.args)
    if not query:
        await update.message.reply_text("Lütfen bir soru girin.")
        return

    result = search_knowledgebase(query)
    await update.message.reply_text(result)

async def listepdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pdfs = list_pdfs()
    if not pdfs:
        await update.message.reply_text("Kayıtlı PDF yok.")
    else:
        await update.message.reply_text("Kayıtlı PDF'ler:\n" + "\n".join(f"- {p}" for p in pdfs))

async def silpdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("Bu komutu sadece admin kullanabilir.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("Silmek istediğiniz PDF adını yazın. Örn: /silpdf kilavuz.pdf")
        return

    filename = ' '.join(args)
    success = delete_pdf_section(filename)
    if success:
        await update.message.reply_text(f"{filename} silindi.")
    else:
        await update.message.reply_text(f"{filename} bulunamadı.")

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(CommandHandler("listepdf", listepdf))
    app.add_handler(CommandHandler("silpdf", silpdf))
    app.add_handler(MessageHandler(filters.Document.PDF, handle_pdf))
    app.run_polling()

if __name__ == "__main__":
    main()
