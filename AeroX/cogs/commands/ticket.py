import discord 
from discord .ext import commands 
from discord import app_commands 
import aiosqlite 
import asyncio 
import datetime 
import logging 
from typing import Optional ,List ,Dict ,Any 
import json 
import io 
from utils .tickets import (
get_ticket_channel ,get_ticket_role ,is_ticket_channel ,
user_has_support_role ,validate_ticket_data ,get_all_support_roles 
)

logger =logging .getLogger ('discord')

class AdvancedTicketSystem (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .cooldowns ={}
        self .panel_refresh_task =None 

    async def cog_load (self ):
        """Initialize the ticket system and start background tasks"""
        await self .setup_database ()

        await self .restore_persistent_panels ()
        self .panel_refresh_task =asyncio .create_task (self .auto_refresh_panels ())

    async def restore_persistent_panels (self ):
        """Restore persistent panel views after bot restart"""
        try :

            await asyncio .sleep (3 )


            try :
                async with aiosqlite .connect ("db/tickets.db")as db :
                    await db .execute ("SELECT 1")
            except Exception as e :
                logger .error (f"Database connection failed during panel restoration: {db_error}")
                return 

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT guild_id, channel_id, message_id, panel_type FROM ticket_panels
                """)as cursor :
                    panels =await cursor .fetchall ()

            if not panels :

                return 

            restored_count =0 
            failed_count =0 

            for guild_id ,channel_id ,message_id ,panel_type in panels :
                try :
                    guild =self .bot .get_guild (guild_id )
                    if not guild :

                        try :
                            guild =await self .bot .fetch_guild (guild_id )
                        except discord .NotFound :
                            logger .debug (f"Guild {guild_id} not found, cleaning up panel entry")
                            async with aiosqlite .connect ("db/tickets.db")as db :
                                await db .execute ("DELETE FROM ticket_panels WHERE guild_id = ?",(guild_id ,))
                                await db .commit ()
                            failed_count +=1 
                            continue 
                        except discord .Forbidden :
                            logger .debug (f"No access to guild {guild_id}, cleaning up panel entry")
                            async with aiosqlite .connect ("db/tickets.db")as db :
                                await db .execute ("DELETE FROM ticket_panels WHERE guild_id = ?",(guild_id ,))
                                await db .commit ()
                            failed_count +=1 
                            continue 
                        except Exception as e :

                            logger .debug (f"Unable to verify guild {guild_id}, skipping panel restoration")
                            failed_count +=1 
                            continue 

                    channel =guild .get_channel (channel_id )
                    if not channel :

                        try :
                            channel =await guild .fetch_channel (channel_id )
                        except discord .NotFound :
                            logger .debug (f"Channel {channel_id} not found in guild {guild.name}, cleaning up entry")
                            async with aiosqlite .connect ("db/tickets.db")as db :
                                await db .execute ("DELETE FROM ticket_panels WHERE channel_id = ?",(channel_id ,))
                                await db .commit ()
                            failed_count +=1 
                            continue 
                        except discord .Forbidden :
                            logger .debug (f"No access to channel {channel_id} in guild {guild.name}")
                            failed_count +=1 
                            continue 
                        except Exception as e :

                            logger .debug (f"Unable to verify channel {channel_id}, skipping panel restoration")
                            failed_count +=1 
                            continue 


                    try :
                        message =await channel .fetch_message (message_id )
                    except discord .NotFound :
                        logger .warning (f"Message {message_id} not found, cleaning up database entry")
                        async with aiosqlite .connect ("db/tickets.db")as db :
                            await db .execute ("DELETE FROM ticket_panels WHERE message_id = ?",(message_id ,))
                            await db .commit ()
                        failed_count +=1 
                        continue 
                    except Exception as e :
                        logger .error (f"Error fetching message {message_id}: {e}")
                        failed_count +=1 
                        continue 


                    categories =[]
                    try :
                        async with aiosqlite .connect ("db/tickets.db")as db :
                            async with db .execute ("""
                                SELECT category_name, category_emoji FROM ticket_categories 
                                WHERE guild_id = ? ORDER BY category_name
                            """,(guild_id ,))as cursor :
                                raw_categories =await cursor .fetchall ()

                        for category_data in raw_categories :
                            if len (category_data )>=2 :
                                name ,emoji =category_data [0 ],category_data [1 ]
                                if name and emoji :
                                    categories .append ((name ,emoji ))

                        if not categories :
                            categories =[("General","🎫")]

                    except Exception as e :
                        logger .error (f"Error getting categories for guild {guild_id}: {cat_error}")
                        categories =[("General","🎫")]


                    try :
                        if panel_type =="dropdown":
                            view =TicketDropdownView (categories ,guild_id )
                        else :
                            view =TicketButtonView (categories ,guild_id )

                        view .timeout =None 
                        self .bot .add_view (view ,message_id =message_id )
                        restored_count +=1 
                        logger .info (f"Restored {panel_type} panel for message {message_id} in guild {guild.name}")

                    except Exception as e :
                        logger .error (f"Error creating view for panel {message_id}: {view_error}")
                        failed_count +=1 

                except Exception as e :
                    logger .error (f"Error restoring panel {message_id}: {e}")
                    failed_count +=1 

            total_panels =len (panels )
            logger .info (f"Panel restoration complete: {restored_count} restored, {failed_count} failed, {total_panels} total")

        except Exception as e :
            logger .error (f"Critical error restoring persistent panels: {e}")
            import traceback 
            logger .error (f"Full traceback: {traceback.format_exc()}")

    async def cog_unload (self ):
        """Clean up tasks when cog is unloaded"""
        if self .panel_refresh_task :
            self .panel_refresh_task .cancel ()

    async def setup_database (self ):
        """Setup all required database tables with comprehensive schema"""
        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("SELECT 1")
            logger .info ("Database connection test successful")

            async with aiosqlite .connect ("db/tickets.db")as db :

                await db .execute ("DROP TABLE IF EXISTS tickets_old")


                try :
                    cursor =await db .execute ("PRAGMA table_info(tickets)")
                    columns_info =await cursor .fetchall ()
                    existing_columns =[col [1 ]for col in columns_info ]


                    required_columns =[
                    'guild_id','channel_id','role_id','category_id','log_channel_id',
                    'ping_role_id','embed_title','embed_description','embed_footer',
                    'embed_color','embed_image','embed_thumbnail'
                    ]


                    missing_columns =[col for col in required_columns if col not in existing_columns ]

                    if missing_columns or not existing_columns :

                        if existing_columns :
                            await db .execute ("ALTER TABLE tickets RENAME TO tickets_backup")


                        await db .execute ("""
                            CREATE TABLE tickets (
                                guild_id INTEGER PRIMARY KEY,
                                channel_id INTEGER,
                                role_id INTEGER,
                                category_id INTEGER,
                                log_channel_id INTEGER,
                                ping_role_id INTEGER,
                                embed_title TEXT DEFAULT '🎫 Create a Support Ticket',
                                embed_description TEXT DEFAULT 'Need help? Click the button below to create a ticket and our support team will assist you!',
                                embed_footer TEXT DEFAULT 'Powered by AeroX Development',
                                embed_color INTEGER DEFAULT 0,
                                embed_image TEXT,
                                embed_thumbnail TEXT
                            )
                        """)


                        if existing_columns :
                            try :

                                common_columns =[col for col in existing_columns if col in required_columns ]
                                if common_columns :
                                    columns_str =', '.join (common_columns )
                                    placeholders =', '.join (['?'for _ in common_columns ])

                                    cursor =await db .execute (f"SELECT {columns_str} FROM tickets_backup")
                                    rows =await cursor .fetchall ()

                                    for row in rows :
                                        await db .execute (
                                        f"INSERT OR REPLACE INTO tickets ({columns_str}) VALUES ({placeholders})",
                                        row 
                                        )

                                await db .execute ("DROP TABLE tickets_backup")
                                logger .info ("Successfully migrated ticket data from backup")
                            except Exception as e :
                                logger .error (f"Error migrating ticket data: {e}")

                        logger .info ("Created new tickets table with correct schema")

                except Exception as e :
                    logger .warning (f"Error checking tickets table: {e}")

                    await db .execute ("DROP TABLE IF EXISTS tickets")
                    await db .execute ("""
                        CREATE TABLE tickets (
                            guild_id INTEGER PRIMARY KEY,
                            channel_id INTEGER,
                            role_id INTEGER,
                            category_id INTEGER,
                            log_channel_id INTEGER,
                            ping_role_id INTEGER,
                            embed_title TEXT DEFAULT '🎫 Create a Support Ticket',
                            embed_description TEXT DEFAULT 'Need help? Click the button below to create a ticket and our support team will assist you!',
                            embed_footer TEXT DEFAULT 'Powered by AeroX Development',
                            embed_color INTEGER DEFAULT 0,
                            embed_image TEXT,
                            embed_thumbnail TEXT
                        )
                    """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_instances (
                        channel_id INTEGER PRIMARY KEY,
                        guild_id INTEGER,
                        creator_id INTEGER,
                        claimer_id INTEGER,
                        closer_id INTEGER,
                        category TEXT DEFAULT 'General',
                        reason TEXT,
                        urgency TEXT DEFAULT 'medium',
                        priority TEXT DEFAULT 'medium',
                        created_at TEXT,
                        claimed_at TEXT,
                        closed_at TEXT,
                        ticket_number INTEGER,
                        status TEXT DEFAULT 'open',
                        is_claimed INTEGER DEFAULT 0
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_categories (
                        guild_id INTEGER,
                        category_name TEXT,
                        category_emoji TEXT DEFAULT '<:icon_tick:1372375089668161597>',
                        discord_category_id INTEGER,
                        PRIMARY KEY (guild_id, category_name)
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_support_roles (
                        guild_id INTEGER,
                        role_id INTEGER,
                        PRIMARY KEY (guild_id, role_id)
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_ratings (
                        ticket_id INTEGER,
                        guild_id INTEGER,
                        user_id INTEGER,
                        rating INTEGER,
                        feedback TEXT,
                        rated_at TEXT,
                        PRIMARY KEY (ticket_id, user_id)
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_panels (
                        guild_id INTEGER,
                        channel_id INTEGER,
                        message_id INTEGER,
                        panel_type TEXT DEFAULT 'dropdown',
                        created_at TEXT,
                        PRIMARY KEY (guild_id, channel_id)
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_messages (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER,
                        channel_id INTEGER,
                        message_id INTEGER,
                        author_id INTEGER,
                        content TEXT,
                        attachments TEXT,
                        timestamp TEXT
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ticket_cooldowns (
                        user_id INTEGER,
                        guild_id INTEGER,
                        last_ticket TEXT,
                        PRIMARY KEY (user_id, guild_id)
                    )
                """)

                await db .commit ()


        except Exception as e :
            logger .error (f"Failed to setup ticket database: {e}")
            raise 

    async def auto_refresh_panels (self ):
        """Background task to refresh panels every 3 days"""
        while True :
            try :
                await asyncio .sleep (3600 )
                await self .refresh_expired_panels ()
            except asyncio .CancelledError :
                break 
            except Exception as e :
                logger .error (f"Error in panel refresh task: {e}")
                await asyncio .sleep (3600 )

    async def refresh_expired_panels (self ):
        """Refresh panels that are older than 3 days"""
        try :
            cutoff =datetime .datetime .utcnow ()-datetime .timedelta (days =3 )

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT guild_id, channel_id, message_id, panel_type 
                    FROM ticket_panels 
                    WHERE datetime(created_at) < ?
                """,(cutoff .isoformat (),))as cursor :
                    expired_panels =await cursor .fetchall ()

                for guild_id ,channel_id ,message_id ,panel_type in expired_panels :
                    try :
                        channel =self .bot .get_channel (channel_id )
                        if channel :
                            try :
                                old_message =await channel .fetch_message (message_id )
                                await old_message .delete ()
                            except :
                                pass 


                            await self .send_ticket_panel (channel ,panel_type )

                    except Exception as e :
                        logger .error (f"Failed to refresh panel {message_id}: {e}")


                await db .execute ("DELETE FROM ticket_panels WHERE datetime(created_at) < ?",(cutoff .isoformat (),))
                await db .commit ()

        except Exception as e :
            logger .error (f"Error refreshing expired panels: {e}")

    async def check_cooldown (self ,user_id :int ,guild_id :int )->bool :
        """Check if user is on cooldown"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT last_ticket FROM ticket_cooldowns 
                    WHERE user_id = ? AND guild_id = ?
                """,(user_id ,guild_id ))as cursor :
                    result =await cursor .fetchone ()

                if result :
                    last_ticket =datetime .datetime .fromisoformat (result [0 ])
                    if datetime .datetime .utcnow ()-last_ticket <datetime .timedelta (seconds =60 ):
                        return False 


                await db .execute ("""
                    INSERT OR REPLACE INTO ticket_cooldowns (user_id, guild_id, last_ticket)
                    VALUES (?, ?, ?)
                """,(user_id ,guild_id ,datetime .datetime .utcnow ().isoformat ()))

                await db .commit ()
                return True 

        except Exception as e :
            logger .error (f"Error checking cooldown: {e}")
            return True 

    async def has_open_ticket (self ,user_id :int ,guild_id :int )->bool :
        """Check if user already has an open ticket"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT channel_id FROM ticket_instances 
                    WHERE creator_id = ? AND guild_id = ? AND status = 'open'
                """,(user_id ,guild_id ))as cursor :
                    result =await cursor .fetchone ()

                if result :

                    channel =self .bot .get_channel (result [0 ])
                    if channel :
                        return True 
                    else :

                        await db .execute ("""
                            UPDATE ticket_instances SET status = 'deleted' 
                            WHERE channel_id = ?
                        """,(result [0 ],))
                        await db .commit ()

                return False 

        except Exception as e :
            logger .error (f"Error checking open tickets: {e}")
            return False 

    def create_branded_embed (self ,title :str ,description :str =None ,color :int =0x000000 )->discord .Embed :
        """Create a consistently branded embed"""
        embed =discord .Embed (title =title ,description =description ,color =color )
        embed .set_author (name ="Strelizia Ticket System",icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None )
        embed .set_footer (text ="Developed By AeroX Development",icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None )
        embed .timestamp =datetime .datetime .utcnow ()
        return embed 

    async def log_ticket_event (self ,guild_id :int ,event_type :str ,data :Dict [str ,Any ]):
        """Log ticket events to the configured log channel with new styled format"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("SELECT log_channel_id FROM tickets WHERE guild_id = ?",(guild_id ,))as cursor :
                    result =await cursor .fetchone ()

                if not result or not result [0 ]:
                    return 

                log_channel =self .bot .get_channel (result [0 ])
                if not log_channel :
                    return 


            guild =self .bot .get_guild (guild_id )
            if not guild :
                return 

            if event_type =="Created":
                creator =guild .get_member (data ['creator_id'])or await self .bot .fetch_user (data ['creator_id'])
                if not creator :
                    return 

                timestamp =int (datetime .datetime .utcnow ().timestamp ())

                embed =discord .Embed (
                title ="Ticket Created",
                description =(
                "╭━━━━━━━━━━━━━━━━━━━━╮\n"
                "┃ 🆕 Created\n"
                f"┃ 👤 User: {creator.display_name}\n"
                f"┃ 🆔 ID: {creator.id}\n"
                f"┃ 🕒 Time: <t:{timestamp}:F>\n"
                "╰━━━━━━━━━━━━━━━━━━━━╯"
                ),
                color =0x57F287 
                )

                embed .set_author (
                name =creator .display_name ,
                icon_url =creator .display_avatar .url 
                )
                embed .set_thumbnail (url =creator .display_avatar .url )
                embed .set_footer (
                text ="Thanks for using Strelizia ❤️",
                icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None 
                )
                embed .timestamp =datetime .datetime .utcnow ()

            elif event_type =="Claimed":
                claimer =guild .get_member (data ['claimer_id'])or await self .bot .fetch_user (data ['claimer_id'])
                creator =guild .get_member (data .get ('creator_id',0 ))or await self .bot .fetch_user (data .get ('creator_id',0 ))if data .get ('creator_id')else None 

                if not claimer :
                    return 

                timestamp =int (datetime .datetime .utcnow ().timestamp ())

                embed =discord .Embed (
                title ="Ticket Claimed",
                description =(
                "╭━━━━━━━━━━━━━━━━━━━━╮\n"
                "┃ 🎯 Claimed\n"
                f"┃ 🧑‍💼 Staff: {claimer.display_name}\n"
                f"┃ 🕒 Time: <t:{timestamp}:F>\n"
                "╰━━━━━━━━━━━━━━━━━━━━╯"
                ),
                color =0x00B0F4 
                )

                if creator :
                    embed .set_author (
                    name =creator .display_name ,
                    icon_url =creator .display_avatar .url 
                    )

                embed .set_thumbnail (url =claimer .display_avatar .url )
                embed .set_footer (
                text ="Thanks for using Strelizia ❤️",
                icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None 
                )
                embed .timestamp =datetime .datetime .utcnow ()

            elif event_type =="Closed":
                closer =guild .get_member (data ['closer_id'])or await self .bot .fetch_user (data ['closer_id'])
                creator =guild .get_member (data ['creator_id'])or await self .bot .fetch_user (data ['creator_id'])

                if not closer or not creator :
                    return 

                timestamp =int (datetime .datetime .utcnow ().timestamp ())

                embed =discord .Embed (
                title ="Ticket Closed",
                description =(
                "╭━━━━━━━━━━━━━━━━━━━━╮\n"
                "┃ 🔒 Closed\n"
                f"┃ 🧑‍💼 Staff: {closer.display_name}\n"
                f"┃ 🕒 Time: <t:{timestamp}:F> • <t:{timestamp}:R>\n"
                "╰━━━━━━━━━━━━━━━━━━━━╯"
                ),
                color =0xED4245 
                )

                embed .set_author (
                name =creator .display_name ,
                icon_url =creator .display_avatar .url 
                )
                embed .set_thumbnail (url =self .bot .user .avatar .url if self .bot .user .avatar else None )
                embed .set_footer (
                text ="Thanks for using Strelizia ❤️",
                icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None 
                )
                embed .timestamp =datetime .datetime .utcnow ()


                if 'transcript'in data :
                    transcript_file =discord .File (
                    io .StringIO (data ['transcript']),
                    filename =f"ticket-{data.get('ticket_number', 'unknown')}-transcript.html"
                    )

                    view =TicketAuthorInfoView (data ['creator_id'])
                    await log_channel .send (embed =embed ,file =transcript_file ,view =view )
                    return 
                else :

                    view =TicketAuthorInfoView (data ['creator_id'])
                    await log_channel .send (embed =embed ,view =view )
                    return 

            elif event_type =="Rated":
                user =guild .get_member (data ['user_id'])or await self .bot .fetch_user (data ['user_id'])
                if not user :
                    return 

                rating =data ['rating']
                stars ="⭐"*rating 


                color =0xFFD700 if rating >=4 else 0x00B0F4 if rating >=3 else 0xFF6B35 if rating >=2 else 0xED4245 


                reaction_emoji ="🥰"if rating ==5 else "😊"if rating ==4 else "😐"if rating ==3 else "😞"if rating ==2 else "😢"

                embed =discord .Embed (
                title ="💝 Customer Feedback Received",
                description =(
                f"╭━━━━━━━━━━━━━━━━━━━━╮\n"
                f"┃ {reaction_emoji} Customer Rating\n"
                f"┃ 🎫 Ticket: #{data.get('ticket_number', 'Unknown')}\n"
                f"┃ ⭐ Rating: {stars} ({rating}/5)\n"
                f"┃ 👤 User: {user.display_name}\n"
                f"╰━━━━━━━━━━━━━━━━━━━━╯"
                ),
                color =color 
                )

                embed .set_author (
                name =user .display_name ,
                icon_url =user .display_avatar .url 
                )
                embed .set_thumbnail (url =user .display_avatar .url )


                if data .get ('feedback')and data ['feedback'].strip ():
                    feedback_text =data ['feedback'][:200 ]+"..."if len (data ['feedback'])>200 else data ['feedback']
                    embed .add_field (
                    name ="💬 Additional Feedback",
                    value =f"```\n{feedback_text}\n```",
                    inline =False 
                    )

                embed .set_footer (
                text ="Thanks for using Strelizia ❤️",
                icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None 
                )
                embed .timestamp =datetime .datetime .utcnow ()

            await log_channel .send (embed =embed )

        except Exception as e :
            logger .error (f"Error logging ticket event: {e}")



    @commands .hybrid_group (invoke_without_command =True ,name ="ticket",description ="🎫 Ticket system commands")
    async def ticket (self ,ctx :commands .Context ):
        """Ticket system commands"""
        if ctx .subcommand_passed is None :
            await ctx .send_help (ctx .command )

    @ticket .command (name ="setup",description ="🎮 Setup the ticket system with interactive dropdowns")
    @commands .has_permissions (manage_guild =True )
    async def setup (self ,ctx :commands .Context ):
        """Complete ticket system setup with dropdowns and customization"""
        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("SELECT * FROM tickets WHERE guild_id = ?",(ctx .guild .id ,))as cursor :
                    existing =await cursor .fetchone ()

            if existing :
                embed =discord .Embed (
                title ="<:icon_danger:1373170993236803688> Ticket System Already Configured",
                description =f"A ticket system is already set up for {ctx.guild.name}. Use `ticket reset` to reset it or other commands to modify it.",
                color =0x000000 
                )
                await ctx .send (embed =embed )
                return 


            embed =self .create_branded_embed (
            "🎮 Ticket System Setup",
            "Please configure your ticket system using the dropdowns below:\n\n"
            "**Step 1:** Select a panel channel\n"
            "**Step 2:** Select a support role\n"
            "**Step 3:** Select a log channel (optional)\n"
            "**Step 4:** Customize your panel (optional)"
            )

            view =TicketSetupView (ctx .author ,ctx .guild ,self )
            message =await ctx .send (embed =embed ,view =view )
            view .message =message 

        except Exception as e :
            logger .error (f"Error in ticket setup: {e}")
            pass 

    @ticket .command (name ="reset",description ="⚠️ Reset the entire ticket system")
    @commands .has_permissions (manage_guild =True )
    async def reset (self ,ctx :commands .Context ):
        """Reset the entire ticket system for the guild"""
        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("SELECT * FROM tickets WHERE guild_id = ?",(ctx .guild .id ,))as cursor :
                    existing =await cursor .fetchone ()

            if not existing :
                embed =self .create_branded_embed (
                "<:icon_danger:1373170993236803688> No Ticket System Found",
                f"No ticket system is configured for {ctx.guild.name}. Use `ticket setup` to create one."
                )
                await ctx .send (embed =embed )
                return 


            view =TicketResetConfirmView (ctx .author ,self ,ctx .guild )
            embed =self .create_branded_embed (
            "<:icon_danger:1373170993236803688> Confirm Ticket System Reset",
            f"**This will completely reset the ticket system for {ctx.guild.name}!**\n\n"
            f"**What will be deleted:**\n"
            f"• All ticket configuration\n"
            f"• All ticket categories and their Discord categories\n"
            f"• All active ticket channels\n"
            f"• All ticket history and ratings\n"
            f"• All support role configurations\n\n"
            f"**<:icon_danger:1372375135604047902> This action cannot be undone!**\n\n"
            f"Click **Confirm Reset** to proceed or **Cancel** to abort."
            )
            embed .color =0x000000 

            await ctx .send (embed =embed ,view =view )

        except Exception as e :
            logger .error (f"Error in ticket reset: {e}")
            pass 

    @ticket .command (name ="close",description ="❌ Close the current ticket")
    async def close (self ,ctx :commands .Context ):
        """Close the current ticket"""
        if not await is_ticket_channel (self .bot ,ctx .channel ):
            await ctx .send ("<:icon_cross:1372375094336425986> This command can only be used in ticket channels.")
            return 


        if not await self .can_manage_ticket (ctx .author ,ctx .channel ):
            await ctx .send ("<:icon_cross:1372375094336425986> You don't have permission to close this ticket.")
            return 


        embed =self .create_branded_embed (
        "<:icon_danger:1372375135604047902> Confirm Ticket Closure",
        f"Are you sure you want to close this ticket?\n\n"
        f"**Channel:** {ctx.channel.mention}\n"
        f"**Requested by:** {ctx.author.mention}\n\n"
        f"This action cannot be undone and the channel will be deleted."
        )
        embed .color =0xFF6B35 

        view =TicketCloseConfirmView (ctx .author ,self )
        await ctx .send (embed =embed ,view =view ,ephemeral =True )

    @ticket .command (name ="transcript",description ="📄 Get ticket transcript")
    async def transcript (self ,ctx :commands .Context ):
        """Get ticket transcript"""
        if not await is_ticket_channel (self .bot ,ctx .channel ):
            await ctx .send ("<:icon_cross:1372375094336425986> This command can only be used in ticket channels.")
            return 

        if not await self .can_manage_ticket (ctx .author ,ctx .channel ):
            await ctx .send ("<:icon_cross:1372375094336425986> You don't have permission to view this ticket's transcript.")
            return 

        try :
            transcript =await self .generate_transcript (ctx .channel )


            ticket_info =await self .get_ticket_info (ctx .channel .id )
            filename =f"ticket-{ticket_info['ticket_number'] if ticket_info else 'unknown'}-transcript.html"

            transcript_file =discord .File (
            io .StringIO (transcript ),
            filename =filename 
            )

            embed =self .create_branded_embed (
            "📄 Ticket Transcript",
            f"Transcript for {ctx.channel.mention}"
            )

            await ctx .send (embed =embed ,file =transcript_file )

        except Exception as e :
            logger .error (f"Error generating transcript: {e}")
            pass 

    @ticket .command (name ="add",description ="➕ Add user to ticket")
    async def add (self ,ctx :commands .Context ,user :discord .Member ):
        """Add user to ticket"""
        if not await is_ticket_channel (self .bot ,ctx .channel ):
            await ctx .send ("❌ This command can only be used in ticket channels.")
            return 

        if not await self .can_manage_ticket (ctx .author ,ctx .channel ):
            await ctx .send ("❌ You don't have permission to add users to this ticket.")
            return 

        try :
            await ctx .channel .set_permissions (
            user ,
            view_channel =True ,
            send_messages =True ,
            read_message_history =True 
            )

            embed =self .create_branded_embed (
            "➕ User Added",
            f"{user.mention} has been added to this ticket"
            )

            await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error adding user to ticket: {e}")
            pass 

    @ticket .command (name ="remove",description ="➖ Remove user from ticket")
    async def remove (self ,ctx :commands .Context ,user :discord .Member ):
        """Remove user from ticket"""
        if not await is_ticket_channel (self .bot ,ctx .channel ):
            await ctx .send ("❌ This command can only be used in ticket channels.")
            return 

        if not await self .can_manage_ticket (ctx .author ,ctx .channel ):
            await ctx .send ("❌ You don't have permission to remove users from this ticket.")
            return 

        try :
            await ctx .channel .set_permissions (user ,overwrite =None )

            embed =self .create_branded_embed (
            "➖ User Removed",
            f"{user.mention} has been removed from this ticket"
            )

            await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error removing user from ticket: {e}")
            pass 

    @ticket .command (name ="rename",description ="✏️ Rename the ticket channel")
    async def rename (self ,ctx :commands .Context ,*,new_name :str ):
        """Rename the ticket channel"""
        if not await is_ticket_channel (self .bot ,ctx .channel ):
            await ctx .send ("❌ This command can only be used in ticket channels.")
            return 

        if not await self .can_manage_ticket (ctx .author ,ctx .channel ):
            await ctx .send ("❌ You don't have permission to rename this ticket.")
            return 

        try :
            old_name =ctx .channel .name 
            await ctx .channel .edit (name =new_name )

            embed =self .create_branded_embed (
            "✏️ Ticket Renamed",
            f"**Old name:** {old_name}\n**New name:** {new_name}"
            )

            await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error renaming ticket: {e}")
            pass 

    @ticket .command (name ="claim",description ="🤝 Claim the current ticket")
    async def claim (self ,ctx :commands .Context ):
        """Claim the current ticket"""
        if not await is_ticket_channel (self .bot ,ctx .channel ):
            await ctx .send ("❌ This command can only be used in ticket channels.")
            return 


        if not await user_has_support_role (self .bot ,ctx .author ):
            await ctx .send ("❌ You don't have permission to claim tickets.")
            return 

        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT is_claimed, claimer_id, creator_id FROM ticket_instances 
                    WHERE channel_id = ?
                """,(ctx .channel .id ,))as cursor :
                    result =await cursor .fetchone ()

                if not result :
                    await ctx .send ("<:icon_cross:1372375094336425986> Could not find ticket information.")
                    return 

                is_claimed ,claimer_id ,creator_id =result 

                if is_claimed and claimer_id :
                    claimer =ctx .guild .get_member (claimer_id )
                    claimer_name =claimer .mention if claimer else f"<@{claimer_id}>"
                    await ctx .send (f"<:icon_cross:1372375094336425986> This ticket is already claimed by {claimer_name}.")
                    return 


                await db .execute ("""
                    UPDATE ticket_instances 
                    SET claimer_id = ?, claimed_at = ?, is_claimed = 1
                    WHERE channel_id = ?
                """,(ctx .author .id ,datetime .datetime .utcnow ().isoformat (),ctx .channel .id ))
                await db .commit ()

            embed =self .create_branded_embed (
            "🤝 Ticket Claimed",
            f"This ticket has been claimed by {ctx.author.mention}"
            )


            await self .log_ticket_event (ctx .guild .id ,"Claimed",{
            'channel_id':ctx .channel .id ,
            'claimer_id':ctx .author .id ,
            'creator_id':creator_id 
            })

            await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error claiming ticket: {e}")
            pass 



    @ticket .command (name ="category-add",description ="📂 Add a ticket category")
    @commands .has_permissions (manage_guild =True )
    async def category_add (self ,ctx :commands .Context ,emoji :str ,*,name :str ):
        """Add a ticket category and create Discord category channel"""
        try :

            category_channel =await ctx .guild .create_category (
            name =f"🎫 {name}",
            reason =f"Category created for ticket type: {name}"
            )


            overwrites ={
            ctx .guild .default_role :discord .PermissionOverwrite (view_channel =False ),
            ctx .guild .me :discord .PermissionOverwrite (
            view_channel =True ,
            manage_channels =True ,
            manage_permissions =True 
            )
            }


            async with aiosqlite .connect ("db/tickets.db")as db :

                async with db .execute ("SELECT role_id FROM tickets WHERE guild_id = ?",(ctx .guild .id ,))as cursor :
                    result =await cursor .fetchone ()
                    if result :
                        main_role =ctx .guild .get_role (result [0 ])
                        if main_role :
                            overwrites [main_role ]=discord .PermissionOverwrite (
                            view_channel =True ,
                            manage_channels =True ,
                            manage_permissions =True 
                            )


                async with db .execute ("SELECT role_id FROM ticket_support_roles WHERE guild_id = ?",(ctx .guild .id ,))as cursor :
                    support_roles =await cursor .fetchall ()
                    for role_id ,in support_roles :
                        role =ctx .guild .get_role (role_id )
                        if role :
                            overwrites [role ]=discord .PermissionOverwrite (
                            view_channel =True ,
                            manage_channels =True ,
                            manage_permissions =True 
                            )

            await category_channel .edit (overwrites =overwrites )


            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    INSERT OR REPLACE INTO ticket_categories (guild_id, category_name, category_emoji, discord_category_id)
                    VALUES (?, ?, ?, ?)
                """,(ctx .guild .id ,name ,emoji ,category_channel .id ))
                await db .commit ()

            embed =self .create_branded_embed (
            "<:icon_tick:1372375089668161597> Category Added",
            f"{emoji} **{name}** has been added to ticket categories\n"
            f"Discord category created: {category_channel.mention}"
            )
            await ctx .send (embed =embed )


            await self .refresh_all_panels (ctx .guild )

        except Exception as e :
            logger .error (f"Error adding category: {e}")
            pass 

    @ticket .command (name ="category-remove",description ="🗑️ Remove a ticket category")
    @commands .has_permissions (manage_guild =True )
    async def category_remove (self ,ctx :commands .Context ,*,name :str ):
        """Remove a ticket category and its Discord category channel"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :

                async with db .execute ("""
                    SELECT discord_category_id FROM ticket_categories 
                    WHERE guild_id = ? AND category_name = ?
                """,(ctx .guild .id ,name ))as cursor :
                    result =await cursor .fetchone ()

                if not result :
                    await ctx .send (f"<:icon_danger:1372375135604047902> Category **{name}** not found.")
                    return 


                if result [0 ]:
                    category_channel =ctx .guild .get_channel (result [0 ])
                    if category_channel :
                        await category_channel .delete (reason =f"Ticket category '{name}' removed")


                await db .execute ("""
                    DELETE FROM ticket_categories 
                    WHERE guild_id = ? AND category_name = ?
                """,(ctx .guild .id ,name ))
                await db .commit ()

            embed =self .create_branded_embed (
            "<:icon_tick:1372375089668161597> Category Removed",
            f"**{name}** has been removed from ticket categories and its Discord category has been deleted"
            )
            await ctx .send (embed =embed )


            await self .refresh_all_panels (ctx .guild )

        except Exception as e :
            logger .error (f"Error removing category: {e}")
            pass 

    @ticket .command (name ="category-list",description ="📋 List all ticket categories")
    async def category_list (self ,ctx :commands .Context ):
        """List all ticket categories"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT category_name, category_emoji, discord_category_id FROM ticket_categories 
                    WHERE guild_id = ? ORDER BY category_name
                """,(ctx .guild .id ,))as cursor :
                    categories =await cursor .fetchall ()

            embed =self .create_branded_embed ("📂 Ticket Categories")

            if categories :
                category_list =[]
                for name ,emoji ,discord_id in categories :
                    category_channel =ctx .guild .get_channel (discord_id )if discord_id else None 
                    status ="<:icon_tick:1372375089668161597>"if category_channel else "<:icon_cross:1372375094336425986>"
                    category_list .append (f"{emoji} **{name}** {status}")

                embed .description ="\n".join (category_list )
                embed .add_field (
                name ="Legend",
                value ="<:icon_tick:1372375089668161597> = Discord category exists\n<:icon_cross:1372375094336425986> = Discord category missing",
                inline =False 
                )
            else :
                embed .description ="No categories configured. Use `ticket category-add` to add some!"

            await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error listing categories: {e}")
            pass 

    @ticket .command (name ="category-default",description ="📦 Add default ticket categories")
    @commands .has_permissions (manage_guild =True )
    async def category_default (self ,ctx :commands .Context ):
        """Add default ticket categories"""
        default_categories =[
        ("<:reason:1388729552385212576>","Technical Support"),
        ("<a:open:1388729422689079297>","Billing & Payments"),
        ("🎫","General Questions"),
        ("<:icon_danger:1373170993236803688>","Report Issue"),
        ("<a:star:1376600544847593482>","Feature Request"),
        ("<a:crown:1376599839290429512>","Partnership Inquiry")
        ]

        try :
            added_categories =[]
            for emoji ,name in default_categories :
                try :

                    category_channel =await ctx .guild .create_category (
                    name =f"🎫 {name}",
                    reason =f"Default category created for ticket type: {name}"
                    )


                    overwrites ={
                    ctx .guild .default_role :discord .PermissionOverwrite (view_channel =False ),
                    ctx .guild .me :discord .PermissionOverwrite (
                    view_channel =True ,
                    manage_channels =True ,
                    manage_permissions =True 
                    )
                    }
                    await category_channel .edit (overwrites =overwrites )


                    async with aiosqlite .connect ("db/tickets.db")as db :
                        await db .execute ("""
                            INSERT OR IGNORE INTO ticket_categories (guild_id, category_name, category_emoji, discord_category_id)
                            VALUES (?, ?, ?, ?)
                        """,(ctx .guild .id ,name ,emoji ,category_channel .id ))
                        await db .commit ()

                    added_categories .append (f"{emoji} **{name}**")

                except Exception as e :
                    logger .error (f"Error creating category {name}: {e}")
                    continue 

            embed =self .create_branded_embed (
            "<:icon_tick:1372375089668161597> Default Categories Added",
            "The following default categories have been added:\n\n"+
            "\n".join (added_categories )
            )
            await ctx .send (embed =embed )


            if added_categories :
                await self .refresh_all_panels (ctx .guild )

        except Exception as e :
            logger .error (f"Error adding default categories: {e}")
            pass 



    @ticket .command (name ="panel-send",description ="📋 Send the ticket panel")
    @app_commands .describe (panel_type ="Choose between dropdown menu or button style")
    @app_commands .choices (panel_type =[
    app_commands .Choice (name ="Dropdown Menu",value ="dropdown"),
    app_commands .Choice (name ="Buttons",value ="buttons")
    ])
    @commands .has_permissions (manage_guild =True )
    async def panel_send (self ,ctx :commands .Context ,panel_type :str ="dropdown"):
        """Send the ticket panel"""
        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("SELECT * FROM tickets WHERE guild_id = ?",(ctx .guild .id ,))as cursor :
                    config =await cursor .fetchone ()

                if not config :
                    await ctx .send ("<:icon_cross:1372375094336425986> Ticket system not setup. Use `ticket setup` first.")
                    return 


            await self .remove_existing_panel (ctx .channel .id )


            panel_message =await self .send_ticket_panel (ctx .channel ,panel_type )

            if panel_message :
                embed =self .create_branded_embed (
                "<:icon_tick:1372375089668161597> Panel Sent",
                f"Ticket panel ({panel_type}) has been sent successfully!"
                )
                await ctx .send (embed =embed )
            else :
                pass 

        except Exception as e :
            logger .error (f"Error sending panel: {e}")
            pass 



    async def can_manage_ticket (self ,user :discord .Member ,channel :discord .TextChannel )->bool :
        """Check if user can manage the ticket"""
        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT creator_id FROM ticket_instances WHERE channel_id = ?
                """,(channel .id ,))as cursor :
                    result =await cursor .fetchone ()

                if result and result [0 ]==user .id :
                    return True 


            return await user_has_support_role (self .bot ,user )

        except Exception as e :
            logger .error (f"Error checking ticket permissions: {e}")
            return False 

    async def get_ticket_info (self ,channel_id :int )->Optional [Dict [str ,Any ]]:
        """Get ticket information"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT * FROM ticket_instances WHERE channel_id = ?
                """,(channel_id ,))as cursor :
                    result =await cursor .fetchone ()

                if result :
                    columns =[desc [0 ]for desc in cursor .description ]
                    return dict (zip (columns ,result ))

                return None 

        except Exception as e :
            logger .error (f"Error getting ticket info: {e}")
            return None 

    async def generate_transcript (self ,channel :discord .TextChannel )->str :
        """Generate ultra-modern, responsive chat transcript with premium design and smooth navigation"""
        from utils .transcript import generate_transcript 


        ticket_info =await self .get_ticket_info (channel .id )

        return await generate_transcript (self .bot ,channel ,ticket_info )

    def format_duration (self ,duration :datetime .timedelta )->str :
        """Format duration in a readable way"""
        total_seconds =int (duration .total_seconds ())
        days =total_seconds //86400 
        hours =(total_seconds %86400 )//3600 
        minutes =(total_seconds %3600 )//60 

        parts =[]
        if days :
            parts .append (f"{days}d")
        if hours :
            parts .append (f"{hours}h")
        if minutes :
            parts .append (f"{minutes}m")

        return " ".join (parts )if parts else "< 1m"

    async def send_rating_dm (self ,user_id :int ,ticket_info :Dict [str ,Any ],transcript :str ):
        """Send single rating embed with select menu and transcript file"""
        try :
            user =self .bot .get_user (user_id )
            if not user :
                logger .warning (f"Could not find user {user_id} for rating DM")
                return 

            if not ticket_info :
                logger .error ("No ticket info provided for rating DM")
                return 

            ticket_number =ticket_info .get ('ticket_number','Unknown')
            guild_id =ticket_info .get ('guild_id')


            guild =self .bot .get_guild (guild_id )if guild_id else None 


            embed =discord .Embed (
            title ="Ticket Closed",
            description =f"Hey {user.display_name}! 👋\nYour ticket (#{ticket_number}) has just been closed by a staff member.\n\nThank you for reaching out to us. If you need further help, feel free to open a new ticket anytime!",
            color =0x000000 
            )


            embed .set_author (
            name =self .bot .user .display_name ,
            icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None 
            )


            if guild and guild .icon :
                embed .set_thumbnail (url =guild .icon .url )

            embed .set_footer (text ="Thanks for using Strelizia ❤️")


            view =RatingSelectView (ticket_info ,transcript )
            view .timeout =None 


            transcript_file =discord .File (
            io .StringIO (transcript ),
            filename =f"ticket-{ticket_number}-transcript.html"
            )

            try :

                rating_message =await user .send (embed =embed ,view =view )
                view .message =rating_message 
                self .bot .add_view (view ,message_id =rating_message .id )


                rating_embed =discord .Embed (
                title ="⭐ How was our support?",
                description ="We'd love to hear your feedback. Please rate your experience below!",
                color =0xFEE75C 
                )
                rating_embed .set_footer (text ="Your feedback helps us improve.")

                await user .send (embed =rating_embed ,view =RatingSelectOnlyView (ticket_info ,transcript ,rating_message ))


                await user .send (file =transcript_file )

                logger .info (f"Sent rating DM and transcript to user {user_id} for ticket #{ticket_number}")

            except discord .Forbidden :
                logger .warning (f"Could not send DM to user {user_id} - DMs disabled")

            except discord .HTTPException as e :
                logger .error (f"HTTP error sending DM to user {user_id}: {e}")

        except Exception as e :
            logger .error (f"Error sending rating DM to user {user_id}: {e}")
            import traceback 
            logger .error (f"Full traceback: {traceback.format_exc()}")

    async def create_ticket_channel (self ,interaction :discord .Interaction ,category :str ,reason :str ):
        """Create a new ticket channel"""
        try :

            if not await self .check_cooldown (interaction .user .id ,interaction .guild .id ):
                await interaction .response .send_message (
                "⏰ You're on cooldown! Please wait before creating another ticket.",
                ephemeral =True 
                )
                return 


            if await self .has_open_ticket (interaction .user .id ,interaction .guild .id ):
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> You already have an open ticket! Please close it before creating a new one.",
                ephemeral =True 
                )
                return 

            await interaction .response .defer (ephemeral =True )


            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT role_id, ping_role_id, category_id FROM tickets WHERE guild_id = ?
                """,(interaction .guild .id ,))as cursor :
                    config =await cursor .fetchone ()

                if not config :
                    await interaction .followup .send ("<:icon_cross:1372375094336425986> Ticket system not configured.",ephemeral =True )
                    return 


                async with db .execute ("""
                    SELECT discord_category_id FROM ticket_categories 
                    WHERE guild_id = ? AND category_name = ?
                """,(interaction .guild .id ,category ))as cursor :
                    category_result =await cursor .fetchone ()


                category_id =category_result [0 ]if category_result and category_result [0 ]else config [2 ]

                if not category_id :
                    await interaction .followup .send ("<:icon_cross:1372375094336425986> No category channel configured.",ephemeral =True )
                    return 


                async with db .execute ("""
                    SELECT COUNT(*) FROM ticket_instances WHERE guild_id = ?
                """,(interaction .guild .id ,))as cursor :
                    ticket_number =(await cursor .fetchone ())[0 ]+1 

            category_channel =interaction .guild .get_channel (category_id )
            support_role =interaction .guild .get_role (config [0 ])
            ping_role =interaction .guild .get_role (config [1 ])if config [1 ]else None 

            if not category_channel or not support_role :
                await interaction .followup .send ("<:icon_cross:1372375094336425986> Ticket system configuration is invalid.",ephemeral =True )
                return 


            all_support_roles =await get_all_support_roles (self .bot ,interaction .guild .id )


            overwrites ={
            interaction .guild .default_role :discord .PermissionOverwrite (view_channel =False ),
            interaction .user :discord .PermissionOverwrite (
            view_channel =True ,
            send_messages =True ,
            read_message_history =True 
            ),
            support_role :discord .PermissionOverwrite (
            view_channel =True ,
            send_messages =True ,
            read_message_history =True ,
            manage_messages =True 
            ),
            interaction .guild .me :discord .PermissionOverwrite (
            view_channel =True ,
            send_messages =True ,
            manage_channels =True ,
            manage_messages =True 
            )
            }


            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("SELECT role_id FROM ticket_support_roles WHERE guild_id = ?",(interaction .guild .id ,))as cursor :
                    support_roles =await cursor .fetchall ()
                    for role_id ,in support_roles :
                        role =interaction .guild .get_role (role_id )
                        if role and role .id !=support_role .id :
                            overwrites [role ]=discord .PermissionOverwrite (
                            view_channel =True ,
                            send_messages =True ,
                            read_message_history =True ,
                            manage_messages =True 
                            )


            channel_name =f"ticket-{interaction.user.name}-{ticket_number}"
            ticket_channel =await interaction .guild .create_text_channel (
            name =channel_name ,
            category =category_channel ,
            overwrites =overwrites ,
            topic =f"Ticket #{ticket_number} | {category} | Created by {interaction.user}"
            )


            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    INSERT INTO ticket_instances 
                    (channel_id, guild_id, creator_id, category, reason, created_at, ticket_number, status, is_claimed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 'open', 0)
                """,(
                ticket_channel .id ,
                interaction .guild .id ,
                interaction .user .id ,
                category ,
                reason ,
                datetime .datetime .utcnow ().isoformat (),
                ticket_number 
                ))
                await db .commit ()


            ping_messages =[]


            for role in all_support_roles :
                if role :
                    ping_messages .append (role .mention )


            if ping_role :
                ping_messages .append (ping_role .mention )


            if ping_messages :
                ping_message =" ".join (ping_messages )
                await ticket_channel .send (ping_message )


            created_time =datetime .datetime .utcnow ()
            welcome_embed =discord .Embed (
            title ="<:icon_tick:1372375089668161597> Your Ticket Has Been Created!",
            description =f"Hey {interaction.user.mention}! Thanks for opening a ticket <a:_rose:1367348649381859490>\n"
            f"Our team will be with you as soon as possible — hang tight! <:heart_em:1274781856406962250>\n"
            f"In the meantime, feel free to describe your issue in more detail <:Heeriye:1274769360560328846>",
            color =0xFFB6C1 
            )

            welcome_embed .set_author (
            name =f"{interaction.user.display_name}",
            icon_url =interaction .user .display_avatar .url 
            )
            welcome_embed .set_thumbnail (url =interaction .user .display_avatar .url )

            welcome_embed .add_field (name ="🎮 Category",value =category ,inline =True )
            welcome_embed .add_field (name ="<:reason:1388729552385212576> Reason",value =reason ,inline =True )
            welcome_embed .add_field (name ="<a:open:1388729422689079297> Opened",value =f"<t:{int(created_time.timestamp())}:f>",inline =True )
            welcome_embed .add_field (name ="<a:crown:1376599839290429512> Opened By",value =f"{interaction.user} ({interaction.user.id})",inline =False )

            welcome_embed .add_field (
            name ="—",
            value ="<a:star:1376600544847593482> Use the buttons below to manage your ticket.\n"
            "<:help:1388729258263969903> Need help fast? Mention a support staff politely.",
            inline =False 
            )

            welcome_embed .set_footer (
            text ="Developed By AeroX Development",
            icon_url =self .bot .user .avatar .url if self .bot .user .avatar else None 
            )
            welcome_embed .timestamp =created_time 

            welcome_view =TicketControlView ()
            welcome_message =await ticket_channel .send (embed =welcome_embed ,view =welcome_view )


            try :
                await welcome_message .pin ()
            except discord .HTTPException :
                pass 


            await self .log_ticket_event (interaction .guild .id ,"Created",{
            'channel_id':ticket_channel .id ,
            'creator_id':interaction .user .id ,
            'category':category ,
            'reason':reason ,
            'priority':'medium',
            'ticket_number':ticket_number 
            })


            embed =self .create_branded_embed (
            "<:icon_tick:1372375089668161597> Ticket Created",
            f"Your ticket has been created: {ticket_channel.mention}"
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )

        except Exception as e :
            logger .error (f"Error creating ticket: {e}")
            pass 

    async def remove_existing_panel (self ,channel_id :int ):
        """Remove existing panel from channel"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT message_id FROM ticket_panels WHERE channel_id = ?
                """,(channel_id ,))as cursor :
                    result =await cursor .fetchone ()

                if result :
                    try :
                        channel =self .bot .get_channel (channel_id )
                        if channel :
                            message =await channel .fetch_message (result [0 ])
                            await message .delete ()
                    except :
                        pass 

                    await db .execute ("DELETE FROM ticket_panels WHERE channel_id = ?",(channel_id ,))
                    await db .commit ()

        except Exception as e :
            logger .error (f"Error removing existing panel: {e}")

    async def refresh_all_panels (self ,guild :discord .Guild ):
        """Refresh all existing panels in the guild with updated categories"""
        try :
            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT channel_id, message_id, panel_type FROM ticket_panels 
                    WHERE guild_id = ?
                """,(guild .id ,))as cursor :
                    panels =await cursor .fetchall ()

            refreshed_count =0 
            for channel_id ,message_id ,panel_type in panels :
                try :
                    channel =guild .get_channel (channel_id )
                    if not channel :
                        logger .warning (f"Channel {channel_id} not found, skipping panel refresh")
                        continue 


                    try :
                        old_message =await channel .fetch_message (message_id )
                        await old_message .delete ()
                    except Exception as e :
                        logger .warning (f"Could not delete old panel message {message_id}: {delete_error}")


                    new_message =await self .send_ticket_panel (channel ,panel_type )
                    if new_message :
                        refreshed_count +=1 
                        logger .info (f"Refreshed panel in {channel.name} for guild {guild.name}")
                    else :
                        logger .error (f"Failed to send new panel in {channel.name}")

                except Exception as e :
                    logger .error (f"Error refreshing panel {message_id} in channel {channel_id}: {e}")

            logger .info (f"Successfully refreshed {refreshed_count}/{len(panels)} panels for guild {guild.name}")

        except Exception as e :
            logger .error (f"Error refreshing all panels for guild {guild.id}: {e}")

    async def send_ticket_panel (self ,channel :discord .TextChannel ,panel_type :str ):
        """Send ticket panel to channel"""
        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT embed_title, embed_description, embed_footer, embed_color, embed_image, embed_thumbnail
                    FROM tickets WHERE guild_id = ?
                """,(channel .guild .id ,))as cursor :
                    config =await cursor .fetchone ()

                if not config :
                    logger .error (f"No ticket configuration found for guild {channel.guild.id}")
                    return None 


                async with db .execute ("""
                    SELECT category_name, category_emoji FROM ticket_categories 
                    WHERE guild_id = ? ORDER BY category_name
                """,(channel .guild .id ,))as cursor :
                    raw_categories =await cursor .fetchall ()


                categories =[]
                for category_data in raw_categories :
                    if len (category_data )>=2 :
                        name ,emoji =category_data [0 ],category_data [1 ]

                        if name and emoji :
                            categories .append ((name ,emoji ))

                logger .info (f"Found {len(categories)} valid categories for guild {channel.guild.id}: {categories}")


                if not categories :
                    logger .info (f"No categories found, using default General category for guild {channel.guild.id}")
                    categories =[("General","🎫")]


            embed =discord .Embed (
            title =config [0 ]or "🎫 Create a Support Ticket",
            description =config [1 ]or "Need help? Click the button below to create a ticket and our support team will assist you!",
            color =config [3 ]or 0x000000 
            )
            embed .set_footer (text =config [2 ]or "Developed By AeroX Development")
            embed .timestamp =datetime .datetime .utcnow ()


            if config [5 ]:
                embed .set_thumbnail (url =config [5 ])
            elif self .bot .user .avatar :
                embed .set_thumbnail (url =self .bot .user .avatar .url )

            if config [4 ]:
                embed .set_image (url =config [4 ])


            try :
                if panel_type =="dropdown":
                    view =TicketDropdownView (categories ,channel .guild .id )
                elif panel_type =="buttons":
                    view =TicketButtonView (categories ,channel .guild .id )
                else :
                    view =TicketDropdownView (categories ,channel .guild .id )

                view .timeout =None 
                logger .info (f"Created {panel_type} view with {len(categories)} categories")

            except Exception as e :
                logger .error (f"Error creating view: {view_error}")

                categories =[("General","🎫")]
                view =TicketDropdownView (categories ,channel .guild .id )
                view .timeout =None 

            message =await channel .send (embed =embed ,view =view )


            self .bot .add_view (view ,message_id =message .id )
            logger .info (f"Panel sent successfully to {channel.name} ({channel.id}) with message ID {message.id}")


            for child in view .children :
                if hasattr (child ,'custom_id'):
                    logger .info (f"Registered component with custom_id: {child.custom_id}")


            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    INSERT OR REPLACE INTO ticket_panels 
                    (guild_id, channel_id, message_id, panel_type, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """,(
                channel .guild .id ,
                channel .id ,
                message .id ,
                panel_type ,
                datetime .datetime .utcnow ().isoformat ()
                ))
                await db .commit ()

            return message 

        except Exception as e :
            logger .error (f"Error sending ticket panel: {e}")
            import traceback 
            logger .error (f"Full traceback: {traceback.format_exc()}")
            return None 



class TicketSetupView (discord .ui .View ):
    def __init__ (self ,author :discord .Member ,guild :discord .Guild ,cog ):
        super ().__init__ (timeout =300 )
        self .author =author 
        self .guild =guild 
        self .cog =cog 
        self .message =None 
        self .setup_data ={
        'panel_channel':None ,
        'support_role':None ,
        'log_channel':None 
        }


        self .add_item (ChannelSelect (author ,guild ,"panel"))
        self .add_item (RoleSelect (author ,guild ))
        self .add_item (ChannelSelect (author ,guild ,"log"))


        customize_button =discord .ui .Button (
        label ="Customize Panel",
        style =discord .ButtonStyle .secondary ,
        emoji ="🎨"
        )
        customize_button .callback =self .customize_panel 
        self .add_item (customize_button )


        finish_button =discord .ui .Button (
        label ="Finish Setup",
        style =discord .ButtonStyle .success ,
        emoji ="<:icon_tick:1372375089668161597>"
        )
        finish_button .callback =self .finish_setup 
        self .add_item (finish_button )

    async def customize_panel (self ,interaction :discord .Interaction ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the command author can customize the panel.",ephemeral =True )
            return 

        modal =PanelCustomizationModal ()
        await interaction .response .send_modal (modal )

    async def finish_setup (self ,interaction :discord .Interaction ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the command author can finish setup.",ephemeral =True )
            return 


        panel_channel =self .setup_data .get ('panel_channel')
        support_role =self .setup_data .get ('support_role')
        log_channel =self .setup_data .get ('log_channel')

        if not panel_channel or not support_role :
            missing =[]
            if not panel_channel :
                missing .append ("panel channel")
            if not support_role :
                missing .append ("support role")

            await interaction .response .send_message (
            f"<:icon_cross:1372375094336425986> Please select the missing items: {', '.join(missing)}",
            ephemeral =True 
            )
            return 

        try :
            await interaction .response .defer ()


            main_category =discord .utils .get (self .guild .categories ,name ="🎫 Tickets")
            if not main_category :
                main_category =await self .guild .create_category (
                "🎫 Tickets",
                overwrites ={
                self .guild .default_role :discord .PermissionOverwrite (view_channel =False ),
                support_role :discord .PermissionOverwrite (
                view_channel =True ,
                manage_channels =True ,
                manage_permissions =True 
                ),
                self .guild .me :discord .PermissionOverwrite (
                view_channel =True ,
                manage_channels =True ,
                manage_permissions =True 
                )
                }
                )


            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    INSERT OR REPLACE INTO tickets (
                        guild_id, channel_id, role_id, category_id, log_channel_id,
                        embed_title, embed_description, embed_footer, embed_color, embed_image, embed_thumbnail
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,(
                self .guild .id ,
                panel_channel .id ,
                support_role .id ,
                main_category .id ,
                log_channel .id if log_channel else None ,
                "🎫 Create a Support Ticket",
                "Need help? Click the button below to create a ticket and our support team will assist you!",
                "Developed By AeroX Development",
                0x000000 ,
                None ,
                None 
                ))


                await db .execute ("""
                    INSERT OR REPLACE INTO ticket_support_roles (guild_id, role_id)
                    VALUES (?, ?)
                """,(self .guild .id ,support_role .id ))

                await db .commit ()

            embed =self .cog .create_branded_embed (
            "<:icon_tick:1372375089668161597> Ticket System Setup Complete!",
            f"**📍 Panel Channel:** {panel_channel.mention}\n"
            f"**👥 Support Role:** {support_role.mention}\n"
            f"**📊 Log Channel:** {log_channel.mention if log_channel else 'None'}\n"
            f"**📁 Main Category:** {main_category.mention}\n\n"
            f"**Next Steps:**\n"
            f"• Use `ticket category-add` to add categories\n"
            f"• Use `ticket panel-send` to send the ticket panel"
            )

            await interaction .followup .edit_message (message_id =self .message .id ,embed =embed ,view =None )

        except Exception as e :
            logger .error (f"Error finishing setup: {e}")
            await interaction .followup .send (f"<:icon_cross:1372375094336425986> Setup error: {str(e)}",ephemeral =True )

class ChannelSelect (discord .ui .ChannelSelect ):
    def __init__ (self ,author :discord .Member ,guild :discord .Guild ,channel_type :str ):
        self .author =author 
        self .guild =guild 
        self .channel_type =channel_type 

        placeholder ="Select panel channel"if channel_type =="panel"else "Select log channel (optional)"

        super ().__init__ (
        placeholder =placeholder ,
        channel_types =[discord .ChannelType .text ],
        max_values =1 
        )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the command author can select channels.",ephemeral =True )
            return 

        selected_channel =self .values [0 ]
        view =self .view 

        if self .channel_type =="panel":
            view .setup_data ['panel_channel']=selected_channel 
            channel_name ="Panel"
        else :
            view .setup_data ['log_channel']=selected_channel 
            channel_name ="Log"

        await interaction .response .send_message (f"<:icon_tick:1372375089668161597> {channel_name} channel set to {selected_channel.mention}",ephemeral =True )

class RoleSelect (discord .ui .RoleSelect ):
    def __init__ (self ,author :discord .Member ,guild :discord .Guild ):
        self .author =author 
        self .guild =guild 

        super ().__init__ (
        placeholder ="Select support role",
        max_values =1 
        )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the command author can select roles.",ephemeral =True )
            return 

        selected_role =self .values [0 ]
        self .view .setup_data ['support_role']=selected_role 

        await interaction .response .send_message (f"<:icon_tick:1372375089668161597> Support role set to {selected_role.mention}",ephemeral =True )

class PanelCustomizationModal (discord .ui .Modal ):
    def __init__ (self ):
        super ().__init__ (title ="Customize Ticket Panel")

        self .panel_title =discord .ui .TextInput (
        label ="Panel Title",
        placeholder ="🎫 Create a Support Ticket",
        default ="🎫 Create a Support Ticket",
        max_length =256 
        )
        self .add_item (self .panel_title )

        self .panel_description =discord .ui .TextInput (
        label ="Panel Description",
        placeholder ="Need help? Click the button below to create a ticket...",
        default ="Need help? Click the button below to create a ticket and our support team will assist you!",
        style =discord .TextStyle .paragraph ,
        max_length =2048 
        )
        self .add_item (self .panel_description )

        self .panel_image =discord .ui .TextInput (
        label ="Panel Image URL (optional)",
        placeholder ="https://example.com/image.png",
        required =False ,
        max_length =500 
        )
        self .add_item (self .panel_image )

        self .panel_thumbnail =discord .ui .TextInput (
        label ="Panel Thumbnail URL (optional)",
        placeholder ="https://example.com/thumbnail.png",
        required =False ,
        max_length =500 
        )
        self .add_item (self .panel_thumbnail )

        self .embed_color =discord .ui .TextInput (
        label ="Embed Color (hex code)",
        placeholder ="#000000",
        default ="000000",
        max_length =7 
        )
        self .add_item (self .embed_color )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :

            color_hex =self .embed_color .value .lstrip ('#')
            try :
                color_int =int (color_hex ,16 )if color_hex else 0 
            except ValueError :
                await interaction .response .send_message ("<:icon_cross:1372375094336425986> Invalid color code. Please use a valid hex color (e.g., #FF0000 or FF0000).",ephemeral =True )
                return 


            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    UPDATE tickets SET 
                    embed_title = ?, embed_description = ?, embed_color = ?, 
                    embed_image = ?, embed_thumbnail = ?
                    WHERE guild_id = ?
                """,(
                self .panel_title .value ,
                self .panel_description .value ,
                color_int ,
                self .panel_image .value if self .panel_image .value else None ,
                self .panel_thumbnail .value if self .panel_thumbnail .value else None ,
                interaction .guild .id 
                ))
                await db .commit ()

            await interaction .response .send_message ("<:icon_tick:1372375089668161597> Panel customization saved successfully!",ephemeral =True )

        except Exception as e :
            pass 

class TicketDropdownView (discord .ui .View ):
    def __init__ (self ,categories ,guild_id =None ):
        super ().__init__ (timeout =None )
        self .add_item (TicketDropdown (categories ,guild_id ))

class TicketDropdown (discord .ui .Select ):
    def __init__ (self ,categories ,guild_id =None ):

        if not categories :
            categories =[("General","🎫")]

        self .guild_id =guild_id 

        options =[]
        for name ,emoji in categories [:25 ]:

            if not emoji or not isinstance (emoji ,str ):
                emoji ="🎫"
            if not name or not isinstance (name ,str ):
                name ="General"


            try :

                if emoji .startswith ('\\U'):
                    emoji =emoji .encode ().decode ('unicode_escape')


                emoji .encode ('utf-8').decode ('utf-8')


                if len (emoji .encode ('utf-8'))>4 or not emoji .isprintable ():
                    emoji ="🎫"

            except (UnicodeError ,UnicodeDecodeError ,AttributeError ,TypeError ):
                emoji ="🎫"

            try :
                options .append (discord .SelectOption (
                label =str (name )[:100 ],
                emoji =str (emoji ),
                description =f"Create a {str(name).lower()} ticket"[:100 ],
                value =str (name )
                ))
            except Exception as e :
                logger .error (f"Error creating select option for {name}: {e}")

                options .append (discord .SelectOption (
                label ="General",
                emoji ="🎫",
                description ="Create a general support ticket",
                value ="General"
                ))


        if not options :
            options =[discord .SelectOption (
            label ="General",
            emoji ="🎫",
            description ="Create a general support ticket",
            value ="General"
            )]


        if guild_id :
            custom_id =f"ticket_dropdown_{guild_id}"
        else :
            custom_id ="ticket_dropdown_persistent"

        try :
            super ().__init__ (
            placeholder ="🎫 Select a category to create a ticket...",
            options =options ,
            custom_id =custom_id 
            )
        except Exception as e :
            logger .error (f"Error initializing dropdown: {e}")

            super ().__init__ (
            placeholder ="🎫 Select a category to create a ticket...",
            options =[discord .SelectOption (
            label ="General",
            emoji ="🎫",
            description ="Create a general support ticket",
            value ="General"
            )],
            custom_id =custom_id 
            )

    async def callback (self ,interaction :discord .Interaction ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if cog :
            modal =TicketModal (self .values [0 ])
            await interaction .response .send_modal (modal )

class TicketButtonView (discord .ui .View ):
    def __init__ (self ,categories ,guild_id =None ):
        super ().__init__ (timeout =None )


        if not categories :
            categories =[("General","🎫")]


        for i ,(name ,emoji )in enumerate (categories [:25 ]):

            if not emoji :
                emoji ="🎫"
            if not name :
                name ="General"

            button =TicketButton (name ,emoji ,i ,guild_id )
            self .add_item (button )

class TicketButton (discord .ui .Button ):
    def __init__ (self ,category :str ,emoji :str ,index :int ,guild_id =None ):
        row =index //5 


        try :

            if emoji .startswith ('\\U'):
                emoji =emoji .encode ().decode ('unicode_escape')


            emoji .encode ('utf-8').decode ('utf-8')


            if len (emoji .encode ('utf-8'))>4 or not emoji .isprintable ():
                emoji ="🎫"

        except (UnicodeError ,UnicodeDecodeError ,AttributeError ):
            emoji ="🎫"


        if guild_id :
            custom_id =f"ticket_button_{category}_{guild_id}"
        else :
            custom_id =f"ticket_button_{category}_persistent"

        super ().__init__ (
        label =category ,
        emoji =emoji ,
        style =discord .ButtonStyle .primary ,
        custom_id =custom_id ,
        row =row 
        )
        self .category =category 

    async def callback (self ,interaction :discord .Interaction ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if cog :
            modal =TicketModal (self .category )
            await interaction .response .send_modal (modal )

class TicketModal (discord .ui .Modal ):
    def __init__ (self ,category :str ):
        super ().__init__ (title =f"Create {category} Ticket")
        self .category =category 

        self .reason =discord .ui .TextInput (
        label ="Reason for ticket",
        placeholder ="Please describe your issue...",
        style =discord .TextStyle .paragraph ,
        max_length =1000 ,
        required =True 
        )
        self .add_item (self .reason )

    async def on_submit (self ,interaction :discord .Interaction ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if cog :
            await cog .create_ticket_channel (interaction ,self .category ,self .reason .value )

class TicketControlView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )

    @discord .ui .button (label ="Close",emoji ="<:close:1388408726716682281>",style =discord .ButtonStyle .red ,custom_id ="ticket_control_close")
    async def close_ticket (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if not cog :
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Ticket system not available.",ephemeral =True )
            return 


        if not await is_ticket_channel (cog .bot ,interaction .channel ):
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> This can only be used in ticket channels.",ephemeral =True )
            return 


        if not await cog .can_manage_ticket (interaction .user ,interaction .channel ):
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> You don't have permission to close this ticket.",ephemeral =True )
            return 


        embed =cog .create_branded_embed (
        "<:icon_danger:1372375135604047902> Confirm Ticket Closure",
        f"Are you sure you want to close this ticket?\n\n"
        f"**Channel:** {interaction.channel.mention}\n"
        f"**Requested by:** {interaction.user.mention}\n\n"
        f"This action cannot be undone and the channel will be deleted."
        )
        embed .color =0xFF6B35 

        view =TicketCloseConfirmView (interaction .user ,cog )
        await interaction .response .send_message (embed =embed ,view =view ,ephemeral =True )

    @discord .ui .button (label ="Staff Panel",emoji ="🎮",style =discord .ButtonStyle .secondary ,custom_id ="ticket_control_staff_panel")
    async def staff_panel (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if not cog :
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Ticket system not available.",ephemeral =True )
            return 


        if not await is_ticket_channel (cog .bot ,interaction .channel ):
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> This can only be used in ticket channels.",ephemeral =True )
            return 


        if not await user_has_support_role (cog .bot ,interaction .user ):
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Only staff can access this panel.",ephemeral =True )
            return 


        view =StaffPanelView ()
        embed =cog .create_branded_embed (
        "🛠️ Staff Panel",
        "Choose an action to perform on this ticket:"
        )
        await interaction .response .send_message (embed =embed ,view =view ,ephemeral =True )

class StaffPanelView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )

    @discord .ui .button (label ="Rename Ticket",emoji ="✏️",style =discord .ButtonStyle .primary ,custom_id ="staff_panel_rename_ticket")
    async def rename_ticket (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        modal =RenameTicketModal ()
        await interaction .response .send_modal (modal )

    @discord .ui .button (label ="Claim Ticket",emoji ="🤝",style =discord .ButtonStyle .success ,custom_id ="staff_panel_claim_ticket")
    async def claim_ticket (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if not cog :
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Ticket system not available.",ephemeral =True )
            return 

        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT is_claimed, claimer_id FROM ticket_instances 
                    WHERE channel_id = ?
                """,(interaction .channel .id ,))as cursor :
                    result =await cursor .fetchone ()

                if not result :
                    await interaction .response .send_message ("<:icon_cross:1372375094336425986> Could not find ticket information.",ephemeral =True )
                    return 

                is_claimed ,claimer_id =result 

                if is_claimed and claimer_id :
                    claimer =interaction .guild .get_member (claimer_id )
                    claimer_name =claimer .mention if claimer else f"<@{claimer_id}>"
                    await interaction .response .send_message (
                    f"<:icon_cross:1372375094336425986> This ticket is already claimed by {claimer_name}.",
                    ephemeral =True 
                    )
                    return 


                await db .execute ("""
                    UPDATE ticket_instances 
                    SET claimer_id = ?, claimed_at = ?, is_claimed = 1
                    WHERE channel_id = ?
                """,(interaction .user .id ,datetime .datetime .utcnow ().isoformat (),interaction .channel .id ))
                await db .commit ()

            embed =cog .create_branded_embed (
            "🤝 Ticket Claimed",
            f"This ticket has been claimed by {interaction.user.mention}"
            )


            await cog .log_ticket_event (interaction .guild .id ,"Claimed",{
            'channel_id':interaction .channel .id ,
            'claimer_id':interaction .user .id 
            })

            await interaction .response .send_message (embed =embed )

        except Exception as e :
            logger .error (f"Error claiming ticket: {e}")
            pass 

    @discord .ui .button (label ="Transfer Ticket",emoji ="🔄",style =discord .ButtonStyle .secondary ,custom_id ="staff_panel_transfer_ticket")
    async def transfer_ticket (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if not cog :
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Ticket system not available.",ephemeral =True )
            return 

        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                async with db .execute ("""
                    SELECT claimer_id FROM ticket_instances 
                    WHERE channel_id = ?
                """,(interaction .channel .id ,))as cursor :
                    result =await cursor .fetchone ()

                if not result or not result [0 ]:
                    await interaction .response .send_message ("<:icon_cross:1372375094336425986> This ticket is not claimed.",ephemeral =True )
                    return 

                if result [0 ]!=interaction .user .id :
                    await interaction .response .send_message ("<:icon_cross:1372375094336425986> You can only transfer tickets you have claimed.",ephemeral =True )
                    return 


            view =TransferTicketView ()
            await interaction .response .send_message ("Select a staff member to transfer this ticket to:",view =view ,ephemeral =True )

        except Exception as e :
            logger .error (f"Error transferring ticket: {e}")
            pass 

class RenameTicketModal (discord .ui .Modal ):
    def __init__ (self ):
        super ().__init__ (title ="Rename Ticket")

        self .new_name =discord .ui .TextInput (
        label ="New Channel Name",
        placeholder ="Enter new channel name...",
        required =True ,
        max_length =100 
        )
        self .add_item (self .new_name )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            old_name =interaction .channel .name 
            await interaction .channel .edit (name =self .new_name .value )

            cog =interaction .client .get_cog ("AdvancedTicketSystem")
            embed =cog .create_branded_embed (
            "✏️ Ticket Renamed",
            f"**Old name:** {old_name}\n**New name:** {self.new_name.value}"
            )

            await interaction .response .send_message (embed =embed )

        except Exception as e :
            logger .error (f"Error renaming ticket: {e}")
            pass 

class TransferTicketView (discord .ui .View ):
    def __init__ (self ):
        super ().__init__ (timeout =None )
        self .add_item (TransferUserSelect ())

class TransferUserSelect (discord .ui .UserSelect ):
    def __init__ (self ):
        super ().__init__ (
        placeholder ="Select a staff member...",
        max_values =1 ,
        custom_id ="transfer_ticket_user_select"
        )

    async def callback (self ,interaction :discord .Interaction ):
        cog =interaction .client .get_cog ("AdvancedTicketSystem")
        if not cog :
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Ticket system not available.",ephemeral =True )
            return 

        selected_user =self .values [0 ]


        if not await user_has_support_role (cog .bot ,selected_user ):
            await interaction .response .send_message ("<:icon_cross:1372375094336425986> Selected user is not a staff member.",ephemeral =True )
            return 

        try :

            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    UPDATE ticket_instances 
                    SET claimer_id = ?, claimed_at = ?
                    WHERE channel_id = ?
                """,(selected_user .id ,datetime .datetime .utcnow ().isoformat (),interaction .channel .id ))
                await db .commit ()

            embed =cog .create_branded_embed (
            "🔄 Ticket Transferred",
            f"This ticket has been transferred from {interaction.user.mention} to {selected_user.mention}"
            )

            await interaction .response .send_message (embed =embed )

        except Exception as e :
            logger .error (f"Error transferring ticket: {e}")
            pass 

class RatingSelectView (discord .ui .View ):
    def __init__ (self ,ticket_info :Dict [str ,Any ]=None ,transcript :str =""):
        super ().__init__ (timeout =None )
        self .ticket_info =ticket_info or {}
        self .transcript =transcript 
        self .message =None 

class RatingSelectOnlyView (discord .ui .View ):
    def __init__ (self ,ticket_info :Dict [str ,Any ]=None ,transcript :str ="",original_message =None ):
        super ().__init__ (timeout =None )
        self .ticket_info =ticket_info or {}
        self .transcript =transcript 
        self .original_message =original_message 
        self .add_item (RatingSelect (ticket_info ,transcript ,original_message ))

class RatingSelect (discord .ui .Select ):
    def __init__ (self ,ticket_info :Dict [str ,Any ]=None ,transcript :str ="",original_message =None ):
        self .ticket_info =ticket_info or {}
        self .transcript =transcript 
        self .original_message =original_message 

        options =[
        discord .SelectOption (label ="⭐ 1 Star",description ="Very poor experience",value ="1",emoji ="⭐"),
        discord .SelectOption (label ="⭐⭐ 2 Stars",description ="Poor experience",value ="2",emoji ="⭐"),
        discord .SelectOption (label ="⭐⭐⭐ 3 Stars",description ="Average experience",value ="3",emoji ="⭐"),
        discord .SelectOption (label ="⭐⭐⭐⭐ 4 Stars",description ="Good experience",value ="4",emoji ="⭐"),
        discord .SelectOption (label ="⭐⭐⭐⭐⭐ 5 Stars",description ="Excellent experience",value ="5",emoji ="⭐")
        ]

        super ().__init__ (
        placeholder ="Select your rating...",
        options =options ,
        custom_id ="ticket_rating_select"
        )

    async def callback (self ,interaction :discord .Interaction ):
        try :
            rating =int (self .values [0 ])


            if not self .ticket_info or not self .ticket_info .get ('ticket_number'):
                try :
                    async with aiosqlite .connect ("db/tickets.db")as db :
                        async with db .execute ("""
                            SELECT * FROM ticket_instances 
                            WHERE creator_id = ? AND status = 'closed'
                            ORDER BY closed_at DESC LIMIT 1
                        """,(interaction .user .id ,))as cursor :
                            result =await cursor .fetchone ()
                            if result :
                                columns =[desc [0 ]for desc in cursor .description ]
                                self .ticket_info =dict (zip (columns ,result ))
                except Exception as e :
                    logger .error (f"Error getting ticket info for rating: {e}")
                    await interaction .response .send_message (
                    "<:icon_cross:1372375094336425986> Could not find your ticket information. Please try again later.",
                    ephemeral =True 
                    )
                    return 

            if not self .ticket_info :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> No ticket information found. This rating may have expired.",
                ephemeral =True 
                )
                return 


            modal =FeedbackModal (rating ,self .ticket_info ,self .transcript ,self .original_message ,interaction .message )
            await interaction .response .send_modal (modal )

        except Exception as e :
            logger .error (f"Error handling rating selection: {e}")
            try :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> An error occurred while processing your rating. Please try again.",
                ephemeral =True 
                )
            except :
                pass 

class RatingView (discord .ui .View ):
    """Legacy view for backwards compatibility"""
    def __init__ (self ,ticket_info :Dict [str ,Any ]=None ,transcript :str =""):
        super ().__init__ (timeout =None )
        self .ticket_info =ticket_info or {}
        self .transcript =transcript 

class FeedbackModal (discord .ui .Modal ):
    def __init__ (self ,rating :int ,ticket_info :Dict [str ,Any ],transcript :str ,original_message =None ,rating_message =None ):
        super ().__init__ (title =f"Rate Your Experience ({rating}/5)")
        self .rating =rating 
        self .ticket_info =ticket_info 
        self .transcript =transcript 
        self .original_message =original_message 
        self .rating_message =rating_message 

        self .feedback =discord .ui .TextInput (
        label ="Additional Feedback (Optional)",
        placeholder ="Tell us about your experience...",
        style =discord .TextStyle .paragraph ,
        max_length =500 ,
        required =False 
        )
        self .add_item (self .feedback )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            cog =interaction .client .get_cog ("AdvancedTicketSystem")
            if not cog :
                pass 
                return 


            if not self .ticket_info or not isinstance (self .ticket_info ,dict ):
                await interaction .response .send_message ("<:icon_cross:1372375094336425986> Invalid ticket information.",ephemeral =True )
                return 

            ticket_number =self .ticket_info .get ('ticket_number',0 )
            guild_id =self .ticket_info .get ('guild_id',0 )

            if not ticket_number or not guild_id :
                await interaction .response .send_message ("<:icon_cross:1372375094336425986> Missing ticket information.",ephemeral =True )
                return 


            try :
                async with aiosqlite .connect ("db/tickets.db")as db :
                    await db .execute ("""
                        INSERT OR REPLACE INTO ticket_ratings 
                        (ticket_id, guild_id, user_id, rating, feedback, rated_at)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,(
                    ticket_number ,
                    guild_id ,
                    interaction .user .id ,
                    self .rating ,
                    self .feedback .value or None ,
                    datetime .datetime .utcnow ().isoformat ()
                    ))
                    await db .commit ()
                    logger .info (f"Rating stored for ticket #{ticket_number} by user {interaction.user.id}")
            except Exception as e :
                return 


            try :
                await cog .log_ticket_event (guild_id ,"Rated",{
                'ticket_name':f"Ticket #{ticket_number}",
                'user_id':interaction .user .id ,
                'rating':self .rating ,
                'feedback':self .feedback .value ,
                'ticket_number':ticket_number 
                })
            except Exception as e :
                logger .error (f"Error logging rating event: {log_error}")


            stars ="⭐"*self .rating 


            thank_you_embed =discord .Embed (
            title ="<:icon_tick:1372375089668161597> Thanks for Rating!",
            description =f"**Rating:** {stars} ({self.rating}/5)\n\nYour feedback has been recorded and will help us improve our support quality. Thank you for taking the time to share your experience!",
            color =0x00FF00 
            )
            thank_you_embed .set_footer (text ="We appreciate your feedback!")


            try :
                await interaction .response .edit_message (embed =thank_you_embed ,view =None )
            except :

                await interaction .response .send_message (embed =thank_you_embed ,ephemeral =True )

        except discord .InteractionResponded :
            logger .warning ("Interaction already responded to in feedback modal")
        except Exception as e :
            logger .error (f"Error submitting rating: {e}")
            import traceback 
            logger .error (f"Full traceback: {traceback.format_exc()}")

            try :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> An error occurred while submitting your rating. Please try again.",
                ephemeral =True 
                )
            except discord .InteractionResponded :
                try :
                    await interaction .followup .send (
                    "<:icon_cross:1372375094336425986> An error occurred while submitting your rating. Please try again.",
                    ephemeral =True 
                    )
                except :
                    pass 

class TicketResetConfirmView (discord .ui .View ):
    def __init__ (self ,author :discord .Member ,cog ,guild :discord .Guild ):
        super ().__init__ (timeout =60 )
        self .author =author 
        self .cog =cog 
        self .guild =guild 

    @discord .ui .button (label ="Confirm Reset",style =discord .ButtonStyle .danger ,emoji ="<:icon_danger:1373170993236803688>",custom_id ="ticket_reset_confirm")
    async def confirm_reset (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the command author can confirm this action.",ephemeral =True )
            return 

        try :
            await interaction .response .defer ()

            deleted_channels =0 
            deleted_categories =0 
            errors =[]

            try :
                async with aiosqlite .connect ("db/tickets.db")as db :

                    async with db .execute ("""
                        SELECT channel_id FROM ticket_instances 
                        WHERE guild_id = ?
                    """,(self .guild .id ,))as cursor :
                        all_tickets =await cursor .fetchall ()


                    for channel_id ,in all_tickets :
                        try :
                            channel =self .guild .get_channel (channel_id )
                            if channel :
                                await channel .delete (reason ="Ticket system reset")
                                deleted_channels +=1 
                        except Exception as e :
                            errors .append (f"Error deleting ticket channel {channel_id}: {str(e)}")


                    async with db .execute ("""
                        SELECT discord_category_id FROM ticket_categories 
                        WHERE guild_id = ?
                    """,(self .guild .id ,))as cursor :
                        categories =await cursor .fetchall ()


                    for category_id ,in categories :
                        if category_id :
                            try :
                                category =self .guild .get_channel (category_id )
                                if category :

                                    for channel in category .channels :
                                        try :
                                            await channel .delete (reason ="Ticket system reset - cleaning category")
                                        except :
                                            pass 

                                    await category .delete (reason ="Ticket system reset")
                                    deleted_categories +=1 
                            except Exception as e :
                                errors .append (f"Error deleting category {category_id}: {str(e)}")


                    tables_to_clear =[
                    "ticket_panels","ticket_ratings","ticket_instances",
                    "ticket_categories","ticket_support_roles","ticket_cooldowns",
                    "ticket_messages","tickets"
                    ]

                    for table in tables_to_clear :
                        try :
                            await db .execute (f"DELETE FROM {table} WHERE guild_id = ?",(self .guild .id ,))
                        except Exception as e :
                            pass 

                    await db .commit ()

            except Exception as e :
                pass 


            if errors :
                embed =self .cog .create_branded_embed (
                "<:icon_danger:1372375135604047902> Ticket System Reset Completed with Warnings",
                f"The ticket system for **{self.guild.name}** has been reset with some warnings.\n\n"
                f"**Statistics:**\n"
                f"• Deleted {deleted_channels} ticket channels\n"
                f"• Deleted {deleted_categories} category channels\n"
                f"• Database cleared successfully\n\n"
                f"**Warnings ({len(errors)}):**\n"+
                "\n".join ([f"• {error}"for error in errors [:5 ]])+
                (f"\n• ... and {len(errors) - 5} more"if len (errors )>5 else "")+
                f"\n\nYou can now use `ticket setup` to configure a new ticket system."
                )
                embed .color =0xFFA500 
            else :
                embed =self .cog .create_branded_embed (
                "<:icon_tick:1372375089668161597> Ticket System Reset Complete",
                f"The ticket system for **{self.guild.name}** has been completely reset!\n\n"
                f"**Statistics:**\n"
                f"• Deleted {deleted_channels} ticket channels\n"
                f"• Deleted {deleted_categories} category channels\n"
                f"• Cleared all ticket data from database\n\n"
                f"You can now use `ticket setup` to configure a new ticket system."
                )


            for item in self .children :
                item .disabled =True 

            await interaction .edit_original_response (embed =embed ,view =self )

        except Exception as e :
            logger .error (f"Critical error during ticket system reset: {e}")


            error_embed =self .cog .create_branded_embed (
            "<:icon_cross:1372375094336425986> Reset Failed",
            f"A critical error occurred during the reset process:\n\n"
            f"**Error:** {str(e)}\n\n"
            f"The ticket system may be partially reset."
            )
            error_embed .color =0xFF0000 


            for item in self .children :
                item .disabled =True 

            try :
                await interaction .edit_original_response (embed =error_embed ,view =self )
            except :
                pass 

    @discord .ui .button (label ="Cancel",style =discord .ButtonStyle .secondary ,emoji ="<:close:1388408726716682281>",custom_id ="ticket_reset_cancel")
    async def cancel_reset (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the command author can cancel this action.",ephemeral =True )
            return 

        embed =self .cog .create_branded_embed (
        "<:icon_cross:1372375094336425986> Reset Cancelled",
        "The ticket system reset has been cancelled. No changes were made."
        )


        for item in self .children :
            item .disabled =True 

        await interaction .response .edit_message (embed =embed ,view =self )

class TicketCloseConfirmView (discord .ui .View ):
    def __init__ (self ,author :discord .Member ,cog ):
        super ().__init__ (timeout =60 )
        self .author =author 
        self .cog =cog 

    @discord .ui .button (label ="Confirm",emoji ="<:icon_tick:1372375089668161597>",style =discord .ButtonStyle .danger ,custom_id ="ticket_close_confirm")
    async def confirm_close (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the person who requested the closure can confirm.",ephemeral =True )
            return 

        await interaction .response .defer ()

        try :

            ticket_info =await self .cog .get_ticket_info (interaction .channel .id )
            if not ticket_info :
                await interaction .followup .send ("<:icon_cross:1372375094336425986> Could not retrieve ticket information.",ephemeral =True )
                return 


            transcript =await self .cog .generate_transcript (interaction .channel )


            created_at =datetime .datetime .fromisoformat (ticket_info ['created_at'])
            duration =datetime .datetime .utcnow ()-created_at 
            duration_str =self .cog .format_duration (duration )


            message_count =len (transcript .split ('\n'))-1 


            async with aiosqlite .connect ("db/tickets.db")as db :
                await db .execute ("""
                    UPDATE ticket_instances 
                    SET status = 'closed', closer_id = ?, closed_at = ?
                    WHERE channel_id = ?
                """,(interaction .user .id ,datetime .datetime .utcnow ().isoformat (),interaction .channel .id ))
                await db .commit ()


            await self .cog .log_ticket_event (interaction .guild .id ,"Closed",{
            'ticket_name':interaction .channel .name ,
            'creator_id':ticket_info ['creator_id'],
            'closer_id':interaction .user .id ,
            'category':ticket_info ['category'],
            'duration':duration_str ,
            'message_count':message_count ,
            'transcript':transcript ,
            'ticket_number':ticket_info ['ticket_number']
            })


            embed =self .cog .create_branded_embed (
            "🔒 Ticket Closed",
            f"This ticket has been closed by {interaction.user.mention}\n\n"
            f"**📊 Statistics:**\n"
            f"• Duration: {duration_str}\n"
            f"• Messages: {message_count}\n"
            f"• Category: {ticket_info['category']}\n\n"
            f"*This channel will be deleted in 10 seconds...*"
            )

            await interaction .followup .send (embed =embed )


            await self .cog .send_rating_dm (ticket_info ['creator_id'],ticket_info ,transcript )


            await asyncio .sleep (10 )
            await interaction .channel .delete (reason =f"Ticket closed by {interaction.user}")

        except Exception as e :
            logger .error (f"Error closing ticket: {e}")
            pass 

    @discord .ui .button (label ="Cancel",emoji ="<:close:1388408726716682281>",style =discord .ButtonStyle .secondary ,custom_id ="ticket_close_cancel")
    async def cancel_close (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .author :
            await interaction .response .send_message ("Only the person who requested the closure can cancel.",ephemeral =True )
            return 

        embed =self .cog .create_branded_embed (
        "<:icon_cross:1372375094336425986> Ticket Closure Cancelled",
        "The ticket closure has been cancelled. The ticket remains open."
        )
        embed .color =0x00FF00 


        for item in self .children :
            item .disabled =True 

        await interaction .response .edit_message (embed =embed ,view =self )

class TicketAuthorInfoView (discord .ui .View ):
    def __init__ (self ,author_id :int ):
        super ().__init__ (timeout =None )
        self .author_id =author_id 

    @discord .ui .button (label ="Ticket Author Info",emoji ="<:icon_tick:1372375089668161597>",style =discord .ButtonStyle .primary ,custom_id ="ticket_author_info")
    async def show_author_info (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :

            try :
                user =await interaction .client .fetch_user (self .author_id )
            except :
                user =interaction .client .get_user (self .author_id )

            member =interaction .guild .get_member (self .author_id )if interaction .guild else None 

            if not user :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> Could not find user information.",
                ephemeral =True 
                )
                return 

            embed =discord .Embed (
            title ="🎫 Ticket Author Information",
            color =0x000000 ,
            timestamp =datetime .datetime .utcnow ()
            )

            embed .set_thumbnail (url =user .display_avatar .url )


            embed .add_field (name ="👤 Display Name",value =user .display_name ,inline =True )
            embed .add_field (name ="🏷️ Username",value =f"@{user.name}",inline =True )
            embed .add_field (name ="🆔 User ID",value =str (user .id ),inline =True )


            created_timestamp =int (user .created_at .timestamp ())
            embed .add_field (
            name ="📅 Registered On",
            value =f"<t:{created_timestamp}:F>\n<t:{created_timestamp}:R>",
            inline =True 
            )

            if member :

                joined_timestamp =int (member .joined_at .timestamp ())
                embed .add_field (
                name ="📥 Joined Server",
                value =f"<t:{joined_timestamp}:F>\n<t:{joined_timestamp}:R>",
                inline =True 
                )


                perms =member .guild_permissions 
                key_perms =[]
                if perms .administrator :
                    key_perms .append ("Administrator")
                elif perms .manage_guild :
                    key_perms .append ("Manage Server")
                elif perms .manage_channels :
                    key_perms .append ("Manage Channels")
                elif perms .manage_messages :
                    key_perms .append ("Manage Messages")
                elif perms .kick_members :
                    key_perms .append ("Kick Members")
                elif perms .ban_members :
                    key_perms .append ("Ban Members")

                if not key_perms :
                    key_perms .append ("Regular Member")

                embed .add_field (
                name ="🔑 Key Permissions",
                value ="```\n"+"\n".join (key_perms [:5 ])+"\n```",
                inline =True 
                )


                status_emoji ={
                discord .Status .online :"🟢",
                discord .Status .idle :"🟡",
                discord .Status .dnd :"🔴",
                discord .Status .offline :"⚫"
                }

                embed .add_field (
                name ="📊 Status",
                value =f"{status_emoji.get(member.status, '❓')} {str(member.status).title()}",
                inline =True 
                )


                if member .roles [1 :]:
                    roles =sorted (member .roles [1 :],key =lambda r :r .position ,reverse =True )
                    role_list =[]
                    for role in roles [:15 ]:
                        role_list .append (f"• {role.name}")

                    if len (roles )>15 :
                        role_list .append (f"... +{len(roles) - 15} more roles")

                    roles_text ="```\n"+"\n".join (role_list )+"\n```"
                    embed .add_field (
                    name =f"🎭 Roles ({len(roles)})",
                    value =roles_text ,
                    inline =False 
                    )
            else :
                embed .add_field (
                name ="<:icon_danger:1372375135604047902> Server Status",
                value ="User is not in this server",
                inline =False 
                )

            embed .set_footer (
            text ="Developed By AeroX Development",
            icon_url =interaction .client .user .avatar .url if interaction .client .user .avatar else None 
            )

            await interaction .response .send_message (embed =embed ,ephemeral =True )

        except Exception as e :
            logger .error (f"Error showing author info: {e}")
            await interaction .response .send_message (
            "<:icon_cross:1372375094336425986> An error occurred while fetching author information.",
            ephemeral =True 
            )

async def setup (bot ):
    cog =AdvancedTicketSystem (bot )
    await bot .add_cog (cog )


    try :

        if not bot .is_ready ():
            await bot .wait_until_ready ()


        ticket_control_view =TicketControlView ()
        ticket_control_view .timeout =None 
        bot .add_view (ticket_control_view )


        rating_view =RatingView ()
        rating_view .timeout =None 
        bot .add_view (rating_view )

        rating_select_view =RatingSelectOnlyView ()
        rating_select_view .timeout =None 
        bot .add_view (rating_select_view )

        staff_panel_view =StaffPanelView ()
        staff_panel_view .timeout =None 
        bot .add_view (staff_panel_view )

        transfer_view =TransferTicketView ()
        transfer_view .timeout =None 
        bot .add_view (transfer_view )


        author_info_view =TicketAuthorInfoView (0 )
        author_info_view .timeout =None 
        bot .add_view (author_info_view )

        logger .info ("All persistent views registered successfully")
    except Exception as e :
        logger .error (f"Error adding persistent views: {e}")
        import traceback 
        logger .error (f"Persistent view setup traceback: {traceback.format_exc()}")
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
