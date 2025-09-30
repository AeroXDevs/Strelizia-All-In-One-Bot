import discord 
from discord .ext import commands 
from datetime import datetime ,timezone 
from utils .Tools import *

class SnipeView (discord .ui .View ):
    def __init__ (self ,bot ,snipes ,user_id ):
        super ().__init__ (timeout =120 )
        self .bot =bot 
        self .snipes =snipes 
        self .index =0 
        self .user_id =user_id 
        self .update_buttons ()

    def update_buttons (self ):
        self .first_button .disabled =self .index ==0 or len (self .snipes )==1 
        self .prev_button .disabled =self .index ==0 or len (self .snipes )==1 
        self .next_button .disabled =self .index ==len (self .snipes )-1 or len (self .snipes )==1 
        self .last_button .disabled =self .index ==len (self .snipes )-1 or len (self .snipes )==1 

    async def send_snipe_embed (self ,interaction :discord .Interaction ):
        snipe =self .snipes [self .index ]
        embed =discord .Embed (color =0x000000 )
        embed .set_author (name =f"Deleted Message {self.index + 1}/{len(self.snipes)}",icon_url =snipe ['author_avatar'])
        uid =snipe ['author_id']
        display_name =snipe ['author_name']


        current_time =int (datetime .now (timezone .utc ).timestamp ())
        time_diff =current_time -snipe ['deleted_at']

        if time_diff <60 :
            time_ago =f"{time_diff} second{'s' if time_diff != 1 else ''} ago"
        elif time_diff <3600 :
            minutes =time_diff //60 
            time_ago =f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_diff <86400 :
            hours =time_diff //3600 
            time_ago =f"{hours} hour{'s' if hours != 1 else ''} ago"
        else :
            days =time_diff //86400 
            time_ago =f"{days} day{'s' if days != 1 else ''} ago"

        embed .description =(
        f"**Author:** **[{display_name}](https://discord.com/users/{uid})**\n"
        f"**Author ID:** `{snipe['author_id']}`\n"
        f"**Author Mention:** <@{snipe['author_id']}>\n"
        f"**Deleted:** {time_ago}\n"
        )

        if snipe ['content']:
            embed .add_field (name ="<:delete:1372988987836469450> **Content:**",value =snipe ['content'])
        if snipe ['attachments']:
            attachment_links ="\n".join ([f"[{attachment['name']}]({attachment['url']})"for attachment in snipe ['attachments']])
            embed .add_field (name ="**Attachments:**",value =attachment_links )

        embed .set_footer (text =f"Total Deleted Messages: {len(self.snipes)} | Requested by {interaction.user}",icon_url =interaction .user .avatar .url )
        await interaction .response .edit_message (embed =embed ,view =self )

    async def interaction_check (self ,interaction :discord .Interaction )->bool :
        return interaction .user .id ==self .user_id 

    @discord .ui .button (emoji ="<:forward:1329361532999569439>",style =discord .ButtonStyle .secondary ,custom_id ="first")
    async def first_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        self .index =0 
        self .update_buttons ()
        await self .send_snipe_embed (interaction )

    @discord .ui .button (emoji ="<:rewind1:1329360839874056225>",style =discord .ButtonStyle .secondary ,custom_id ="previous")
    async def prev_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if self .index >0 :
            self .index -=1 
        self .update_buttons ()
        await self .send_snipe_embed (interaction )

    @discord .ui .button (emoji ="<:delete:1372988987836469450>",style =discord .ButtonStyle .danger ,custom_id ="delete")
    async def delete_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .message .delete ()

    @discord .ui .button (emoji ="<:forward:1329361532999569439>",style =discord .ButtonStyle .secondary ,custom_id ="next")
    async def next_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if self .index <len (self .snipes )-1 :
            self .index +=1 
        self .update_buttons ()
        await self .send_snipe_embed (interaction )

    @discord .ui .button (emoji ="<:rewind1:1329360839874056225>",style =discord .ButtonStyle .secondary ,custom_id ="last")
    async def last_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        self .index =len (self .snipes )-1 
        self .update_buttons ()
        await self .send_snipe_embed (interaction )

    async def on_timeout (self ):
        for child in self .children :
            child .disabled =True 
        await self .message .edit (view =self )


class Snipe (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .snipes ={}

    @commands .Cog .listener ()
    async def on_message_delete (self ,message ):
        if not message .guild or message .author .bot :
            return 
        if message .channel .id not in self .snipes :
            self .snipes [message .channel .id ]=[]
        if len (self .snipes [message .channel .id ])>=10 :
            self .snipes [message .channel .id ].pop (0 )

        attachments =[]
        if message .attachments :
            attachments =[{'name':attachment .filename ,'url':attachment .url }for attachment in message .attachments ]


        deleted_at =int (datetime .now (timezone .utc ).timestamp ())

        self .snipes [message .channel .id ].insert (0 ,{
        'author_name':message .author .name ,
        'author_avatar':message .author .avatar .url if message .author .avatar else None ,
        'author_id':message .author .id ,
        'content':message .content or None ,
        'deleted_at':deleted_at ,
        'attachments':attachments 
        })

    @commands .hybrid_command (name ='snipe',help ="Shows the recently deleted messages in the channel.")
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,3 ,commands .BucketType .user )
    async def snipe (self ,ctx ):
        channel_snipes =self .snipes .get (ctx .channel .id ,[])
        if not channel_snipes :
            await ctx .send ("No recently deleted messages found in this channel.")
            return 

        first_snipe =channel_snipes [0 ]
        embed =discord .Embed (color =0x000000 )
        embed .set_author (name ="Last Deleted Message",icon_url =first_snipe ['author_avatar'])
        uid =first_snipe ['author_id']
        display_name =first_snipe ['author_name']

        current_time =int (datetime .now (timezone .utc ).timestamp ())
        time_diff =current_time -first_snipe ['deleted_at']

        if time_diff <60 :
            time_ago =f"{time_diff} second{'s' if time_diff != 1 else ''} ago"
        elif time_diff <3600 :
            minutes =time_diff //60 
            time_ago =f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        elif time_diff <86400 :
            hours =time_diff //3600 
            time_ago =f"{hours} hour{'s' if hours != 1 else ''} ago"
        else :
            days =time_diff //86400 
            time_ago =f"{days} day{'s' if days != 1 else ''} ago"

        embed .description =(
        f"**Author:** **[{display_name}](https://discord.com/users/{uid})**\n"
        f"**Author ID:** `{first_snipe['author_id']}`\n"
        f"**Author Mention:** <@{first_snipe['author_id']}>\n"
        f"**Deleted:** {time_ago}\n"
        )

        if first_snipe ['content']:
            embed .add_field (name ="<:delete:1372988987836469450> **Content:**",value =first_snipe ['content'])
        if first_snipe ['attachments']:
            attachment_links ="\n".join ([f"[{attachment['name']}]({attachment['url']})"for attachment in first_snipe ['attachments']])
            embed .add_field (name ="**Attachments:**",value =attachment_links )

        embed .set_footer (text =f"Total Deleted Messages: {len(channel_snipes)} | Requested by {ctx.author}",icon_url =ctx .author .avatar .url )

        view =SnipeView (self .bot ,channel_snipes ,ctx .author .id )

        if len (channel_snipes )>1 :
            message =await ctx .send (embed =embed ,view =view )
            view .message =message 
        else :
            view .first_button .disabled =True 
            view .prev_button .disabled =True 
            view .next_button .disabled =True 
            view .last_button .disabled =True 
            message =await ctx .send (embed =embed ,view =view )
            view .message =message 

"""
@Author: Aegis
    + Discord: Solcodez
    + Community: https://discord.strelix.xyz (AeroX Development)
    + for any queries reach out Community or DM me.
"""
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
