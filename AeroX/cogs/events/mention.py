from utils import getConfig 

import discord 

from discord .ext import commands 

from utils .Tools import get_ignore_data 

import aiosqlite 

class Mention (commands .Cog ):

    def __init__ (self ,bot ):

        self .bot =bot 

        self .color =0x000000 

        self .bot_name ="Strelizia"

    async def is_blacklisted (self ,message ):

        async with aiosqlite .connect ("db/block.db")as db :

            cursor =await db .execute ("SELECT 1 FROM guild_blacklist WHERE guild_id = ?",(message .guild .id ,))

            if await cursor .fetchone ():

                return True 



            cursor =await db .execute ("SELECT 1 FROM user_blacklist WHERE user_id = ?",(message .author .id ,))

            if await cursor .fetchone ():

                return True 

        return False 

    @commands .Cog .listener ()

    async def on_message (self ,message ):

        if message .author .bot or not message .guild :

            return 

        if await self .is_blacklisted (message ):

            return 

        ignore_data =await get_ignore_data (message .guild .id )

        if str (message .author .id )in ignore_data ["user"]or str (message .channel .id )in ignore_data ["channel"]:

            return 

        if message .reference and message .reference .resolved :

            if isinstance (message .reference .resolved ,discord .Message ):

                if message .reference .resolved .author .id ==self .bot .user .id :

                    return 

        guild_id =message .guild .id 

        data =await getConfig (guild_id )

        prefix =data ["prefix"]

        if self .bot .user in message .mentions :
            if len (message .content .strip ().split ())==1 :

                custom_image_url ="https://cdn.discordapp.com/attachments/1386644896622055435/1387413915759022160/Fun_Purple_Girl_Gamer_Illustration_Twitch_Banner_20250618_132215_0000.png"

                embed =discord .Embed (
                color =self .color ,
                description =(
                f"**Greetings, <@{message.author.id}>**\n"
                f"**Prefix for this server:** `{prefix}`\n\n"
                f"> `Strelizia is a refined and intelligent presence—elegant, calm, and built to empower your server.`\n"
                f"> `She listens when needed, acts with precision, and adds a layer of style to every interaction.`\n"
                f"> `From moderation to utility, she does it all—quietly, efficiently, and beautifully.`\n"
                f"> `Not just a bot. A companion.`\n\n"
                )
                )
                embed .set_author (
                name =self .bot .user .display_name ,
                icon_url =self .bot .user .avatar .url 
                )
                embed .set_thumbnail (url =self .bot .user .avatar .url )
                embed .set_image (url =custom_image_url )
                embed .set_footer (
                text ="🩶 Welcome to her sanctuary.",
                icon_url =self .bot .user .avatar .url 
                )
                embed .timestamp =discord .utils .utcnow ()
                await message .channel .send (embed =embed )
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
