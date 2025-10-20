from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton


kb_main = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📋 Мои задачи")],
        [
            KeyboardButton(text="➕ Добавить задачу"),KeyboardButton(text="📅 Расписание на день")

        ],
        [
            KeyboardButton(text="🎯 Фокус-сессия"),KeyboardButton(text="📊 Статистика")
        ]
        
    ],
    resize_keyboard=True
)

kb_focus = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Старт✅")],
        [KeyboardButton(text="Стоп❗️")],
        [KeyboardButton(text='Назад🔙')]

    ],
    resize_keyboard=True
)