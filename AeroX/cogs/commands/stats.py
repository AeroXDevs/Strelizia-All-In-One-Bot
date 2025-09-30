import discord 
import psutil 
import sys 
import os 
import time 
import aiosqlite 
import platform 
import pkg_resources 
import datetime 
from discord import Embed ,ButtonStyle 
from discord .ui import Button ,View 
from discord .ext import commands 
from utils .Tools import *
import aiosqlite 
import wavelink 

class Stats (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .start_time =time .time ()
        self .total_songs_played =0 
        self .bot .loop .create_task (self .setup_database ())


    async def setup_database (self ):
        async with aiosqlite .connect ("db/stats.db")as db :

            await db .execute ("CREATE TABLE IF NOT EXISTS stats (key TEXT PRIMARY KEY, value INTEGER)")
            await db .commit ()


            async with db .execute ("SELECT value FROM stats WHERE key = 'total_songs_played'")as cursor :
                row =await cursor .fetchone ()
                self .total_songs_played =row [0 ]if row else 0 

    async def update_total_songs_played (self ):
        async with aiosqlite .connect ("db/stats.db")as db :
            await db .execute ("INSERT OR REPLACE INTO stats (key, value) VALUES ('total_songs_played', ?)",(self .total_songs_played ,))
            await db .commit ()

    @commands .Cog .listener ()
    async def on_wavelink_track_start (self ,payload :wavelink .TrackStartEventPayload ):
        self .total_songs_played +=1 
        await self .update_total_songs_played ()

    def count_code_stats (self ,file_path ):
        total_lines =0 
        total_words =0 
        try :
            with open (file_path ,'r',encoding ='utf-8')as file :
                for line in file :
                    stripped_line =line .strip ()
                    if stripped_line and not stripped_line .startswith (('〇')):
                        total_lines +=1 
                        total_words +=len (stripped_line .split ())
        except (UnicodeDecodeError ,IOError ):
            pass 
        return total_lines ,total_words 

    def gather_file_stats (self ,directory ):
        total_files =0 
        total_lines =0 
        total_words =0 
        for root ,_ ,files in os .walk (directory ):
            for file in files :
                file_path =os .path .join (root ,file )
                if file .endswith ('.py')and '.local'not in root :
                    total_files +=1 
                    file_lines ,file_words =self .count_code_stats (file_path )
                    total_lines +=file_lines 
                    total_words +=file_words 
        return total_files ,total_lines ,total_words 

    @commands .hybrid_command (name ="stats",aliases =["botinfo","botstats","bi","statistics"],help ="Shows the bot's information.")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,7 ,commands .BucketType .user )
    async def stats (self ,ctx ):
        processing_message =await ctx .send ("<a:Strelizia_loading:1373173756113195081> Loading Strelizia-bot information...")

        guild_count =len (self .bot .guilds )
        user_count =sum (len (g .members )for g in self .bot .guilds )
        bot_count =sum (sum (1 for m in g .members if m .bot )for g in self .bot .guilds )
        human_count =user_count -bot_count 
        channel_count =len (set (self .bot .get_all_channels ()))
        total_users =user_count 
        text_channel_count =len ([c for c in self .bot .get_all_channels ()if isinstance (c ,discord .TextChannel )])
        voice_channel_count =len ([c for c in self .bot .get_all_channels ()if isinstance (c ,discord .VoiceChannel )])
        category_channel_count =len ([c for c in self .bot .get_all_channels ()if isinstance (c ,discord .CategoryChannel )])
        slash_commands =len ([cmd for cmd in self .bot .tree .get_commands ()])
        commands_count =len (set (self .bot .walk_commands ()))
        uptime_seconds =int (round (time .time ()-self .start_time ))
        uptime_timedelta =datetime .timedelta (seconds =uptime_seconds )
        uptime =f"{uptime_timedelta.days} days, {uptime_timedelta.seconds // 3600} hours, {(uptime_timedelta.seconds // 60) % 60} minutes, {uptime_timedelta.seconds % 60} seconds"

        total_files ,total_lines ,total_words =self .gather_file_stats ('.')

        cpu_info =psutil .cpu_freq ()
        memory_info =psutil .virtual_memory ()

        total_libraries =sum (1 for _ in pkg_resources .working_set )
        channels_connected =sum (1 for vc in self .bot .voice_clients if vc )
        playing_tracks =sum (1 for vc in self .bot .voice_clients if vc .playing )

        embed =Embed (title ="Strelizia-bot Statistics: General",color =0x000000 )
        embed .add_field (name =" Channels",value =f"Total: **{channel_count}**\nText: **{text_channel_count}**   |   Voice: **{voice_channel_count}**   |   Category: **{category_channel_count}**",inline =False )
        embed .add_field (name ="<:icons_pings:1373173701704683540> Uptime",value =f"{uptime}",inline =False )
        embed .add_field (name ="<:icon_teams:1373173654904639540> User Count",value =f"Humans: **{human_count}**   |   Bots: **{bot_count}**",inline =False )
        embed .add_field (name ="<:icon_categories:1373173618858659901> Commands",value =f"Total: **{commands_count}**   |   Slash: **{slash_commands}**",inline =False )
        embed .add_field (name ="<:icon_ignore:1373173575078379590> Libraries Used",value =f"Discord Library: **[discord.py](https://discordpy.readthedocs.io/en/stable/)**\nTotal Libraries: **{total_libraries}**",inline =False )
        embed .add_field (name ="<:code_icons:1387456901192749116> Codebase Stats",value =f"Total Python Files: **{total_files}**\nTotal Lines: **{total_lines}**\nTotal Words: **{total_words}**",inline =False )
        embed .add_field (
        name ="<:music:1373174130907807814> Music Stats",
        value =f"Currently Connected: **{channels_connected}**\n"
        f"Currently Playing: **{playing_tracks}**\n"
        f"Total Songs Played: **{self.total_songs_played}**",
        inline =False 
        )
        embed .set_footer (text ="Powered by AeroX Development",icon_url =self .bot .user .display_avatar .url )

        view =View ()


        general_button =Button (label ="General",style =ButtonStyle .gray )
        async def general_button_callback (interaction ):
            if interaction .user ==ctx .author :
                await interaction .response .edit_message (embed =embed ,view =view )
        general_button .callback =general_button_callback 
        view .add_item (general_button )

        system_button =Button (label ="System",style =ButtonStyle .gray )
        async def system_button_callback (interaction ):
            if interaction .user ==ctx .author :
                system_embed =Embed (title ="Strelizia-bot Statistics: System",color =0x000000 )

                system_embed .add_field (name ="<:icon_ignore:1373173575078379590> System Info",value =f"• Discord.py: **{discord.__version__}**\n• Python: **{platform.python_version()}**\n• Architecture: **{platform.machine()}**\n• Platform: **{platform.system()}**",inline =False )

                system_embed .add_field (name ="<:memory:1373174007473504326> Memory Info",value =f"• Total Memory: **{memory_info.total / (1024 ** 2):,.2f} MB**\n• Memory Left: **{memory_info.available / (1024 ** 2):,.2f} MB**\n• Heap Total: **{memory_info.used / (1024 ** 2):,.2f} MB**",inline =False )
                cpu_freq =psutil .cpu_freq ()
                cpu_max =f"{cpu_freq.max} GHz"if cpu_freq and cpu_freq .max else "N/A"
                cpu_current =f"{cpu_info.current:.2f} MHz"if cpu_info and cpu_info .current else "N/A"

                system_embed .add_field (name ="<:icon_settings:1373173980466384967>  CPU Info",value =f"• CPU: **{cpu_max}**\n• CPU Usage: **{psutil.cpu_percent()}%**\n• CPU Cores: **{psutil.cpu_count(logical=False)}**\n• CPU Speed: **{cpu_current}**",inline =False )
                system_embed .set_footer (text ="Powered by AeroX Development",icon_url =self .bot .user .display_avatar .url )

                await interaction .response .edit_message (embed =system_embed ,view =view )
        system_button .callback =system_button_callback 
        view .add_item (system_button )


        ping_button =Button (label ="Ping",style =ButtonStyle .green )
        async def ping_button_callback (interaction ):
            if interaction .user ==ctx .author :
                s_id =ctx .guild .shard_id 
                sh =self .bot .get_shard (s_id )

                db_latency =None 
                try :
                    async with aiosqlite .connect ("db/afk.db")as db :
                        start_time =time .perf_counter ()
                        await db .execute ("SELECT 1")
                        end_time =time .perf_counter ()
                        db_latency =(end_time -start_time )*1000 
                        db_latency =round (db_latency ,2 )
                except Exception as e :
                    db_latency ="N/A"

                wsping =round (self .bot .latency *1000 ,2 )

                ping_embed =Embed (title ="Strelizia-bot Statistics: Latency Overview",color =0x000000 )
                ping_embed .add_field (
                name ="<:icons_pings:1373173701704683540> Latency Overview",
                value =f"<:icon_teams:1373173654904639540> Bot Latency: **{round(sh.latency * 800)}ms**\n"
                f"<:icon_categories:1373173618858659901> Database Latency: **{db_latency}ms**\n"
                f"<:icon_ignore:1373173575078379590> WebSocket Latency: **{wsping}ms**\n\n"
                f"<:code_icons:1387456901192749116> Last Ping Check: <t:{int(time.time())}:R>",
                inline =False 
                )
                ping_embed .set_footer (text ="Developed By AeroX Development",icon_url =self .bot .user .display_avatar .url )
                ping_embed .set_author (name =self .bot .user .display_name ,icon_url =self .bot .user .display_avatar .url )
                ping_embed .set_thumbnail (url =self .bot .user .display_avatar .url )
                await interaction .response .edit_message (embed =ping_embed ,view =view )
        ping_button .callback =ping_button_callback 
        view .add_item (ping_button )






        delete_button =Button (label ="🗑️",style =ButtonStyle .red )
        async def delete_button_callback (interaction ):
            if interaction .user ==ctx .author :
                await interaction .message .delete ()
        delete_button .callback =delete_button_callback 
        view .add_item (delete_button )


        server_count_button =Button (label =f"Servers: {guild_count}    |    Users: {total_users}",style =ButtonStyle .success ,disabled =True )
        view .add_item (server_count_button )


        await ctx .reply (embed =embed ,view =view )
        await processing_message .delete ()

"""
@Author: Aegis
    + Discord: Solcodez
    + Community: https://discord.strelix.xyz (AeroX Development)
    + for any queries reach out Community or DM me.
"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
