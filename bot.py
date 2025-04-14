import os
import logging
import sqlite3
import pandas as pd
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# инициализация бд
def init_db():
    conn = sqlite3.connect('sources.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            url TEXT NOT NULL,
            xpath TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Обработчик start
    await update.message.reply_text(
        'Привет! Я бот для управления источниками парсинга. '
        'Отправьте мне Excel файл со следующими колонками:\n'
        '- title: название сайта\n'
        '- url: ссылка на сайт\n'
        '- xpath: путь к элементу с ценой'
    )

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # обработчик файлов
    try:
        # Получаем файл
        file = await context.bot.get_file(update.message.document.file_id)
        file_path = f"temp_{update.message.document.file_name}"
        await file.download_to_drive(file_path)

        # читаем файл
        df = pd.read_excel(file_path)
        
        # проверяем колонки
        required_columns = ['title', 'url', 'xpath']
        if not all(col in df.columns for col in required_columns):
            await update.message.reply_text(
                'Ошибка: файл должен содержать колонки: title, url, xpath'
            )
            return

        # сохраняем в бд
        conn = sqlite3.connect('sources.db')
        df.to_sql('sources', conn, if_exists='append', index=False)
        conn.close()

        # отправляем подтверждение
        await update.message.reply_text(
            f'Данные успешно сохранены!\n\n'
            f'Содержимое файла:\n{df.to_string()}'
        )

        # удаляем временный файл
        os.remove(file_path)

    except Exception as e:
        logger.error(f"Error processing file: {e}")
        await update.message.reply_text(
            'Произошла ошибка при обработке файла. '
            'Пожалуйста, убедитесь, что файл в правильном формате.'
        )

def main():
    # ЗАПУСК БОТА
    # инициализация бд
    init_db()

    # создание приложения
    application = Application.builder().token("").build()

    # добавление обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

    # запуск бота
    application.run_polling()

if __name__ == '__main__':
    main() 
