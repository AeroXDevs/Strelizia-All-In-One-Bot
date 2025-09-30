from __future__ import annotations 
import discord 
import asyncio 
import logging 
import aiosqlite 
import json 
from discord .ext import commands 
from core import Cog ,Strelizia 

class BoosterListener (Cog ):
    def __init__ (self ,bot :Strelizia ):
        self .bot =bot 
        self .color =0x000000 
        self .db_path ="db/boost.db"

    async def get_boost_config (self ,guild_id :int )->dict :
        """Get boost configuration for a guild"""
        async with aiosqlite .connect (self .db_path )as db :
            async with db .execute ("SELECT config FROM boost_config WHERE guild_id = ?",(guild_id ,))as cursor :
                row =await cursor .fetchone ()
                if row :
                    return json .loads (row [0 ])


                default_config ={
                "boost":{
                "channel":[],
                "message":"{user.mention} just boosted {server.name}!",
                "embed":True ,
                "ping":False ,
                "image":"",
                "thumbnail":"",
                "autodel":0 
                },
                "boost_roles":{
                "roles":[]
                }
                }
                return default_config 

    def format_boost_message (self ,message :str ,user :discord .Member ,guild :discord .Guild )->str :
        """Format boost message with variable replacements"""
        replacements ={

        "{server.name}":guild .name ,
        "{server.id}":str (guild .id ),
        "{server.owner}":str (guild .owner ),
        "{server.icon}":guild .icon .url if guild .icon else "",
        "{server.boost_count}":str (guild .premium_subscription_count ),
        "{server.boost_level}":f"Level {guild.premium_tier}",
        "{server.member_count}":str (guild .member_count ),


        "{user.name}":user .display_name ,
        "{user.mention}":user .mention ,
        "{user.tag}":str (user ),
        "{user.id}":str (user .id ),
        "{user.avatar}":user .display_avatar .url ,
        "{user.created_at}":f"<t:{int(user.created_at.timestamp())}:F>",
        "{user.joined_at}":f"<t:{int(user.joined_at.timestamp())}:F>"if user .joined_at else "Unknown",
        "{user.top_role}":user .top_role .name if user .top_role else "None",
        "{user.is_booster}":str (bool (user .premium_since )),
        "{user.is_mobile}":str (user .is_on_mobile ()),
        "{user.boosted_at}":f"<t:{int(user.premium_since.timestamp())}:F>"if user .premium_since else "Unknown"
        }

        for old ,new in replacements .items ():
            message =message .replace (old ,new )

        return message 

    @commands .Cog .listener ()
    async def on_member_update (self ,before :discord .Member ,after :discord .Member ):
        """Detect when a member boosts the server"""
        try :

            if not before .premium_since and after .premium_since :

                config =await self .get_boost_config (after .guild .id )
                boost_config =config ["boost"]
                channels =boost_config ["channel"]


                boost_roles =config ["boost_roles"]["roles"]
                if boost_roles :
                    roles_to_add =[]
                    for role_id in boost_roles :
                        role =after .guild .get_role (int (role_id ))
                        if role and role not in after .roles :
                            roles_to_add .append (role )

                    if roles_to_add :
                        try :
                            await after .add_roles (*roles_to_add ,reason ="Server booster reward")
                        except discord .Forbidden :
                            pass 
                        except Exception :
                            pass 


                if channels :
                    formatted_message =self .format_boost_message (boost_config ["message"],after ,after .guild )

                    for channel_id in channels :
                        channel =self .bot .get_channel (int (channel_id ))
                        if not channel or not hasattr (channel ,'send'):
                            continue 

                        try :
                            if boost_config ["embed"]:
                                embed =discord .Embed (description =formatted_message ,color =self .color )
                                embed .set_author (name =after .display_name ,icon_url =after .display_avatar .url )
                                embed .timestamp =discord .utils .utcnow ()

                                if boost_config ["image"]:
                                    embed .set_image (url =boost_config ["image"])

                                if boost_config ["thumbnail"]:
                                    embed .set_thumbnail (url =boost_config ["thumbnail"])

                                if after .guild .icon :
                                    embed .set_footer (text =after .guild .name ,icon_url =after .guild .icon .url )

                                ping_content =after .mention if boost_config ["ping"]else ""
                                message =await channel .send (ping_content ,embed =embed )
                            else :
                                message =await channel .send (formatted_message )


                            if boost_config ["autodel"]>0 :
                                await asyncio .sleep (boost_config ["autodel"])
                                try :
                                    await message .delete ()
                                except Exception :
                                    pass 

                        except discord .Forbidden :
                            continue 
                        except Exception :
                            continue 

        except Exception :
            pass 

async def setup (bot ):
    await bot .add_cog (BoosterListener (bot ))