import random
from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from dispatcher import dp, bot
from datetime import datetime
from datetime import timedelta
from bot import BotDB
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
import asyncio

Pay_button = InlineKeyboardButton(text="Платно", callback_data="Платно")
Free_button = InlineKeyboardButton(text="Безкоштовно", callback_data="Безкоштовно")
inline_answer1 = InlineKeyboardMarkup().add(Pay_button).add(Free_button)
About_button = KeyboardButton(text="Моя інформація")
Next_pay_button = KeyboardButton(text="Наступна плата")
In_gym_button = KeyboardButton(text="Я в залі")
Out_gym_button = KeyboardButton(text="Я пішов з залу")
All_in_gym_button = KeyboardButton(text="Скільки людей в залі?")
in_gym_check = KeyboardButton(text="Так", callback_data="Я все ще в залі")
main_reply = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(In_gym_button).add(About_button).add(Next_pay_button).add(All_in_gym_button)
in_gym_reply = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(Out_gym_button)
in_gym_check_markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(in_gym_check).add(Out_gym_button)

class Test(StatesGroup):
    Question1 = State()
    Question2 = State()

@dp.message_handler(commands="start")
async def start(message: types.Message):
    if(not BotDB.user_exists(message.from_user.id)):
        BotDB.add_user(message.from_user.id, message.from_user.username)
        BotDB.update_info(message.from_user.id, 'in_gym', "FALSE")
        await message.bot.send_message(message.from_user.id, "Вітаю👋\nЯ бот спортзалу 11 гуртожитку!\nДля початку потрібно пройти реєстрацію", parse_mode="html")
        await message.bot.send_message(message.from_user.id, "Напишіть ваше Ім'я та Прізвище:")
        await Test.Question1.set()
    else:
        pass
    # await message.bot.send_message(message.from_user.id, "Напишіть ваш гуртожиток та кімнату:")
    # await Test.Question2.set()
    # await message.bot.send_message(message.from_user.id, "У якій форму ви хочете платити за зал?\n<b>Платно - 100грн на місяць<\b>\n<b>Безкоштовно - 1 раз на місяць прибирати зал<\b>", parse_mode="html")

@dp.message_handler(state=Test.Question1)
async def answer_question(message: types.Message, state: FSMContext):
    answer = message.text
    BotDB.update_info(message.from_user.id, 'name_surname', answer)
    data = BotDB.get_google_list(0)
    status = BotDB.google_update_data(0, len(data)+1, 1, answer)
    status = BotDB.google_update_data(0, len(data)+1, 3, message.from_user.username)
    await state.update_data(answer=(len(data)+1))
    await message.bot.send_message(message.from_user.id, "Напишіть ваш гуртожиток та кімнату:")
    await Test.Question2.set()

@dp.message_handler(state=Test.Question2)
async def answer_question(message: types.Message, state: FSMContext):
    row = await state.get_data()
    row_data = row.get("answer")
    await state.update_data(answer=row_data)
    print("Row: " + str(row_data))
    answer = message.text
    BotDB.update_info(message.from_user.id, 'adres', answer)
    status = BotDB.google_update_data(0, row_data, 2, answer)
    await message.bot.send_message(message.from_user.id,
                                   "У якій форму ви хочете платити за зал?\n<b>Платно - 100грн на місяць</b>\n<b>Безкоштовно - 1 раз на місяць прибирати зал</b>",
                                   parse_mode="html", reply_markup=inline_answer1)
    await Test.Question2.set()


@dp.callback_query_handler(state=Test.Question2)
async def check_button(call: types.CallbackQuery, state: FSMContext):
    row = await state.get_data()
    row_data = row.get("answer")
    await state.finish()
    if call.data == "Платно":
        BotDB.update_info(call.from_user.id, "payment_type", "True")
        BotDB.update_info(call.from_user.id, 'next_pay', 31)
        end_date = datetime.now() + timedelta(days=31)
        status = BotDB.google_update_data(0, row_data, 4, datetime.strftime(end_date, "%d.%m.20%y"))
        await call.bot.send_message(call.from_user.id, "Дякую, реєстрацію завершено", reply_markup=main_reply)
    elif call.data == "Безкоштовно":
        BotDB.update_info(call.from_user.id, "payment_type", "False")
        status = BotDB.google_update_data(0, row_data, 4, "Безкоштовно")
        await call.bot.send_message(call.from_user.id, "Дякую, реєстрацію завершено", reply_markup=main_reply)

async def send_advice():
    users = BotDB.get_users()
    for user_id in users:
        next_pay = int(BotDB.get_next_pay(user_id[0]))
        next_pay -= 1
        BotDB.update_info(user_id[0], "next_pay", next_pay)
        if next_pay == 7:
            await bot.send_message(user_id[0], "Через 7 днів потрібно оплатити спортзал")
        elif next_pay == 1:
            await bot.send_message(user_id[0], "Завтра потрібно оплатити спортзал")
        else:
            pass
async def scheduler():
    count = 0
    while True:
        if count == 0:
            now = datetime.now()
            delay = (0 - int(now.strftime("%H")))*3600 + (0-int(now.strftime("%M")))*60 - int(now.strftime("%S"))
            count += 1
            if delay < 0:
                delay = 86400 + delay
            print(delay)
        else:
            delay = 86400 - minus
        await asyncio.sleep(delay)
        time = datetime.now()
        await send_advice()
        minus = int(datetime.now().strftime("%S")) - int(time.strftime("%S"))

async def on_startup(dp):
    # pass
    asyncio.create_task(scheduler())

@dp.message_handler()
async def start(message: types.Message):
    # spread1_values = BotDB.get_google_list(0)
    # print(spread1_values)
    # status = BotDB.google_update_data(0, 2,1, "Hello world!")
    # print(status)d
    if message.text == "Моя інформація":
        in_gym = BotDB.get_custom_info(message.from_user.id, 'in_gym')[0][0]
        if in_gym == "TRUE":
            await message.bot.send_message(message.from_user.id, "Інформацію можна отримати після виходу з залу!\nКнопка для виходу знизу",
                                           reply_markup=in_gym_reply)
        else:
            data = BotDB.get_user_info(message.from_user.id)
            if data[2] == "True":
                payment = "Платно"
            else:
                payment = "Безкоштовно"
            stats = BotDB.get_in_gym_info(message.from_user.id)
            enter_counter = int(len(stats) / 2)
            if len(stats) == 0:
                time_gym = "0:00:00"
            for i in range(int(len(stats))):
                if i == 0:
                    time_gym = datetime.strptime(stats[i + 1][1].split(" ")[1], '%H:%M:%S') - datetime.strptime(
                        stats[i][1].split(" ")[1], '%H:%M:%S')
                    # print(datetime.strptime(stats[i + 1][1].split(" ")[0], '%y-%m-%d') - datetime.strptime(
                    #     stats[i][1].split(" ")[0], '%y-%m-%d'))
                elif i % 2 == 0:
                    time_gym = time_gym + (datetime.strptime(stats[i + 1][1].split(" ")[1], '%H:%M:%S') - datetime.strptime(
                        stats[i][1].split(" ")[1], '%H:%M:%S'))
            current_level = BotDB.get_custom_info(message.from_user.id, "level")[0][0]
            next_level_time = (int(current_level)*int(current_level)) - int(str(time_gym).split(":")[0])
            await message.bot.send_message(message.from_user.id, f"Ваше ім'я - {str(data[0])}\nВаша адреса - {str(data[1])}\nТип оплати - {str(payment)}\n<b>Всього тренувань: </b>{str(enter_counter)}\n<b>Часу проведено в залі: </b>{str(time_gym)}\n<b>Ваш рівень: </b>{current_level}\n<b>До наступного рівня</b>: {next_level_time} години", reply_markup=main_reply)
    elif message.text == "Наступна плата":
        next_pay = BotDB.get_next_pay(message.from_user.id)
        await message.bot.send_message(message.from_user.id, f"Ваша наступна оплата через <b>{str(next_pay)}</b> днів", parse_mode="html", reply_markup=main_reply)
    elif message.text == "Я в залі":
        in_gym = BotDB.get_custom_info(message.from_user.id, 'in_gym')[0][0]
        if in_gym == "TRUE":
            await message.bot.send_message(message.from_user.id, "Ти уже в залі!\nКнопка для виходу знизу", reply_markup=in_gym_reply)
        else:
            await message.bot.send_message(message.from_user.id, "Гарного тренування", reply_markup=in_gym_reply)
            await message.bot.send_sticker(message.from_user.id, "CAACAgIAAxkBAAELqhNl7xcY_Y-tSF-6n8Nw7Th6uZkn5wACugADTptkArbrc3oLzTyHNAQ")
            BotDB.get_in_gym(message.from_user.id, "Ввійшов")
            BotDB.update_info(message.from_user.id, 'in_gym', "TRUE")
            await asyncio.sleep(10800)
            status = BotDB.get_custom_info(message.from_user.id, "in_gym")[0][0]
            if status == "TRUE":
                await message.bot.send_message(message.from_user.id, "Ти все ще в залі?", reply_markup=in_gym_check_markup)
    elif message.text == "Я пішов з залу":
        in_gym = BotDB.get_custom_info(message.from_user.id, 'in_gym')[0][0]
        if in_gym == "FALSE":
            await message.bot.send_message(message.from_user.id, "Ти і так не в залі!", reply_markup=main_reply)
        else:
            await message.bot.send_message(message.from_user.id, "Класно напампився", reply_markup=main_reply)
            await message.bot.send_sticker(message.from_user.id,
                                           "CAACAgIAAxkBAAELqhFl7xbDwcFou5p0NkreSu9bj8zlDwACZBQAAjzxyEuwdKvRZVMPlzQE")
            BotDB.get_in_gym(message.from_user.id, "Вийшов")
            BotDB.update_info(message.from_user.id, 'in_gym', "FALSE")
            stats = BotDB.get_in_gym_info(message.from_user.id)
            for i in range(int(len(stats))):
                if i == 0:
                    time_gym = datetime.strptime(stats[i + 1][1].split(" ")[1], '%H:%M:%S') - datetime.strptime(
                        stats[i][1].split(" ")[1], '%H:%M:%S')
                    # print(datetime.strptime(stats[i + 1][1].split(" ")[0], '%y-%m-%d') - datetime.strptime(
                    #     stats[i][1].split(" ")[0], '%y-%m-%d'))
                elif i % 2 == 0:
                    time_gym = time_gym + (datetime.strptime(stats[i + 1][1].split(" ")[1], '%H:%M:%S') - datetime.strptime(
                        stats[i][1].split(" ")[1], '%H:%M:%S'))
            current_level = BotDB.get_custom_info(message.from_user.id, "level")[0][0]
            hours_gym = int(str(time_gym).split(":")[0])
            if hours_gym >= (int(current_level)*int(current_level)):
                new_level = current_level + 1
                await message.bot.send_message(message.from_user.id, f"Вітаю, ти провів у залі: <b>{str(hours_gym)}</b> годин!\nТепер у тебе <b>{str(new_level)}</b> рівень🥳", parse_mode="html", reply_markup=main_reply)
                BotDB.update_info(message.from_user.id, "level", new_level)
    elif message.text == "Так":
        await message.bot.send_message(message.from_user.id, "Круто!", reply_markup=in_gym_reply)
    elif message.text == "Скільки людей в залі?":
        in_gym = BotDB.get_all_in_gym()
        counter = 0
        for i in in_gym:
            if i[0] == "TRUE":
                counter += 1
        await message.bot.send_message(message.from_user.id, f"В залі зараз <b>{counter}</b> людей", parse_mode="html", reply_markup=main_reply)

