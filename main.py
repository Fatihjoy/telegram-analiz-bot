import os
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from fuzzywuzzy import fuzz
import unidecode

logging.basicConfig(level=logging.INFO)
DATA_FILE = "knowledge.txt"
ADMIN_IDS = [1568041366]

def append_qa_entry(question: str, answer: str):
    with open(DATA_FILE, "a", encoding="utf-8") as f:
        f.write(f"Soru: {question.strip()}\n")
        f.write(f"Cevap: {answer.strip()}\n")
        f.write("---\n")

def load_qa_pairs():
    if not os.path.exists(DATA_FILE):
        return []

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        blocks = f.read().split("---\n")

    qa_pairs = []
    for block in blocks:
        if "Soru:" in block and "Cevap:" in block:
            lines = block.strip().split("\n")
            question = lines[0].replace("Soru:", "").strip()
            answer = lines[1].replace("Cevap:", "").strip()
            qa_pairs.append((question, answer))
    return qa_pairs

def normalize(text):
    return unidecode.unidecode(text.lower())

def count_matching_words(input_text, target_text):
    input_words = set(normalize(input_text).split())
    target_words = set(normalize(target_text).split())
    return len(input_words & target_words)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Soru-Cevap sistemine hoş geldiniz. Soru eklemek için /ekle, sormak için /sor kullanın.")

async def ekle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("Bu komutu sadece admin kullanabilir.")
        return

    text = ' '.join(context.args)
    if "=" not in text:
        await update.message.reply_text("Lütfen şu formatta girin: /ekle Soru ? = Cevap")
        return

    question, answer = text.split("=", 1)
    append_qa_entry(question.strip(), answer.strip())
    await update.message.reply_text("Soru ve cevap başarıyla kaydedildi.")

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
        blocks = f.read().split("---\n")
        for block in blocks:
            if "Soru:" in block and "Cevap:" in block:
                lines = block.strip().split("\n")
                question = lines[0].replace("Soru:", "").strip()
                answer = lines[1].replace("Cevap:", "").strip()
                append_qa_entry(question, answer)

    await update.message.reply_text(f"{update.message.document.file_name} başarıyla işlendi ve kaydedildi.")

async def sor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_query = ' '.join(context.args).strip()
    if not user_query:
        await update.message.reply_text("Lütfen bir soru girin.")
        return

    qa_pairs = load_qa_pairs()
    normalized_query = normalize(user_query)

    # Kelime kapsayıcılığına göre eşleşme
    best_match = None
    best_word_overlap = 0
    best_score = 0

    for q, a in qa_pairs:
        overlap = count_matching_words(user_query, q)
        score = fuzz.partial_ratio(normalize(q), normalized_query)
        logging.info(f"Kelime eşleşmesi: '{q}' → {overlap} kelime, {score} fuzzy puan")
        if overlap > best_word_overlap or (overlap == best_word_overlap and score > best_score):
            best_match = a
            best_word_overlap = overlap
            best_score = score

    if best_match and (best_word_overlap > 0 or best_score >= 60):
        await update.message.reply_text(best_match)
    else:
        await update.message.reply_text("Bu soruya dair bilgi bulunamadı.")

def main():
    app = ApplicationBuilder().token(os.getenv("BOT_TOKEN")).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ekle", ekle))
    app.add_handler(CommandHandler("sor", sor))
    app.add_handler(MessageHandler(filters.Document.TEXT, handle_txt_file))
    app.run_polling()

if __name__ == "__main__":
    main()
