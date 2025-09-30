import discord 
from discord .ext import commands ,tasks 
import aiosqlite 
import aiohttp 
import os 
from utils .Tools import blacklist_check ,ignore_check 
import asyncio 
from typing import Optional 
import time 

DB_PATH ="db/vanity.db"

class VanityRoles (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .bot .loop .create_task (self .initialize_db ())
        self .vanity_checker .start ()
        self .stats ={
        "checks_performed":0 ,
        "roles_assigned":0 ,
        "roles_removed":0 ,
        "last_check":None 
        }

    async def initialize_db (self ):
        os .makedirs (os .path .dirname (DB_PATH ),exist_ok =True )
        async with aiosqlite .connect (DB_PATH )as db :
            await db .execute ("""
                CREATE TABLE IF NOT EXISTS vanity_roles (
                    guild_id INTEGER,
                    vanity TEXT NOT NULL,
                    role_id INTEGER NOT NULL,
                    log_channel_id INTEGER NOT NULL,
                    current_status TEXT,
                    created_at INTEGER DEFAULT (strftime('%s', 'now')),
                    last_checked INTEGER DEFAULT (strftime('%s', 'now')),
                    total_assigned INTEGER DEFAULT 0,
                    total_removed INTEGER DEFAULT 0,
                    enabled INTEGER DEFAULT 1,
                    PRIMARY KEY (guild_id, vanity)
                )
            """)
            await db .commit ()


            columns_to_add =[
            ("created_at","INTEGER DEFAULT (strftime('%s', 'now'))"),
            ("last_checked","INTEGER DEFAULT (strftime('%s', 'now'))"),
            ("total_assigned","INTEGER DEFAULT 0"),
            ("total_removed","INTEGER DEFAULT 0"),
            ("enabled","INTEGER DEFAULT 1")
            ]

            async with db .execute ("PRAGMA table_info(vanity_roles)")as cursor :
                existing_columns =[column [1 ]for column in await cursor .fetchall ()]

            for column_name ,column_def in columns_to_add :
                if column_name not in existing_columns :
                    await db .execute (f"ALTER TABLE vanity_roles ADD COLUMN {column_name} {column_def}")
                    await db .commit ()

    def _clean_vanity_url (self ,vanity :str )->str :
        """Clean and normalize vanity URL"""
        vanity_clean =vanity .lower ().strip ()
        for prefix in ["https://discord.gg/","discord.gg/","http://discord.gg/"]:
            if vanity_clean .startswith (prefix ):
                vanity_clean =vanity_clean .replace (prefix ,"")
        return vanity_clean 

    async def _test_vanity_url (self ,vanity :str )->tuple [bool ,str ]:
        """Test vanity URL and return status"""
        try :
            async with aiohttp .ClientSession ()as session :
                async with session .get (f"https://discord.com/api/v10/invites/{vanity}")as response :
                    if response .status ==200 :
                        return True ,"Active"
                    elif response .status ==404 :
                        return False ,"Not Found"
                    else :
                        return False ,f"Error ({response.status})"
        except Exception :
            return False ,"Connection Error"

    @commands .group (name ="vanityroles",invoke_without_command =True )
    @blacklist_check ()
    @ignore_check ()
    async def vanityroles (self ,ctx ):
        embed =discord .Embed (
        title ="Vanity Roles Management",
        description ="Advanced vanity role system for automatic role assignment based on server vanity URL status.",
        color =0x000000 
        )


        async with aiosqlite .connect (DB_PATH )as db :
            cursor =await db .execute ("SELECT COUNT(*) FROM vanity_roles WHERE guild_id = ?",(ctx .guild .id ,))
            config_count =(await cursor .fetchone ())[0 ]

            cursor =await db .execute ("SELECT SUM(total_assigned), SUM(total_removed) FROM vanity_roles WHERE guild_id = ?",(ctx .guild .id ,))
            stats =await cursor .fetchone ()
            total_assigned =stats [0 ]or 0 
            total_removed =stats [1 ]or 0 

        embed .add_field (
        name ="Setup Command",
        value ="`vanityroles setup <vanity> <@role> <#log_channel>`\nConfigure a new vanity role assignment",
        inline =True 
        )
        embed .add_field (
        name ="View Command",
        value ="`vanityroles show`\nDisplay all configurations with detailed status",
        inline =True 
        )
        embed .add_field (
        name ="Reset Command",
        value ="`vanityroles reset`\nRemove all vanity role configurations",
        inline =True 
        )
        embed .add_field (
        name ="Statistics Command",
        value ="`vanityroles stats`\nView detailed system statistics",
        inline =True 
        )
        embed .add_field (
        name ="Test Command",
        value ="`vanityroles test <vanity>`\nTest vanity URL status manually",
        inline =True 
        )
        embed .add_field (
        name ="Toggle Command",
        value ="`vanityroles toggle <vanity>`\nEnable/disable specific configurations",
        inline =True 
        )

        embed .add_field (
        name ="Server Status",
        value =f"**Configurations:** {config_count}\n**Total Assigned:** {total_assigned}\n**Total Removed:** {total_removed}",
        inline =False 
        )

        embed .set_footer (text =f"Requested by {ctx.author} | System checks every 60 seconds",icon_url =ctx .author .display_avatar .url )
        await ctx .send (embed =embed )

    @vanityroles .command (name ="setup")
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (manage_guild =True )
    async def setup (self ,ctx ,vanity :str ,role :discord .Role ,channel :discord .TextChannel ):
        """Setup a vanity role configuration with advanced validation"""


        if not ctx .guild .me .guild_permissions .manage_roles :
            embed =discord .Embed (
            title ="Permission Required",
            description ="The bot requires `Manage Roles` permission to operate the vanity role system.",
            color =0x000000 
            )
            embed .add_field (name ="Required Permission",value ="Manage Roles",inline =True )
            embed .add_field (name ="Current Status",value ="Missing",inline =True )
            embed .set_footer (text ="Please grant the required permission and try again")
            return await ctx .send (embed =embed )

        if role .position >=ctx .guild .me .top_role .position :
            embed =discord .Embed (
            title ="Role Hierarchy Error",
            description ="The specified role cannot be managed due to role hierarchy restrictions.",
            color =0x000000 
            )
            embed .add_field (name ="Target Role Position",value =str (role .position ),inline =True )
            embed .add_field (name ="Bot Highest Role Position",value =str (ctx .guild .me .top_role .position ),inline =True )
            embed .add_field (name ="Solution",value ="Move the bot's role above the target role",inline =False )
            return await ctx .send (embed =embed )


        vanity_clean =self ._clean_vanity_url (vanity )


        is_valid ,status_msg =await self ._test_vanity_url (vanity_clean )

        try :
            async with aiosqlite .connect (DB_PATH )as db :

                cursor =await db .execute ("SELECT vanity FROM vanity_roles WHERE guild_id = ? AND vanity = ?",(ctx .guild .id ,vanity_clean ))
                existing =await cursor .fetchone ()

                await db .execute ("""
                    INSERT OR REPLACE INTO vanity_roles 
                    (guild_id, vanity, role_id, log_channel_id, current_status, created_at, last_checked, total_assigned, total_removed, enabled)
                    VALUES (?, ?, ?, ?, ?, ?, ?, 0, 0, 1)
                """,(ctx .guild .id ,vanity_clean ,role .id ,channel .id ,"active"if is_valid else "inactive",int (time .time ()),int (time .time ())))
                await db .commit ()

            embed =discord .Embed (
            title ="Configuration Complete",
            description ="Vanity role system has been successfully configured with advanced monitoring.",
            color =0x000000 
            )
            embed .add_field (name ="Vanity URL",value =f"`discord.gg/{vanity_clean}`",inline =True )
            embed .add_field (name ="Assigned Role",value =role .mention ,inline =True )
            embed .add_field (name ="Log Channel",value =channel .mention ,inline =True )
            embed .add_field (name ="Initial Status",value =status_msg ,inline =True )
            embed .add_field (name ="Check Interval",value ="60 seconds",inline =True )
            embed .add_field (name ="Configuration Type",value ="Updated"if existing else "New",inline =True )

            embed .set_footer (text =f"Setup by {ctx.author} | Monitoring will begin immediately",icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            title ="Setup Error",
            description ="An error occurred during vanity role configuration.",
            color =0x000000 
            )
            embed .add_field (name ="Error Details",value =f"```{str(e)[:100]}```",inline =False )
            embed .add_field (name ="Troubleshooting",value ="Verify permissions and try again",inline =False )
            await ctx .send (embed =embed )

    @vanityroles .command (name ="show")
    @blacklist_check ()
    @ignore_check ()
    async def show (self ,ctx ):
        """Display all vanity role configurations with detailed status"""
        try :
            async with aiosqlite .connect (DB_PATH )as db :
                async with db .execute ("""
                    SELECT vanity, role_id, log_channel_id, current_status, created_at, 
                           total_assigned, total_removed, enabled, last_checked
                    FROM vanity_roles WHERE guild_id = ?
                """,(ctx .guild .id ,))as cursor :
                    rows =await cursor .fetchall ()

            if not rows :
                embed =discord .Embed (
                title ="Vanity Role Configurations",
                description ="No vanity role configurations found for this server.",
                color =0x000000 
                )
                embed .add_field (name ="Getting Started",value ="Use `vanityroles setup` to create your first configuration",inline =False )
                return await ctx .send (embed =embed )

            embed =discord .Embed (
            title ="Vanity Role Configurations",
            description =f"Displaying {len(rows)} active configuration(s)",
            color =0x000000 
            )

            for vanity ,role_id ,log_channel_id ,current_status ,created_at ,total_assigned ,total_removed ,enabled ,last_checked in rows :
                role =ctx .guild .get_role (role_id )
                channel =ctx .guild .get_channel (log_channel_id )

                status_indicator ="Active"if current_status =="active"else "Inactive"
                enabled_status ="Enabled"if enabled else "Disabled"
                created_time =f"<t:{created_at}:R>"if created_at else "Unknown"
                last_check_time =f"<t:{last_checked}:R>"if last_checked else "Never"

                field_value =f"**Role:** {role.mention if role else f'`{role_id}` (deleted)'}\n"
                field_value +=f"**Log Channel:** {channel.mention if channel else f'`{log_channel_id}` (deleted)'}\n"
                field_value +=f"**Status:** {status_indicator} ({enabled_status})\n"
                field_value +=f"**Statistics:** {total_assigned} assigned, {total_removed} removed\n"
                field_value +=f"**Created:** {created_time} | **Last Check:** {last_check_time}"

                embed .add_field (
                name =f"discord.gg/{vanity}",
                value =field_value ,
                inline =False 
                )

            embed .set_footer (text =f"Requested by {ctx.author} | Use 'vanityroles stats' for detailed analytics",
            icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            title ="Display Error",
            description ="An error occurred while retrieving configurations.",
            color =0x000000 
            )
            embed .add_field (name ="Error Details",value =f"```{str(e)[:100]}```",inline =False )
            await ctx .send (embed =embed )

    @vanityroles .command (name ="reset")
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (manage_guild =True )
    async def reset (self ,ctx ):
        """Reset all vanity role configurations with confirmation"""
        try :
            async with aiosqlite .connect (DB_PATH )as db :
                cursor =await db .execute ("SELECT COUNT(*) FROM vanity_roles WHERE guild_id = ?",(ctx .guild .id ,))
                count =(await cursor .fetchone ())[0 ]

                if count ==0 :
                    embed =discord .Embed (
                    title ="No Configurations",
                    description ="No vanity role configurations found to reset.",
                    color =0x000000 
                    )
                    embed .add_field (name ="Current Status",value ="No active configurations",inline =False )
                    return await ctx .send (embed =embed )

                await db .execute ("DELETE FROM vanity_roles WHERE guild_id = ?",(ctx .guild .id ,))
                await db .commit ()

            embed =discord .Embed (
            title ="Reset Complete",
            description ="All vanity role configurations have been successfully removed.",
            color =0x000000 
            )
            embed .add_field (name ="Configurations Removed",value =str (count ),inline =True )
            embed .add_field (name ="Status",value ="System reset",inline =True )
            embed .set_footer (text =f"Reset by {ctx.author} | Use 'vanityroles setup' to create new configurations",
            icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            title ="Reset Error",
            description ="An error occurred during the reset operation.",
            color =0x000000 
            )
            embed .add_field (name ="Error Details",value =f"```{str(e)[:100]}```",inline =False )
            await ctx .send (embed =embed )

    @vanityroles .command (name ="stats")
    @blacklist_check ()
    @ignore_check ()
    async def stats (self ,ctx ):
        """Display detailed system statistics"""
        try :
            async with aiosqlite .connect (DB_PATH )as db :

                cursor =await db .execute ("""
                    SELECT COUNT(*), SUM(total_assigned), SUM(total_removed), 
                           COUNT(CASE WHEN enabled = 1 THEN 1 END),
                           COUNT(CASE WHEN current_status = 'active' THEN 1 END)
                    FROM vanity_roles WHERE guild_id = ?
                """,(ctx .guild .id ,))
                server_stats =await cursor .fetchone ()


                cursor =await db .execute ("""
                    SELECT COUNT(*), SUM(total_assigned), SUM(total_removed)
                    FROM vanity_roles
                """)
                global_stats =await cursor .fetchone ()

            embed =discord .Embed (
            title ="Vanity Roles Statistics",
            description ="Comprehensive system analytics and performance metrics",
            color =0x000000 
            )


            embed .add_field (
            name ="Server Statistics",
            value =f"**Total Configurations:** {server_stats[0] or 0}\n"
            f"**Enabled Configurations:** {server_stats[3] or 0}\n"
            f"**Currently Active:** {server_stats[4] or 0}\n"
            f"**Total Roles Assigned:** {server_stats[1] or 0}\n"
            f"**Total Roles Removed:** {server_stats[2] or 0}",
            inline =True 
            )


            embed .add_field (
            name ="System Statistics",
            value =f"**Global Configurations:** {global_stats[0] or 0}\n"
            f"**Global Roles Assigned:** {global_stats[1] or 0}\n"
            f"**Global Roles Removed:** {global_stats[2] or 0}\n"
            f"**Checks Performed:** {self.stats['checks_performed']}\n"
            f"**Last Check:** {self.stats['last_check'] or 'Never'}",
            inline =True 
            )


            efficiency =0 
            if server_stats [1 ]and server_stats [2 ]:
                efficiency =round ((server_stats [1 ]/(server_stats [1 ]+server_stats [2 ]))*100 ,1 )

            embed .add_field (
            name ="Performance Metrics",
            value =f"**Assignment Efficiency:** {efficiency}%\n"
            f"**Average Per Config:** {round((server_stats[1] or 0) / max(server_stats[0] or 1, 1), 1)}\n"
            f"**System Uptime:** Active\n"
            f"**Database Status:** Operational",
            inline =False 
            )

            embed .set_footer (text =f"Statistics requested by {ctx.author} | Updated in real-time",
            icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            title ="Statistics Error",
            description ="An error occurred while retrieving statistics.",
            color =0x000000 
            )
            embed .add_field (name ="Error Details",value =f"```{str(e)[:100]}```",inline =False )
            await ctx .send (embed =embed )

    @vanityroles .command (name ="test")
    @blacklist_check ()
    @ignore_check ()
    async def test (self ,ctx ,vanity :str ):
        """Test a vanity URL status manually"""
        vanity_clean =self ._clean_vanity_url (vanity )

        embed =discord .Embed (
        title ="Testing Vanity URL",
        description =f"Performing live test of `discord.gg/{vanity_clean}`",
        color =0x000000 
        )
        embed .add_field (name ="Status",value ="Testing...",inline =False )
        message =await ctx .send (embed =embed )

        is_valid ,status_msg =await self ._test_vanity_url (vanity_clean )

        embed =discord .Embed (
        title ="Vanity URL Test Results",
        description =f"Test completed for `discord.gg/{vanity_clean}`",
        color =0x000000 
        )
        embed .add_field (name ="URL Status",value =status_msg ,inline =True )
        embed .add_field (name ="Accessible",value ="Yes"if is_valid else "No",inline =True )
        embed .add_field (name ="Test Time",value =f"<t:{int(time.time())}:T>",inline =True )

        if is_valid :
            embed .add_field (name ="Recommendation",value ="This vanity URL is active and can be used for role assignment",inline =False )
        else :
            embed .add_field (name ="Recommendation",value ="This vanity URL is not accessible and will not trigger role assignments",inline =False )

        embed .set_footer (text =f"Test performed by {ctx.author}",icon_url =ctx .author .display_avatar .url )
        await message .edit (embed =embed )

    @vanityroles .command (name ="toggle")
    @blacklist_check ()
    @ignore_check ()
    @commands .has_permissions (manage_guild =True )
    async def toggle (self ,ctx ,vanity :str ):
        """Enable or disable a specific vanity role configuration"""
        vanity_clean =self ._clean_vanity_url (vanity )

        try :
            async with aiosqlite .connect (DB_PATH )as db :
                cursor =await db .execute ("SELECT enabled FROM vanity_roles WHERE guild_id = ? AND vanity = ?",(ctx .guild .id ,vanity_clean ))
                result =await cursor .fetchone ()

                if not result :
                    embed =discord .Embed (
                    title ="Configuration Not Found",
                    description =f"No vanity role configuration found for `discord.gg/{vanity_clean}`",
                    color =0x000000 
                    )
                    embed .add_field (name ="Available Configurations",value ="Use `vanityroles show` to view existing configurations",inline =False )
                    return await ctx .send (embed =embed )

                current_status =result [0 ]
                new_status =0 if current_status else 1 

                await db .execute ("UPDATE vanity_roles SET enabled = ? WHERE guild_id = ? AND vanity = ?",
                (new_status ,ctx .guild .id ,vanity_clean ))
                await db .commit ()

            status_text ="Enabled"if new_status else "Disabled"
            embed =discord .Embed (
            title ="Configuration Updated",
            description =f"Vanity role configuration has been {status_text.lower()}",
            color =0x000000 
            )
            embed .add_field (name ="Vanity URL",value =f"`discord.gg/{vanity_clean}`",inline =True )
            embed .add_field (name ="New Status",value =status_text ,inline =True )
            embed .add_field (name ="Effect",value ="Monitoring active"if new_status else "Monitoring paused",inline =True )

            embed .set_footer (text =f"Updated by {ctx.author} | Changes take effect immediately",
            icon_url =ctx .author .display_avatar .url )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            title ="Toggle Error",
            description ="An error occurred while updating the configuration.",
            color =0x000000 
            )
            embed .add_field (name ="Error Details",value =f"```{str(e)[:100]}```",inline =False )
            await ctx .send (embed =embed )

    @tasks .loop (seconds =60 )
    async def vanity_checker (self ):
        """Advanced background task to monitor vanity URLs and manage roles"""
        try :
            self .stats ["checks_performed"]+=1 
            self .stats ["last_check"]=f"<t:{int(time.time())}:T>"

            async with aiohttp .ClientSession ()as session :
                async with aiosqlite .connect (DB_PATH )as db :
                    async with db .execute ("""
                        SELECT guild_id, vanity, role_id, log_channel_id, current_status, total_assigned, total_removed
                        FROM vanity_roles WHERE enabled = 1
                    """)as cursor :
                        rows =await cursor .fetchall ()

                for guild_id ,vanity ,role_id ,log_channel_id ,current_status ,total_assigned ,total_removed in rows :
                    guild =self .bot .get_guild (guild_id )
                    if not guild :
                        continue 

                    role =guild .get_role (role_id )
                    log_channel =guild .get_channel (log_channel_id )


                    if not role or not log_channel :
                        continue 


                    if not guild .me .guild_permissions .manage_roles :
                        continue 


                    is_active ,_ =await self ._test_vanity_url (vanity )


                    await self ._update_check_time (guild_id ,vanity )


                    if is_active and current_status !="active":
                        assigned =await self ._assign_roles (guild ,role ,vanity )
                        await self ._update_status_and_stats (guild_id ,vanity ,"active",assigned ,0 )
                        await self ._send_log_message (log_channel ,vanity ,role ,"active",assigned )
                        self .stats ["roles_assigned"]+=assigned 

                    elif not is_active and current_status =="active":
                        removed =await self ._remove_roles (guild ,role ,vanity )
                        await self ._update_status_and_stats (guild_id ,vanity ,"inactive",0 ,removed )
                        await self ._send_log_message (log_channel ,vanity ,role ,"inactive",removed )
                        self .stats ["roles_removed"]+=removed 

        except Exception as e :
            print (f"[FATAL] Vanity check loop crashed: {e}")

    async def _assign_roles (self ,guild :discord .Guild ,role :discord .Role ,vanity :str )->int :
        """Assign roles to eligible members"""
        assigned =0 
        for member in guild .members :
            if (member .status !=discord .Status .offline and 
            role not in member .roles and 
            not member .bot ):
                try :
                    await member .add_roles (role ,reason =f"Vanity URL {vanity} is active")
                    assigned +=1 
                except (discord .Forbidden ,discord .HTTPException ):
                    continue 
        return assigned 

    async def _remove_roles (self ,guild :discord .Guild ,role :discord .Role ,vanity :str )->int :
        """Remove roles from members"""
        removed =0 
        for member in guild .members :
            if role in member .roles and not member .bot :
                try :
                    await member .remove_roles (role ,reason =f"Vanity URL {vanity} is inactive")
                    removed +=1 
                except (discord .Forbidden ,discord .HTTPException ):
                    continue 
        return removed 

    async def _send_log_message (self ,channel :discord .TextChannel ,vanity :str ,role :discord .Role ,status :str ,count :int ):
        """Send formatted log message"""
        try :
            status_emoji ="🟢"if status =="active"else "🔴"
            action ="assigned"if status =="active"else "removed"

            embed =discord .Embed (
            title =f"Vanity URL Status Change",
            description =f"{status_emoji} `discord.gg/{vanity}` is now **{status}**",
            color =0x000000 
            )
            embed .add_field (name ="Role",value =role .mention ,inline =True )
            embed .add_field (name =f"Roles {action.title()}",value =str (count ),inline =True )
            embed .add_field (name ="Timestamp",value =f"<t:{int(time.time())}:T>",inline =True )
            embed .set_footer (text ="Automated vanity role system")

            await channel .send (embed =embed )
        except Exception :
            pass 

    async def _update_status_and_stats (self ,guild_id :int ,vanity :str ,status :str ,assigned :int ,removed :int ):
        """Update database with new status and statistics"""
        try :
            async with aiosqlite .connect (DB_PATH )as db :
                await db .execute ("""
                    UPDATE vanity_roles 
                    SET current_status = ?, total_assigned = total_assigned + ?, total_removed = total_removed + ?
                    WHERE guild_id = ? AND vanity = ?
                """,(status ,assigned ,removed ,guild_id ,vanity ))
                await db .commit ()
        except Exception :
            pass 

    async def _update_check_time (self ,guild_id :int ,vanity :str ):
        """Update last checked timestamp"""
        try :
            async with aiosqlite .connect (DB_PATH )as db :
                await db .execute ("""
                    UPDATE vanity_roles SET last_checked = ? WHERE guild_id = ? AND vanity = ?
                """,(int (time .time ()),guild_id ,vanity ))
                await db .commit ()
        except Exception :
            pass 

    @vanity_checker .before_loop 
    async def before_checker (self ):
        """Wait for bot to be ready before starting the checker"""
        await self .bot .wait_until_ready ()

    async def cog_unload (self ):
        """Clean up when cog is unloaded"""
        self .vanity_checker .cancel ()

async def setup (bot ):
    await bot .add_cog (VanityRoles (bot ))