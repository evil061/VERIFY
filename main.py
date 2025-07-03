import discord
from discord.ext import commands
import asyncio
import random
from dotenv import load_dotenv
import csv
import os
import B

load_dotenv()
TOKEN = os.getenv('TOKEN')

B.b()

intents = discord.Intents.default()
intents.bans = True
intents.dm_messages = True
intents.dm_reactions = True
intents.dm_typing = True
intents.emojis = True
intents.emojis_and_stickers = True
intents.guild_messages = True
intents.guild_reactions = True
intents.guild_scheduled_events = True
intents.guild_typing = True
intents.guilds = True
intents.integrations = True
intents.invites = True
intents.messages = True # `message_content` is required to get the content of the messages
intents.reactions = True
intents.typing = True
intents.voice_states = True
intents.webhooks = True
intents.members = True  # Enable the members intent
intents.message_content = True  # Enable message content intent if needed
client = commands.Bot(command_prefix='--', intents=intents)
client.remove_command('help')
# Dictionary to store server configurations (will be loaded from CSV)
server_configs = {}

def load_server_configs():
    """Load server configurations from CSV file"""
    if not os.path.exists('server_config.csv'):
        # Create file with headers if it doesn't exist
        with open('server_config.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['server_id', 'prefix', 'channel_id'])
    else:
        # Load existing configurations
        with open('server_config.csv', 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                server_configs[int(row['server_id'])] = {
                    'prefix': row['prefix'],
                    'channel_id': int(row['channel_id'])
                }

def save_server_config(server_id, prefix, channel_id):
    """Save server configuration to CSV file"""
    configs = []
    # Read existing configurations
    if os.path.exists('server_config.csv'):
        with open('server_config.csv', 'r') as file:
            reader = csv.DictReader(file)
            configs = list(reader)

    # Update or add new configuration
    updated = False
    for config in configs:
        if int(config['server_id']) == server_id:
            config['prefix'] = prefix
            config['channel_id'] = channel_id
            updated = True
            break

    if not updated:
        configs.append({
            'server_id': server_id,
            'prefix': prefix,
            'channel_id': channel_id
        })

    # Write all configurations back to file
    with open('server_config.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['server_id', 'prefix', 'channel_id'])
        writer.writeheader()
        writer.writerows(configs)

    # Update the in-memory dictionary
    server_configs[server_id] = {
        'prefix': prefix,
        'channel_id': channel_id
    }

@client.event
async def on_ready():
    await client.wait_until_ready()
    print("Logged in as {}".format(client.user.name))
    await client.change_presence(activity=discord.Game("VERIFICATION"))
    # Load server configurations when bot starts
    load_server_configs()

@client.event
async def on_message(message):
    # Ignore messages from the bot itself
    if message.author.id == client.user.id:
        return

    # If message is sent in channel 1360963446165995530, send message content and user to channel 1360963446165995533
    if message.channel.id == 1360963446165995530:
        target_channel = client.get_channel(1302143379387187233)
        if target_channel:
            # Forward text content
            if message.content:
                await target_channel.send(f" {message.author}: {message.content}")
            # Forward attachments (images, videos, etc.)
            if message.attachments:
                for attachment in message.attachments:
                    await target_channel.send(f"{message.author} sent an attachment:", file=await attachment.to_file())

    # Check if the bot is mentioned
    if client.user.mentioned_in(message):
        await message.channel.send(f"Hello {message.author.mention}, Use --help for more")

    # Allow setup command to work
    await client.process_commands(message)

    # Check if the server has a configuration
    if message.guild.id in server_configs:
        config = server_configs[message.guild.id]
        # Only respond if the message is in the stored verification channel
        if message.channel.id != config['channel_id']:
            return

        if message.content.upper().startswith('VERIFY'):
            answer = random.randint(1000, 9999)
            embed = discord.Embed(color=0x00ff00)
            embed.title = "VERIFICATION" 
            embed.description = '**Code:** {}\n\n{}\nRE ENTER THE VERIFICATION CODE HERE \n\n CODE GENERATED FROM CHANNEL <#{}>\nFROM SERVER `{}`'.format(answer, message.author.mention, message.channel.id, message.guild.name)
            channel = await message.author.create_dm()
            await channel.send(embed=embed)
            await message.channel.send("{} I HAVE SENT YOU THE CODE ".format(message.author.mention))
            await message.channel.send(embed=embed)

            def is_correct(m):
                return m.author == message.author and m.content.isdigit()

            try:
                guess = await client.wait_for('message', check=is_correct, timeout=120.0)
            except asyncio.TimeoutError:
                embed = discord.Embed(color=0x00ff00)
                embed.title = "VERIFICATION" 
                embed.description = '{} \nYOU TOOK TOO LONG TO RESPOND'.format(message.author.mention)
                await channel.send(embed=embed)
                embed.description = '{} \nVERIFICATION CANCELED'.format(message.author.mention)
                await message.channel.send(embed=embed)
                return

            if int(guess.content) == answer:
                role = discord.utils.get(message.guild.roles, name='verified')
                if role is not None:
                    await message.author.add_roles(role)
                    embed = discord.Embed(color=0x00ff00)
                    embed.title = ":white_check_mark: SUCCESSFUL" 
                    embed.description =  "{} CONGRATULATIONS YOU ARE VERIFIED SUCCESSFULLY!".format(message.author.mention)
                    await channel.send(embed=embed)
                    await message.channel.send(embed=embed)
                else:
                    embed = discord.Embed(color=0xff0000)
                    embed.title = ":warning: ERROR!!" 
                    embed.description = "{}  The 'verified' role was not found on the server.".format(message.author.mention)
                    await channel.send(embed=embed)
                    await message.channel.send(embed=embed)
            else:
                embed = discord.Embed(color=0xff0000)
                embed.title = ":warning: ERROR!!" 
                embed.description = "{} WRONG CODE THE CODE WAS  `{}`.\nTYPE VERIFY IN <#{}> CHANNEL TO GET YOUR VERIFICATION CODE AGAIN".format(message.author.mention, answer, message.channel.id)
                await channel.send(embed=embed)
                await message.channel.send(embed=embed)

@client.command()
async def setup(ctx, channel: discord.TextChannel):
    """```command uses !!setup <channel> to set the verification channel```"""
    if ctx.guild is None:
        await ctx.send("This command can only be used in a server.")
        return

    if not isinstance(channel, discord.TextChannel):
        await ctx.send("Invalid channel specified.")
        return

    try:
        # Save the server configuration to CSV
        save_server_config(ctx.guild.id, ctx.prefix, channel.id)
        await ctx.send(f"Verification setup complete! Channel set to {channel.mention}")
    except Exception as e:
        await ctx.send(f"Error setting up verification: {str(e)}")

@client.command()
async def help(ctx):
    """Custom help command that sends an embed with available commands."""
    embed = discord.Embed(
        title="Help Command",
        description="Here are the available commands:",
        color=0x00ff00  # Green color
    )
    # Add fields for each command
    embed.add_field(
        name="--setup <channel>",
        value="Set the verification channel for the server.",
        inline=False
    )
    embed.add_field(
        name="--help",
        value="Show this help message.",
        inline=False
    )
    embed.add_field(
        name="Mention the bot",
        value="The bot will reply when mentioned.",
        inline=False
    )
    embed.add_field(
        name="VERIFY",
        value="Start the verification process in the designated channel.",
        inline=False
    )
    embed.add_field(
        name="Support server",
        value="Follow the link to join the support server."+ "\n" +"(link)[https://discord.gg/AuM7eBWAwe]",
        inline=False
    )
    # Set footer (optional)
    embed.set_footer(text="Bot created by EVIL BOY")
    # Send the embed
    await ctx.send(embed=embed)


client.run(TOKEN)
