import discord 
from discord .ext import commands 
from discord import ui 

class HideUnhideView (ui .View ):
    def __init__ (self ,channel ,author ,ctx ):
        super ().__init__ (timeout =120 )
        self .channel =channel 
        self .author =author 
        self .ctx =ctx 
        self .message =None 

    async def interaction_check (self ,interaction :discord .Interaction )->bool :
        if interaction .user !=self .author :
            await interaction .response .send_message ("You are not allowed to interact with this!",ephemeral =True )
            return False 
        return True 

    async def on_timeout (self ):
        for item in self .children :
            if item .label !="Delete":
                item .disabled =True 
        if self .message :
            try :
                await self .message .edit (view =self )
            except Exception as e :
                pass 

    @ui .button (label ="Unhide",style =discord .ButtonStyle .success )
    async def unhide (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await self .channel .set_permissions (interaction .guild .default_role ,read_messages =True )
        await interaction .response .send_message (f"{self.channel.mention} has been unhidden.",ephemeral =True )

        embed =discord .Embed (
        description =f"<:icon_ignore:1373173575078379590> **Channel**: {self.channel.mention}\n<:icon_tick:1372375089668161597> **Status**: Unhidden\n <:icon_danger:1373170993236803688> **Reason:** Unhide request by {self.author}",
        color =0x000000 
        )
        embed .add_field (name ="<:icon_bot:1358327914646732901> **Moderator:**",value =self .ctx .author .mention ,inline =False )
        embed .set_author (name =f"Successfully Unhidden {self.channel.name}",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        await self .message .edit (embed =embed ,view =self )

        for item in self .children :
            if item .label !="Delete":
                item .disabled =True 
        await self .message .edit (view =self )

    @ui .button (style =discord .ButtonStyle .gray ,emoji ="<:delete:1372988987836469450>")
    async def delete (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .message .delete ()


class Hide (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .color =discord .Color .from_rgb (0 ,0 ,0 )

    @commands .hybrid_command (
    name ="hide",
    help ="Hides a channel from the default role (@everyone).",
    usage ="hide <channel>",
    aliases =["hidechannel"])
    @commands .has_permissions (manage_roles =True )
    @commands .bot_has_permissions (manage_roles =True )
    async def hide_command (self ,ctx ,channel :discord .TextChannel =None ):
        channel =channel or ctx .channel 
        if not channel .permissions_for (ctx .guild .default_role ).read_messages :
            embed =discord .Embed (
            description =f"**<:icon_ignore:1373173575078379590> Channel**: {channel.mention}\n<:icon_tick:1372375089668161597> **Status**: Already Hidden",
            color =self .color 
            )
            embed .set_author (name =f"{channel.name} is Already Hidden",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
            embed .set_footer (text =f"Requested by {ctx.author}",icon_url =ctx .author .avatar .url )
            view =HideUnhideView (channel =channel ,author =ctx .author ,ctx =ctx )
            message =await ctx .send (embed =embed ,view =view )
            view .message =message 
            return 

        await channel .set_permissions (ctx .guild .default_role ,read_messages =False )

        embed =discord .Embed (
        description =f"<:icon_ignore:1373173575078379590> **Channel**: {channel.mention}\n<:icon_tick:1372375089668161597> **Status**: Hidden\n<:icon_danger:1373170993236803688> **Reason:** Hide request by {ctx.author}",
        color =self .color 
        )
        embed .add_field (name ="<:icon_bot:1358327914646732901> **Moderator:**",value =ctx .author .mention ,inline =False )
        embed .set_author (name =f"Successfully Hidden {channel.name}",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        embed .set_footer (text =f"Requested by {ctx.author}",icon_url =ctx .author .avatar .url )
        view =HideUnhideView (channel =channel ,author =ctx .author ,ctx =ctx )
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
