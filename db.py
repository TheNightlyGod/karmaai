from pyrogram.types import InlineKeyboardButton
import aiosqlite

async def modelsdata(userid, affiliation, modelid=False, modeltextid=False, modelname=False, time=False, keyboard=False):
    async with aiosqlite.connect('karmaai.db') as db:
        if affiliation == "t2i":
            if keyboard:
                async with db.execute('SELECT modelname FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result1 = await cursor.fetchall()
                async with db.execute('SELECT modelid FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result2 = await cursor.fetchall()
                buttons = []
                for text in result1:
                    callback_data = next((id for id, button_text in zip(result2, result1) if button_text == text), None)
                    if callback_data:
                        buttons.append([InlineKeyboardButton(text=text[0] if await modelusersettings(userid, t2i=True) != callback_data[0] else "✅" + text[0], callback_data=callback_data[0])])
                return buttons
            elif modelid:
                async with db.execute('SELECT modelid FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result = await cursor.fetchall()
                    return result
            model = await modelusersettings(userid, t2i=True)
            if modeltextid:
                async with db.execute('SELECT modeltextid FROM Models WHERE modelid = ?', (model,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
            elif modelname:
                async with db.execute('SELECT modelname FROM Models WHERE modelid = ?', (model,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
            elif time:
                async with db.execute('SELECT time FROM Models WHERE modelid = ?', (model,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
        elif affiliation == "cc":
            if keyboard:
                async with db.execute('SELECT modelname FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result1 = await cursor.fetchall()
                async with db.execute('SELECT modelid FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result2 = await cursor.fetchall()
                buttons = []
                for text in result1:
                    callback_data = next((id for id, button_text in zip(result2, result1) if button_text == text), None)
                    if callback_data:
                        buttons.append([InlineKeyboardButton(text=text[0] if await modelusersettings(userid) != callback_data[0] else "✅" + text[0], callback_data=callback_data[0])])
                return buttons
            elif modelid:
                async with db.execute('SELECT modelid FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result = await cursor.fetchall()
                    return result
            model = await modelusersettings(userid)
            if modeltextid:
                async with db.execute('SELECT modeltextid FROM Models WHERE modelid = ?', (model,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
            elif modelname:
                async with db.execute('SELECT modelname FROM Models WHERE modelid = ?', (model,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
            elif time:
                async with db.execute('SELECT time FROM Models WHERE modelid = ?', (model,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
        elif affiliation == "tr":
            if modeltextid:
                async with db.execute('SELECT modeltextid FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
            elif modelname:
                async with db.execute('SELECT modelname FROM Models WHERE affiliation = ?', (affiliation,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]

async def checkuseracc(userid):
    async with aiosqlite.connect('karmaai.db') as db:
        async with db.execute('SELECT userid FROM UserData WHERE userid = ?', (userid,)) as cursor:
            result = await cursor.fetchall()
            if result:
                return True
            else:
                return False

async def adduseracc(userid):
    async with aiosqlite.connect('karmaai.db') as db:
        await db.execute('INSERT INTO UserData (userid) VALUES (?)', (userid,))
        await db.commit()

async def modelusersettings(userid, t2i=False, model=False, change=False):
    async with aiosqlite.connect('karmaai.db') as db:
        if change:
            if t2i:
                await db.execute('UPDATE UserData SET modelt2i = ? WHERE userid = ?', (model, userid))
                await db.commit()
            elif not t2i:
                await db.execute('UPDATE UserData SET modelcc = ? WHERE userid = ?', (model, userid))
                await db.commit()
        elif not change:
            if t2i:
                async with db.execute('SELECT modelt2i FROM UserData WHERE userid = ?', (userid,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]
            elif not t2i:
                async with db.execute('SELECT modelcc FROM UserData WHERE userid = ?', (userid,)) as cursor:
                    result = await cursor.fetchall()
                    return result[0][0]

async def checkuserhistory(userid):
    modelsel = await modelusersettings(userid)
    async with aiosqlite.connect('karmaai.db') as db:
        if modelsel == "gemini":
            async with db.execute('SELECT * FROM UserMessages WHERE userid = ?', (userid,)) as cursor:
                messages = await cursor.fetchall()
                return [
                    {
                        "parts": {
                            "text": msg[1]
                        },
                        "role": msg[2]
                    }
                    for msg in messages]
        else:
            async with db.execute('SELECT * FROM UserMessages WHERE userid = ? AND model = ?', (userid, modelsel)) as cursor:
                messages = await cursor.fetchall()
                return [{ "role": msg[2], "content": msg[1]} for msg in messages]

async def saveuserhistory(userid, message, assistant_response, roleu, rolea, model):
    async with aiosqlite.connect('karmaai.db') as db:
        await db.execute('INSERT INTO UserMessages (userid, message, role, model) VALUES (?, ?, ?, ?)', (userid, message, roleu, model))
        await db.execute('INSERT INTO UserMessages (userid, message, role, model) VALUES (?, ?, ?, ?)', (userid, assistant_response, rolea, model))
        await db.commit()

async def resetuserhistory(userid):
    modelsel = await modelusersettings(userid)
    async with aiosqlite.connect('karmaai.db') as db:
        await db.execute('DELETE FROM UserMessages WHERE userid = ? AND model = ?', (userid, modelsel))
        await db.commit()

async def bancheck(userid):
    async with aiosqlite.connect('karmaai.db') as db:
        async with db.execute("SELECT ban FROM UserData WHERE userid = ?", (userid,)) as cursor:
            result = await cursor.fetchall()
            if not result[0][0] == 1:
                return True
            else:
                return False
