import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from openrouter_ai_qwery import get_response
# Конфигурация
TELEGRAM_TOKEN = "вставьте свой токен"

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🤖 Привет! Я-бот. Чем могу помочь?\n"
        "(Если я не справлюсь - позовите администратора) /admin\n"
        "🔄 /reset - сбросить историю диалога"
    )
    await update.message.reply_text(welcome_text)


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if delete_session(user_id):
        await update.message.reply_text("🔄 История диалога сброшена")
    else:
        await update.message.reply_text("❌ История не найдена")


async def admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👨💼 В ближайшее время вам ответит администратор")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_input = update.message.text

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action="typing"
    )

    try:
        response = await get_response(user_id, user_input)
        await update.message.reply_text(response)
    except Exception as e:
        logger.error(f"Error processing message: {e}")
        await update.message.reply_text("⚠️ Произошла ошибка при обработке запроса")


def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    handlers = [
        CommandHandler("start", start),
        CommandHandler("reset", reset),
        CommandHandler("admin", admin),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
    ]
    application.add_handlers(handlers)
    application.run_polling()


if __name__ == "__main__":
    main()
