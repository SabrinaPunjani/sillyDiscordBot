import discord
import random
import asyncio
import json
import requests
from bs4 import BeautifulSoup
import difflib
import re
from submodule.IIDX_dan_courses.courses import dan_courses_sp, dan_courses_dp
from rngddr import getRng

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

        search_results = soup.find('div', class_='searchresults')
        if not search_results:
            return "No search results found on remywiki.com."

        results = {a.get_text(): a['href'] for a in search_results.find_all('a') if a.get_text() and a.has_attr('href')}
        if not results:
            return "No valid search results found."

        titles = list(results.keys())
        best_match = difflib.get_close_matches(query, titles, n=1, cutoff=0.4)

        if not best_match:
            return f"I couldn't find a good match for '{query}' on remywiki.com."

        page_url = f"https://remywiki.com{results[best_match[0]]}"

        page_response = await asyncio.to_thread(requests.get, page_url)
        page_response.raise_for_status()
        page_soup = BeautifulSoup(page_response.text, 'html.parser')

        content_div = page_soup.find('div', id='mw-content-text')
        if not content_div:
            return "Could not find content on the page."

        paragraphs = content_div.find_all('p', limit=3)
        if not paragraphs:
            return "No paragraphs found on the page."

        return '\n'.join([p.get_text() for p in paragraphs])

    except requests.exceptions.RequestException as e:
        return f"Error accessing remywiki.com: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

async def get_random_remywiki_page():
    random_url = "https://remywiki.com/Special:Random"
    try:
        response = await asyncio.to_thread(requests.get, random_url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        title = soup.find('h1', id='firstHeading').get_text()
        content_div = soup.find('div', id='mw-content-text')
        first_paragraph = content_div.find('p').get_text()

        return f"**{title}**\n{first_paragraph}\n\n{response.url}"

    except requests.exceptions.RequestException as e:
        return f"Error accessing remywiki.com: {e}"
    except Exception as e:
        return f"An error occurred: {e}"

class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.allowed_channel_ids = [int(ch_id) for ch_id in config.get('allowed_channels', [])]
        self.all_channels = []

    async def on_ready(self):
        print(f'Logged on as {self.user}')
        
        guild = self.get_guild(SERVER_ID)
        if guild:
            if not self.allowed_channel_ids:
                print("Warning: 'allowed_channels' is empty in config.json. The bot will not send messages to any channel.")
            
            self.all_channels = [ch for ch in guild.text_channels if ch.id in self.allowed_channel_ids and ch.permissions_for(guild.me).send_messages]
            
            if self.all_channels:
                print(f"Found {len(self.all_channels)} allowed channels to post in: {[ch.name for ch in self.all_channels]}")
            else:
                print("Could not find any of the allowed channels on this server, or I don't have permissions to send messages in them.")
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

        if message.content.startswith('!daquan'):
            await message.channel.send("<:daquan:1379633390260850718>")
            return
        
        if message.content.startswith('!ddr'):
            await message.channel.send(getRng())
            return

        if message.content.startswith('!dan'):
            source_link = "\nSource: https://remywiki.com/Beatmania_IIDX_Dan_Courses"
            try:
                match = re.match(r'^!dan(?:\s+(sp|dp))?\s+\"([^\"]+)\"\s+\"([^\"]+)\"$', message.content, re.IGNORECASE)
                if not match:
                    await message.channel.send(f"Usage: `!dan [sp/dp] \"<dan course>\" \"<game>\"`{source_link}")
                    return

                play_style_input, dan_course_input, game_input = match.groups()
                play_style = play_style_input.lower() if play_style_input else 'sp'

                course_data = dan_courses_sp if play_style == 'sp' else dan_courses_dp

                # Case-insensitive dan course matching
                matched_dan_course = None
                for key in course_data.keys():
                    if key.lower() == dan_course_input.lower():
                        matched_dan_course = key
                        break

                if not matched_dan_course:
                    # Find closest match
                    lower_keys = [k.lower() for k in course_data.keys()]
                    closest_dan = difflib.get_close_matches(dan_course_input.lower(), lower_keys, n=1, cutoff=0.6)
                    if closest_dan:
                        # Find the original cased key
                        for k in course_data.keys():
                            if k.lower() == closest_dan[0]:
                                await message.channel.send(f"Dan course '{dan_course_input}' not found. Did you mean '{k}'?{source_link}")
                                return
                    else:
                        await message.channel.send(f"Dan course '{dan_course_input}' not found.{source_link}")
                    return
                
                # Partial and case-insensitive game matching
                matched_game = None
                game_keys = course_data[matched_dan_course].keys()
                
                # Exact match first
                for key in game_keys:
                    if key.lower() == game_input.lower():
                        matched_game = key
                        break
                
                # Then startswith match
                if not matched_game:
                    for key in game_keys:
                        if key.lower().startswith(game_input.lower()):
                            matched_game = key
                            break

                if not matched_game:
                    lower_game_keys = [k.lower() for k in game_keys]
                    closest_game = difflib.get_close_matches(game_input.lower(), lower_game_keys, n=1, cutoff=0.6)
                    if closest_game:
                        for k in game_keys:
                            if k.lower() == closest_game[0]:
                                await message.channel.send(f"Game '{game_input}' not found for {matched_dan_course}. Did you mean '{k}'?{source_link}")
                                return
                    else:
                        await message.channel.send(f"Game '{game_input}' not found for {matched_dan_course}.{source_link}")
                    return

                song_list = course_data[matched_dan_course][matched_game]
                response = f"**{matched_dan_course} ({play_style.upper()}) - {matched_game}**\n"
                for i, song in enumerate(song_list):
                    response += f"{i+1}. {song}\n"
                
                await message.channel.send(f"{response}{source_link}")
                return
            except Exception as e:
                print(f"Error processing !dan command: {e}")
                await message.channel.send(f"An error occurred while processing the command.{source_link}")
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
        elif len(words) > 1 and words[0] == 'remove':
            role_name = words[1]
            guild = message.guild
            role = discord.utils.get(guild.roles, name=role_name)

            if not guild.me.guild_permissions.manage_roles:
                await message.channel.send("I don't have the `manage_roles` permission.")
                return

            if not role:
                await message.channel.send(f"The role {role_name} doesn't exist.")
                return

            if role not in message.author.roles:
                await message.channel.send(f"You don't have the {role_name} role.")
                return

            try:
                await message.author.remove_roles(role)
                await message.channel.send(f"Removed the {role_name} role.")
            except discord.Forbidden:
                await message.channel.send("I don't have permission to remove roles.")
            except Exception as e:
                print(f"Error removing role: {e}")
                await message.channel.send("Something went wrong while removing the role.")
            return

        # If the bot is mentioned or it's a reply to the bot
        if self.user in message.mentions or (message.reference and message.reference.resolved and message.reference.resolved.author == self.user):
            # Q&A functionality
            keywords = ['?', 'bemani', 'ddr', 'beatmania', 'iidx', 'round1']
            random_keywords = ['fact', 'random']
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
            elif any(keyword in message.content.lower() for keyword in random_keywords):
                try:
                    await message.channel.send("Getting a random page from remywiki.com for you...")
                    response = await get_random_remywiki_page()
                    await message.channel.send(response)
                except Exception as e:
                    print(f"Error during random page fetch: {e}")
                    await message.channel.send("Sorry, I couldn't fetch a random page.")
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

activity = discord.Game(name="ask me a question about BEMANI")
client = MyClient(intents=intents, activity=activity)

client.run(TOKEN)
