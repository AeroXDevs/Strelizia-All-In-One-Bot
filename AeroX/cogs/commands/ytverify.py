import discord 
from discord .ext import commands 
from discord import app_commands 
import aiosqlite 
import os 
import json 
import asyncio 
import logging 
from datetime import datetime ,timezone ,timedelta 
from typing import Optional ,Union ,Dict ,Any 
from utils .Tools import *


try :
    import google .generativeai as genai 
    GEMINI_AVAILABLE =True 
except ImportError :
    GEMINI_AVAILABLE =False 


logger =logging .getLogger ('discord')

DATABASE_PATH ='db/ytverify.db'


COLORS ={
'primary':0x000000 ,
'success':0x57F287 ,
'warning':0xFEE75C ,
'error':0xED4245 ,
'info':0x5865F2 
}

class ChannelNameModal (discord .ui .Modal ):
    """Modal for entering YouTube channel name"""

    def __init__ (self ,view ):
        super ().__init__ (title ="YouTube Channel Name")
        self .view =view 

        self .channel_name =discord .ui .TextInput (
        label ="YouTube Channel Name",
        placeholder ="Enter the YouTube channel name to verify against",
        max_length =100 ,
        required =True 
        )
        self .add_item (self .channel_name )

    async def on_submit (self ,interaction :discord .Interaction ):
        self .view .setup_data ['channel_name']=self .channel_name .value 
        await interaction .response .send_message (
        f"<:icon_tick:1372375089668161597> YouTube channel set to: **{self.channel_name.value}**",
        ephemeral =True 
        )
        await self .view .update_embed (interaction )

class CustomChannelModal (discord .ui .Modal ):
    """Modal for custom channel input via ID or mention"""

    def __init__ (self ,view ):
        super ().__init__ (title ="Custom Channel")
        self .view =view 

        self .channel_input =discord .ui .TextInput (
        label ="Channel ID or Mention",
        placeholder ="#channel or 123456789012345678",
        max_length =100 ,
        required =True 
        )
        self .add_item (self .channel_input )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :

            channel_id =self .channel_input .value .strip ()
            if channel_id .startswith ('<#')and channel_id .endswith ('>'):
                channel_id =channel_id [2 :-1 ]
            elif channel_id .startswith ('#'):

                if interaction .guild :
                    channel =discord .utils .get (interaction .guild .channels ,name =channel_id [1 :])
                    if channel and isinstance (channel ,discord .TextChannel ):
                        self .view .setup_data ['verification_channel']=channel 
                        await interaction .response .send_message (
                        f"<:icon_tick:1372375089668161597> Verification channel set to {channel.mention}",
                        ephemeral =True 
                        )
                        await self .view .update_embed (interaction )
                        return 
                    else :
                        await interaction .response .send_message (
                        "<:icon_cross:1372375094336425986> Channel not found with that name.",
                        ephemeral =True 
                        )
                        return 

            if interaction .guild :
                channel =interaction .guild .get_channel (int (channel_id ))
                if not channel or not isinstance (channel ,discord .TextChannel ):
                    await interaction .response .send_message (
                    "<:icon_cross:1372375094336425986> Invalid channel. Please provide a valid text channel.",
                    ephemeral =True 
                    )
                    return 

                self .view .setup_data ['verification_channel']=channel 
                await interaction .response .send_message (
                f"<:icon_tick:1372375089668161597> Verification channel set to {channel.mention}",
                ephemeral =True 
                )
                await self .view .update_embed (interaction )

        except ValueError :
            await interaction .response .send_message (
            "<:icon_cross:1372375094336425986> Invalid channel ID format.",
            ephemeral =True 
            )

class CustomRoleModal (discord .ui .Modal ):
    """Modal for custom role input via ID or mention"""

    def __init__ (self ,view ):
        super ().__init__ (title ="Custom Role")
        self .view =view 

        self .role_input =discord .ui .TextInput (
        label ="Role ID, Mention, or Name",
        placeholder ="@role, 123456789012345678, or RoleName",
        max_length =100 ,
        required =True 
        )
        self .add_item (self .role_input )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :

            role_input =self .role_input .value .strip ()
            role =None 

            if interaction .guild :
                if role_input .startswith ('<@&')and role_input .endswith ('>'):

                    role_id =role_input [3 :-1 ]
                    role =interaction .guild .get_role (int (role_id ))
                elif role_input .isdigit ():

                    role =interaction .guild .get_role (int (role_input ))
                else :

                    role =discord .utils .get (interaction .guild .roles ,name =role_input )

                if not role :
                    await interaction .response .send_message (
                    "<:icon_cross:1372375094336425986> Role not found. Please check the role name, ID, or mention.",
                    ephemeral =True 
                    )
                    return 

                self .view .setup_data ['verified_role']=role 
                await interaction .response .send_message (
                f"<:icon_tick:1372375089668161597> Verified role set to {role.mention}",
                ephemeral =True 
                )
                await self .view .update_embed (interaction )

        except ValueError :
            await interaction .response .send_message (
            "<:icon_cross:1372375094336425986> Invalid role format.",
            ephemeral =True 
            )

class ChannelSelectMenu (discord .ui .ChannelSelect ):
    """Select menu for verification channel"""

    def __init__ (self ,view ):
        self .setup_view =view 

        super ().__init__ (
        placeholder ="📍 Select verification channel or choose custom...",
        channel_types =[discord .ChannelType .text ],
        min_values =0 ,
        max_values =1 ,
        row =0 
        )


        self ._custom_option_added =False 

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .setup_view .ctx .user :
            await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
            return 

        if self .values :
            channel =self .values [0 ]
            self .setup_view .setup_data ['verification_channel']=channel 
            await interaction .response .send_message (
            f"<:icon_tick:1372375089668161597> Verification channel set to: {channel.mention}",
            ephemeral =True 
            )
            await self .setup_view .update_embed ()

class RoleSelectMenu (discord .ui .RoleSelect ):
    """Select menu for verified role"""

    def __init__ (self ,view ):
        self .setup_view =view 

        super ().__init__ (
        placeholder ="🎭 Select verified role or choose custom...",
        min_values =0 ,
        max_values =1 ,
        row =1 
        )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .setup_view .ctx .user :
            await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
            return 

        if self .values :
            role =self .values [0 ]
            self .setup_view .setup_data ['verified_role']=role 
            await interaction .response .send_message (
            f"<:icon_tick:1372375089668161597> Verified role set to: {role.mention}",
            ephemeral =True 
            )
            await self .setup_view .update_embed ()

class CustomOptionsSelect (discord .ui .Select ):
    """Select menu for custom options"""

    def __init__ (self ,view ):
        self .setup_view =view 

        options =[
        discord .SelectOption (
        label ="Custom Channel (Type ID/Mention)",
        description ="Enter channel manually via text input",
        emoji ="📝",
        value ="custom_channel"
        ),
        discord .SelectOption (
        label ="Custom Role (Type ID/Mention)",
        description ="Enter role manually via text input",
        emoji ="📝",
        value ="custom_role"
        )
        ]

        super ().__init__ (
        placeholder ="⚙️ Custom options (type in chat)...",
        options =options ,
        min_values =0 ,
        max_values =1 ,
        row =2 
        )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .setup_view .ctx .user :
            await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
            return 

        selected =self .values [0 ]

        if selected =="custom_channel":
            modal =CustomChannelModal (self .setup_view )
            await interaction .response .send_modal (modal )
        elif selected =="custom_role":
            modal =CustomRoleModal (self .setup_view )
            await interaction .response .send_modal (modal )

class ChannelNameButton (discord .ui .Button ):
    """Button to set YouTube channel name"""

    def __init__ (self ,view ):
        self .setup_view =view 
        super ().__init__ (
        label ="📺 Set YouTube Channel Name",
        style =discord .ButtonStyle .primary ,
        row =3 
        )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .setup_view .ctx .user :
            await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
            return 

        modal =ChannelNameModal (self .setup_view )
        await interaction .response .send_modal (modal )

class ConfirmSetupButton (discord .ui .Button ):
    """Button to confirm and complete setup"""

    def __init__ (self ,view ):
        self .setup_view =view 
        super ().__init__ (
        label ="✅ Complete Setup",
        style =discord .ButtonStyle .success ,
        row =3 
        )

    async def callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .setup_view .ctx .user :
            await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
            return 


        if not all ([
        self .setup_view .setup_data .get ('channel_name'),
        self .setup_view .setup_data .get ('verification_channel'),
        self .setup_view .setup_data .get ('verified_role')
        ]):
            await interaction .response .send_message (
            "<:icon_cross:1372375094336425986> Please configure all required settings first:\n"
            "• YouTube Channel Name\n"
            "• Verification Channel\n"
            "• Verified Role",
            ephemeral =True 
            )
            return 

        await self .setup_view .complete_setup (interaction )
        if interaction .user !=self ._parent_view .ctx .user :
            await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
            return 

        selected =self .values [0 ]

        if selected =="channel_name":
            modal =ChannelNameModal (self ._parent_view )
            await interaction .response .send_modal (modal )

        elif selected =="verification_channel":

            temp_view =discord .ui .View (timeout =60 )

            class VerificationChannelSelect (discord .ui .ChannelSelect ):
                def __init__ (self ,parent_view ):
                    self .parent_view =parent_view 
                    super ().__init__ (
                    placeholder ="Select verification channel",
                    channel_types =[discord .ChannelType .text ],
                    max_values =1 
                    )

                async def callback (self ,interaction :discord .Interaction ):
                    channel =self .values [0 ]
                    self .parent_view .setup_data ['verification_channel']=channel 
                    await interaction .response .send_message (
                    f"<:icon_tick:1372375089668161597> Verification channel set to {channel.mention}",
                    ephemeral =True 
                    )
                    await self .parent_view .update_embed (interaction )

            temp_view .add_item (VerificationChannelSelect (self ._parent_view ))
            await interaction .response .send_message (
            "Select the channel where users will upload screenshots:",
            view =temp_view ,
            ephemeral =True 
            )

        elif selected =="verified_role":

            temp_view =discord .ui .View (timeout =60 )

            class VerifiedRoleSelect (discord .ui .RoleSelect ):
                def __init__ (self ,parent_view ):
                    self .parent_view =parent_view 
                    super ().__init__ (
                    placeholder ="Select verified role",
                    max_values =1 
                    )

                async def callback (self ,interaction :discord .Interaction ):
                    role =self .values [0 ]
                    self .parent_view .setup_data ['verified_role']=role 
                    await interaction .response .send_message (
                    f"<:icon_tick:1372375089668161597> Verified role set to {role.mention}",
                    ephemeral =True 
                    )
                    await self .parent_view .update_embed (interaction )

            temp_view .add_item (VerifiedRoleSelect (self ._parent_view ))
            await interaction .response .send_message (
            "Select the role to assign to verified users:",
            view =temp_view ,
            ephemeral =True 
            )

        elif selected =="custom_channel":
            modal =CustomChannelModal (self ._parent_view )
            await interaction .response .send_modal (modal )

        elif selected =="custom_role":
            modal =CustomRoleModal (self ._parent_view )
            await interaction .response .send_modal (modal )

class YouTubeVerificationSetupView (discord .ui .View ):
    """Elegant setup view for YouTube verification system"""

    def __init__ (self ,ctx ):
        super ().__init__ (timeout =300 )
        self .ctx =ctx 
        self .setup_data ={}
        self .original_message =None 


        self .add_item (ChannelSelectMenu (self ))
        self .add_item (RoleSelectMenu (self ))
        self .add_item (CustomOptionsSelect (self ))
        self .add_item (ChannelNameButton (self ))
        self .add_item (ConfirmSetupButton (self ))

    async def update_embed (self ,interaction :discord .Interaction ):
        """Update the setup embed with current configuration"""
        embed =discord .Embed (
        title ="📺 YouTube Verification Setup",
        description ="Configure your YouTube subscription verification system",
        color =COLORS ['info']
        )


        channel_name =self .setup_data .get ('channel_name','❌ Not set')
        embed .add_field (
        name ="📺 YouTube Channel",
        value =f"`{channel_name}`"if channel_name !='❌ Not set'else channel_name ,
        inline =False 
        )


        verification_channel =self .setup_data .get ('verification_channel')
        embed .add_field (
        name ="#️⃣ Verification Channel",
        value =verification_channel .mention if verification_channel else "❌ Not set",
        inline =False 
        )


        verified_role =self .setup_data .get ('verified_role')
        embed .add_field (
        name ="🏷️ Verified Role",
        value =verified_role .mention if verified_role else "❌ Not set",
        inline =False 
        )

        embed .set_footer (text ="Complete all steps to finish setup • Developed by AeroX Development")

        try :
            if hasattr (interaction ,'edit_original_response'):
                await interaction .edit_original_response (embed =embed ,view =self )
            elif self .original_message :
                await self .original_message .edit (embed =embed ,view =self )
        except :
            pass 

    async def complete_setup (self ,interaction :discord .Interaction ):
        """Complete the setup process"""

        channel_name =self .setup_data .get ('channel_name')
        verification_channel =self .setup_data .get ('verification_channel')
        verified_role =self .setup_data .get ('verified_role')

        if not all ([channel_name ,verification_channel ,verified_role ]):
            missing =[]
            if not channel_name :
                missing .append ("YouTube channel name")
            if not verification_channel :
                missing .append ("verification channel")
            if not verified_role :
                missing .append ("verified role")

            await interaction .response .send_message (
            f"<:icon_cross:1372375094336425986> Please configure: {', '.join(missing)}",
            ephemeral =True 
            )
            return 

        await interaction .response .defer ()

        try :

            async with aiosqlite .connect (DATABASE_PATH )as db :
                await db .execute ("""
                    INSERT OR REPLACE INTO ytverify_config 
                    (guild_id, channel_name, verification_channel_id, verified_role_id, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,(
                interaction .guild .id if interaction .guild else 0 ,
                channel_name ,
                verification_channel .id ,
                verified_role .id ,
                datetime .now (timezone .utc ).isoformat (),
                datetime .now (timezone .utc ).isoformat ()
                ))
                await db .commit ()


            embed =discord .Embed (
            title ="✅ YouTube Verification Configured",
            description ="The YouTube verification system has been successfully set up!",
            color =COLORS ['success']
            )
            embed .add_field (name ="📺 Channel",value =f"`{channel_name}`",inline =False )
            embed .add_field (name ="#️⃣ Verification Channel",value =verification_channel .mention ,inline =False )
            embed .add_field (name ="🏷️ Verified Role",value =verified_role .mention ,inline =False )
            embed .set_footer (text ="Users can now upload screenshots to verify their subscription")


            self .clear_items ()

            if self .original_message :
                await self .original_message .edit (embed =embed ,view =self )
            else :
                await interaction .edit_original_response (embed =embed ,view =self )

        except Exception as e :
            logger .error (f"Error saving YouTube verification config: {e}")
            await interaction .followup .send (
            "<:icon_cross:1372375094336425986> An error occurred while saving the configuration.",
            ephemeral =True 
            )




class YTVerify (commands .Cog ):
    """Professional YouTube Verification System"""

    def __init__ (self ,bot ):
        self .bot =bot 
        self .gemini_client =None 
        self .initialize_gemini ()
        self .bot .loop .create_task (self .setup_database ())

    def initialize_gemini (self ):
        """Initialize Gemini client"""
        if not GEMINI_AVAILABLE :
            logger .warning ("Gemini API not available. YouTube verification will work with limited functionality.")
            return 


        api_key =os .getenv ('GOOGLE_API_KEY')or os .getenv ('GEMINI_API_KEY')
        if api_key and GEMINI_AVAILABLE :
            try :
                genai .configure (api_key =api_key )
                self .gemini_client =genai 
                logger .info ("Gemini API initialized successfully")
            except Exception as e :
                logger .error (f"Failed to initialize Gemini API: {e}")
        else :
            logger .warning ("GOOGLE_API_KEY or GEMINI_API_KEY not found in environment variables")

    async def setup_database (self ):
        """Initialize database tables"""
        os .makedirs (os .path .dirname (DATABASE_PATH ),exist_ok =True )

        try :
            async with aiosqlite .connect (DATABASE_PATH )as db :

                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ytverify_config (
                        guild_id INTEGER PRIMARY KEY,
                        channel_name TEXT NOT NULL,
                        verification_channel_id INTEGER NOT NULL,
                        verified_role_id INTEGER NOT NULL,
                        enabled BOOLEAN DEFAULT 1,
                        created_at TEXT NOT NULL,
                        updated_at TEXT NOT NULL
                    )
                """)


                await db .execute ("""
                    CREATE TABLE IF NOT EXISTS ytverify_attempts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        guild_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        message_id INTEGER NOT NULL,
                        verification_status TEXT NOT NULL,
                        failure_reason TEXT,
                        confidence REAL DEFAULT 0.0,
                        created_at TEXT NOT NULL,
                        verified_at TEXT
                    )
                """)

                await db .commit ()

        except Exception as e :
            logger .error (f"Failed to setup YouTube verification database: {e}")
            raise 

    def create_branded_embed (self ,title :str ,description :str ,color :int ):
        """Create a branded embed"""
        embed =discord .Embed (title =title ,description =description ,color =color )
        embed .set_footer (text ="YouTube Verification • Developed by AeroX Development")
        return embed 

    async def analyze_screenshot_with_gemini (self ,image_url :str ,channel_name :str )->Dict [str ,Any ]:
        """Analyze screenshot using Gemini AI"""
        if not self .gemini_client :
            return {
            'is_subscribed':False ,
            'confidence':0.0 ,
            'reason':'AI analysis is unavailable (API key not configured)',
            'channel_found':False ,
            'subscription_indicator':False 
            }

        try :

            import aiohttp 
            async with aiohttp .ClientSession ()as session :
                async with session .get (image_url )as response :
                    if response .status !=200 :
                        raise Exception ("Failed to download image")
                    image_data =await response .read ()


            prompt =f"""Analyze this screenshot to verify if the user is subscribed to the YouTube channel "{channel_name}".

Look for these key indicators:
1. YouTube website/app interface
2. The specific channel name "{channel_name}" visible
3. Subscription status indicators (Subscribe button vs Subscribed button)
4. Bell icon status for notifications
5. Any confirmation messages about subscription

Return your analysis in JSON format:
{{
    "is_subscribed": boolean,
    "confidence": number (0.0-1.0),
    "reason": "detailed explanation",
    "channel_found": boolean,
    "subscription_indicator": boolean
}}

Be strict in your analysis - only return true if you can clearly see subscription confirmation."""


            if GEMINI_AVAILABLE :
                import base64 
                import PIL .Image 
                import io 


                image =PIL .Image .open (io .BytesIO (image_data ))


                model =self .gemini_client .GenerativeModel ('gemini-1.5-flash')
                response =model .generate_content ([prompt ,image ])
            else :
                raise Exception ("Gemini API not available")

            if response .text :

                try :

                    response_text =response .text .strip ()
                    if response_text .startswith ("```json"):
                        response_text =response_text .split ("```json")[1 ].split ("```")[0 ].strip ()
                    elif response_text .startswith ("```"):
                        response_text =response_text .split ("```")[1 ].split ("```")[0 ].strip ()

                    result =json .loads (response_text )
                    logger .info (f"Parsed Gemini analysis result: {result}")
                    return result 
                except json .JSONDecodeError as e :
                    logger .error (f"Failed to parse JSON response: {e}")

                    text_lower =response .text .lower ()
                    if "subscribed"in text_lower and "true"in text_lower :
                        return {
                        'is_subscribed':True ,
                        'confidence':0.7 ,
                        'reason':'AI detected subscription indicators in image',
                        'channel_found':True ,
                        'subscription_indicator':True 
                        }
                    else :
                        return {
                        'is_subscribed':False ,
                        'confidence':0.7 ,
                        'reason':'AI could not confirm subscription',
                        'channel_found':False ,
                        'subscription_indicator':False 
                        }
            else :
                raise Exception ("No response from Gemini")

        except Exception as e :
            logger .error (f"Error in Gemini analysis: {e}")
            return {
            'is_subscribed':False ,
            'confidence':0.0 ,
            'reason':f'Analysis failed: {str(e)}',
            'channel_found':False ,
            'subscription_indicator':False 
            }

    async def get_guild_config (self ,guild_id :int )->Optional [Dict [str ,Any ]]:
        """Get guild YouTube verification configuration"""
        try :
            async with aiosqlite .connect (DATABASE_PATH )as db :
                async with db .execute (
                "SELECT * FROM ytverify_config WHERE guild_id = ?",
                (guild_id ,)
                )as cursor :
                    row =await cursor .fetchone ()
                    if row :
                        return {
                        'guild_id':row [0 ],
                        'channel_name':row [1 ],
                        'verification_channel_id':row [2 ],
                        'verified_role_id':row [3 ],
                        'enabled':bool (row [4 ]),
                        'created_at':row [5 ],
                        'updated_at':row [6 ]
                        }
                    return None 
        except Exception as e :
            logger .error (f"Error getting guild config: {e}")
            return None 

    @commands .Cog .listener ()
    async def on_message (self ,message :discord .Message ):
        """Handle screenshot uploads in verification channels"""
        if message .author .bot or not message .guild :
            return 


        logger .info (f"YTVerify: Message received in channel {message.channel.id} from user {message.author.id}")


        config =await self .get_guild_config (message .guild .id )
        if not config :
            logger .info (f"YTVerify: No config found for guild {message.guild.id}")
            return 

        if not config .get ('enabled',True ):
            logger .info (f"YTVerify: System disabled for guild {message.guild.id}")
            return 

        logger .info (f"YTVerify: Config found - verification channel: {config['verification_channel_id']}, current channel: {message.channel.id}")

        if message .channel .id !=config ['verification_channel_id']:
            return 

        logger .info (f"YTVerify: Message in verification channel! Checking for images...")


        image_attachments =[att for att in message .attachments if att .content_type and att .content_type .startswith ('image/')]
        if not image_attachments :
            logger .info (f"YTVerify: No image attachments found. Attachments: {len(message.attachments)}")

            for att in message .attachments :
                logger .info (f"YTVerify: Attachment: {att.filename}, content_type: {att.content_type}")
            return 

        logger .info (f"YTVerify: Found {len(image_attachments)} image attachment(s). Processing...")


        attachment =image_attachments [0 ]


        embed =self .create_branded_embed (
        "🔍 Analyzing Screenshot",
        "Please wait while I verify your YouTube subscription...",
        COLORS ['warning']
        )
        processing_msg =await message .reply (embed =embed ,mention_author =False )

        try :

            analysis =await self .analyze_screenshot_with_gemini (attachment .url ,config ['channel_name'])


            logger .info (f"YTVerify: Logging attempt to database...")
            try :
                async with aiosqlite .connect (DATABASE_PATH )as db :
                    await db .execute ("""
                        INSERT INTO ytverify_attempts 
                        (guild_id, user_id, message_id, verification_status, failure_reason, confidence, created_at, verified_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,(
                    message .guild .id ,
                    message .author .id ,
                    message .id ,
                    'verified'if analysis ['is_subscribed']else 'failed',
                    analysis ['reason']if not analysis ['is_subscribed']else None ,
                    analysis ['confidence'],
                    datetime .now (timezone .utc ).isoformat (),
                    datetime .now (timezone .utc ).isoformat ()if analysis ['is_subscribed']else None 
                    ))
                    await db .commit ()
                logger .info (f"YTVerify: Database logging successful")
            except Exception as db_error :
                logger .error (f"YTVerify: Database error: {db_error}")

            logger .info (f"YTVerify: Checking verification status - subscribed: {analysis['is_subscribed']}, confidence: {analysis['confidence']}")
            if analysis ['is_subscribed']and analysis ['confidence']>=0.8 :

                logger .info (f"YTVerify: Verification successful, granting role. Confidence: {analysis['confidence']}")
                role =message .guild .get_role (config ['verified_role_id'])
                logger .info (f"YTVerify: Role lookup - ID: {config['verified_role_id']}, Found: {role is not None}")

                if role and isinstance (message .author ,discord .Member ):
                    if role not in message .author .roles :
                        try :
                            logger .info (f"YTVerify: Adding role {role.name} to {message.author}")
                            await message .author .add_roles (role ,reason ="YouTube subscription verified")
                            logger .info (f"YTVerify: Role successfully added")

                            embed =self .create_branded_embed (
                            "✅ Verification Successful",
                            f"Congratulations! You have been verified as a subscriber to **{config['channel_name']}**.\n\n"
                            f"**Role Granted:** {role.mention}\n"
                            f"**Confidence:** {analysis['confidence']:.1%}",
                            COLORS ['success']
                            )
                        except discord .Forbidden :
                            embed =self .create_branded_embed (
                            "⚠️ Verification Successful (Role Error)",
                            f"You have been verified as a subscriber to **{config['channel_name']}**, but I couldn't assign the role due to permission issues.\n\n"
                            f"Please contact a server administrator.",
                            COLORS ['warning']
                            )
                    else :
                        embed =self .create_branded_embed (
                        "ℹ️ Already Verified",
                        f"You already have the verified role for **{config['channel_name']}**!",
                        COLORS ['info']
                        )
                else :
                    embed =self .create_branded_embed (
                    "❌ Role Configuration Error",
                    "The verified role no longer exists or insufficient permissions.",
                    COLORS ['error']
                    )
            else :

                embed =self .create_branded_embed (
                "❌ Verification Failed",
                f"I couldn't verify your subscription to **{config['channel_name']}**.\n\n"
                f"**Reason:** {analysis['reason']}\n\n"
                f"Please ensure your screenshot shows:\n"
                f"• The YouTube channel page for **{config['channel_name']}**\n"
                f"• A clear 'Subscribed' button or subscription confirmation\n"
                f"• The full browser/app interface",
                COLORS ['error']
                )

            await processing_msg .edit (embed =embed )

        except Exception as e :
            logger .error (f"Error processing verification: {e}")
            embed =self .create_branded_embed (
            "❌ Processing Error",
            "An error occurred while processing your screenshot. Please try again later.",
            COLORS ['error']
            )
            try :
                await processing_msg .edit (embed =embed )
            except :
                pass 


    @app_commands .command (name ="ytverify",description ="Configure YouTube subscription verification system")
    @app_commands .describe (
    action ="Choose an action: setup, enable, disable, or status"
    )
    @app_commands .choices (action =[
    app_commands .Choice (name ="Setup System",value ="setup"),
    app_commands .Choice (name ="Enable System",value ="enable"),
    app_commands .Choice (name ="Disable System",value ="disable"),
    app_commands .Choice (name ="Check Status",value ="status"),
    app_commands .Choice (name ="Reset System",value ="reset")
    ])
    async def ytverify_slash (self ,interaction :discord .Interaction ,action :str ):
        """YouTube verification system management (slash command)"""
        await self ._ytverify_logic (interaction ,action )


    @commands .command (name ="ytverify",aliases =['yt-verify','youtubeverify'])
    async def ytverify_prefix (self ,ctx ,action :str =None ):
        """YouTube verification system management (prefix command)"""
        if not action :
            embed =self .create_branded_embed (
            "📺 YouTube Verification System",
            "**Usage:** `ytverify <action>`\n\n"
            "**Actions:**\n"
            "• `setup` - Configure the verification system\n"
            "• `enable` - Enable the system\n"
            "• `disable` - Disable the system\n"
            "• `status` - Check current status\n"
            "• `reset` - Clear all configuration data",
            COLORS ['info']
            )
            await ctx .send (embed =embed )
            return 


        class PrefixInteraction :
            def __init__ (self ,ctx ):
                self .user =ctx .author 
                self .guild =ctx .guild 
                self .channel =ctx .channel 
                self ._ctx =ctx 
                self ._responded =False 
                self ._response_obj =None 

            async def response_send_message (self ,*args ,**kwargs ):
                self ._responded =True 
                return await self ._ctx .send (*args ,**kwargs )

            async def edit_original_response (self ,*args ,**kwargs ):

                return await self ._ctx .send (*args ,**kwargs )

            async def original_response (self ):
                return None 

            async def defer (self ):
                pass 

            async def followup_send (self ,*args ,**kwargs ):
                return await self ._ctx .send (*args ,**kwargs )


        pseudo_interaction =PrefixInteraction (ctx )


        class ResponseObj :
            def __init__ (self ,interaction ):
                self ._interaction =interaction 

            async def send_message (self ,*args ,**kwargs ):
                return await self ._interaction .response_send_message (*args ,**kwargs )

        pseudo_interaction ._response_obj =ResponseObj (pseudo_interaction )
        pseudo_interaction .response =pseudo_interaction ._response_obj 

        await self ._ytverify_logic (pseudo_interaction ,action .lower ()if action else "")

    async def _ytverify_logic (self ,interaction ,action :str ):
        """Shared logic for both slash and prefix commands"""

        if action =="setup":

            if hasattr (interaction .user ,'guild_permissions'):
                has_permission =interaction .user .guild_permissions .manage_guild 
            else :

                has_permission =any (role .permissions .manage_guild for role in interaction .user .roles )

            if not has_permission :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> You need `Manage Server` permission to configure YouTube verification.",
                ephemeral =True 
                )
                return 


            view =YouTubeVerificationSetupView (interaction )

            embed =discord .Embed (
            title ="📺 YouTube Verification Setup",
            description ="Configure your YouTube subscription verification system using the dropdown menu below.",
            color =COLORS ['info']
            )
            embed .add_field (name ="📺 YouTube Channel",value ="❌ Not set",inline =False )
            embed .add_field (name ="#️⃣ Verification Channel",value ="❌ Not set",inline =False )
            embed .add_field (name ="🏷️ Verified Role",value ="❌ Not set",inline =False )
            embed .set_footer (text ="Complete all steps to finish setup • Developed by AeroX Development")

            await interaction .response .send_message (embed =embed ,view =view )
            if hasattr (interaction ,'original_response'):
                view .original_message =await interaction .original_response ()

        elif action =="enable":
            if hasattr (interaction .user ,'guild_permissions'):
                has_permission =interaction .user .guild_permissions .manage_guild 
            elif hasattr (interaction .user ,'roles'):
                has_permission =any (role .permissions .manage_guild for role in interaction .user .roles )
            else :
                has_permission =False 

            if not has_permission :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> You need `Manage Server` permission to manage YouTube verification.",
                ephemeral =True 
                )
                return 

            try :
                async with aiosqlite .connect (DATABASE_PATH )as db :

                    async with db .execute ("SELECT guild_id FROM ytverify_config WHERE guild_id = ?",(interaction .guild .id ,))as cursor :
                        exists =await cursor .fetchone ()

                    if not exists :
                        await interaction .response .send_message (
                        "<:icon_cross:1372375094336425986> YouTube verification is not set up yet. Use `ytverify setup` first.",
                        ephemeral =True 
                        )
                        return 


                    await db .execute ("UPDATE ytverify_config SET enabled = 1 WHERE guild_id = ?",(interaction .guild .id ,))
                    await db .commit ()

                embed =self .create_branded_embed (
                "✅ System Enabled",
                "YouTube verification system has been enabled!",
                COLORS ['success']
                )
                await interaction .response .send_message (embed =embed )

            except Exception as e :
                logger .error (f"Error enabling YouTube verification: {e}")
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> An error occurred while enabling the system.",
                ephemeral =True 
                )

        elif action =="disable":
            if hasattr (interaction .user ,'guild_permissions'):
                has_permission =interaction .user .guild_permissions .manage_guild 
            elif hasattr (interaction .user ,'roles'):
                has_permission =any (role .permissions .manage_guild for role in interaction .user .roles )
            else :
                has_permission =False 

            if not has_permission :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> You need `Manage Server` permission to manage YouTube verification.",
                ephemeral =True 
                )
                return 

            try :
                async with aiosqlite .connect (DATABASE_PATH )as db :
                    await db .execute ("UPDATE ytverify_config SET enabled = 0 WHERE guild_id = ?",(interaction .guild .id ,))
                    await db .commit ()

                embed =self .create_branded_embed (
                "⏸️ System Disabled",
                "YouTube verification system has been disabled.",
                COLORS ['warning']
                )
                await interaction .response .send_message (embed =embed )

            except Exception as e :
                logger .error (f"Error disabling YouTube verification: {e}")
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> An error occurred while disabling the system.",
                ephemeral =True 
                )

        elif action =="status":
            config =await self .get_guild_config (interaction .guild .id )

            if not config :
                embed =self .create_branded_embed (
                "📺 YouTube Verification Status",
                "❌ **Not configured**\n\nUse `ytverify setup` to get started!",
                COLORS ['error']
                )
            else :
                channel =interaction .guild .get_channel (config ['verification_channel_id'])
                role =interaction .guild .get_role (config ['verified_role_id'])

                status ="🟢 **Enabled**"if config .get ('enabled',True )else "🔴 **Disabled**"

                embed =self .create_branded_embed (
                "📺 YouTube Verification Status",
                f"{status}\n\n"
                f"**📺 Channel:** `{config['channel_name']}`\n"
                f"**#️⃣ Verification Channel:** {channel.mention if channel else '❌ Channel not found'}\n"
                f"**🏷️ Verified Role:** {role.mention if role else '❌ Role not found'}",
                COLORS ['success']if config .get ('enabled',True )else COLORS ['warning']
                )

            await interaction .response .send_message (embed =embed )

        elif action =="reset":
            if hasattr (interaction .user ,'guild_permissions'):
                has_permission =interaction .user .guild_permissions .manage_guild 
            elif hasattr (interaction .user ,'roles'):
                has_permission =any (role .permissions .manage_guild for role in interaction .user .roles )
            else :
                has_permission =False 

            if not has_permission :
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> You need `Manage Server` permission to reset YouTube verification.",
                ephemeral =True 
                )
                return 


            config =await self .get_guild_config (interaction .guild .id )
            if not config :
                embed =self .create_branded_embed (
                "❌ No Configuration Found",
                "No YouTube verification configuration exists for this server.",
                COLORS ['error']
                )
                await interaction .response .send_message (embed =embed ,ephemeral =True )
                return 

            try :
                async with aiosqlite .connect (DATABASE_PATH )as db :

                    await db .execute ("DELETE FROM ytverify_config WHERE guild_id = ?",(interaction .guild .id ,))
                    await db .execute ("DELETE FROM ytverify_attempts WHERE guild_id = ?",(interaction .guild .id ,))
                    await db .commit ()

                embed =self .create_branded_embed (
                "✅ System Reset Complete",
                "All YouTube verification data has been cleared for this server.\n\n"
                "• Configuration removed\n"
                "• Verification attempts cleared\n\n"
                "Use `ytverify setup` to configure the system again.",
                COLORS ['success']
                )
                await interaction .response .send_message (embed =embed )

            except Exception as e :
                logger .error (f"Error resetting YouTube verification: {e}")
                await interaction .response .send_message (
                "<:icon_cross:1372375094336425986> An error occurred while resetting the system.",
                ephemeral =True 
                )

        else :
            embed =self .create_branded_embed (
            "❌ Invalid Action",
            "Please use one of: `setup`, `enable`, `disable`, `status`, `reset`",
            COLORS ['error']
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

async def setup (bot ):
    await bot .add_cog (YTVerify (bot ))