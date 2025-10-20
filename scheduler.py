import asyncio
from aiogram import Bot, Dispatcher, types, F   
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime
import logging

dp = Dispatcher()
scheduler = AsyncIOScheduler()
user_data = {}

@dp.message(Command("reminder"))
async def add_reminder(message: types.Message):
    await message.answer("Привет! Напиши что нужно напомнить")


@dp.message(F.text)
async def get_reminder(message: types.Message):
    user_id = message.from_user.id
    
    if user_id not in user_data:
        user_data[user_id] = {'step': 'text', 'text': message.text}
        await message.answer('Когда напомнить? (в формате ДД.ММ.ГГГГ)')
    elif user_data[user_id]['step'] == 'text':
        try:
            date = datetime.strptime(message.text, '%d.%m.%Y').date()
            user_data[user_id]['date'] = date
            user_data[user_id]['step'] = 'date'
            await message.answer('Во сколько напомнить? (в формате ЧЧ:ММ)')
        except ValueError:
            await message.answer('Неверный формат даты. Пример: 01.01.2025')
    elif user_data[user_id]['step'] == 'date':
        try:
            time = datetime.strptime(message.text, '%H:%M').time()
            reminder_time = datetime.combine(user_data[user_id]['date'], time)
            now = datetime.now()

            if reminder_time < now:
                await message.answer('Это время уже прошло, введите другое время')
                return
            user_data[user_id]['time'] = time
            user_data[user_id]['step'] = 'done'

            text = user_data[user_id]['text']
            scheduler.add_job(
                send_reminder,
                'date',
                run_date=reminder_time,
                args=[user_id, text]
                )
            await message.answer('Напоминание добавлено\n\n'
                f'Дата: {user_data[user_id]["date"].strftime("%d.%m.%Y")}\n'
                f'Время: {user_data[user_id]["time"].strftime("%H:%M")}\n'
                f'Текст: {user_data[user_id]["text"]}\n'
            )
            del user_data[user_id]
        except ValueError:
            await message.answer('Неверный формат времени. Пример: 12:30')
async def send_reminder(user_id, text):
    try:
        await bot.send_message(user_id, text)
    except Exception as e:
        logging.error(f"Ошибка отправки сообщения: {e}")
        
