
import json 
import datetime 
import discord 
import aiosqlite 
from typing import Dict ,Any ,Optional ,Tuple 

async def check_user_level (guild_id :int ,user_id :int )->int :
    """Check user's level from leveling database"""
    try :
        async with aiosqlite .connect ('db/leveling.db')as db :
            cursor =await db .cursor ()
            await cursor .execute ("SELECT level FROM leveling WHERE guild_id = ? AND user_id = ?",(guild_id ,user_id ))
            result =await cursor .fetchone ()
            return result [0 ]if result else 0 
    except Exception :
        return 0 

async def check_user_messages (guild_id :int ,user_id :int ,days :int =None )->int :
    """Check user's message count from tracking database"""
    try :
        async with aiosqlite .connect ('db/tracking.db')as db :
            cursor =await db .cursor ()

            if days :
                since_date =datetime .datetime .now ()-datetime .timedelta (days =days )
                await cursor .execute (
                "SELECT COUNT(*) FROM user_activity WHERE guild_id = ? AND user_id = ? AND timestamp >= ?",
                (guild_id ,user_id ,since_date .timestamp ())
                )
            else :
                await cursor .execute (
                "SELECT COUNT(*) FROM user_activity WHERE guild_id = ? AND user_id = ?",
                (guild_id ,user_id )
                )

            result =await cursor .fetchone ()
            return result [0 ]if result else 0 
    except Exception :
        return 0 

def format_giveaway_config (config :Dict [str ,Any ])->str :
    """Format giveaway configuration for display"""
    if not config :
        return "No special requirements"

    requirements =[]

    if config .get ('required_role'):
        requirements .append (f"Required Role: <@&{config['required_role']}>")

    if config .get ('required_level'):
        requirements .append (f"Required Level: {config['required_level']}+")

    message_reqs =[]
    if config .get ('required_daily_messages'):
        message_reqs .append (f"Daily: {config['required_daily_messages']}")
    if config .get ('required_weekly_messages'):
        message_reqs .append (f"Weekly: {config['required_weekly_messages']}")
    if config .get ('required_monthly_messages'):
        message_reqs .append (f"Monthly: {config['required_monthly_messages']}")
    if config .get ('required_total_messages'):
        message_reqs .append (f"Total: {config['required_total_messages']}")

    if message_reqs :
        requirements .append (f"Messages: {', '.join(message_reqs)}")

    if config .get ('requirement_bypass_role'):
        requirements .append (f"Bypass Role: <@&{config['requirement_bypass_role']}>")

    return "\n".join (requirements )if requirements else "No special requirements"

def validate_giveaway_duration (duration_str :str )->Tuple [bool ,int ,str ]:
    """Validate and convert duration string"""
    time_units ={"s":1 ,"m":60 ,"h":3600 ,"d":86400 ,"w":604800 }

    if not duration_str or len (duration_str )<2 :
        return False ,0 ,"Duration must be at least 2 characters (e.g., '1h')"

    unit =duration_str [-1 ].lower ()
    if unit not in time_units :
        return False ,0 ,"Invalid time unit. Use: s, m, h, d, w"

    try :
        value =int (duration_str [:-1 ])
        if value <=0 :
            return False ,0 ,"Duration value must be positive"
    except ValueError :
        return False ,0 ,"Invalid duration value"

    seconds =value *time_units [unit ]


    if seconds <60 :
        return False ,0 ,"Duration must be at least 1 minute"

    if seconds >2678400 :
        return False ,0 ,"Duration cannot exceed 31 days"

    return True ,seconds ,"Valid duration"

def create_giveaway_embed (prize :str ,winners :int ,ends_at :float ,host :discord .Member ,
config :Dict [str ,Any ]=None ,ended :bool =False )->discord .Embed :
    """Create a standardized giveaway embed"""
    config =config or {}

    if ended :
        title =f"🎉 {prize} (ENDED)"
        color =int (config .get ('end_color','0x000000').replace ('#',''),16 )if config .get ('end_color')else 0x000000 
        description =f"**Ended:** <t:{int(ends_at)}:R>\n**Host:** {host.mention}"
    else :
        title =f"🎉 {prize}"
        color =int (config .get ('color','0x000000').replace ('#',''),16 )if config .get ('color')else 0x000000 
        description =f"**Winners:** {winners}\n**Ends:** <t:{int(ends_at)}:R> (<t:{int(ends_at)}:f>)\n**Host:** {host.mention}\n\nReact with 🎉 to enter!"

    embed =discord .Embed (title =title ,description =description ,color =color )

    if config .get ('image'):
        embed .set_image (url =config ['image'])

    if config .get ('thumbnail'):
        embed .set_thumbnail (url =config ['thumbnail'])


    req_text =format_giveaway_config (config )
    if req_text !="No special requirements":
        embed .add_field (name ="📋 Requirements",value =req_text ,inline =False )

    embed .set_footer (text ="Ended at"if ended else "Ends at",icon_url =host .avatar .url if host .avatar else None )
    embed .timestamp =datetime .datetime .utcfromtimestamp (ends_at )

    return embed 

async def get_giveaway_templates (guild_id :int )->list :
    """Get all templates for a guild"""
    try :
        async with aiosqlite .connect ('db/giveaways.db')as db :
            cursor =await db .cursor ()
            await cursor .execute ("SELECT name, data FROM GiveawayTemplates WHERE guild_id = ?",(guild_id ,))
            results =await cursor .fetchall ()

            templates =[]
            for name ,data in results :
                templates .append ({
                'name':name ,
                'data':json .loads (data )
                })

            return templates 
    except Exception :
        return []

async def save_giveaway_template (guild_id :int ,name :str ,data :Dict [str ,Any ])->bool :
    """Save a giveaway template"""
    try :
        async with aiosqlite .connect ('db/giveaways.db')as db :
            cursor =await db .cursor ()
            await cursor .execute (
            "INSERT OR REPLACE INTO GiveawayTemplates (guild_id, name, data) VALUES (?, ?, ?)",
            (guild_id ,name ,json .dumps (data ))
            )
            await db .commit ()
            return True 
    except Exception :
        return False 

async def delete_giveaway_template (guild_id :int ,name :str )->bool :
    """Delete a giveaway template"""
    try :
        async with aiosqlite .connect ('db/giveaways.db')as db :
            cursor =await db .cursor ()
            await cursor .execute ("DELETE FROM GiveawayTemplates WHERE guild_id = ? AND name = ?",(guild_id ,name ))
            deleted =cursor .rowcount >0 
            await db .commit ()
            return deleted 
    except Exception :
        return False 

def parse_hex_color (color_input :str )->int :
    """Parse color from various input formats"""
    if not color_input :
        return 0x000000 

    color_input =color_input .lower ().strip ()


    color_map ={
    'red':0xff0000 ,'green':0x00ff00 ,'blue':0x0000ff ,
    'yellow':0xffff00 ,'purple':0x800080 ,'orange':0xffa500 ,
    'pink':0xffc0cb ,'cyan':0x00ffff ,'white':0xffffff ,
    'black':0x000000 ,'gold':0xffd700 ,'silver':0xc0c0c0 ,
    'gray':0x808080 ,'grey':0x808080 ,'brown':0x964b00 ,
    'lime':0x32cd32 ,'navy':0x000080 ,'teal':0x008080 
    }

    if color_input in color_map :
        return color_map [color_input ]


    if color_input .startswith ('#'):
        color_input =color_input [1 :]


    try :
        return int (color_input ,16 )
    except ValueError :
        return 0x000000 

def format_duration (seconds :int )->str :
    """Format duration in seconds to human readable string"""
    units =[
    ('week',604800 ),
    ('day',86400 ),
    ('hour',3600 ),
    ('minute',60 ),
    ('second',1 )
    ]

    parts =[]
    for unit_name ,unit_seconds in units :
        if seconds >=unit_seconds :
            unit_count =seconds //unit_seconds 
            seconds %=unit_seconds 
            unit_text =unit_name if unit_count ==1 else f"{unit_name}s"
            parts .append (f"{unit_count} {unit_text}")

    if not parts :
        return "0 seconds"

    if len (parts )==1 :
        return parts [0 ]
    elif len (parts )==2 :
        return f"{parts[0]} and {parts[1]}"
    else :
        return f"{', '.join(parts[:-1])}, and {parts[-1]}"

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
