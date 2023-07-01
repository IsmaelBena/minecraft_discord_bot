import os
from dotenv import load_dotenv
import json
import discord
from discord.ext import commands
from mc_server_controller import MC_Server_Controller, ServerState

# get env vars
load_dotenv()
BOT_TOKEN = os.environ.get("BOT_TOKEN")
MC_SERVER_DIR = os.environ.get("MC_SERVER_DIR")
MC_SERVER_START_SCRIPT = os.environ.get("MC_SERVER_START_SCRIPT")
ELEVATED_PRIVILEGES_STR = os.environ.get("ELEVATED_PRIVILEGES") 
print(ELEVATED_PRIVILEGES_STR)
ELEVATED_PRIVILEGES = [int(i) for i in ELEVATED_PRIVILEGES_STR.split(",")]


intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents)

# 
MCSC = MC_Server_Controller(MC_SERVER_DIR, MC_SERVER_START_SCRIPT)

# get list of commands for the help command
with open('./help.json', 'r') as file:
    help_data = json.load(file)

@bot.event
async def on_ready():
    print('Logged on as {0}!'.format(bot.user))
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over you"))

@bot.command()
async def ping(ctx):
    print('ping recieved from {0}'.format(ctx.author))
    await ctx.channel.send("```\npong\n```")
    print('responded with pong in {0}'.format(ctx.channel))

bot.remove_command("help")
@bot.command()
async def help(ctx, *args):
    print('{0} asked for help'.format(ctx.author))
    if len(args) < 1:
        helpMsg = '================== All Commands =================='     
        for command in help_data:
            helpMsg += f"\n + {command['command']} {command['example']}"
            if "args" in command:
                helpMsg += f" (Use [!help {command['command']}] to see all arguments)"
            if "aliases" in command:
                helpMsg += f":\n\t - Aliases:"
                for alias in command["aliases"]:
                    helpMsg += f" [{alias}]"
            helpMsg += f":\n\t - {command['desc']}\n"
        helpMsg += "=================================================="
        await ctx.channel.send(f"```{helpMsg}```")
    else:
        for command in help_data:
            if (args[0] == command['command'] or ('aliases' in command and args[0] in command['aliases'])):
                helpMsg = f"================ Help: {command['command']} ================"
                bottomBannerLength = len(helpMsg) - 32
                for arg in command['args']:
                    helpMsg += f"\n + {arg['arg']} {arg['example']}:"
                    if "aliases" in arg:
                        helpMsg += f":\n\t - Aliases:"
                        for alias in arg["aliases"]:
                            helpMsg += f" [{alias}]"
                    helpMsg += f":\n\t - {arg['desc']}\n"
                helpMsg += "================================".ljust(bottomBannerLength, '=')
                await ctx.channel.send(f"```{helpMsg}```")
                break
        
@bot.command()
async def mc(ctx, *args):
    if len(args) < 1:
        await ctx.channel.send("```\nNo args given\n```")
    else:
        if (args[0].lower() == "start"):
            await mcStart(ctx.channel)
        elif (args[0].lower() == "stop"):
            await mcStop(ctx.channel)
        elif (args[0].lower() == "status"):
            await mcStatus(ctx.channel)
        elif (args[0].lower() == "info"):
            await mcInfo(ctx.channel)
        elif (args[0].lower() == "op"):
            await mcOP(ctx.channel, args[1])
        elif (args[0].lower() == "clearweather"):
            await mcWeatherClear(ctx.channel)

async def mcStart(channel):
    if MCSC.server_state != ServerState.OFF:
        await channel.send("```\nServer is currently not off\n```")
    else:
        await MCSC.start(channel)
        await bot.change_presence(activity=discord.Game(name="Minecraft Server Management"))

async def mcStop(channel):
    if MCSC.server_state != ServerState.ON:
        await channel.send("```\nServer is not currently on so it cannot shutdown\n```")
    else:
        await MCSC.stop(channel)
        await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="over you"))

async def mcStatus(channel):
    print("server status")
    await MCSC.status(channel)

async def mcInfo(channel):
    print("server info")
    await MCSC.getInfo(channel)

async def mcOP(channel, target):
    if ctx.author.id in ELEVATED_PRIVILEGES:
        print(f"Attempting to OP {target}")
        await MCSC.op(channel, target)
    else:
        await ctx.channel.send(f"```\nYou don't have the permission to do that {ctx.author}\n```")

@bot.command()
async def shutdown_pc(ctx):
    if ctx.author.id in ELEVATED_PRIVILEGES:
        await ctx.channel.send("```\nServer PC is now shutting down.\n```")
        os.system("shutdown /s /t 10 /c \"Discord bot is turning off this pc\"")
    else:
        await ctx.channel.send(f"```\nYou don't have the permission to do that {ctx.author}\n```")
        print(ctx)

bot.run(BOT_TOKEN)