import os
from datetime import datetime
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ВСТАВЬ СЮДА СВОЙ TELEGRAM ID
ADMIN_ID = 603365919

PRICE = "0.15 €"
LOG_FILE = "client_logs.txt"

# Клавиатуры
keyboard_ru = [
    ["💧 Цена", "⚙️ Как пользоваться"],
    ["📞 Оператор", "🌍 Сменить язык"]
]

keyboard_bg = [
    ["💧 Цена", "⚙️ Как се ползва"],
    ["📞 Оператор", "🌍 Смени език"]
]

keyboard_en = [
    ["💧 Price", "⚙️ How to use"],
    ["📞 Operator", "🌍 Change language"]
]

markup_ru = ReplyKeyboardMarkup(keyboard_ru, resize_keyboard=True)
markup_bg = ReplyKeyboardMarkup(keyboard_bg, resize_keyboard=True)
markup_en = ReplyKeyboardMarkup(keyboard_en, resize_keyboard=True)

language_keyboard = [["Русский", "Български", "English"]]
language_markup = ReplyKeyboardMarkup(language_keyboard, resize_keyboard=True)


def get_markup(lang: str):
    if lang == "bg":
        return markup_bg
    if lang == "en":
        return markup_en
    return markup_ru


def log_message(user_id: int, username: str, full_name: str, lang: str | None, text: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{now}] {user_id} | {username} | {full_name} | {lang} | {text}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["lang"] = None
    context.user_data["waiting_operator"] = False

    await update.message.reply_text(
        "Выберите язык / Изберете език / Choose language",
        reply_markup=language_markup
    )


async def reply_to_client(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("Нет доступа.")
        return

    if len(context.args) < 2:
        await update.message.reply_text("Пример: /reply user_id текст")
        return

    try:
        target_user_id = int(context.args[0])
        reply_text = " ".join(context.args[1:])

        await context.bot.send_message(chat_id=target_user_id, text=reply_text)
        await update.message.reply_text("Ответ отправлен клиенту.")

    except ValueError:
        await update.message.reply_text("user_id должен быть числом.")
    except Exception as e:
        print("REPLY ERROR:", e)
        await update.message.reply_text("Не удалось отправить ответ клиенту.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    lang = context.user_data.get("lang")

    user = update.effective_user
    user_id = user.id
    username = user.username or "no_username"
    full_name = user.full_name or "no_name"

    log_message(user_id, username, full_name, lang, text)

    # Выбор языка
    if text == "Русский":
        context.user_data["lang"] = "ru"
        context.user_data["waiting_operator"] = False
        await update.message.reply_text("Вы выбрали русский.", reply_markup=markup_ru)
        return

    if text == "Български":
        context.user_data["lang"] = "bg"
        context.user_data["waiting_operator"] = False
        await update.message.reply_text("Избрахте български.", reply_markup=markup_bg)
        return

    if text == "English":
        context.user_data["lang"] = "en"
        context.user_data["waiting_operator"] = False
        await update.message.reply_text("You selected English.", reply_markup=markup_en)
        return

    # Смена языка
    if text in ["🌍 Сменить язык", "🌍 Смени език", "🌍 Change language"]:
        context.user_data["lang"] = None
        context.user_data["waiting_operator"] = False
        await update.message.reply_text(
            "Выберите язык / Изберете език / Choose language",
            reply_markup=language_markup
        )
        return

    # Если язык не выбран
    if not lang:
        await update.message.reply_text(
            "Сначала выберите язык / Първо изберете език / First choose a language",
            reply_markup=language_markup
        )
        return

    # Если бот ждёт сообщение для оператора
    if context.user_data.get("waiting_operator") is True:
        context.user_data["waiting_operator"] = False

        try:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"📩 Клиент\n"
                    f"{full_name} (@{username})\n"
                    f"ID: {user_id}\n"
                    f"Язык: {lang}\n"
                    f"Сообщение: {text}\n\n"
                    f"/reply {user_id} ваш_ответ"
                )
            )

            if lang == "bg":
                msg = "Съобщението е изпратено до оператор."
            elif lang == "en":
                msg = "Your message has been sent to the operator."
            else:
                msg = "Ваше сообщение отправлено оператору."

            await update.message.reply_text(msg, reply_markup=get_markup(lang))
            return

        except Exception as e:
            print("OPERATOR SEND ERROR:", e)

            if lang == "bg":
                msg = "Неуспешно изпращане до оператор."
            elif lang == "en":
                msg = "Failed to send message to the operator."
            else:
                msg = "Не удалось отправить сообщение оператору."

            await update.message.reply_text(msg, reply_markup=get_markup(lang))
            return

    # Кнопка "Оператор"
    if text in ["📞 Оператор", "📞 Operator"]:
        context.user_data["waiting_operator"] = True

        if lang == "bg":
            msg = "Напишете въпроса си в съобщение."
        elif lang == "en":
            msg = "Write your question in a message."
        else:
            msg = "Напишите ваш вопрос сообщением."

        await update.message.reply_text(msg, reply_markup=get_markup(lang))
        return

    # Автоматические ответы
    if lang == "ru":
        if text == "💧 Цена":
            await update.message.reply_text(
                f"Цена воды — {PRICE} за литр.",
                reply_markup=markup_ru
            )
            return

        if text == "⚙️ Как пользоваться":
            await update.message.reply_text(
                "1. Подставьте свою тару\n"
                "2. Выберите нужный объём или начните налив\n"
                "3. Оплатите\n"
                "4. Дождитесь окончания или нажмите СТОП\n"
                "5. Заберите воду",
                reply_markup=markup_ru
            )
            return

    if lang == "bg":
        if text == "💧 Цена":
            await update.message.reply_text(
                f"Цената е {PRICE} за литър.",
                reply_markup=markup_bg
            )
            return

        if text == "⚙️ Как се ползва":
            await update.message.reply_text(
                "1. Поставете вашия съд\n"
                "2. Изберете количество или започнете наливане\n"
                "3. Платете\n"
                "4. Изчакайте до края или натиснете СТОП\n"
                "5. Вземете водата",
                reply_markup=markup_bg
            )
            return

    if lang == "en":
        if text == "💧 Price":
            await update.message.reply_text(
                f"Price is {PRICE} per liter.",
                reply_markup=markup_en
            )
            return

        if text == "⚙️ How to use":
            await update.message.reply_text(
                "1. Place your container\n"
                "2. Select volume or start filling\n"
                "3. Pay\n"
                "4. Wait until finished or press STOP\n"
                "5. Take your water",
                reply_markup=markup_en
            )
            return

    # Всё остальное отправляем оператору
    try:
        await context.bot.send_message(
            chat_id=ADMIN_ID,
            text=(
                f"📩 Клиент\n"
                f"{full_name} (@{username})\n"
                f"ID: {user_id}\n"
                f"Язык: {lang}\n"
                f"Сообщение: {text}\n\n"
                f"/reply {user_id} ваш_ответ"
            )
        )

        if lang == "bg":
            msg = "Изпратено до оператор."
        elif lang == "en":
            msg = "Sent to operator."
        else:
            msg = "Отправлено оператору."

        await update.message.reply_text(msg, reply_markup=get_markup(lang))

    except Exception as e:
        print("GENERAL SEND ERROR:", e)

        if lang == "bg":
            msg = "Неуспешно изпращане до оператор."
        elif lang == "en":
            msg = "Failed to send message to the operator."
        else:
            msg = "Не удалось отправить сообщение оператору."

        await update.message.reply_text(msg, reply_markup=get_markup(lang))


def main():
    if not TELEGRAM_BOT_TOKEN:
        raise ValueError("Не найден TELEGRAM_BOT_TOKEN")

    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reply", reply_to_client))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Бот работает...")
    app.run_polling()


if __name__ == "__main__":
    main()