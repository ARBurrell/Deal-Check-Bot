import discord
from discord import app_commands
from bs4 import BeautifulSoup
from selenium import webdriver
import schedule
import time
import toml
import csv
import os
import re
import logging
import random

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)
config = toml.load('config.toml')  # Use config.toml for live, testconfig.toml for test
test_mode = config['mode']['test_mode']
section_name = 'testdiscord' if test_mode == 'true' else 'discord'
guild_id = config[section_name]['guild_id']
LINKS_FILE = 'links.csv'  # Can be empty, will store the most recent 'link' (the links are now identifiers, but links may be used again later)
DEAL_CHANNEL_NAME = 'amazon-deals'  # Replace with the actual name of your 'deal-of-the-day' text channel
startup_check_enabled = config[section_name]['startup_check_enabled']  # Set to False to disable the startup check and post

driver = webdriver.Chrome()  # Webdriver startup, currently only works with Chrome reliably

global last_posted_link  # Declare last_posted_link as a global variable
last_posted_link = None  # Variable to store the last posted deal link

# Configure the logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)

# Load phrases from a file
def load_phrases(filename):
    with open(filename, 'r') as file:
        phrases = [line.strip() for line in file if line.strip()]
    return phrases

# Randomly select a phrase
def get_random_phrase(phrases):
    return random.choice(phrases)

# Load phrases from local txt files for deal and no new deal messages
deal_phrases = load_phrases('deal_phrases.txt')
no_deal_phrases = load_phrases('no_deal_phrases.txt')

# On startup, confirm login and confirm readiness, check for previous entries, check link and post it if mismatching
@client.event
async def on_ready():
    logging.info('Logged in successfully!')
    logging.info('------')
    logging.info('!In testing mode!') if test_mode == 'true' else ('')
    logging.info('Ready!')
    logging.info('------')
    channel = discord.utils.get(client.get_all_channels(), name=DEAL_CHANNEL_NAME, type=discord.ChannelType.text)
    if channel is not None:
        last_posted_link = read_last_link()
        if last_posted_link is None and STARTUP_CHECK_ENABLED:
            new_deal_link = await get_new_deal_link()
            if new_deal_link is not None:
                await post_deal_to_channel(channel, new_deal_link)
                last_posted_link = extract_unique_id(new_deal_link)
                save_last_link(last_posted_link)

# Listen for manual /deal commands in any channel the bot has access to
@tree.command(name="deal", description="Find the current top deal!")
async def deal(interaction: discord.Interaction):
    global last_posted_link
    await interaction.response.send_message('Received your request!', ephemeral=True)  # Need ephemeral or it'll 'no response' error
    new_deal_link = await get_new_deal_link()
    if new_deal_link is not None:
        unique_id = extract_unique_id(new_deal_link)
        if last_posted_link is None or last_posted_link != unique_id:
            await post_deal_to_channel(interaction.channel, new_deal_link)
            last_posted_link = unique_id
            save_last_link(last_posted_link)  # Save the new link to the CSV file
        else:
            await interaction.channel.send(get_random_phrase(no_deal_phrases))
    else:
        await interaction.channel.send(get_random_phrase(no_deal_phrases))

# List available commands
@tree.command(name="help", description="Display available commands.")
async def help_command(interaction: discord.Interaction):
    command_list = [
        app_command.name for app_command in tree.commands.values()
    ]
    commands = "\n".join(command_list)
    await interaction.response.send_message(f"Available commands:\n{commands}", ephemeral=True)

async def post_deal_to_channel(channel, new_deal_link):
    try:
        # Get the webpage title from the deal URL
        driver.get(new_deal_link)  # Visit the deal URL
        deal_page_source = driver.page_source
        deal_soup = BeautifulSoup(deal_page_source, 'html.parser')
        title = deal_soup.title.string.strip()

        message = f"{get_random_phrase(deal_phrases)}\n\n{title}!\n\n{new_deal_link}"
        logging.info(message)
        await channel.send(message)
    except Exception as e:
        logging.error(f'An error occurred: {str(e)}')

# Currently in use instead of true URLs, using UIDs
def extract_unique_id(url):
    # Creating the unique identifier from the URL using regex
    pattern = r'([^/?]+)\?'
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def read_last_link():
    if os.path.isfile(LINKS_FILE):
        with open(LINKS_FILE, 'r', newline='') as file:
            reader = csv.reader(file)
            for row in reader:
                return row[0]
    return None

def save_last_link(link):
    with open(LINKS_FILE, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([link])

# Checking the deal every hour on the hour, only posting if deal never posted
async def check_deal_and_post():
    channel = discord.utils.get(client.get_all_channels(), name=DEAL_CHANNEL_NAME, type=discord.ChannelType.text)
    if channel is not None:
        new_deal_link = await get_new_deal_link()
        if new_deal_link is not None and new_deal_link != last_posted_link:
            await post_deal_to_channel(channel, new_deal_link)
            last_posted_link = new_deal_link
    schedule.every().hour.at(':00').do(check_deal_and_post)

# Finding the first 'deal' link on the Amazon Au page. Would be nice to expand this to other regions.
async def get_new_deal_link():
    driver.get('https://www.amazon.com.au/gp/goldbox')
    driver.implicitly_wait(10)
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, 'html.parser')
    for a in soup.find_all('a', href=True):
        if a['href'].startswith('https://www.amazon.com.au/deal/'):
            return a['href']
    return None

# Manually sync slash commands using a ! command to keep it away from public usage
async def on_message(message):
    if message.content.startswith('!slashSync'):
        try:
            await tree.sync()

            print(f'Synced')
        except Exception as e:
            print(e)

# Pulling the key from the 'config.toml' file. Heading should be [api], on the line below remove single quotes, swap 123 for actual key 'key = "123"'
client.run(config['discord']['token'])
