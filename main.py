from fastapi import FastAPI, Request
from aiogram import types
from bot import dp

app = FastAPI()

@app.post("/webhook")
async def telegram_webhook(req: Request):
    body = await req.json()
    update = types.Update(**body)
    await dp.process_update(update)
    return {"ok": True}