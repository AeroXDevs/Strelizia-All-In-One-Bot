import discord 
from discord .ext import commands 
import aiosqlite 
import asyncio 
import datetime 
import pytz 
import json 

class AntiChannelDelete (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .event_limits ={}
        self .cooldowns ={}
        self .channel_snapshots ={}
        self .nuke_detection ={}
        self .emergency_lockdown ={}

    def can_fetch_audit (self ,guild_id ,event_name ,max_requests =1 ,interval =5 ,cooldown_duration =120 ):
        now =datetime .datetime .now ()
        self .event_limits .setdefault (guild_id ,{}).setdefault (event_name ,[]).append (now )

        timestamps =self .event_limits [guild_id ][event_name ]
        timestamps =[t for t in timestamps if (now -t ).total_seconds ()<=interval ]
        self .event_limits [guild_id ][event_name ]=timestamps 

        if guild_id in self .cooldowns and event_name in self .cooldowns [guild_id ]:
            if (now -self .cooldowns [guild_id ][event_name ]).total_seconds ()<cooldown_duration :
                return False 
            del self .cooldowns [guild_id ][event_name ]

        if len (timestamps )>max_requests :
            self .cooldowns .setdefault (guild_id ,{})[event_name ]=now 
            return False 
        return True 

    async def take_channel_snapshot (self ,guild ):
        """Take a snapshot of all channels for recovery purposes"""
        try :
            snapshot ={
            'categories':[],
            'text_channels':[],
            'voice_channels':[],
            'threads':[],
            'timestamp':datetime .datetime .now ().isoformat ()
            }

            for category in guild .categories :
                cat_data ={
                'id':category .id ,
                'name':category .name ,
                'position':category .position ,
                'overwrites':{}
                }
                for target ,overwrite in category .overwrites .items ():
                    cat_data ['overwrites'][str (target .id )]={
                    'type':'role'if isinstance (target ,discord .Role )else 'member',
                    'allow':overwrite .pair ()[0 ].value ,
                    'deny':overwrite .pair ()[1 ].value 
                    }
                snapshot ['categories'].append (cat_data )

            for channel in guild .text_channels :
                ch_data ={
                'id':channel .id ,
                'name':channel .name ,
                'topic':channel .topic ,
                'position':channel .position ,
                'category_id':channel .category .id if channel .category else None ,
                'slowmode_delay':channel .slowmode_delay ,
                'nsfw':channel .nsfw ,
                'overwrites':{}
                }
                for target ,overwrite in channel .overwrites .items ():
                    ch_data ['overwrites'][str (target .id )]={
                    'type':'role'if isinstance (target ,discord .Role )else 'member',
                    'allow':overwrite .pair ()[0 ].value ,
                    'deny':overwrite .pair ()[1 ].value 
                    }
                snapshot ['text_channels'].append (ch_data )

            for channel in guild .voice_channels :
                ch_data ={
                'id':channel .id ,
                'name':channel .name ,
                'position':channel .position ,
                'category_id':channel .category .id if channel .category else None ,
                'bitrate':channel .bitrate ,
                'user_limit':channel .user_limit ,
                'overwrites':{}
                }
                for target ,overwrite in channel .overwrites .items ():
                    ch_data ['overwrites'][str (target .id )]={
                    'type':'role'if isinstance (target ,discord .Role )else 'member',
                    'allow':overwrite .pair ()[0 ].value ,
                    'deny':overwrite .pair ()[1 ].value 
                    }
                snapshot ['voice_channels'].append (ch_data )

            self .channel_snapshots [guild .id ]=snapshot 


            async with aiosqlite .connect ('db/anti.db')as db :
                await db .execute ('''CREATE TABLE IF NOT EXISTS channel_snapshots 
                                   (guild_id INTEGER PRIMARY KEY, snapshot_data TEXT, created_at TIMESTAMP)''')
                await db .execute ('INSERT OR REPLACE INTO channel_snapshots VALUES (?, ?, ?)',
                (guild .id ,json .dumps (snapshot ),datetime .datetime .now ()))
                await db .commit ()

        except Exception as e :
            print (f"Error taking channel snapshot: {e}")

    async def detect_nuke_attempt (self ,guild_id ):
        """Detect if a nuke attempt is happening"""
        now =datetime .datetime .now ()

        if guild_id not in self .nuke_detection :
            self .nuke_detection [guild_id ]=[]


        self .nuke_detection [guild_id ].append (now )


        self .nuke_detection [guild_id ]=[
        event for event in self .nuke_detection [guild_id ]
        if (now -event ).total_seconds ()<=30 
        ]


        return len (self .nuke_detection [guild_id ])>=1 

    async def emergency_lockdown_guild (self ,guild ,executor ):
        """Immediately lockdown guild and remove dangerous permissions"""
        try :
            if guild .id in self .emergency_lockdown :
                return 

            self .emergency_lockdown [guild .id ]=True 


            bot_top_role =guild .me .top_role 
            dangerous_perms =discord .Permissions (
            administrator =False ,
            manage_channels =False ,
            manage_roles =False ,
            manage_guild =False ,
            ban_members =False ,
            kick_members =False 
            )

            for role in guild .roles :
                if role .position <bot_top_role .position and not role .is_default ():
                    try :
                        if role .permissions .administrator or role .permissions .manage_channels :
                            await role .edit (permissions =dangerous_perms ,reason ="Emergency lockdown - Nuke detected")
                            await asyncio .sleep (0.5 )
                    except :
                        continue 


            if executor and executor .bot :
                try :
                    await guild .ban (executor ,reason ="Bot nuke attempt detected - Emergency ban")
                except :
                    pass 

        except Exception as e :
            print (f"Emergency lockdown error: {e}")

    async def full_server_recovery (self ,guild ):
        """Recover entire server structure from snapshot"""
        try :
            if guild .id not in self .channel_snapshots :

                async with aiosqlite .connect ('db/anti.db')as db :
                    async with db .execute ('SELECT snapshot_data FROM channel_snapshots WHERE guild_id = ?',(guild .id ,))as cursor :
                        row =await cursor .fetchone ()
                        if row :
                            self .channel_snapshots [guild .id ]=json .loads (row [0 ])
                        else :
                            return False 

            snapshot =self .channel_snapshots [guild .id ]


            recovery_channel =None 
            try :
                recovery_channel =await guild .create_text_channel (
                "🚨recovery-status",
                reason ="Emergency recovery channel"
                )
                await recovery_channel .send ("🚨 **NUKE DETECTED - FULL RECOVERY INITIATED**\n"
                "📊 Restoring server structure from backup...")
            except :
                pass 


            category_map ={}
            for cat_data in snapshot ['categories']:
                try :
                    overwrites ={}
                    for target_id ,perm_data in cat_data ['overwrites'].items ():
                        target =guild .get_role (int (target_id ))or guild .get_member (int (target_id ))
                        if target :
                            overwrites [target ]=discord .PermissionOverwrite .from_pair (
                            discord .Permissions (perm_data ['allow']),
                            discord .Permissions (perm_data ['deny'])
                            )

                    new_category =await guild .create_category (
                    name =cat_data ['name'],
                    overwrites =overwrites ,
                    reason ="Emergency recovery - Category restoration"
                    )
                    category_map [cat_data ['id']]=new_category 
                    await asyncio .sleep (0.3 )

                    if recovery_channel :
                        await recovery_channel .send (f"<:icon_tick:1372375089668161597> Restored category: **{cat_data['name']}**")

                except Exception as e :
                    if recovery_channel :
                        await recovery_channel .send (f"<:icon_cross:1372375094336425986> Failed to restore category {cat_data['name']}: {e}")


            for ch_data in snapshot ['text_channels']:
                try :
                    category =category_map .get (ch_data ['category_id'])
                    overwrites ={}
                    for target_id ,perm_data in ch_data ['overwrites'].items ():
                        target =guild .get_role (int (target_id ))or guild .get_member (int (target_id ))
                        if target :
                            overwrites [target ]=discord .PermissionOverwrite .from_pair (
                            discord .Permissions (perm_data ['allow']),
                            discord .Permissions (perm_data ['deny'])
                            )

                    new_channel =await guild .create_text_channel (
                    name =ch_data ['name'],
                    category =category ,
                    topic =ch_data ['topic'],
                    slowmode_delay =ch_data ['slowmode_delay'],
                    nsfw =ch_data ['nsfw'],
                    overwrites =overwrites ,
                    reason ="Emergency recovery - Channel restoration"
                    )
                    await asyncio .sleep (0.3 )

                    if recovery_channel :
                        await recovery_channel .send (f"📝 Restored text channel: **#{ch_data['name']}**")

                except Exception as e :
                    if recovery_channel :
                        await recovery_channel .send (f"<:icon_cross:1372375094336425986> Failed to restore text channel {ch_data['name']}: {e}")


            for ch_data in snapshot ['voice_channels']:
                try :
                    category =category_map .get (ch_data ['category_id'])
                    overwrites ={}
                    for target_id ,perm_data in ch_data ['overwrites'].items ():
                        target =guild .get_role (int (target_id ))or guild .get_member (int (target_id ))
                        if target :
                            overwrites [target ]=discord .PermissionOverwrite .from_pair (
                            discord .Permissions (perm_data ['allow']),
                            discord .Permissions (perm_data ['deny'])
                            )

                    new_channel =await guild .create_voice_channel (
                    name =ch_data ['name'],
                    category =category ,
                    bitrate =min (ch_data ['bitrate'],384000 ),
                    user_limit =ch_data ['user_limit'],
                    overwrites =overwrites ,
                    reason ="Emergency recovery - Voice channel restoration"
                    )
                    await asyncio .sleep (0.3 )

                    if recovery_channel :
                        await recovery_channel .send (f"🔊 Restored voice channel: **{ch_data['name']}**")

                except Exception as e :
                    if recovery_channel :
                        await recovery_channel .send (f"<:icon_cross:1372375094336425986> Failed to restore voice channel {ch_data['name']}: {e}")

            if recovery_channel :
                await recovery_channel .send ("<:icon_tick:1372375089668161597> **FULL SERVER RECOVERY COMPLETED**\n"
                "🔒 Server has been secured against further attacks.\n"
                "<:icon_danger:1372375135604047902> All suspicious bots have been banned.")


            if guild .id in self .emergency_lockdown :
                del self .emergency_lockdown [guild .id ]

            return True 

        except Exception as e :
            print (f"Full recovery error: {e}")
            return False 

    async def fetch_audit_logs (self ,guild ,action ,target_id ):
        if not guild .me .guild_permissions .view_audit_log :
            return None 
        try :
            async for entry in guild .audit_logs (action =action ,limit =1 ):
                if entry .target .id ==target_id :
                    now =datetime .datetime .now (pytz .utc )
                    if (now -entry .created_at ).total_seconds ()<=60 :
                        return entry 
        except Exception as e :
            pass 
        return None 

    @commands .Cog .listener ()
    async def on_ready (self ):
        """Periodically take snapshots of all guilds"""
        await asyncio .sleep (10 )
        while True :
            try :
                for guild in self .bot .guilds :
                    async with aiosqlite .connect ('db/anti.db')as db :
                        async with db .execute ("SELECT status FROM antinuke WHERE guild_id = ?",(guild .id ,))as cursor :
                            antinuke_status =await cursor .fetchone ()
                        if antinuke_status and antinuke_status [0 ]:
                            await self .take_channel_snapshot (guild )
                            await asyncio .sleep (2 )

                await asyncio .sleep (300 )
            except Exception as e :
                print (f"Snapshot error: {e}")
                await asyncio .sleep (60 )

    @commands .Cog .listener ()
    async def on_guild_channel_delete (self ,channel ):
        guild =channel .guild 


        async with aiosqlite .connect ('db/anti.db')as db :
            async with db .execute ("SELECT status FROM antinuke WHERE guild_id = ?",(guild .id ,))as cursor :
                antinuke_status =await cursor .fetchone ()
            if not antinuke_status or not antinuke_status [0 ]:
                return 


            is_nuke_attempt =await self .detect_nuke_attempt (guild .id )

            logs =await self .fetch_audit_logs (guild ,discord .AuditLogAction .channel_delete ,channel .id )
            executor =None 
            if logs :
                executor =logs .user 


                if executor .id in {guild .owner_id ,self .bot .user .id }:
                    return 


                async with db .execute ("SELECT owner_id FROM extraowners WHERE guild_id = ? AND owner_id = ?",(guild .id ,executor .id ))as cursor :
                    if await cursor .fetchone ():
                        return 


                async with db .execute ("SELECT chdl FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",(guild .id ,executor .id ))as cursor :
                    whitelist_status =await cursor .fetchone ()
                if whitelist_status and whitelist_status [0 ]:
                    return 


            if is_nuke_attempt or (executor and executor .bot ):

                if executor :
                    await self .emergency_lockdown_guild (guild ,executor )


                remaining_channels =len (guild .channels )
                if remaining_channels <=2 :
                    coordinator =self .bot .get_cog ('AntiNukeCoordinator')
                    if coordinator and not coordinator .is_recovery_in_progress (guild .id ):
                        await coordinator .initiate_emergency_protocol (guild )
                    await self .full_server_recovery (guild )
                    return 


                if executor :
                    try :
                        await guild .ban (executor ,reason ="NUKE ATTEMPT DETECTED - Immediate Emergency Ban")
                    except :
                        pass 


            await self .recreate_channel_and_ban (channel ,executor )

    async def recreate_channel_and_ban (self ,channel ,executor ,retries =3 ):
        """Enhanced channel recreation with better error handling"""
        guild =channel .guild 


        new_channel =None 
        attempt =0 
        while attempt <retries and not new_channel :
            try :

                overwrites ={}
                for target ,overwrite in channel .overwrites .items ():
                    try :
                        overwrites [target ]=overwrite 
                    except :
                        continue 

                if isinstance (channel ,discord .TextChannel ):
                    new_channel =await guild .create_text_channel (
                    name =channel .name ,
                    topic =channel .topic ,
                    slowmode_delay =channel .slowmode_delay ,
                    nsfw =channel .nsfw ,
                    category =channel .category ,
                    overwrites =overwrites ,
                    reason ="Anti-Nuke: Channel restored after unauthorized deletion"
                    )
                elif isinstance (channel ,discord .VoiceChannel ):
                    new_channel =await guild .create_voice_channel (
                    name =channel .name ,
                    bitrate =min (channel .bitrate ,384000 ),
                    user_limit =channel .user_limit ,
                    category =channel .category ,
                    overwrites =overwrites ,
                    reason ="Anti-Nuke: Voice channel restored after unauthorized deletion"
                    )

                if new_channel :
                    try :
                        await new_channel .edit (position =channel .position )
                    except :
                        pass 
                break 

            except discord .HTTPException as e :
                if e .status ==429 :
                    retry_after =e .response .headers .get ('Retry-After','1')
                    await asyncio .sleep (float (retry_after ))
                attempt +=1 
            except Exception as e :
                attempt +=1 
                await asyncio .sleep (1 )


        if executor and not executor .bot :
            ban_attempts =0 
            while ban_attempts <3 :
                try :
                    await guild .ban (executor ,reason ="Unauthorized Channel Deletion - Anti-Nuke Protection")
                    break 
                except discord .HTTPException as e :
                    if e .status ==429 :
                        retry_after =e .response .headers .get ('Retry-After','2')
                        await asyncio .sleep (float (retry_after ))
                    ban_attempts +=1 
                except :
                    break 

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
