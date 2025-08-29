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

import discord
import random
import asyncio
import json
import requests
from bs4 import BeautifulSoup

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

async def search_remywiki(query):
    search_url = f"https://remywiki.com/index.php?search={query}"
    try:
        response = await asyncio.to_thread(requests.get, search_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        # Find the first search result link
        search_results = soup.find('div', class_='searchresults')
        if not search_results:
            return "No search results found on remywiki.com."

        first_result = search_results.find('a')
        if not first_result or 'href' not in first_result.attrs:
            return "No valid search results found."

        page_url = f"https://remywiki.com{first_result['href']}"

        # Get the content of the page
        page_response = await asyncio.to_thread(requests.get, page_url)
        page_response.raise_for_status()
        page_soup = BeautifulSoup(page_response.text, 'html.parser')

        # Extract the main content
        content_div = page_soup.find('div', id='mw-content-text')
        if not content_div:
            return "Could not find content on the page."

        # Get the first few paragraphs
        paragraphs = content_div.find_all('p', limit=3)
        if not paragraphs:
            return "No paragraphs found on the page."

        return '\n'.join([p.get_text() for p in paragraphs])

    except requests.exceptions.RequestException as e:
        return f"Error accessing remywiki.com: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

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

    async def on_message(self, message):
        # Don't reply to ourselves
        if message.author == self.user:
            return

        # Role assignment logic
        words = message.content.lower().split()
        if len(words) > 1 and (words[0] == 'color' or words[0] == 'country'):
            role_name = words[1]
            guild = message.guild

            if not guild.me.guild_permissions.manage_roles:
                await message.channel.send("I don't have the `manage_roles` permission.")
                return

            # Check if role already exists
            role = discord.utils.get(guild.roles, name=role_name)

            if not role:
                try:
                    color = discord.Color.default()
                    if words[0] == 'color':
                        try:
                            color = getattr(discord.Color, words[1])()
                        except AttributeError:
                            await message.channel.send(f"Sorry, I don't know the color {role_name}.")
                            return
                    elif words[0] == 'country':
                        color = discord.Color.random()

                    role = await guild.create_role(name=role_name, color=color, permissions=discord.Permissions.none())
                    await message.channel.send(f"Created the {role_name} role for you!")

                except discord.Forbidden:
                    await message.channel.send("I don't have permission to create roles.")
                    return
                except Exception as e:
                    print(f"Error creating role: {e}")
                    await message.channel.send("Something went wrong while creating the role.")
                    return

            # Assign the role
            try:
                await message.author.add_roles(role)
                await message.channel.send(f"You now have the {role_name} role!")
            except discord.Forbidden:
                await message.channel.send("I don't have permission to assign roles.")
            except Exception as e:
                print(f"Error assigning role: {e}")
                await message.channel.send("Something went wrong while assigning the role.")
            return

        # If the bot is mentioned or it's a reply to the bot
        if self.user in message.mentions or (message.reference and message.reference.resolved.author == self.user):
            # Q&A functionality
            keywords = ['?', 'bemani', 'ddr', 'beatmania', 'iidx', 'round1']
            if any(keyword in message.content.lower() for keyword in keywords):
                try:
                    await message.channel.send("Let me check remywiki.com for you...")
                    query = message.content.replace(f'<@!{self.user.id}>', '').strip()
                    response = await search_remywiki(query)
                    await message.channel.send(response)
                except Exception as e:
                    print(f"Error during web fetch: {e}")
                    await message.channel.send("Sorry, I couldn't fetch the information.")
                return

            reply_message = random.choice(messages)
            await message.channel.send(reply_message)
            print(f"Replied to {message.author} in #{message.channel.name}: {reply_message}")

intents = discord.Intents.default()
intents.presences = True
intents.messages = True
intents.guilds = True
intents.members = True
intents.message_content = True
#intents.manage_roles = True

activity = discord.Game(name="with your feelings")
client = MyClient(intents=intents, activity=activity)

client.run(TOKEN)
