import discord
import random
import asyncio
import json

# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

TOKEN = config['token']
SERVER_ID = int(config['server_id'])
MIN_DELAY = 3600 * 24 / config['max_posts_per_day'] # 4 posts -> 6 hours
MAX_DELAY = 3600 * 24 / config['min_posts_per_day'] # 14 posts -> ~1.7 hours

# Load messages
with open('messages.txt', 'r') as f:
    messages = [line.strip() for line in f if line.strip()]

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.all_channels = []

    async def on_ready(self):
        print(f'Logged on as {self.user}')
        
        guild = self.get_guild(SERVER_ID)
        if guild:
            self.all_channels = [ch for ch in guild.text_channels if ch.permissions_for(guild.me).send_messages]
            print(f"Found {len(self.all_channels)} channels to post in.")
        else:
            print(f"Could not find server with ID {SERVER_ID}. Bot will not send messages.")

        self.bg_task = self.loop.create_task(self.send_messages())

    async def send_messages(self):
        await self.wait_until_ready()
        while not self.is_closed():
            try:
                if not messages or not self.all_channels:
                    print("No messages or channels available. Waiting...")
                    await asyncio.sleep(60)
                    continue

                channel = random.choice(self.all_channels)
                
                message = random.choice(messages)
                await channel.send(message)
                print(f"Sent message to #{channel.name}: {message}")

                delay = random.uniform(MIN_DELAY, MAX_DELAY)
                await asyncio.sleep(delay)

            except Exception as e:
                print(f"An error occurred: {e}")
                await asyncio.sleep(60) # Wait a bit before retrying

intents = discord.Intents.default()
client = MyClient(intents=intents)
client.run(TOKEN)
