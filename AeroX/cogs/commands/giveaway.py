from discord .ext import commands ,tasks 
import datetime ,pytz ,time as t 
from discord .ui import Button ,Select ,View ,Modal ,TextInput 
import aiosqlite ,random ,typing 
import sqlite3 
import asyncio 
import discord ,logging 
from discord .utils import get 
from discord import app_commands 
from utils .Tools import *
import os 
import aiohttp 
import json 
from PIL import Image ,ImageDraw ,ImageFont 
import random 
import string 
import io 

db_folder ='db'
db_file ='giveaways.db'
db_path =os .path .join (db_folder ,db_file )


os .makedirs (db_folder ,exist_ok =True )


LEVELING_DB_PATH ='leveling.db'

async def init_database_async ():
    """Initialize database tables asynchronously"""
    try :
        async with aiosqlite .connect (db_path )as connection :
            cursor =await connection .cursor ()


            await cursor .execute ("PRAGMA table_info(Giveaway)")
            columns =[column [1 ]for column in await cursor .fetchall ()]

            if not columns :

                await cursor .execute ('''CREATE TABLE Giveaway (
                                    guild_id INTEGER,
                                    host_id INTEGER,
                                    start_time TIMESTAMP,
                                    ends_at TIMESTAMP,
                                    prize TEXT,
                                    winners INTEGER,
                                    message_id INTEGER,
                                    channel_id INTEGER,
                                    config TEXT,
                                    is_paused INTEGER DEFAULT 0,
                                    is_processing INTEGER DEFAULT 0,
                                    PRIMARY KEY (guild_id, message_id)
                                )''')
            else :

                if 'config'not in columns :
                    await cursor .execute ('ALTER TABLE Giveaway ADD COLUMN config TEXT')
                if 'is_paused'not in columns :
                    await cursor .execute ('ALTER TABLE Giveaway ADD COLUMN is_paused INTEGER DEFAULT 0')
                if 'is_processing'not in columns :
                    await cursor .execute ('ALTER TABLE Giveaway ADD COLUMN is_processing INTEGER DEFAULT 0')


            await cursor .execute ('''CREATE TABLE IF NOT EXISTS GiveawayTemplates (
                                guild_id INTEGER,
                                name TEXT,
                                data TEXT,
                                PRIMARY KEY (guild_id, name)
                            )''')


            await cursor .execute ('''CREATE TABLE IF NOT EXISTS GiveawayBlacklist (
                                guild_id INTEGER,
                                user_id INTEGER,
                                PRIMARY KEY (guild_id, user_id)
                            )''')


            await cursor .execute ('''CREATE TABLE IF NOT EXISTS GiveawayParticipants (
                                guild_id INTEGER,
                                message_id INTEGER,
                                user_id INTEGER,
                                entries INTEGER DEFAULT 1,
                                PRIMARY KEY (guild_id, message_id, user_id)
                            )''')


            await cursor .execute ("PRAGMA table_info(GiveawayParticipants)")
            participant_columns =[column [1 ]for column in await cursor .fetchall ()]

            if 'entries'not in participant_columns :
                await cursor .execute ('ALTER TABLE GiveawayParticipants ADD COLUMN entries INTEGER DEFAULT 1')

                await cursor .execute ('UPDATE GiveawayParticipants SET entries = 1 WHERE entries IS NULL')

            await connection .commit ()
            return True 
    except Exception as e :
        return False 

def convert_time (time ):
    pos =["s","m","h","d","w"]
    time_dict ={"s":1 ,"m":60 ,"h":3600 ,"d":86400 ,"w":604800 }
    unit =time [-1 ].lower ()
    if unit not in pos :
        return -1 
    try :
        val =int (time [:-1 ])
    except ValueError :
        return -2 
    return val *time_dict [unit ]

def parse_color (color_str ):
    """Parse color from hex string or color name"""
    if not color_str :
        return 0x000000 

    color_str =color_str .lower ().strip ()


    colors ={
    'red':0xff0000 ,'green':0x00ff00 ,'blue':0x0000ff ,
    'yellow':0xffff00 ,'purple':0x800080 ,'orange':0xffa500 ,
    'pink':0xffc0cb ,'cyan':0x00ffff ,'white':0xffffff ,
    'black':0x000000 ,'gold':0xffd700 ,'silver':0xc0c0c0 
    }

    if color_str in colors :
        return colors [color_str ]


    if color_str .startswith ('#'):
        color_str =color_str [1 :]

    try :
        return int (color_str ,16 )
    except ValueError :
        return 0x000000 

class GiveawayConfigModal (Modal ):
    def __init__ (self ,config_type ,giveaway_data ,callback ):
        super ().__init__ (title =f"Configure {config_type}")
        self .config_type =config_type 
        self .giveaway_data =giveaway_data 
        self .callback =callback 


        text_input =None 

        if config_type =="Prize":
            text_input =TextInput (
            label ="Prize",
            placeholder ="Enter the prize description",
            default =giveaway_data .get ('prize',''),
            max_length =256 
            )
        elif config_type =="Duration":
            text_input =TextInput (
            label ="Duration",
            placeholder ="e.g., 1h, 2d, 3w",
            default =giveaway_data .get ('duration',''),
            max_length =10 
            )
        elif config_type =="Winners":
            text_input =TextInput (
            label ="Winners",
            placeholder ="Number of winners (1-15)",
            default =str (giveaway_data .get ('winners',1 )),
            max_length =2 
            )
        elif config_type =="Channel":
            text_input =TextInput (
            label ="Channel ID",
            placeholder ="Channel to host in (leave empty for current)",
            default =str (giveaway_data .get ('channel_id','')),
            required =False ,
            max_length =20 
            )
        elif config_type =="Giveaway Host":
            text_input =TextInput (
            label ="Host User ID",
            placeholder ="User ID of the giveaway host",
            default =giveaway_data .get ('host_override',''),
            required =False ,
            max_length =20 
            )
        elif config_type =="Image":
            text_input =TextInput (
            label ="Image URL",
            placeholder ="Giveaway image URL",
            default =giveaway_data .get ('image',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Thumbnail":
            text_input =TextInput (
            label ="Thumbnail URL",
            placeholder ="Giveaway thumbnail URL",
            default =giveaway_data .get ('thumbnail',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Required role to join":
            text_input =TextInput (
            label ="Required Role ID",
            placeholder ="Role ID required to enter",
            default =giveaway_data .get ('required_role',''),
            required =False ,
            max_length =20 
            )
        elif config_type =="Required level to join":
            text_input =TextInput (
            label ="Required Level",
            placeholder ="Minimum level required",
            default =str (giveaway_data .get ('required_level','')),
            required =False ,
            max_length =3 
            )
        elif config_type =="Giveaway winner dm message":
            text_input =TextInput (
            label ="Winners DM Message",
            placeholder ="DM message for winners",
            default =giveaway_data .get ('giveaway_winners_dm_message',''),
            required =False ,
            max_length =512 ,
            style =discord .TextStyle .paragraph 
            )
        elif config_type =="Required Total messages":
            text_input =TextInput (
            label ="Total Messages",
            placeholder ="Required total messages",
            default =str (giveaway_data .get ('required_total_messages','')),
            required =False ,
            max_length =6 
            )
        elif config_type =="Giveaway Create Message":
            text_input =TextInput (
            label ="Create Message",
            placeholder ="Custom announcement message",
            default =giveaway_data .get ('giveaway_create_message',''),
            required =False ,
            max_length =256 ,
            style =discord .TextStyle .paragraph 
            )
        elif config_type =="Color":
            text_input =TextInput (
            label ="Embed Color",
            placeholder ="Hex color or color name (e.g., #ff0000, red)",
            default =giveaway_data .get ('color',''),
            required =False ,
            max_length =10 
            )
        elif config_type =="End color":
            text_input =TextInput (
            label ="End Color",
            placeholder ="Color when giveaway ends",
            default =giveaway_data .get ('end_color',''),
            required =False ,
            max_length =10 
            )
        elif config_type =="Entry Confirmation message":
            text_input =TextInput (
            label ="Entry Confirmation Message",
            placeholder ="Message when user enters giveaway",
            default =giveaway_data .get ('entry_confirmation_message',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Entry Deny message":
            text_input =TextInput (
            label ="Entry Deny Message",
            placeholder ="Message when entry is denied",
            default =giveaway_data .get ('entry_deny_message',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Entry Remove Message":
            text_input =TextInput (
            label ="Entry Remove Message",
            placeholder ="Message when user leaves giveaway",
            default =giveaway_data .get ('giveaway_leave_message',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Title":
            text_input =TextInput (
            label ="Giveaway Title",
            placeholder ="Custom title for the giveaway",
            default =giveaway_data .get ('title',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Author":
            text_input =TextInput (
            label ="Giveaway Author",
            placeholder ="Custom author name",
            default =giveaway_data .get ('author',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Footer":
            text_input =TextInput (
            label ="Giveaway Footer",
            placeholder ="Custom footer text",
            default =giveaway_data .get ('footer',''),
            required =False ,
            max_length =256 
            )
        elif config_type =="Use Template":
            text_input =TextInput (
            label ="Template Name",
            placeholder ="Enter template name to use",
            default =giveaway_data .get ('use_template',''),
            max_length =32 
            )
        elif config_type =="Template Name":
            text_input =TextInput (
            label ="Template Name",
            placeholder ="Name for this template",
            default =giveaway_data .get ('template_name',''),
            max_length =32 
            )


        if text_input :
            self .add_item (text_input )

    async def on_submit (self ,interaction ):
        try :
            await interaction .response .defer (ephemeral =True )
        except discord .InteractionResponded :
            pass 
        except Exception as e :
            return 

        value =self .children [0 ].value if self .children else ""


        config_mapping ={
        "Prize":"prize",
        "Duration":"duration",
        "Winners":"winners",
        "Channel":"channel_id",
        "Required Role":"required_role",
        "Required Level":"required_level",
        "Bypass Role":"requirement_bypass_role",
        "Extra Entries Role":"extra_entries_role",
        "Extra Entries Count":"extra_entries_count",
        "Create Message":"giveaway_create_message",
        "Winners Message":"giveaway_winners_message",
        "Leave Message":"giveaway_leave_message",
        "Embed Color":"color",
        "End Color":"end_color",
        "Daily Messages":"required_daily_messages",
        "Weekly Messages":"required_weekly_messages",
        "Monthly Messages":"required_monthly_messages",
        "Total Messages":"required_total_messages",
        "Winners Role":"giveaway_winners_role",
        "Winners DM Message":"giveaway_winners_dm_message",
        "Image":"image",
        "Thumbnail":"thumbnail",
        "Host Override":"host_override",
        "Custom Footer":"custom_footer",
        "Ping Role":"ping_role",
        "Reaction Emoji":"reaction_emoji",
        "Max Entries":"max_entries",
        "Min Account Age":"min_account_age",
        "Min Server Join":"min_server_join",
        "Blacklisted Roles":"blacklisted_roles",
        "Required Invites":"required_invites",
        "Donor Role":"donor_role",
        "Donor Multiplier":"donor_multiplier",
        "Server Boost Req":"require_boost",
        "Boost Multiplier":"boost_multiplier",
        "Auto Delete Time":"auto_delete_hours",
        "Winner Contact":"winner_contact",
        "Prize Delivery":"prize_delivery",
        "Giveaway Type":"giveaway_type",
        "Entry Cooldown":"entry_cooldown",
        "Multiple Accounts":"allow_multiple_accounts",
        "IP Limit":"ip_limit",
        "VPN Detection":"block_vpn",
        "Webhook URL":"webhook_url",
        "API Integration":"api_integration",
        "Custom Fields":"custom_fields",
        "Notification Settings":"notification_settings",
        "Backup Settings":"backup_settings",
        "Analytics":"analytics",
        "Advanced Options":"advanced_options"
        }


        if self .config_type =="Title"and value :
            self .giveaway_data ['title']=value 
        elif self .config_type =="Author"and value :
            self .giveaway_data ['author']=value 
        elif self .config_type =="Footer"and value :
            self .giveaway_data ['footer']=value 
        elif self .config_type =="Template Name"and value :
            self .giveaway_data ['template_name']=value 
        elif self .config_type =="Use Template"and value :
            self .giveaway_data ['use_template']=value 
        elif self .config_type in config_mapping and value :
            data_key =config_mapping [self .config_type ]


            if self .config_type in ["Winners","Required Level","Extra Entries Count","Daily Messages",
            "Weekly Messages","Monthly Messages","Total Messages","Max Entries",
            "Min Account Age","Min Server Join","Required Invites","Donor Multiplier",
            "Boost Multiplier","Auto Delete Time","Entry Cooldown"]:
                try :
                    self .giveaway_data [data_key ]=int (value )
                except ValueError :
                    pass 
            elif self .config_type =="Channel":
                try :
                    self .giveaway_data [data_key ]=int (value )
                except ValueError :
                    pass 
            else :
                self .giveaway_data [data_key ]=value 

        await self .callback (interaction ,self .giveaway_data )

class GiveawayPreviewGenerator :
    """Helper class to generate giveaway previews similar to welcomer"""

    @staticmethod 
    def create_preview_embed (giveaway_data ,author ,guild ):
        """Create a preview embed for the giveaway"""

        prize =giveaway_data .get ('prize','Example Prize')
        winners =giveaway_data .get ('winners',1 )
        duration =giveaway_data .get ('duration','1h')


        preview_time =datetime .datetime .now ().timestamp ()+3600 


        color =parse_color (giveaway_data .get ('color','#000000'))


        title =giveaway_data .get ('title',f"🎉 {prize}")

        description_parts =[
        f"**Winners:** {winners}",
        f"**Ends:** <t:{round(preview_time)}:R> (<t:{round(preview_time)}:f>)",
        f"**Host:** {author.mention}",
        "",
        "Click **Join** to enter!"
        ]

        embed =discord .Embed (
        title =title ,
        description ="\n".join (description_parts ),
        color =color 
        )


        if giveaway_data .get ('author'):
            embed .set_author (name =giveaway_data ['author'])


        if giveaway_data .get ('image'):
            embed .set_image (url =giveaway_data ['image'])
        if giveaway_data .get ('thumbnail'):
            embed .set_thumbnail (url =giveaway_data ['thumbnail'])


        requirements =[]


        required_roles =giveaway_data .get ('required_roles',[])
        if isinstance (required_roles ,str ):
            try :
                required_roles =[int (required_roles )]
            except :
                required_roles =[]
        elif not isinstance (required_roles ,list ):
            required_roles =[]


        if giveaway_data .get ('required_role'):
            try :
                required_roles .append (int (giveaway_data ['required_role']))
            except :
                pass 

        if required_roles :
            role_mentions =[]
            for role_id in required_roles :
                try :
                    role =guild .get_role (int (role_id ))
                    if role :
                        role_mentions .append (role .mention )
                    else :
                        role_mentions .append (f"<@&{role_id}>")
                except :
                    role_mentions .append (f"<@&{role_id}>")

            if role_mentions :
                role_type =giveaway_data .get ('required_role_type','any')
                if role_type =='all':
                    requirements .append (f"🔐 **Required Roles (ALL):** {', '.join(role_mentions)}")
                else :
                    requirements .append (f"🔐 **Required Role:** {', '.join(role_mentions)}")

        if giveaway_data .get ('required_level'):
            requirements .append (f"📈 **Level:** {giveaway_data['required_level']}+")

        if giveaway_data .get ('required_total_messages'):
            requirements .append (f"💬 **Total Messages:** {giveaway_data['required_total_messages']}+")


        bypass_role_id =giveaway_data .get ('requirement_bypass_role')or giveaway_data .get ('bypass_role')or giveaway_data .get ('requirements_bypass_role')
        if bypass_role_id :
            try :
                bypass_role =guild .get_role (int (bypass_role_id ))
                if bypass_role :
                    requirements .append (f"⭐ **Bypass Role:** {bypass_role.mention}")
                else :
                    requirements .append (f"⭐ **Bypass Role:** <@&{bypass_role_id}>")
            except :
                requirements .append (f"⭐ **Bypass Role:** <@&{bypass_role_id}>")


        extra_role_id =giveaway_data .get ('extra_entries_role')
        extra_count =giveaway_data .get ('extra_entries_count',1 )
        if extra_role_id and extra_count >0 :
            try :
                extra_role =guild .get_role (int (extra_role_id ))
                if extra_role :
                    requirements .append (f"🎯 **Extra Entries:** {extra_role.mention} (+{extra_count} entries)")
                else :
                    requirements .append (f"🎯 **Extra Entries:** <@&{extra_role_id}> (+{extra_count} entries)")
            except :
                requirements .append (f"🎯 **Extra Entries:** <@&{extra_role_id}> (+{extra_count} entries)")

        if requirements :
            embed .add_field (name ="📋 Requirements",value ="\n".join (requirements ),inline =False )


        footer_text =giveaway_data .get ('footer',"Ends at")
        embed .set_footer (text =footer_text ,icon_url =author .display_avatar .url )
        embed .timestamp =datetime .datetime .utcfromtimestamp (preview_time )

        return embed 

class RemoveParticipantModal (Modal ):
    def __init__ (self ,callback ):
        super ().__init__ (title ="Remove Participant")
        self .callback =callback 

        self .add_item (TextInput (
        label ="User ID",
        placeholder ="Enter the user ID to remove",
        max_length =20 
        ))

    async def on_submit (self ,interaction ):
        await interaction .response .defer (ephemeral =True )
        user_id =self .children [0 ].value 

        try :
            user_id =int (user_id )
            await self .callback (interaction ,user_id )
        except ValueError :
            embed =discord .Embed (
            description ="Invalid user ID provided!",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )

class CaptchaVerificationModal (Modal ):
    def __init__ (self ,giveaway_cog ,message_id ,expected_code ):
        super ().__init__ (title ="CAPTCHA Verification")
        self .giveaway_cog =giveaway_cog 
        self .message_id =message_id 
        self .expected_code =expected_code 

        self .captcha_input =TextInput (
        label ="Enter the CAPTCHA code",
        placeholder ="Enter the 5-character code from the image",
        max_length =5 ,
        min_length =5 
        )
        self .add_item (self .captcha_input )

    async def on_submit (self ,interaction ):
        user_input =self .captcha_input .value .upper ()

        if user_input ==self .expected_code :

            await self .giveaway_cog .handle_giveaway_join_after_captcha (interaction ,self .message_id )
        else :
            embed =discord .Embed (
            title ="❌ CAPTCHA Failed",
            description ="The CAPTCHA code you entered is incorrect. Please try joining the giveaway again.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

class CaptchaView (View ):
    def __init__ (self ,modal ):
        super ().__init__ (timeout =300 )
        self .modal =modal 

    @discord .ui .button (label ="Enter CAPTCHA Code",style =discord .ButtonStyle .primary ,emoji ="🔒")
    async def enter_captcha (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .send_modal (self .modal )

class LeaveConfirmationView (View ):
    def __init__ (self ,giveaway_cog ,message_id ):
        super ().__init__ (timeout =60 )
        self .giveaway_cog =giveaway_cog 
        self .message_id =message_id 

    @discord .ui .button (label ="Yes, Leave Giveaway",style =discord .ButtonStyle .red ,emoji ="❌")
    async def confirm_leave (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .defer (ephemeral =True )


        await self .giveaway_cog .cursor .execute (
        "DELETE FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ? AND user_id = ?",
        (interaction .guild .id ,self .message_id ,interaction .user .id )
        )
        await self .giveaway_cog .connection .commit ()


        await self .giveaway_cog .update_participant_count (interaction .guild .id ,self .message_id )


        await self .giveaway_cog .cursor .execute ("SELECT config FROM Giveaway WHERE message_id = ? AND guild_id = ?",(self .message_id ,interaction .guild .id ))
        result =await self .giveaway_cog .cursor .fetchone ()
        config =json .loads (result [0 ])if result and result [0 ]else {}

        leave_msg =config .get ('giveaway_leave_message',"You have successfully left the giveaway!")

        embed =discord .Embed (
        title ="✅ Left Giveaway",
        description =leave_msg ,
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )

    @discord .ui .button (label ="Cancel",style =discord .ButtonStyle .secondary ,emoji ="✖️")
    async def cancel_leave (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        embed =discord .Embed (
        title ="🎉 Staying in Giveaway",
        description ="You're still participating in the giveaway! Good luck!",
        color =0x00ff00 
        )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

class GiveawayConfigurationView (View ):
    def __init__ (self ,giveaway_data ,callback ,page =1 ):
        super ().__init__ (timeout =300 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .page =page 


        if page ==1 :
            self .add_item (self .create_config_select_1 ())
        elif page ==2 :
            self .add_item (self .create_config_select_2 ())
        elif page ==3 :
            self .add_item (self .create_config_select_3 ())


        if page >1 :
            self .add_item (self .create_prev_button ())
        if page <3 :
            self .add_item (self .create_next_button ())

    def create_config_select_1 (self ):
        select =discord .ui .Select (
        placeholder ="Choose configuration option (Page 1/3)...",
        options =[
        discord .SelectOption (label ="1. Prize",description ="Set the giveaway prize"),
        discord .SelectOption (label ="2. Duration",description ="Set giveaway duration"),
        discord .SelectOption (label ="3. Winners",description ="Set number of winners"),
        discord .SelectOption (label ="4. Channel",description ="Set giveaway channel"),
        discord .SelectOption (label ="5. Required Role",description ="Set required role to enter"),
        discord .SelectOption (label ="6. Required Level",description ="Set minimum level required"),
        discord .SelectOption (label ="7. Bypass Role",description ="Role that bypasses requirements"),
        discord .SelectOption (label ="8. Extra Entries Role",description ="Role that gets extra entries"),
        discord .SelectOption (label ="9. Extra Entries Count",description ="Number of extra entries"),
        discord .SelectOption (label ="10. Create Message",description ="Custom announcement message"),
        discord .SelectOption (label ="11. Winners Message",description ="Custom winner announcement"),
        discord .SelectOption (label ="12. Leave Message",description ="Message when user leaves"),
        discord .SelectOption (label ="13. Embed Color",description ="Giveaway embed color"),
        discord .SelectOption (label ="14. End Color",description ="Color when giveaway ends"),
        discord .SelectOption (label ="15. Image",description ="Giveaway image URL"),
        discord .SelectOption (label ="16. Thumbnail",description ="Giveaway thumbnail URL"),
        discord .SelectOption (label ="17. Title",description ="Custom giveaway title"),
        discord .SelectOption (label ="18. Author",description ="Custom author name"),
        discord .SelectOption (label ="19. Footer",description ="Custom footer text"),
        discord .SelectOption (label ="20. Host Override",description ="Override giveaway host")
        ]
        )
        select .callback =self .config_select_callback 
        return select 

    def create_config_select_2 (self ):
        select =discord .ui .Select (
        placeholder ="Choose configuration option (Page 2/3)...",
        options =[
        discord .SelectOption (label ="21. Daily Messages",description ="Required daily messages"),
        discord .SelectOption (label ="22. Weekly Messages",description ="Required weekly messages"),
        discord .SelectOption (label ="23. Monthly Messages",description ="Required monthly messages"),
        discord .SelectOption (label ="24. Total Messages",description ="Required total messages"),
        discord .SelectOption (label ="25. Winners Role",description ="Role to give to winners"),
        discord .SelectOption (label ="26. Winners DM Message",description ="DM message for winners"),
        discord .SelectOption (label ="27. Entry Confirmation",description ="Message when user enters"),
        discord .SelectOption (label ="28. Entry Deny",description ="Message when entry denied"),
        discord .SelectOption (label ="29. Reaction Emoji",description ="Custom reaction emoji"),
        discord .SelectOption (label ="30. Max Entries",description ="Maximum entries per user"),
        discord .SelectOption (label ="31. Min Account Age",description ="Minimum account age (days)"),
        discord .SelectOption (label ="32. Min Server Join",description ="Min server join time (days)"),
        discord .SelectOption (label ="33. Blacklisted Roles",description ="Roles that cannot enter"),
        discord .SelectOption (label ="34. Required Invites",description ="Required invites count"),
        discord .SelectOption (label ="35. Donor Role",description ="Donor/premium role"),
        discord .SelectOption (label ="36. Donor Multiplier",description ="Entry multiplier for donors"),
        discord .SelectOption (label ="37. Server Boost Req",description ="Require server boost"),
        discord .SelectOption (label ="38. Boost Multiplier",description ="Entry multiplier for boosters"),
        discord .SelectOption (label ="39. Auto Delete Time",description ="Auto delete after end (hours)"),
        discord .SelectOption (label ="40. Winner Contact",description ="How to contact winners")
        ]
        )
        select .callback =self .config_select_callback 
        return select 

    def create_config_select_3 (self ):
        select =discord .ui .Select (
        placeholder ="Choose configuration option (Page 3/3)...",
        options =[
        discord .SelectOption (label ="41. Prize Delivery",description ="Prize delivery method"),
        discord .SelectOption (label ="42. Giveaway Type",description ="Type of giveaway"),
        discord .SelectOption (label ="43. Entry Cooldown",description ="Cooldown between entries"),
        discord .SelectOption (label ="44. Multiple Accounts",description ="Allow multiple accounts"),
        discord .SelectOption (label ="45. IP Limit",description ="Limit entries by IP"),
        discord .SelectOption (label ="46. VPN Detection",description ="Block VPN users"),
        discord .SelectOption (label ="47. Webhook URL",description ="Discord webhook for logs"),
        discord .SelectOption (label ="48. API Integration",description ="External API settings"),
        discord .SelectOption (label ="49. Custom Fields",description ="Additional custom fields"),
        discord .SelectOption (label ="50. Notification Settings",description ="Winner notification options"),
        discord .SelectOption (label ="51. Backup Settings",description ="Backup winner selection"),
        discord .SelectOption (label ="52. Analytics",description ="Track giveaway analytics"),
        discord .SelectOption (label ="53. Advanced Options",description ="Other advanced settings"),
        discord .SelectOption (label ="54. Template Name",description ="Save as template"),
        discord .SelectOption (label ="55. Use Template",description ="Load existing template")
        ]
        )
        select .callback =self .config_select_callback 
        return select 

    def create_prev_button (self ):
        button =discord .ui .Button (label ="◀️ Previous",style =discord .ButtonStyle .secondary )
        button .callback =self .prev_page_callback 
        return button 

    def create_next_button (self ):
        button =discord .ui .Button (label ="Next ▶️",style =discord .ButtonStyle .secondary )
        button .callback =self .next_page_callback 
        return button 

    async def config_select_callback (self ,interaction :discord .Interaction ):
        config_type =interaction .data ['values'][0 ].split (". ",1 )[1 ]
        modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
        await interaction .response .send_modal (modal )

    async def prev_page_callback (self ,interaction :discord .Interaction ):
        if self .page >1 :
            new_view =GiveawayConfigurationView (self .giveaway_data ,self .callback ,self .page -1 )
            embed =discord .Embed (
            title ="🎉 Giveaway Configuration",
            description =f"**Page {self.page - 1}/3**\n\nSelect a configuration option:",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def next_page_callback (self ,interaction :discord .Interaction ):
        if self .page <3 :
            new_view =GiveawayConfigurationView (self .giveaway_data ,self .callback ,self .page +1 )
            embed =discord .Embed (
            title ="🎉 Giveaway Configuration",
            description =f"**Page {self.page + 1}/3**\n\nSelect a configuration option:",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )

        embed =discord .Embed (
        title ="✅ Configuration Updated",
        description ="Setting updated successfully! You can continue configuring or close this message and start the giveaway.",
        color =0x00ff00 
        )

        try :
            await interaction .followup .send (embed =embed ,ephemeral =True )

            if hasattr (self ,'callback')and self .callback :
                await self .callback (interaction ,self .giveaway_data ,action ="edit")
        except :
            pass 

class GiveawaySetupView (View ):
    def __init__ (self ,giveaway_data ,giveaway_cog ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .giveaway_cog =giveaway_cog 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    async def update_preview (self ,interaction ):
        """Update the preview embed"""
        preview_embed =GiveawayPreviewGenerator .create_preview_embed (
        self .giveaway_data ,self .author ,self .guild 
        )


        create_msg =self .giveaway_data .get ('giveaway_create_message','🎉 **GIVEAWAY** 🎉')
        content =f"**Preview:** {create_msg}"


        config_lines =[]
        if self .giveaway_data .get ('prize'):
            config_lines .append (f"**Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            config_lines .append (f"**Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            config_lines .append (f"**Winners:** {self.giveaway_data['winners']}")
        if self .giveaway_data .get ('channel_id'):
            channel =self .guild .get_channel (int (self .giveaway_data ['channel_id']))
            if channel :
                config_lines .append (f"**Channel:** {channel.mention}")

        config_embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="\n".join (config_lines )if config_lines else "No configuration set yet.",
        color =0x0099ff 
        )

        config_embed .add_field (
        name ="Instructions",
        value ="• Use the select menu to configure options\n• Click **Preview** to see how it looks\n• Click **Start** to create the giveaway"if not self .is_template else "• Use the select menu to configure options\n• Click **Preview** to see how it looks\n• Click **Save Template** to save the template",
        inline =False 
        )

        try :
            await interaction .edit_original_response (
            content =content ,
            embeds =[config_embed ,preview_embed ],
            view =self 
            )
        except :
            await interaction .followup .send (
            content =content ,
            embeds =[config_embed ,preview_embed ],
            view =self ,
            ephemeral =True 
            )

    async def setup_callback (self ,interaction ,giveaway_data ,action ="edit"):
        if action =="start":
            if self .is_template :
                await self .save_template (interaction )
            else :
                await self .start_giveaway (interaction )
        else :
            self .giveaway_data .update (giveaway_data )
            await self .update_preview (interaction )

    async def save_template (self ,interaction ):
        """Save the template"""
        await interaction .response .defer ()


        template_name =self .giveaway_data .get ('template_name')
        if not template_name :
            embed =discord .Embed (
            title ="❌ Missing Template Name",
            description ="Please set a template name first!",
            color =0xff0000 
            )
            await interaction .followup .followup .send (embed =embed ,ephemeral =True )
            return 


        template_data ={k :v for k ,v in self .giveaway_data .items ()if k !='template_name'}
        await self .giveaway_cog .save_template (self .guild .id ,template_name ,template_data )

        embed =discord .Embed (
        title ="✅ Template Saved!",
        description =f"Template `{template_name}` has been saved successfully!",
        color =0x00ff00 
        )
        await interaction .edit_original_response (embed =embed ,view =None )

    async def start_giveaway (self ,interaction ):
        await interaction .response .defer ()


        if not self .giveaway_data .get ('prize'):
            embed =discord .Embed (
            title ="❌ Missing Prize",
            description ="Please configure a prize for the giveaway!",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 

        if not self .giveaway_data .get ('duration'):
            embed =discord .Embed (
            title ="❌ Missing Duration",
            description ="Please configure a duration for the giveaway!",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 


        duration_seconds =convert_time (self .giveaway_data ['duration'])
        if duration_seconds <=0 :
            embed =discord .Embed (
            title ="❌ Invalid Duration",
            description ="Invalid duration format! Use formats like: 1h, 2d, 3w",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 


        channel_id =self .giveaway_data .get ('channel_id')
        if channel_id :
            channel =self .guild .get_channel (channel_id )
            if not channel :
                embed =discord .Embed (
                title ="❌ Invalid Channel",
                description ="The specified channel was not found!",
                color =0xff0000 
                )
                await interaction .followup .send (embed =embed ,ephemeral =True )
                return 
        else :
            channel =interaction .channel 


        ctx =type ('obj',(object ,),{
        'guild':interaction .guild ,
        'author':interaction .user ,
        'send':interaction .followup .send 
        })


        await self .giveaway_cog .create_giveaway (
        ctx =ctx ,
        channel =channel ,
        duration =duration_seconds ,
        winners =self .giveaway_data .get ('winners',1 ),
        prize =self .giveaway_data ['prize'],
        interaction =interaction ,
        **{k :v for k ,v in self .giveaway_data .items ()if k not in ['prize','winners','duration','channel_id']}
        )


        embed =discord .Embed (
        title ="✅ Giveaway Created!",
        description =f"Your giveaway has been created in {channel.mention}!",
        color =0x00ff00 
        )
        await interaction .edit_original_response (embed =embed ,view =None )

class ParticipantsView (View ):
    def __init__ (self ,giveaway_cog ,message_id ,participants ,page =0 ):
        super ().__init__ (timeout =300 )
        self .giveaway_cog =giveaway_cog 
        self .message_id =message_id 
        self .participants =participants 
        self .page =page 
        self .per_page =5 

    @discord .ui .button (label ="◀️",style =discord .ButtonStyle .secondary ,disabled =True )
    async def previous_page (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        self .page -=1 
        await self .update_view (interaction )

    @discord .ui .button (label ="Show User Tags",style =discord .ButtonStyle .primary ,emoji ="👥")
    async def show_tags (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await self .show_participants_page (interaction ,show_tags =True )

    @discord .ui .button (label ="Remove Participant",style =discord .ButtonStyle .red ,emoji ="🗑️")
    async def remove_participant (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        modal =RemoveParticipantModal (self .remove_user_callback )
        await interaction .response .send_modal (modal )

    @discord .ui .button (label ="▶️",style =discord .ButtonStyle .secondary )
    async def next_page (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        self .page +=1 
        await self .update_view (interaction )

    async def update_view (self ,interaction ):
        total_pages =(len (self .participants )-1 )//self .per_page +1 


        self .children [0 ].disabled =self .page ==0 
        self .children [3 ].disabled =self .page >=total_pages -1 

        await self .show_participants_page (interaction ,show_tags =False )

    async def show_participants_page (self ,interaction ,show_tags =False ):
        start_idx =self .page *self .per_page 
        end_idx =start_idx +self .per_page 
        page_participants =self .participants [start_idx :end_idx ]

        if not page_participants :
            embed =discord .Embed (
            title ="📝 No Participants",
            description ="No participants on this page!",
            color =0xffff00 
            )
            if interaction .response .is_done ():
                await interaction .followup .send (embed =embed ,view =self ,ephemeral =True )
            else :
                await interaction .response .send_message (embed =embed ,view =self ,ephemeral =True )
            return 


        await self .giveaway_cog .cursor .execute ("SELECT prize, winners FROM Giveaway WHERE message_id = ?",(self .message_id ,))
        giveaway_info =await self .giveaway_cog .cursor .fetchone ()

        if not giveaway_info :
            embed =discord .Embed (
            description ="Giveaway not found!",
            color =0xff0000 
            )
            if interaction .response .is_done ():
                await interaction .followup .send (embed =embed ,view =self ,ephemeral =True )
            else :
                await interaction .response .send_message (embed =embed ,view =self ,ephemeral =True )
            return 

        prize ,winners =giveaway_info 


        participant_list =[]
        for i ,(user_id ,entries )in enumerate (page_participants ,start_idx +1 ):
            user =interaction .guild .get_member (user_id )
            if user :
                if show_tags :
                    participant_list .append (f"{i}. {user.mention} (Entries: {entries})")
                else :
                    participant_list .append (f"{i}. {user.display_name} (Entries: {entries})")
            else :
                participant_list .append (f"{i}. Unknown User ({user_id}) (Entries: {entries})")

        total_pages =(len (self .participants )-1 )//self .per_page +1 

        embed =discord .Embed (
        title =f"🎉 Giveaway Participants",
        description =f"**Prize:** {prize}\n**Winners:** {winners}\n**Total Participants:** {len(self.participants)}",
        color =0x00ff00 
        )

        participants_text ="\n".join (participant_list )
        embed .add_field (name =f"Page {self.page + 1}/{total_pages}",value =participants_text or "None",inline =False )
        embed .set_footer (text =f"Total: {len(self.participants)} participants")

        if interaction .response .is_done ():
            await interaction .followup .send (embed =embed ,view =self ,ephemeral =True )
        else :
            await interaction .response .send_message (embed =embed ,view =self ,ephemeral =True )

    async def remove_user_callback (self ,interaction ,user_id ):

        await self .giveaway_cog .cursor .execute (
        "DELETE FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ? AND user_id = ?",
        (interaction .guild .id ,self .message_id ,user_id )
        )

        if self .giveaway_cog .cursor .rowcount >0 :
            await self .giveaway_cog .connection .commit ()
            await self .giveaway_cog .update_participant_count (interaction .guild .id ,self .message_id )


            await self .giveaway_cog .cursor .execute (
            "SELECT user_id, entries FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",
            (interaction .guild .id ,self .message_id )
            )
            self .participants =await self .giveaway_cog .cursor .fetchall ()


            total_pages =(len (self .participants )-1 )//self .per_page +1 if self .participants else 1 
            if self .page >=total_pages :
                self .page =max (0 ,total_pages -1 )

            embed =discord .Embed (
            title ="✅ Participant Removed",
            description =f"User <@{user_id}> has been removed from the giveaway.",
            color =0x00ff00 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )


            await self .update_view (interaction )
        else :
            embed =discord .Embed (
            description ="User was not found in this giveaway!",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )

class GiveawayEditView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ,timeout_duration =900 ):
        super ().__init__ (timeout =timeout_duration )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 


        self .start_button_label ="Save Template"if is_template else "Start Giveaway"


        if len (self .children )>=3 :
            self .children [2 ].label =self .start_button_label 

    @discord .ui .select (
    placeholder ="Select what to configure...",
    options =[
    discord .SelectOption (label ="1. Basic Settings",description ="Prize, Duration, Winners, Channel"),
    discord .SelectOption (label ="2. Requirements",description ="Role, Level, Message requirements"),
    discord .SelectOption (label ="3. Appearance",description ="Color, Image, Thumbnail, Title"),
    discord .SelectOption (label ="4. Messages",description ="Custom messages and announcements"),
    discord .SelectOption (label ="5. Advanced",description ="Extra entries, bypass roles, etc."),
    discord .SelectOption (label ="6. Templates",description ="Save/Load templates")
    ]
    )
    async def config_category_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        category =select .values [0 ].split (". ",1 )[1 ]

        if category =="Basic Settings":
            view =BasicSettingsView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )
        elif category =="Requirements":
            view =RequirementsView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )
        elif category =="Appearance":
            view =AppearanceView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )
        elif category =="Messages":
            view =MessagesView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )
        elif category =="Advanced":
            view =AdvancedView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )
        elif category =="Templates":
            view =TemplatesView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title =f"Configure {category}",
        description ="Select what you want to configure:",
        color =0x0099ff 
        )
        await interaction .response .send_message (embed =embed ,view =view ,ephemeral =True )

    @discord .ui .button (label ="Preview",style =discord .ButtonStyle .secondary )
    async def preview_giveaway (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        preview_embed =GiveawayPreviewGenerator .create_preview_embed (
        self .giveaway_data ,self .author ,self .guild 
        )

        create_msg =self .giveaway_data .get ('giveaway_create_message','🎉 **GIVEAWAY** 🎉')

        await interaction .response .send_message (
        content =f"**Preview:** {create_msg}",
        embed =preview_embed ,
        ephemeral =True 
        )

    @discord .ui .button (label ="Start Giveaway",style =discord .ButtonStyle .green )
    async def start_giveaway (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await self .callback (interaction ,self .giveaway_data ,action ="start")

    @discord .ui .button (label ="Cancel",style =discord .ButtonStyle .red )
    async def cancel_giveaway (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        embed =discord .Embed (
        title ="Setup Cancelled",
        description ="Giveaway setup has been cancelled.",
        color =0xff0000 
        )
        await interaction .response .edit_message (embed =embed ,view =None )



class BasicSettingsView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    @discord .ui .select (
    placeholder ="Select basic setting to configure...",
    options =[
    discord .SelectOption (label ="1. Prize",description ="Set the giveaway prize"),
    discord .SelectOption (label ="2. Duration",description ="Set giveaway duration"),
    discord .SelectOption (label ="3. Winners",description ="Set number of winners"),
    discord .SelectOption (label ="4. Channel",description ="Set giveaway channel"),
    discord .SelectOption (label ="5. Giveaway Host",description ="Set giveaway host"),
    discord .SelectOption (label ="6. Use Template",description ="Use existing template"),
    ]
    )
    async def basic_config_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        config_type =select .values [0 ].split (". ",1 )[1 ]
        modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
        await interaction .response .send_modal (modal )

    @discord .ui .button (label ="← Back to Main Menu",style =discord .ButtonStyle .secondary ,emoji ="🔙")
    async def back_to_main (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        edit_view =GiveawayEditView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="**Main Configuration Menu**\n\nSelect a category below to configure your giveaway settings:",
        color =0x7289da 
        )


        settings_preview =[]
        if self .giveaway_data .get ('prize'):
            settings_preview .append (f"🎁 **Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            settings_preview .append (f"⏱️ **Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            settings_preview .append (f"🏆 **Winners:** {self.giveaway_data['winners']}")

        if settings_preview :
            embed .add_field (
            name ="📋 Current Settings",
            value ="\n".join (settings_preview [:3 ]),
            inline =False 
            )

        embed .set_footer (text ="💡 Use the dropdown menu to select a configuration category")

        await interaction .response .edit_message (embed =embed ,view =edit_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )
        embed =discord .Embed (
        title ="✅ Setting Updated",
        description ="Configuration updated successfully! Continue configuring more basic settings or go back to main menu.",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )


class RequirementsView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    @discord .ui .select (
    placeholder ="Select requirement to configure...",
    options =[
    discord .SelectOption (label ="1. Required role to join",description ="Role required to enter"),
    discord .SelectOption (label ="2. Required level to join",description ="Level required to join"),
    discord .SelectOption (label ="3. Required Total messages",description ="Total messages required"),
    discord .SelectOption (label ="4. Requirements Bypass role",description ="Role that bypasses requirements"),
    discord .SelectOption (label ="5. Show Giveaway Entry Captcha",description ="Enable/disable captcha verification"),
    ]
    )
    async def requirements_config_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        config_type =select .values [0 ].split (". ",1 )[1 ]

        if config_type =="Show Giveaway Entry Captcha":
            view =CaptchaConfigView (self .giveaway_data ,self .callback )
            embed =discord .Embed (
            title ="Configure CAPTCHA",
            description ="Enable or disable CAPTCHA verification for giveaway entries:",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =view )
        else :
            modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
            await interaction .response .send_modal (modal )

    @discord .ui .button (label ="← Back to Main Menu",style =discord .ButtonStyle .secondary ,emoji ="🔙")
    async def back_to_main (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        edit_view =GiveawayEditView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="**Main Configuration Menu**\n\nSelect a category below to configure your giveaway settings:",
        color =0x7289da 
        )


        settings_preview =[]
        if self .giveaway_data .get ('prize'):
            settings_preview .append (f"🎁 **Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            settings_preview .append (f"⏱️ **Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            settings_preview .append (f"🏆 **Winners:** {self.giveaway_data['winners']}")

        if settings_preview :
            embed .add_field (
            name ="📋 Current Settings",
            value ="\n".join (settings_preview [:3 ]),
            inline =False 
            )

        embed .set_footer (text ="💡 Use the dropdown menu to select a configuration category")

        await interaction .response .edit_message (embed =embed ,view =edit_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )
        embed =discord .Embed (
        title ="✅ Setting Updated",
        description ="Configuration updated successfully! Continue configuring more requirements or go back to main menu.",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )


class AppearanceView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    @discord .ui .select (
    placeholder ="Select appearance setting to configure...",
    options =[
    discord .SelectOption (label ="1. Title",description ="Set giveaway title"),
    discord .SelectOption (label ="2. Color",description ="Giveaway embed color"),
    discord .SelectOption (label ="3. End color",description ="Color when giveaway ends"),
    discord .SelectOption (label ="4. Image",description ="Set giveaway image"),
    discord .SelectOption (label ="5. Thumbnail",description ="Set giveaway thumbnail"),
    discord .SelectOption (label ="6. Author",description ="Set giveaway author"),
    discord .SelectOption (label ="7. Footer",description ="Set giveaway footer"),
    ]
    )
    async def appearance_config_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        config_type =select .values [0 ].split (". ",1 )[1 ]
        modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
        await interaction .response .send_modal (modal )

    @discord .ui .button (label ="← Back to Main Menu",style =discord .ButtonStyle .secondary ,emoji ="🔙")
    async def back_to_main (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        edit_view =GiveawayEditView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="**Main Configuration Menu**\n\nSelect a category below to configure your giveaway settings:",
        color =0x7289da 
        )


        settings_preview =[]
        if self .giveaway_data .get ('prize'):
            settings_preview .append (f"🎁 **Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            settings_preview .append (f"⏱️ **Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            settings_preview .append (f"🏆 **Winners:** {self.giveaway_data['winners']}")

        if settings_preview :
            embed .add_field (
            name ="📋 Current Settings",
            value ="\n".join (settings_preview [:3 ]),
            inline =False 
            )

        embed .set_footer (text ="💡 Use the dropdown menu to select a configuration category")

        await interaction .response .edit_message (embed =embed ,view =edit_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )
        embed =discord .Embed (
        title ="✅ Setting Updated",
        description ="Configuration updated successfully! Continue configuring more appearance settings or go back to main menu.",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )


class MessagesView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    @discord .ui .select (
    placeholder ="Select message setting to configure...",
    options =[
    discord .SelectOption (label ="1. Giveaway Create Message",description ="Custom announcement message"),
    discord .SelectOption (label ="2. Giveaway winner dm message",description ="DM message for winners"),
    discord .SelectOption (label ="3. Entry Confirmation message",description ="Message when user enters"),
    discord .SelectOption (label ="4. Entry Deny message",description ="Message when entry is denied"),
    discord .SelectOption (label ="5. Entry Remove Message",description ="Message when user leaves giveaway"),
    ]
    )
    async def messages_config_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        config_type =select .values [0 ].split (". ",1 )[1 ]
        modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
        await interaction .response .send_modal (modal )

    @discord .ui .button (label ="← Back to Main Menu",style =discord .ButtonStyle .secondary ,emoji ="🔙")
    async def back_to_main (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        edit_view =GiveawayEditView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="**Main Configuration Menu**\n\nSelect a category below to configure your giveaway settings:",
        color =0x7289da 
        )


        settings_preview =[]
        if self .giveaway_data .get ('prize'):
            settings_preview .append (f"🎁 **Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            settings_preview .append (f"⏱️ **Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            settings_preview .append (f"🏆 **Winners:** {self.giveaway_data['winners']}")

        if settings_preview :
            embed .add_field (
            name ="📋 Current Settings",
            value ="\n".join (settings_preview [:3 ]),
            inline =False 
            )

        embed .set_footer (text ="💡 Use the dropdown menu to select a configuration category")

        await interaction .response .edit_message (embed =embed ,view =edit_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )
        embed =discord .Embed (
        title ="✅ Setting Updated",
        description ="Configuration updated successfully! Continue configuring more message settings or go back to main menu.",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )


class AdvancedView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    @discord .ui .select (
    placeholder ="Select advanced setting to configure...",
    options =[
    discord .SelectOption (label ="1. Extra Entries",description ="Configure extra entries for roles"),
    discord .SelectOption (label ="2. Required Roles",description ="Set required roles to enter"),
    discord .SelectOption (label ="3. Required Role Type",description ="Set how required roles work"),
    discord .SelectOption (label ="4. Blacklisted role",description ="Roles that cannot enter"),
    ]
    )
    async def advanced_config_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        config_type =select .values [0 ].split (". ",1 )[1 ]

        if config_type =="Extra Entries":
            view =ExtraEntriesView (self .giveaway_data ,self .callback ,self .guild )
            embed =discord .Embed (
            title ="Configure Extra Entries",
            description ="Select a role that should get extra entries:",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =view )
        elif config_type =="Required Roles":
            view =RequiredRoleView (self .giveaway_data ,self .callback ,self .guild )
            embed =discord .Embed (
            title ="Configure Required Roles",
            description ="Select roles required to enter giveaway:",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =view )
        elif config_type =="Required Role Type":
            view =RequiredRoleTypeView (self .giveaway_data ,self .callback )
            embed =discord .Embed (
            title ="Configure Required Role Type",
            description ="How should required roles work?",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =view )
        elif config_type =="Blacklisted role":
            view =BlacklistedRolesView (self .giveaway_data ,self .callback ,self .guild )
            embed =discord .Embed (
            title ="Configure Blacklisted Roles",
            description ="Select roles that cannot enter giveaways:",
            color =0x0099ff 
            )
            await interaction .response .edit_message (embed =embed ,view =view )
        else :
            modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
            await interaction .response .send_modal (modal )

    @discord .ui .button (label ="← Back to Main Menu",style =discord .ButtonStyle .secondary ,emoji ="🔙")
    async def back_to_main (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        edit_view =GiveawayEditView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="**Main Configuration Menu**\n\nSelect a category below to configure your giveaway settings:",
        color =0x7289da 
        )


        settings_preview =[]
        if self .giveaway_data .get ('prize'):
            settings_preview .append (f"🎁 **Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            settings_preview .append (f"⏱️ **Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            settings_preview .append (f"🏆 **Winners:** {self.giveaway_data['winners']}")

        if settings_preview :
            embed .add_field (
            name ="📋 Current Settings",
            value ="\n".join (settings_preview [:3 ]),
            inline =False 
            )

        embed .set_footer (text ="💡 Use the dropdown menu to select a configuration category")

        await interaction .response .edit_message (embed =embed ,view =edit_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )
        embed =discord .Embed (
        title ="✅ Setting Updated",
        description ="Configuration updated successfully! Continue configuring more advanced settings or go back to main menu.",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )


class CaptchaConfigView (View ):
    def __init__ (self ,giveaway_data ,callback ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 

    @discord .ui .select (
    placeholder ="Make a selection",
    options =[
    discord .SelectOption (label ="Yes",description ="Enable captcha verification"),
    discord .SelectOption (label ="No",description ="Disable captcha verification")
    ]
    )
    async def captcha_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        choice =select .values [0 ]
        self .giveaway_data ['show_captcha']=choice =="Yes"

        embed =discord .Embed (
        title ="✅ Captcha Configuration Updated",
        description =f"Successfully {'enabled' if choice == 'Yes' else 'disabled'} showing giveaway entry captcha!",
        color =0x00ff00 
        )

        view =ContinueEditingView (self .giveaway_data ,self .callback )
        await interaction .response .edit_message (embed =embed ,view =view )

class ExtraEntriesView (View ):
    def __init__ (self ,giveaway_data ,callback ,guild ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .guild =guild 


        self .role_select =discord .ui .RoleSelect (
        placeholder ="Select a role for extra entries",
        max_values =1 
        )
        self .role_select .callback =self .role_select_callback 
        self .add_item (self .role_select )

    async def role_select_callback (self ,interaction :discord .Interaction ):
        if not self .role_select .values :
            embed =discord .Embed (
            title ="❌ No Role Selected",
            description ="Please select a role to configure extra entries.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        role =self .role_select .values [0 ]
        modal =ExtraEntriesModal (role ,self .giveaway_data ,self .modal_callback )
        await interaction .response .send_modal (modal )

    async def modal_callback (self ,interaction ,role ,entries ):
        self .giveaway_data ['extra_entries_role']=str (role .id )
        self .giveaway_data ['extra_entries_count']=entries 

        embed =discord .Embed (
        title ="✅ Extra Entries Set",
        description =f"Successfully set {entries} extra entries for {role.mention}!",
        color =0x00ff00 
        )

        view =ContinueEditingView (self .giveaway_data ,self .callback )
        await interaction .followup .send (embed =embed ,view =view ,ephemeral =True )

class ExtraEntriesModal (Modal ):
    def __init__ (self ,role ,giveaway_data ,callback ):
        super ().__init__ (title =f"Extra Entries for {role.name}")
        self .role =role 
        self .giveaway_data =giveaway_data 
        self .callback =callback 

        self .add_item (TextInput (
        label ="Number of Extra Entries",
        placeholder ="Enter number of extra entries (1-10)",
        default ="1",
        max_length =2 
        ))

    async def on_submit (self ,interaction ):
        await interaction .response .defer (ephemeral =True )

        try :
            entries =int (self .children [0 ].value )
            if entries <1 or entries >10 :
                raise ValueError ("Entries must be between 1 and 10")

            await self .callback (interaction ,self .role ,entries )
        except ValueError :
            embed =discord .Embed (
            title ="❌ Invalid Input",
            description ="Please enter a valid number between 1 and 10.",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )

class ChannelSelectionView (View ):
    def __init__ (self ,giveaway_data ,callback ,guild ,page =0 ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .guild =guild 
        self .page =page 
        self .channels_per_page =23 


        self .all_channels =[channel for channel in guild .text_channels if channel .permissions_for (guild .me ).send_messages ]


        total_channels =len (self .all_channels )
        self .total_pages =(total_channels -1 )//self .channels_per_page +1 if total_channels >0 else 1 


        self .add_channel_select ()


        if self .total_pages >1 :
            if self .page >0 :
                prev_button =discord .ui .Button (label ="◀️ Previous",style =discord .ButtonStyle .secondary )
                prev_button .callback =self .prev_page 
                self .add_item (prev_button )

            if self .page <self .total_pages -1 :
                next_button =discord .ui .Button (label ="Next ▶️",style =discord .ButtonStyle .secondary )
                next_button .callback =self .next_page 
                self .add_item (next_button )

    def add_channel_select (self ):
        start_idx =self .page *self .channels_per_page 
        end_idx =start_idx +self .channels_per_page 
        page_channels =self .all_channels [start_idx :end_idx ]

        if not page_channels :
            return 

        options =[]
        for channel in page_channels :
            options .append (discord .SelectOption (
            label =f"#{channel.name}",
            value =str (channel .id ),
            description =f"ID: {channel.id}"
            ))

        if options :
            placeholder =f"Select giveaway channel (Page {self.page + 1}/{self.total_pages})"
            channel_select =discord .ui .Select (
            placeholder =placeholder ,
            options =options ,
            max_values =1 
            )
            channel_select .callback =self .channel_select_callback 
            self .add_item (channel_select )

    async def channel_select_callback (self ,interaction :discord .Interaction ):
        selected_channel_id =interaction .data .get ('values',[])[0 ]if interaction .data .get ('values')else None 

        if selected_channel_id :
            channel =self .guild .get_channel (int (selected_channel_id ))
            if channel :
                self .giveaway_data ['channel_id']=int (selected_channel_id )

                embed =discord .Embed (
                title ="✅ Channel Selected",
                description =f"Giveaway channel set to {channel.mention}",
                color =0x00ff00 
                )

                view =ContinueEditingView (self .giveaway_data ,self .callback )
                await interaction .response .edit_message (embed =embed ,view =view )

    async def prev_page (self ,interaction :discord .Interaction ):
        if self .page >0 :
            new_view =ChannelSelectionView (self .giveaway_data ,self .callback ,self .guild ,self .page -1 )

            embed =discord .Embed (
            title ="Select Giveaway Channel",
            description =f"Choose a channel for the giveaway:",
            color =0x0099ff 
            )
            embed .set_footer (text =f"Page {self.page}/{self.total_pages}")

            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def next_page (self ,interaction :discord .Interaction ):
        if self .page <self .total_pages -1 :
            new_view =ChannelSelectionView (self .giveaway_data ,self .callback ,self .guild ,self .page +1 )

            embed =discord .Embed (
            title ="Select Giveaway Channel",
            description =f"Choose a channel for the giveaway:",
            color =0x0099ff 
            )
            embed .set_footer (text =f"Page {self.page + 2}/{self.total_pages}")

            await interaction .response .edit_message (embed =embed ,view =new_view )

class RequiredRoleView (View ):
    def __init__ (self ,giveaway_data ,callback ,guild ,page =0 ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .guild =guild 
        self .page =page 
        self .roles_per_page =23 


        self .all_roles =[role for role in guild .roles if role .name !="@everyone"]


        selected_role_ids =self .giveaway_data .get ('required_roles',[])
        if isinstance (selected_role_ids ,str ):
            try :
                selected_role_ids =[int (selected_role_ids )]
            except :
                selected_role_ids =[]
        elif not isinstance (selected_role_ids ,list ):
            selected_role_ids =[]

        self .selected_roles =set (str (role_id )for role_id in selected_role_ids )


        total_roles =len (self .all_roles )
        self .total_pages =(total_roles -1 )//self .roles_per_page +1 if total_roles >0 else 1 


        self .add_role_select ()


        if self .total_pages >1 :
            if self .page >0 :
                prev_button =discord .ui .Button (label ="◀️ Previous",style =discord .ButtonStyle .secondary )
                prev_button .callback =self .prev_page 
                self .add_item (prev_button )

            if self .page <self .total_pages -1 :
                next_button =discord .ui .Button (label ="Next ▶️",style =discord .ButtonStyle .secondary )
                next_button .callback =self .next_page 
                self .add_item (next_button )


        finish_button =discord .ui .Button (label ="✅ Finish Selection",style =discord .ButtonStyle .green )
        finish_button .callback =self .finish_selection 
        self .add_item (finish_button )

    def add_role_select (self ):
        start_idx =self .page *self .roles_per_page 
        end_idx =start_idx +self .roles_per_page 
        page_roles =self .all_roles [start_idx :end_idx ]

        if not page_roles :
            return 

        options =[]
        for role in page_roles :
            is_selected =str (role .id )in self .selected_roles 
            emoji ="✅"if is_selected else None 
            description =f"Currently {'selected' if is_selected else 'not selected'}"

            options .append (discord .SelectOption (
            label =role .name [:100 ],
            value =str (role .id ),
            description =description [:100 ],
            emoji =emoji 
            ))

        if options :
            placeholder =f"Select required roles (Page {self.page + 1}/{self.total_pages})"
            role_select =discord .ui .Select (
            placeholder =placeholder ,
            options =options ,
            max_values =len (options )
            )
            role_select .callback =self .role_select_callback 
            self .add_item (role_select )

    async def role_select_callback (self ,interaction :discord .Interaction ):
        selected_values =interaction .data .get ('values',[])


        for role_id in selected_values :
            if role_id in self .selected_roles :
                self .selected_roles .remove (role_id )
            else :
                self .selected_roles .add (role_id )


        await self .update_view (interaction )

    async def update_view (self ,interaction ):

        new_view =RequiredRoleView (self .giveaway_data ,self .callback ,self .guild ,self .page )
        new_view .selected_roles =self .selected_roles .copy ()


        selected_role_names =[]
        for role_id in self .selected_roles :
            role =self .guild .get_role (int (role_id ))
            if role :
                selected_role_names .append (role .name )

        embed =discord .Embed (
        title ="Configure Required Roles",
        description =f"Select roles required to enter giveaway:\n\n**Currently Selected ({len(selected_role_names)}):**\n"+
        (", ".join (selected_role_names [:10 ])+("..."if len (selected_role_names )>10 else "")if selected_role_names else "None"),
        color =0x0099ff 
        )

        if self .total_pages >1 :
            embed .set_footer (text =f"Page {self.page + 1}/{self.total_pages} • Click roles to toggle selection")
        else :
            embed .set_footer (text ="Click roles to toggle selection")

        await interaction .response .edit_message (embed =embed ,view =new_view )

    async def prev_page (self ,interaction :discord .Interaction ):
        if self .page >0 :
            new_view =RequiredRoleView (self .giveaway_data ,self .callback ,self .guild ,self .page -1 )
            new_view .selected_roles =self .selected_roles .copy ()

            selected_role_names =[]
            for role_id in self .selected_roles :
                role =self .guild .get_role (int (role_id ))
                if role :
                    selected_role_names .append (role .name )

            embed =discord .Embed (
            title ="Configure Required Roles",
            description =f"Select roles required to enter giveaway:\n\n**Currently Selected ({len(selected_role_names)}):**\n"+
            (", ".join (selected_role_names [:10 ])+("..."if len (selected_role_names )>10 else "")if selected_role_names else "None"),
            color =0x0099ff 
            )
            embed .set_footer (text =f"Page {self.page}/{self.total_pages} • Click roles to toggle selection")

            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def next_page (self ,interaction :discord .Interaction ):
        if self .page <self .total_pages -1 :
            new_view =RequiredRoleView (self .giveaway_data ,self .callback ,self .guild ,self .page +1 )
            new_view .selected_roles =self .selected_roles .copy ()

            selected_role_names =[]
            for role_id in self .selected_roles :
                role =self .guild .get_role (int (role_id ))
                if role :
                    selected_role_names .append (role .name )

            embed =discord .Embed (
            title ="Configure Required Roles",
            description =f"Select roles required to enter giveaway:\n\n**Currently Selected ({len(selected_role_names)}):**\n"+
            (", ".join (selected_role_names [:10 ])+("..."if len (selected_role_names )>10 else "")if selected_role_names else "None"),
            color =0x0099ff 
            )
            embed .set_footer (text =f"Page {self.page + 2}/{self.total_pages} • Click roles to toggle selection")

            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def finish_selection (self ,interaction :discord .Interaction ):

        selected_role_ids =[int (role_id )for role_id in self .selected_roles ]
        self .giveaway_data ['required_roles']=selected_role_ids 


        selected_role_names =[]
        for role_id in selected_role_ids :
            role =self .guild .get_role (role_id )
            if role :
                selected_role_names .append (role .name )

        embed =discord .Embed (
        title ="✅ Required Roles Updated",
        description =f"**Selected Roles ({len(selected_role_names)}):**\n"+
        (", ".join (selected_role_names )if selected_role_names else "None"),
        color =0x00ff00 
        )

        view =ContinueEditingView (self .giveaway_data ,self .callback )
        await interaction .response .edit_message (embed =embed ,view =view )

class RequiredRoleTypeView (View ):
    def __init__ (self ,giveaway_data ,callback ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 

    @discord .ui .select (
    placeholder ="Make a selection",
    options =[
    discord .SelectOption (
    label ="Participants must have all required roles",
    description ="User needs ALL the required roles",
    value ="all"
    ),
    discord .SelectOption (
    label ="Participants must have one of the required roles",
    description ="User needs at least ONE of the required roles",
    value ="any"
    )
    ]
    )
    async def role_type_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        choice =select .values [0 ]
        self .giveaway_data ['required_role_type']=choice 

        description ="all required roles"if choice =="all"else "at least one of the required roles"

        embed =discord .Embed (
        title ="✅ Required Role Type Set",
        description =f"Participants must have {description}.",
        color =0x00ff00 
        )

        view =ContinueEditingView (self .giveaway_data ,self .callback )
        await interaction .response .edit_message (embed =embed ,view =view )

class TemplatesView (View ):
    def __init__ (self ,giveaway_data ,callback ,author ,guild ,is_template =False ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .author =author 
        self .guild =guild 
        self .is_template =is_template 

    @discord .ui .select (
    placeholder ="Select template option...",
    options =[
    discord .SelectOption (label ="1. Template Name",description ="Set template name for saving"),
    discord .SelectOption (label ="2. Use Template",description ="Load existing template"),
    ]
    )
    async def template_config_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        config_type =select .values [0 ].split (". ",1 )[1 ]
        modal =GiveawayConfigModal (config_type ,self .giveaway_data ,self .modal_callback )
        await interaction .response .send_modal (modal )

    @discord .ui .button (label ="← Back to Main Menu",style =discord .ButtonStyle .secondary ,emoji ="🔙")
    async def back_to_main (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        edit_view =GiveawayEditView (self .giveaway_data ,self .callback ,self .author ,self .guild ,self .is_template )

        embed =discord .Embed (
        title ="🎉 Giveaway Configuration",
        description ="**Main Configuration Menu**\n\nSelect a category below to configure your giveaway settings:",
        color =0x7289da 
        )


        settings_preview =[]
        if self .giveaway_data .get ('prize'):
            settings_preview .append (f"🎁 **Prize:** {self.giveaway_data['prize']}")
        if self .giveaway_data .get ('duration'):
            settings_preview .append (f"⏱️ **Duration:** {self.giveaway_data['duration']}")
        if self .giveaway_data .get ('winners'):
            settings_preview .append (f"🏆 **Winners:** {self.giveaway_data['winners']}")

        if settings_preview :
            embed .add_field (
            name ="📋 Current Settings",
            value ="\n".join (settings_preview [:3 ]),
            inline =False 
            )

        embed .set_footer (text ="💡 Use the dropdown menu to select a configuration category")

        await interaction .response .edit_message (embed =embed ,view =edit_view )

    async def modal_callback (self ,interaction ,updated_data ):
        self .giveaway_data .update (updated_data )
        embed =discord .Embed (
        title ="✅ Setting Updated",
        description ="Configuration updated successfully! Continue configuring more template settings or go back to main menu.",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )

class BlacklistedRolesView (View ):
    def __init__ (self ,giveaway_data ,callback ,guild ,page =0 ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 
        self .guild =guild 
        self .page =page 
        self .roles_per_page =23 


        self .all_roles =[role for role in guild .roles if role .name !="@everyone"]


        selected_role_ids =self .giveaway_data .get ('blacklisted_roles',[])
        if isinstance (selected_role_ids ,str ):
            try :
                selected_role_ids =[int (selected_role_ids )]
            except :
                selected_role_ids =[]
        elif not isinstance (selected_role_ids ,list ):
            selected_role_ids =[]

        self .selected_roles =set (str (role_id )for role_id in selected_role_ids )


        total_roles =len (self .all_roles )
        self .total_pages =(total_roles -1 )//self .roles_per_page +1 if total_roles >0 else 1 


        self .add_role_select ()


        if self .total_pages >1 :
            if self .page >0 :
                prev_button =discord .ui .Button (label ="◀️ Previous",style =discord .ButtonStyle .secondary )
                prev_button .callback =self .prev_page 
                self .add_item (prev_button )

            if self .page <self .total_pages -1 :
                next_button =discord .ui .Button (label ="Next ▶️",style =discord .ButtonStyle .secondary )
                next_button .callback =self .next_page 
                self .add_item (next_button )


        finish_button =discord .ui .Button (label ="✅ Finish Selection",style =discord .ButtonStyle .green )
        finish_button .callback =self .finish_selection 
        self .add_item (finish_button )

    def add_role_select (self ):
        start_idx =self .page *self .roles_per_page 
        end_idx =start_idx +self .roles_per_page 
        page_roles =self .all_roles [start_idx :end_idx ]

        if not page_roles :
            return 

        options =[]
        for role in page_roles :
            is_selected =str (role .id )in self .selected_roles 
            emoji ="✅"if is_selected else None 
            description =f"Currently {'selected' if is_selected else 'not selected'}"

            options .append (discord .SelectOption (
            label =role .name [:100 ],
            value =str (role .id ),
            description =description [:100 ],
            emoji =emoji 
            ))

        if options :
            placeholder =f"Select blacklisted roles (Page {self.page + 1}/{self.total_pages})"
            role_select =discord .ui .Select (
            placeholder =placeholder ,
            options =options ,
            max_values =len (options )
            )
            role_select .callback =self .role_select_callback 
            self .add_item (role_select )

    async def role_select_callback (self ,interaction :discord .Interaction ):
        selected_values =interaction .data .get ('values',[])


        for role_id in selected_values :
            if role_id in self .selected_roles :
                self .selected_roles .remove (role_id )
            else :
                self .selected_roles .add (role_id )


        await self .update_view (interaction )

    async def update_view (self ,interaction ):

        new_view =BlacklistedRolesView (self .giveaway_data ,self .callback ,self .guild ,self .page )
        new_view .selected_roles =self .selected_roles .copy ()


        selected_role_names =[]
        for role_id in self .selected_roles :
            role =self .guild .get_role (int (role_id ))
            if role :
                selected_role_names .append (role .name )

        embed =discord .Embed (
        title ="Configure Blacklisted Roles",
        description =f"Select roles that cannot enter giveaways:\n\n**Currently Selected ({len(selected_role_names)}):**\n"+
        (", ".join (selected_role_names [:10 ])+("..."if len (selected_role_names )>10 else "")if selected_role_names else "None"),
        color =0x0099ff 
        )

        if self .total_pages >1 :
            embed .set_footer (text =f"Page {self.page + 1}/{self.total_pages} • Click roles to toggle selection")
        else :
            embed .set_footer (text ="Click roles to toggle selection")

        await interaction .response .edit_message (embed =embed ,view =new_view )

    async def prev_page (self ,interaction :discord .Interaction ):
        if self .page >0 :
            new_view =BlacklistedRolesView (self .giveaway_data ,self .callback ,self .guild ,self .page -1 )
            new_view .selected_roles =self .selected_roles .copy ()

            selected_role_names =[]
            for role_id in self .selected_roles :
                role =self .guild .get_role (int (role_id ))
                if role :
                    selected_role_names .append (role .name )

            embed =discord .Embed (
            title ="Configure Blacklisted Roles",
            description =f"Select roles that cannot enter giveaways:\n\n**Currently Selected ({len(selected_role_names)}):**\n"+
            (", ".join (selected_role_names [:10 ])+("..."if len (selected_role_names )>10 else "")if selected_role_names else "None"),
            color =0x0099ff 
            )
            embed .set_footer (text =f"Page {self.page}/{self.total_pages} • Click roles to toggle selection")

            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def next_page (self ,interaction :discord .Interaction ):
        if self .page <self .total_pages -1 :
            new_view =BlacklistedRolesView (self .giveaway_data ,self .callback ,self .guild ,self .page +1 )
            new_view .selected_roles =self .selected_roles .copy ()

            selected_role_names =[]
            for role_id in self .selected_roles :
                role =self .guild .get_role (int (role_id ))
                if role :
                    selected_role_names .append (role .name )

            embed =discord .Embed (
            title ="Configure Blacklisted Roles",
            description =f"Select roles that cannot enter giveaways:\n\n**Currently Selected ({len(selected_role_names)}):**\n"+
            (", ".join (selected_role_names [:10 ])+("..."if len (selected_role_names )>10 else "")if selected_role_names else "None"),
            color =0x0099ff 
            )
            embed .set_footer (text =f"Page {self.page + 2}/{self.total_pages} • Click roles to toggle selection")

            await interaction .response .edit_message (embed =embed ,view =new_view )

    async def finish_selection (self ,interaction :discord .Interaction ):

        selected_role_ids =[int (role_id )for role_id in self .selected_roles ]
        self .giveaway_data ['blacklisted_roles']=selected_role_ids 


        selected_role_names =[]
        for role_id in selected_role_ids :
            role =self .guild .get_role (role_id )
            if role :
                selected_role_names .append (role .name )

        embed =discord .Embed (
        title ="✅ Blacklisted Roles Updated",
        description =f"**Selected Roles ({len(selected_role_names)}):**\n"+
        (", ".join (selected_role_names )if selected_role_names else "None"),
        color =0x00ff00 
        )

        view =ContinueEditingView (self .giveaway_data ,self .callback )
        await interaction .response .edit_message (embed =embed ,view =view )

class GiveawayMainConfigView (View ):
    def __init__ (self ,giveaway_data ,callback ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 

    @discord .ui .select (
    placeholder ="Select configuration category...",
    options =[
    discord .SelectOption (label ="1. Basic Settings",description ="Prize, Duration, Winners, Channel"),
    discord .SelectOption (label ="2. Requirements",description ="Role, Level, Message requirements"),
    discord .SelectOption (label ="3. Appearance",description ="Color, Image, Thumbnail, Title"),
    discord .SelectOption (label ="4. Messages",description ="Custom messages and announcements"),
    discord .SelectOption (label ="5. Advanced",description ="Extra entries, bypass roles, etc."),
    discord .SelectOption (label ="6. Templates",description ="Save/Load templates")
    ]
    )
    async def config_category_select (self ,interaction :discord .Interaction ,select :discord .ui .Select ):
        category =select .values [0 ].split (". ",1 )[1 ]

        if category =="Basic Settings":
            view =BasicSettingsView (self .giveaway_data ,self .callback ,interaction .user ,interaction .guild )
        elif category =="Requirements":
            view =RequirementsView (self .giveaway_data ,self .callback ,interaction .user ,interaction .guild )
        elif category =="Appearance":
            view =AppearanceView (self .giveaway_data ,self .callback ,interaction .user ,interaction .guild )
        elif category =="Messages":
            view =MessagesView (self .giveaway_data ,self .callback ,interaction .user ,interaction .guild )
        elif category =="Advanced":
            view =AdvancedView (self .giveaway_data ,self .callback ,interaction .user ,interaction .guild )
        elif category =="Templates":
            view =TemplatesView (self .giveaway_data ,self .callback ,interaction .user ,interaction .guild )

        embed =discord .Embed (
        title =f"Configure {category}",
        description ="Select what you want to configure:",
        color =0x0099ff 
        )
        await interaction .response .edit_message (embed =embed ,view =view )

class ContinueEditingView (View ):
    def __init__ (self ,giveaway_data ,callback ):
        super ().__init__ (timeout =900 )
        self .giveaway_data =giveaway_data 
        self .callback =callback 

    @discord .ui .button (label ="Continue editing",style =discord .ButtonStyle .primary )
    async def continue_editing (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        view =GiveawayMainConfigView (self .giveaway_data ,self .callback )
        embed =discord .Embed (
        title ="Edit Giveaway Configuration",
        description ="Select what you want to edit:",
        color =0x0099ff 
        )
        await interaction .response .edit_message (embed =embed ,view =view )

class GiveawayView (View ):
    def __init__ (self ,giveaway_cog ,guild_id ,message_id ):
        super ().__init__ (timeout =None )
        self .giveaway_cog =giveaway_cog 
        self .guild_id =guild_id 
        self .message_id =message_id 

    async def on_error (self ,interaction :discord .Interaction ,error :Exception ,item ):
        try :
            embed =discord .Embed (
            color =0xff0000 
            )
            if not interaction .response .is_done ():
                await interaction .response .send_message (embed =embed ,ephemeral =True )
            else :
                await interaction .followup .send (embed =embed ,ephemeral =True )
        except discord .InteractionResponded :
            pass 
        except discord .NotFound :
            pass 
        except Exception as e :
            pass 

    @discord .ui .button (label ="Join",style =discord .ButtonStyle .green ,emoji ="🎉")
    async def join_giveaway (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :
            await self .giveaway_cog .handle_giveaway_join (interaction ,self .message_id )
        except Exception as e :
            try :
                embed =discord .Embed (
                color =0xff0000 
                )
                if not interaction .response .is_done ():
                    await interaction .response .send_message (embed =embed ,ephemeral =True )
                else :
                    await interaction .followup .send (embed =embed ,ephemeral =True )
            except :
                pass 

    @discord .ui .button (label ="Participants",style =discord .ButtonStyle .secondary ,emoji ="👥")
    async def show_participants (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :
            await self .giveaway_cog .show_giveaway_participants (interaction ,self .message_id )
        except Exception as e :
            try :
                embed =discord .Embed (
                color =0xff0000 
                )
                if not interaction .response .is_done ():
                    await interaction .response .send_message (embed =embed ,ephemeral =True )
                else :
                    await interaction .followup .send (embed =embed ,ephemeral =True )
            except :
                pass 

class Giveaway (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    async def cog_load (self )->None :
        try :

            if not await init_database_async ():
                return 


            self .connection =await aiosqlite .connect (db_path )
            self .cursor =await self .connection .cursor ()


            self .connection .row_factory =aiosqlite .Row 


            await self .cursor .execute ("SELECT 1")


            await self .setup_persistent_views ()


            await self .check_for_ended_giveaways ()


            if not self .GiveawayEnd .is_running ():
                self .GiveawayEnd .start ()

        except Exception as e :
            if hasattr (self ,'connection'):
                try :
                    await self .connection .close ()
                except :
                    pass 

    async def setup_persistent_views (self ):
        """Setup persistent views for active giveaways"""
        try :
            await self .cursor .execute ("SELECT guild_id, message_id FROM Giveaway WHERE is_paused = 0")
            active_giveaways =await self .cursor .fetchall ()

            for guild_id ,message_id in active_giveaways :
                view =GiveawayView (self ,guild_id ,message_id )
                self .bot .add_view (view ,message_id =message_id )

        except Exception as e :
            pass 

    async def cog_unload (self )->None :
        try :
            if hasattr (self ,'GiveawayEnd'):
                self .GiveawayEnd .cancel ()
            if hasattr (self ,'connection'):
                await self .connection .close ()
        except Exception as e :
            pass 

    def generate_captcha_code (self ):
        """Generate a random 5-character captcha code"""
        return ''.join (random .choices (string .ascii_uppercase +string .digits ,k =5 ))

    def create_captcha_image (self ,code ):
        """Create a CAPTCHA image with the given code"""
        try :

            width ,height =300 ,100 
            img =Image .new ('RGB',(width ,height ),color ='white')
            draw =ImageDraw .Draw (img )


            try :
                font =ImageFont .truetype ("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",36 )
            except :
                font =ImageFont .load_default ()


            for _ in range (500 ):
                x =random .randint (0 ,width )
                y =random .randint (0 ,height )
                draw .point ((x ,y ),fill =(random .randint (0 ,255 ),random .randint (0 ,255 ),random .randint (0 ,255 )))


            for _ in range (5 ):
                x1 =random .randint (0 ,width )
                y1 =random .randint (0 ,height )
                x2 =random .randint (0 ,width )
                y2 =random .randint (0 ,height )
                draw .line ((x1 ,y1 ,x2 ,y2 ),fill =(random .randint (0 ,255 ),random .randint (0 ,255 ),random .randint (0 ,255 )),width =2 )


            text_bbox =draw .textbbox ((0 ,0 ),code ,font =font )
            text_width =text_bbox [2 ]-text_bbox [0 ]
            text_height =text_bbox [3 ]-text_bbox [1 ]
            text_x =(width -text_width )//2 
            text_y =(height -text_height )//2 


            for i ,char in enumerate (code ):
                char_x =text_x +(i *(text_width //len (code )))
                char_y =text_y +random .randint (-10 ,10 )
                color =(random .randint (0 ,100 ),random .randint (0 ,100 ),random .randint (0 ,100 ))
                draw .text ((char_x ,char_y ),char ,font =font ,fill =color )


            img_bytes =io .BytesIO ()
            img .save (img_bytes ,format ='PNG')
            img_bytes .seek (0 )
            img .close ()
            return img_bytes 

        except Exception as e :

            img =Image .new ('RGB',(300 ,100 ),color ='lightgray')
            draw =ImageDraw .Draw (img )
            font =ImageFont .load_default ()
            draw .text ((50 ,30 ),code ,fill ='black',font =font )

            img_bytes =io .BytesIO ()
            img .save (img_bytes ,format ='PNG')
            img_bytes .seek (0 )
            img .close ()
            return img_bytes 

    async def update_participant_count (self ,guild_id ,message_id ):
        """Update the participant count on the giveaway message"""
        try :

            await self .cursor .execute (
            "SELECT COUNT(*) FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",
            (guild_id ,message_id )
            )
            count_result =await self .cursor .fetchone ()
            participant_count =count_result [0 ]if count_result else 0 


            await self .cursor .execute (
            "SELECT channel_id, prize, winners, ends_at, host_id, config FROM Giveaway WHERE guild_id = ? AND message_id = ?",
            (guild_id ,message_id )
            )
            giveaway_result =await self .cursor .fetchone ()

            if not giveaway_result :
                return 

            channel_id ,prize ,winners ,ends_at ,host_id ,config_str =giveaway_result 
            config =json .loads (config_str )if config_str else {}


            channel =self .bot .get_channel (channel_id )
            if not channel :
                return 

            try :
                message =await channel .fetch_message (message_id )
            except discord .NotFound :
                return 


            view =GiveawayView (self ,guild_id ,message_id )
            view .children [0 ].label =f"Join {participant_count}"


            color =parse_color (config .get ('color','#000000'))
            embed =discord .Embed (
            title =f"🎉 {prize}",
            description =f"**Winners:** {winners}\n**Ends:** <t:{round(ends_at)}:R> (<t:{round(ends_at)}:f>)\n**Host:** <@{host_id}>\n\nClick **Join** to enter!",
            color =color 
            )

            if config .get ('image'):
                embed .set_image (url =config ['image'])
            if config .get ('thumbnail'):
                embed .set_thumbnail (url =config ['thumbnail'])

            embed .set_footer (text ="Ends at",icon_url =self .bot .user .avatar .url )
            embed .timestamp =datetime .datetime .utcfromtimestamp (ends_at )


            requirements =[]


            required_roles =config .get ('required_roles',[])
            if isinstance (required_roles ,str ):
                try :
                    required_roles =[int (required_roles )]
                except :
                    required_roles =[]
            elif not isinstance (required_roles ,list ):
                required_roles =[]


            if config .get ('required_role'):
                try :
                    required_roles .append (int (config ['required_role']))
                except :
                    pass 

            if required_roles :
                guild =self .bot .get_guild (guild_id )
                role_mentions =[]
                for role_id in required_roles :
                    role =guild .get_role (role_id )
                    if role :
                        role_mentions .append (role .mention )

                if role_mentions :
                    role_type =config .get ('required_role_type','any')
                    if role_type =='all':
                        requirements .append (f"🔐 **Required Roles (ALL):** {', '.join(role_mentions)}")
                    else :
                        requirements .append (f"🔐 **Required Role:** {', '.join(role_mentions)}")


            if config .get ('required_level'):
                requirements .append (f"📈 **Level:** {config['required_level']}+")


            if config .get ('required_total_messages'):
                requirements .append (f"💬 **Total Messages:** {config['required_total_messages']}+")

            if config .get ('required_daily_messages'):
                requirements .append (f"📅 **Daily Messages:** {config['required_daily_messages']}+")

            if config .get ('required_weekly_messages'):
                requirements .append (f"📊 **Weekly Messages:** {config['required_weekly_messages']}+")

            if config .get ('required_monthly_messages'):
                requirements .append (f"📈 **Monthly Messages:** {config['required_monthly_messages']}+")


            bypass_role_id =config .get ('requirement_bypass_role')or config .get ('bypass_role')or config .get ('requirements_bypass_role')
            if bypass_role_id :
                try :
                    guild =self .bot .get_guild (guild_id )
                    bypass_role =guild .get_role (int (bypass_role_id ))
                    if bypass_role :
                        requirements .append (f"⭐ **Bypass Role:** {bypass_role.mention}")
                except :
                    pass 


            extra_role_id =config .get ('extra_entries_role')
            extra_count =config .get ('extra_entries_count',1 )
            if extra_role_id and extra_count >0 :
                try :
                    guild =self .bot .get_guild (guild_id )
                    extra_role =guild .get_role (int (extra_role_id ))
                    if extra_role :
                        requirements .append (f"🎯 **Extra Entries:** {extra_role.mention} (+{extra_count} entries)")
                except :
                    pass 


            blacklisted_roles =config .get ('blacklisted_roles',[])
            if blacklisted_roles :
                if isinstance (blacklisted_roles ,str ):
                    try :
                        blacklisted_roles =[int (blacklisted_roles )]
                    except :
                        blacklisted_roles =[]
                elif not isinstance (blacklisted_roles ,list ):
                    blacklisted_roles =[]

                if blacklisted_roles :
                    guild =self .bot .get_guild (guild_id )
                    blacklisted_mentions =[]
                    for role_id in blacklisted_roles :
                        try :
                            role =guild .get_role (int (role_id ))
                            if role :
                                blacklisted_mentions .append (role .mention )
                        except :
                            pass 

                    if blacklisted_mentions :
                        requirements .append (f"❌ **Blacklisted Roles:** {', '.join(blacklisted_mentions)}")

            if requirements :
                embed .add_field (name ="📋 Requirements",value ="\n".join (requirements ),inline =False )

            await message .edit (embed =embed ,view =view )

        except Exception as e :
            pass 

    async def handle_giveaway_join (self ,interaction ,message_id ):
        """Handle user joining/leaving giveaway via button"""
        try :
            await interaction .response .defer (ephemeral =True )
        except discord .InteractionResponded :
            pass 
        except Exception as e :
            return 


        try :
            await self .cursor .execute ("SELECT 1")
        except Exception as e :
            try :
                if hasattr (self ,'connection'):
                    await self .connection .close ()
            except :
                pass 
            try :
                self .connection =await aiosqlite .connect (db_path )
                self .cursor =await self .connection .cursor ()
                self .connection .row_factory =aiosqlite .Row 
            except Exception as e :
                embed =discord .Embed (
                description ="Database connection failed. Please try again.",
                color =0xff0000 
                )
                await interaction .followup .send (embed =embed ,ephemeral =True )
                return 


        await self .cursor .execute ("SELECT config FROM Giveaway WHERE message_id = ? AND guild_id = ?",(message_id ,interaction .guild .id ))
        result =await self .cursor .fetchone ()

        if not result :
            embed =discord .Embed (
            description ="This giveaway no longer exists!",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 

        config =json .loads (result [0 ])if result [0 ]else {}


        await self .cursor .execute ("SELECT entries FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ? AND user_id = ?",
        (interaction .guild .id ,message_id ,interaction .user .id ))
        is_participating =await self .cursor .fetchone ()

        if is_participating :

            leave_view =LeaveConfirmationView (self ,message_id )
            embed =discord .Embed (
            title ="🎉 Leave Giveaway?",
            description ="Are you sure you want to leave this giveaway?",
            color =0xffff00 
            )
            await interaction .followup .send (embed =embed ,view =leave_view ,ephemeral =True )
            return 


        if config .get ('show_captcha',False ):

            captcha_code =self .generate_captcha_code ()
            captcha_image =self .create_captcha_image (captcha_code )

            try :

                modal =CaptchaVerificationModal (self ,message_id ,captcha_code )
                view =CaptchaView (modal )


                file =discord .File (captcha_image ,filename ="captcha.png")
                embed =discord .Embed (
                title ="🔒 CAPTCHA Verification Required",
                description =f"**Server:** {interaction.guild.name}\n\n"
                f"To join this giveaway, please solve the CAPTCHA below.\n"
                f"Click the button to enter your answer.\n\n"
                f"**Note:** The code is case-sensitive!",
                color =0x0099ff 
                )
                embed .set_image (url ="attachment://captcha.png")
                embed .set_footer (text ="CAPTCHA expires in 5 minutes")

                await interaction .user .send (embed =embed ,file =file ,view =view )


                embed =discord .Embed (
                title ="📨 Check Your DMs",
                description ="I've sent you a CAPTCHA in your direct messages.\n\n"
                f"**Steps:**\n"
                f"1. Check your DMs from me\n"
                f"2. Solve the CAPTCHA image\n"
                f"3. Click the button to enter your answer\n\n"
                f"Make sure your DMs are open!",
                color =0x0099ff 
                )
                embed .set_footer (text ="CAPTCHA expires in 5 minutes")
                await interaction .followup .send (embed =embed ,ephemeral =True )

            except discord .Forbidden :
                embed =discord .Embed (
                title ="❌ DMs Disabled",
                description ="I couldn't send you a DM! Please enable DMs from server members and try again.\n\n"
                f"**How to enable DMs:**\n"
                f"1. Right-click on **{interaction.guild.name}**\n"
                f"2. Go to **Privacy Settings**\n"
                f"3. Enable **Direct Messages**\n"
                f"4. Try joining the giveaway again",
                color =0xff0000 
                )
                await interaction .followup .send (embed =embed ,ephemeral =True )
        else :

            await self .handle_giveaway_join_after_captcha (interaction ,message_id )

    async def handle_giveaway_join_after_captcha (self ,interaction ,message_id ):
        """Handle giveaway entry after captcha verification (or when no captcha required)"""

        await self .cursor .execute ("SELECT config FROM Giveaway WHERE message_id = ? AND guild_id = ?",(message_id ,interaction .guild .id ))
        result =await self .cursor .fetchone ()
        config =json .loads (result [0 ])if result and result [0 ]else {}

        can_enter ,reason =await self .check_requirements (interaction .user ,interaction .guild ,config )

        if not can_enter :
            embed =discord .Embed (
            title ="❌ Cannot Enter",
            description =f"You cannot enter this giveaway: {reason}",
            color =0xff0000 
            )
            if interaction .response .is_done ():
                await interaction .followup .send (embed =embed ,ephemeral =True )
            else :
                await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        entries =1 
        extra_role_id =config .get ('extra_entries_role')
        extra_count =config .get ('extra_entries_count',1 )

        if extra_role_id :
            extra_role =interaction .guild .get_role (int (extra_role_id ))
            if extra_role and extra_role in interaction .user .roles :
                entries +=extra_count 


        await self .cursor .execute ("INSERT INTO GiveawayParticipants (guild_id, message_id, user_id, entries) VALUES (?, ?, ?, ?)",
        (interaction .guild .id ,message_id ,interaction .user .id ,entries ))
        await self .connection .commit ()


        await self .update_participant_count (interaction .guild .id ,message_id )

        entry_text =f"with {entries} entries"if entries >1 else ""
        embed =discord .Embed (
        title ="✅ Joined Giveaway",
        description =f"You have successfully joined the giveaway {entry_text}! Good luck!",
        color =0x00ff00 
        )

        if interaction .response .is_done ():
            await interaction .followup .send (embed =embed ,ephemeral =True )
        else :
            await interaction .response .send_message (embed =embed ,ephemeral =True )

    async def show_giveaway_participants (self ,interaction ,message_id ):
        """Show giveaway participants with management options"""
        await interaction .response .defer (ephemeral =True )


        await self .cursor .execute ("SELECT user_id, entries FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",
        (interaction .guild .id ,message_id ))
        participants =await self .cursor .fetchall ()

        if not participants :
            embed =discord .Embed (
            title ="📝 No Participants",
            description ="No participants yet!",
            color =0xffff00 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 


        await self .cursor .execute ("SELECT host_id FROM Giveaway WHERE guild_id = ? AND message_id = ?",
        (interaction .guild .id ,message_id ))
        host_result =await self .cursor .fetchone ()

        is_host =(host_result and host_result [0 ]==interaction .user .id )or interaction .user .guild_permissions .manage_guild 

        if is_host :

            view =ParticipantsView (self ,message_id ,participants )
            await view .show_participants_page (interaction ,show_tags =False )
        else :

            await self .show_simple_participants (interaction ,message_id ,participants )

    async def show_simple_participants (self ,interaction ,message_id ,participants ):
        """Show simple participants list for non-hosts"""

        await self .cursor .execute ("SELECT prize, winners FROM Giveaway WHERE guild_id = ? AND message_id = ?",
        (interaction .guild .id ,message_id ))
        giveaway_info =await self .cursor .fetchone ()

        if not giveaway_info :
            embed =discord .Embed (
            description ="Giveaway not found!",
            color =0xff0000 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )
            return 

        prize ,winners =giveaway_info 


        participant_list =[]
        total_entries =sum (entries for _ ,entries in participants )

        for i ,(user_id ,entries )in enumerate (participants [:20 ],1 ):
            user =interaction .guild .get_member (user_id )
            if user :
                participant_list .append (f"{i}. {user.display_name} (Entries: {entries})")
            else :
                participant_list .append (f"{i}. Unknown User ({user_id}) (Entries: {entries})")

        embed =discord .Embed (
        title =f"🎉 Giveaway Participants",
        description =f"**Prize:** {prize}\n**Winners:** {winners}\n**Total Participants:** {len(participants)}\n**Total Entries:** {total_entries}",
        color =0x00ff00 
        )

        participants_text ="\n".join (participant_list )
        if len (participants )>20 :
            participants_text +=f"\n... and {len(participants) - 20} more"

        embed .add_field (name ="Participants",value =participants_text or "None",inline =False )
        embed .set_footer (text =f"Total: {len(participants)} participants")

        await interaction .followup .send (embed =embed ,ephemeral =True )

    async def check_requirements (self ,user ,guild ,config ):
        """Check if user meets giveaway requirements"""
        if not config :
            return True ,None 

        try :

            if not hasattr (self ,'cursor')or not self .cursor :
                try :
                    self .connection =await aiosqlite .connect (db_path )
                    self .cursor =await self .connection .cursor ()
                    self .connection .row_factory =aiosqlite .Row 
                except Exception as e :
                    pass 
                    return True ,None 


            try :
                await self .cursor .execute ("SELECT 1")
            except Exception as e :
                try :
                    await self .connection .close ()
                except :
                    pass 
                try :
                    self .connection =await aiosqlite .connect (db_path )
                    self .cursor =await self .connection .cursor ()
                    self .connection .row_factory =aiosqlite .Row 
                except Exception as e :
                    pass 
                    return True ,None 


            await self .cursor .execute ("SELECT 1 FROM GiveawayBlacklist WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
            if await self .cursor .fetchone ():
                return False ,"You are blacklisted from giveaways."
        except Exception as e :
            pass 
            return True ,None 


        bypass_role =config .get ('requirement_bypass_role')or config .get ('bypass_role')or config .get ('requirements_bypass_role')
        if bypass_role :
            try :
                role =guild .get_role (int (bypass_role ))
                if role and role in user .roles :
                    return True ,None 
            except (ValueError ,TypeError ):
                pass 


        blacklisted_roles =config .get ('blacklisted_roles',[])
        if blacklisted_roles :
            if isinstance (blacklisted_roles ,str ):
                try :
                    blacklisted_roles =[int (blacklisted_roles )]
                except :
                    blacklisted_roles =[]
            elif not isinstance (blacklisted_roles ,list ):
                blacklisted_roles =[]

            for role_id in blacklisted_roles :
                try :
                    role =guild .get_role (int (role_id ))
                    if role and role in user .roles :
                        return False ,f"You cannot enter this giveaway because you have the {role.name} role."
                except :
                    continue 


        required_roles =config .get ('required_roles',[])
        if isinstance (required_roles ,str ):
            try :
                required_roles =[int (required_roles )]
            except :
                required_roles =[]
        elif not isinstance (required_roles ,list ):
            required_roles =[]


        if config .get ('required_role'):
            try :
                required_roles .append (int (config ['required_role']))
            except :
                pass 

        if required_roles :
            required_role_type =config .get ('required_role_type','any')
            user_role_ids =[role .id for role in user .roles ]

            if required_role_type =='all':

                missing_roles =[]
                for role_id in required_roles :
                    if role_id not in user_role_ids :
                        role =guild .get_role (role_id )
                        if role :
                            missing_roles .append (role .name )

                if missing_roles :
                    return False ,f"You need all of these roles: {', '.join(missing_roles)}"
            else :

                has_required_role =any (role_id in user_role_ids for role_id in required_roles )
                if not has_required_role :
                    role_names =[]
                    for role_id in required_roles :
                        role =guild .get_role (role_id )
                        if role :
                            role_names .append (role .name )

                    if role_names :
                        return False ,f"You need one of these roles: {', '.join(role_names)}"


        required_level =config .get ('required_level')
        if required_level :
            try :

                async with aiosqlite .connect ('db/leveling.db')as level_db :
                    level_cursor =await level_db .cursor ()


                    user_level =0 


                    try :
                        await level_cursor .execute ("SELECT level FROM leveling WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
                        result =await level_cursor .fetchone ()
                        if result :
                            user_level =result [0 ]
                    except :
                        pass 


                    if user_level ==0 :
                        try :
                            await level_cursor .execute ("SELECT xp FROM user_xp WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
                            result =await level_cursor .fetchone ()
                            if result :
                                xp =result [0 ]

                                import math 
                                user_level =int (math .sqrt (xp /100 ))if xp >0 else 0 
                        except :
                            pass 

                    if user_level <required_level :
                        return False ,f"You need to be level {required_level} or higher. You are level {user_level}."
            except Exception as e :
                pass 
                pass 


        message_checks =[
        ('required_daily_messages',1 ,'daily'),
        ('required_weekly_messages',7 ,'weekly'),
        ('required_monthly_messages',30 ,'monthly')
        ]

        for req_key ,days ,period in message_checks :
            required_msgs =config .get (req_key )
            if required_msgs :
                try :

                    async with aiosqlite .connect ('db/tracking.db')as track_db :
                        track_cursor =await track_db .cursor ()
                        since_date =datetime .datetime .now ()-datetime .timedelta (days =days )


                        await track_cursor .execute (
                        "SELECT COUNT(*) FROM user_activity WHERE guild_id = ? AND user_id = ? AND timestamp >= ?",
                        (guild .id ,user .id ,since_date .timestamp ())
                        )
                        result =await track_cursor .fetchone ()
                        user_messages =result [0 ]if result else 0 

                        if user_messages <required_msgs :
                            return False ,f"You need {required_msgs} messages in the last {period}. You have {user_messages}."
                except Exception as e :

                    try :
                        async with aiosqlite .connect ('db/leveling.db')as level_db :
                            level_cursor =await level_db .cursor ()


                            user_messages =0 
                            try :
                                await level_cursor .execute ("SELECT messages FROM leveling WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
                                result =await level_cursor .fetchone ()
                                if result :
                                    user_messages =result [0 ]
                            except :
                                try :
                                    await level_cursor .execute ("SELECT message_count FROM leveling WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
                                    result =await level_cursor .fetchone ()
                                    if result :
                                        user_messages =result [0 ]
                                except :
                                    pass 

                            if user_messages <required_msgs :
                                return False ,f"You need {required_msgs} messages in the last {period}. You have {user_messages}."
                    except Exception as e :
                        pass 
                        pass 


        required_total =config .get ('required_total_messages')
        if required_total :
            try :

                async with aiosqlite .connect ('db/tracking.db')as track_db :
                    track_cursor =await track_db .cursor ()
                    await track_cursor .execute (
                    "SELECT COUNT(*) FROM user_activity WHERE guild_id = ? AND user_id = ?",
                    (guild .id ,user .id )
                    )
                    result =await track_cursor .fetchone ()
                    user_total =result [0 ]if result else 0 

                    if user_total <required_total :
                        return False ,f"You need {required_total} total messages. You have {user_total}."
            except Exception as e :

                try :
                    async with aiosqlite .connect ('db/leveling.db')as level_db :
                        level_cursor =await level_db .cursor ()


                        user_total =0 
                        try :
                            await level_cursor .execute ("SELECT messages FROM leveling WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
                            result =await level_cursor .fetchone ()
                            if result :
                                user_total =result [0 ]
                        except :
                            try :
                                await level_cursor .execute ("SELECT message_count FROM leveling WHERE guild_id = ? AND user_id = ?",(guild .id ,user .id ))
                                result =await level_cursor .fetchone ()
                                if result :
                                    user_total =result [0 ]
                            except :
                                pass 

                        if user_total <required_total :
                            return False ,f"You need {required_total} total messages. You have {user_total}."
                except Exception as e :
                    pass 
                    pass 

        return True ,None 

    async def save_template (self ,guild_id ,name ,data ):
        """Save a giveaway template"""
        try :
            await self .cursor .execute (
            "INSERT OR REPLACE INTO GiveawayTemplates (guild_id, name, data) VALUES (?, ?, ?)",
            (guild_id ,name ,json .dumps (data ))
            )
            await self .connection .commit ()
        except Exception as e :
            pass 

    async def get_template (self ,guild_id ,name ):
        """Get a giveaway template"""
        try :
            await self .cursor .execute ("SELECT data FROM GiveawayTemplates WHERE guild_id = ? AND name = ?",(guild_id ,name ))
            result =await self .cursor .fetchone ()
            if result :
                template_data =json .loads (result [0 ])

                if not isinstance (template_data ,dict ):
                    pass 
                    return None 
                return template_data 
        except Exception as e :
            pass 
        return None 

    async def create_giveaway (self ,ctx ,channel ,duration ,winners ,prize ,template_name =None ,interaction =None ,**kwargs ):
        """Create a new giveaway"""

        await self .cursor .execute ("SELECT COUNT(*) FROM Giveaway WHERE guild_id = ?",(ctx .guild .id ,))
        count =(await self .cursor .fetchone ())[0 ]
        if count >=5 :
            embed =discord .Embed (
            title ="❌ Limit Reached",
            description ="You can only host up to 5 giveaways in this server.",
            color =0xff0000 
            )
            if interaction :
                await interaction .followup .send (embed =embed ,ephemeral =True )
            else :
                await ctx .send (embed =embed )
            return 


        config ={}
        if template_name :
            template_data =await self .get_template (ctx .guild .id ,template_name )
            if template_data :
                config .update (template_data )

                if not kwargs .get ('prize')and template_data .get ('prize'):
                    prize =template_data .get ('prize')
                if not kwargs .get ('winners')and template_data .get ('winners'):
                    winners =template_data .get ('winners')


        config .update (kwargs )

        ends_at =datetime .datetime .now ().timestamp ()+duration 


        color =parse_color (config .get ('color','#000000'))
        embed =discord .Embed (
        title =f"🎉 {prize}",
        description =f"**Winners:** {winners}\n**Ends:** <t:{round(ends_at)}:R> (<t:{round(ends_at)}:f>)\n**Host:** {ctx.author.mention}\n\nClick **Join** to enter!",
        color =color 
        )

        if config .get ('image'):
            embed .set_image (url =config ['image'])
        if config .get ('thumbnail'):
            embed .set_thumbnail (url =config ['thumbnail'])

        embed .set_footer (text ="Ends at",icon_url =self .bot .user .avatar .url )
        embed .timestamp =datetime .datetime .utcfromtimestamp (ends_at )


        requirements =[]


        required_roles =config .get ('required_roles',[])
        if isinstance (required_roles ,str ):
            try :
                required_roles =[int (required_roles )]
            except :
                required_roles =[]
        elif not isinstance (required_roles ,list ):
            required_roles =[]


        if config .get ('required_role'):
            try :
                required_roles .append (int (config ['required_role']))
            except :
                pass 

        if required_roles :
            role_mentions =[]
            for role_id in required_roles :
                role =ctx .guild .get_role (role_id )
                if role :
                    role_mentions .append (role .mention )

            if role_mentions :
                role_type =config .get ('required_role_type','any')
                if role_type =='all':
                    requirements .append (f"🔐 **Required Roles (ALL):** {', '.join(role_mentions)}")
                else :
                    requirements .append (f"🔐 **Required Role:** {', '.join(role_mentions)}")


        if config .get ('required_level'):
            requirements .append (f"📈 **Level:** {config['required_level']}+")


        if config .get ('required_total_messages'):
            requirements .append (f"💬 **Total Messages:** {config['required_total_messages']}+")


        bypass_role_id =config .get ('requirement_bypass_role')or config .get ('bypass_role')or config .get ('requirements_bypass_role')
        if bypass_role_id :
            try :
                bypass_role =ctx .guild .get_role (int (bypass_role_id ))
                if bypass_role :
                    requirements .append (f"⭐ **Bypass Role:** {bypass_role.mention}")
            except :
                pass 


        extra_role_id =config .get ('extra_entries_role')
        extra_count =config .get ('extra_entries_count',1 )
        if extra_role_id and extra_count >0 :
            try :
                extra_role =ctx .guild .get_role (int (extra_role_id ))
                if extra_role :
                    requirements .append (f"🎯 **Extra Entries:** {extra_role.mention} (+{extra_count} entries)")
            except :
                pass 

        if requirements :
            embed .add_field (name ="📋 Requirements",value ="\n".join (requirements ),inline =False )


        content =config .get ('giveaway_create_message',"🎉 **GIVEAWAY** 🎉")


        if interaction :
            message =await channel .send (content ,embed =embed )
        else :
            message =await channel .send (content ,embed =embed )
            try :
                await ctx .message .delete ()
            except :
                pass 


        view =GiveawayView (self ,ctx .guild .id ,message .id )
        view .children [0 ].label ="Join 0"
        await message .edit (view =view )

        if interaction :
            embed =discord .Embed (
            title ="✅ Giveaway Created",
            description =f"Giveaway created in {channel.mention}!",
            color =0x00ff00 
            )
            await interaction .followup .send (embed =embed ,ephemeral =True )


        try :
            await self .cursor .execute (
            "INSERT INTO Giveaway (guild_id, host_id, start_time, ends_at, prize, winners, message_id, channel_id, config) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (ctx .guild .id ,ctx .author .id ,datetime .datetime .now ().timestamp (),ends_at ,prize ,winners ,message .id ,channel .id ,json .dumps (config ))
            )
            await self .connection .commit ()
        except Exception as e :
            embed =discord .Embed (
            color =0xff0000 
            )
            if interaction :
                await interaction .followup .send (embed =embed ,ephemeral =True )
            else :
                await ctx .send (embed =embed )
            return 

    async def check_for_ended_giveaways (self ):
        await self .cursor .execute ("SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id, config FROM Giveaway WHERE ends_at <= ? AND is_paused = 0",(datetime .datetime .now ().timestamp (),))
        ended_giveaways =await self .cursor .fetchall ()
        for giveaway in ended_giveaways :
            await self .end_giveaway (giveaway [1 ],giveaway [2 ])

    async def end_giveaway (self ,guild_id ,message_id ,manual =False ):
        """End a giveaway and select winners"""

        giveaway_key =f"{guild_id}_{message_id}"


        if not hasattr (self ,'_processing_giveaways'):
            self ._processing_giveaways =set ()

        if giveaway_key in self ._processing_giveaways :
            pass 
            return 

        self ._processing_giveaways .add (giveaway_key )

        try :

            await self .cursor .execute ("BEGIN IMMEDIATE TRANSACTION")


            await self .cursor .execute (
            "UPDATE Giveaway SET is_processing = 1 WHERE guild_id = ? AND message_id = ? AND is_processing = 0",
            (guild_id ,message_id )
            )

            if self .cursor .rowcount ==0 :

                await self .cursor .execute ("ROLLBACK")
                pass 
                return 


            await self .cursor .execute (
            "SELECT channel_id, prize, winners, host_id, config FROM Giveaway WHERE guild_id = ? AND message_id = ?",
            (guild_id ,message_id )
            )
            giveaway_result =await self .cursor .fetchone ()

            if not giveaway_result :
                await self .cursor .execute ("ROLLBACK")
                return 


            await self .cursor .execute (
            "DELETE FROM Giveaway WHERE guild_id = ? AND message_id = ?",
            (guild_id ,message_id )
            )

            await self .cursor .execute ("COMMIT")

            channel_id ,prize ,winners_count ,host_id ,config_str =giveaway_result 
            config =json .loads (config_str )if config_str else {}


            await self .cursor .execute ("SELECT user_id, entries FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",
            (guild_id ,message_id ))
            participants =await self .cursor .fetchall ()

            if not participants :

                guild =self .bot .get_guild (guild_id )
                channel =guild .get_channel (channel_id )if guild else None 

                if channel :
                    embed =discord .Embed (
                    title ="🎉 Giveaway Ended",
                    description =f"**Prize:** {prize}\n**Winners:** No participants!",
                    color =0xff0000 
                    )
                    await channel .send (embed =embed )
                return 


            weighted_participants =[]
            for user_id ,entries in participants :
                for _ in range (entries ):
                    weighted_participants .append (user_id )


            import random 
            selected_winners =[]
            winners_count =min (winners_count ,len (participants ))

            for _ in range (winners_count ):
                if weighted_participants :
                    winner =random .choice (weighted_participants )
                    selected_winners .append (winner )

                    weighted_participants =[uid for uid in weighted_participants if uid !=winner ]


            guild =self .bot .get_guild (guild_id )
            channel =guild .get_channel (channel_id )if guild else None 

            if not channel :
                return 


            try :
                message =await channel .fetch_message (message_id )


                end_color =parse_color (config .get ('end_color','#ff0000'))
                embed =discord .Embed (
                title =f"🎉 {prize}",
                description =f"**Winners:** {', '.join([f'<@{uid}>' for uid in selected_winners]) if selected_winners else 'No winners'}\n**Ended:** <t:{round(t.time())}:R>\n**Host:** <@{host_id}>",
                color =end_color 
                )

                if config .get ('image'):
                    embed .set_image (url =config ['image'])
                if config .get ('thumbnail'):
                    embed .set_thumbnail (url =config ['thumbnail'])

                embed .set_footer (text ="Giveaway Ended",icon_url =self .bot .user .avatar .url )


                await message .edit (embed =embed ,view =None )
            except discord .NotFound :
                pass 


            if selected_winners :
                winner_mentions =', '.join ([f'<@{uid}>'for uid in selected_winners ])
                embed =discord .Embed (
                title ="🎉 Congratulations!",
                description =f"**Winners:** {winner_mentions}\n**Prize:** {prize}",
                color =0x00ff00 
                )
                await channel .send (embed =embed )


                dm_message =config .get ('giveaway_winners_dm_message')
                if dm_message :

                    dm_message =dm_message .replace ('{prize}',prize )
                    dm_message =dm_message .replace ('{server}',guild .name )
                else :
                    dm_message =f"🎉 Congratulations! You won **{prize}** in {guild.name}!\n\nPlease contact the server administrators to claim your prize."

                for winner_id in selected_winners :
                    try :
                        winner =guild .get_member (winner_id )
                        if winner :
                            dm_embed =discord .Embed (
                            title ="🎉 You Won a Giveaway!",
                            description =dm_message ,
                            color =0x00ff00 ,
                            timestamp =datetime .datetime .utcnow ()
                            )
                            dm_embed .add_field (name ="🏆 Prize",value =prize ,inline =True )
                            dm_embed .add_field (name ="🏠 Server",value =guild .name ,inline =True )
                            dm_embed .add_field (name ="📅 Won On",value =f"<t:{round(t.time())}:F>",inline =True )

                            if guild .icon :
                                dm_embed .set_thumbnail (url =guild .icon .url )

                            dm_embed .set_footer (text =f"Message ID: {message_id}")

                            await winner .send (embed =dm_embed )
                            pass 
                    except discord .Forbidden :
                        pass 

                        try :
                            await channel .send (f"<@{winner_id}> I couldn't send you a DM! Please enable DMs from server members to receive your prize information.",delete_after =30 )
                        except :
                            pass 
                    except Exception as e :
                        pass 


            await self .cursor .execute ("DELETE FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",(guild_id ,message_id ))
            await self .connection .commit ()
            pass 

        except Exception as e :
            pass 

            try :
                await self .cursor .execute ("ROLLBACK")
            except :
                pass 

            try :
                await self .cursor .execute ("DELETE FROM Giveaway WHERE guild_id = ? AND message_id = ?",(guild_id ,message_id ))
                await self .cursor .execute ("DELETE FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",(guild_id ,message_id ))
                await self .connection .commit ()
                pass 
            except Exception as e :
                pass 
        finally :

            if hasattr (self ,'_processing_giveaways'):
                self ._processing_giveaways .discard (giveaway_key )

    @tasks .loop (seconds =60 )
    async def GiveawayEnd (self ):

        if not hasattr (self ,'_task_lock'):
            self ._task_lock =asyncio .Lock ()

        if self ._task_lock .locked ():
            pass 
            return 

        async with self ._task_lock :
            try :
                if not hasattr (self ,'cursor')or not self .cursor or not hasattr (self ,'connection'):
                    return 


                try :
                    await self .cursor .execute ("SELECT 1")
                except Exception as e :
                    try :
                        if hasattr (self ,'connection'):
                            await self .connection .close ()
                    except :
                        pass 
                    self .connection =await aiosqlite .connect (db_path )
                    self .cursor =await self .connection .cursor ()
                    self .connection .row_factory =aiosqlite .Row 


                current_time =datetime .datetime .now ().timestamp ()
                await self .cursor .execute (
                "SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id, config FROM Giveaway WHERE ends_at <= ? AND is_paused = 0 AND is_processing = 0 ORDER BY ends_at ASC LIMIT 1",
                (current_time ,)
                )
                ended_giveaways =await self .cursor .fetchall ()

                if not ended_giveaways :
                    return 


                if not hasattr (self ,'_processing_giveaways'):
                    self ._processing_giveaways =set ()


                giveaway =ended_giveaways [0 ]
                giveaway_key =f"{giveaway[1]}_{giveaway[2]}"


                if giveaway_key in self ._processing_giveaways :
                    pass 
                    return 

                try :
                    await self .end_giveaway (giveaway [1 ],giveaway [2 ])
                    pass 

                except Exception as e :
                    pass 

                    try :
                        await self .cursor .execute ("BEGIN IMMEDIATE TRANSACTION")
                        await self .cursor .execute ("DELETE FROM Giveaway WHERE guild_id = ? AND message_id = ?",(giveaway [1 ],giveaway [2 ]))
                        await self .cursor .execute ("DELETE FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",(giveaway [1 ],giveaway [2 ]))
                        await self .cursor .execute ("COMMIT")
                        pass 
                    except Exception as e :
                        pass 
                        try :
                            await self .cursor .execute ("ROLLBACK")
                        except :
                            pass 
                    finally :

                        if hasattr (self ,'_processing_giveaways'):
                            self ._processing_giveaways .discard (giveaway_key )

            except Exception as e :
                pass 

                try :
                    if hasattr (self ,'connection'):
                        await self .connection .close ()
                    self .connection =await aiosqlite .connect (db_path )
                    self .cursor =await self .connection .cursor ()
                    self .connection .row_factory =aiosqlite .Row 
                except Exception as e :
                    pass 

    @GiveawayEnd .before_loop 
    async def before_giveaway_end (self ):
        await self .bot .wait_until_ready ()

        try :
            await self .cursor .execute ("UPDATE Giveaway SET is_processing = 0 WHERE is_processing = 1")
            await self .connection .commit ()
            pass 
        except Exception as e :
            pass 

    async def cleanup_stuck_giveaways (self ):
        """Clean up giveaways that might be stuck in processing state"""
        try :

            await self .cursor .execute (
            "UPDATE Giveaway SET is_processing = 0 WHERE is_processing = 1 AND ends_at < ?",
            (datetime .datetime .now ().timestamp ()-300 ,)
            )
            if self .cursor .rowcount >0 :
                await self .connection .commit ()
                pass 
        except Exception as e :
            pass 


    giveaway_group =app_commands .Group (name ="giveaway",description ="Giveaway commands")

    @giveaway_group .command (name ="create",description ="Create a new giveaway with advanced configuration")
    @app_commands .describe (
    duration ="Duration (e.g., 1h, 2d, 3w) - Optional if using template",
    winners ="Number of winners - Optional if using template",
    prize ="Prize description - Optional if using template",
    use_template ="Template to use as base"
    )
    async def slash_create (
    self ,interaction :discord .Interaction ,
    duration :str =None ,
    winners :int =None ,
    prize :str =None ,
    use_template :str =None 
    ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        giveaway_data ={}


        if use_template :
            template_data =await self .get_template (interaction .guild .id ,use_template )
            if template_data :
                giveaway_data .update (template_data )
            else :
                embed =discord .Embed (
                title ="❌ Template Not Found",
                description =f"Template '{use_template}' not found!",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 


        if duration :
            giveaway_data ['duration']=duration 
        if winners is not None :
            giveaway_data ['winners']=winners 
        if prize :
            giveaway_data ['prize']=prize 


        if 'winners'not in giveaway_data :
            giveaway_data ['winners']=1 


        setup_view =GiveawaySetupView (giveaway_data ,self ,interaction .user ,interaction .guild ,is_template =False )
        edit_view =GiveawayEditView (giveaway_data ,setup_view .setup_callback ,interaction .user ,interaction .guild ,is_template =False ,timeout_duration =900 )


        preview_embed =GiveawayPreviewGenerator .create_preview_embed (
        giveaway_data ,interaction .user ,interaction .guild 
        )


        create_msg =giveaway_data .get ('giveaway_create_message','🎉 **GIVEAWAY** 🎉')
        content =f"**Preview:** {create_msg}"

        await interaction .response .send_message (
        content =content ,
        embed =preview_embed ,
        view =edit_view ,
        ephemeral =False 
        )

    @giveaway_group .command (name ="end",description ="End a giveaway early")
    @app_commands .describe (message_id ="Giveaway message ID")
    async def slash_end (self ,interaction :discord .Interaction ,message_id :str ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        try :
            msg_id =int (message_id )
        except ValueError :
            embed =discord .Embed (
            title ="❌ Invalid Input",
            description ="Invalid message ID!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        await self .cursor .execute ('SELECT ends_at, guild_id, message_id, host_id, winners, prize, channel_id, config FROM Giveaway WHERE message_id = ?',(msg_id ,))
        giveaway =await self .cursor .fetchone ()

        if not giveaway :
            embed =discord .Embed (
            title ="❌ Not Found",
            description ="Giveaway not found!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        await interaction .response .defer ()
        await self .end_giveaway (giveaway [1 ],giveaway [2 ])

        embed =discord .Embed (
        title ="✅ Giveaway Ended",
        description ="Giveaway ended successfully!",
        color =0x00ff00 
        )
        await interaction .followup .send (embed =embed ,ephemeral =True )

    @giveaway_group .command (name ="reroll",description ="Reroll a giveaway")
    @app_commands .describe (message_id ="Giveaway message ID")
    async def slash_reroll (self ,interaction :discord .Interaction ,message_id :str ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        try :
            msg_id =int (message_id )
            message =await interaction .channel .fetch_message (msg_id )
        except (ValueError ,discord .NotFound ):
            embed =discord .Embed (
            title ="❌ Invalid Input",
            description ="Invalid message ID or message not found!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        if message .author !=self .bot .user :
            embed =discord .Embed (
            title ="❌ Invalid Message",
            description ="This is not a giveaway message!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        await self .cursor .execute ("SELECT 1 FROM Giveaway WHERE message_id = ?",(msg_id ,))
        if await self .cursor .fetchone ():
            embed =discord .Embed (
            title ="❌ Still Active",
            description ="This giveaway is still active! Use `/giveaway end` first.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        try :

            await self .cursor .execute ("SELECT user_id, entries FROM GiveawayParticipants WHERE guild_id = ? AND message_id = ?",
            (interaction .guild .id ,msg_id ))
            participants =await self .cursor .fetchall ()

            if not participants :
                embed =discord .Embed (
                title ="❌ No Participants",
                description ="No participants to reroll!",
                color =0xff0000 
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 


            weighted_users =[]
            for user_id ,entries in participants :
                weighted_users .extend ([user_id ]*entries )

            winner =random .choice (weighted_users )

            embed =discord .Embed (
            title ="🎉 New Winner!",
            description =f"Congratulations <@{winner}>!",
            color =0x00ff00 
            )
            await interaction .response .send_message (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

    @giveaway_group .command (name ="list",description ="List active giveaways")
    async def slash_list (self ,interaction :discord .Interaction ):
        await self .cursor .execute ("SELECT prize, ends_at, winners, message_id, channel_id FROM Giveaway WHERE guild_id = ?",(interaction .guild .id ,))
        giveaways =await self .cursor .fetchall ()

        if not giveaways :
            embed =discord .Embed (
            title ="📝 No Active Giveaways",
            description ="No active giveaways found.",
            color =0xffff00 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        embed =discord .Embed (title ="🎉 Active Giveaways",color =0x00ff00 )
        for prize ,ends_at ,winners ,message_id ,channel_id in giveaways :
            embed .add_field (
            name =prize ,
            value =f"**Ends:** <t:{int(ends_at)}:R>\n**Winners:** {winners}\n**Channel:** <#{channel_id}>\n[Jump to Message](https://discord.com/channels/{interaction.guild.id}/{channel_id}/{message_id})",
            inline =False 
            )

        await interaction .response .send_message (embed =embed ,ephemeral =True )


    template_group =app_commands .Group (name ="template",description ="Template commands",parent =giveaway_group )

    @template_group .command (name ="create",description ="Create a giveaway template with interactive setup")
    @app_commands .describe (template_name ="Template name")
    async def slash_template_create (
    self ,interaction :discord .Interaction ,
    template_name :str 
    ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 


        template_data ={
        'template_name':template_name ,
        'winners':1 
        }


        setup_view =GiveawaySetupView (template_data ,self ,interaction .user ,interaction .guild ,is_template =True )
        edit_view =GiveawayEditView (template_data ,setup_view .setup_callback ,interaction .user ,interaction .guild ,is_template =True ,timeout_duration =900 )


        preview_embed =GiveawayPreviewGenerator .create_preview_embed (
        template_data ,interaction .user ,interaction .guild 
        )


        create_msg =template_data .get ('giveaway_create_message','🎉 **GIVEAWAY** 🎉')
        content =f"**Preview:** {create_msg}"

        await interaction .response .send_message (
        content =content ,
        embed =preview_embed ,
        view =edit_view ,
        ephemeral =False 
        )

    @template_group .command (name ="list",description ="List saved templates")
    async def slash_template_list (self ,interaction :discord .Interaction ):
        await self .cursor .execute ("SELECT name FROM GiveawayTemplates WHERE guild_id = ?",(interaction .guild .id ,))
        templates =await self .cursor .fetchall ()

        if not templates :
            embed =discord .Embed (
            title ="📝 No Templates",
            description ="No templates saved.",
            color =0xffff00 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        template_list ="\n".join ([f"• `{t[0]}`"for t in templates ])
        embed =discord .Embed (title ="📋 Saved Templates",description =template_list ,color =0x0099ff )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

    @template_group .command (name ="delete",description ="Delete a template")
    @app_commands .describe (name ="Template name")
    async def slash_template_delete (self ,interaction :discord .Interaction ,name :str ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        await self .cursor .execute ("DELETE FROM GiveawayTemplates WHERE guild_id = ? AND name = ?",(interaction .guild .id ,name ))

        if self .cursor .rowcount >0 :
            await self .connection .commit ()
            embed =discord .Embed (
            title ="✅ Template Deleted",
            description =f"Template `{name}` deleted successfully!",
            color =0x00ff00 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        else :
            embed =discord .Embed (
            title ="❌ Not Found",
            description =f"Template `{name}` not found!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )


    blacklist_group =app_commands .Group (name ="blacklist",description ="Blacklist commands",parent =giveaway_group )

    @blacklist_group .command (name ="add",description ="Add user to giveaway blacklist")
    @app_commands .describe (user ="User to blacklist")
    async def slash_blacklist_add (self ,interaction :discord .Interaction ,user :discord .Member ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        await self .cursor .execute ("INSERT OR IGNORE INTO GiveawayBlacklist (guild_id, user_id) VALUES (?, ?)",(interaction .guild .id ,user .id ))
        await self .connection .commit ()

        embed =discord .Embed (
        title ="✅ User Blacklisted",
        description =f"{user.mention} has been blacklisted from giveaways.",
        color =0x00ff00 
        )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

    @blacklist_group .command (name ="remove",description ="Remove user from giveaway blacklist")
    @app_commands .describe (user ="User to remove from blacklist")
    async def slash_blacklist_remove (self ,interaction :discord .Interaction ,user :discord .Member ):
        if not interaction .user .guild_permissions .manage_guild :
            embed =discord .Embed (
            title ="❌ Missing Permissions",
            description ="You need Manage Server permission!",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        await self .cursor .execute ("DELETE FROM GiveawayBlacklist WHERE guild_id = ? AND user_id = ?",(interaction .guild .id ,user .id ))

        if self .cursor .rowcount >0 :
            await self .connection .commit ()
            embed =discord .Embed (
            title ="✅ User Removed",
            description =f"{user.mention} has been removed from the giveaway blacklist.",
            color =0x00ff00 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
        else :
            embed =discord .Embed (
            title ="❌ Not Blacklisted",
            description =f"{user.mention} was not blacklisted.",
            color =0xff0000 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

    @blacklist_group .command (name ="list",description ="List blacklisted users")
    async def slash_blacklist_list (self ,interaction :discord .Interaction ):
        await self .cursor .execute ("SELECT user_id FROM GiveawayBlacklist WHERE guild_id = ?",(interaction .guild .id ,))
        blacklisted =await self .cursor .fetchall ()

        if not blacklisted :
            embed =discord .Embed (
            title ="📝 No Blacklisted Users",
            description ="No users are blacklisted.",
            color =0xffff00 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )
            return 

        users =[]
        for user_id ,in blacklisted :
            user =interaction .guild .get_member (user_id )
            if user :
                users .append (f"• {user.mention} ({user.id})")

        embed =discord .Embed (title ="🚫 Blacklisted Users",description ="\n".join (users )or "No valid users found",color =0xff0000 )
        await interaction .response .send_message (embed =embed ,ephemeral =True )

    @commands .Cog .listener ("on_message_delete")
    async def on_giveaway_message_delete (self ,message ):
        if message .author !=self .bot .user :
            return 

        await self .cursor .execute ("SELECT message_id FROM Giveaway WHERE guild_id = ? AND message_id = ?",(message .guild .id ,message .id ))
        result =await self .cursor .fetchone ()

        if result :
            await self .cursor .execute ("DELETE FROM Giveaway WHERE channel_id = ? AND message_id = ? AND guild_id = ?",(message .channel .id ,message .id ,message .guild .id ))
            await self .cursor .execute ("DELETE FROM GiveawayParticipants WHERE message_id = ? AND guild_id = ?",(message .id ,message .guild .id ))
            await self .connection .commit ()

async def setup (bot ):
    await bot .add_cog (Giveaway (bot ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""