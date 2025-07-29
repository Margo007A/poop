
import logging
import json
import random
import asyncio
from datetime import datetime, timedelta
import pytz

from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes,
)

# === КОНФИГ ===
BOT_TOKEN = "8276571944:AAF3ypIPxV-IPJYW-Rr6PiEql8vUONzEGeE"
GROUP_CHAT_ID = -1002444770684
THREAD_ID = 2
REMINDER_HOUR = 20
REMINDER_MINUTE = 50
USER_DATA_FILE = "subscribers.json"

MSK = pytz.timezone("Europe/Moscow")

logging.basicConfig(level=logging.INFO)

def load_users():
    try:
        with open(USER_DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_users(user_ids):
    with open(USER_DATA_FILE, "w") as f:
        json.dump(user_ids, f)

subscribers = load_users()

JOKES = [
    "💌 Привет любимый. Пора делать скрины — актив сам себя не заскринит!",
    "📸 Скрин или позор. Ты знаешь, что делать!",
    "😎 Легенды делают скрины в 20:50. Не подведи легенду!",
    "🥵 Пора скринить. Актив жаждет внимания!",
    "👀 Я не шпион, но я знаю, что ты забыл про актив. Исправься!",
    "🫠 У кого-то уже 0 очков, а ты всё ещё не скринишь?",
    "😴 Скрины не сделаются сами. Просыпайся!",
    "🎯 Один скрин — и ты ближе к победе.",
    "🧠 Умный делает скрины вовремя. А ты умный, да? 😉",
    "🥷 Скрини быстро и тихо. Как ниндзя активности.",
] + [f"💡 Вариант шутки #{i+11}: не забудь про актив!" for i in range(90)]

async def is_user_in_group(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=GROUP_CHAT_ID, user_id=user_id)
        return member.status in [ChatMember.MEMBER, ChatMember.OWNER, ChatMember.ADMINISTRATOR]
    except:
        return False

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    username = f"@{user.username}" if user.username else user.full_name

    if update.effective_chat.type != "private":
        return

    if not await is_user_in_group(context.bot, user_id):
        await update.message.reply_text("❌ Только участники группы могут подписаться на напоминания.")
        return

    if user_id not in subscribers:
        subscribers.append(user_id)
        save_users(subscribers)
        await update.message.reply_text("✅ Ты подписан на напоминания о скринах в 20:50 по МСК!")
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            message_thread_id=THREAD_ID,
            text=f"✅ {username} нажал старт и будет получать напоминание в 20:50 по МСК."
        )
    else:
        await update.message.reply_text("😎 Ты уже подписан. Я напомню тебе обязательно!")

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in subscribers:
        subscribers.remove(user_id)
        save_users(subscribers)
        await update.message.reply_text("❌ Ты отписался от напоминаний.")
    else:
        await update.message.reply_text("Ты и так не подписан 😅")

async def list_subs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "📋 Подписаны на напоминания:
"
    if not subscribers:
        text += "👻 Никого нет... одни призраки. Кто будет скринить актив?!"
    else:
        for uid in subscribers:
            text += f"• [{uid}](tg://user?id={uid})\n"
    await update.message.reply_text(text, parse_mode="Markdown")

async def reminder_loop(bot):
    while True:
        now = datetime.now(MSK)
        target = now.replace(hour=REMINDER_HOUR, minute=REMINDER_MINUTE, second=0, microsecond=0)
        if now >= target:
            target += timedelta(days=1)
        wait_seconds = (target - now).total_seconds()
        await asyncio.sleep(wait_seconds)
        try:
            await bot.send_message(
                chat_id=GROUP_CHAT_ID,
                message_thread_id=THREAD_ID,
                text="⏰ Все участники группы получили уведомление о скринах актива в 20:50 по МСК!"
            )
        except Exception as e:
            logging.warning(f"Ошибка при отправке в тему: {e}")
        for user_id in subscribers:
            try:
                msg = random.choice(JOKES)
                await bot.send_message(chat_id=user_id, text=msg)
            except Exception as e:
                logging.warning(f"Ошибка отправки пользователю {user_id}: {e}")

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stop", stop))
    app.add_handler(CommandHandler("list", list_subs))
    asyncio.create_task(reminder_loop(app.bot))
    print("✅ Бот запущен и ждёт 20:50 по МСК...")
    await app.run_polling()

if __name__ == "__main__":
    asyncio.run(main())
