import asyncio
import logging
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from database import reminder, init_db
from kb import kb_main, kb_focus
from aiogram.types import BotCommand
from database import init_focus, focus
from database import get_focus_stats

logging.basicConfig(level=logging.INFO)

API_TOKEN = '8095807426:AAEaZh6Sg6fFaFf_xmU9RuNp6Q-vc37CmBg'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
scheduler = AsyncIOScheduler()

user_data = {}
user_start_time = {}
focus_sessions = {}

async def set_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота"),
        BotCommand(command="info", description="Информация о боте"),
    ]
    await bot.set_my_commands(commands)
    

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Я бот, который может запланировать задачи для вас.", reply_markup=kb_main)

@router.message(Command("info"))
async def cmd_info(message: types.Message):
    await message.answer("Я бот, который может запланировать задачи для вас.")



@router.message(F.text == "➕ Добавить задачу")
async def add_reminder(message: types.Message):
    await message.answer("Что нужно напомнить?")
    user_data[message.from_user.id] = {"step": "text"}


@router.message(F.text == "📋 Мои задачи")
async def view_reminders(message: types.Message):
    await message.answer("Введите дату (в формате ГГГГ.ММ.ДД), чтобы посмотреть задачи.")
    user_data[message.from_user.id] = {"step": "check_tasks"}



@router.message(F.text == "📅 Расписание на день")
async def daily_schedule(message: types.Message):
    await message.answer("Введите дату (в формате ГГГГ.ММ.ДД), чтобы увидеть расписание.")
    user_data[message.from_user.id] = {"step": "schedule"}

@router.message(F.text == "📊 Статистика")
async def statistics(message: types.Message):
    try:
        with sqlite3.connect("reminders.db") as conn:
            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM reminders WHERE user_id = ?", (message.from_user.id,))
            count = cur.fetchone()[0]

 
        total_sessions, total_time, avg_duration = get_focus_stats(message.from_user.id)

 
        text = f"📊 Ваша статистика:\n\n- Всего задач: {count}\n\n"

        if total_sessions == 0:
            text += "😴 У вас пока нет фокус-сессий."
        else:
            total_hours, total_minutes = divmod(int(total_time.total_seconds()) // 60, 60)
            avg_minutes = int(avg_duration.total_seconds() // 60)

            text += (
                "🎯 Фокус-сессии:\n\n"
                f"- Среднее время фокуса: {avg_minutes} мин\n"
                f"- Всего проведено: {total_sessions} сессий\n"
                f"- Суммарное время: {total_hours} ч {total_minutes} мин\n"
            )

        await message.answer(text, reply_markup=kb_main)

    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    




@router.message(F.text == "🎯 Фокус-сессия")
async def focus_session(message: types.Message):
    await message.answer("🎯 Фокус-сессия", reply_markup=kb_focus)


@router.message(F.text == "Старт✅")
async def start_focus_session(message: types.Message):
    user_id = message.from_user.id
    user_start_time[user_id] = datetime.now()
    await message.answer("⏱️ Таймер запущен! Нажми Стоп❗️ чтобы завершить.", reply_markup=kb_focus)


@router.message(F.text == "Стоп❗️")
async def stop_focus_session(message: types.Message):
    user_id = message.from_user.id
    start = user_start_time.get(user_id)

    if not start:
        await message.answer("❗️ Таймер не запущен. Нажми Старт✅.", reply_markup=kb_focus)
        return

    end = datetime.now()
    duration = end - start
    hours, remainder = divmod(int(duration.total_seconds()), 3600)
    minutes, seconds = divmod(remainder, 60)


    save_focus_session(user_id, start, end)

    del user_start_time[user_id]

    await message.answer(
        f"✅ Сессия завершена!\n⏰ Продолжительность: {hours}ч {minutes}м {seconds}с",
        reply_markup=kb_main
    )

@router.message(F.text == "Назад🔙")
async def back_to_main(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data:
        del user_data[user_id]
    await message.answer("Главное меню", reply_markup=kb_main)
        


    

@router.message()
async def universal_handler(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data:
        return
    step = user_data[user_id]["step"]

    if step == "text":
        user_data[user_id]["text"] = message.text
        user_data[user_id]["step"] = "date"
        await message.answer("Когда напомнить? (в формате ГГГГ.ММ.ДД)")
        return

    elif step == "date":
        try:
            date = datetime.strptime(message.text, "%Y.%m.%d").date()
            user_data[user_id]["date"] = date
            user_data[user_id]["step"] = "time"
            await message.answer("Во сколько напомнить? (в формате ЧЧ:ММ)")
        except ValueError:
            await message.answer("❌ Неверный формат даты. Пример: 2025.10.12")
        return

    elif step == "time":
        try:
            time = datetime.strptime(message.text, "%H:%M").time()
            reminder_time = datetime.combine(user_data[user_id]["date"], time)
            if reminder_time < datetime.now():
                await message.answer("⏰ Это время уже прошло, введите другое.")
                return
            text = user_data[user_id]["text"]
            date_str = user_data[user_id]["date"].strftime("%Y-%m-%d")
            time_str = time.strftime("%H:%M")
            reminder(user_id, text, date_str, time_str)
            scheduler.add_job(send_reminder, 'date', run_date=reminder_time, args=[user_id, text])
            await message.answer(
                "✅ Напоминание добавлено:\n\n"
                f"📅 Дата: {date_str}\n"
                f"⏰ Время: {time_str}\n"
                f"📝 Текст: {text}",
                reply_markup=kb_main
            )
            del user_data[user_id]
        except ValueError:
            await message.answer("❌ Неверный формат времени. Пример: 12:30")
        return

    elif step == "check_tasks":
        try:
            date = datetime.strptime(message.text, "%Y.%m.%d").date()
            with sqlite3.connect("reminders.db") as conn:
                cur = conn.cursor()
                cur.execute("SELECT text, time FROM reminders WHERE date = ?", (date.strftime("%Y-%m-%d"),))
                reminders = cur.fetchall()
            if reminders:
                msg = "\n\n".join([f"⏰ {t} — {txt}" for txt, t in reminders])
                await message.answer(f"📅 Напоминания на {date}:\n\n{msg}")
            else:
                await message.answer("❌ Нет напоминаний на эту дату.")
        except ValueError:
            await message.answer("❌ Неверный формат даты. Пример: 2025.10.12")
        del user_data[user_id]
        return

    elif step == "schedule":
        try:
            date = datetime.strptime(message.text, "%Y.%m.%d").date()
            with sqlite3.connect("reminders.db") as conn:
                cur = conn.cursor()
                cur.execute("SELECT time, text FROM reminders WHERE date = ?", (date.strftime("%Y-%m-%d"),))
                reminders = cur.fetchall()
            if reminders:
                msg = "\n".join([f"{t} — {txt}" for t, txt in reminders])
                await message.answer(f"📋 Расписание на {date}:\n\n{msg}")
            else:
                await message.answer("Нет запланированных задач.")
        except ValueError:
            await message.answer("Неверный формат даты. Пример: 2025.10.12")
        del user_data[user_id]
        return



async def send_reminder(user_id, text):
    try:
        await bot.send_message(user_id, f"🔔 Напоминание:\n{text}")
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения: {e}")

async def main():
    init_db()
    init_focus()
    scheduler.start()
    dp.include_router(router)
    await set_commands()
    print("Бот запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())