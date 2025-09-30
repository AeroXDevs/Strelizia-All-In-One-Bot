
import discord 
import logging 
import asyncio 
import traceback 
from discord .ext import commands 
from utils .Tools import get_ignore_data 
from core import Strelizia ,Cog ,Context 


_error_handled =set ()


logger =logging .getLogger (__name__ )
if not logger .handlers :
    handler =logging .FileHandler ('logs/bot_errors.log')
    handler .setLevel (logging .ERROR )
    formatter =logging .Formatter ('%(asctime)s %(levelname)s:%(message)s')
    handler .setFormatter (formatter )
    logger .addHandler (handler )
    logger .setLevel (logging .ERROR )


discord_logger =logging .getLogger ('discord')
class CheckFailureFilter (logging .Filter ):
    def filter (self ,record ):
        message =record .getMessage ().lower ()


        if any (embed_phrase in message for embed_phrase in [
        'embed',
        'discord.embed',
        'embeds',
        'embed_',
        'set_embed'
        ]):
            return True 


        if any (phrase in message for phrase in [
        'check functions for command',
        'failed',
        'command raised an exception'
        ]):
            return False 


        if 'error'in message and not any (embed_phrase in message for embed_phrase in [
        'embed',
        'discord.embed',
        'embeds'
        ]):
            return False 

        return True 


discord_logger .addFilter (CheckFailureFilter ())
for handler in discord_logger .handlers :
    handler .addFilter (CheckFailureFilter ())


commands_logger =logging .getLogger ('discord.ext.commands')
commands_logger .addFilter (CheckFailureFilter ())
for handler in commands_logger .handlers :
    handler .addFilter (CheckFailureFilter ())

class Errors (Cog ):
    def __init__ (self ,client :Strelizia ):
        self .client =client 
        self ._error_cache =set ()
        self ._processing_errors =set ()
        self ._sent_errors =set ()

    @commands .Cog .listener ()
    async def on_error (self ,event ,*args ,**kwargs ):
        """Handle general bot errors"""
        logger .error (f"Error in event {event}: {traceback.format_exc()}")

    async def cog_load (self ):
        """Called when the cog is loaded"""
        logger .info ("Error handling cog loaded successfully")

        self .client .loop .create_task (self ._cleanup_task ())

    async def _cleanup_task (self ):
        """Periodically clean up old error tracking data"""
        while True :
            try :
                await asyncio .sleep (300 )

                if len (self ._sent_errors )>50 :
                    self ._sent_errors .clear ()
                if len (self ._processing_errors )>50 :
                    self ._processing_errors .clear ()
            except Exception as e :
                pass 

    @commands .Cog .listener ()
    async def on_command_error (self ,ctx :Context ,error ):
        if ctx .command is None :
            return 


        command_key =(ctx .message .id ,ctx .command .name )
        error_key =(ctx .message .id ,ctx .command .name ,type (error ).__name__ )


        if command_key in self ._sent_errors or error_key in self ._processing_errors :
            return 


        _error_handled .add (command_key )

        self ._processing_errors .add (error_key )
        self ._sent_errors .add (command_key )

        try :

            if isinstance (error ,commands .CommandInvokeError ):
                error =error .original 


            if isinstance (error ,commands .CheckFailure ):

                try :
                    data =await get_ignore_data (ctx .guild .id )
                    ch =data .get ("channel",[])
                    iuser =data .get ("user",[])
                    cmd =data .get ("command",[])
                    buser =data .get ("bypassuser",[])

                    if str (ctx .author .id )in buser :
                        return 

                    if str (ctx .channel .id )in ch :
                        await ctx .reply (
                        f"{ctx.author.mention} This **channel** is on the **ignored** list. Please try my commands in another channel.",
                        delete_after =8 
                        )
                        return 

                    if str (ctx .author .id )in iuser :
                        await ctx .reply (
                        f"{ctx.author.mention} You are set as an **ignored user** for this guild. Please try my commands or modules in a different guild.",
                        delete_after =8 
                        )
                        return 

                    if ctx .command .name in cmd or any (alias in cmd for alias in ctx .command .aliases ):
                        await ctx .reply (
                        f"{ctx.author.mention} This **command is ignored** in this guild. Please use other commands or try this command in a different guild.",
                        delete_after =8 
                        )
                        return 
                except Exception as e :

                    pass 


                return 


            logger .error (f"Error in command {ctx.command} invoked by {ctx.author} ({ctx.author.id}): {error}",exc_info =True )


            if isinstance (error ,commands .MissingRequiredArgument ):
                await ctx .send_help (ctx .command )
                ctx .command .reset_cooldown (ctx )
                return 

            if isinstance (error ,commands .NoPrivateMessage ):
                embed =discord .Embed (
                color =0x000000 ,
                description ="You can't use my commands in DMs."
                )
                embed .set_author (
                name =ctx .author ,
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                embed .set_thumbnail (
                url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =20 )
                return 

            if isinstance (error ,commands .TooManyArguments ):
                await ctx .send_help (ctx .command )
                ctx .command .reset_cooldown (ctx )
                return 

            if isinstance (error ,commands .CommandOnCooldown ):
                embed =discord .Embed (
                color =0x000000 ,
                description =f"{ctx.author.mention} Whoa, slow down there! You can run the command again in **{error.retry_after:.2f}** seconds."
                )
                embed .set_author (name ="Cooldown",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                return 

            if isinstance (error ,commands .MaxConcurrencyReached ):
                embed =discord .Embed (
                color =0x000000 ,
                description =f"{ctx.author.mention} This command is already in progress. Please let it finish and try again afterward."
                )
                embed .set_author (name ="Command in Progress",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                ctx .command .reset_cooldown (ctx )
                return 

            if isinstance (error ,commands .MissingPermissions ):
                missing =[perm .replace ("_"," ").replace ("guild","server").title ()for perm in error .missing_permissions ]
                fmt ="{}, and {}".format (", ".join (missing [:-1 ]),missing [-1 ])if len (missing )>2 else " and ".join (missing )
                embed =discord .Embed (
                color =0x000000 ,
                description =f"You lack the **{fmt}** permission(s) to run the **{ctx.command.name}** command!"
                )
                embed .set_author (name ="Missing Permissions",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                ctx .command .reset_cooldown (ctx )
                return 

            if isinstance (error ,commands .BadArgument ):
                await ctx .send_help (ctx .command )
                ctx .command .reset_cooldown (ctx )
                return 

            if isinstance (error ,commands .BotMissingPermissions ):
                missing =[perm .replace ("_"," ").replace ("guild","server").title ()for perm in error .missing_permissions ]
                fmt ="{}, and {}".format (", ".join (missing [:-1 ]),missing [-1 ])if len (missing )>2 else " and ".join (missing )
                embed =discord .Embed (
                color =0x000000 ,
                description =f"I need the **{fmt}** permission(s) to run the **{ctx.command.qualified_name}** command!"
                )
                embed .set_author (name ="Bot Missing Permissions",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                return 


            if isinstance (error ,discord .Forbidden ):
                embed =discord .Embed (
                color =0x000000 ,
                description ="I don't have permission to perform this action."
                )
                embed .set_author (name ="Permission Error",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                return 

            if isinstance (error ,discord .HTTPException ):
                embed =discord .Embed (
                color =0x000000 ,
                description ="A Discord API error occurred. Please try again later."
                )
                embed .set_author (name ="API Error",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                return 


            if "database"in str (error ).lower ()or "sqlite"in str (error ).lower ():
                embed =discord .Embed (
                color =0x000000 ,
                description ="A database error occurred. Please try again later."
                )
                embed .set_author (name ="Database Error",icon_url =self .client .user .avatar .url )
                embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
                embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                await ctx .reply (embed =embed ,delete_after =10 )
                return 


            embed =discord .Embed (
            color =0x000000 ,
            description ="An unexpected error occurred. Please try again later."
            )
            embed .set_author (name ="Unexpected Error",icon_url =self .client .user .avatar .url )
            embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")
            embed .set_footer (
            text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            await ctx .reply (embed =embed ,delete_after =15 )

        except Exception as send_error :

            logger .error (f"Failed to send error message for command {ctx.command}: {send_error}")

        finally :

            self ._processing_errors .discard (error_key )


            if len (self ._processing_errors )>100 :
                self ._processing_errors .clear ()
            if len (self ._sent_errors )>200 :
                self ._sent_errors .clear ()

    @commands .Cog .listener ()
    async def on_application_command_error (self ,interaction :discord .Interaction ,error ):
        """Handle slash command errors"""
        logger .error (f"Application command error: {error}",exc_info =True )


        embed =discord .Embed (color =0x000000 )
        embed .set_thumbnail (url ="https://cdn.discordapp.com/emojis/1339632539354136701.png")

        if isinstance (error ,commands .MissingPermissions ):
            missing =[perm .replace ("_"," ").replace ("guild","server").title ()for perm in error .missing_permissions ]
            fmt ="{}, and {}".format (", ".join (missing [:-1 ]),missing [-1 ])if len (missing )>2 else " and ".join (missing )
            embed .title ="Missing Permissions"
            embed .description =f"You need the **{fmt}** permission(s) to use this command."
        elif isinstance (error ,commands .BotMissingPermissions ):
            missing =[perm .replace ("_"," ").replace ("guild","server").title ()for perm in error .missing_permissions ]
            fmt ="{}, and {}".format (", ".join (missing [:-1 ]),missing [-1 ])if len (missing )>2 else " and ".join (missing )
            embed .title ="Bot Missing Permissions"
            embed .description =f"I need the **{fmt}** permission(s) to run this command."
        elif isinstance (error ,discord .Forbidden ):
            embed .title ="Permission Error"
            embed .description ="I don't have permission to perform this action."
        elif isinstance (error ,discord .NotFound ):
            embed .title ="Not Found"
            embed .description ="The requested resource was not found."
        else :
            embed .title ="Unexpected Error"
            embed .description ="An unexpected error occurred. Please try again later."

        try :
            if interaction .response .is_done ():
                await interaction .followup .send (embed =embed ,ephemeral =True )
            else :
                await interaction .response .send_message (embed =embed ,ephemeral =True )
        except Exception as e :
            logger .error (f"Failed to send slash command error message: {e}")

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
