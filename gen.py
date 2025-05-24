from huggingface_hub import AsyncInferenceClient
from concurrent.futures import ThreadPoolExecutor
import google.generativeai as genai
import asyncio, config, db, random

genai.configure(api_key=config.genai_key)
model = genai.GenerativeModel('gemini-1.5-pro-002')
clienthf = AsyncInferenceClient(api_key=config.hf_key)

async def tr(message):
    modeltextid = await db.modelsdata(userid=False, modeltextid=True, affiliation="tr")
    result = await clienthf.translation(
        model=modeltextid,
        text=message
    )

    return result.translation_text

async def gentxt(userid, message):
    modelid = await db.modelusersettings(userid)
    modeltextid = await db.modelsdata(userid, modeltextid=True, affiliation="cc")
    if modelid == "gemini":
        past_messages = await db.checkuserhistory(userid)

        loop = asyncio.get_event_loop()
        chat = await loop.run_in_executor(None, lambda: model.start_chat(history=past_messages))
        response = await loop.run_in_executor(None, chat.send_message, message)

        await db.saveuserhistory(userid, message, response.text, "user", "model", modelid)

        return response.text
    else:
        past_messages = [{"role": "system", "content": "Speaks only the language the user speaks"}] + await db.checkuserhistory(userid) + [{"role": "user", "content": message}]

        completion = await clienthf.chat.completions.create(
            model=modeltextid,
            messages=past_messages,
            temperature=0.5,
            max_tokens=1024,
            top_p=0.7
        )

        await db.saveuserhistory(userid, message, completion.choices[0].message.content, "user", "assistant", modelid)

        return completion.choices[0].message.content

def save_image(image, path):
    image.save(path)

async def async_save_image(image, path):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor() as executor:
        await loop.run_in_executor(executor, save_image, image, path)

async def genimg(userid, message):
    modeltextid = await db.modelsdata(userid, modeltextid=True, affiliation="t2i")

    prompt = await tr(message)

    image = await clienthf.text_to_image(
        model=modeltextid,
        prompt=prompt,
        seed=random.randint(1, 2147483647)
    )

    await async_save_image(image, f"{userid}.png")

    return True
