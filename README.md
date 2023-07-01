# Minecraft Discord Bot
A discord bot used to manage a minecraft server that is being hosted local to the bot.

Use !help to see commands.

Currently Supports:
- turning on/off server
- shutting down host pc
- checking servers status and info

In order for the bot to run you first need to create a .env file and file it with the following

```
# Bot Token
BOT_TOKEN = 
# Root directory of the minecraft server. e.g. C:\\Users\\Games\\Minecraft-Server
MC_SERVER_DIR = 
# File used to run the server. Default is start.bat
MC_SERVER_START_SCRIPT = start.bat
# Array of discord IDs of users who can shutdown the host machine and op users. Insert discord IDs seperated by commas without spaces, format: ELEVATED_PRIVILEGES = xxxxxxxxxxxxxx,xxxxxxxxxxxxxxxxxxx,xxxxxxxxxxxxxxxx
ELEVATED_PRIVILEGES = 
```
