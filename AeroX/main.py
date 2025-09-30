import os 
import sys 
import asyncio 
import traceback 
import signal 
from threading import Thread 
from datetime import datetime ,timezone ,timedelta 


if sys .version_info <(3 ,11 ):
    import typing 
    if not hasattr (typing ,'Self'):
        try :
            from typing_extensions import Self 
            typing .Self =Self 
        except ImportError :

            typing .Self =type ('Self',(),{})

import aiohttp 
import discord 
from discord .ext import commands 
from core import Context 
from core .Strelizia import Strelizia 
from utils .Tools import *
from utils .config import *
import jishaku 
import cogs 




async def load_reactionrole ():
    await bot .add_cog (cogs .ReactionRole (bot ))
import aiosqlite 
import logging 
from dotenv import load_dotenv 


class Colors :

    PURPLE ='\033[95m'
    CYAN ='\033[96m'
    PINK ='\033[38;5;213m'
    LAVENDER ='\033[38;5;183m'
    BLUE ='\033[94m'
    GREEN ='\033[92m'
    YELLOW ='\033[93m'
    RED ='\033[91m'
    WHITE ='\033[97m'
    GRAY ='\033[90m'
    DARK_GRAY ='\033[38;5;240m'


    BOLD ='\033[1m'
    DIM ='\033[2m'
    UNDERLINE ='\033[4m'
    RESET ='\033[0m'


    STRELIZIA_PINK ='\033[38;5;219m'
    STRELIZIA_PURPLE ='\033[38;5;141m'
    STRELIZIA_BLUE ='\033[38;5;111m'

def print_strelizia_header ():
    """Print Strelizia's elegant startup header"""
    print (f"\n{Colors.STRELIZIA_PINK}╭─────────────────────────────────────────────────────────────╮{Colors.RESET}")
    print (f"{Colors.STRELIZIA_PINK}│{Colors.RESET}                    {Colors.BOLD}{Colors.STRELIZIA_PURPLE}✦ STRELIZIA ✦{Colors.RESET}                     {Colors.STRELIZIA_PINK}│{Colors.RESET}")
    print (f"{Colors.STRELIZIA_PINK}│{Colors.RESET}            {Colors.DIM}{Colors.WHITE}Elegant • Intelligent • Sophisticated{Colors.RESET}           {Colors.STRELIZIA_PINK}│{Colors.RESET}")
    print (f"{Colors.STRELIZIA_PINK}╰─────────────────────────────────────────────────────────────╯{Colors.RESET}\n")

def print_bot_ready (bot_name ):
    print (f"\n{Colors.STRELIZIA_BLUE}◆{Colors.RESET} {Colors.BOLD}{Colors.GREEN}Authentication successful{Colors.RESET} {Colors.DIM}→{Colors.RESET} {Colors.STRELIZIA_PURPLE}{bot_name}{Colors.RESET}")

def print_error (message ):
    print (f"{Colors.RED}✗{Colors.RESET} {Colors.BOLD}Error:{Colors.RESET} {message}")

def print_loading (message ):
    print (f"{Colors.STRELIZIA_BLUE}◆{Colors.RESET} {Colors.DIM}Loading{Colors.RESET} {Colors.WHITE}{message}{Colors.RESET}{Colors.DIM}...{Colors.RESET}")

def print_success (message ):
    print (f"{Colors.GREEN}✓{Colors.RESET} {Colors.WHITE}{message}{Colors.RESET}")

def print_info (message ):
    print (f"{Colors.STRELIZIA_PURPLE}ⓘ{Colors.RESET} {Colors.WHITE}{message}{Colors.RESET}")

def print_elegant_separator ():
    """Print Strelizia's signature separator"""
    separator =f"{Colors.STRELIZIA_PINK}─{Colors.STRELIZIA_PURPLE}─{Colors.STRELIZIA_BLUE}─{Colors.RESET}"
    print (f"   {separator * 20}")

def print_system_ready ():
    """Print the final system ready message"""
    print_elegant_separator ()
    print (f"\n   {Colors.BOLD}{Colors.STRELIZIA_PURPLE}✦ System Operational ✦{Colors.RESET}")
    print (f"   {Colors.DIM}{Colors.WHITE}Developed with {Colors.STRELIZIA_PINK}♡{Colors.WHITE} by AeroX Development{Colors.RESET}")
    print (f"   {Colors.DIM}{Colors.DARK_GRAY}Ready to serve with elegance and precision{Colors.RESET}\n")
    print_elegant_separator ()
    print ()

def print_status (status ,message ,color =Colors .WHITE ):
    print (f"{color}[{status}]{Colors.RESET} {message}")




load_dotenv ()


logging .basicConfig (
level =logging .CRITICAL ,
format ='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
handlers =[
logging .StreamHandler ()
]
)


logging .getLogger ('discord').setLevel (logging .CRITICAL )
logging .getLogger ('discord.http').setLevel (logging .CRITICAL )
logging .getLogger ('discord.gateway').setLevel (logging .CRITICAL )
logging .getLogger ('discord.client').setLevel (logging .CRITICAL )
logging .getLogger ('wavelink').setLevel (logging .CRITICAL )
logging .getLogger ('wavelink.websocket').setLevel (logging .CRITICAL )


class DatabaseTestFilter (logging .Filter ):
    def filter (self ,record ):
        message =record .getMessage ().lower ()

        if 'database connection test successful'in message :
            return False 
        return True 


for logger_name in ['discord','discord.http','discord.gateway','discord.client']:
    logger =logging .getLogger (logger_name )
    logger .addFilter (DatabaseTestFilter ())
    for handler in logger .handlers :
        handler .addFilter (DatabaseTestFilter ())


logging .getLogger ().addFilter (DatabaseTestFilter ())


logger =logging .getLogger ('bot')
logger .setLevel (logging .CRITICAL )

os .environ ["JISHAKU_NO_DM_TRACEBACK"]="False"
os .environ ["JISHAKU_HIDE"]="True"
os .environ ["JISHAKU_NO_UNDERSCORE"]="True"
os .environ ["JISHAKU_FORCE_PAGINATOR"]="True"


def utc_to_ist (dt ):
    ist_offset =timedelta (hours =5 ,minutes =30 )
    return dt .replace (tzinfo =timezone .utc ).astimezone (timezone (ist_offset ))

class TicketBot (Strelizia ):
    def __init__ (self ):
        super ().__init__ ()
        self .db =None 

    async def setup_hook (self ):
        print_strelizia_header ()
        print_loading ("Initializing database connection")
        try :
            self .db =await aiosqlite .connect ("db/bot_database.db")
            if self .db is None :
                raise Exception ("Failed to connect to database")

            print_success ("Database connection established")
            
            # Update all guild prefixes to use current BOT_PREFIX from environment
            from utils.Tools import updateAllGuildsPrefixFromEnv
            await updateAllGuildsPrefixFromEnv()
            
            print_success ("Database schema initialized")


            await self .db .execute ("""
                CREATE TABLE IF NOT EXISTS tickets (
                    guild_id INTEGER PRIMARY KEY,
                    channel_id INTEGER,
                    role_id INTEGER,
                    category_id INTEGER,
                    log_channel_id INTEGER,
                    ping_role_id INTEGER,
                    embed_title TEXT DEFAULT 'Create a Ticket',
                    embed_description TEXT DEFAULT 'Need assistance? Select a category below to create a ticket, and our support team will assist you shortly! 📩',
                    embed_footer TEXT DEFAULT 'Powered by AeroX Development',
                    embed_image_url TEXT,
                    embed_color INTEGER DEFAULT 16711680,
                    panel_type TEXT DEFAULT 'dropdown'
                )
            """)


            async with self .db .cursor ()as cur :
                await cur .execute ("PRAGMA table_info(tickets)")
                columns =[col [1 ]for col in await cur .fetchall ()]
                if "panel_type"not in columns :
                    await cur .execute ("ALTER TABLE tickets ADD COLUMN panel_type TEXT DEFAULT 'dropdown'")
                if "ping_role_id"not in columns :
                    await cur .execute ("ALTER TABLE tickets ADD COLUMN ping_role_id INTEGER")
                if "embed_color"in columns :
                    await cur .execute ("PRAGMA table_info(tickets)")
                    col_info =[col for col in await cur .fetchall ()if col [1 ]=="embed_color"]
                    if col_info and col_info [0 ][2 ]=="TEXT":
                        await cur .execute ("ALTER TABLE tickets RENAME TO old_tickets")
                        await self .db .execute ("""
                            CREATE TABLE tickets (
                                guild_id INTEGER PRIMARY KEY,
                                channel_id INTEGER,
                                role_id INTEGER,
                                category_id INTEGER,
                                log_channel_id INTEGER,
                                ping_role_id INTEGER,
                                embed_title TEXT DEFAULT 'Create a Ticket',
                                embed_description TEXT DEFAULT 'Need assistance? Select a category below to create a ticket, and our support team will assist you shortly! 📩',
                                embed_footer TEXT DEFAULT 'Powered by AeroX Development',
                                embed_image_url TEXT,
                                embed_color INTEGER DEFAULT 16711680,
                                panel_type TEXT DEFAULT 'dropdown'
                            )
                        """)
                        await cur .execute ("""
                            INSERT INTO tickets (
                                guild_id, channel_id, role_id, category_id, log_channel_id, ping_role_id,
                                embed_title, embed_description, embed_footer, embed_image_url, embed_color, panel_type
                            )
                            SELECT guild_id, channel_id, role_id, category_id, log_channel_id, ping_role_id,
                                   embed_title, embed_description, embed_footer, embed_image_url,
                                   CAST(embed_color AS INTEGER), panel_type
                            FROM old_tickets
                        """)
                        await cur .execute ("DROP TABLE old_tickets")
                        await self .db .commit ()


            await self .db .execute ("""
                CREATE TABLE IF NOT EXISTS ticket_categories (
                    guild_id INTEGER,
                    category_name TEXT,
                    PRIMARY KEY (guild_id, category_name)
                )
            """)


            await self .db .execute ("""
                CREATE TABLE IF NOT EXISTS ticket_panels (
                    guild_id INTEGER,
                    channel_id INTEGER,
                    message_id INTEGER,
                    PRIMARY KEY (guild_id, message_id)
                )
            """)


            await self .db .execute ("""
                CREATE TABLE IF NOT EXISTS guild_blacklist (
                    guild_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    blacklisted_at TEXT
                )
            """)

            await self .db .execute ("""
                CREATE TABLE IF NOT EXISTS user_blacklist (
                    user_id INTEGER PRIMARY KEY,
                    reason TEXT,
                    blacklisted_at TEXT
                )
            """)

            await self .db .commit ()
            print_success ("Database schema initialized")
        except Exception as e :
            print_error (f"Database setup failed: {str(e)}")
            raise 

        print_loading ("Loading core modules")
        try :
            await self .load_extension ("jishaku")
            print_success ("Core utilities loaded")
            await self .load_extension ("cogs")
            print_success ("Command modules loaded")
            print_info ("All modules loaded successfully")
        except Exception as e :
            print_error (f"Failed to load extensions: {e}")
            raise 

        print_loading ("Synchronizing command tree")
        try :
            synced =await self .tree .sync ()
            print_success (f"Command synchronization complete ({len(synced)} commands)")
        except Exception as e :
            print_error (f"Failed to sync commands: {e}")
            raise 

    async def close (self ):
        try :

            if hasattr (self ,'status_rotation'):
                self .status_rotation .cancel ()


            if self .db :
                await self .db .close ()
                print_info ("Database connection gracefully closed")




            import gc 
            for obj in gc .get_objects ():
                if hasattr (obj ,'close')and 'aiosqlite'in str (type (obj )):
                    try :
                        await obj .close ()
                    except :
                        pass 

        except Exception as e :
            print_error (f"Failed to close resources: {e}")
        finally :
            await super ().close ()

client =TicketBot ()
tree =client .tree 


shutdown_flag =False 

def signal_handler (signum ,frame ):
    """Handle SIGTERM and SIGINT signals for graceful shutdown"""
    global shutdown_flag 
    print_info (f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_flag =True 

def setup_signal_handlers ():
    """Setup signal handlers for graceful shutdown"""
    signal .signal (signal .SIGTERM ,signal_handler )
    signal .signal (signal .SIGINT ,signal_handler )

@client .event 
async def on_ready ():
    await client .wait_until_ready ()

    print_bot_ready (client .user .name )



    print_system_ready ()

@client .event 
async def on_interaction (interaction :discord .Interaction ):
    if interaction .type !=discord .InteractionType .component :
        return 
    try :
        custom_id =interaction .data .get ("custom_id")
        if not custom_id :
            print (f"[INTERACTION ERROR] Received interaction without custom_id from user {interaction.user.id}")
            logger .warning ("Received interaction without custom_id")
            return 

        print (f"[INTERACTION] Processing interaction: {custom_id} from user {interaction.user.id} in guild {interaction.guild.id if interaction.guild else 'DM'}")


    except Exception as e :
        print (f"[INTERACTION ERROR] Critical error in interaction handler: {str(e)}")
        print (f"[INTERACTION ERROR] User: {interaction.user.id}, Guild: {interaction.guild.id if interaction.guild else 'None'}")
        print (f"[INTERACTION ERROR] Custom ID: {custom_id}")
        print (f"[INTERACTION ERROR] Traceback: {traceback.format_exc()}")
        logger .error (f"Interaction failed: {str(e)}")
        traceback .print_exc ()
        try :
            if not interaction .response .is_done ():
                await interaction .response .send_message ("An error occurred while handling this interaction.",ephemeral =True )
        except Exception as followup_error :
            print (f"[INTERACTION ERROR] Failed to send error message: {followup_error}")

@client .event 
async def on_command_completion (context :commands .Context )->None :
    if context .author .id ==1070619070468214824 :
        return 

    full_command_name =context .command .qualified_name 
    split =full_command_name .split ("\n")
    executed_command =str (split [0 ])
    webhook_url =WEBHOOK_URL 
    async with aiohttp .ClientSession ()as session :
        webhook =discord .Webhook .from_url (webhook_url ,session =session )

        if context .guild is not None :
            try :
                embed =discord .Embed (color =0x000000 )
                avatar_url =context .author .avatar .url if context .author .avatar else context .author .default_avatar .url 
                embed .set_author (
                name =f"Executed {executed_command} Command By : {context.author}",
                icon_url =avatar_url 
                )
                embed .set_thumbnail (url =avatar_url )
                embed .add_field (
                name ="<:arrow:1373603890309890059> Command Name :",
                value =f"{executed_command}",
                inline =False 
                )
                embed .add_field (
                name ="<:arrow:1373603890309890059> Guild Name :",
                value =f"{context.guild.name} ({context.guild.id})",
                inline =False 
                )
                embed .add_field (
                name ="<:arrow:1373603890309890059> Channel Name :",
                value =f"{context.channel.name} ({context.channel.id})",
                inline =False 
                )
                embed .add_field (
                name ="<:arrow:1373603890309890059> User :",
                value =f"{context.author} ({context.author.id})",
                inline =False 
                )
                current_time =utc_to_ist (discord .utils .utcnow ())
                embed .timestamp =current_time 
                embed .set_footer (text =f"Command Executed at {current_time.strftime('%I:%M %p IST')}")
                await webhook .send (embed =embed )
            except Exception as e :
                logger .error (f"Error sending command completion webhook: {e}")
                traceback .print_exc ()




TOKEN =os .getenv ("TOKEN")
WEBHOOK_URL =os .getenv ("WEBHOOK_URL")
PREFIX =os .getenv ("PREFIX")

if TOKEN is None :
    logger .error ("TOKEN environment variable not set in .env file. Please ensure your .env file contains the TOKEN.")
    raise ValueError ("TOKEN environment variable not set in .env file. Cannot start the bot.")

if WEBHOOK_URL is None :
    logger .error ("WEBHOOK_URL environment variable not set in .env file. Please ensure your .env file contains the WEBHOOK_URL.")
    raise ValueError ("WEBHOOK_URL environment variable not set in .env file.")

if PREFIX is None :
    logger .error ("PREFIX environment variable not set in .env file. Please ensure your .env file contains the PREFIX.")
    raise ValueError ("PREFIX environment variable not set in .env file.")

async def run_bot ():
    """Run the bot with graceful shutdown handling"""
    try :
        print_loading ("Establishing connection to Discord")
        await client .start (TOKEN )
    except discord .LoginFailure :
        print_error ("Authentication failed - Invalid token configuration")
    except Exception as e :
        print_error (f"Startup failed: {e}")
    finally :
        if not client .is_closed ():
            print_info ("Closing bot connection...")
            await client .close ()

async def main ():
    """Main function with signal handling and graceful shutdown"""
    global shutdown_flag 


    setup_signal_handlers ()


    bot_task =asyncio .create_task (run_bot ())

    try :

        while not bot_task .done ()and not shutdown_flag :
            await asyncio .sleep (0.1 )

        if shutdown_flag :
            print_info ("Shutdown signal received, stopping bot gracefully...")
            await client .close ()
            bot_task .cancel ()
            try :
                await bot_task 
            except asyncio .CancelledError :
                pass 
            print_success ("Bot shutdown completed gracefully")
        else :

            await bot_task 

    except KeyboardInterrupt :
        print_info ("Keyboard interrupt received, shutting down...")
        await client .close ()
        bot_task .cancel ()
        try :
            await bot_task 
        except asyncio .CancelledError :
            pass 
        print_success ("Bot shutdown completed")

if __name__ =='__main__':
    try :
        asyncio .run (main ())
    except Exception as e :
        print_error (f"Critical error: {e}")
        sys .exit (1 )
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
