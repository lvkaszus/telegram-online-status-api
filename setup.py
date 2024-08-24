import os
import yaml
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, 'config/config.yml')


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

async def main():
    try:
        await client.start()
    except Exception as e:
        print(f"Error while authorizing you to the Telegram API: {e}")

if __name__ == "__main__":
    with client:
        client.loop.run_until_complete(main())