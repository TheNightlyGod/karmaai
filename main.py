from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import logging, random, string, os, aiofiles, config, db, gen

logging.basicConfig(filename='app.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
app = Client("karmaai", api_hash=config.tg_api_hash, api_id=config.tg_api_id, bot_token=config.bot_token)

print("Started!")

async def banreson(client, message):
    await client.send_message(chat_id=message.chat.id,
                              text="Вы забанены в боте!",
                              reply_to_message_id=message.id)

async def responseempty(client, message):
    await client.send_message(chat_id=message.chat.id,
                              text="Нету запроса!",
                              reply_to_message_id=message.id)

async def agreeuseracc(client, message):
    keyboard = [[
        InlineKeyboardButton("Да", callback_data="createaccyes"),
        InlineKeyboardButton("Нет", callback_data="createaccno"),
    ]]
    await client.send_message(chat_id=message.chat.id,
                              text='Внимание!\n'
                                   'Нажимая на кнопку "Да", вы соглашаетесь на то, что мы имеем право сохранять, а также просматривать ваши генерации.\n'
                                   'Это является обязательным условием для использования бота.',
                              reply_to_message_id=message.id,
                              reply_markup=InlineKeyboardMarkup(keyboard))

@app.on_message(filters.command("start"))
async def start(client, message):
        if await db.checkuseracc(message.chat.id):
            if await db.bancheck(message.chat.id):
                await client.send_message(chat_id=message.chat.id,
                                          text=f"Добро пожаловать, {message.from_user.first_name}!\n"
                                               f"Я готова к работе!\n"
                                               f"Спросите у меня что либо и я отвечу.",
                                          reply_to_message_id=message.id)
            else:
                await banreson(client, message)
        else:
            await agreeuseracc(client, message)

@app.on_message(filters.command("help"))
async def helpp(client, message):
    if await db.checkuseracc(message.chat.id):
        if await db.bancheck(message.chat.id):
            await client.send_message(chat_id=message.chat.id,
                                      text="/help - Помощь\n"
                                           "/settings - Настройки AI\n"
                                           "/reset - Забыть разговор\n"
                                           "/gen - Сгенерировать текст\n"
                                           "/genimg - Сгенерировать изображение",
                                      reply_to_message_id=message.id)
        else:
            await banreson(client, message)
    else:
        await agreeuseracc(client, message)

@app.on_message(filters.command("reset"))
async def reset(client, message):
    if await db.checkuseracc(message.chat.id):
        if await db.bancheck(message.chat.id):
            logger.info(f"Пользователь {message.from_user.first_name}({message.from_user.id}) удалил разговор")
            await db.resetuserhistory(message.from_user.id)
            await client.send_message(chat_id=message.chat.id, text="Я забыла наш разговор.", reply_to_message_id=message.id)
        else:
            await banreson(client, message)
    else:
        await agreeuseracc(client, message)

@app.on_message(filters.command("gen"))
async def gentxt(client, message):
    if await db.bancheck(message.chat.id):
        if await db.checkuseracc(message.chat.id):
            command, *args = message.text.split(" ", 1)

            if not args:
                await responseempty(client, message)
                return

            modelname = await db.modelsdata(message.chat.id, affiliation="cc", modelname=True)
            time = await db.modelsdata(message.chat.id, affiliation="cc", time=True)

            messagebot = await client.send_message(chat_id=message.chat.id,
                                                   text="Подождите генерирую текст...\n"
                                                        f"Вы выбрали {modelname}\n"
                                                        f"Это может занять до {time}.",
                                                   reply_to_message_id=message.id)

            prompt = args[0]
            generated_text = await gen.gentxt(message.from_user.id, prompt)

            logger.info(f'Пользователь {message.from_user.first_name}({message.from_user.id}) запросил генерацию текста "{prompt}" у модели {modelname}.\n'
                        f'Текст генерации:\n'
                        f'{generated_text}')

            await messagebot.delete()
            await client.send_message(
                chat_id=message.chat.id,
                text=generated_text,
                reply_to_message_id=message.id
            )
        else:
            await banreson(client, message)
    else:
        await agreeuseracc(client, message)

@app.on_message(filters.command("genimg"))
async def genimg(client, message):
    if await db.checkuseracc(message.chat.id):
        if await db.bancheck(message.chat.id):
            command, *args = message.text.split(" ", 1)

            if not args:
                await responseempty(client, message)
                return

            modelname = await db.modelsdata(message.chat.id, modelname=True, affiliation="t2i")
            time = await db.modelsdata(message.chat.id, time=True, affiliation="t2i")

            textimg = args[0]
            messagebot = await client.send_message(chat_id=message.chat.id,
                                                   text="Подождите генерирую изображение...\n"
                                                        f"Вы выбрали {modelname}.\n"
                                                        f"Это может занять до {time}.",
                                                   reply_to_message_id=message.id)

            await gen.genimg(message.from_user.id, textimg)

            backupfile = ''.join(random.choice(string.ascii_letters) for _ in range(8)) + ".png"
            full_backup_path = os.path.join('logs', backupfile)
            source_file = f"{message.from_user.id}.png"
            async with aiofiles.open(source_file, 'rb') as src, aiofiles.open(full_backup_path, 'wb') as dst:
                await dst.write(await src.read())

            logger.info(f'Пользователь {message.from_user.first_name}({message.from_user.id}) запросил генерацию изображения "{textimg}" у модели {modelname}.\n'
                        f'Файл генерации: {full_backup_path}')

            await messagebot.delete()
            await client.send_photo(chat_id=message.chat.id,
                                    photo=f"{message.from_user.id}.png",
                                    caption=f"Промпт: `{textimg}`.\n"
                                            f"Модель: {modelname}.\n"
                                            f"@karmaai_bot",
                                    reply_to_message_id=message.id)
        else:
            await banreson(client, message)
    else:
        await agreeuseracc(client, message)

@app.on_message(filters.command("settings"))
async def settings(client, message):
    if await db.checkuseracc(message.chat.id):
        if await db.bancheck(message.chat.id):
            keyboard = [[
                InlineKeyboardButton("Настройка мозгов", callback_data="settingstextgen"),
                InlineKeyboardButton("Настройка рисовашки", callback_data="settingsimggen"),
                InlineKeyboardButton("Выход", callback_data="close")
            ]]

            await client.send_message(chat_id=message.chat.id,
                                      text="Настройки Карма AI",
                                      reply_to_message_id=message.id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))
        else:
            await banreson(client, message)
    else:
        await agreeuseracc(client, message)

@app.on_callback_query()
async def handle_callback(client, callback_query):
    if callback_query.data == "settingstextgen":
        keyboard = await db.modelsdata(userid=callback_query.message.chat.id, keyboard=True, affiliation="cc") + [[InlineKeyboardButton("Назад", callback_data="backsettings")]]

        await callback_query.message.edit_text("Настройка мозгов",
                                               reply_markup=InlineKeyboardMarkup(keyboard))
    elif callback_query.data in [id[0] for id in await db.modelsdata(userid=False, affiliation="cc", modelid=True)]:
        await db.modelusersettings(callback_query.message.chat.id, change=True, model=callback_query.data)
        modelsel = await db.modelsdata(callback_query.message.chat.id, modelname=True, affiliation="cc")
        keyboard = await db.modelsdata(userid=callback_query.message.chat.id, keyboard=True, affiliation="cc") + [[InlineKeyboardButton("Назад", callback_data="backsettings")]]

        await callback_query.message.edit_text("Настройка мозгов\n"
                                               "\n"
                                               f"Вы выбрали {modelsel}!",
                                               reply_markup=InlineKeyboardMarkup(keyboard))
    elif callback_query.data == "settingsimggen":
        keyboard = await db.modelsdata(userid=callback_query.message.chat.id, keyboard=True, affiliation="t2i") + [[InlineKeyboardButton("Назад", callback_data="backsettings")]]

        await callback_query.message.edit_text("Настройка рисовашки",
                                               reply_markup=InlineKeyboardMarkup(keyboard))
    elif callback_query.data in [id[0] for id in await db.modelsdata(userid=False, affiliation="t2i", modelid=True)]:
        await db.modelusersettings(callback_query.message.chat.id, t2i=True, change=True, model=callback_query.data)
        modelsel = await db.modelsdata(callback_query.message.chat.id, modelname=True, affiliation="t2i")
        keyboard = await db.modelsdata(userid=callback_query.message.chat.id, keyboard=True, affiliation="t2i") + [[InlineKeyboardButton("Назад", callback_data="backsettings")]]

        await callback_query.message.edit_text("Настройка рисовашки\n"
                                               "\n"
                                               f"Вы выбрали {modelsel}!",
                                               reply_markup=InlineKeyboardMarkup(keyboard))
    elif callback_query.data == "backsettings":
        keyboard = [[
            InlineKeyboardButton("Настройка мозгов", callback_data="settingstextgen"),
            InlineKeyboardButton("Настройка рисовашки", callback_data="settingsimggen"),
            InlineKeyboardButton("Выход", callback_data="close")
        ]]

        await callback_query.message.edit_text(text="Настройки Карма AI",
                                               reply_markup=InlineKeyboardMarkup(keyboard))
    elif callback_query.data == "close":
        await callback_query.message.delete()
    elif callback_query.data == "createaccyes":
        await db.adduseracc(callback_query.message.chat.id)
        await callback_query.message.edit_text(text=f"Добро пожаловать, {callback_query.message.chat.first_name}!\n"
                                                    "Я готова к работе!\n"
                                                    "Спросите у меня что либо и я отвечу.")
        await client.send_message(chat_id=callback_query.message.chat.id,
                                  text="/help - Помощь\n"
                                       "/settings - Настройки AI\n"
                                       "/reset - Забыть разговор\n"
                                       "/gen - Сгенерировать текст\n"
                                       "/genimg - Сгенерировать изображение",
                                  reply_to_message_id=callback_query.message.id)
    elif callback_query.data == "createaccno":
        await callback_query.message.edit_text(text="Отказ получен!\n"
                                                    "Доступ к боту невозможен.")
    else:
        await callback_query.answer("Неизвестная кнопка")

@app.on_message()
async def gentxtonm(client, message):
    if await db.bancheck(message.chat.id):
        if await db.checkuseracc(message.chat.id):
            modelname = await db.modelsdata(message.chat.id, affiliation="cc", modelname=True)
            time = await db.modelsdata(message.chat.id, affiliation="cc", time=True)

            messagebot = await client.send_message(chat_id=message.chat.id,
                                                   text="Подождите генерирую текст...\n"
                                                        f"Вы выбрали {modelname}\n"
                                                        f"Это может занять до {time}.",
                                                   reply_to_message_id=message.id)

            generated_text = await gen.gentxt(message.from_user.id, message.text)

            logger.info(
                f'Пользователь {message.from_user.first_name}({message.from_user.id}) запросил генерацию текста "{message.text}" у модели {modelname}.\n'
                f'Текст генерации:\n'
                f'{generated_text}')

            await messagebot.delete()
            await client.send_message(
                chat_id=message.chat.id,
                text=generated_text,
                reply_to_message_id=message.id
            )
        else:
            await agreeuseracc(client, message)
    else:
        await banreson(client, message)

app.run()