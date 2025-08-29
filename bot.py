import discord
import random
import asyncio
import json

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

TOKEN = config['token']
SERVER_ID = int(config['server_id'])
CHANNEL_IDS = [int(cid) for cid in config['channel_ids']]
MIN_DELAY = 3600 * 24 / config['max_posts_per_day'] # 4 posts -> 6 hours
MAX_DELAY = 3600 * 24 / config['min_posts_per_day'] # 14 posts -> ~1.7 hours

# Load messages
with open('messages.txt', 'r') as f:
    messages = [line.strip() for line in f if line.strip()]

class MyClient(discord.Client):
    async def on_ready(self):
        print(f'Logged on as {self.user}')
        self.bg_task = self.loop.create_task(self.send_messages())

    async def send_messages(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                if not messages or not CHANNEL_IDS:
                    print("No messages or channels configured. Waiting...")
                    await asyncio.sleep(60)
                    continue

                channel_id = random.choice(CHANNEL_IDS)
                channel = self.get_channel(channel_id)
                
                if channel:
                    message = random.choice(messages)
                    await channel.send(message)
                    print(f"Sent message to #{channel.name}: {message}")
                else:
                    print(f"Could not find channel with ID {channel_id}")

                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"An error occurred: {e}")
                await asyncio.sleep(60) # Wait a bit before retrying

intents = discord.Intents.default()
client = MyClient(intents=intents)
client.run(TOKEN)
