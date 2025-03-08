import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile
from aiogram.filters import Command

TOKEN = "8094268456:AAF6zYaMbnEVrXT7dCnnKHa4A-qaquDYnhA"
OWNER_IDS = [1383822774, 1118338651]

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)

# Создаем объект бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Проверка владельца
def is_owner(message: types.Message) -> bool:
    return message.from_user.id in OWNER_IDS

# Основная клавиатура
keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Запрос")],
        [KeyboardButton(text="Отзыв")],
        [KeyboardButton(text='Обнуление')]
    ],
    resize_keyboard=True
)
async def track_action(user_id, action):
    await bot.send_message(1383822774, f"📍 Маруся нажала: {action}")

# Ожидание данных от пользователей
waiting_for_reference = {}
waiting_for_feedback = {}

@dp.message(Command("start"))
async def start_command(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "Старт")
    photo = FSInputFile("cupon.png")
    await message.answer_photo(photo, caption="Привет, вот купончик, пользуйся ❤️", reply_markup=keyboard)

@dp.message(lambda message: message.text == "Запрос")
async def request_handler(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "Запрос")
    keyboard1 = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Референс щас отправлю")],
            [KeyboardButton(text="Референса не будет, сам выбирай")],
            [KeyboardButton(text='Назад')],
            [KeyboardButton(text='Обнуление')]
        ],
        resize_keyboard=True
    )
    await message.answer("Выбери действие (хоть бы немного референса получить 🥺)", reply_markup=keyboard1)

@dp.message(lambda message: message.text == "Отзыв")
async def review_handler(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "Отзыв")
    user_id = message.from_user.id
    waiting_for_feedback[user_id] = {"step": "waiting_for_bouquet"}
    await message.answer("Пожалуйста, пришлите фото букета! Только фото (не селфи, просто фото букета)")

@dp.message(lambda message: message.text == "Назад")
async def back_to_start(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "Назад")
    await message.answer("Вы вернулись в главное меню.", reply_markup=keyboard)



@dp.message(lambda message: message.text == "Обнуление")
async def back_to_start(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "Обнуление")
    await message.answer("Вы вернулись в главное меню.", reply_markup=keyboard)
    waiting_for_reference.clear()
    waiting_for_feedback.clear()


@dp.message(lambda message: message.from_user.id in waiting_for_feedback)
async def process_feedback(message: types.Message):
    await track_action(message.from_user.id, "ожидай фотку")
    user_id = message.from_user.id
    step = waiting_for_feedback[user_id]["step"]

    if step == "waiting_for_bouquet" and message.photo:
        waiting_for_feedback[user_id]["bouquet_photo"] = message.photo[-1].file_id
        waiting_for_feedback[user_id]["step"] = "waiting_for_selfie"
        await message.answer("Теперь пришлите селфи с букетом.")
    elif step == "waiting_for_selfie" and message.photo:
        waiting_for_feedback[user_id]["selfie_photo"] = message.photo[-1].file_id
        waiting_for_feedback[user_id]["step"] = "waiting_for_rating"
        await message.answer("Теперь оцените букет от 1 до 13.")
    elif step == "waiting_for_rating" and message.text.isdigit():
        rating = int(message.text)
        if 1 <= rating <= 13:
            waiting_for_feedback[user_id]["rating"] = rating
            await send_feedback_to_owner(user_id)
        else:
            await message.answer("Оценка должна быть от 1 до 13. Попробуйте еще раз.")
    else:
        await message.answer("Пожалуйста, следуйте инструкциям и отправляйте фото или оценку.")

async def send_feedback_to_owner(user_id):
    rating = waiting_for_feedback[user_id]["rating"]
    text = f"🌸 Новый отзыв от Маруси:\n\nОценка: {rating}/13"
    await bot.send_photo(1383822774, waiting_for_feedback[user_id]["bouquet_photo"], caption="📷 Фото букета:")
    await bot.send_photo(1383822774, waiting_for_feedback[user_id]["selfie_photo"], caption="🤳 Селфи с букетом:")
    await bot.send_message(1383822774, text)
    del waiting_for_feedback[user_id]
    await bot.send_message(user_id, "Спасибо! Ваш отзыв отправлен.")

@dp.message(lambda message: message.text == "Референс щас отправлю")
async def reference_handler(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "Ща будет референс")
    waiting_for_reference[message.from_user.id] = True
    await message.answer("Отправь текст, фото или фото с подписью!")

@dp.message(lambda message: message.from_user.id in waiting_for_reference and waiting_for_reference[message.from_user.id])
async def handle_reference(message: types.Message):
    user_id = message.from_user.id
    if message.photo:
        photo = message.photo[-1].file_id
        caption = message.caption if message.caption else "Без подписи"
        await bot.send_photo(1383822774, photo, caption=f"📷 Референс от Маруси:\n\n{caption}")
    elif message.text:
        await bot.send_message(1383822774, f"📝 Текстовый референс от Маруси:\n\n{message.text}")
    del waiting_for_reference[user_id]
    await message.answer("Спасибо, ваш запрос принят.")

@dp.message(lambda message: message.text == "Референса не будет, сам выбирай")
async def no_reference_handler(message: types.Message):
    if not is_owner(message):
        return
    await track_action(message.from_user.id, "референса не будет")
    await message.answer("Ваш запрос принят, ожидайте 1-3 дня.")
    await bot.send_message(1383822774, "Новый заказ без референса, выбирай что захочешь (1-3 дня).")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())