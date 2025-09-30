import discord 
from discord .ext import commands 
import logging 
import re 
from typing import Optional 

class AIResponses (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    @commands .Cog .listener ()
    async def on_ready (self ):
        pass 

    @commands .Cog .listener ()
    async def on_message (self ,message ):

        if message .author .bot or not message .guild :
            return 


        if self .bot .user not in message .mentions :
            return 


        content =message .content 
        for mention in message .mentions :
            content =content .replace (f'<@{mention.id}>','').replace (f'<@!{mention.id}>','')
        content =content .strip ()

        if not content :

            embed =discord .Embed (
            title ="💕 Hey there!",
            description =(
            f"Hi sweetie! I'm **Strelizia**, your caring Discord companion! ✨\n\n"
            f"💬 **Chat with me**: Use `&ai <your message>` to have a conversation!\n"
            f"📚 **My commands**: Use `&help` to see all my 700+ commands!\n"
            f"🎯 **Quick help**: Use `&help <category>` for specific features\n\n"
            f"What can I help you with today? 💖"
            ),
            color =0xff69b4 
            )
            embed .set_footer (text ="Made with love by AeroX Development 💕")
            await message .reply (embed =embed ,mention_author =True )
            return 


        embed =discord .Embed (
        title ="💭 Let's chat!",
        description =(
        f"I'd love to help you with that! 💕\n\n"
        f"💬 **For conversations**: Use `&ai {content}` and we can talk!\n"
        f"📚 **For commands**: Use `&help` to explore my features\n"
        f"🎯 **Quick help**: Try `&help <category>` for specific topics\n\n"
        f"What would you like to know more about? ✨"
        ),
        color =0xff69b4 
        )
        embed .set_footer (text ="Powered by AeroX Development")
        await message .reply (embed =embed ,mention_author =True )

async def setup (bot ):
    await bot .add_cog (AIResponses (bot ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
