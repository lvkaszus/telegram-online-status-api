import os
import yaml
import json
import asyncio
from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
from telethon.tl.types import UserStatusOnline, UserStatusOffline
from datetime import datetime, timezone, timedelta
from fastapi.responses import JSONResponse
import uvicorn
import aiofiles

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config/config.yml')
CACHE_PATH = os.path.join(BASE_DIR, 'cache/client_cache.json')

def load_config():
    if not os.path.exists(CONFIG_PATH):
        raise FileNotFoundError(f"Application initialization failed! Configuration file {CONFIG_PATH} was not found inside root application folder.")
    
    try:
        with open(CONFIG_PATH, 'r') as file:
            config = yaml.safe_load(file)
            return config
    except yaml.YAMLError as e:
        raise ValueError(f"Application initialization failed! Configuration file {CONFIG_PATH} contains syntax errors: {e}")

config = load_config()

client = TelegramClient('lvtosapi', config['api'].get('id'), config['api'].get('hash'))

async def load_cache():
    if os.path.exists(CACHE_PATH):
        if os.path.getsize(CACHE_PATH) == 0:
            return None
        async with aiofiles.open(CACHE_PATH, 'r') as file:
            content = await file.read()
            return json.loads(content)
    else:
        return None

async def save_cache(data):
    os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
    
    async with aiofiles.open(CACHE_PATH, 'w') as file:
        await file.write(json.dumps(data))

async def is_recently_online(status):
    if isinstance(status, UserStatusOnline):
        return True
    elif isinstance(status, UserStatusOffline):
        now = datetime.now(timezone.utc)
        if status.was_online and (now - status.was_online) < timedelta(minutes=1):
            return True
    return False

async def create_initial_cache():
    await client.start()

    me = await client.get_me()

    if await is_recently_online(me.status):
        telegram_status = True
    else:
        telegram_status = False

    cache = {
        'expires': (datetime.now() + timedelta(minutes=15)).isoformat(),
        'cache': False,
        'status': telegram_status
    }

    await save_cache(cache)

    return cache

app = FastAPI(
    title="lvkaszus - Telegram Online Status - Public API",
    description="This API is used to check the online status of configured user and return it in JSON format.",
    version="1.0.0"
)

async def startup():
    await client.connect()

async def shutdown():
    await client.disconnect()

app.lifespan = lambda: (startup(), shutdown())

@app.get("/data")
async def get_status():
    cache = await load_cache()

    if cache is None:
        cache = await create_initial_cache()

    expires = datetime.fromisoformat(cache['expires'])
    now = datetime.now()

    if now > expires:
        await client.start()

        me = await client.get_me()
        
        if await is_recently_online(me.status):
            cache['status'] = True
        else:
            cache['status'] = False
        
        cache['expires'] = (now + timedelta(minutes=15)).isoformat()
        cache['cache'] = True
        await save_cache(cache)

        return {"cache": False, "online": cache['status']}

    return {"cache": True, "online": cache['status']}

if __name__ == "__main__":
    uvicorn.run("server:app", port=8001)
