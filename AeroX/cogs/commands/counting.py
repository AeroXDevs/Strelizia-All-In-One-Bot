import discord 
from discord .ext import commands 
from discord import app_commands ,Webhook 
from discord .ui import View ,Select ,Button ,Modal ,TextInput 
import aiosqlite 
import asyncio 
import ast 
import operator 
import re 
import math 
import logging 
import json 
import aiohttp 
from datetime import datetime ,timedelta 
from typing import Optional ,Dict ,Any ,List ,Tuple 
from sympy import symbols ,factorial ,sqrt ,pi ,E ,I ,simplify ,latex ,parse_expr 
import sympy as sp 


logging .basicConfig (level =logging .INFO )
logger =logging .getLogger (__name__ )


LANGUAGES ={
'en':{
'count_accepted':'Count Accepted',
'wrong_count':'Wrong Count',
'same_user':'Same User',
'cannot_count_twice':'You cannot count twice in a row!',
'expected_but_got':'Expected **{expected}** but got **{attempted}**',
'reset':'Reset',
'count_reset':'Count has been reset to 0!',
'continue':'Continue',
'next_count_should_be':'Next count should be **{expected}**',
'leaderboard':'Counting Leaderboard',
'global_leaderboard':'Global Counting Leaderboard',
'counting_enabled':'Counting Enabled',
'counting_disabled':'Counting Disabled',
'channel_set':'Channel Set'
},
'es':{
'count_accepted':'Conteo Aceptado',
'wrong_count':'Conteo Incorrecto',
'same_user':'Mismo Usuario',
'cannot_count_twice':'¡No puedes contar dos veces seguidas!',
'expected_but_got':'Esperado **{expected}** pero obtuviste **{attempted}**',
'reset':'Reiniciar',
'count_reset':'¡El conteo ha sido reiniciado a 0!',
'continue':'Continuar',
'next_count_should_be':'El próximo conteo debería ser **{expected}**',
'leaderboard':'Tabla de Clasificación',
'global_leaderboard':'Tabla de Clasificación Global',
'counting_enabled':'Conteo Habilitado',
'counting_disabled':'Conteo Deshabilitado',
'channel_set':'Canal Configurado'
},
'fr':{
'count_accepted':'Comptage Accepté',
'wrong_count':'Mauvais Comptage',
'same_user':'Même Utilisateur',
'cannot_count_twice':'Vous ne pouvez pas compter deux fois de suite!',
'expected_but_got':'Attendu **{expected}** mais obtenu **{attempted}**',
'reset':'Réinitialiser',
'count_reset':'Le comptage a été réinitialisé à 0!',
'continue':'Continuer',
'next_count_should_be':'Le prochain comptage devrait être **{expected}**',
'leaderboard':'Classement',
'global_leaderboard':'Classement Global',
'counting_enabled':'Comptage Activé',
'counting_disabled':'Comptage Désactivé',
'channel_set':'Canal Défini'
},
'hi':{
'count_accepted':'गिनती स्वीकार',
'wrong_count':'गलत गिनती',
'same_user':'वही उपयोगकर्ता',
'cannot_count_twice':'आप लगातार दो बार गिनती नहीं कर सकते!',
'expected_but_got':'अपेक्षित **{expected}** लेकिन मिला **{attempted}**',
'reset':'रीसेट',
'count_reset':'गिनती 0 पर रीसेट हो गई है!',
'continue':'जारी रखें',
'next_count_should_be':'अगली गिनती **{expected}** होनी चाहिए',
'leaderboard':'गिनती लीडरबोर्ड',
'global_leaderboard':'वैश्विक गिनती लीडरबोर्ड',
'counting_enabled':'गिनती सक्षम',
'counting_disabled':'गिनती अक्षम',
'channel_set':'चैनल सेट'
}
}

class AdvancedMathParser :
    """Advanced mathematical expression parser with complex features"""

    def __init__ (self ):
        self .x =symbols ('x')

    @classmethod 
    def normalize_expression (cls ,expression :str )->str :
        """Convert special characters and notations to Python/SymPy syntax"""

        expression =cls .convert_unicode_digits (expression )


        expression =expression .replace ('×','*').replace ('·','*').replace ('⋅','*')

        expression =expression .replace ('÷','/')

        expression =re .sub (r'√(\d+(?:\.\d+)?)',r'sqrt(\1)',expression )

        expression =re .sub (r'(\d+)!',r'factorial(\1)',expression )

        expression =expression .replace ('^','**')

        expression =re .sub (r'(\d+(?:\.\d+)?)e([+-]?\d+)',r'\1*10**\2',expression )

        expression =expression .replace ('i','*I').replace ('j','*I')

        expression =expression .replace ('π','pi').replace ('e','E')

        expression =re .sub (r'\s+','',expression )
        return expression 

    @classmethod 
    def convert_unicode_digits (cls ,text :str )->str :
        """Convert Unicode digits from various languages to Arabic numerals"""

        digit_mappings ={

        '०':'0','१':'1','२':'2','३':'3','४':'4',
        '५':'5','६':'6','७':'7','८':'8','९':'9',


        '٠':'0','١':'1','٢':'2','٣':'3','٤':'4',
        '٥':'5','٦':'6','٧':'7','٨':'8','٩':'9',


        '۰':'0','۱':'1','۲':'2','۳':'3','۴':'4',
        '۵':'5','۶':'6','۷':'7','۸':'8','۹':'9',


        '০':'0','১':'1','২':'2','৩':'3','৪':'4',
        '৫':'5','৬':'6','৭':'7','৮':'8','৯':'9'
        }


        for unicode_digit ,arabic_digit in digit_mappings .items ():
            text =text .replace (unicode_digit ,arabic_digit )

        return text 

    @classmethod 
    def safe_eval (cls ,expression :str )->complex :
        """Safely evaluate mathematical expressions using SymPy"""
        try :
            expression =cls .normalize_expression (expression )

            parsed =parse_expr (expression ,transformations ='all',evaluate =True )

            result_numeric =parsed .evalf ()

            if hasattr (result_numeric ,'as_real_imag'):
                real_part ,imag_part =result_numeric .as_real_imag ()
                return complex (float (real_part ),float (imag_part ))
            else :
                return complex (float (result_numeric ))
        except (ValueError ,TypeError ,AttributeError ,SyntaxError )as e :
            raise ValueError (f"Invalid mathematical expression: {e}")
        except Exception as e :
            raise ValueError (f"Error evaluating expression: {e}")

class CountingConfigModal (Modal ):
    """Enhanced modal for configuring counting settings"""

    def __init__ (self ,bot ,guild_id :int ,current_settings :Dict [str ,Any ]):
        super ().__init__ (title ="Counting Configuration")
        self .bot =bot 
        self .guild_id =guild_id 
        self .current_settings =current_settings 

        self .reset_on_fail =TextInput (
        label ="Reset on Fail (true/false)",
        placeholder ="Enter 'true' or 'false'",
        default =str (current_settings .get ('reset_on_fail',True )).lower (),
        max_length =5 
        )

        self .enforce_alternating =TextInput (
        label ="Enforce Alternating Users (true/false)",
        placeholder ="Enter 'true' or 'false'",
        default =str (current_settings .get ('enforce_alternating',True )).lower (),
        max_length =5 
        )

        self .language =TextInput (
        label ="Language (en/es/fr/hi)",
        placeholder ="Enter language code",
        default =current_settings .get ('language','en'),
        max_length =2 
        )

        self .add_item (self .reset_on_fail )
        self .add_item (self .enforce_alternating )
        self .add_item (self .language )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            reset_val =self .reset_on_fail .value .lower ()=='true'
            alternating_val =self .enforce_alternating .value .lower ()=='true'
            lang =self .language .value if self .language .value in ['en','es','fr','hi']else 'en'

            async with aiosqlite .connect ("db/counting.db")as db :
                await db .execute ("""
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, reset_on_fail, enforce_alternating, language)
                VALUES (?, ?, ?, ?)
                """,(self .guild_id ,reset_val ,alternating_val ,lang ))
                await db .commit ()

            embed =discord .Embed (
            title ="<:icon_tick:1372375089668161597> Configuration Updated",
            description =f"Settings updated successfully!",
            color =0x00FF00 
            )
            await interaction .response .send_message (embed =embed ,ephemeral =True )

        except Exception as e :
            await interaction .response .send_message (f"Error updating configuration: {e}",ephemeral =True )

class GlobalLeaderboardView (View ):
    """Global leaderboard view across all servers"""

    def __init__ (self ,leaderboard_data :List [Tuple ],page_size :int =10 ):
        super ().__init__ (timeout =300 )
        self .leaderboard_data =leaderboard_data 
        self .page_size =page_size 
        self .current_page =0 
        self .total_pages =(len (leaderboard_data )+page_size -1 )//page_size 

        if self .total_pages >1 :
            self .add_page_selector ()

    def add_page_selector (self ):
        """Add page selection dropdown"""
        options =[]
        for i in range (min (self .total_pages ,25 )):
            start_rank =i *self .page_size +1 
            end_rank =min ((i +1 )*self .page_size ,len (self .leaderboard_data ))
            options .append (
            discord .SelectOption (
            label =f"Page {i + 1}",
            description =f"Global ranks {start_rank}-{end_rank}",
            value =str (i )
            )
            )

        select =Select (placeholder ="Choose a page",options =options )
        select .callback =self .page_callback 
        self .add_item (select )

    async def page_callback (self ,interaction :discord .Interaction ):
        """Handle page selection"""
        self .current_page =int (interaction .values [0 ])
        embed =self .create_leaderboard_embed ()
        await interaction .response .edit_message (embed =embed ,view =self )

    def create_leaderboard_embed (self )->discord .Embed :
        """Create global leaderboard embed"""
        embed =discord .Embed (
        title ="🌍 Global Counting Leaderboard",
        description ="Top counters across all servers",
        color =0x000000 
        )

        start_idx =self .current_page *self .page_size 
        end_idx =min (start_idx +self .page_size ,len (self .leaderboard_data ))

        leaderboard_text =""
        for i in range (start_idx ,end_idx ):
            user_id ,count ,guild_count =self .leaderboard_data [i ]
            rank =i +1 
            medal ="🥇"if rank ==1 else "🥈"if rank ==2 else "🥉"if rank ==3 else f"#{rank}"
            leaderboard_text +=f"{medal} <@{user_id}> - **{count}** total counts ({guild_count} servers)\n"

        embed .description =leaderboard_text or "No global counting data available."
        embed .set_footer (text =f"Page {self.current_page + 1}/{self.total_pages}")
        return embed 

class Counting (commands .Cog ):
    """Advanced counting cog with mathematical expression support"""

    def __init__ (self ,bot ):
        self .bot =bot 
        self .math_parser =AdvancedMathParser ()
        self .rate_limiter ={}
        self .webhooks ={}
        self .bot .loop .create_task (self ._create_tables ())
        pass 

    async def _create_tables (self ):
        """Create necessary database tables"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :

                await db .execute ("""
                CREATE TABLE IF NOT EXISTS counting (
                    guild_id INTEGER PRIMARY KEY,
                    current_count INTEGER DEFAULT 0,
                    last_user_id INTEGER,
                    channel_id INTEGER
                )
                """)


                await db .execute ("""
                CREATE TABLE IF NOT EXISTS count_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER,
                    user_id INTEGER,
                    expression TEXT,
                    result INTEGER,
                    timestamp TEXT
                )
                """)


                await db .execute ("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id INTEGER PRIMARY KEY,
                    reset_on_fail BOOLEAN DEFAULT TRUE,
                    enforce_alternating BOOLEAN DEFAULT TRUE,
                    language TEXT DEFAULT 'en',
                    counting_enabled BOOLEAN DEFAULT TRUE
                )
                """)


                await db .execute ("""
                CREATE TABLE IF NOT EXISTS user_stats (
                    guild_id INTEGER,
                    user_id INTEGER,
                    total_counts INTEGER DEFAULT 0,
                    highest_count INTEGER DEFAULT 0,
                    last_count_time TEXT,
                    PRIMARY KEY (guild_id, user_id)
                )
                """)

                await db .commit ()
                pass 
        except Exception as e :
            logger .error (f"Error creating counting tables: {e}")

    async def get_text (self ,guild_id :int ,key :str ,**kwargs )->str :
        """Get localized text"""
        settings =await self .get_guild_settings (guild_id )
        lang =settings .get ('language','en')
        text =LANGUAGES .get (lang ,LANGUAGES ['en']).get (key ,key )
        return text .format (**kwargs )if kwargs else text 

    async def get_user_stats (self ,guild_id :int ,user_id :int )->Dict [str ,Any ]:
        """Get comprehensive user statistics"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                async with db .execute ("""
                SELECT total_counts, highest_count
                FROM user_stats WHERE guild_id = ? AND user_id = ?
                """,(guild_id ,user_id ))as cursor :
                    row =await cursor .fetchone ()
                    if row :
                        return {
                        'total_counts':row [0 ],
                        'highest_count':row [1 ]
                        }
                    return {
                    'total_counts':0 ,
                    'highest_count':0 
                    }
        except Exception as e :
            logger .error (f"Error getting user stats: {e}")
            return {}

    async def update_user_stats (self ,guild_id :int ,user_id :int ,count :int ):
        """Update user statistics"""
        try :
            stats =await self .get_user_stats (guild_id ,user_id )

            now =datetime .now ()
            async with aiosqlite .connect ("db/counting.db")as db :
                await db .execute ("""
                INSERT OR REPLACE INTO user_stats 
                (guild_id, user_id, total_counts, highest_count, last_count_time)
                VALUES (?, ?, ?, ?, ?)
                """,(
                guild_id ,user_id ,
                stats ['total_counts']+1 ,
                max (stats ['highest_count'],count ),
                now .isoformat ()
                ))
                await db .commit ()
        except Exception as e :
            logger .error (f"Error updating user stats: {e}")

    async def get_or_create_webhook (self ,channel ):
        """Get or create webhook for the channel"""
        try :
            if channel .id in self .webhooks :
                return self .webhooks [channel .id ]


            webhooks =await channel .webhooks ()
            for webhook in webhooks :
                if webhook .name =="Counting Bot":
                    self .webhooks [channel .id ]=webhook 
                    return webhook 


            webhook =await channel .create_webhook (name ="Counting Bot")
            self .webhooks [channel .id ]=webhook 
            return webhook 
        except Exception as e :
            logger .error (f"Error creating webhook: {e}")
            return None 

    @commands .Cog .listener ()
    async def on_message (self ,message ):
        """Enhanced message listener with webhook functionality"""
        if message .author .bot :
            return 

        guild_id =message .guild .id 
        counting_data =await self .get_counting_data (guild_id )
        settings =await self .get_guild_settings (guild_id )


        if not settings .get ('counting_enabled',True ):
            return 

        if not counting_data or counting_data ['channel_id']!=message .channel .id :
            return 


        if message .attachments or message .embeds :
            return 

        content =message .content .strip ()
        if not content or len (content )>500 :
            return 


        text_patterns =[
        r'^[a-zA-Z]+\s+[a-zA-Z]+',
        r'\b(hello|hi|hey|lol|lmao|omg|wtf|brb|ok|okay|yes|no|yeah|nah|nice|good|bad|cool|wow|damn|what|why|how|when|where|who|the|and|or|but|if|then|else|this|that|these|those|here|there|now|later|today|tomorrow|yesterday)\b',
        r'[.!?]{2,}',
        r'@\w+',
        r'<[:#@&][!&]?\d+>',
        r'https?://',
        r':\w+:',
        ]

        content_lower =content .lower ()
        for pattern in text_patterns :
            if re .search (pattern ,content_lower ,re .IGNORECASE ):
                return 


        if re .match (r'^[a-zA-Z\s]+$',content )and not any (char in content .lower ()for char in ['pi','e','i','x']):
            return 

        try :

            result =self .math_parser .safe_eval (content )


            if isinstance (result ,complex ):
                if abs (result .imag )>1e-10 :
                    await message .add_reaction ("<:icon_cross:1372375094336425986>")
                    return 
                result =result .real 


            if not isinstance (result ,(int ,float )):
                await message .add_reaction ("<:icon_cross:1372375094336425986>")
                return 


            try :
                result_int =int (round (float (result )))
                if abs (result -result_int )>1e-10 or result_int <0 :
                    await message .add_reaction ("<:icon_cross:1372375094336425986>")
                    return 
                result =result_int 
            except (ValueError ,OverflowError ):
                await message .add_reaction ("<:icon_cross:1372375094336425986>")
                return 

            expected_count =counting_data ['current_count']+1 


            if result !=expected_count :
                await self .handle_wrong_count (message ,guild_id ,result ,expected_count )
                return 


            now =datetime .now ()
            user_key =f"{guild_id}_{message.author.id}"
            if user_key in self .rate_limiter :
                time_diff =(now -self .rate_limiter [user_key ]).total_seconds ()
                if time_diff <1 :
                    await message .add_reaction ("⏰")
                    return 
            self .rate_limiter [user_key ]=now 


            if settings ['enforce_alternating']and counting_data ['last_user_id']==message .author .id :
                embed =discord .Embed (
                title ="<:icon_cross:1372375094336425986> Same User",
                description =await self .get_text (guild_id ,'cannot_count_twice'),
                color =0xFF0000 
                )
                try :
                    await message .delete ()
                except :
                    pass 
                await message .channel .send (embed =embed ,delete_after =5 )
                return 


            try :
                await message .delete ()
            except :
                pass 


            webhook =await self .get_or_create_webhook (message .channel )
            if webhook :
                try :
                    await webhook .send (
                    content =str (result ),
                    username =message .author .display_name ,
                    avatar_url =message .author .display_avatar .url 
                    )
                except Exception as e :
                    logger .error (f"Webhook send error: {e}")

                    await message .channel .send (f"**{result}** - {message.author.mention}")
            else :

                await message .channel .send (f"**{result}** - {message.author.mention}")


            await self .update_counting_data (guild_id ,result ,message .author .id ,message .channel .id )


            await self .log_count (guild_id ,message .author .id ,content ,result )


            await self .update_user_stats (guild_id ,message .author .id ,result )


            if result %1000 ==0 :

                async for msg in message .channel .history (limit =1 ):
                    await msg .add_reaction ("🎆")
                    break 
            elif result %100 ==0 :
                async for msg in message .channel .history (limit =1 ):
                    await msg .add_reaction ("🎉")
                    break 
            elif result %50 ==0 :
                async for msg in message .channel .history (limit =1 ):
                    await msg .add_reaction ("🎊")
                    break 

            logger .info (f"Valid count {result} by {message.author} in guild {guild_id}")

        except ValueError :
            return 
        except Exception as e :
            logger .error (f"Error processing count in guild {guild_id}: {e}")

    async def get_counting_data (self ,guild_id :int )->Optional [Dict [str ,Any ]]:
        """Get current counting data for a guild"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                async with db .execute ("""
                SELECT current_count, last_user_id, channel_id 
                FROM counting WHERE guild_id = ?
                """,(guild_id ,))as cursor :
                    row =await cursor .fetchone ()
                    if row :
                        return {
                        'current_count':row [0 ],
                        'last_user_id':row [1 ],
                        'channel_id':row [2 ]
                        }
                    return None 
        except Exception as e :
            logger .error (f"Error getting counting data for guild {guild_id}: {e}")
            return None 

    async def get_guild_settings (self ,guild_id :int )->Dict [str ,Any ]:
        """Get enhanced guild settings with defaults"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                async with db .execute ("""
                SELECT reset_on_fail, enforce_alternating, language, counting_enabled
                FROM guild_settings WHERE guild_id = ?
                """,(guild_id ,))as cursor :
                    row =await cursor .fetchone ()
                    if row :
                        return {
                        'reset_on_fail':row [0 ],
                        'enforce_alternating':row [1 ],
                        'language':row [2 ]or 'en',
                        'counting_enabled':row [3 ]if row [3 ]is not None else True 
                        }
                    return {
                    'reset_on_fail':True ,
                    'enforce_alternating':True ,
                    'language':'en',
                    'counting_enabled':True 
                    }
        except Exception as e :
            logger .error (f"Error getting guild settings for guild {guild_id}: {e}")
            return {
            'reset_on_fail':True ,
            'enforce_alternating':True ,
            'language':'en',
            'counting_enabled':True 
            }

    async def update_counting_data (self ,guild_id :int ,count :int ,user_id :int ,channel_id :int ):
        """Update counting data for a guild"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                await db .execute ("""
                INSERT OR REPLACE INTO counting (guild_id, current_count, last_user_id, channel_id)
                VALUES (?, ?, ?, ?)
                """,(guild_id ,count ,user_id ,channel_id ))
                await db .commit ()
        except Exception as e :
            logger .error (f"Error updating counting data for guild {guild_id}: {e}")

    async def log_count (self ,guild_id :int ,user_id :int ,expression :str ,result :int ):
        """Enhanced count logging"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                await db .execute ("""
                INSERT INTO count_logs (guild_id, user_id, expression, result, timestamp)
                VALUES (?, ?, ?, ?, ?)
                """,(guild_id ,user_id ,expression ,result ,datetime .now ().isoformat ()))
                await db .commit ()
        except Exception as e :
            logger .error (f"Error logging count for guild {guild_id}: {e}")

    async def reset_counting (self ,guild_id :int ):
        """Reset counting for a guild"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                await db .execute ("""
                UPDATE counting SET current_count = 0, last_user_id = NULL 
                WHERE guild_id = ?
                """,(guild_id ,))
                await db .commit ()
        except Exception as e :
            logger .error (f"Error resetting counting for guild {guild_id}: {e}")

    async def reset_guild_database (self ,guild_id :int ):
        """Reset all counting data for a guild"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :

                await db .execute ("DELETE FROM counting WHERE guild_id = ?",(guild_id ,))
                await db .execute ("DELETE FROM count_logs WHERE guild_id = ?",(guild_id ,))
                await db .execute ("DELETE FROM user_stats WHERE guild_id = ?",(guild_id ,))
                await db .execute ("DELETE FROM guild_settings WHERE guild_id = ?",(guild_id ,))
                await db .commit ()
        except Exception as e :
            logger .error (f"Error resetting guild database for guild {guild_id}: {e}")

    async def handle_wrong_count (self ,message ,guild_id :int ,attempted :int ,expected :int ):
        """Enhanced wrong count handler"""
        settings =await self .get_guild_settings (guild_id )

        embed =discord .Embed (
        title ="<:icon_cross:1372375094336425986> "+await self .get_text (guild_id ,'wrong_count'),
        description =await self .get_text (guild_id ,'expected_but_got',expected =expected ,attempted =attempted ),
        color =0xFF0000 
        )

        if settings ['reset_on_fail']:
            await self .reset_counting (guild_id )
            embed .add_field (
            name =await self .get_text (guild_id ,'reset'),
            value =await self .get_text (guild_id ,'count_reset'),
            inline =False 
            )
        else :
            embed .add_field (
            name =await self .get_text (guild_id ,'continue'),
            value =await self .get_text (guild_id ,'next_count_should_be',expected =expected ),
            inline =False 
            )


        try :
            await message .delete ()
        except :
            pass 


        await message .channel .send (embed =embed ,delete_after =10 )

    @commands .hybrid_group (name ="counting",description ="Counting commands and management")
    async def counting_group (self ,ctx ):
        """Enhanced counting command group"""
        if ctx .invoked_subcommand is None :
            await ctx .send_help (ctx .command )

    @counting_group .command (name ="config",description ="Configure counting settings")
    @commands .has_permissions (administrator =True )
    async def counting_config (self ,ctx ):
        """Interactive configuration"""
        current_settings =await self .get_guild_settings (ctx .guild .id )
        counting_data =await self .get_counting_data (ctx .guild .id )

        embed =discord .Embed (
        title ="⚙️ Counting Configuration",
        description ="Configure your server's counting settings",
        color =0x000000 
        )

        view =View (timeout =300 )


        if ctx .guild .text_channels :
            channel_options =[
            discord .SelectOption (
            label =f"#{channel.name}",
            value =str (channel .id ),
            description =f"Set counting channel to #{channel.name}"
            )
            for channel in ctx .guild .text_channels [:25 ]
            ]

            channel_select =Select (
            placeholder ="Select counting channel",
            options =channel_options ,
            custom_id ="channel_select"
            )

            async def channel_callback (interaction :discord .Interaction ):
                try :
                    if interaction .user .id !=ctx .author .id :
                        await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
                        return 

                    selected_values =interaction .data .get ('values',[])
                    if not selected_values :
                        await interaction .response .send_message ("No channel selected.",ephemeral =True )
                        return 

                    channel_id =int (selected_values [0 ])
                    current_count =counting_data ['current_count']if counting_data else 0 

                    await self .update_counting_data (ctx .guild .id ,current_count ,None ,channel_id )

                    embed_response =discord .Embed (
                    title ="<:icon_tick:1372375089668161597> Channel Updated",
                    description =f"Counting channel set to <#{channelid}>",
                    color =0x00FF00 
                    )
                    await interaction .response .send_message (embed =embed_response ,ephemeral =True )
                except Exception as e :
                    await interaction .response .send_message (f"Error updating channel: {e}",ephemeral =True )

            channel_select .callback =channel_callback 
            view .add_item (channel_select )


        settings_button =Button (label ="Settings",style =discord .ButtonStyle .primary ,custom_id ="settings_btn")

        async def settings_callback (interaction :discord .Interaction ):
            try :
                if interaction .user .id !=ctx .author .id :
                    await interaction .response .send_message ("Only the command author can configure this.",ephemeral =True )
                    return 

                modal =CountingConfigModal (self .bot ,ctx .guild .id ,current_settings )
                await interaction .response .send_modal (modal )
            except Exception as e :
                await interaction .response .send_message (f"Error opening settings: {e}",ephemeral =True )

        settings_button .callback =settings_callback 
        view .add_item (settings_button )


        if counting_data :
            current_channel =f"<#{counting_data['channel_id']}>"if counting_data ['channel_id']else "None"
            embed .add_field (name ="Current Channel",value =current_channel ,inline =False )
            embed .add_field (name ="Current Count",value =str (counting_data ['current_count']),inline =True )

        embed .add_field (name ="Language",value =current_settings .get ('language','en').upper (),inline =True )

        await ctx .send (embed =embed ,view =view )

    @counting_group .command (name ="leaderboard",description ="Show server counting leaderboard")
    async def counting_leaderboard (self ,ctx ):
        """Display server counting leaderboard"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                async with db .execute ("""
                SELECT user_id, total_counts FROM user_stats 
                WHERE guild_id = ? AND total_counts > 0
                ORDER BY total_counts DESC
                LIMIT 25
                """,(ctx .guild .id ,))as cursor :
                    leaderboard_data =await cursor .fetchall ()

            embed =discord .Embed (
            title =f"🏆 {ctx.guild.name} Counting Leaderboard",
            color =0x000000 
            )

            if leaderboard_data :
                leaderboard_text =""
                for i ,(user_id ,count )in enumerate (leaderboard_data ,1 ):
                    medal ="🥇"if i ==1 else "🥈"if i ==2 else "🥉"if i ==3 else f"#{i}"
                    leaderboard_text +=f"{medal} <@{user_id}> - **{count}** counts\n"

                embed .description =leaderboard_text 
            else :
                embed .description ="No counting data available yet!"

            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to fetch leaderboard: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="global",description ="Show global leaderboard across all servers")
    async def counting_global (self ,ctx ):
        """Display global counting leaderboard"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                async with db .execute ("""
                SELECT user_id, SUM(total_counts) as total_counts, COUNT(DISTINCT guild_id) as guild_count
                FROM user_stats 
                GROUP BY user_id
                HAVING total_counts > 0
                ORDER BY total_counts DESC
                LIMIT 100
                """)as cursor :
                    leaderboard_data =await cursor .fetchall ()

            if not leaderboard_data :
                embed =discord .Embed (
                title ="🌍 "+await self .get_text (ctx .guild .id ,'global_leaderboard'),
                description ="No global counting data available yet!",
                color =0x000000 
                )
                await ctx .send (embed =embed )
                return 

            view =GlobalLeaderboardView (leaderboard_data )
            embed =view .create_leaderboard_embed ()
            await ctx .send (embed =embed ,view =view )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to fetch global leaderboard: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="stats",description ="Show counting statistics")
    async def counting_stats (self ,ctx ,user :Optional [discord .Member ]=None ):
        """Display user counting statistics"""
        target_user =user or ctx .author 

        try :
            user_stats =await self .get_user_stats (ctx .guild .id ,target_user .id )

            embed =discord .Embed (
            title =f"📊 Counting Stats - {target_user.display_name}",
            color =0x000000 
            )
            embed .set_thumbnail (url =target_user .display_avatar .url )

            embed .add_field (name ="Total Counts",value =str (user_stats ['total_counts']),inline =True )
            embed .add_field (name ="Highest Count",value =str (user_stats ['highest_count']),inline =True )

            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to fetch statistics: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="enable",description ="Enable counting in this server")
    @commands .has_permissions (administrator =True )
    async def counting_enable (self ,ctx ):
        """Enable counting functionality"""
        try :
            async with aiosqlite .connect ("db/counting.db")as db :
                await db .execute ("""
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, counting_enabled, reset_on_fail, enforce_alternating, language)
                VALUES (?, ?, 
                COALESCE((SELECT reset_on_fail FROM guild_settings WHERE guild_id = ?), TRUE),
                COALESCE((SELECT enforce_alternating FROM guild_settings WHERE guild_id = ?), TRUE),
                COALESCE((SELECT language FROM guild_settings WHERE guild_id = ?), 'en'))
                """,(ctx .guild .id ,True ,ctx .guild .id ,ctx .guild .id ,ctx .guild .id ))
                await db .commit ()

            embed =discord .Embed (
            title ="<:icon_tick:1372375089668161597> "+await self .get_text (ctx .guild .id ,'counting_enabled'),
            description ="Counting has been enabled for this server!",
            color =0x00FF00 
            )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to enable counting: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="disable",description ="Disable counting in this server")
    @commands .has_permissions (administrator =True )
    async def counting_disable (self ,ctx ):
        """Disable counting functionality and reset database"""
        try :

            await self .reset_guild_database (ctx .guild .id )

            embed =discord .Embed (
            title ="🔴 "+await self .get_text (ctx .guild .id ,'counting_disabled'),
            description ="Counting has been disabled and all data has been reset for this server!",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to disable counting: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="channel",description ="Set the counting channel")
    @commands .has_permissions (administrator =True )
    async def counting_channel (self ,ctx ,channel :discord .TextChannel =None ):
        """Set the counting channel"""
        try :
            if not channel :
                channel =ctx .channel 

            counting_data =await self .get_counting_data (ctx .guild .id )
            current_count =counting_data ['current_count']if counting_data else 0 

            await self .update_counting_data (ctx .guild .id ,current_count ,None ,channel .id )

            embed =discord .Embed (
            title ="<:icon_tick:1372375089668161597> "+await self .get_text (ctx .guild .id ,'channel_set'),
            description =f"Counting channel set to {channel.mention}!",
            color =0x00FF00 
            )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to set counting channel: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="reset",description ="Reset the counting to 0")
    @commands .has_permissions (administrator =True )
    async def counting_reset_cmd (self ,ctx ):
        """Reset counting to 0"""
        try :
            await self .reset_counting (ctx .guild .id )

            embed =discord .Embed (
            title ="🔄 "+await self .get_text (ctx .guild .id ,'reset'),
            description =await self .get_text (ctx .guild .id ,'count_reset'),
            color =0xFFFF00 
            )
            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to reset counting: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

    @counting_group .command (name ="info",description ="Show current counting information")
    async def counting_info (self ,ctx ):
        """Display current counting information"""
        try :
            counting_data =await self .get_counting_data (ctx .guild .id )
            settings =await self .get_guild_settings (ctx .guild .id )

            embed =discord .Embed (
            title ="ℹ️ Counting Information",
            color =0x000000 
            )

            if counting_data :
                embed .add_field (name ="Current Count",value =str (counting_data ['current_count']),inline =True )
                embed .add_field (name ="Channel",value =f"<#{counting_data['channel_id']}>"if counting_data ['channel_id']else "None",inline =True )
                if counting_data ['last_user_id']:
                    embed .add_field (name ="Last Counter",value =f"<@{counting_data['last_user_id']}>",inline =True )

                next_count =counting_data ['current_count']+1 
                embed .add_field (name ="Next Number",value =str (next_count ),inline =True )
            else :
                embed .description ="Counting not set up yet! Use `/counting config` to get started."

            embed .add_field (name ="Reset on Fail",value ="<:icon_tick:1372375089668161597>"if settings ['reset_on_fail']else "<:icon_cross:1372375094336425986>",inline =True )
            embed .add_field (name ="Alternating Users",value ="<:icon_tick:1372375089668161597>"if settings ['enforce_alternating']else "<:icon_cross:1372375094336425986>",inline =True )

            await ctx .send (embed =embed )

        except Exception as e :
            embed =discord .Embed (
            description =f"Failed to fetch counting info: {e}",
            color =0xFF0000 
            )
            await ctx .send (embed =embed )

async def setup (bot ):
    """Setup function for the cog"""
    await bot .add_cog (Counting (bot ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
