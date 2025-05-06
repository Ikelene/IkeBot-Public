import os
import json
from pydoc import describe
import random
import discord
from discord import app_commands, FFmpegPCMAudio
from discord.ext import commands, tasks
import re

VERSION = "v7.6d"

# music list
PLAYLIST_OPTIONS = ["Random", "Egyptian", "Jazz"]

RANDOM_PLAYLIST = ["music/Tropical Crust.mp3", "music/INCINERATOR V2.mp3", "music/Sugar Nature.mp3", "music/Why's this dealer.mp3", "music/Pralax.mp3", "music/Bouncing Around.mp3", "music/Be Quick Or Be Dead.mp3", "music/Deadly Force.mp3", "music/Hackers.mp3", "music/Meltdown Black Mesa.mp3", "music/MELTDOWN.mp3", "music/Beast.mp3", "music/boogie-down.mp3", "music/ELEVATOR.mp3", "music/from the start (meowfey).mp3", "music/Project Borealis OST  2. Resonance.mp3", "music/Project Borealis OST 9. Breach 4.mp3", "music/Crazy Cattle 3D OST - Ireland.mp3", "music/I got a brand new saxophone.mp3", "music/Anak Nonstop Remix.mp3", "music/antiPLUR-Runengon.mp3"]
EGYPTIAN_PLAYLIST = ["egyptian/Screwbot Factory.mp3", "egyptian/Tomb Raiders.mp3", "egyptian/Egyptian Warriors.mp3", "egyptian/Desert Mercenaries.mp3", "egyptian/Desert Lullaby.mp3", "egyptian/The Nile River.mp3", "egyptian/Desert Phoenix.mp3", "egyptian/Joseph.mp3", "egyptian/Prince of Egypt.mp3", "egyptian/Lost Tombs.mp3", "egyptian/Golden Scarabs.mp3", "egyptian/Land of the Pharaohs.mp3"]
JAZZ_PLAYLIST = ["jazz/Jazzaddicts.mp3", "jazz/Nighttime Stroll.mp3", "jazz/Night Out.mp3", "jazz/Gotta Go.mp3", "jazz/Fortuna.mp3", "jazz/EARLY SUMMER.mp3"]

LOADING_EMOJI = "<a:loading:1348408945731178601>"
DONE_EMOJI = "<:success:1348408534957690921>"
WARNING_EMOJI = "<:warning:1348408510001451091>"
ERROR_EMOJI = "<a:error:1348408553635057667>"
MUSIC_EMOJI = "<a:music_eq_bars:1348408058941804565>"
NEXTUP_EMOJI = "<:nextup:1366543129083379883>"
DOT_EMOJI = "<:dot:1366543136003719228>"
YES_EMOJI = "<:yes:1351946116882497578>"
NO_EMOJI = "<:no:1351946042274218005>"
NOTICE_EMOJI = "<:notice:1351942621622439987>"

INTERACTIONS_DISABLED_MESSAGE = "has interactions disabled.**\n*Basically you cannot use commands on them silly.*"
SELF_INTERACTIONS_DISABLED_MESSAGE = f"{WARNING_EMOJI}** You have interactions disabled.**\nTurn them on if you want to use them on other people"

# code to make it work in dms but it does not work right now
# big sadge moment

# @app_commands.contexts(
#     InteractionContextType.bot_dm,
#     InteractionContextType.guild,
#     InteractionContextType.private_channel
# )
# @app_commands.integration_types(
#     ApplicationIntegrationType.guild_install,
#     ApplicationIntegrationType.user_install
# )

def load_settings():
    if not os.path.exists(SETTINGS_FILE):
        return {}
    with open(SETTINGS_FILE, 'r') as f:
        return json.load(f)

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def get_user_settings(user_id):
    settings = load_settings()
    user_id = str(user_id)
    if user_id not in settings:
        settings[user_id] = DEFAULT_SETTINGS.copy()
        save_settings(settings)
    return settings[user_id]

def set_user_interactions(user_id, enabled):
    settings = load_settings()
    user_id = str(user_id)
    if user_id not in settings:
        settings[user_id] = DEFAULT_SETTINGS.copy()
    settings[user_id]["interactions"] = enabled
    save_settings(settings)

def interactions_enabled(user_id):
    settings = get_user_settings(user_id)
    return settings.get("interactions", True)

async def check_interactions(interaction_user, *other_users):
    if not interactions_enabled(interaction_user.id):
        return SELF_INTERACTIONS_DISABLED_MESSAGE

    for user in other_users:
        if not interactions_enabled(user.id):
            return f"{ERROR_EMOJI} **{user.name} {INTERACTIONS_DISABLED_MESSAGE}"
        elif user == 677321837985792021:
            return None

    return None

# Function to parse time input (e.g., 5h, 1d, 10m, etc.)
def parse_time_input(time_str):
    match = re.match(r'(\d+)([hmds])', time_str)
    if not match:
        return None
    value, unit = match.groups()
    value = int(value)

    if unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 's':
        return timedelta(seconds=value)

    return None

# Fix for serializing timedelta
def timedelta_to_seconds(delta):
    return delta.total_seconds()

def seconds_to_timedelta(seconds):
    return timedelta(seconds=seconds)

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
	    

@bot.tree.command(name="interactions", description="Enable or disable interactions for yourself")
@app_commands.describe(enabled="Set to true to enable, false to disable")
async def interactions(interaction: discord.Interaction, enabled: bool):
    set_user_interactions(interaction.user.id, enabled)
    state = "enabled" if enabled else "disabled"
    await interaction.response.send_message(f"Interactions have been {state} for you.")

# Slash command to enable/disable dead chat stats
@bot.tree.command(name="deadchat_stats", description="Enable/Disable dead chat stats for a channel")
async def deadchat_stats(interaction: discord.Interaction, channel: discord.TextChannel, time: str):
    if not interaction.user.guild_permissions.administrator:
        return await interaction.response.send_message("❌ only server admins can run this command.", ephemeral=True)

    try:
        settings = await load_deadchat_settings()

        if time == "0" or time.lower() == "off":
            settings.pop(str(channel.id), None)
            await save_deadchat_settings(settings)
            await interaction.response.send_message(f"Dead chat stats disabled for {channel.mention} {DONE_EMOJI}.")
            return

        parsed_time = parse_time_input(time)
        if parsed_time is None:
            await interaction.response.send_message("Invalid time input. Please use a format like 5h, 10m, 1d, etc.")
            return

        settings[str(channel.id)] = {
            "time_limit": parsed_time,
            "last_message_time": None
        }
        await save_deadchat_settings(settings)

        await interaction.response.send_message(f"Dead chat stats enabled for {channel.mention} for {time} {DONE_EMOJI}.")
        watch_dead_chat.start(channel)

    except Exception as e:
        await interaction.response.send_message(f"Error occurred: {ERROR_EMOJI} {str(e)}")
        print(f"Error in deadchat_stats command: {str(e)}")



@bot.tree.command(name="meme")
async def meme(interaction: discord.Interaction):
    # URL of the meme generator
    meme_url = "https://ikelene.ca/media/meme.php"

    try:
        # Fetch the meme image from the URL
        response = requests.get(meme_url)

        # Check if the request was successful
        if response.status_code != 200:
            return await interaction.response.send_message(f"¯\\_(ツ)_/¯ failed to fetch meme image. Status code: {response.status_code}", ephemeral=True)

        # Check if the response is an image
        if 'image' not in response.headers['Content-Type']:
            return await interaction.response.send_message(f"¯\\_(ツ)_/¯ the response isn't an image! Content-Type: {response.headers['Content-Type']}", ephemeral=True)

        # Save the image temporarily
        meme_path = "memes/brainrot/temp_meme.png"
        with open(meme_path, "wb") as f:
            f.write(response.content)

        # Send the image to Discord
        await interaction.response.send_message(file=discord.File(meme_path))

        # Remove the temporary image after sending
        os.remove(meme_path)
        print(f"✅ Removed the temporary meme image")

    except Exception as e:
        return await interaction.response.send_message(f"¯\\_(ツ)_/¯ something went wrong: {e}", ephemeral=True)


@bot.tree.command(name="snapchat")
@app_commands.describe(text="snapchat caption", image="snap image")
async def snapchat(interaction: discord.Interaction, text: str, image: discord.Attachment):
    await interaction.response.defer()
    data = await image.read()
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    overlay = Image.new("RGBA", img.size, (0,0,0,0))
    draw = ImageDraw.Draw(overlay)
    font = ImageFont.truetype("arial.ttf", size=24)

    # after img/open and overlay setup
    bbox = draw.textbbox((0,0), text, font=font)
    text_w, text_h = bbox[2]-bbox[0], bbox[3]-bbox[1]
    pad = 10
    y = img.height//2 + (img.height//2 - text_h)//2 - 80

    # full-width 50% opaque box
    draw.rectangle((0, y-pad, img.width, y+text_h+pad), fill=(0,0,0,128))

    # center your text in that box
    x = (img.width - text_w)//2
    draw.text((x, y), text, font=font, fill=(255,255,255,255))


    result = Image.alpha_composite(img, overlay)
    buf = io.BytesIO()
    result.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    await interaction.followup.send(           # <- change this
        file=discord.File(buf, filename="snapchat.png")
    )


@bot.tree.command(name="brainrot")
@app_commands.describe(topic="subject of brainrot")
async def brainrot(interaction: discord.Interaction, topic: str):
    emojis = ["low taper fade", "massive", "2025 brainrot", "sigma", "skibidi toilet", "ipad kid", "gen z", "in the big 2025", "mong us"]
    yaps = [f"when {topic} vibes too hard, it glitchs into next gen. brainrot overload!", f"when {topic} starts doing backflips in my serotonin receptors", f"{topic} got that rizzcore pipeline real bad", f"this ain’t even brainrot no more this is brain **evaporation**", f"{topic} been cooking in my head rent free since the skibidi era", f"{topic} rewired my neurons and now i bark at walls", f"bro i saw {topic} once and now i say “be fr” to the microwave", f"{topic}? oh you mean my intrusive thought bestie???", f"touched grass once but still thinking bout {topic}", f"{topic} got me in a chokehold stronger than 2016 vine edits", f"this the type of {topic} that makes me forget how to blink", f"{topic} lives in my head with a lease and a HOA", f"i unironically meowed because of {topic}", f"saw {topic} and my brain played the windows xp shutdown sound"]
    lines = []
    yap_choice = ""
    for i in range(1,6):
        vibe = random.choice(emojis)
        yap_choice = random.choice(yaps)
        lines.append(f"• **{vibe}** headcanon {i}: {yap_choice}")
    text = "\n".join(lines)
    await interaction.response.send_message(f"**🤯  brainrot maxed**\n{text}")


# /freak command
@bot.tree.command(name="freak", description="Turns your text 𝓯𝓻𝓮𝓪𝓴𝔂")
async def freak(interaction: discord.Interaction, text: str):
    normal = ["a","b","c","d","e","f","g","h","i","j","k","l","m","n","o","p","q","r","s","t","u","v","w","x","y","z"]
    fancy = ["𝓪","𝓫","𝓬","𝓭","𝓮","𝓯","𝓰","𝓱","𝓲","𝓳","𝓴","𝓵","𝓶","𝓷","𝓸","𝓹","𝓺","𝓻","𝓼","𝓽","𝓾","𝓿","𝔀","𝔁","𝔂","𝔃"]
    conversion = {normal[i]: fancy[i] for i in range(len(normal))}

    result = "".join([conversion.get(char, char) for char in text.lower()])
    await interaction.response.send_message(result)

# /alternate command
@bot.tree.command(name="alternate", description="Convert text to alternating upper and lowercase.")
async def alternate(interaction: discord.Interaction, text: str):
    result = ''.join(
        char.upper() if i % 2 == 0 else char.lower()
        for i, char in enumerate(text)
    )
    await interaction.response.send_message(result)

# /hacker command
@bot.tree.command(name="hacker", description="Convert text to symbols to make it look like a hacker wrote it")
async def hacker(interaction: discord.Interaction, text: str):
    symbol_map = {
        'a': '@', 'b': '8', 'c': 'c', 'd': 'd', 'e': '3', 'f': 'f', 'g': '9',
        'h': '#', 'i': '!', 'j': ']', 'k': 'k', 'l': '1', 'm': 'm', 'n': 'n',
        'o': '0', 'p': 'p', 'q': 'q', 'r': 'r', 's': '$', 't': '+', 'u': 'u',
        'v': 'v', 'w': 'w', 'x': '*', 'y': 'y', 'z': '2'
    }
    result = ''.join(symbol_map.get(char.lower(), char) for char in text)
    await interaction.response.send_message(result)


@bot.tree.command(name="rizzify", description="convert text into rizzified slang")
async def rizzify(interaction: discord.Interaction, text: str):
    mapping = {
        "hello": ["ne how"],
        "there": ["fyne shyt"],
        "you": ["ewe"],
        "my": ["mai"],
        "love": ["luv"],
        "what's": ["wuts"],
        "up": ["upp"],
        "bro": ["bruhh"],
        "rizz": ["rizzle", "rizzlord", "big rizz energy"],
        "drip": ["rizzdrip", "drippin'"],
        "vibe": ["vybe", "vybess"],
        "cool": ["kewl", "k00l"],
        "money": ["m00ney", "moneez"],
        "party": ["partee", "par-tay"],
        "yes": ["yessir", "yezz"],
        "no": ["nahh", "nope"],
        "what": ["wut", "wha"],
        "why": ["y?", "whyy"],
        "please": ["plz", "plzzz"],
        "thanks": ["thx", "tysm"],
        "sorry": ["srry", "soz"],
        "everyone": ["evry1", "evrybody"],
        "game": ["g4m3", "g4me"],
        "time": ["tyme"],
        "again": ["agan", "agin"],
        "best": ["besst"],
        "sis": ["siz"],
        "duck": ["ducc"],
        "cat": ["katt"],
        "dog": ["doggo"],
        "night": ["nite", "nitez"]
    }
    words = text.split()
    transformed = []
    for w in words:
        lw = w.lower()
        if lw in mapping:
            transformed.append(random.choice(mapping[lw]))
        else:
            transformed.append(w[1:] + w[0] + "ez")
    await interaction.response.send_message(" ".join(transformed))

@bot.tree.command(name="diagnose", description="diagnose a user with silly syndrome")
async def diagnose(interaction: discord.Interaction, user: discord.Member):
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return
    dx = [
        "minecraft obsession syndrome",
        "ligma disease",
        "skibidi toilet addiction",
        "discord moditis",
        "sleep deprivation disorder",
        "algorithm obsession syndrome",
        "ai hallucination disorder",
        "meme overdraft",
        "fps rage quit fever",
        "hyperfixation flux",
        "quantum rizz overload"
    ]
    tx = [
        "uninstall roblox",
        "touch grass",
        "watch more tiktoks",
        "drink water",
        "take a nap",
        "join a book club",
        "limit screen time",
        "yoga break",
        "eat a sandwich",
        "listen to lofi",
        "drink coffee responsibly"
    ]
    chosen_dx = random.choice(dx)
    chosen_tx = random.choice(tx)
    msg = f"you’ve been diagnosed with: **{chosen_dx}**\ntreatment: {chosen_tx}"
    await interaction.response.send_message(msg)

@bot.tree.command(name="sit", description="send a random sit gif")
async def sit(interaction: discord.Interaction):
    gifs = [
        "https://tenor.com/view/jeremiah-jarrell-buie-seat-chair-gif-19385503",
        "https://tenor.com/view/corner-sit-deer-gif-10844181262590199499",
        "https://tenor.com/view/retro-wave-cat-sit-sits-gif-26176375",
        "https://tenor.com/view/cat-fight-cat-fight-sit-sit-on-it-gif-27527868",
        "https://tenor.com/view/blue-archive-mutsuki-asagi-%E3%83%A0%E3%83%84%E3%82%AD-gif-1462759947642942531",
        "https://tenor.com/view/nadeshiko-kagamihara-yurucamp-yuru-camp-kagamihara-nadeshiko-nadeshiko-gif-9671488999527369023",
        "https://tenor.com/view/sit-back-crossed-leg-leg-rest-sit-seating-position-gif-9177457557525245165"
    ]
    url = random.choice(gifs)
    await interaction.response.send_message(f"you’ve been sat. respectfully.\n{url}")

@bot.tree.command(name="skull", description="send a spooky skull quote")
async def skull(interaction: discord.Interaction):
    quotes = [
        "this message was so uncalled for it made me respawn in ohio 💀",
        "i died laughing but never respawned 💀",
        "skull vibes only 💀",
        "when the server crashes i come back as a skeleton 💀",
        "my brain's a haunted house rn 💀",
        "everyone's a ghost in my skull city 💀"
    ]
    await interaction.response.send_message(random.choice(quotes))

@bot.tree.command(name="ipad_detect", description="detect if a user is an iPad kid")
async def ipad_detect(interaction: discord.Interaction, user: discord.Member):
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return
    probs = [
        "high",
        "100%",
        "probable",
        "sus AF",
        "over 9000",
        "unstable wifi signature",
        "permanently stuck on portrait mode",
        "charging with case on",
        "detected multiple screen taps",
        "battery health critical"
    ]
    await interaction.response.send_message(
        f"🔍 user detected: probable ipad user ({random.choice(probs)})"
    )

@bot.tree.command(name="melt", description="melt your message")
async def melt(interaction: discord.Interaction):
    await interaction.response.send_message("melting…")
    await discord.utils.sleep_until(discord.utils.utcnow() + discord.timedelta(seconds=3))
    msgs = await interaction.channel.history(limit=1).flatten()
    await msgs[0].delete()


@bot.tree.command(name="howmassive", description="Evaluate how massive an object is. EX: A rock")
async def howmassive(interaction: discord.Interaction, object: str):

    percent = random.randint(1, 100)
    if percent < 10:
        emoji = f"(dude its tiny how do you even see {object})"
    elif percent < 50:
        emoji = f"({object} is average size i dunno what ur talking about)"
    elif percent < 75:
        emoji = f"({object} is pretty large, but i know something thats bigger)"
    else:
        emoji = f"(holy moly! now thats MASSIVE!)\nAnd yk what else is massive??\nLLLOOOOWWWWWW-"
    result = f"**{object}** is **{percent}%** large.\n{emoji}"
    await interaction.response.send_message(result)


@bot.tree.command(name="howtall", description="Evaluate how tall a user is. Short kings together 🫶🙌💅")
async def howtall(interaction: discord.Interaction, user: discord.Member):
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    foot = random.randint(4, 9)
    inch = random.randint(0, 11)

    if foot < 6:
        text = "short kings together forever 💖💅🙌"
    else:
        text = "shut ur tall ass up 🤬🤬"

    result = f"**{user}** is {foot}'{inch}\"\n{text}"
    await interaction.response.send_message(result)

    if foot == 9 and inch == 11:
        user_id = str(interaction.user.id)
        ACHIEVEMENTS_FILE = "achievements.json"

        if os.path.exists(ACHIEVEMENTS_FILE):
            with open(ACHIEVEMENTS_FILE, "r") as f:
                achievements = json.load(f)
        else:
            achievements = {}

        user_achievements = achievements.setdefault(user_id, [])
        if "never_forget" not in user_achievements:
            user_achievements.append("never_forget")

            with open(ACHIEVEMENTS_FILE, "w") as f:
                json.dump(achievements, f, indent=4)

            await interaction.followup.send(
                "🏅 You unlocked an achievement: <:neverforget:1366951784630976613> **Never Forget**"
            )


@bot.tree.command(name="howautistic", description="Command to check someones 'tism.")
async def howautistic(interaction: discord.Interaction, user: discord.Member):
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    percent = random.randint(1, 100)
    if percent < 10:
        emoji = f"🔥"
    elif percent < 50:
        emoji = f"🤐"
    elif percent < 75:
        emoji = f"🧠"
    else:
        emoji = f"🧩"
    result = f"**{user}** is **{percent}%** autistic. {emoji}"
    await interaction.response.send_message(result)


@bot.tree.command(name="gayrate", description="how gay is the user")
async def gayrate(interaction: discord.Interaction, user: discord.Member):
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    # Decide percentage
    if user.id == 677321837985792021:
        percent = 0
    elif user.id in [1334240018541187073, 698163250403082261]:
        percent = 100
    else:
        percent = random.randint(1, 100)

    # Emoji based on level
    if percent < 10:
        emoji = "♀️"
    elif percent < 50:
        emoji = "🤫"
    elif percent < 75:
        emoji = "🤑"
    else:
        emoji = "🏳️‍🌈🫃"

    result = f"**{user}** is **{percent}%** gay {emoji}"

    # Respond first to avoid webhook timeout
    await interaction.response.send_message(result)

    # Optional: Check for achievement
    if percent == 100:
        user_id = str(interaction.user.id)
        ACHIEVEMENTS_FILE = "achievements.json"

        if os.path.exists(ACHIEVEMENTS_FILE):
            with open(ACHIEVEMENTS_FILE, "r") as f:
                achievements = json.load(f)
        else:
            achievements = {}

        user_achievements = achievements.setdefault(user_id, [])
        if "confirmed_gay" not in user_achievements:
            user_achievements.append("confirmed_gay")

            with open(ACHIEVEMENTS_FILE, "w") as f:
                json.dump(achievements, f, indent=4)

            await interaction.followup.send(
                "🏅 You unlocked an achievement: <:gay:1355562085244862571> **Confirmed Gay**"
            )


# /ddededodediamante command
@bot.tree.command(name="ddededodediamante", description="how ddededodediamantely is the person")
async def ddededodediamante(interaction: discord.Interaction, user: discord.Member):
    # Check interaction settings
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    percent = random.randint(1, 100)
    if {user} == "<@694587798598058004>":
        emoji = "*actually ddededodediamante!?*"
    elif percent < 10:
        emoji = "*they will never be like him*"
    elif percent < 50:
        emoji = "*bad copycat*"
    elif percent < 90:
        emoji = "*they **MIGHT** be ddededodediamante but idk*"
    else:
        emoji = "*thats ddededodediamante trust*"
    print(f"User: {user}")
    print(f"User to compare: <@694587798598058004>")
    result = f"**{user}** is **{percent}%** a ddededodediamante. {emoji}"
    await interaction.response.send_message(result)

# /shit command
@bot.tree.command(name="shit", description="take a FAT SHIT on someones message")
async def shit(interaction: discord.Interaction, user: discord.Member):
    # Check interaction settings
    interaction_check = await check_interactions(interaction.user, user)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    result = f"**{interaction.user}** took a **fat shit** on {user}'s message.\n-# This command is ass dw im working on a revamp 💔"
    await interaction.response.send_message(result)


@bot.tree.command(name="quote", description="Generate a quote image with your avatar and text.")
async def quote(interaction: discord.Interaction, text: str):
    try:
        await interaction.response.defer()

        # Use the user who ran the command
        target_user = interaction.user

        # Get avatar
        avatar_url = target_user.avatar.url if target_user.avatar else None
        if avatar_url:
            avatar_response = requests.get(avatar_url)
            avatar_image = Image.open(BytesIO(avatar_response.content)).convert("RGBA")
            avatar_image = avatar_image.resize((400, 400))
        else:
            await interaction.followup.send("No avatar found.")
            return

        # Create base image
        img_width, img_height = 1200, 630
        base_img = Image.new("RGB", (img_width, img_height), color="black")
        base_img.paste(avatar_image, (50, (img_height - 400) // 2), mask=avatar_image)

        # Draw text
        draw = ImageDraw.Draw(base_img)
        font_path = "arial.ttf"
        font_small = ImageFont.truetype(font_path, 36)
        font_mini = ImageFont.truetype(font_path, 20)

        max_width = img_width - 550
        text_size = 72
        while text_size > 20:
            font_large = ImageFont.truetype(font_path, text_size)
            lines = []
            words = text.split()
            current_line = ""

            for word in words:
                test_line = f"{current_line} {word}".strip()
                text_width, _ = draw.textbbox((0, 0), test_line, font=font_large)[2:4]
                if text_width <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            line_height = font_large.getbbox("A")[3]
            total_height = line_height * len(lines)

            if total_height <= img_height - 150:
                break

            text_size -= 2

        y_offset = (img_height - total_height) // 2
        text_x_start = 500
        for line in lines:
            text_width = draw.textbbox((0, 0), line, font=font_large)[2]
            x_offset = (text_x_start + (max_width - text_width) // 2)
            draw.text((x_offset, y_offset), line, font=font_large, fill="white")
            y_offset += line_height

        username_text = f"- {target_user.name}"
        username_width = draw.textbbox((0, 0), username_text, font=font_small)[2]
        username_x = (text_x_start + (max_width - username_width) // 2)
        draw.text((username_x, y_offset + 20), username_text, font=font_small, fill="white")

        draw.text((img_width - 250, img_height - 50), "IkeBot Quote Generator", font=font_mini, fill="grey")

        output_buffer = BytesIO()
        base_img.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        print(f"Quote made; {text}")
        await interaction.followup.send(file=discord.File(fp=output_buffer, filename="quote.png"))

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")


# /status command
@bot.tree.command(name="status", description="Get the SnowShare server status")
async def status(interaction: discord.Interaction	):
	await interaction.response.send_message("status page https://ikelene.betteruptime.com")


@bot.tree.command(name="ship", description="Calculate how well a relationship would work between two users.")
async def ship(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    # Check interaction settings
    interaction_check = await check_interactions(interaction.user, user1, user2)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    try:
        # Defer the response to avoid timeouts
        await interaction.response.defer()

        # Name similarity (0-100%)
        name_sim = int(difflib.SequenceMatcher(None, user1.name.lower(), user2.name.lower()).ratio() * 100)

        # Profile picture similarity (0-100%)
        pfp_sim = 100 if user1.avatar and user2.avatar and user1.avatar.url == user2.avatar.url else random.randint(10,
                                                                                                                    90)

        # Bio similarity (0-100%)
        about1 = user1.public_flags if user1.public_flags else "No bio"
        about2 = user2.public_flags if user2.public_flags else "No bio"
        bio_sim = int(difflib.SequenceMatcher(None, str(about1),
                                              str(about2)).ratio() * 100) if about1 != "No bio" and about2 != "No bio" else random.randint(
            10, 90)

        # Final love percentage (weighted average)
        final_percent = int((name_sim * 0.4) + (pfp_sim * 0.3) + (bio_sim * 0.3))

        # Generate progress bar
        progress_bar = "<a:bar_begin_pink:1348113893502750831>"  # Start emoji
        filled = int(final_percent / 10)  # Number of filled segments
        empty = 10 - filled  # Number of empty segments

        progress_bar += "<a:bar_full_pink:1348113914944294975>" * filled
        progress_bar += "<a:bar_empty:1348113937928945756>" * empty

        if filled == 10:
            progress_bar += "<a:bar_end_pink:1348113953409990677>"  # Full end
        else:
            progress_bar += "<a:bar_end:1348114002684936203>"  # Empty end

        # Create the shipping image
        img_width, img_height = 1280, 720
        ship_image = Image.new("RGB", (img_width, img_height), (0, 0, 0))

        # Load and resize user avatars
        user1_pfp = requests.get(user1.avatar.url).content
        user2_pfp = requests.get(user2.avatar.url).content

        user1_img = Image.open(BytesIO(user1_pfp)).convert("RGBA").resize((400, 400))
        user2_img = Image.open(BytesIO(user2_pfp)).convert("RGBA").resize((400, 400))

        # Load the plus sign image
        plus_img = Image.open("plusImage.png").convert("RGBA").resize((200, 200))

        # Paste images onto the canvas
        ship_image.paste(user1_img, (140, 160), mask=user1_img)
        ship_image.paste(user2_img, (740, 160), mask=user2_img)
        ship_image.paste(plus_img, (540, 260), mask=plus_img)

        # Save the image to a buffer
        image_buffer = BytesIO()
        ship_image.save(image_buffer, format="PNG")
        image_buffer.seek(0)

        # Create the embed
        embed = discord.Embed(
            title="💖 Love Compatibility Test 💖",
            description=f"**{user1.mention}** + **{user2.mention}** = **{final_percent}%** compatibility!\n\n"
                        f"🔠 **Name Similarity:** {name_sim}%\n"
                        f"🖼 **Profile Picture Similarity:** {pfp_sim}%\n"
                        f"📜 **Bio Similarity:** {bio_sim}%\n\n"
                        f"{progress_bar} ** - {final_percent}%**",
            color=discord.Color.pink()
        )

        embed.set_image(url="attachment://ship_image.png")
        embed.set_footer(text="Made with 💖 by IkeBot")

        # Send the embed with the image
        await interaction.followup.send(embed=embed, file=discord.File(image_buffer, filename="ship_image.png"))

    except Exception as e:
        await interaction.followup.send(f"An error occurred: {e}")


@bot.tree.command(name="antibodies", description="Test a user's blood sample for antibodies.")
async def antibodies(interaction: discord.Interaction, patient: discord.Member):
    # Check interaction settings
    interaction_check = await check_interactions(interaction.user, patient)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    # First, defer the response to let Discord know the bot is processing
    await interaction.response.defer()

    # Send the initial "loading" message
    loading_msg = await interaction.followup.send(
        f"<a:loading:1348013386209955933> Testing {patient.mention}'s blood sample..."
    )

    # Simulate processing delay
    await asyncio.sleep(2)

    # Generate random antibody percentage
    antibody_percent = random.randint(0, 100)

    # Get the current date in the format "Month Year"
    date_str = datetime.now().strftime("%B %Y")  # Example: "March 2025"

    if antibody_percent < 10:
        emoji = "Don't go outside."
    elif antibody_percent < 50:
        emoji = "Wear a mask for your next date or you'll be sorry."
    elif antibody_percent < 80:
        emoji = "You're pretty okay to go outside and not get sick, but don't overdo it!"
    else:
        emoji = "You can go outside and take your pants off and you still wont be sick! Lucky you!"

    # Create embed
    embed = discord.Embed(
        title="🩸 COVID-19 Antibodies Report 🩸",
        description=f"🔬 Test lab location: **{interaction.guild.name}**\n\n"
                    f"🔤 Patient name: **{patient.mention}**\n\n"
                    f"📅 Date of COVID-19 test: **{date_str}**\n\n"
                    f"🧪 **Antibody Levels:** {antibody_percent}%\n\n"
                    f"Final Verdict: **{emoji}**",
        color=discord.Color.red()
    )

    embed.set_footer(text="Test conducted by IkeBot Laboratories™")

    # Edit the message to show the final results
    await loading_msg.edit(content="", embed=embed)


@bot.tree.command(name="8ball", description="Ask the Magic 8-Ball a question")
async def magic_8ball(interaction: discord.Interaction, question: str):
    responses = [
        "It is certain.",
        "Without a doubt.",
        "You may rely on it.",
        "Ask again later.",
        "Don't count on it.",
        "Very doubtful."
    ]
    answer = random.choice(responses)
    await interaction.response.send_message(f"🎱 Question: {question}\nAnswer: {answer}")


@bot.tree.command(name="rps", description="Play Rock, Paper, Scissors")
async def rock_paper_scissors(interaction: discord.Interaction, choice: str):
    choices = ["rock", "paper", "scissors"]
    bot_choice = random.choice(choices)
    if choice == bot_choice:
        result = "It's a tie!"
    elif (choice == "rock" and bot_choice == "scissors") or \
         (choice == "paper" and bot_choice == "rock") or \
         (choice == "scissors" and bot_choice == "paper"):
        result = "You win!"
    else:
        result = "You lose!"
    await interaction.response.send_message(f"🤖 Bot chose: {bot_choice}\n{result}")


@bot.tree.command(name="avatarfusion", description="Combine avatars of two users")
async def avatar_fusion(interaction: discord.Interaction, user1: discord.Member, user2: discord.Member):
    # Check interaction settings
    interaction_check = await check_interactions(interaction.user, user1, user2)
    if interaction_check:
        await interaction.response.send_message(interaction_check)
        return

    avatars = []
    for user in [user1, user2]:
        async with aiohttp.ClientSession() as session:
            async with session.get(user.avatar.url) as response:
                if response.status == 200:
                    avatars.append(Image.open(BytesIO(await response.read())))
                else:
                    await interaction.response.send_message(f"Couldn't fetch avatar for {user.display_name}")
                    return
    avatars = [avatar.resize((256, 256)) for avatar in avatars]
    fused_image = Image.blend(avatars[0], avatars[1], alpha=0.5)
    fused_image.save("fused_avatar.png")
    await interaction.response.send_message(file=discord.File("fused_avatar.png"))

    
@bot.tree.command(name="stats", description="Show bot stats or another user's stats")
@app_commands.describe(user="Optional user to check")
async def stats_command(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    user_id = str(user.id)
    guild_id = str(interaction.guild.id)

    user_data = stats["users"].get(user_id, {"messages": 0, "votes": 0})
    server_data = stats["servers"].get(guild_id, {"commands": 0})

    total_users = len(stats["users"])
    total_servers = len(bot.guilds)

    embed = discord.Embed(title=f"📊 Stats for {user.display_name}", color=discord.Color.blue())
    embed.add_field(name="🌐 Bot Stats", value=(
        f"**Servers:** {total_servers}\n"
        f"**Users:** {total_users}\n"
	f"**Version:** {VERSION}\n"
        f"**Commands Run (Global):** {stats['global_commands']}\n"
        f"**Commands Run (This Server):** {server_data['commands']}\n"
        f"[🔗 Vote Here](https://top.gg/bot/{BOT_ID})"
    ), inline=False)

    embed.add_field(name=f"👤 User Stats", value=(
        f"**Messages Sent:** N/A *(WIP)*\n" # {user_data['messages']}
        f"**Times Voted:** {user_data['votes']}"
    ), inline=False)

    icons = [ACHIEVEMENT_DATA[key]["emoji"] for key in achievements.get(user_id, []) if key in ACHIEVEMENT_DATA]
    if icons:
        embed.add_field(name="🏆 Achievements", value=" ".join(icons), inline=False)

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="achievements", description="Show your or another user's achievement list")
@app_commands.describe(user="Optional user to check")
async def achievements_command(interaction: discord.Interaction, user: discord.User = None):
    user = user or interaction.user
    user_id = str(user.id)

    unlocked = achievements.get(user_id, [])

    embed = discord.Embed(title=f"🏅 Achievements for {user.display_name}", color=discord.Color.gold())
    for key, data in ACHIEVEMENT_DATA.items():
        if key in unlocked:
            embed.add_field(name=f"{data['emoji']} {data['title']}", value=data['desc'], inline=False)

    if not unlocked:
        embed.description = "No achievements yet. Start using the bot!"

    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="vote", description="Get the link to vote for the bot on Top.gg")
async def vote_command(interaction: discord.Interaction):
    vote_link = f"https://top.gg/bot/{BOT_ID}/vote"
    embed = discord.Embed(
        title="🗳️ Vote for Me!",
        description=f"Support the bot by voting:\n[Click Here to Vote]({vote_link})\nAfter voting, use `/confirmvote` to receive your achievement badges!",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="confirmvote", description="Manually confirm you voted for the bot.")
async def confirm_vote(interaction: discord.Interaction):
    user_id = str(interaction.user.id)

    # Check top.gg API
    headers = {
        "Authorization": TOPGG_API_TOKEN
    }

    url = f"https://top.gg/api/bots/{bot.user.id}/check?userId={user_id}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status != 200:
                return await interaction.response.send_message(
                    "❌ Failed to check vote status from top.gg. Please try again later.",
                    ephemeral=True
                )

            data = await response.json()
            if not data.get("voted"):
                return await interaction.response.send_message(
                    "❌ You haven’t voted yet! Please vote at https://top.gg/bot/{bot_id}/vote before using this command.",
                    ephemeral=True
                )

    # Continue with your logic
    now = datetime.utcnow()
    vote_times[user_id] = now.isoformat()
    stats["users"].setdefault(user_id, {"messages": 0, "votes": 0})
    stats["users"][user_id]["votes"] += 1
    achievements.setdefault(user_id, [])
    if "voter" not in achievements[user_id]:
        achievements[user_id].append("voter")
    if "active_voter" not in achievements[user_id]:
        achievements[user_id].append("active_voter")
    save_all()
    await interaction.response.send_message(
        "✅ Your vote has been confirmed via top.gg! You've received the voter and active voter achievements.",
        ephemeral=True
    )


@bot.event
async def on_message(message: discord.Message):
    # Ignore bot messages
    if message.author.bot:
        return

    # Check if the bot was mentioned directly
    BOT_ID = 1333250511729852416
    BOT_MENTION_TAGS = [f"<@{BOT_ID}>", f"<@!{BOT_ID}>"]
    if not any(tag in message.content for tag in BOT_MENTION_TAGS):
        return

    # Make sure it's a reply to something
    if not message.reference:
        return

    try:
        channel = message.channel
        try:
            replied_message = await channel.fetch_message(message.reference.message_id)
        except discord.NotFound:
            await message.channel.send("⚠️ I couldn't access the replied message.")
            return

        target_user = replied_message.author
        quote_text = replied_message.content.strip()

        # 🔒 Check interaction settings
        interaction_check = await check_interactions(message.author, target_user)
        if interaction_check:
            await message.channel.send(interaction_check)
            return

        # Handle empty-looking messages
        if not quote_text or quote_text.isspace():
            if replied_message.embeds:
                quote_text = "[Embedded content]"
            elif replied_message.attachments:
                quote_text = "[Attachment]"
            elif replied_message.stickers:
                quote_text = "[Sticker]"
            elif replied_message.clean_content.strip():
                quote_text = replied_message.clean_content.strip()
            else:
                await message.channel.send("⚠️ I can't quote an empty message.")
                return

        # Load avatar
        avatar_url = target_user.avatar.url if target_user.avatar else None
        if avatar_url:
            avatar_response = requests.get(avatar_url)
            avatar_image = Image.open(BytesIO(avatar_response.content)).convert("RGBA")
            avatar_image = avatar_image.resize((400, 400))
        else:
            await message.channel.send("⚠️ Could not retrieve avatar.")
            return

        # Create quote image
        img_width, img_height = 1200, 630
        base_img = Image.new("RGB", (img_width, img_height), color="black")
        base_img.paste(avatar_image, (50, (img_height - 400) // 2), mask=avatar_image)

        draw = ImageDraw.Draw(base_img)
        font_path = "arial.ttf"
        font_small = ImageFont.truetype(font_path, 36)
        font_mini = ImageFont.truetype(font_path, 20)

        max_width = img_width - 550
        text_size = 72
        while text_size > 20:
            font_large = ImageFont.truetype(font_path, text_size)
            lines = []
            words = quote_text.split()
            current_line = ""

            for word in words:
                test_line = f"{current_line} {word}".strip()
                text_width, _ = draw.textbbox((0, 0), test_line, font=font_large)[2:4]
                if text_width <= max_width:
                    current_line = test_line
                else:
                    lines.append(current_line)
                    current_line = word

            if current_line:
                lines.append(current_line)

            line_height = font_large.getbbox("A")[3]
            total_height = line_height * len(lines)

            if total_height <= img_height - 150:
                break

            text_size -= 2

        y_offset = (img_height - total_height) // 2
        text_x_start = 500
        for line in lines:
            text_width = draw.textbbox((0, 0), line, font=font_large)[2]
            x_offset = (text_x_start + (max_width - text_width) // 2)
            draw.text((x_offset, y_offset), line, font=font_large, fill="white")
            y_offset += line_height

        username_text = f"- {target_user.name}"
        username_width = draw.textbbox((0, 0), username_text, font=font_small)[2]
        username_x = (text_x_start + (max_width - username_width) // 2)
        draw.text((username_x, y_offset + 20), username_text, font=font_small, fill="white")

        draw.text((img_width - 250, img_height - 50), "IkeBot Quote Generator", font=font_mini, fill="grey")

        output_buffer = BytesIO()
        base_img.save(output_buffer, format="PNG")
        output_buffer.seek(0)

        await message.channel.send(file=discord.File(fp=output_buffer, filename="quote.png"))

    except Exception as e:
        await message.channel.send(f"❌ An error occurred: `{e}`")
        print(f"Quote error: {e}")


# track active players by user id
players: dict[int, dict] = {}

# sill lil music player
@bot.tree.command(name="music", description="Play music from a playlist")
@app_commands.describe(playlist="Pick a playlist")
@app_commands.choices(playlist=[
    app_commands.Choice(name=option, value=option) for option in PLAYLIST_OPTIONS
])
async def pm_music(interaction: discord.Interaction, playlist: str):
    user = interaction.user
    vc_channel = user.voice.channel if user.voice else None
    if not vc_channel:
        return await interaction.response.send_message(f"{WARNING_EMOJI} you need to be in a voice channel!", ephemeral=True)
    if vc_channel.guild.voice_client:
        return await interaction.response.send_message(f"{ERROR_EMOJI} i'm already in a vc here!", ephemeral=True)

    playlist_var_name = playlist.upper() + "_PLAYLIST"
    music = globals().get(playlist_var_name)

    if not music:
        return await interaction.response.send_message(f"{ERROR_EMOJI} playlist not found!", ephemeral=True)

    vc: discord.VoiceClient = await vc_channel.connect()

    prev_btn = Button(label="⏮ previous", style=discord.ButtonStyle.primary)
    next_btn = Button(label="⏭ skip", style=discord.ButtonStyle.danger)
    view = View(timeout=None)
    view.add_item(prev_btn)
    view.add_item(next_btn)

    state = {
        "vc": vc,
        "text_channel": interaction.channel,
        "starter_id": user.id,
        "view": view,
        "stop": False,
        "song_index": 0,
        "action": None,
        "music": music,
        "playlist_name": playlist.upper()
    }
    players[user.id] = state

    async def prev_cb(i: discord.Interaction):
        if i.user.id != state["starter_id"]:
            return await i.response.send_message(f"{WARNING_EMOJI} only the command initiator can use this!", ephemeral=True)
        state["song_index"] = (state["song_index"] - 1) % len(state["music"])
        state["action"] = "prev"
        state["vc"].stop()
        await i.response.defer()
    prev_btn.callback = prev_cb

    async def next_cb(i: discord.Interaction):
        if i.user.id != state["starter_id"]:
            return await i.response.send_message(f"{WARNING_EMOJI} only the command initiator can use this!", ephemeral=True)
        state["song_index"] = (state["song_index"] + 1) % len(state["music"])
        state["action"] = "skip"
        state["vc"].stop()
        await i.response.defer()
    next_btn.callback = next_cb

    def build_embed():
        embed = discord.Embed(title=f"**__{playlist} Playlist__**", color=discord.Color.green())
        lines = []
        for idx, path in enumerate(state["music"]):
            name = os.path.splitext(os.path.basename(path))[0]
            if idx == state["song_index"]:
                lines.append(f"{MUSIC_EMOJI} **{name} -- now playing**")
            elif idx == (state["song_index"] + 1) % len(state["music"]):
                lines.append(f"{NEXTUP_EMOJI} *{name} -- next up*")
            else:
                lines.append(f"{DOT_EMOJI} {name}")
        embed.description = "\n".join(lines)
        return embed

    await interaction.response.send_message(
        f"{DONE_EMOJI} joined **{vc_channel.name}** and starting music from **{playlist}**!",
        ephemeral=False
    )
    playlist_msg = await interaction.channel.send(embed=build_embed(), view=view)
    state["message"] = playlist_msg

    async def player_loop():
        while not state["stop"]:
            idx = state["song_index"]
            song = state["music"][idx]
            state["vc"].play(FFmpegPCMAudio(song))
            await state["message"].edit(embed=build_embed(), view=view)
            while state["vc"].is_playing():
                await asyncio.sleep(1)
                member = vc_channel.guild.get_member(state["starter_id"])
                if not member or not member.voice or member.voice.channel != vc_channel:
                    state["vc"].stop()
                    state["stop"] = True
                    break
            if state["stop"]:
                break
            if state["action"]:
                state["action"] = None
            else:
                state["song_index"] = (state["song_index"] + 1) % len(state["music"])

        if state["vc"].is_connected():
            await state["vc"].disconnect()
        view.stop()
        del players[state["starter_id"]]
        await state["text_channel"].send(f"{WARNING_EMOJI} music stopped (you left)")

    bot.loop.create_task(player_loop())


@tasks.loop(seconds=30)
async def check_topgg_votes():
    # Handle vote expiry only
    to_remove = []
    for user_id, vote_time in vote_times.items():
        vote_datetime = datetime.fromisoformat(vote_time)
        if datetime.utcnow() > vote_datetime + timedelta(hours=24):
            if "active_voter" in achievements.get(user_id, []):
                achievements[user_id].remove("active_voter")
                try:
                    user = await bot.fetch_user(int(user_id))
                    await user.send(f"🔔 Your Active Voter badge expired. You can vote again here: https://top.gg/bot/{BOT_ID}")
                except:
                    pass
            to_remove.append(user_id)

    for user_id in to_remove:
        del vote_times[user_id]

    save_all()

@tasks.loop(seconds=15)
async def watch_dead_chat(channel: discord.TextChannel):
    try:
        settings = await load_deadchat_settings()
        key = str(channel.id)
        if key not in settings:
            return

        s = settings[key]
        if not isinstance(s, dict) or "time_limit" not in s:
            del settings[key]
            await save_deadchat_settings(settings)
            return

        tl = s["time_limit"]
        time_limit = timedelta(seconds=float(tl))

        lmt_iso = s.get("last_message_time")
        if not lmt_iso:
            msgs = [m async for m in channel.history(limit=100) if not m.author.bot]
            if not msgs:
                return
            lmt = msgs[0].created_at
            s["last_message_time"] = lmt.isoformat()
            await save_deadchat_settings(settings)
        else:
            lmt = datetime.fromisoformat(lmt_iso)

        if lmt.tzinfo is None:
            lmt = lmt.replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)

        notified = s.get("notified", False)

        # dead notification
        if not notified and now - lmt > time_limit:
            await channel.send(embed=discord.Embed(
                title="dead chat stats",
                description=(
                    f"this chat has been dead since <t:{int(lmt.timestamp())}:F>\n"
                    f"the last message was sent <t:{int(lmt.timestamp())}:R>"
                ),
                color=discord.Color.red()
            ))
            s["notified"] = True
            await save_deadchat_settings(settings)
            return

        # revival notification (only once per dead period)
        msgs = [m async for m in channel.history(limit=100) if not m.author.bot]
        if notified and msgs and msgs[0].created_at.replace(tzinfo=timezone.utc) > lmt:
            s["last_message_time"] = msgs[0].created_at.isoformat()
            s["notified"] = False
            await save_deadchat_settings(settings)
            await channel.send(embed=discord.Embed(
                title="chat revived!",
                description="the chat was successfully revived!",
                color=discord.Color.green()
            ))
            return

    except Exception as e:
        print(f"error in watch_dead_chat: {e}")
        try:
            await channel.send(embed=discord.Embed(
                title="error",
                description=f"an error occurred while processing dead chat stats. {ERROR_EMOJI}\n\nerror: {e}",
                color=discord.Color.red()
            ))
        except:
            pass

async def load_deadchat_settings():
    try:
        data = open('deadchatsettings.json','r').read().strip()
        if not data:
            return {}
        settings = json.loads(data)
        # convert stored seconds to int/float, leave for watch loop to turn into timedelta
        return settings
    except Exception:
        if os.path.exists('deadchatsettings.json'):
            os.remove('deadchatsettings.json')
        return {}

async def save_deadchat_settings(settings):
    try:
        # ensure time_limit stored as seconds
        for s in settings.values():
            tl = s.get("time_limit")
            if isinstance(tl, timedelta):
                s["time_limit"] = tl.total_seconds()
        with open('deadchatsettings.json','w') as f:
            json.dump(settings, f, indent=4)
    except Exception as e:
        print(f"error saving settings: {e}")
