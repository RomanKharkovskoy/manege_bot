import os
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, FSInputFile, ContentType
from aiogram.filters import Command
from aiogram import F
from datetime import datetime
from image_checker import check_image  
from database import create_tables, add_user, update_user_progress, get_user_progress, user_exists

API_TOKEN = 'API_TOKEN'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()

QUEST_IMAGES_FOLDER = 'quest_images'
IDEAL_IMAGES_FOLDER = 'ideal_images'

TEMP_FOLDER = 'temp'
os.makedirs(TEMP_FOLDER, exist_ok=True)

ROUNDS = {
    1: 7, 
    2: 7, 
    3: 6   
}

HINTS_FILE = 'hints.txt'

def load_hints():
    hints = {}
    if os.path.exists(HINTS_FILE):
        with open(HINTS_FILE, 'r', encoding='utf-8') as file:
            for line in file:
                key, hint = line.strip().split(': ', 1)
                hints[key] = hint
    return hints

hints = load_hints()

create_tables()

control_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='⬅️ Влево'), KeyboardButton(text='➡️ Вправо')],
        [KeyboardButton(text='💡 Подсказка')]
    ],
    resize_keyboard=True
)

start_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Начать')]
    ],
    resize_keyboard=True
)

@dp.message(Command('start'))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    await message.answer('''Привет! Рады видеть тебя на нашем квесте :)\n 
🔴 Напомним о правилах:\n
⚪️ Ваша задача - найти и сфотографировать зашифрованные фрагменты картин с выставки.\n
🔴 Сфотографируйте найденный фрагмент картины, отправьте в этот чат и переходите к поиску следующего фрагмента.\n
⚪️ Просим вас выполнять задания самостоятельно, а также соблюдать порядок в зале и не мешать посетителям выставки.\n
🔴 У вас есть 2 подсказки, используйте их с умом. \n
⚪️ Чтобы приступить к прохождению квеста, нажми на кнопку "Начать" (если кнопку не видно, то нажми на значок, который выглядит как то, что отправил тебе бот).\n 
🔴 Желаем удачи!\n
⚪️ Если остались вопросы или возникли проблемы пишите @RomanKharkovskoy \n
''', reply_markup=start_keyboard)
    await message.answer_photo(FSInputFile('keyboard_button.png', 'rb'))

@dp.message(lambda message: message.text == "Начать")
async def register_handler(message: types.Message):
    user_id = message.from_user.id
    if not user_exists(user_id):
        await message.answer("Введите своё имя:")
        add_user(user_id, "", "") 
        update_user_progress(user_id, 1, 1, 2, set())
    else:
        user_progress = get_user_progress(user_id)
        await message.answer(f"Вы уже зарегистрированы, {user_progress['name']} {user_progress['surname']}!",
                             reply_markup=control_keyboard)
        await show_image(message)

@dp.message(lambda message: get_user_progress(message.from_user.id)['name'] == "")
async def process_name(message: types.Message):
    user_id = message.from_user.id
    name = message.text
    update_user_progress(user_id, name=name)
    await message.answer("Введите свою фамилию:")

@dp.message(lambda message: get_user_progress(message.from_user.id)['surname'] == "" and get_user_progress(message.from_user.id)['name'] != "")
async def process_surname(message: types.Message):
    user_id = message.from_user.id
    surname = message.text
    update_user_progress(user_id, surname=surname)
    user_progress = get_user_progress(user_id)
    await message.answer(f"Регистрация успешна, {user_progress['name']} {surname}!", reply_markup=control_keyboard)
    await show_image(message)

async def show_image(message: types.Message):
    user_id = message.from_user.id
    user_progress = get_user_progress(user_id)
    current_round = user_progress['current_round']
    current_image = user_progress['current_image']
    image_path = os.path.join(QUEST_IMAGES_FOLDER, f'{current_round}_round', f'{current_image}.jpg')
    
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await message.answer_photo(photo)
    else:
        await message.answer("Картинка не найдена!")

@dp.message(F.text.in_(['⬅️ Влево', '➡️ Вправо', '💡 Подсказка']))
async def button_handler(message: types.Message):
    user_id = message.from_user.id
    user_progress = get_user_progress(user_id)
    current_round = user_progress['current_round']
    max_images = ROUNDS[current_round]

    current_image_index = user_progress['current_image']

    if message.text == '⬅️ Влево':
        if current_image_index == 1:
            user_progress['current_image'] = max_images
        else:
            user_progress['current_image'] = current_image_index - 1

    elif message.text == '➡️ Вправо':
        if current_image_index == max_images:
            user_progress['current_image'] = 1
        else:
            user_progress['current_image'] = current_image_index + 1

    elif message.text == '💡 Подсказка':
        current_image = user_progress['current_image']
        hint_key = f'{current_round}_{current_image}'
        if user_progress['hints_left'] > 0:
            user_progress['hints_left'] -= 1
            if hint_key in hints:
                hint = hints[hint_key]
                await message.answer(f"Подсказка: {hint}")
            else:
                await message.answer("Для этой картинки нет подсказки.")

            update_user_progress(user_id, current_round, current_image, user_progress['hints_left'], user_progress['completed_images'])
        else:
            await message.answer("У вас закончились подсказки.")

    update_user_progress(user_id, user_progress['current_round'], user_progress['current_image'],
                         user_progress['hints_left'], user_progress['completed_images'])

    await show_image(message)

@dp.message(F.content_type == ContentType.PHOTO)
async def process_image_upload(message: types.Message):
    user_id = message.from_user.id
    user_progress = get_user_progress(user_id)

    try:
        photo = message.photo[-1]

        file_info = await bot.get_file(photo.file_id)
        uploaded_image_path = os.path.join(TEMP_FOLDER, f'uploaded_{user_id}.jpg')

        await bot.download_file(file_info.file_path, uploaded_image_path)

        current_image_number = user_progress['current_image']

        round_folder = os.path.join(IDEAL_IMAGES_FOLDER, f'{user_progress["current_round"]}_round')
        ideal_image_path = os.path.join(round_folder, f'{current_image_number}.jpg')

        if not os.path.exists(ideal_image_path):
            await message.answer(f"Эталонное изображение {ideal_image_path} не найдено.")
            return

        if check_image(ideal_image_path, uploaded_image_path):
            user_progress['completed_images'].add(current_image_number)
            await message.answer("Картинка совпала с эталоном, молодец!")

            if len(user_progress['completed_images']) == ROUNDS[user_progress['current_round']]:
                user_progress['current_round'] += 1
                user_progress['current_image'] = 1
                user_progress['completed_images'] = set()

                if user_progress['current_round'] > len(ROUNDS):
                    end_time = datetime.now().isoformat()
                    update_user_progress(user_id, end_time=end_time)
                    await message.answer("Спасибо за участие в квесте! Победителей мы объявим немного позже. Ждем на прощальной вечеринке в 21:00!")
                    update_user_progress(user_id, current_round=user_progress['current_round'],
                                         completed_images=user_progress['completed_images'])
                    return

                await message.answer(f"Вы перешли на этап {user_progress['current_round']}!")
        else:
            await message.answer("Картинка не совпала с эталоном, попробуйте еще раз.")
    except Exception as e:
        await message.answer(f"Произошла ошибка при обработке изображения: {e}")

    finally:
        if os.path.exists(uploaded_image_path):
            os.remove(uploaded_image_path)

        update_user_progress(user_id, current_round=user_progress['current_round'],
                             current_image=user_progress['current_image'],
                             hints_left=user_progress['hints_left'],
                             completed_images=user_progress['completed_images'])


# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
