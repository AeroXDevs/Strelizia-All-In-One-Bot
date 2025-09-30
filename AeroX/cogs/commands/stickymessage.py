import discord 
import aiosqlite 
import json 
import asyncio 
from discord .ext import commands 
from typing import Optional ,Union 


class StickyMessage (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        asyncio .create_task (self .setup_database ())

    """Sticky Message commands"""

    def help_custom (self ):
        emoji ='<:sticky:1396894496519884851>'
        label ="Sticky Messages"
        description ="Sticky message system with embed support"
        return emoji ,label ,description 

    async def setup_database (self ):
        """Initialize sticky message database tables"""
        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                CREATE TABLE IF NOT EXISTS sticky_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id INTEGER NOT NULL,
                    channel_id INTEGER NOT NULL,
                    message_type TEXT DEFAULT 'plain',
                    message_content TEXT,
                    embed_data TEXT,
                    last_message_id INTEGER,
                    enabled BOOLEAN DEFAULT 1,
                    delay_seconds INTEGER DEFAULT 3,
                    auto_delete_after INTEGER DEFAULT 0,
                    ignore_bots BOOLEAN DEFAULT 1,
                    ignore_commands BOOLEAN DEFAULT 1,
                    trigger_count INTEGER DEFAULT 1,
                    current_count INTEGER DEFAULT 0,
                    UNIQUE(guild_id, channel_id)
                )
            """)

            await db .execute ("""
                CREATE TABLE IF NOT EXISTS sticky_settings (
                    guild_id INTEGER PRIMARY KEY,
                    max_sticky_per_guild INTEGER DEFAULT 10,
                    default_delay INTEGER DEFAULT 3,
                    allow_multiple_per_channel BOOLEAN DEFAULT 0
                )
            """)
            await db .commit ()

    @commands .group (aliases =['sticky','sm'],invoke_without_command =True )
    @commands .has_permissions (manage_messages =True )
    async def stickymessage (self ,ctx ):
        """Advanced sticky message management system"""
        if ctx .invoked_subcommand is None :
            await ctx .send_help (ctx .command )

    @stickymessage .command (name ='setup')
    @commands .has_permissions (manage_messages =True )
    async def sticky_setup (self ,ctx ,channel :Optional [discord .TextChannel ]=None ):
        """Setup a new sticky message in a channel"""
        if channel is None :
            channel =ctx .channel 


        async with aiosqlite .connect ("db/stickymessages.db")as db :
            cursor =await db .execute (
            "SELECT id FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (ctx .guild .id ,channel .id )
            )
            existing =await cursor .fetchone ()

            if existing :
                embed =discord .Embed (
                title ="Sticky Already Exists",
                description =f"A sticky message already exists in {channel.mention}.\nUse `{ctx.prefix}stickymessage edit #{channel.name}` to modify it.",
                color =0x000000 
                )
                return await ctx .send (embed =embed )


        setup_embed =discord .Embed (
        title ="Sticky Message Setup",
        description =f"Setting up sticky message for {channel.mention}\nChoose the message type:",
        color =0x000000 
        )


        view =StickySetupView (ctx ,channel )
        await ctx .send (embed =setup_embed ,view =view )

    @stickymessage .command (name ='remove',aliases =['delete','del'])
    @commands .has_permissions (manage_messages =True )
    async def sticky_remove (self ,ctx ,channel :Optional [discord .TextChannel ]=None ):
        """Remove sticky message from a channel"""
        if channel is None :
            channel =ctx .channel 

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            cursor =await db .execute (
            "SELECT id, last_message_id FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (ctx .guild .id ,channel .id )
            )
            sticky_data =await cursor .fetchone ()

            if not sticky_data :
                embed =discord .Embed (
                title ="No Sticky Found",
                description =f"No sticky message exists in {channel.mention}",
                color =0x000000 
                )
                return await ctx .send (embed =embed )


            if sticky_data [1 ]:
                try :
                    last_message =await channel .fetch_message (sticky_data [1 ])
                    await last_message .delete ()
                except :
                    pass 


            await db .execute (
            "DELETE FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (ctx .guild .id ,channel .id )
            )
            await db .commit ()

        embed =discord .Embed (
        title ="Sticky Removed",
        description =f"Successfully removed sticky message from {channel.mention}",
        color =0x000000 
        )
        await ctx .send (embed =embed )

    @stickymessage .command (name ='list')
    @commands .has_permissions (manage_messages =True )
    async def sticky_list (self ,ctx ):
        """List all sticky messages in the server"""
        async with aiosqlite .connect ("db/stickymessages.db")as db :
            cursor =await db .execute (
            """SELECT channel_id, message_type, enabled, delay_seconds 
                   FROM sticky_messages WHERE guild_id = ?""",
            (ctx .guild .id ,)
            )
            sticky_messages =await cursor .fetchall ()

        if not sticky_messages :
            embed =discord .Embed (
            title ="No Sticky Messages",
            description ="No sticky messages are configured in this server.",
            color =0x000000 
            )
            return await ctx .send (embed =embed )

        embed =discord .Embed (
        title ="Sticky Messages",
        description =f"Active sticky messages in **{ctx.guild.name}**:",
        color =0x000000 
        )

        for channel_id ,msg_type ,enabled ,delay in sticky_messages :
            channel =self .bot .get_channel (channel_id )
            if channel :
                status ="Enabled"if enabled else "Disabled"
                embed .add_field (
                name =f"#{channel.name}",
                value =f"Type: {msg_type.title()}\nStatus: {status}\nDelay: {delay}s",
                inline =True 
                )

        await ctx .send (embed =embed )

    @stickymessage .command (name ='toggle')
    @commands .has_permissions (manage_messages =True )
    async def sticky_toggle (self ,ctx ,channel :Optional [discord .TextChannel ]=None ):
        """Enable/disable sticky message in a channel"""
        if channel is None :
            channel =ctx .channel 

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            cursor =await db .execute (
            "SELECT enabled FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (ctx .guild .id ,channel .id )
            )
            result =await cursor .fetchone ()

            if not result :
                embed =discord .Embed (
                title ="No Sticky Found",
                description =f"No sticky message exists in {channel.mention}",
                color =0x000000 
                )
                return await ctx .send (embed =embed )

            new_status =not result [0 ]
            await db .execute (
            "UPDATE sticky_messages SET enabled = ? WHERE guild_id = ? AND channel_id = ?",
            (new_status ,ctx .guild .id ,channel .id )
            )
            await db .commit ()

        status_text ="enabled"if new_status else "disabled"

        embed =discord .Embed (
        title =f"Sticky {status_text.title()}",
        description =f"Sticky message in {channel.mention} has been **{status_text}**",
        color =0x000000 
        )
        await ctx .send (embed =embed )

    @stickymessage .command (name ='edit')
    @commands .has_permissions (manage_messages =True )
    async def sticky_edit (self ,ctx ,channel :Optional [discord .TextChannel ]=None ):
        """Edit existing sticky message"""
        if channel is None :
            channel =ctx .channel 

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            cursor =await db .execute (
            "SELECT * FROM sticky_messages WHERE guild_id = ? AND channel_id = ?",
            (ctx .guild .id ,channel .id )
            )
            sticky_data =await cursor .fetchone ()

            if not sticky_data :
                embed =discord .Embed (
                title ="No Sticky Found",
                description =f"No sticky message exists in {channel.mention}",
                color =0x000000 
                )
                return await ctx .send (embed =embed )


        view =StickyEditView (ctx ,channel ,sticky_data )

        embed =discord .Embed (
        title ="Edit Sticky Message",
        description =f"Editing sticky message for {channel.mention}\nChoose what to edit:",
        color =0x000000 
        )

        await ctx .send (embed =embed ,view =view )

    @stickymessage .command (name ='config')
    @commands .has_permissions (manage_guild =True )
    async def sticky_config (self ,ctx ):
        """Configure sticky message settings for the server"""
        view =StickyConfigView (ctx )

        embed =discord .Embed (
        title ="Sticky Message Configuration",
        description ="Configure server-wide sticky message settings:",
        color =0x000000 
        )

        await ctx .send (embed =embed ,view =view )


class StickySetupView (discord .ui .View ):
    def __init__ (self ,ctx ,channel ):
        super ().__init__ (timeout =300 )
        self .ctx =ctx 
        self .channel =channel 
        self .message_type =None 

    @discord .ui .button (label ='Plain Text',style =discord .ButtonStyle .primary ,emoji ='📝')
    async def plain_text (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        self .message_type ='plain'
        await interaction .response .send_modal (PlainTextModal (self .ctx ,self .channel ))

    @discord .ui .button (label ='Embed',style =discord .ButtonStyle .secondary ,emoji ='📋')
    async def embed_message (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        self .message_type ='embed'
        await interaction .response .send_modal (EmbedModal (self .ctx ,self .channel ))

    @discord .ui .button (label ='Cancel',style =discord .ButtonStyle .danger )
    async def cancel (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        embed =discord .Embed (
        title ="Setup Cancelled",
        description ="Sticky message setup has been cancelled.",
        color =0x000000 
        )
        await interaction .response .edit_message (embed =embed ,view =None )


class PlainTextModal (discord .ui .Modal ,title ='Plain Text Sticky Message'):
    def __init__ (self ,ctx ,channel ):
        super ().__init__ ()
        self .ctx =ctx 
        self .channel =channel 

    message_content =discord .ui .TextInput (
    label ='Message Content',
    placeholder ='Enter your sticky message here...',
    style =discord .TextStyle .long ,
    required =True ,
    max_length =2000 
    )

    delay_seconds =discord .ui .TextInput (
    label ='Delay (seconds)',
    placeholder ='3',
    default ='3',
    required =False ,
    max_length =3 
    )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            delay =int (self .delay_seconds .value or "3")
            if delay <1 :
                delay =1 
        except ValueError :
            delay =3 

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                INSERT INTO sticky_messages 
                (guild_id, channel_id, message_type, message_content, delay_seconds)
                VALUES (?, ?, ?, ?, ?)
            """,(self .ctx .guild .id ,self .channel .id ,'plain',self .message_content .value ,delay ))
            await db .commit ()

        embed =discord .Embed (
        title ="Sticky Message Created",
        description =f"Successfully created plain text sticky message in {self.channel.mention}",
        color =0x000000 
        )
        embed .add_field (name ="Delay",value =f"{delay} seconds",inline =True )
        embed .add_field (name ="Preview",value =self .message_content .value [:100 ]+"..."if len (self .message_content .value )>100 else self .message_content .value ,inline =False )

        await interaction .response .edit_message (embed =embed ,view =None )


class EmbedModal (discord .ui .Modal ,title ='Embed Sticky Message'):
    def __init__ (self ,ctx ,channel ):
        super ().__init__ ()
        self .ctx =ctx 
        self .channel =channel 

    title =discord .ui .TextInput (
    label ='Embed Title',
    placeholder ='Enter embed title...',
    required =False ,
    max_length =256 
    )

    description =discord .ui .TextInput (
    label ='Embed Description',
    placeholder ='Enter embed description...',
    style =discord .TextStyle .long ,
    required =True ,
    max_length =4000 
    )

    color =discord .ui .TextInput (
    label ='Embed Color (hex)',
    placeholder ='#000000',
    default ='#000000',
    required =False ,
    max_length =7 
    )

    footer =discord .ui .TextInput (
    label ='Footer Text',
    placeholder ='Footer text (optional)',
    required =False ,
    max_length =2048 
    )

    delay_seconds =discord .ui .TextInput (
    label ='Delay (seconds)',
    placeholder ='3',
    default ='3',
    required =False ,
    max_length =3 
    )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            delay =int (self .delay_seconds .value or "3")
            if delay <1 :
                delay =1 
        except ValueError :
            delay =3 


        embed_data ={
        "title":self .title .value ,
        "description":self .description .value ,
        "color":self .color .value ,
        "footer":self .footer .value 
        }

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                INSERT INTO sticky_messages 
                (guild_id, channel_id, message_type, embed_data, delay_seconds)
                VALUES (?, ?, ?, ?, ?)
            """,(self .ctx .guild .id ,self .channel .id ,'embed',json .dumps (embed_data ),delay ))
            await db .commit ()


        try :
            color_int =int (self .color .value .lstrip ('#'),16 )if self .color .value else 0x000000 
        except ValueError :
            color_int =0x000000 

        preview_embed =discord .Embed (
        title =self .title .value or None ,
        description =self .description .value ,
        color =color_int 
        )
        if self .footer .value :
            preview_embed .set_footer (text =self .footer .value )

        success_embed =discord .Embed (
        title ="Sticky Embed Created",
        description =f"Successfully created embed sticky message in {self.channel.mention}",
        color =0x000000 
        )
        success_embed .add_field (name ="Delay",value =f"{delay} seconds",inline =True )

        await interaction .response .edit_message (embed =success_embed ,view =None )
        await interaction .followup .send ("**Preview:**",embed =preview_embed ,ephemeral =True )


class StickyEditView (discord .ui .View ):
    def __init__ (self ,ctx ,channel ,sticky_data ):
        super ().__init__ (timeout =300 )
        self .ctx =ctx 
        self .channel =channel 
        self .sticky_data =sticky_data 

    @discord .ui .button (label ='Edit Content',style =discord .ButtonStyle .primary )
    async def edit_content (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        if self .sticky_data [3 ]=='plain':
            modal =EditPlainTextModal (self .ctx ,self .channel ,self .sticky_data )
        else :
            modal =EditEmbedModal (self .ctx ,self .channel ,self .sticky_data )

        await interaction .response .send_modal (modal )

    @discord .ui .button (label ='Edit Settings',style =discord .ButtonStyle .secondary )
    async def edit_settings (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        await interaction .response .send_modal (EditSettingsModal (self .ctx ,self .channel ,self .sticky_data ))

    @discord .ui .button (label ='Cancel',style =discord .ButtonStyle .danger )
    async def cancel (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        embed =discord .Embed (
        title ="Edit Cancelled",
        description ="Sticky message editing has been cancelled.",
        color =0x000000 
        )
        await interaction .response .edit_message (embed =embed ,view =None )


class EditPlainTextModal (discord .ui .Modal ,title ='Edit Plain Text'):
    def __init__ (self ,ctx ,channel ,sticky_data ):
        super ().__init__ ()
        self .ctx =ctx 
        self .channel =channel 
        self .sticky_data =sticky_data 


        self .message_content =discord .ui .TextInput (
        label ='Message Content',
        style =discord .TextStyle .long ,
        required =True ,
        max_length =2000 ,
        default =sticky_data [4 ]or ""
        )

    async def on_submit (self ,interaction :discord .Interaction ):
        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                UPDATE sticky_messages 
                SET message_content = ?
                WHERE guild_id = ? AND channel_id = ?
            """,(self .message_content .value ,self .ctx .guild .id ,self .channel .id ))
            await db .commit ()

        embed =discord .Embed (
        title ="Content Updated",
        description =f"Successfully updated sticky message content in {self.channel.mention}",
        color =0x000000 
        )
        await interaction .response .edit_message (embed =embed ,view =None )


class EditEmbedModal (discord .ui .Modal ,title ='Edit Embed'):
    def __init__ (self ,ctx ,channel ,sticky_data ):
        super ().__init__ ()
        self .ctx =ctx 
        self .channel =channel 
        self .sticky_data =sticky_data 


        try :
            embed_data =json .loads (sticky_data [5 ])if sticky_data [5 ]else {}
        except json .JSONDecodeError :
            embed_data ={}


        self .title =discord .ui .TextInput (
        label ='Embed Title',
        required =False ,
        max_length =256 ,
        default =embed_data .get ("title","")
        )

        self .description =discord .ui .TextInput (
        label ='Embed Description',
        style =discord .TextStyle .long ,
        required =True ,
        max_length =4000 ,
        default =embed_data .get ("description","")
        )

        self .color =discord .ui .TextInput (
        label ='Embed Color (hex)',
        required =False ,
        max_length =7 ,
        default =embed_data .get ("color","#000000")
        )

        self .footer =discord .ui .TextInput (
        label ='Footer Text',
        required =False ,
        max_length =2048 ,
        default =embed_data .get ("footer","")
        )

    async def on_submit (self ,interaction :discord .Interaction ):
        embed_data ={
        "title":self .title .value ,
        "description":self .description .value ,
        "color":self .color .value ,
        "footer":self .footer .value 
        }

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                UPDATE sticky_messages 
                SET embed_data = ?
                WHERE guild_id = ? AND channel_id = ?
            """,(json .dumps (embed_data ),self .ctx .guild .id ,self .channel .id ))
            await db .commit ()

        embed =discord .Embed (
        title ="Embed Updated",
        description =f"Successfully updated sticky embed in {self.channel.mention}",
        color =0x000000 
        )
        await interaction .response .edit_message (embed =embed ,view =None )


class EditSettingsModal (discord .ui .Modal ,title ='Edit Sticky Settings'):
    def __init__ (self ,ctx ,channel ,sticky_data ):
        super ().__init__ ()
        self .ctx =ctx 
        self .channel =channel 
        self .sticky_data =sticky_data 


        self .delay_seconds =discord .ui .TextInput (
        label ='Delay (seconds)',
        placeholder ='3',
        required =False ,
        max_length =3 ,
        default =str (sticky_data [8 ])
        )

        self .auto_delete =discord .ui .TextInput (
        label ='Auto Delete After (seconds, 0 = disabled)',
        placeholder ='0',
        required =False ,
        max_length =4 ,
        default =str (sticky_data [9 ])
        )

        self .trigger_count =discord .ui .TextInput (
        label ='Trigger Count (messages to wait)',
        placeholder ='1',
        required =False ,
        max_length =2 ,
        default =str (sticky_data [12 ])
        )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            delay =max (1 ,int (self .delay_seconds .value or "3"))
            auto_del =max (0 ,int (self .auto_delete .value or "0"))
            trigger =max (1 ,int (self .trigger_count .value or "1"))
        except ValueError :
            return await interaction .response .send_message ("Please enter valid numbers!",ephemeral =True )

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                UPDATE sticky_messages 
                SET delay_seconds = ?, auto_delete_after = ?, trigger_count = ?
                WHERE guild_id = ? AND channel_id = ?
            """,(delay ,auto_del ,trigger ,self .ctx .guild .id ,self .channel .id ))
            await db .commit ()

        embed =discord .Embed (
        title ="Settings Updated",
        description =f"Successfully updated sticky settings in {self.channel.mention}",
        color =0x000000 
        )
        embed .add_field (name ="Delay",value =f"{delay}s",inline =True )
        embed .add_field (name ="Auto Delete",value =f"{auto_del}s"if auto_del >0 else "Disabled",inline =True )
        embed .add_field (name ="Trigger Count",value =f"{trigger} messages",inline =True )

        await interaction .response .edit_message (embed =embed ,view =None )


class StickyConfigView (discord .ui .View ):
    def __init__ (self ,ctx ):
        super ().__init__ (timeout =300 )
        self .ctx =ctx 

    @discord .ui .button (label ='Server Settings',style =discord .ButtonStyle .primary )
    async def server_settings (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        await interaction .response .send_modal (ServerConfigModal (self .ctx ))

    @discord .ui .button (label ='View Current Settings',style =discord .ButtonStyle .secondary )
    async def view_settings (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if interaction .user !=self .ctx .author :
            return await interaction .response .send_message ("Only the command author can use this!",ephemeral =True )

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            cursor =await db .execute (
            "SELECT * FROM sticky_settings WHERE guild_id = ?",
            (self .ctx .guild .id ,)
            )
            settings =await cursor .fetchone ()

        if not settings :

            async with aiosqlite .connect ("db/stickymessages.db")as db :
                await db .execute (
                "INSERT INTO sticky_settings (guild_id) VALUES (?)",
                (self .ctx .guild .id ,)
                )
                await db .commit ()
            settings =(self .ctx .guild .id ,10 ,3 ,0 )

        embed =discord .Embed (
        title ="Current Server Settings",
        description =f"Sticky message settings for **{self.ctx.guild.name}**:",
        color =0x000000 
        )
        embed .add_field (name ="Max Sticky Per Guild",value =settings [1 ],inline =True )
        embed .add_field (name ="Default Delay",value =f"{settings[2]} seconds",inline =True )
        embed .add_field (name ="Multiple Per Channel",value ="Yes"if settings [3 ]else "No",inline =True )

        await interaction .response .edit_message (embed =embed ,view =self )


class ServerConfigModal (discord .ui .Modal ,title ='Server Configuration'):
    def __init__ (self ,ctx ):
        super ().__init__ ()
        self .ctx =ctx 

    max_sticky =discord .ui .TextInput (
    label ='Max Sticky Messages Per Guild',
    placeholder ='10',
    default ='10',
    required =False ,
    max_length =3 
    )

    default_delay =discord .ui .TextInput (
    label ='Default Delay (seconds)',
    placeholder ='3',
    default ='3',
    required =False ,
    max_length =3 
    )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            max_val =max (1 ,min (50 ,int (self .max_sticky .value or "10")))
            delay_val =max (1 ,int (self .default_delay .value or "3"))
        except ValueError :
            return await interaction .response .send_message ("Please enter valid numbers!",ephemeral =True )

        async with aiosqlite .connect ("db/stickymessages.db")as db :
            await db .execute ("""
                INSERT OR REPLACE INTO sticky_settings 
                (guild_id, max_sticky_per_guild, default_delay)
                VALUES (?, ?, ?)
            """,(self .ctx .guild .id ,max_val ,delay_val ))
            await db .commit ()

        embed =discord .Embed (
        title ="Configuration Updated",
        description ="Server sticky message settings have been updated!",
        color =0x000000 
        )
        embed .add_field (name ="Max Sticky Per Guild",value =max_val ,inline =True )
        embed .add_field (name ="Default Delay",value =f"{delay_val} seconds",inline =True )

        await interaction .response .edit_message (embed =embed ,view =None )


async def setup (bot ):
    await bot .add_cog (StickyMessage (bot ))