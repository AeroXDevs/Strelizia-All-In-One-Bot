
import random 
import discord 
from discord .ext import commands ,tasks 
from discord import app_commands 
import datetime 
from datetime import datetime ,timezone 
from discord .ui import Button ,View 
import wavelink 
from wavelink .enums import TrackSource 
from utils import Paginator ,DescriptionEmbedPaginator 
from core import Cog ,Strelizia ,Context 
from PIL import Image ,ImageDraw ,ImageFont ,ImageOps 
import io 
import aiohttp 
from typing import cast 
import asyncio 
from utils .Tools import *
import json 
import os 
from dotenv import load_dotenv 
import lyricsgenius 
track_histories ={}
user_favorites ={}
playlist_cache ={}
import base64 
import asyncio 
import re 
from collections import defaultdict ,deque 


load_dotenv ()


TWENTYFOURSEVEN_FILE ="jsondb/247_channels.json"
FAVORITES_FILE ="jsondb/user_favorites.json"
QUEUE_HISTORY_FILE ="jsondb/queue_history.json"

def load_user_favorites ():
    try :
        if os .path .exists (FAVORITES_FILE ):
            with open (FAVORITES_FILE ,'r')as f :
                return json .load (f )
    except Exception as e :
        pass 
    return {}

def save_user_favorites (data ):
    try :
        os .makedirs (os .path .dirname (FAVORITES_FILE ),exist_ok =True )
        with open (FAVORITES_FILE ,'w')as f :
            json .dump (data ,f )
    except Exception as e :
        pass 

def load_queue_history ():
    try :
        if os .path .exists (QUEUE_HISTORY_FILE ):
            with open (QUEUE_HISTORY_FILE ,'r')as f :
                return json .load (f )
    except Exception as e :
        pass 
    return {}

def save_queue_history (data ):
    try :
        os .makedirs (os .path .dirname (QUEUE_HISTORY_FILE ),exist_ok =True )
        with open (QUEUE_HISTORY_FILE ,'w')as f :
            json .dump (data ,f )
    except Exception as e :
        pass 

def load_247_channels ():
    try :
        if os .path .exists (TWENTYFOURSEVEN_FILE ):
            with open (TWENTYFOURSEVEN_FILE ,'r')as f :
                return json .load (f )
    except Exception as e :
        pass 
    return {}

def save_247_channels (data ):
    try :
        os .makedirs (os .path .dirname (TWENTYFOURSEVEN_FILE ),exist_ok =True )
        with open (TWENTYFOURSEVEN_FILE ,'w')as f :
            json .dump (data ,f )
    except Exception as e :
        pass 

SPOTIFY_TRACK_REGEX =r"https?://open\.spotify\.com/track/([a-zA-Z0-9]+)"
SPOTIFY_PLAYLIST_REGEX =r"https?://open\.spotify\.com/playlist/([a-zA-Z0-9]+)"
SPOTIFY_ALBUM_REGEX =r"https?://open\.spotify\.com/album/([a-zA-Z0-9]+)"

class SpotifyAPI :
    BASE_URL ="https://api.spotify.com/v1"

    def __init__ (self ,client_id ,client_secret ):
        self .client_id =client_id 
        self .client_secret =client_secret 
        self .token =None 

    async def get_token (self ):
        auth_url ="https://accounts.spotify.com/api/token"
        auth_value =base64 .b64encode (f"{self.client_id}:{self.client_secret}".encode ('utf-8')).decode ('utf-8')
        headers ={"Authorization":f"Basic {auth_value}"}
        data ={"grant_type":"client_credentials"}
        async with aiohttp .ClientSession ()as session :
            try :
                async with session .post (auth_url ,headers =headers ,data =data )as response :
                    text =await response .text ()
                    if response .status !=200 :
                        raise Exception (f"Failed to fetch token: {response.status}, response: {text}")
                    self .token =(await response .json ()).get ("access_token")
            except Exception as e :
                pass 

    async def get (self ,endpoint ,params =None ):
        retries =2 
        for attempt in range (retries ):
            try :
                if not self .token or attempt >0 :
                    await self .get_token ()

                url =f"{self.BASE_URL}/{endpoint}"
                headers ={"Authorization":f"Bearer {self.token}"}
                async with aiohttp .ClientSession ()as session :
                    async with session .get (url ,headers =headers ,params =params )as response :
                        if response .status ==401 and attempt <retries -1 :
                            continue 
                        elif response .status !=200 :
                            raise Exception (f"Failed to fetch data from Spotify: {response.status}")
                        return await response .json ()
            except Exception as e :
                if attempt ==retries -1 :
                    return None 
        return None 

    async def get_track (self ,track_id ):
        return await self .get (f"tracks/{track_id}")

    async def get_playlist (self ,playlist_id ):
        return await self .get (f"playlists/{playlist_id}")

spotify_api =SpotifyAPI (client_id ="ac2b614ca5ce46a18dfd1d3475fd6fd9",client_secret ="df7bec95ae88438e8286db597bac8621")

class PlatformSelectView (View ):
    def __init__ (self ,ctx ,query ):
        super ().__init__ (timeout =60 )
        self .ctx =ctx 
        self .query =query 


        youtube_button =Button (label ="YouTube",style =discord .ButtonStyle .red ,emoji ="<:yt:1373931239123189810>")
        youtube_button .callback =self .create_callback ("ytsearch")
        self .add_item (youtube_button )


        soundcloud_button =Button (label ="SoundCloud",style =discord .ButtonStyle .grey ,emoji ="<:SoundCloud:1373930998005370900>")
        soundcloud_button .callback =self .create_callback ("scsearch")
        self .add_item (soundcloud_button )

    def create_callback (self ,source ):
        async def callback (interaction :discord .Interaction ):
            try :
                if interaction .user !=self .ctx .author :
                    await interaction .response .send_message ("Only the command author can select a platform.",ephemeral =True )
                    return 

                await interaction .response .defer ()
                await self .perform_search (source ,interaction )
            except Exception as e :
                pass 
        return callback 

    async def perform_search (self ,source ,interaction ):
        try :

            user_key =f"{self.ctx.guild.id}_{self.ctx.author.id}"
            music_cog =self .ctx .bot .get_cog ('Music')
            if music_cog :
                music_cog .user_platform_preferences [user_key ]=source 

            results =await wavelink .Playable .search (self .query ,source =source )
            if not results :
                embed =discord .Embed (description ="No results found.",color =0x000000 )
                await interaction .edit_original_response (embed =embed ,view =None )
                return 

            top_results =results [:5 ]
            platform_name ="YouTube"if source =="ytsearch"else "SoundCloud"
            embed =discord .Embed (
            title =f"Top 5 Results for '{self.query}' on {platform_name}",
            description ="Select a track to play or add to queue:",
            color =0x000000 
            )

            for i ,track in enumerate (top_results ,start =1 ):
                duration =f"{track.length // 1000 // 60}:{track.length // 1000 % 60:02d}"
                embed .add_field (
                name =f"{i}. {track.title[:50]}{'...' if len(track.title) > 50 else ''}",
                value =f"**Artist:** {track.author}\n**Duration:** {duration}",
                inline =False 
                )

            await interaction .edit_original_response (embed =embed ,view =SearchResultView (self .ctx ,top_results ))
        except Exception as e :
            embed =discord .Embed (color =0x000000 )
            await interaction .edit_original_response (embed =embed ,view =None )

class SearchResultView (View ):
    def __init__ (self ,ctx ,results ):
        super ().__init__ (timeout =60 )
        self .ctx =ctx 
        self .results =results 

        for i in range (min (5 ,len (results ))):
            button =Button (label =f"Track {i + 1}",style =discord .ButtonStyle .primary )
            button .callback =self .create_callback (i )
            self .add_item (button )

    def create_callback (self ,index ):
        async def callback (interaction :discord .Interaction ):
            try :
                if interaction .user !=self .ctx .author :
                    await interaction .response .send_message ("Only the command author can select a track.",ephemeral =True )
                    return 

                track =self .results [index ]
                vc =self .ctx .voice_client 

                if not vc :
                    if not self .ctx .author .voice :
                        await interaction .response .send_message ("You need to be in a voice channel.",ephemeral =True )
                        return 
                    try :
                        vc =await self .ctx .author .voice .channel .connect (cls =wavelink .Player ,timeout =10.0 ,self_deaf =True )
                    except Exception as e :
                        pass 
                        return 

                vc .ctx =self .ctx 

                if not vc .playing :
                    await vc .play (track )
                    embed =discord .Embed (
                    description =f"🎵 Started playing **{track.title}**",
                    color =0x000000 
                    )
                    await interaction .response .send_message (embed =embed )
                    await self .ctx .cog .display_player_embed (vc ,track ,self .ctx )
                else :
                    await vc .queue .put_wait (track )
                    embed =discord .Embed (
                    description =f"➕ Added **{track.title}** to the queue",
                    color =0x000000 
                    )
                    await interaction .response .send_message (embed =embed )


                await interaction .edit_original_response (view =None )
            except Exception as e :
                await interaction .response .send_message (f"Error: {str(e)}",ephemeral =True )
        return callback 

class MusicControlView (View ):
    def __init__ (self ,player ,ctx ):
        super ().__init__ (timeout =None )
        self .player =player 
        self .ctx =ctx 

    async def interaction_check (self ,interaction :discord .Interaction )->bool :
        if not self .ctx .voice_client or not self .player .playing :
            await interaction .response .send_message ("I'm not currently playing this anymore.",ephemeral =True )
            return False 
        if interaction .user in self .ctx .voice_client .channel .members :
            return True 
        await interaction .response .send_message (
        embed =discord .Embed (description ="Only members in the same voice channel as me can control the player.",color =0x000000 ),
        ephemeral =True 
        )
        return False 

    @discord .ui .button (emoji ="<:icon_volume:1373928182314565693>",style =discord .ButtonStyle .secondary )
    async def autoplay_button (self ,interaction :discord .Interaction ,button :Button ):
        self .player .autoplay =(
        wavelink .AutoPlayMode .enabled if self .player .autoplay !=wavelink .AutoPlayMode .enabled else wavelink .AutoPlayMode .disabled 
        )
        await interaction .response .send_message (f"Autoplay {'enabled' if self.player.autoplay == wavelink.AutoPlayMode.enabled else 'disabled'} by **{interaction.user.display_name}**.",ephemeral =True )

    @discord .ui .button (emoji ="<:rewind:1373926276683005975>",style =discord .ButtonStyle .secondary )
    async def previous_button (self ,interaction :discord .Interaction ,button :Button ):
        guild_id =interaction .guild .id 

        if guild_id in track_histories and len (track_histories [guild_id ])>1 :
            track_histories [guild_id ].pop ()
            previous_track =track_histories [guild_id ][-1 ]

            player =self .player 
            vc =self .ctx .voice_client 

            if player .playing :
                await player .stop ()

            await vc .queue .put_wait (previous_track )

            await interaction .response .send_message (f"Playing previous track: `{previous_track.title}`.")
        else :
            await interaction .response .send_message ("No previous track available.",ephemeral =True )

    @discord .ui .button (emoji ="<:music_stop:1373925462828650592>",style =discord .ButtonStyle .success )
    async def pause_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player .paused :
            await self .player .pause (False )

            await self .player .channel .edit (status =f"<:auto:1374271451594489898> Playing: {self.player.current.title}")
            button .emoji ="<:music_stop:1373925462828650592>"
            await interaction .response .edit_message (view =self )

        elif self .player .playing :
            await self .player .pause (True )
            await self .player .channel .edit (status =f"<:auto:1374271451594489898>  Paused: {self.player.current.title}")
            button .emoji ="<:icons_pause:1381535606382792726>"
            await interaction .response .edit_message (view =self )

    @discord .ui .button (emoji ="<:music_skip:1373925947685998653>",style =discord .ButtonStyle .secondary )
    async def skip_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player and self .player .playing :
            await self .player .stop ()
            await interaction .response .send_message (f"Skipped song by **{interaction.user.display_name}**.")
        else :
            await interaction .response .send_message ("No song is currently playing.",ephemeral =True )

    @discord .ui .button (emoji ="<a:Strelizia_loading:1372527554761855038>",style =discord .ButtonStyle .secondary )
    async def loop_button (self ,interaction :discord .Interaction ,button :Button ):
        self .player .queue .mode =wavelink .QueueMode .loop if self .player .queue .mode !=wavelink .QueueMode .loop else wavelink .QueueMode .normal 
        await interaction .response .send_message (f"Loop {'enabled' if self.player.queue.mode == wavelink.QueueMode.loop else 'disabled'} by **{interaction.user.display_name}**.")

    @discord .ui .button (emoji ="<:shuffle:1373926136945311855>",style =discord .ButtonStyle .secondary )
    async def shuffle_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player .queue :
            random .shuffle (self .player .queue )
            await interaction .response .send_message (f"Queue shuffled by **{interaction.user.display_name}**.")
        else :
            await interaction .response .send_message ("Queue is empty.",ephemeral =True )

    @discord .ui .button (emoji ="<:rewind:1373926276683005975>",style =discord .ButtonStyle .secondary )
    async def rewind_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player .playing :
            new_position =max (self .player .position -10000 ,0 )
            await self .player .seek (new_position )
            await interaction .response .send_message ("Rewinded 10 seconds.",ephemeral =True )
        else :
            await interaction .response .send_message ("No track is currently playing.",ephemeral =True )

    @discord .ui .button (emoji ="<:music_stop:1373925462828650592>",style =discord .ButtonStyle .secondary )
    async def stop_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player :
            voice_channel =self .player .channel 
            if voice_channel :
                await voice_channel .edit (status =None )

            await self .player .disconnect ()
            await interaction .response .send_message (f"Stopped and disconnected by **{interaction.user.display_name}**.")
        else :
            await interaction .response .send_message ("Not connected.",ephemeral =True )

    @discord .ui .button (emoji ="<:icons_next:1327829470027055184>",style =discord .ButtonStyle .secondary )
    async def forward_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player .playing :
            new_position =min (self .player .position +10000 ,self .player .current .length )
            await self .player .seek (new_position )
            await interaction .response .send_message ("Forwarded 10 seconds.",ephemeral =True )
        else :
            await interaction .response .send_message ("No track is currently playing.",ephemeral =True )

    @discord .ui .button (emoji ="<:music:1373174130907807814>",style =discord .ButtonStyle .secondary )
    async def replay_button (self ,interaction :discord .Interaction ,button :Button ):
        if self .player .playing :
            await self .player .seek (0 )
            await interaction .response .send_message ("Replaying the current track.",ephemeral =True )
        else :
            await interaction .response .send_message ("No track is currently playing.",ephemeral =True )

class Music (Cog ):
    def __init__ (self ,client :Strelizia ):
        self .client =client 
        self .inactivity_timeout =300 
        self .player_inactivity ={}
        self .twentyfourseven_channels =load_247_channels ()
        self .user_platform_preferences ={}
        self .voice_tracking ={}
        self .user_favorites =load_user_favorites ()
        self .queue_history =load_queue_history ()
        self .smart_queue =defaultdict (list )
        self .advanced_filters ={}
        self .crossfade_enabled ={}
        self .queue_repeat_modes ={}


        genius_api_key =os .getenv ('GENIUS_API_KEY')
        if genius_api_key :
            try :
                self .genius =lyricsgenius .Genius (genius_api_key )
                self .genius .verbose =False 
                self .genius .remove_section_headers =True 
            except Exception as e :
                print (f"Failed to initialize Genius API: {e}")
                self .genius =None 
        else :
            print ("GENIUS_API_KEY environment variable not set")
            self .genius =None 



    async def cog_load (self ):
        """Called when the cog is loaded"""
        asyncio .create_task (self .connect_nodes ())
        asyncio .create_task (self .monitor_inactivity ())
        await self .init_music_stats_db ()

    async def init_music_stats_db (self ):
        """Initialize music stats database"""
        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :
                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS user_music_stats (
                        user_id INTEGER,
                        guild_id INTEGER,
                        total_songs_played INTEGER DEFAULT 0,
                        total_listening_time INTEGER DEFAULT 0,
                        favorite_song TEXT DEFAULT '',
                        favorite_artist TEXT DEFAULT '',
                        last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                        PRIMARY KEY (user_id, guild_id)
                    )
                """)
                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS song_history (
                        user_id INTEGER,
                        guild_id INTEGER,
                        song_title TEXT,
                        song_artist TEXT,
                        song_duration INTEGER,
                        played_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                await db .commit ()
        except Exception as e :
            print (f"Error initializing music stats database: {e}")

    async def play_with_source (self ,ctx ,query ,source ):
        """Play music with a specific source without asking for platform"""
        try :
            if not ctx .author .voice :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in a voice channel to use this command.",color =0x000000 ))
                return 

            if not ctx .voice_client :
                try :
                    vc =await ctx .author .voice .channel .connect (cls =wavelink .Player ,timeout =10.0 ,self_deaf =True )
                except Exception as e :
                    await ctx .send (embed =discord .Embed (description =f"Failed to connect to voice channel: {str(e)}",color =0xFF0000 ))
                    return 
            else :
                vc =ctx .voice_client 
            vc .ctx =ctx 

            if vc .playing :
                if ctx .voice_client and ctx .voice_client .channel !=ctx .author .voice .channel :
                    await ctx .send (embed =discord .Embed (description =f"You must be connected to {ctx.voice_client.channel.mention} to play.",color =0x000000 ))
                    return 

            tracks =await wavelink .Playable .search (query ,source =source )
            if not tracks :
                await ctx .send (embed =discord .Embed (description ="No results found.",color =0x000000 ))
                return 

            track =tracks [0 ]
            await vc .queue .put_wait (track )
            await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added [{track.title}](https://discord.gg/JxCFmz9nZP) to the queue.",color =0x000000 ))

            if not vc .playing :
                try :
                    next_track =await vc .queue .get_wait ()
                    await vc .play (next_track )
                    await self .display_player_embed (vc ,next_track ,ctx )
                    await self .update_music_stats (ctx .author .id ,ctx .guild .id ,next_track )
                except Exception as e :
                    pass 
            else :
                await self .update_music_stats (ctx .author .id ,ctx .guild .id ,track )
        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))

    async def update_music_stats (self ,user_id ,guild_id ,track ):
        """Update user's music statistics - only increment song count"""
        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :

                await db .execute ("""
                    INSERT OR REPLACE INTO user_music_stats 
                    (user_id, guild_id, total_songs_played, total_listening_time, last_updated)
                    VALUES (?, ?, 
                        COALESCE((SELECT total_songs_played FROM user_music_stats WHERE user_id = ? AND guild_id = ?), 0) + 1,
                        COALESCE((SELECT total_listening_time FROM user_music_stats WHERE user_id = ? AND guild_id = ?), 0),
                        CURRENT_TIMESTAMP)
                """,(user_id ,guild_id ,user_id ,guild_id ,user_id ,guild_id ))


                await db .execute ("""
                    INSERT INTO song_history (user_id, guild_id, song_title, song_artist, song_duration)
                    VALUES (?, ?, ?, ?, ?)
                """,(user_id ,guild_id ,track .title ,track .author ,track .length //1000 ))

                await db .commit ()
        except Exception as e :
            print (f"Error updating music stats: {e}")

    async def track_listening_time (self ,user_id ,guild_id ,seconds ):
        """Track actual listening time for a user"""
        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :
                await db .execute ("""
                    INSERT OR REPLACE INTO user_music_stats 
                    (user_id, guild_id, total_songs_played, total_listening_time, last_updated)
                    VALUES (?, ?, 
                        COALESCE((SELECT total_songs_played FROM user_music_stats WHERE user_id = ? AND guild_id = ?), 0),
                        COALESCE((SELECT total_listening_time FROM user_music_stats WHERE user_id = ? AND guild_id = ?), 0) + ?,
                        CURRENT_TIMESTAMP)
                """,(user_id ,guild_id ,user_id ,guild_id ,user_id ,guild_id ,seconds ))
                await db .commit ()
        except Exception as e :
            print (f"Error tracking listening time: {e}")

    async def monitor_inactivity (self ):
        while True :
            try :
                for guild in self .client .guilds :
                    await self .check_inactivity (guild .id )
                await asyncio .sleep (60 )
            except Exception as e :
                await asyncio .sleep (60 )

    async def check_inactivity (self ,guild_id ):
        try :
            guild =self .client .get_guild (guild_id )
            if not guild :
                return 


            if str (guild_id )in self .twentyfourseven_channels :
                return 

            player =None 
            for vc in self .client .voice_clients :
                if vc .guild .id ==guild .id :
                    player =vc 
                    break 

            if player and player .connected and hasattr (player ,'channel')and player .channel :
                human_members =[m for m in player .channel .members if not m .bot ]

                if len (human_members )==0 and not player .playing :
                    await self .inactivity_timer (guild ,player )
        except Exception as e :
            pass 

    async def inactivity_timer (self ,guild ,player ):
        try :
            await asyncio .sleep (self .inactivity_timeout )


            if player and player .connected and hasattr (player ,'channel')and player .channel :
                human_members =[m for m in player .channel .members if not m .bot ]
                if len (human_members )==0 and str (guild .id )not in self .twentyfourseven_channels :
                    try :
                        await player .disconnect (force =True )
                        if hasattr (player ,'ctx')and player .ctx :
                            ended =discord .Embed (description ="Bot has been disconnected due to inactivity (being idle in Voice Channel) for more than 2 minutes.",color =0x000000 )
                            ended .set_author (name ="Inactive Timeout",icon_url =self .client .user .avatar .url )
                            ended .set_footer (text ="Thanks for choosing Strelizia-bot!")
                            support =Button (label ='Support',style =discord .ButtonStyle .link ,url ='https://discord.gg/JxCFmz9nZP')
                            vote =Button (label ='Vote',style =discord .ButtonStyle .link ,url ='https://top.gg')
                            view =View ()
                            view .add_item (support )
                            view .add_item (vote )
                            await player .ctx .channel .send (embed =ended ,view =view )
                    except Exception as e :
                        pass 
        except Exception as e :
            pass 

    async def connect_nodes (self )->None :
        try :

            host =os .getenv ('LAVALINK_HOST','lava-v4.ajieblogs.eu.org')
            port =os .getenv ('LAVALINK_PORT','443')
            secure =os .getenv ('LAVALINK_SECURE','true').lower ()=='true'
            password =os .getenv ('LAVALINK_PASSWORD','https://dsc.gg/ajidevserver')


            protocol ='https'if secure else 'http'
            uri =f"{protocol}://{host}:{port}"


            node =wavelink .Node (uri =uri ,password =password )
            await wavelink .Pool .connect (nodes =[node ],client =self .client ,cache_capacity =None )
        except Exception as e :
            print (f"Failed to connect to Lavalink node: {e}")
            pass 

    async def display_player_embed (self ,player ,track ,ctx ,autoplay =False ):
        try :
            if track .artwork :
                template_path ='data/pictures/player.png'
                font_path ='utils/arial.ttf'

                try :
                    font =ImageFont .truetype (font_path ,40 )
                    base_img =Image .open (template_path ).convert ("RGBA")

                    async with aiohttp .ClientSession ()as session :
                        async with session .get (track .artwork )as resp :
                            if resp .status ==200 :
                                track_img_data =io .BytesIO (await resp .read ())
                                track_img =Image .open (track_img_data ).convert ("RGBA")
                                track_img =ImageOps .fit (track_img ,(220 ,220 ),centering =(0.5 ,0.5 ))

                                mask =Image .new ('L',(220 ,220 ),0 )
                                draw =ImageDraw .Draw (mask )
                                draw .ellipse ((0 ,0 ,220 ,220 ),fill =255 )
                                track_img .putalpha (mask )
                                base_img .paste (track_img ,(15 ,125 -85 ),track_img )

                    draw =ImageDraw .Draw (base_img )
                    title =track .title [:30 ]+"..."if len (track .title )>30 else track .title 
                    draw .text ((240 ,50 ),title ,font =font ,fill ="white")

                    image_bytes =io .BytesIO ()
                    base_img .save (image_bytes ,format ="PNG")
                    image_bytes .seek (0 )

                    file =discord .File (image_bytes ,filename ="player.png")
                except Exception as e :
                    file =None 
            else :
                file =None 

            sec =track .length //1000 
            duration =f"0{sec // 60}:{sec % 60:02d}"if sec <600 else f"{sec // 60}:{sec % 60:02d}"

            color =0x000000 
            if "spotify"in track .source :
                color =0x1DB954 
            elif "youtube"in track .source :
                color =0xFF0000 
            elif "soundcloud"in track .source :
                color =0xFF5500 

            embed =discord .Embed (title =f"**{track.title}**",color =color )
            embed .add_field (name ="Author",value =f"`{track.author}`")
            embed .add_field (name ="Duration",value =f"`{duration}`")

            source_text =""
            if "spotify"in track .source :
                source_text =f"[<:spotify:1373930579078152324>  Listen on Spotify]({track.uri})"
            elif "soundcloud"in track .source :
                source_text =f"[<:SoundCloud:1373930998005370900> Listen on SoundCloud]({track.uri})"
            else :
                source_text =f"[<:yt:1373931239123189810> Listen on YouTube]({track.uri})"

            embed .add_field (name ="Source",value =source_text )

            if file :
                embed .set_image (url ="attachment://player.png")

            footer_text ="Requested by "+(ctx .author .display_name if not autoplay else f"{ctx.author.display_name} (Autoplay Mode)")
            embed .set_footer (text =footer_text ,icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )

            await ctx .send (embed =embed ,file =file ,view =MusicControlView (player ,ctx ))
        except Exception as e :
            embed =discord .Embed (description ="Now playing: "+track .title ,color =0x000000 )
            await ctx .send (embed =embed ,view =MusicControlView (player ,ctx ))

    @commands .Cog .listener ()
    async def on_voice_state_update (self ,member ,before ,after ):
        """Track voice channel join/leave for accurate listening time"""
        if member .bot :
            return 

        try :
            current_time =asyncio .get_event_loop ().time ()
            user_key =f"{member.guild.id}_{member.id}"


            voice_client =None 
            for vc in self .client .voice_clients :
                if vc .guild .id ==member .guild .id and vc .playing :
                    voice_client =vc 
                    break 

            if not voice_client :
                return 


            if after .channel and after .channel .id ==voice_client .channel .id and not before .channel :
                self .voice_tracking [user_key ]=current_time 


            elif before .channel and before .channel .id ==voice_client .channel .id and not after .channel :
                if user_key in self .voice_tracking :
                    listening_time =int (current_time -self .voice_tracking [user_key ])
                    if listening_time >0 :
                        await self .track_listening_time (member .id ,member .guild .id ,listening_time )
                    del self .voice_tracking [user_key ]


            elif before .channel and before .channel .id ==voice_client .channel .id and after .channel and after .channel .id !=voice_client .channel .id :
                if user_key in self .voice_tracking :
                    listening_time =int (current_time -self .voice_tracking [user_key ])
                    if listening_time >0 :
                        await self .track_listening_time (member .id ,member .guild .id ,listening_time )
                    del self .voice_tracking [user_key ]

        except Exception as e :
            print (f"Error in voice state tracking: {e}")

    async def on_track_end (self ,payload :wavelink .TrackEndEventPayload ):
        try :
            player =payload .player 

            if not player .connected :
                return 


            if hasattr (player ,'channel')and player .channel :
                current_time =asyncio .get_event_loop ().time ()
                for member in player .channel .members :
                    if not member .bot :
                        user_key =f"{player.guild.id}_{member.id}"
                        if user_key in self .voice_tracking :
                            listening_time =int (current_time -self .voice_tracking [user_key ])
                            if listening_time >0 :
                                await self .track_listening_time (member .id ,player .guild .id ,listening_time )

                            self .voice_tracking [user_key ]=current_time 

            if player .queue .mode ==wavelink .QueueMode .loop and payload .track :

                crossfade_delay =1 if self .crossfade_enabled .get (player .guild .id ,False )else 2 
                await asyncio .sleep (crossfade_delay )
                await player .play (payload .track )
                return 

            if not player .queue .is_empty :

                crossfade_delay =1 if self .crossfade_enabled .get (player .guild .id ,False )else 2 
                await asyncio .sleep (crossfade_delay )
                next_track =await player .queue .get_wait ()
                await player .play (next_track )
                await self .display_player_embed (player ,next_track ,player .ctx )
            elif player .autoplay ==wavelink .AutoPlayMode .enabled :
                await asyncio .sleep (2 )
                if player .current :
                    await self .display_player_embed (player ,player .current ,player .ctx ,autoplay =True )
            else :

                guild_id =str (player .guild .id )
                if guild_id not in self .twentyfourseven_channels :
                    await asyncio .sleep (1 )
                    if player .connected :
                        await player .disconnect ()
                        try :
                            ended =discord .Embed (description ="All tracks have been played, leaving the voice channel.",color =0x000000 )
                            ended .set_author (name ="Queue Ended",icon_url =self .client .user .avatar .url )


                            class SmartQueueView (View ):
                                def __init__ (self ,music_cog ):
                                    super ().__init__ (timeout =300 )
                                    self .music_cog =music_cog 

                                @discord .ui .button (label ='Generate Smart Queue',style =discord .ButtonStyle .primary ,emoji ='🧠')
                                async def smart_queue_button (self ,interaction :discord .Interaction ,button :Button ):
                                    try :

                                        await interaction .response .send_message ("🧠 Generating smart queue... This may take a moment.",ephemeral =True )
                                    except Exception as e :
                                        pass 

                            support =Button (label ='Support',style =discord .ButtonStyle .link ,url ='https://discord.gg/JxCFmz9nZP')
                            vote =Button (label ='Vote',style =discord .ButtonStyle .link ,url ='https://top.gg')
                            view =SmartQueueView (self )
                            view .add_item (support )
                            view .add_item (vote )
                            await player .ctx .channel .send (embed =ended ,view =view )
                        except Exception as e :
                            pass 
        except Exception as e :
            try :
                if payload .player .connected :
                    await payload .player .disconnect ()
            except Exception as e :
                pass 

    async def play_source (self ,ctx ,query ):
        try :
            if not ctx .author .voice :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in a voice channel to use this command.",color =0x000000 ))
                return 

            if not ctx .voice_client :
                try :
                    vc =await ctx .author .voice .channel .connect (cls =wavelink .Player ,timeout =10.0 ,self_deaf =True )
                except Exception as e :
                    await ctx .send (embed =discord .Embed (description =f"Failed to connect to voice channel: {str(e)}",color =0xFF0000 ))
                    return 
            else :
                vc =ctx .voice_client 
            vc .ctx =ctx 

            if vc .playing :
                if ctx .voice_client and ctx .voice_client .channel !=ctx .author .voice .channel :
                    await ctx .send (embed =discord .Embed (description =f"You must be connected to {ctx.voice_client.channel.mention} to play.",color =0x000000 ))
                    return 
            vc .autoplay =wavelink .AutoPlayMode .disabled 

            if re .match (SPOTIFY_TRACK_REGEX ,query ):
                await self .handle_spotify_link (ctx ,vc ,query ,"track")
                return 
            elif re .match (SPOTIFY_PLAYLIST_REGEX ,query ):
                await self .handle_spotify_link (ctx ,vc ,query ,"playlist")
                return 
            elif re .match (SPOTIFY_ALBUM_REGEX ,query ):
                await self .handle_spotify_link (ctx ,vc ,query ,"album")
                return 

            tracks =await wavelink .Playable .search (query )
            if not tracks :
                await ctx .send (embed =discord .Embed (description ="No results found.",color =0x000000 ))
                return 

            if isinstance (tracks ,wavelink .Playlist ):
                await vc .queue .put_wait (tracks .tracks )
                await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added playlist [{tracks.name}](https://discord.gg/JxCFmz9nZP) with **{len(tracks.tracks)} songs** to the queue.",color =0x000000 ))
                if not vc .playing :
                    track =await vc .queue .get_wait ()
                    await vc .play (track )
                    await self .display_player_embed (vc ,track ,ctx )
            else :
                track =tracks [0 ]
                await vc .queue .put_wait (track )
                await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added [{track.title}](https://discord.gg/JxCFmz9nZP) to the queue.",color =0x000000 ))
                if not vc .playing :
                    try :
                        next_track =await vc .queue .get_wait ()
                        await vc .play (next_track )
                        await self .display_player_embed (vc ,next_track ,ctx )
                    except Exception as e :
                        pass 
                self .client .loop .create_task (self .check_inactivity (ctx .guild .id ))
        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))

    async def handle_spotify_link (self ,ctx ,vc ,link ,type_ ):
        try :
            if type_ =="track":
                track_id =re .search (SPOTIFY_TRACK_REGEX ,link ).group (1 )
                track_info =await spotify_api .get_track (track_id )

                if not track_info :
                    await ctx .send ("Can't fetch track info from Spotify.")
                    return 

                title =track_info ['name']
                author =', '.join (artist ['name']for artist in track_info ['artists'])
                search_query =f"{title} by {author}"
                search_results =await wavelink .Playable .search (search_query ,source =wavelink .enums .TrackSource .YouTube )

                if not search_results :
                    await ctx .send ("Can't play this track from Spotify, please try with another track.")
                    return 

                track =search_results [0 ]
                await vc .queue .put_wait (track )
                await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added [{track.title}](https://discord.gg/JxCFmz9nZP) to the queue.",color =0x000000 ))
                if not vc .playing :
                    await vc .play (track )
                    await self .display_player_embed (vc ,track ,ctx )

            elif type_ =="playlist":
                lmao =await ctx .send ("⏳ Processing to add tracks from the playlist, this may take a while...")

                playlist_id =re .search (SPOTIFY_PLAYLIST_REGEX ,link ).group (1 )
                playlist_info =await spotify_api .get (f"playlists/{playlist_id}")

                if not playlist_info :
                    await ctx .send ("Can't fetch playlist info from Spotify.")
                    await lmao .delete ()
                    return 

                tracks =playlist_info .get ("tracks",{}).get ("items",[])
                playlist_length =len (tracks )

                if not tracks :
                    await ctx .send ("No tracks found in the playlist.")
                    await lmao .delete ()
                    return 

                c =0 
                for track in tracks :
                    try :
                        title =track ['track']['name']
                        author =', '.join (artist ['name']for artist in track ['track']['artists'])
                        search_query =f"{title} {author}"

                        track_results =await wavelink .Playable .search (search_query ,source =wavelink .enums .TrackSource .YouTube )
                        if track_results :
                            await vc .queue .put_wait (track_results [0 ])
                            c +=1 
                            try :
                                await ctx .message .add_reaction ("<:icon_tick:1372375089668161597>")
                            except Exception as e :
                                pass 
                    except Exception as e :
                        continue 

                await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added **{c}** of **{playlist_length}** tracks from **playlist** **[{playlist_info['name']}](https://discord.gg/JxCFmz9nZP)** to the queue.",color =0x000000 ))
                await lmao .delete ()

                if not vc .playing :
                    next_track =await vc .queue .get_wait ()
                    await vc .play (next_track )
                    await self .display_player_embed (vc ,next_track ,ctx )

            elif type_ =="album":
                try :
                    await ctx .message .add_reaction ("<a:Strelizia_loading:1372527554761855038>")
                except Exception as e :
                    pass 

                album_id =re .search (SPOTIFY_ALBUM_REGEX ,link ).group (1 )
                album_info =await spotify_api .get (f"albums/{album_id}")

                if not album_info :
                    await ctx .send ("Can't fetch album info from Spotify.")
                    return 

                tracks =album_info .get ("tracks",{}).get ("items",[])

                if not tracks :
                    await ctx .send ("No tracks found in the album.")
                    return 

                c =0 
                for track in tracks :
                    try :
                        title =track ['name']
                        author =', '.join (artist ['name']for artist in track ['artists'])
                        search_query =f"{title} {author}"

                        track_results =await wavelink .Playable .search (search_query ,source =wavelink .enums .TrackSource .YouTube )
                        if track_results :
                            await vc .queue .put_wait (track_results [0 ])
                            c +=1 
                    except Exception as e :
                        continue 

                await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added **{c}** tracks from album **[{album_info['name']}](https://discord.gg/JxCFmz9nZP)** to the queue.",color =0x000000 ))
                if not vc .playing :
                    next_track =await vc .queue .get_wait ()
                    await vc .play (next_track )
                    await self .display_player_embed (vc ,next_track ,ctx )

        except Exception as e :
            pass 

    def create_progress_bar (self ,completed ,total ,length =10 ):
        try :
            filled_length =int (length *(completed /total ))
            bar ='█'*filled_length +'░'*(length -filled_length )
            return bar 
        except Exception as e :
            return '░'*length 


    class SimplePaginator :
        def __init__ (self ,entries ,title ,description ,per_page =10 ,color =0x000000 ):
            self .entries =entries 
            self .title =title 
            self .description =description 
            self .per_page =per_page 
            self .color =color 

        def get_page (self ,page =0 ):
            start =page *self .per_page 
            end =start +self .per_page 
            page_entries =self .entries [start :end ]

            embed =discord .Embed (title =self .title ,description =self .description ,color =self .color )
            for entry in page_entries :
                embed .add_field (name ="\u200b",value =entry ,inline =False )

            return embed 


    @commands .hybrid_group (name ="music",invoke_without_command =True ,description ="Music player commands.")
    async def music (self ,ctx ):
        await ctx .send_help (ctx .command )


    @commands .command (name ="play",aliases =['p'],description ="Plays a song or playlist.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def play_prefix (self ,ctx :commands .Context ,*,query :str ):
        await self .play (ctx ,query =query )

    @commands .command (name ="search",description ="Searches music from multiple platforms.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def search_prefix (self ,ctx :commands .Context ,*,query :str ):
        await self .search2 (ctx ,query =query )

    @commands .command (name ="nowplaying",aliases =["current","playing"],description ="Shows the info about current playing song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def nowplaying_prefix (self ,ctx :commands .Context ):
        await self .nowplaying (ctx )

    @commands .command (name ="autoplay",description ="Toggles autoplay mode.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def autoplay_prefix (self ,ctx :commands .Context ):
        await self .autoplay (ctx )

    @commands .command (name ="loop",description ="Toggles loop mode.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def loop_prefix (self ,ctx :commands .Context ):
        await self .loop (ctx )

    @commands .command (name ="pause",description ="Pauses the current song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def pause_prefix (self ,ctx :commands .Context ):
        await self .pause (ctx )

    @commands .command (name ="resume",description ="Resumes the paused song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def resume_prefix (self ,ctx :commands .Context ):
        await self .resume (ctx )

    @commands .command (name ="skip",description ="Skips the current song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def skip_prefix (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc or not vc .playing :
            await ctx .send (embed =discord .Embed (description ="No song is currently playing.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        await vc .stop ()
        await ctx .send (embed =discord .Embed (description =f"Skipped by {ctx.author.mention}.",color =0x000000 ))

    @commands .command (name ="shuffle",description ="Shuffles the queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def shuffle_prefix (self ,ctx :commands .Context ):
        await self .shuffle (ctx )

    @commands .command (name ="stop",description ="Stops the current song and clears the queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def stop_prefix (self ,ctx :commands .Context ):
        await self .stop (ctx )

    @commands .command (name ="volume",aliases =["vol"],description ="Sets the volume of the player.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def volume_prefix (self ,ctx :commands .Context ,level :int ):
        await self .volume (ctx ,level )

    @commands .command (name ="queue",aliases =["playlist"],description ="Shows the current queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def queue_prefix (self ,ctx :commands .Context ):
        await self .queue (ctx )

    @commands .command (name ="clearqueue",aliases =["empty"],description ="Clears the queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def clearqueue_prefix (self ,ctx :commands .Context ):
        await self .clearqueue (ctx )

    @commands .command (name ="replay",description ="Replays the current song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def replay_prefix (self ,ctx :commands .Context ):
        await self .replay (ctx )

    @commands .command (name ="join",aliases =["connect"],description ="Joins the voice channel.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def join_prefix (self ,ctx :commands .Context ):
        await self .join (ctx )

    @commands .command (name ="disconnect",aliases =["dc","leave"],description ="Disconnects the bot from the voice channel.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def disconnect_prefix (self ,ctx :commands .Context ):
        await self .disconnect (ctx )

    @commands .command (name ="seek",description ="Seeks to a specific percentage of the song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def seek_prefix (self ,ctx :commands .Context ,percentage :int ):
        await self .seek (ctx ,percentage )

    @commands .command (name ="remove",description ="Removes a song from the queue at the specified position.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def remove_prefix (self ,ctx :commands .Context ,position :int ):
        await self .remove (ctx ,position )

    @commands .command (name ="move",description ="Moves a song in the queue from one position to another.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def move_prefix (self ,ctx :commands .Context ,from_pos :int ,to_pos :int ):
        await self .move (ctx ,from_pos ,to_pos )

    @commands .command (name ="lyrics",description ="Gets lyrics for the current song or specified song.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def lyrics_prefix (self ,ctx :commands .Context ,*,song :str =None ):
        await self .lyrics (ctx ,song =song )

    @commands .command (name ="twentyfourseven",aliases =['24/7','247'],description ="Enables or disables 24/7 mode for the bot.")
    @commands .has_permissions (manage_guild =True )
    @commands .cooldown (1 ,5 ,commands .BucketType .guild )
    async def twentyfourseven_prefix (self ,ctx :commands .Context ,action :str ,channel :discord .VoiceChannel =None ):
        await self .twentyfourseven (ctx ,action ,channel )

    @commands .command (name ="musicstats",aliases =['mstats'],description ="Shows your music listening statistics.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def musicstats_prefix (self ,ctx :commands .Context ,user :discord .Member =None ):
        await self .stats (ctx ,user )

    @commands .command (name ="musiccard",aliases =['mcard'],description ="Shows your music card.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def musiccard_prefix (self ,ctx :commands .Context ,user :discord .Member =None ):
        await self .musiccard (ctx ,user )

    @commands .command (name ="favorite",aliases =['fav'],description ="Add current song to favorites or manage favorites.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def favorite_prefix (self ,ctx :commands .Context ,action :str ="add"):
        await self .favorite (ctx ,action )

    @commands .command (name ="playfavorites",aliases =['pfav'],description ="Play songs from your favorites.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def playfavorites_prefix (self ,ctx :commands .Context ):
        await self .playfavorites (ctx )

    @commands .command (name ="history",description ="Shows your recently played songs.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def history_prefix (self ,ctx :commands .Context ):
        await self .history (ctx )

    @commands .command (name ="smartqueue",aliases =['sq'],description ="Enable smart queue suggestions.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def smartqueue_prefix (self ,ctx :commands .Context ):
        await self .smartqueue (ctx )

    @commands .command (name ="crossfade",aliases =['cf'],description ="Toggle crossfade between tracks.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def crossfade_prefix (self ,ctx :commands .Context ):
        await self .crossfade (ctx )

    @commands .command (name ="musicleaderboard",aliases =['mlb','mtop'],description ="Shows the music listening leaderboard.")
    @commands .cooldown (1 ,10 ,commands .BucketType .user )
    async def musicleaderboard_prefix (self ,ctx :commands .Context ):
        await self .musicleaderboard (ctx )

    @commands .command (name ="queuemanager",aliases =['qm'],description ="Advanced queue management with filters and sorting.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def queuemanager_prefix (self ,ctx :commands .Context ,action :str ="view",*,filter_query :str =None ):
        await self .queuemanager (ctx ,action ,filter_query =filter_query )

    @commands .command (name ="musicexport",aliases =['mexport'],description ="Export your current queue or favorites.")
    @commands .cooldown (1 ,10 ,commands .BucketType .user )
    async def export_prefix (self ,ctx :commands .Context ,export_type :str ="queue"):
        await self .export (ctx ,export_type )

    @music .command (name ="twentyfourseven",aliases =['24/7','247'],description ="Enables or disables 24/7 mode for the bot.")
    @app_commands .describe (action ="Action: enable/disable/stop",channel ="Voice channel for 24/7 mode (optional)")
    @commands .has_permissions (manage_guild =True )
    @commands .cooldown (1 ,5 ,commands .BucketType .guild )
    async def twentyfourseven (self ,ctx :commands .Context ,action :str ,channel :discord .VoiceChannel =None ):
        guild_id =str (ctx .guild .id )

        if action .lower ()in ['enable','on']:
            if not channel :
                if not ctx .author .voice :
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to specify a voice channel or be in one.",color =0xFF0000 ))
                    return 
                channel =ctx .author .voice .channel 

            self .twentyfourseven_channels [guild_id ]=channel .id 
            save_247_channels (self .twentyfourseven_channels )


            if not ctx .voice_client :
                try :
                    await channel .connect (cls =wavelink .Player )
                except Exception as e :
                    await ctx .send (embed =discord .Embed (description =f"Failed to connect to {channel.mention}: {str(e)}",color =0xFF0000 ))
                    return 

            await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | 24/7 mode enabled for {channel.mention}. The bot will stay connected to this channel.",color =0x000000 ))

        elif action .lower ()in ['disable','off']:
            if guild_id in self .twentyfourseven_channels :
                del self .twentyfourseven_channels [guild_id ]
                save_247_channels (self .twentyfourseven_channels )
                await ctx .send (embed =discord .Embed (description ="<:icon_tick:1372375089668161597> | 24/7 mode disabled. The bot will now disconnect when inactive.",color =0x000000 ))
            else :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | 24/7 mode is not enabled for this server.",color =0xFF0000 ))

        elif action .lower ()=='stop':
            vc =ctx .voice_client 
            if not vc :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0xFF0000 ))
                return 

            if vc .playing :
                await vc .stop ()
            vc .queue .clear ()
            try :
                await vc .channel .edit (status =None )
            except Exception as e :
                pass 
            await ctx .send (embed =discord .Embed (description ="<:icon_tick:1372375089668161597> | Playback stopped but staying connected (24/7 mode).",color =0x000000 ))

        else :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Use `enable`, `disable`, or `stop` as the action.",color =0xFF0000 ))

    @music .command (name ="play",aliases =['p'],description ="Plays a song or playlist.")
    @app_commands .describe (query ="Song name, URL, or search query")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def play (self ,ctx :commands .Context ,*,query :str ):
        if not ctx .author .voice :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in a voice channel to use this command.",color =0x000000 ))
            return 


        if any (x in query .lower ()for x in ['spotify.com','youtube.com','youtu.be','soundcloud.com']):
            await self .play_source (ctx ,query )
            return 


        user_key =f"{ctx.guild.id}_{ctx.author.id}"
        vc =ctx .voice_client 

        if user_key in self .user_platform_preferences and vc and vc .playing :

            preferred_source =self .user_platform_preferences [user_key ]
            await self .play_with_source (ctx ,query ,preferred_source )
            return 


        embed =discord .Embed (
        title ="🎵 Music Platform Selection",
        description =f"**Search Query:** `{query}`\n\n**Choose your preferred platform to search:**\n\n<:yt:1373931239123189810> **YouTube** - World's largest video platform\n<:SoundCloud:1373930998005370900> **SoundCloud** - Independent artists & creators",
        color =0x000000 
        )
        embed .add_field (
        name ="💡 Tips",
        value ="• YouTube has the largest music library\n• SoundCloud features unique remixes & covers\n• Your choice will be remembered while music is playing",
        inline =False 
        )
        embed .set_footer (text ="⏱️ This selection expires in 60 seconds • Click a button below to continue")
        embed .set_thumbnail (url =self .client .user .avatar .url if self .client .user .avatar else None )
        await ctx .send (embed =embed ,view =PlatformSelectView (ctx ,query ))

    @music .command (name ="search",description ="Searches music from multiple platforms.")
    @app_commands .describe (query ="Song name or search query")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def search2 (self ,ctx :commands .Context ,*,query :str ):
        if not ctx .author .voice :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in a voice channel to use this command.",color =0x000000 ))
            return 

        embed =discord .Embed (
        title ="🎵 Music Platform Selection",
        description =f"**Search Query:** `{query}`\n\n**Choose your preferred platform to search:**\n\n<:yt:1373931239123189810> **YouTube** - World's largest video platform\n<:SoundCloud:1373930998005370900> **SoundCloud** - Independent artists & creators",
        color =0x000000 
        )
        embed .add_field (
        name ="💡 Tips",
        value ="• YouTube has the largest music library\n• SoundCloud features unique remixes & covers",
        inline =False 
        )
        embed .set_footer (text ="⏱️ This selection expires in 60 seconds • Click a button below to continue")
        embed .set_thumbnail (url =self .client .user .avatar .url if self .client .user .avatar else None )
        await ctx .send (embed =embed ,view =PlatformSelectView (ctx ,query ))

    @music .command (name ="nowplaying",aliases =["current","playing"],description ="Shows the info about current playing song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def nowplaying (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc or not vc .playing :
            await ctx .send (embed =discord .Embed (description ="No song is currently playing.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="You need to be in the same voice channel as me to use this command.",color =0x000000 ))
            return 

        track =vc .current 
        position =vc .position /1000 
        length =track .length /1000 

        progress_bar =self .create_progress_bar (position ,length ,length =10 )
        position_str =f"{int(position // 60)}:{int(position % 60):02}"
        length_str =f"{int(length // 60)}:{int(length % 60):02}"

        queue_length =len (vc .queue )if vc .queue else 0 

        if "spotify"in track .uri :
            source_name ="Spotify"
        elif "youtube"in track .uri :
            source_name ="YouTube"
        elif "soundcloud"in track .uri :
            source_name ="SoundCloud"
        else :
            source_name ="Unknown Source"

        embed =discord .Embed (
        title ="Now Playing",
        color =0x000000 if source_name =="Spotify"else 0x000000 
        )
        embed .add_field (name ="Track",value =f"[{track.title}]({track.uri})",inline =False )
        embed .add_field (name ="Song By",value =track .author ,inline =False )
        embed .add_field (name ="Progress",value =f"{position_str} [{progress_bar}] {length_str}",inline =False )
        embed .add_field (name ="Duration",value =length_str ,inline =False )
        embed .add_field (name ="Queue Length",value =str (queue_length ),inline =False )
        embed .add_field (name ="Source",value =f"{source_name} - [Link]({track.uri})",inline =False )
        embed .set_thumbnail (url =track .artwork if track .artwork else "")
        embed .set_footer (text =f"Requested by {ctx.author.display_name}",icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )

        await ctx .send (embed =embed )

    @music .command (name ="autoplay",description ="Toggles autoplay mode.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def autoplay (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        vc .autoplay =(
        wavelink .AutoPlayMode .enabled if vc .autoplay !=wavelink .AutoPlayMode .enabled else wavelink .AutoPlayMode .disabled 
        )
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Autoplay {'enabled' if vc.autoplay == wavelink.AutoPlayMode.enabled else 'disabled'} by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="loop",description ="Toggles loop mode.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def loop (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        vc .queue .mode =wavelink .QueueMode .loop if vc .queue .mode !=wavelink .QueueMode .loop else wavelink .QueueMode .normal 
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Loop {'enabled' if vc.queue.mode == wavelink.QueueMode.loop else 'disabled'} by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="pause",description ="Pauses the current song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def pause (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc or not vc .playing :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No song is currently playing.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if vc .playing and not vc .paused :
            await vc .pause (True )
            try :
                await vc .channel .edit (status =f"<:music_stop:1373925462828650592> Paused: {vc.current.title}")
            except Exception as e :
                pass 
            await ctx .send (embed =discord .Embed (description =f"Paused by {ctx.author.mention}.",color =0x000000 ))
        else :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Nothing is playing or already paused.",color =0xFF0000 ))

    @music .command (name ="resume",description ="Resumes the paused song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def resume (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if vc .paused :
            await vc .pause (False )
            try :
                await vc .channel .edit (status =f"<:music:1373174130907807814> Playing: {vc.current.title}")
            except Exception as e :
                pass 
            await ctx .send (embed =discord .Embed (description =f"Resumed by {ctx.author.mention}.",color =0x000000 ))
        else :
            await ctx .send (embed =discord .Embed (description ="Player is not paused.",color =0xFF0000 ))

    @music .command (name ="skip",description ="Skips the current song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def skip (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc or not vc .playing :
            await ctx .send (embed =discord .Embed (description ="No song is currently playing.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        await vc .stop ()
        await ctx .send (embed =discord .Embed (description =f"Skipped by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="shuffle",description ="Shuffles the queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def shuffle (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if vc .queue :
            random .shuffle (vc .queue )
            await ctx .send (embed =discord .Embed (description =f"Queue shuffled by {ctx.author.mention}.",color =0x000000 ))
        else :
            await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0xFF0000 ))

    @music .command (name ="stop",description ="Stops the current song and clears the queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def stop (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        try :
            await vc .channel .edit (status =None )
        except Exception as e :
            pass 
        vc .queue .clear ()
        await vc .disconnect (force =True )
        await ctx .send (embed =discord .Embed (description =f"Stopped and queue cleared by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="volume",aliases =["vol"],description ="Sets the volume of the player.")
    @app_commands .describe (level ="Volume level (1-100)")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def volume (self ,ctx :commands .Context ,level :int ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if level <1 or level >100 :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Volume must be between 1 and 100.",color =0xFF0000 ))
            return 

        await vc .set_volume (level )
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Volume set to {level}% by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="queue",aliases =["playlist"],description ="Shows the current queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def queue (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if not vc .queue :
            await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0x000000 ))
            return 

        queue_entries =[]
        for i ,track in enumerate (vc .queue [:20 ],start =1 ):
            duration =f"{track.length // 1000 // 60}:{track.length // 1000 % 60:02d}"
            queue_entries .append (f"**{i}.** [{track.title}]({track.uri}) - `{duration}`")

        embed =discord .Embed (title ="Music Queue",color =0x000000 )
        embed .description ="\n".join (queue_entries )

        if len (vc .queue )>20 :
            embed .set_footer (text =f"Showing first 20 tracks of {len(vc.queue)} total tracks.")
        else :
            embed .set_footer (text =f"Total tracks in queue: {len(vc.queue)}")

        await ctx .send (embed =embed )

    @music .command (name ="clearqueue",aliases =["empty"],description ="Clears the queue.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def clearqueue (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if not vc .queue :
            await ctx .send (embed =discord .Embed (description ="Queue is already empty.",color =0xFF0000 ))
            return 

        vc .queue .clear ()
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Queue cleared by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="replay",description ="Replays the current song.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def replay (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc or not vc .playing :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No song is currently playing.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        await vc .seek (0 )
        await ctx .send (embed =discord .Embed (description ="<:icon_tick:1372375089668161597> | Replaying the current track.",color =0x000000 ))

    @music .command (name ="join",aliases =["connect"],description ="Joins the voice channel.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def join (self ,ctx :commands .Context ):
        if not ctx .author .voice :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in a voice channel to use this command.",color =0x000000 ))
            return 

        if ctx .voice_client :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | I'm already connected to a voice channel.",color =0xFF0000 ))
            return 

        try :
            vc =await ctx .author .voice .channel .connect (cls =wavelink .Player ,timeout =10.0 ,self_deaf =True )
            vc .ctx =ctx 
            await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Joined {ctx.author.voice.channel.mention}.",color =0x000000 ))
        except Exception as e :
            await ctx .send (embed =discord .Embed (description =f"<:dange:1373926757987520532> | Failed to join voice channel: {str(e)}",color =0xFF0000 ))

    @music .command (name ="disconnect",aliases =["dc","leave"],description ="Disconnects the bot from the voice channel.")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def disconnect (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | I'm not connected to any voice channel.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        try :
            await vc .channel .edit (status =None )
        except Exception as e :
            pass 
        await vc .disconnect ()
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Disconnected by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="seek",description ="Seeks to a specific percentage of the song.")
    @app_commands .describe (percentage ="Percentage to seek to (0-100)")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def seek (self ,ctx :commands .Context ,percentage :int ):
        vc =ctx .voice_client 
        if not vc or not vc .playing :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No song is currently playing.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if percentage <0 or percentage >100 :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Percentage must be between 0 and 100.",color =0xFF0000 ))
            return 

        track =vc .current 
        position =int ((percentage /100 )*track .length )
        await vc .seek (position )
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Seeked to {percentage}% of the track.",color =0x000000 ))

    @music .command (name ="remove",description ="Removes a song from the queue at the specified position.")
    @app_commands .describe (position ="Position of the song to remove (1-based)")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def remove (self ,ctx :commands .Context ,position :int ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if not vc .queue :
            await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0xFF0000 ))
            return 

        if position <1 or position >len (vc .queue ):
            await ctx .send (embed =discord .Embed (description =f"<:dange:1373926757987520532> | Position must be between 1 and {len(vc.queue)}.",color =0xFF0000 ))
            return 

        removed_track =vc .queue [position -1 ]
        del vc .queue [position -1 ]
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Removed **{removed_track.title}** from position {position}.",color =0x000000 ))

    @music .command (name ="move",description ="Moves a song in the queue from one position to another.")
    @app_commands .describe (from_pos ="Current position of the song",to_pos ="New position for the song")
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def move (self ,ctx :commands .Context ,from_pos :int ,to_pos :int ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if not vc .queue :
            await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0xFF0000 ))
            return 

        if from_pos <1 or from_pos >len (vc .queue )or to_pos <1 or to_pos >len (vc .queue ):
            await ctx .send (embed =discord .Embed (description =f"<:dange:1373926757987520532> | Positions must be between 1 and {len(vc.queue)}.",color =0xFF0000 ))
            return 

        track =vc .queue .pop (from_pos -1 )
        vc .queue .insert (to_pos -1 ,track )
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Moved **{track.title}** from position {from_pos} to {to_pos}.",color =0x000000 ))

    @music .command (name ="lyrics",description ="Gets lyrics for the current song or specified song.")
    @app_commands .describe (song ="Song name to search lyrics for (optional)")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def lyrics (self ,ctx :commands .Context ,*,song :str =None ):
        if not self .genius :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Lyrics feature is not available. Please set the GENIUS_API_KEY environment variable.",color =0xFF0000 ))
            return 

        vc =ctx .voice_client 

        if song is None :
            if not vc or not vc .playing :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No song is currently playing and no song specified.",color =0x000000 ))
                return 
            song =f"{vc.current.title} {vc.current.author}"

        try :
            async with ctx .typing ():

                genius_song =self .genius .search_song (song )

                if not genius_song :

                    song_parts =song .split ()
                    if len (song_parts )>2 :
                        simplified_song =" ".join (song_parts [:3 ])
                        genius_song =self .genius .search_song (simplified_song )

                if not genius_song :
                    embed =discord .Embed (
                    description =f"<:dange:1373926757987520532> | Could not find lyrics for **{song}**.\n\n**Suggestions:**\n• Try searching with just the song title\n• Check if the song name is spelled correctly\n• Some songs may not be available on Genius",
                    color =0xFF0000 
                    )
                    await ctx .send (embed =embed )
                    return 

                lyrics =genius_song .lyrics 
                if not lyrics or lyrics .strip ()=="":
                    await ctx .send (embed =discord .Embed (description =f"<:dange:1373926757987520532> | No lyrics found for **{genius_song.title}**.",color =0xFF0000 ))
                    return 


                if len (lyrics )>4000 :
                    lyrics =lyrics [:4000 ]+"...\n\n*[Lyrics truncated due to length]*"

                embed =discord .Embed (
                title =f"🎵 Lyrics for {genius_song.title}",
                description =lyrics ,
                color =0x000000 
                )
                embed .add_field (name ="Artist",value =genius_song .artist ,inline =True )
                embed .add_field (name ="Source",value ="[View on Genius](https://genius.com)",inline =True )
                embed .set_footer (text ="Powered by Genius API")

                await ctx .send (embed =embed )

        except Exception as e :
            error_msg =str (e )


            if "403"in error_msg or "Forbidden"in error_msg :
                error_description =(
                "<:dange:1373926757987520532> | **Lyrics service temporarily unavailable**\n\n"
                "**Possible causes:**\n"
                "• API rate limit exceeded\n"
                "• Invalid API key configuration\n"
                "• Service temporarily down\n\n"
                "**Please try again later or contact the bot administrator.**"
                )
            elif "404"in error_msg or "Not Found"in error_msg :
                error_description =f"<:dange:1373926757987520532> | Song **{song}** not found in lyrics database."
            elif "timeout"in error_msg .lower ():
                error_description ="<:dange:1373926757987520532> | Request timed out. Please try again later."
            else :
                error_description =f"<:dange:1373926757987520532> | An error occurred while fetching lyrics.\n\n**Error:** {error_msg}"

            embed =discord .Embed (description =error_description ,color =0xFF0000 )
            await ctx .send (embed =embed )


    async def musiccard (self ,ctx :commands .Context ,user :discord .Member =None ):
        if user is None :
            user =ctx .author 

        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :

                cursor =await db .execute ("""
                    SELECT total_songs_played, total_listening_time, favorite_song, favorite_artist
                    FROM user_music_stats WHERE user_id = ? AND guild_id = ?
                """,(user .id ,ctx .guild .id ))
                stats =await cursor .fetchone ()

                if not stats :
                    await ctx .send (embed =discord .Embed (description =f"No music stats found for {user.display_name}.",color =0x000000 ))
                    return 


                cursor =await db .execute ("""
                    SELECT song_title, song_artist, COUNT(*) as play_count
                    FROM song_history WHERE user_id = ? AND guild_id = ?
                    GROUP BY song_title, song_artist
                    ORDER BY play_count DESC LIMIT 1
                """,(user .id ,ctx .guild .id ))
                favorite =await cursor .fetchone ()


                cursor =await db .execute ("""
                    SELECT song_title, song_artist, played_at
                    FROM song_history WHERE user_id = ? AND guild_id = ?
                    ORDER BY played_at DESC LIMIT 5
                """,(user .id ,ctx .guild .id ))
                recent_songs =await cursor .fetchall ()


                async with ctx .typing ():
                    card_file =await self .create_modern_music_card (user ,stats ,favorite ,recent_songs )

                    if card_file :
                        embed =discord .Embed (
                        title =f"🎵 {user.display_name}'s Music Card",
                        description ="Beautiful music statistics dashboard",
                        color =0x5865F2 
                        )
                        embed .set_image (url ="attachment://music_stats.png")
                        embed .set_footer (text =f"Requested by {ctx.author.display_name}",icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
                        await ctx .send (embed =embed ,file =card_file )
                    else :
                        await ctx .send (embed =discord .Embed (description ="Failed to generate music card.",color =0xFF0000 ))

        except Exception as e :
            pass 


    async def musicleaderboard (self ,ctx :commands .Context ):
        """Shows music listening leaderboard with visual avatars and stats"""
        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :

                cursor =await db .execute ("""
                    SELECT user_id, total_songs_played, total_listening_time
                    FROM user_music_stats WHERE guild_id = ? AND total_listening_time > 0
                    ORDER BY total_listening_time DESC LIMIT 10
                """,(ctx .guild .id ,))
                top_users =await cursor .fetchall ()

                if not top_users :
                    await ctx .send (embed =discord .Embed (
                    description ="No music statistics found for this server yet!",
                    color =0x000000 
                    ))
                    return 


                async with ctx .typing ():
                    leaderboard_file =await self .create_music_leaderboard_image (ctx .guild ,top_users )

                    if leaderboard_file :
                        embed =discord .Embed (
                        title ="🎵 Music Leaderboard",
                        description =f"Top music listeners in **{ctx.guild.name}**",
                        color =0xFF6384 
                        )
                        embed .set_image (url ="attachment://music_leaderboard.png")
                        embed .set_footer (text =f"Requested by {ctx.author.display_name}",
                        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
                        await ctx .send (embed =embed ,file =leaderboard_file )
                    else :

                        embed =discord .Embed (title ="🎵 Music Leaderboard",color =0xFF6384 )
                        description =f"**Top music listeners in {ctx.guild.name}**\n\n"

                        for i ,(user_id ,songs ,time_seconds )in enumerate (top_users ,1 ):
                            user =ctx .guild .get_member (user_id )
                            if user :
                                hours =time_seconds //3600 
                                minutes =(time_seconds %3600 )//60 
                                time_display =f"{hours}h {minutes}m"if hours >0 else f"{minutes}m"

                                rank_emoji =["🥇","🥈","🥉"][i -1 ]if i <=3 else f"**{i}.**"
                                description +=f"{rank_emoji} **{user.display_name}** - {time_display} ({songs:,} songs)\n"

                        embed .description =description 
                        await ctx .send (embed =embed )

        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))


    async def queuemanager (self ,ctx :commands .Context ,action :str ="view",*,filter_query :str =None ):
        """Advanced queue management system"""
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        if action .lower ()=="view":
            if not vc .queue :
                await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0x000000 ))
                return 


            embed =discord .Embed (title ="🎵 Advanced Queue Manager",color =0x000000 )
            queue_entries =[]

            for i ,track in enumerate (vc .queue [:15 ],start =1 ):
                duration =f"{track.length // 1000 // 60}:{track.length // 1000 % 60:02d}"
                source_emoji ="🟥"if "youtube"in track .source else "🟠"if "soundcloud"in track .source else "🟢"
                queue_entries .append (f"**{i}.** {source_emoji} [{track.title[:35]}{'...' if len(track.title) > 35 else ''}]({track.uri})\n`{track.author}` • `{duration}`")

            embed .description ="\n\n".join (queue_entries )

            if len (vc .queue )>15 :
                embed .set_footer (text =f"Showing 15 of {len(vc.queue)} tracks • Use filters to narrow down")
            else :
                embed .set_footer (text =f"Total: {len(vc.queue)} tracks")

            await ctx .send (embed =embed )

        elif action .lower ()=="dedupe":
            if not vc .queue :
                await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0x000000 ))
                return 

            original_count =len (vc .queue )
            seen_tracks =set ()
            unique_queue =[]

            for track in vc .queue :
                track_id =f"{track.title.lower()}_{track.author.lower()}"
                if track_id not in seen_tracks :
                    seen_tracks .add (track_id )
                    unique_queue .append (track )

            vc .queue .clear ()
            for track in unique_queue :
                await vc .queue .put_wait (track )

            removed_count =original_count -len (unique_queue )
            await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Removed **{removed_count}** duplicate tracks from the queue.",color =0x000000 ))

        elif action .lower ()=="sort":
            if not vc .queue :
                await ctx .send (embed =discord .Embed (description ="Queue is empty.",color =0x000000 ))
                return 

            if not filter_query :
                filter_query ="title"

            queue_list =list (vc .queue )

            if filter_query .lower ()=="title":
                queue_list .sort (key =lambda x :x .title .lower ())
            elif filter_query .lower ()=="artist":
                queue_list .sort (key =lambda x :x .author .lower ())
            elif filter_query .lower ()=="duration":
                queue_list .sort (key =lambda x :x .length )
            else :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Invalid sort option. Use: title, artist, or duration",color =0xFF0000 ))
                return 

            vc .queue .clear ()
            for track in queue_list :
                await vc .queue .put_wait (track )

            await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Queue sorted by **{filter_query}**.",color =0x000000 ))

        elif action .lower ()=="filter":
            if not vc .queue or not filter_query :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Provide a filter query (artist name, title keywords, etc.)",color =0xFF0000 ))
                return 

            filtered_tracks =[]
            for track in vc .queue :
                if (filter_query .lower ()in track .title .lower ()or 
                filter_query .lower ()in track .author .lower ()):
                    filtered_tracks .append (track )

            if not filtered_tracks :
                await ctx .send (embed =discord .Embed (description =f"<:dange:1373926757987520532> | No tracks found matching '{filter_query}'",color =0xFF0000 ))
                return 

            embed =discord .Embed (title =f"🔍 Filtered Results: '{filter_query}'",color =0x000000 )
            filter_entries =[]

            for i ,track in enumerate (filtered_tracks [:10 ],start =1 ):
                duration =f"{track.length // 1000 // 60}:{track.length // 1000 % 60:02d}"
                filter_entries .append (f"**{i}.** [{track.title[:30]}{'...' if len(track.title) > 30 else ''}]({track.uri})\n`{track.author}` • `{duration}`")

            embed .description ="\n\n".join (filter_entries )
            embed .set_footer (text =f"Found {len(filtered_tracks)} matching tracks")
            await ctx .send (embed =embed )

        else :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Available actions: view, dedupe, sort, filter",color =0xFF0000 ))


    async def export (self ,ctx :commands .Context ,export_type :str ="queue"):
        """Export queue or favorites as a text file"""
        try :
            if export_type .lower ()=="queue":
                vc =ctx .voice_client 
                if not vc or not vc .queue :
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No queue to export.",color =0xFF0000 ))
                    return 


                export_data =[]
                export_data .append (f"# {ctx.guild.name} - Music Queue Export")
                export_data .append (f"# Exported by {ctx.author.display_name} on {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                export_data .append (f"# Total tracks: {len(vc.queue)}\n")

                for i ,track in enumerate (vc .queue ,1 ):
                    duration =f"{track.length // 1000 // 60}:{track.length // 1000 % 60:02d}"
                    export_data .append (f"{i}. {track.title}")
                    export_data .append (f"   Artist: {track.author}")
                    export_data .append (f"   Duration: {duration}")
                    export_data .append (f"   URL: {track.uri}")
                    export_data .append ("")

                content ="\n".join (export_data )
                filename =f"queue_export_{ctx.guild.id}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"

            elif export_type .lower ()=="favorites":
                user_key =f"{ctx.guild.id}_{ctx.author.id}"
                if user_key not in self .user_favorites or not self .user_favorites [user_key ]:
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No favorites to export.",color =0xFF0000 ))
                    return 


                export_data =[]
                export_data .append (f"# {ctx.author.display_name}'s Favorite Songs")
                export_data .append (f"# Exported on {discord.utils.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                export_data .append (f"# Total favorites: {len(self.user_favorites[user_key])}\n")

                for i ,fav in enumerate (self .user_favorites [user_key ],1 ):
                    export_data .append (f"{i}. {fav['title']}")
                    export_data .append (f"   Artist: {fav['author']}")
                    export_data .append (f"   Added: {fav['added_at']}")
                    export_data .append (f"   URL: {fav['uri']}")
                    export_data .append ("")

                content ="\n".join (export_data )
                filename =f"favorites_export_{ctx.author.id}_{discord.utils.utcnow().strftime('%Y%m%d_%H%M%S')}.txt"

            else :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Export type must be 'queue' or 'favorites'",color =0xFF0000 ))
                return 


            file_data =io .BytesIO (content .encode ('utf-8'))
            file =discord .File (file_data ,filename =filename )

            embed =discord .Embed (
            title ="📁 Export Complete",
            description =f"Successfully exported your {export_type}!",
            color =0x000000 
            )
            await ctx .send (embed =embed ,file =file )

        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))


    async def favorite (self ,ctx :commands .Context ,action :str ="add"):
        user_key =f"{ctx.guild.id}_{ctx.author.id}"

        if action .lower ()=="add":
            vc =ctx .voice_client 
            if not vc or not vc .playing :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No song is currently playing.",color =0xFF0000 ))
                return 

            track =vc .current 
            if user_key not in self .user_favorites :
                self .user_favorites [user_key ]=[]


            for fav in self .user_favorites [user_key ]:
                if fav ['title']==track .title and fav ['author']==track .author :
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | This song is already in your favorites!",color =0xFF0000 ))
                    return 

            favorite_data ={
            'title':track .title ,
            'author':track .author ,
            'uri':track .uri ,
            'source':track .source ,
            'added_at':discord .utils .utcnow ().isoformat ()
            }

            self .user_favorites [user_key ].append (favorite_data )
            save_user_favorites (self .user_favorites )

            await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Added **{track.title}** to your favorites! ({len(self.user_favorites[user_key])} total)",color =0x000000 ))

        elif action .lower ()=="list":
            if user_key not in self .user_favorites or not self .user_favorites [user_key ]:
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You don't have any favorite songs.",color =0xFF0000 ))
                return 

            favorites =self .user_favorites [user_key ]
            embed =discord .Embed (title ="🎵 Your Favorite Songs",color =0x000000 )

            for i ,fav in enumerate (favorites [:10 ],1 ):
                embed .add_field (
                name =f"{i}. {fav['title'][:40]}{'...' if len(fav['title']) > 40 else ''}",
                value =f"**Artist:** {fav['author']}\n**Added:** <t:{int(discord.utils.parse_time(fav['added_at']).timestamp())}:R>",
                inline =False 
                )

            if len (favorites )>10 :
                embed .set_footer (text =f"Showing 10 of {len(favorites)} favorites. Use 'music playfavorites' to play them!")
            else :
                embed .set_footer (text =f"Total: {len(favorites)} favorites")

            await ctx .send (embed =embed )

        elif action .lower ()=="clear":
            if user_key in self .user_favorites :
                count =len (self .user_favorites [user_key ])
                self .user_favorites [user_key ]=[]
                save_user_favorites (self .user_favorites )
                await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Cleared {count} songs from your favorites.",color =0x000000 ))
            else :
                await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You don't have any favorites to clear.",color =0xFF0000 ))


    async def playfavorites (self ,ctx :commands .Context ):
        if not ctx .author .voice :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in a voice channel to use this command.",color =0x000000 ))
            return 

        user_key =f"{ctx.guild.id}_{ctx.author.id}"
        if user_key not in self .user_favorites or not self .user_favorites [user_key ]:
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You don't have any favorite songs.",color =0xFF0000 ))
            return 

        if not ctx .voice_client :
            try :
                vc =await ctx .author .voice .channel .connect (cls =wavelink .Player ,timeout =10.0 ,self_deaf =True )
            except Exception as e :
                await ctx .send (embed =discord .Embed (description =f"Failed to connect to voice channel: {str(e)}",color =0xFF0000 ))
                return 
        else :
            vc =ctx .voice_client 
        vc .ctx =ctx 

        favorites =self .user_favorites [user_key ]
        added_count =0 

        loading_msg =await ctx .send ("🎵 Loading your favorite songs...")

        for fav in favorites :
            try :

                tracks =await wavelink .Playable .search (f"{fav['title']} {fav['author']}")
                if tracks :
                    await vc .queue .put_wait (tracks [0 ])
                    added_count +=1 
            except Exception as e :
                continue 

        await loading_msg .delete ()

        if added_count >0 :
            await ctx .send (embed =discord .Embed (description =f"<:icons_plus:1373926975407657002> | Added **{added_count}** favorite songs to the queue!",color =0x000000 ))

            if not vc .playing :
                try :
                    next_track =await vc .queue .get_wait ()
                    await vc .play (next_track )
                    await self .display_player_embed (vc ,next_track ,ctx )
                except Exception as e :
                    pass 
        else :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Couldn't find any of your favorite songs.",color =0xFF0000 ))


    async def history (self ,ctx :commands .Context ):
        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :
                cursor =await db .execute ("""
                    SELECT song_title, song_artist, played_at
                    FROM song_history WHERE user_id = ? AND guild_id = ?
                    ORDER BY played_at DESC LIMIT 15
                """,(ctx .author .id ,ctx .guild .id ))
                history =await cursor .fetchall ()

                if not history :
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music history found.",color =0xFF0000 ))
                    return 

                embed =discord .Embed (title ="🕒 Your Music History",color =0x000000 )

                for i ,(title ,artist ,played_at )in enumerate (history ,1 ):
                    try :
                        timestamp =int (discord .utils .parse_time (played_at ).timestamp ())
                        embed .add_field (
                        name =f"{i}. {title[:35]}{'...' if len(title) > 35 else ''}",
                        value =f"**Artist:** {artist}\n**Played:** <t:{timestamp}:R>",
                        inline =True if i %2 ==1 else False 
                        )
                    except :
                        embed .add_field (
                        name =f"{i}. {title[:35]}{'...' if len(title) > 35 else ''}",
                        value =f"**Artist:** {artist}\n**Played:** Recently",
                        inline =True if i %2 ==1 else False 
                        )

                embed .set_footer (text =f"Total songs in history: {len(history)}")
                await ctx .send (embed =embed )

        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))


    async def smartqueue (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :

                cursor =await db .execute ("""
                    SELECT song_artist, COUNT(*) as play_count
                    FROM song_history WHERE user_id = ? AND guild_id = ?
                    GROUP BY song_artist
                    ORDER BY play_count DESC LIMIT 5
                """,(ctx .author .id ,ctx .guild .id ))
                top_artists =await cursor .fetchall ()

                if not top_artists :
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Not enough listening history for smart suggestions.",color =0xFF0000 ))
                    return 

                loading_msg =await ctx .send ("🧠 Generating smart queue suggestions...")
                added_count =0 

                for artist ,_ in top_artists :
                    try :

                        search_query =f"{artist} popular songs"
                        tracks =await wavelink .Playable .search (search_query )
                        if tracks :

                            for track in tracks [:2 ]:
                                await vc .queue .put_wait (track )
                                added_count +=1 
                                if added_count >=10 :
                                    break 
                        if added_count >=10 :
                            break 
                    except Exception as e :
                        continue 

                await loading_msg .delete ()

                if added_count >0 :
                    await ctx .send (embed =discord .Embed (description =f"🧠 Added **{added_count}** smart suggestions to your queue based on your listening history!",color =0x000000 ))
                else :
                    await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | Couldn't generate smart suggestions right now.",color =0xFF0000 ))

        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))


    async def crossfade (self ,ctx :commands .Context ):
        vc =ctx .voice_client 
        if not vc :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | No music player active.",color =0x000000 ))
            return 

        if not ctx .author .voice or ctx .author .voice .channel .id !=vc .channel .id :
            await ctx .send (embed =discord .Embed (description ="<:dange:1373926757987520532> | You need to be in the same voice channel as me to use this command.",color =0xFF0000 ))
            return 

        guild_id =ctx .guild .id 
        current_setting =self .crossfade_enabled .get (guild_id ,False )
        self .crossfade_enabled [guild_id ]=not current_setting 

        status ="enabled"if self .crossfade_enabled [guild_id ]else "disabled"
        await ctx .send (embed =discord .Embed (description =f"<:icon_tick:1372375089668161597> | Crossfade {status} by {ctx.author.mention}.",color =0x000000 ))

    @music .command (name ="stats",description ="Shows your music listening statistics.")
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def stats (self ,ctx :commands .Context ,user :discord .Member =None ):
        if user is None :
            user =ctx .author 

        try :
            import aiosqlite 
            async with aiosqlite .connect ("db/music_stats.db")as db :

                cursor =await db .execute ("""
                    SELECT total_songs_played, total_listening_time, favorite_song, favorite_artist
                    FROM user_music_stats WHERE user_id = ? AND guild_id = ?
                """,(user .id ,ctx .guild .id ))
                stats =await cursor .fetchone ()

                if not stats :
                    await ctx .send (embed =discord .Embed (description =f"No music stats found for {user.display_name}.",color =0x000000 ))
                    return 


                cursor =await db .execute ("""
                    SELECT song_title, song_artist, COUNT(*) as play_count
                    FROM song_history WHERE user_id = ? AND guild_id = ?
                    GROUP BY song_title, song_artist
                    ORDER BY play_count DESC LIMIT 1
                """,(user .id ,ctx .guild .id ))
                favorite =await cursor .fetchone ()


                cursor =await db .execute ("""
                    SELECT song_title, song_artist, played_at
                    FROM song_history WHERE user_id = ? AND guild_id = ?
                    ORDER BY played_at DESC LIMIT 5
                """,(user .id ,ctx .guild .id ))
                recent_songs =await cursor .fetchall ()


                async with ctx .typing ():
                    card_file =await self .create_modern_music_card (user ,stats ,favorite ,recent_songs )

                    total_songs ,total_time =stats [0 ],stats [1 ]
                    hours =total_time //3600 
                    minutes =(total_time %3600 )//60 

                    embed =discord .Embed (
                    title =f"🎵 Music Statistics Dashboard",
                    description =f"**{user.display_name}**'s complete music analytics",
                    color =0x5865F2 
                    )


                    embed .add_field (name ="📊 Songs",value =f"`{total_songs:,}`",inline =True )
                    embed .add_field (name ="⏱️ Time",value =f"`{hours}h {minutes}m`",inline =True )
                    embed .add_field (name ="📈 Rank",value ="`Pro Listener`",inline =True )

                    if favorite :
                        embed .add_field (name ="🎯 Top Track",value =f"`{favorite[0][:30]}{'...' if len(favorite[0]) > 30 else ''}`\nby `{favorite[1]}` • `{favorite[2]} plays`",inline =False )

                    if recent_songs :
                        recent_list =[]
                        for song in recent_songs [:3 ]:
                            song_name =song [0 ][:25 ]+"..."if len (song [0 ])>25 else song [0 ]
                            recent_list .append (f"🎵 `{song_name}` by `{song[1]}`")
                        embed .add_field (name ="🕒 Recently Played",value ="\n".join (recent_list ),inline =False )


                    if card_file :
                        embed .set_image (url ="attachment://music_stats.png")
                        embed .set_footer (text =f"Detailed visual stats above • Requested by {ctx.author.display_name}",
                        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
                        await ctx .send (embed =embed ,file =card_file )
                    else :
                        embed .set_footer (text =f"Requested by {ctx.author.display_name}",
                        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
                        await ctx .send (embed =embed )

        except Exception as e :
            await ctx .send (embed =discord .Embed (color =0xFF0000 ))

    async def create_modern_music_card (self ,user ,stats ,favorite ,recent_songs ):
        """Create a modern, well-aligned music card with perfect spacing and improved colors"""
        try :
            from PIL import Image ,ImageDraw ,ImageFont 
            import aiohttp 


            width ,height =1000 ,700 
            bg_gradient_start =(25 ,20 ,35 )
            bg_gradient_end =(45 ,35 ,60 )
            card_bg =(40 ,35 ,55 )
            accent_primary =(255 ,99 ,132 )
            accent_secondary =(54 ,162 ,235 )
            accent_tertiary =(255 ,205 ,86 )
            text_primary =(255 ,255 ,255 )
            text_secondary =(200 ,200 ,220 )
            section_bg =(55 ,50 ,70 )


            img =Image .new ('RGB',(width ,height ),bg_gradient_start )
            draw =ImageDraw .Draw (img )


            for y in range (height ):
                ratio =y /height 

                r =int (bg_gradient_start [0 ]+(bg_gradient_end [0 ]-bg_gradient_start [0 ])*ratio )
                g =int (bg_gradient_start [1 ]+(bg_gradient_end [1 ]-bg_gradient_start [1 ])*ratio )
                b =int (bg_gradient_start [2 ]+(bg_gradient_end [2 ]-bg_gradient_start [2 ])*ratio )


                if y <height *0.3 :
                    accent_overlay =int (20 *(1 -y /(height *0.3 )))
                    r =min (255 ,r +accent_overlay )
                    b =min (255 ,b +accent_overlay )

                draw .line ([(0 ,y ),(width ,y )],fill =(r ,g ,b ))



            for i in range (5 ):
                x =width -100 +i *15 
                y =50 +i *20 
                draw .ellipse ([x ,y ,x +8 ,y +8 ],fill =(255 ,255 ,255 ,30 ))
                draw .ellipse ([x +3 ,y +15 ,x +11 ,y +23 ],fill =(255 ,255 ,255 ,20 ))


            try :
                title_font =ImageFont .truetype ("utils/arial.ttf",32 )
                subtitle_font =ImageFont .truetype ("utils/arial.ttf",18 )
                stat_big_font =ImageFont .truetype ("utils/arial.ttf",42 )
                stat_label_font =ImageFont .truetype ("utils/arial.ttf",16 )
                section_title_font =ImageFont .truetype ("utils/arial.ttf",20 )
                content_font =ImageFont .truetype ("utils/arial.ttf",16 )
                small_font =ImageFont .truetype ("utils/arial.ttf",14 )
            except :
                title_font =ImageFont .load_default ()
                subtitle_font =ImageFont .load_default ()
                stat_big_font =ImageFont .load_default ()
                stat_label_font =ImageFont .load_default ()
                section_title_font =ImageFont .load_default ()
                content_font =ImageFont .load_default ()
                small_font =ImageFont .load_default ()


            margin =30 
            container_x =margin 
            container_y =margin 
            container_width =width -(margin *2 )
            container_height =height -(margin *2 )


            draw .rounded_rectangle ([container_x ,container_y ,container_x +container_width ,container_y +container_height ],
            radius =20 ,fill =card_bg )


            header_padding =40 
            header_y =container_y +header_padding 


            avatar_size =90 
            avatar_x =container_x +header_padding 
            avatar_url =user .avatar .url if user .avatar else user .default_avatar .url 

            try :
                async with aiohttp .ClientSession ()as session :
                    async with session .get (str (avatar_url ))as resp :
                        if resp .status ==200 :
                            avatar_data =io .BytesIO (await resp .read ())
                            avatar_img =Image .open (avatar_data ).convert ("RGBA")
                            avatar_img =avatar_img .resize ((avatar_size ,avatar_size ))


                            mask =Image .new ('L',(avatar_size ,avatar_size ),0 )
                            mask_draw =ImageDraw .Draw (mask )
                            mask_draw .ellipse ((0 ,0 ,avatar_size ,avatar_size ),fill =255 )


                            for glow_layer in range (3 ):
                                glow_size =avatar_size +(12 -glow_layer *3 )
                                glow_x =avatar_x -(6 -glow_layer *1.5 )
                                glow_y =header_y -(6 -glow_layer *1.5 )
                                glow_alpha =80 -glow_layer *25 
                                glow_color =accent_primary if glow_layer ==0 else accent_secondary 


                                glow_overlay =Image .new ('RGBA',(int (glow_size ),int (glow_size )),
                                (*glow_color ,glow_alpha ))
                                glow_mask =Image .new ('L',(int (glow_size ),int (glow_size )),0 )
                                glow_draw =ImageDraw .Draw (glow_mask )
                                glow_draw .ellipse ((0 ,0 ,glow_size ,glow_size ),fill =255 )
                                glow_overlay .putalpha (glow_mask )
                                img .paste (glow_overlay ,(int (glow_x ),int (glow_y )),glow_overlay )

                            avatar_img .putalpha (mask )
                            img .paste (avatar_img ,(avatar_x ,header_y ),avatar_img )
            except :

                draw .ellipse ([avatar_x ,header_y ,avatar_x +avatar_size ,header_y +avatar_size ],
                fill =accent_primary )


            user_info_x =avatar_x +avatar_size +30 
            draw .text ((user_info_x ,header_y +15 ),f"{user.display_name}",fill =text_primary ,font =title_font )
            draw .text ((user_info_x ,header_y +55 ),"🎵 Music Statistics Dashboard",fill =text_secondary ,font =subtitle_font )


            stats_start_y =header_y +avatar_size +50 
            total_songs ,total_time =stats [0 ],stats [1 ]
            hours =total_time //3600 
            minutes =(total_time %3600 )//60 


            stat_box_width =(container_width -(header_padding *2 )-20 )//2 
            stat_box_height =120 
            stat_box_radius =15 


            left_stat_x =container_x +header_padding 


            stat_gradient =Image .new ('RGBA',(stat_box_width ,stat_box_height ),section_bg )
            stat_draw =ImageDraw .Draw (stat_gradient )
            for i in range (stat_box_height ):
                ratio =i /stat_box_height 
                blend_color =tuple (int (section_bg [j ]+(accent_primary [j ]-section_bg [j ])*ratio *0.1 )for j in range (3 ))
                stat_draw .line ([(0 ,i ),(stat_box_width ,i )],fill =blend_color )


            mask =Image .new ('L',(stat_box_width ,stat_box_height ),0 )
            mask_draw =ImageDraw .Draw (mask )
            mask_draw .rounded_rectangle ([0 ,0 ,stat_box_width ,stat_box_height ],radius =stat_box_radius ,fill =255 )
            stat_gradient .putalpha (mask )
            img .paste (stat_gradient ,(left_stat_x ,stats_start_y ),stat_gradient )


            draw .rounded_rectangle ([left_stat_x ,stats_start_y ,left_stat_x +stat_box_width ,stats_start_y +stat_box_height ],
            radius =stat_box_radius ,outline =accent_primary ,width =2 )


            left_content_x =left_stat_x +(stat_box_width //2 )
            draw .text ((left_content_x ,stats_start_y +20 ),"🎵 Total Songs",fill =text_secondary ,font =stat_label_font ,anchor ="mt")
            draw .text ((left_content_x ,stats_start_y +50 ),f"{total_songs:,}",fill =accent_primary ,font =stat_big_font ,anchor ="mt")
            draw .text ((left_content_x ,stats_start_y +95 ),"tracks played",fill =text_secondary ,font =small_font ,anchor ="mt")


            right_stat_x =left_stat_x +stat_box_width +20 


            stat_gradient2 =Image .new ('RGBA',(stat_box_width ,stat_box_height ),section_bg )
            stat_draw2 =ImageDraw .Draw (stat_gradient2 )
            for i in range (stat_box_height ):
                ratio =i /stat_box_height 
                blend_color =tuple (int (section_bg [j ]+(accent_secondary [j ]-section_bg [j ])*ratio *0.1 )for j in range (3 ))
                stat_draw2 .line ([(0 ,i ),(stat_box_width ,i )],fill =blend_color )

            stat_gradient2 .putalpha (mask )
            img .paste (stat_gradient2 ,(right_stat_x ,stats_start_y ),stat_gradient2 )


            draw .rounded_rectangle ([right_stat_x ,stats_start_y ,right_stat_x +stat_box_width ,stats_start_y +stat_box_height ],
            radius =stat_box_radius ,outline =accent_secondary ,width =2 )


            right_content_x =right_stat_x +(stat_box_width //2 )
            draw .text ((right_content_x ,stats_start_y +20 ),"⏱️ Listening Time",fill =text_secondary ,font =stat_label_font ,anchor ="mt")
            time_display =f"{hours}h {minutes}m"if hours >0 else f"{minutes}m"
            draw .text ((right_content_x ,stats_start_y +50 ),time_display ,fill =accent_secondary ,font =stat_big_font ,anchor ="mt")
            draw .text ((right_content_x ,stats_start_y +95 ),"total duration",fill =text_secondary ,font =small_font ,anchor ="mt")


            if favorite :
                most_played_y =stats_start_y +stat_box_height +30 
                most_played_height =90 

                draw .rounded_rectangle ([container_x +header_padding ,most_played_y ,
                container_x +container_width -header_padding ,most_played_y +most_played_height ],
                radius =stat_box_radius ,fill =section_bg )


                content_x =container_x +header_padding +25 
                draw .text ((content_x ,most_played_y +15 ),"🎯 Most Played Track",fill =accent_primary ,font =section_title_font )

                song_title =favorite [0 ]
                artist_name =favorite [1 ]
                play_count =favorite [2 ]


                max_title_length =60 
                if len (song_title )>max_title_length :
                    song_title =song_title [:max_title_length -3 ]+"..."

                draw .text ((content_x ,most_played_y +45 ),song_title ,fill =text_primary ,font =content_font )
                draw .text ((content_x ,most_played_y +65 ),f"by {artist_name} • {play_count} plays",fill =text_secondary ,font =small_font )

                recent_section_y =most_played_y +most_played_height +30 
            else :
                recent_section_y =stats_start_y +stat_box_height +30 


            if recent_songs and recent_section_y +90 <=container_y +container_height -header_padding :
                draw .rounded_rectangle ([container_x +header_padding ,recent_section_y ,
                container_x +container_width -header_padding ,recent_section_y +90 ],
                radius =stat_box_radius ,fill =section_bg )

                content_x =container_x +header_padding +25 
                draw .text ((content_x ,recent_section_y +15 ),"🕒 Recently Played",fill =accent_secondary ,font =section_title_font )

                if recent_songs :
                    recent_song =recent_songs [0 ]
                    song_name =recent_song [0 ]
                    artist_name =recent_song [1 ]


                    if len (song_name )>55 :
                        song_name =song_name [:52 ]+"..."

                    draw .text ((content_x ,recent_section_y +45 ),song_name ,fill =text_primary ,font =content_font )
                    draw .text ((content_x ,recent_section_y +65 ),f"by {artist_name}",fill =text_secondary ,font =small_font )


            img_bytes =io .BytesIO ()
            img .save (img_bytes ,format ='PNG',quality =95 ,optimize =True )
            img_bytes .seek (0 )

            return discord .File (img_bytes ,filename ="music_stats.png")

        except Exception as e :
            print (f"Error creating modern music card: {e}")
            return None 

    async def create_music_leaderboard_image (self ,guild ,top_users ):
        """Create a visual music leaderboard with user avatars and stats"""
        try :
            from PIL import Image ,ImageDraw ,ImageFont 
            import aiohttp 


            width ,height =800 ,600 
            bg_gradient_start =(30 ,25 ,40 )
            bg_gradient_end =(50 ,40 ,65 )
            card_bg =(45 ,40 ,60 )
            accent_primary =(255 ,99 ,132 )
            accent_secondary =(54 ,162 ,235 )
            text_primary =(255 ,255 ,255 )
            text_secondary =(200 ,200 ,220 )


            img =Image .new ('RGB',(width ,height ),bg_gradient_start )
            draw =ImageDraw .Draw (img )


            for y in range (height ):
                ratio =y /height 
                r =int (bg_gradient_start [0 ]+(bg_gradient_end [0 ]-bg_gradient_start [0 ])*ratio )
                g =int (bg_gradient_start [1 ]+(bg_gradient_end [1 ]-bg_gradient_start [1 ])*ratio )
                b =int (bg_gradient_start [2 ]+(bg_gradient_end [2 ]-bg_gradient_start [2 ])*ratio )
                draw .line ([(0 ,y ),(width ,y )],fill =(r ,g ,b ))


            try :
                title_font =ImageFont .truetype ("utils/arial.ttf",28 )
                name_font =ImageFont .truetype ("utils/arial.ttf",18 )
                stats_font =ImageFont .truetype ("utils/arial.ttf",14 )
                rank_font =ImageFont .truetype ("utils/arial.ttf",20 )
            except :
                title_font =name_font =stats_font =rank_font =ImageFont .load_default ()


            margin =30 
            header_y =margin 
            draw .text ((width //2 ,header_y ),f"🎵 {guild.name} Music Leaderboard",
            fill =text_primary ,font =title_font ,anchor ="mt")


            entry_height =50 
            start_y =header_y +60 
            avatar_size =40 

            for i ,(user_id ,songs ,time_seconds )in enumerate (top_users ):
                user =guild .get_member (user_id )
                if not user :
                    continue 

                y_pos =start_y +i *(entry_height +10 )
                if y_pos +entry_height >height -margin :
                    break 


                rank_colors =[accent_primary ,accent_secondary ,(255 ,205 ,86 )]
                rank_color =rank_colors [i ]if i <3 else (100 ,100 ,120 )


                entry_bg =Image .new ('RGBA',(width -margin *2 ,entry_height ),(*card_bg ,180 ))
                entry_mask =Image .new ('L',(width -margin *2 ,entry_height ),0 )
                entry_draw =ImageDraw .Draw (entry_mask )
                entry_draw .rounded_rectangle ([0 ,0 ,width -margin *2 ,entry_height ],radius =10 ,fill =255 )
                entry_bg .putalpha (entry_mask )
                img .paste (entry_bg ,(margin ,y_pos ),entry_bg )


                rank_size =30 
                rank_x =margin +10 
                rank_y =y_pos +(entry_height -rank_size )//2 
                draw .ellipse ([rank_x ,rank_y ,rank_x +rank_size ,rank_y +rank_size ],fill =rank_color )

                rank_text =str (i +1 )
                rank_bbox =draw .textbbox ((0 ,0 ),rank_text ,font =rank_font )
                rank_text_x =rank_x +(rank_size -(rank_bbox [2 ]-rank_bbox [0 ]))//2 
                rank_text_y =rank_y +(rank_size -(rank_bbox [3 ]-rank_bbox [1 ]))//2 
                draw .text ((rank_text_x ,rank_text_y ),rank_text ,fill =text_primary ,font =rank_font )


                avatar_x =rank_x +rank_size +15 
                avatar_y =y_pos +(entry_height -avatar_size )//2 

                try :
                    avatar_url =user .avatar .url if user .avatar else user .default_avatar .url 
                    async with aiohttp .ClientSession ()as session :
                        async with session .get (str (avatar_url ))as resp :
                            if resp .status ==200 :
                                avatar_data =io .BytesIO (await resp .read ())
                                avatar_img =Image .open (avatar_data ).convert ("RGBA")
                                avatar_img =avatar_img .resize ((avatar_size ,avatar_size ))


                                mask =Image .new ('L',(avatar_size ,avatar_size ),0 )
                                mask_draw =ImageDraw .Draw (mask )
                                mask_draw .ellipse ((0 ,0 ,avatar_size ,avatar_size ),fill =255 )
                                avatar_img .putalpha (mask )
                                img .paste (avatar_img ,(avatar_x ,avatar_y ),avatar_img )
                except :

                    draw .ellipse ([avatar_x ,avatar_y ,avatar_x +avatar_size ,avatar_y +avatar_size ],
                    fill =rank_color )


                info_x =avatar_x +avatar_size +15 
                info_y =y_pos +8 


                username =user .display_name [:20 ]+"..."if len (user .display_name )>20 else user .display_name 
                draw .text ((info_x ,info_y ),username ,fill =text_primary ,font =name_font )


                hours =time_seconds //3600 
                minutes =(time_seconds %3600 )//60 
                time_display =f"{hours}h {minutes}m"if hours >0 else f"{minutes}m"
                stats_text =f"🎵 {songs:,} songs • ⏱️ {time_display}"
                draw .text ((info_x ,info_y +22 ),stats_text ,fill =text_secondary ,font =stats_font )


            footer_text =f"🎼 Active music listeners • Generated at {datetime.now().strftime('%H:%M UTC')}"
            footer_bbox =draw .textbbox ((0 ,0 ),footer_text ,font =stats_font )
            footer_x =(width -(footer_bbox [2 ]-footer_bbox [0 ]))//2 
            draw .text ((footer_x ,height -40 ),footer_text ,fill =text_secondary ,font =stats_font )


            img_bytes =io .BytesIO ()
            img .save (img_bytes ,format ='PNG',quality =95 )
            img_bytes .seek (0 )

            return discord .File (img_bytes ,filename ="music_leaderboard.png")

        except Exception as e :
            print (f"Error creating music leaderboard image: {e}")
            return None 


async def setup (client ):
    await client .add_cog (Music (client ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
