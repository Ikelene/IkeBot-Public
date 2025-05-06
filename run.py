import aiohttp
import discord
import asyncio
from discord.ext import commands, tasks
from discord.ui import Button, View
from discord import app_commands
import requests
from datetime import datetime, timedelta, timezone
import os
import json
import random
from PIL import Image, ImageDraw, ImageFont
import io
from io import BytesIO
import difflib

# Initialize the bot
intents = discord.Intents.default()
bot = commands.Bot(command_prefix="/", intents=intents)

test_Token = "TESTING_BOT_TOKEN" # enter the token to your testing bot if you want to use it, leave blank if no
live_Token = "LIVE_BOT_TOKEN" # enter the real bot token here

TESTING_MODE = False # Make this true if you have a testing bot and want to use that instead of live
GITHUB_TOKEN = "FILL THIS IN IF YOUR FORK IS PRIVATE" # If the fork of this repo for your bot is private, enter a github token here.
REPO = "Ikelene/IkeBot-Public" # Change this if you changed the code in your own repository and want to use the new code
FILE_PATH = "commands.py" # Dont touch this
VERSION = "v0.0 - Sync failed" # Dont change this, if you want to change the version change the variable in commands.py

BOT_ID = "YOUR_BOT_ID"  # The User ID of your bot.
OWNER = "YOUR_USER_ID" # The id of yourself. Only this user can run the /sync command
BOT_MENTION_TAGS = [f"<@{BOT_ID}>", f"<@!{BOT_ID}>"]
SETTINGS_FILE = "user_settings.json"
DEFAULT_SETTINGS = {
    "interactions": True
}
ACHIEVEMENTS_FILE = "achievements.json"
STATS_FILE = "stats.json"
stats = {
    "global_commands": 0,
    "servers": {},
    "users": {}
}

VOTE_TRACK_FILE = "votes.json"
TOPGG_API_TOKEN = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJib3QiOiJ0cnVlIiwiaWQiOiIxMzMzMjUwNTExNzI5ODUyNDE2IiwiaWF0IjoiMTc0MzI2Mjk5NyJ9.rqY0vsbZXbfJgjyFW0rE6ewgJgEODo5mreKC3dSLPmg"
BOT_ID = "1333250511729852416"

# Load stats if it exists
if os.path.exists(STATS_FILE):
    with open(STATS_FILE, "r") as f:
        stats = json.load(f)

def save_stats():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)

# Load or create achievements
if os.path.exists(ACHIEVEMENTS_FILE):
    with open(ACHIEVEMENTS_FILE, "r") as f:
        achievements = json.load(f)
else:
    achievements = {}

# find the emojis yourself im too lazy

ACHIEVEMENT_DATA = {
    "voter": {"emoji": "<:vote:1351946099438518403>", "title": "**Voter**", "desc": "*Voted for the bot.*"},
    "active_voter": {"emoji": "<:active_voter:1355566021301506058>", "title": "**Active Voter**", "desc": "Voted in the last 24 hours."},
    "confirmed_gay": {"emoji": "<:gay:1355562085244862571>", "title": "**Confirmed Gay**", "desc": "*Scored 100% on /gayrate.*"},
    "command_lover": {"emoji": "<:Slash_command:1355562392007999632>", "title": "**Command Lover**", "desc": "*Ran 100+ commands on the bot.*"},
    "server_owner": {"emoji": "<:server_owner:1355562614997909544>", "title": "**Server Owner**", "desc": "*Owns a server the bot is in.*"},
    "popular_server_owner": {"emoji": "<:owner_top:1355562939062423726>", "title": "**Popular Server Owner**", "desc": "*Owns a server with 100+ members the bot is in.*"},
    "never_forget": {"emoji": "<:neverforget:1366951784630976613>", "title": "**Never Forget**", "desc": "*September 11, 2001. 9'11\""} # dont worry about this 
}

# Load or create votes
if os.path.exists(VOTE_TRACK_FILE):
    with open(VOTE_TRACK_FILE, "r") as f:
        vote_times = json.load(f)
else:
    vote_times = {}

def save_all():
    with open(STATS_FILE, "w") as f:
        json.dump(stats, f, indent=4)
    with open(ACHIEVEMENTS_FILE, "w") as f:
        json.dump(achievements, f, indent=4)
    with open(VOTE_TRACK_FILE, "w") as f:
        json.dump(vote_times, f, indent=4)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    guild_id = str(message.guild.id)
    user_id = str(message.author.id)

    stats["users"].setdefault(user_id, {"messages": 0, "votes": 0})
    stats["users"][user_id]["messages"] += 1

    stats["servers"].setdefault(guild_id, {"commands": 0})

    save_all()
    await bot.process_commands(message)

@bot.event
async def on_app_command_completion(interaction: discord.Interaction, command: discord.app_commands.Command):
    user_id = str(interaction.user.id)
    guild_id = str(interaction.guild.id)

    stats["global_commands"] += 1
    stats["servers"].setdefault(guild_id, {"commands": 0})
    stats["servers"][guild_id]["commands"] += 1
    stats["users"].setdefault(user_id, {"messages": 0, "votes": 0})

    # Check achievements
    user_achievements = achievements.setdefault(user_id, [])
    if stats["servers"][guild_id]["commands"] >= 100 and "command_lover" not in user_achievements:
        user_achievements.append("command_lover")
    if interaction.guild.owner_id == interaction.user.id:
        if "server_owner" not in user_achievements:
            user_achievements.append("server_owner")
        if interaction.guild.member_count >= 100 and "popular_server_owner" not in user_achievements:
            user_achievements.append("popular_server_owner")

    save_all()

async def fetch_and_exec_code():
    HEADERS = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3.raw"
    }

    url = f"https://api.github.com/repos/{REPO}/contents/{FILE_PATH}"
    print("Fetching latest code from GitHub...")

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=HEADERS) as resp:
            if resp.status == 200:
                code = await resp.text()
                try:
                    exec(code, globals())
                    print("✅ Synced and executed latest GitHub code!")
                    return True
                except Exception as e:
                    print(f"❌ Failed to execute code: {e}")
                    return False
            else:
                print(f"❌ Failed to fetch code: {resp.status}")
                return False

# commands for testing go here
LOADING_EMOJI = "<a:loading:1348408945731178601>"


@bot.tree.command(name="sync")
async def sync_commands(interaction: discord.Interaction):
    if interaction.user.id != OWNER: # 
        return await interaction.response.send_message(f"💔 you can't do that!", ephemeral=True)

    await interaction.response.send_message(f"{LOADING_EMOJI} syncing commands...", ephemeral=False)

    commands_to_remove = [cmd for cmd in bot.tree.get_commands() if cmd.name != "sync"]
    for cmd in commands_to_remove:
        bot.tree.remove_command(cmd.name)

    # Fetch commit number from GitHub
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}"
    }
    url = f"https://api.github.com/repos/{REPO}/commits"
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an exception for 4xx/5xx responses
        commit_data = response.json()

        # Get the number of commits
        commit_num = len(commit_data)  # The number of commits in the returned data
    except requests.exceptions.RequestException as e:
        print(f"❌ failed to fetch commit number: {e}")
        commit_num = "Unknown"

    success = await fetch_and_exec_code()
    if not success:
        return await interaction.followup.send("❌ failed to fetch GitHub code; sync cancelled.")

    # Re-sync AFTER pulling code
    try:
        synced = await bot.tree.sync()
        await interaction.followup.send(
            f"✅ synced {len(synced)} commands.\nSynced to new version: `{VERSION}`"
        )
        print(f"✅ synced {len(synced)} commands to {VERSION}")
    except Exception as e:
        print(f"❌ failed to sync after github pull: {e}")
        await interaction.followup.send(f"❌ failed to sync after github pull:\n```{e}```")


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

    await bot.change_presence(activity=discord.Activity(
        type=discord.ActivityType.watching, name="💎 Based on IkeBot 💎"
    ))

    # 1. GitHub Auto-Sync first
    success = await fetch_and_exec_code()

    # 2. Now sync commands AFTER fetching code, but only if successful
    if success:
        print("Getting ready to sync commands after fetching GitHub code")
        try:
            # Now sync commands
            synced = await bot.tree.sync()
            print(f"✅ Synced {len(synced)} commands")
        except Exception as e:
            print(f"❌ Failed to sync commands: {str(e)}")

            # >>> NEW PART: Send error to a specific user or channel
            owner = await bot.fetch_user(OWNER)
            if owner:
                try:
                    await owner.send(f"❌ **Bot failed to sync commands:**\n```{str(e)}```")
                except Exception as dm_error:
                    print(f"Also failed to DM error: {str(dm_error)}")
    else:
        print("❌ Skipped command sync because GitHub code fetch failed.")

if TESTING_MODE:
    bot.run(test_Token)
else:
    bot.run(live_Token)
