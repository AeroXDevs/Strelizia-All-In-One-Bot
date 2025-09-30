import discord 
import functools 
from utils .Tools import *


class Dropdown (discord .ui .Select ):

    def __init__ (self ,ctx ,options ,placeholder ="Choose a Category for Help",row =None ):
        super ().__init__ (placeholder =placeholder ,
        min_values =1 ,
        max_values =1 ,
        options =options ,
        row =row )
        self .invoker =ctx .author 

    async def callback (self ,interaction :discord .Interaction ):
        if self .invoker ==interaction .user :
            index =self .view .find_index_from_select (self .values [0 ])
            if not index :
                index =0 
            await self .view .set_page (index ,interaction )
        else :
            await interaction .response .send_message (
            "You must run this command to interact with it.",ephemeral =True )


class Button (discord .ui .Button ):

    def __init__ (self ,command ,ctx ,label ,style :discord .ButtonStyle ,emoji =None ,args =None ):
        disable =False 
        if args ==-1 or args ==0 :
            disable =True 
        super ().__init__ (label =label ,style =style ,emoji =emoji ,disabled =disable )
        self .command =command 
        self .invoker =ctx .author 
        self .args =args 

    async def callback (self ,interaction :discord .Interaction ):
        if self .invoker ==interaction .user :
            if self .args or self .args ==0 :
                func =functools .partial (self .command ,self .args ,interaction )
                await func ()
            else :
                await self .command (interaction )
        else :
            await interaction .response .send_message (
            "You must run this command to interact with it.",ephemeral =True )


class View (discord .ui .View ):

    def __init__ (self ,mapping :dict ,ctx :discord .ext .commands .context .Context ,homeembed :discord .embeds .Embed ,ui :int ):
        super ().__init__ (timeout =None )
        self .mapping ,self .ctx ,self .home =mapping ,ctx ,homeembed 
        self .index ,self .buttons =0 ,None 
        self .current_page =0 

        self .options ,self .embeds ,self .total_pages =self .gen_embeds ()

        if ui ==0 :

            self .add_item (Dropdown (ctx =self .ctx ,options =self .options ))
        elif ui ==1 :

            self .buttons =self .add_buttons ()
        elif ui ==2 :

            self .buttons =self .add_buttons ()

            mid_point =len (self .options )//2 
            options_1 =self .options [:mid_point ]
            options_2 =self .options [mid_point :]


            if options_1 :
                self .add_item (Dropdown (ctx =self .ctx ,options =options_1 ,placeholder ="Core Commands",row =1 ))

            if options_2 :
                self .add_item (Dropdown (ctx =self .ctx ,options =options_2 ,placeholder ="Extra Commands",row =2 ))
        else :

            self .buttons =self .add_buttons ()
            self .add_item (Dropdown (ctx =self .ctx ,options =self .options ))

    def add_buttons (self ):

        self .homeB =discord .ui .Button (label ="",
        emoji ="<:SageDoubleArrowLeft:1385846432535412758>",
        style =discord .ButtonStyle .secondary )
        self .homeB .callback =self .home_callback 


        self .backB =discord .ui .Button (label ="",
        emoji ="<:arrow_left:1385846548625363117>",
        style =discord .ButtonStyle .secondary )
        self .backB .callback =self .back_callback 


        self .nextB =discord .ui .Button (label ="",
        emoji ="<:arrow_right:1385846525204103252>",
        style =discord .ButtonStyle .secondary )
        self .nextB .callback =self .next_callback 


        self .lastB =discord .ui .Button (label ="",
        emoji ="<:SageDoubleArrowRight:1385846409902948362>",
        style =discord .ButtonStyle .secondary )
        self .lastB .callback =self .last_callback 

        buttons =[self .homeB ,self .backB ,self .nextB ,self .lastB ]
        for button in buttons :
            self .add_item (button )
        return buttons 

    async def home_callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You must run this command to interact with it.",ephemeral =True )
            return 
        await self .set_page (0 ,interaction )

    async def back_callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You must run this command to interact with it.",ephemeral =True )
            return 
        current_page =self .index -1 if self .index >0 else len (self .embeds )-1 
        await self .set_page (current_page ,interaction )

    async def quit_callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You must run this command to interact with it.",ephemeral =True )
            return 
        await self .quit (interaction )

    async def next_callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You must run this command to interact with it.",ephemeral =True )
            return 
        current_page =self .index +1 if self .index <len (self .embeds )-1 else 0 
        await self .set_page (current_page ,interaction )

    async def last_callback (self ,interaction :discord .Interaction ):
        if interaction .user !=self .ctx .author :
            await interaction .response .send_message ("You must run this command to interact with it.",ephemeral =True )
            return 
        await self .set_page (len (self .embeds )-1 ,interaction )

    def find_index_from_select (self ,value ):
        i =0 
        used_labels =set ()

        for cog in self .get_cogs ():

            if cog .__class__ .__name__ =="Roleplay":
                continue 

            if "help_custom"in dir (cog ):
                _ ,label ,_ =cog .help_custom ()


                original_label =label 
                counter =1 
                while label in used_labels :
                    label =f"{original_label} {counter}"
                    counter +=1 

                used_labels .add (label )


                if label ==value or value .startswith (original_label +" "):
                    return i +1 
                i +=1 

        return 0 

    def get_cogs (self ):
        return list (self .mapping .keys ())

    def gen_embeds (self ):
        options ,embeds =[],[]
        total_pages =0 
        used_labels =set ()

        options .append (
        discord .SelectOption (label ="Home",
        emoji ='<:icons_home:1337295807430393958>',description =""))
        embeds .append (self .home )
        total_pages +=1 
        used_labels .add ("Home")

        for cog in self .get_cogs ():

            if cog .__class__ .__name__ =="Roleplay":
                continue 

            if "help_custom"in dir (cog ):
                emoji ,label ,description =cog .help_custom ()


                original_label =label 
                counter =1 
                while label in used_labels :
                    label =f"{original_label} {counter}"
                    counter +=1 

                used_labels .add (label )
                options .append (discord .SelectOption (label =label ,emoji =emoji ,description =description ))


                embed =discord .Embed (title =f"{emoji} {original_label}",
                color =0x000000 )

                for command in cog .get_commands ():
                    params =""
                    for param in command .clean_params :
                        if param not in ["self","ctx"]:
                            params +=f" <{param}>"


                    help_text =command .help or "No description available"
                    if len (help_text )>1020 :
                        help_text =help_text [:1017 ]+"..."

                    embed .add_field (name =f"{command.name}{params}",
                    value =f"{help_text}\n\u200b",
                    inline =False )

                embeds .append (embed )
                total_pages +=1 

        self .home .set_footer (text =f"• Help page 1/{total_pages} | Requested by: {self.ctx.author.display_name}",
        icon_url =f"{self.ctx.bot.user.avatar.url}")

        return options ,embeds ,total_pages 

    async def quit (self ,interaction :discord .Interaction ):
        await interaction .response .defer ()
        await interaction .delete_original_response ()

    async def to_page (self ,page :int ,interaction :discord .Interaction ):
        if not self .index +page <0 or not self .index +page >len (self .options ):
            await self .set_index (page )
            embed =self .embeds [self .index ]
            embed .set_footer (text =f"• Help page {self.index + 1}/{self.total_pages} | Requested by: {self.ctx.author.display_name}",
            icon_url =f"{self.ctx.bot.user.avatar.url}")
            await interaction .response .edit_message (embed =embed ,view =self )

    async def set_page (self ,page :int ,interaction :discord .Interaction ):
        self .index =page 
        self .current_page =page 
        await self .to_page (0 ,interaction )

    async def set_index (self ,page ):
        self .index +=page 
        if self .buttons :
            for button in self .buttons [0 :-1 ]:
                button .disabled =False 
            if self .index ==0 :
                self .backB .disabled =True 
            elif self .index ==len (self .options )-1 :
                self .nextB .disabled =True 

    async def set_last_page (self ,interaction :discord .Interaction ):
        await self .set_page (len (self .options )-1 ,interaction )
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
