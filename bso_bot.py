import re
import cv2
import numpy as np
from telegram import Update
from telegram.ext import Application, MessageHandler, filters
import pytesseract
from PIL import Image
import io

TOKEN = "8964967246:AAHPmsVShyvzhcy6RTtjh2om-wWoPtIuA3I"

async def extract_bso_values(image_bytes):
    img = Image.open(io.BytesIO(image_bytes))
    img_cv = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    custom_config = r'--oem 3 --psm 6 -l rus+eng'
    text = pytesseract.image_to_string(thresh, config=custom_config)
    bso_pattern = r'\b[А-Я]{2}\s?\d{6,7}\b'
    matches = re.findall(bso_pattern, text)
    return list(dict.fromkeys(matches))

async def handle_image(update: Update, context):
    if update.message.photo:
        file = await update.message.photo[-1].get_file()
    elif update.message.document and update.message.document.mime_type.startswith('image/'):
        file = await update.message.document.get_file()
    else:
        await update.message.reply_text("❌ Отправь фото с таблицей")
        return
    await update.message.reply_text("🔍 Обрабатываю...")
    image_bytes = await file.download_as_bytearray()
    try:
        bso_values = await extract_bso_values(image_bytes)
        if bso_values:
            result = "✅ **Найденные БСО:**\n\n"
            for i, val in enumerate(bso_values, 1):
                result += f"{i}. `{val}`\n"
            result += f"\n📊 Всего: {len(bso_values)}"
            await update.message.reply_text(result, parse_mode="Markdown")
        else:
            await update.message.reply_text("⚠️ Не найдено значений БСО")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.PHOTO | filters.Document.IMAGE, handle_image))
    print("✅ Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
