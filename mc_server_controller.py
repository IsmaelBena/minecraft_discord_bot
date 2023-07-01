"""
Use !mc to access commands here.

Boot up server:            [!mc start]
Shutdown server:           [!mc stop/shutdown]
Check server status with:  [!mc status]
Check server info with:    [!mc info]

"""
from enum import Enum
import urllib.request
from subprocess import Popen, PIPE, CREATE_NEW_CONSOLE
import os
import time
import aiomcrcon
from jproperties import Properties
import discord
import json

class ServerState(Enum):
    ON = 1
    OFF = 2
    STARTING = 3
    STOPPING = 4

class MC_Server_Controller:

    def __init__(self, server_dir, server_start_script):
        print("MC server controller created")
        self.server_state = ServerState.OFF
        self.external_ipv4 = urllib.request.urlopen('https://api.ipify.org/').read().decode('utf8')
        self.server_dir = str(server_dir)
        self.server_start_script = str(server_start_script)
        self.update_server_config()

    def update_server_config(self):        
        server_configs = Properties()
        print(self.server_dir)
        with open(f'{self.server_dir}\\server.properties', 'rb') as config_file:
            server_configs.load(config_file)
        
        # get server name, ip, port for users
        self.world_name = server_configs.get("level-name").data
        self.server_port = server_configs.get("query.port").data
        self.difficulty = server_configs.get("difficulty").data
        self.hardcore = server_configs.get("hardcore").data
        self.gamemode = server_configs.get("gamemode").data

        self.boot_time_manager()

        #get rcon details
        self.rcon_port = server_configs.get("rcon.port").data
        self.rcon_password = server_configs.get("rcon.password").data

    def boot_time_manager(self, read=True, newVal=0):
        if read:
            try:
                with open(f'{self.server_dir}\\server_boot_time.json', 'r') as file:
                    print("existing file read")
                    self.boot_times_data = json.load(file)
                    print("existing file loaded")
                    self.boot_times = self.boot_times_data['boot_times']
                    print("existing file converted")
                self.average_boot_time = int(sum(self.boot_times) / float(len(self.boot_times)))
            except:
                with open(f'{self.server_dir}\\server_boot_time.json', 'w+') as file:
                    self.boot_times_data = {
                        'boot_times': []
                    }
                    json.dump(self.boot_times_data, file)
                    self.boot_times = self.boot_times_data['boot_times']
                self.average_boot_time = 0
            print(self.boot_times_data)
            print(self.boot_times)

        else:
            print("updating boot times")
            self.boot_times_data['boot_times'].append(newVal)
            print("data appended", self.boot_times_data['boot_times'])
            self.boot_times = self.boot_times_data['boot_times']
            print("local array appended", self.boot_times)
            try:
                self.average_boot_time = int(sum(self.boot_times) / float(len(self.boot_times)))
                print("new average", self.average_boot_time)
            except:
                print("can't divide?")
            with open(f'{self.server_dir}\\server_boot_time.json', 'w') as file:
                json.dump(self.boot_times_data, file)

    async def start(self, channel):
        try:
            p = Popen(['start', 'cmd', '/C', self.server_start_script], cwd=self.server_dir, shell=True)
            self.server_state = ServerState.STARTING
            loadingMsg = await channel.send("```\nMinecraft server is booting up :)\n```")
            time.sleep(1)
            p.terminate()
            current_boot_time = 0
            print(self.rcon_port, self.rcon_password)
            self.client = aiomcrcon.Client(self.external_ipv4, self.rcon_port, self.rcon_password)
        except:
            self.server_state = ServerState.OFF
            return False

        while (not (self.server_state == ServerState.ON)):
            try:
                await self.client.connect(timeout=1)
                print("Server on")
                self.server_state = ServerState.ON
                onlineMsg = f"```\n {progressBar(current_boot_time, self.average_boot_time, complete=True)}\nServer is now online at: {self.external_ipv4}:{self.server_port}\n```"
                self.boot_time_manager(read=False, newVal=current_boot_time+1)
                await loadingMsg.edit(content=onlineMsg)
            except:
                print("Server not on yet")
                current_boot_time += 1
                print(f"{current_boot_time}/{self.average_boot_time}")
                progressMsg = "```\n {0} \n```".format(progressBar(current_boot_time, self.average_boot_time))
                await loadingMsg.edit(content=progressMsg)
                continue

        print("Server online")
        return True

    async def stop(self, channel):
        self.server_state = ServerState.STOPPING
        print("Stopping server")
        shutdownMsg = await channel.send("```\nServer shutting down\n```")
        while True:
            try:
                await self.client.connect()
                await self.client.send_cmd("stop")
                break
            except:
                await shutdownMsg.edit(content="```\nSomething went wrong while attempting to shutdown. Trying again in 5s. If this message is visible for more than 30s then ask the server host to check their hosting machine.\n```")
                time.sleep(5)
        await self.client.close()
        self.server_state = ServerState.OFF
        await shutdownMsg.edit(content="```\nServer offline\n```")            
        return True

    async def status(self, channel):
        if self.server_state == ServerState.ON:
            await self.client.connect()
            cmdRes = await self.client.send_cmd("/list")
            print(cmdRes)
            await channel.send(f"```\n{cmdRes[0]}\n```")
            return True
        elif self.server_state == ServerState.STARTING:
            await channel.send("```\nServer if currently booting up\n```")
            return True
        elif self.server_state == ServerState.STOPPING:
            await channel.send("```\nServer if currently shutting down\n```")
            return True
        await channel.send("```\nServer if currently offline\n```")
        return False

    async def getInfo(self, channel):
        if self.average_boot_time == 0:
            displayed_boot_time = "N/A, MOB has never booted up this server."
        elif self.average_boot_time < 60:
            displayed_boot_time = f"{self.average_boot_time}s"
        else:
            displayed_boot_time =  f"{self.average_boot_time // 60}m {self.average_boot_time % 60}s"
        messageContent = f"\n----- Server MOB Currently Controls -----\n\n + World name: {self.world_name}\n + IP Address and Port: {self.external_ipv4}:{self.server_port}\n\n + Gamemode: {self.gamemode}\n + Difficulty: {self.difficulty}\n + Hardcore: {self.hardcore}\n\n + Average startup time: {displayed_boot_time}\n"
        await channel.send(f"```\n{messageContent}\n```")
        return True


    async def op(self, channel, target):
        try:
            await self.client.connect()
            cmdRes = await self.client.send_cmd(f"/op {target}")
            print(cmdRes)
            await channel.send(f"```\n{cmdRes[0]}\n```")
        except:
            print(f"couldnt op {target}?")

    async def setWeatherClear(self, channel):
        try:
            await self.client.connect()
            cmdRes = await self.client.send_cmd(f"/weather clear")
            print(cmdRes)
            await channel.send(f"```\n{cmdRes[0]}\n```")
        except:
            print(f"not valid command?")

def progressBar(timeElapsed, averagePrevtime, complete=False):
    if not complete:
        if timeElapsed >= averagePrevtime:
            averagePrevtime = timeElapsed + 1
        percent = 100 * (timeElapsed / float(averagePrevtime))
    else:
        percent = 100
    bar = '█' * int(percent) + '-' * (100 - int(percent))

    averagePrevTimeFormatted = ""
    if averagePrevtime < 60:
        averagePrevTimeFormatted = f"{averagePrevtime}s"
    else:
        averagePrevTimeFormatted = f"{averagePrevtime // 60}m {averagePrevtime % 60}s"

    timeElapsedFormatted = ""
    if timeElapsed < 60:
        timeElapsedFormatted = f"{timeElapsed}s"
    else:
        timeElapsedFormatted = f"{timeElapsed // 60}m {timeElapsed % 60}s"

    return f"=====  Based on previous load times  =====\n - Time elapsed: {timeElapsedFormatted} \n - Average Time to Start: {averagePrevTimeFormatted}\n| {bar} | {percent:.2f}%"