import discord
import asyncio

# -------------------------
# CONFIGURATION
# Load configuration
with open('config.json') as config_file:
    config = json.load(config_file)

# -------------------------
TOKEN = config['token']  # Replace with your bot token
GUILD_ID = int(config['server_id']) # Replace with your server (guild) ID
TARGET_USER_ID = 281945549937049600  # Replace with target user ID
OUTPUT_FILE = "messages.txt"
# -------------------------

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True
intents.messages = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Could not find guild.")
        await client.close()
        return

    messages = []

    print("Fetching messages... This may take a while depending on server size.")

    for channel in guild.text_channels:
        try:
            async for message in channel.history(limit=None, oldest_first=True):
                if message.author.id == TARGET_USER_ID:
                    messages.append(message.content.replace("\n", " "))
        except discord.Forbidden:
            print(f"Skipping {channel.name} (no permissions)")
        except discord.HTTPException as e:
            print(f"Error in {channel.name}: {e}")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for msg in messages:
            f.write(msg + "\n")

    print(f"Saved {len(messages)} messages to {OUTPUT_FILE}")
    await client.close()

client.run(TOKEN)
