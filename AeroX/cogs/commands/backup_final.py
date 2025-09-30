import discord 
from discord .ext import commands 
from discord .ui import View ,Select ,Button 
from datetime import datetime 
import pymongo 
import random 
import string 
import aiohttp 
import asyncio 
import logging 
import json 
import io 

logging .basicConfig (level =logging .DEBUG )
logger =logging .getLogger (__name__ )

MONGO_URL ="mongodb+srv://Strelizia:Strelizia@monarchcluster.akf13iq.mongodb.net/?retryWrites=true&w=majority&appName=MonarchCluster"
try :
    mongo =pymongo .MongoClient (MONGO_URL ,serverSelectionTimeoutMS =5000 ,retryWrites =True ,retryReads =True ,maxPoolSize =10 )
    mongo .server_info ()
    db =mongo ["server_backups"]
    collection =db ["backups"]
    MONGO_CONNECTED =True 
except pymongo .errors .ConnectionFailure as e :
    logger .error (f"MongoDB connection failed: {e}")
    mongo =None 
    db =None 
    collection =None 
    MONGO_CONNECTED =False 
OWNER_IDS =[1124248109472550993 ]
GUILD_ID =1370623292142256188 

def generate_backup_id (length =8 ):
    while True :
        backup_id =''.join (random .choices (string .ascii_letters +string .digits ,k =length ))
        if not MONGO_CONNECTED or not collection .find_one ({"backup_id":backup_id }):
            return backup_id 

class Backup (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .session =aiohttp .ClientSession ()
        pass 

    async def cog_unload (self ):
        await self .session .close ()
        logger .info ("Backup cog unloaded.")

    def is_admin (self ,ctx ):
        return ctx .author .guild_permissions .administrator or ctx .author .id in OWNER_IDS 

    def is_owner (self ,user_id ):
        return user_id in OWNER_IDS 

    async def check_db_connection (self ):
        try :
            await self .bot .loop .run_in_executor (None ,lambda :mongo .server_info ())
            return True 
        except pymongo .errors .ConnectionFailure as e :
            logger .error (f"Database connection lost: {e}")
            return False 

    async def post_status (self ,dest ,msg ,color =0x000000 ):
        embed =discord .Embed (description =msg ,color =color )
        try :
            await dest .send (embed =embed )
        except discord .HTTPException as e :
            logger .warning (f"Failed to send status: {e}")

    async def safe_delete (self ,obj ,status_channel ):
        if isinstance (obj ,discord .Role ):
            bot_member =status_channel .guild .get_member (self .bot .user .id )
            if bot_member and obj ==bot_member .top_role :
                logger .debug (f"Skipping deletion of bot's own role: {obj.name}")
                return 
        try :
            await obj .delete ()
            await asyncio .sleep (0.5 )
        except discord .HTTPException as e :
            await self .post_status (status_channel ,f"<:icon_danger:1372375135604047902> Failed to delete {obj}: {e}",0x000000 )

    async def create_emoji_with_retry (self ,guild ,name ,image ,status ,retries =3 ):
        for attempt in range (retries ):
            try :
                await guild .create_custom_emoji (name =name ,image =image )
                await asyncio .sleep (0.5 )
                return True 
            except discord .HTTPException as e :
                if e .status ==429 and attempt <retries -1 :
                    retry_after =e .retry_after if hasattr (e ,"retry_after")else 5 
                    await self .post_status (status ,f"<:icon_danger:1372375135604047902> Rate limit on emoji {name}, retrying in {retry_after}s...",0x000000 )
                    await asyncio .sleep (retry_after )
                    continue 
                await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to create emoji {name}: {e}",0x000000 )
                return False 

    @commands .hybrid_group (
    name ="backup",
    description ="Manage server backups with various subcommands",
    invoke_without_command =True 
    )
    async def backup (self ,ctx ):
        await ctx .send_help (ctx .command )

    @backup .command (name ="create",description ="Create a new server backup")
    @commands .cooldown (1 ,30 ,commands .BucketType .user )
    async def create (self ,ctx ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        if not await self .check_db_connection ():
            return await ctx .send ("<:icon_cross:1372375094336425986> Database unavailable.")
        try :
            if collection .count_documents ({"creator_id":int (ctx .author .id )})>=2 :
                user_backups =list (collection .find ({"creator_id":int (ctx .author .id )}))
                embed =discord .Embed (
                title ="🚫 Backup Limit Reached",
                color =0x000000 ,
                description ="**You've reached the maximum of 2 backups!**\n*Delete one backup to create a new one.*"
                )
                embed .add_field (
                name ="📦 Your Current Backups",
                value ="\n".join (f"🔹 `{b['backup_id']}` - *{b['guild_name']}*"for b in user_backups ),
                inline =False 
                )
                embed .set_footer (text ="💡 Tip: Use 'backup delete <id>' to remove a backup")
                return await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

        backup_id =generate_backup_id ()
        guild =ctx .guild 

        roles =[{"id":r .id ,"name":r .name ,"permissions":r .permissions .value ,"color":r .color .value ,"hoist":r .hoist ,"mentionable":r .mentionable ,"position":r .position }for r in guild .roles if not r .is_default ()]
        categories =[{"name":c .name ,"position":c .position }for c in guild .categories ]
        channels =[]
        for cat in guild .categories :
            for ch in cat .channels :
                overwrites =[{"id":t .id ,"type":"role"if isinstance (t ,discord .Role )else "member","allow":p .pair ()[0 ].value ,"deny":p .pair ()[1 ].value }for t ,p in ch .overwrites .items ()]
                if isinstance (ch ,discord .TextChannel ):
                    channels .append ({"name":ch .name ,"type":"text","topic":ch .topic ,"slowmode":ch .slowmode_delay ,"nsfw":ch .nsfw ,"category":cat .name ,"overwrites":overwrites })
                elif isinstance (ch ,discord .VoiceChannel ):
                    channels .append ({"name":ch .name ,"type":"voice","bitrate":min (ch .bitrate ,96000 ),"user_limit":ch .user_limit ,"category":cat .name ,"overwrites":overwrites })
        emojis =[{"name":e .name ,"url":str (e .url )}for e in guild .emojis ]

        try :
            collection .insert_one ({
            "backup_id":backup_id ,"guild_id":guild .id ,"guild_name":guild .name ,"creator_id":int (ctx .author .id ),
            "created_at":datetime .utcnow (),"roles":roles ,"categories":categories ,"channels":channels ,"emojis":emojis 
            })
            embed =discord .Embed (
            title ="✅ Backup Created Successfully!",
            color =0x000000 ,
            description =f"**Your server backup is ready!**\n🆔 **Backup ID:** `{backup_id}`"
            )
            embed .add_field (name ="📊 Backup Contents",value =f"🎭 **{len(roles)}** roles\n📁 **{len(categories)}** categories\n📺 **{len(channels)}** channels\n😀 **{len(emojis)}** emojis",inline =True )
            embed .add_field (name ="🏠 Server",value =f"**{guild.name}**\n👑 Created by {ctx.author.mention}",inline =True )
            embed .set_thumbnail (url =guild .icon .url if guild .icon else None )
            embed .set_footer (text =f"💾 Use 'backup load {backup_id}' to restore this backup")
            embed .timestamp =datetime .utcnow ()
            await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="list",description ="List all your server backups")
    async def list (self ,ctx ):
        try :
            backups =list (collection .find ({"$or":[{"creator_id":ctx .author .id },{"creator_id":str (ctx .author .id )}]}))
            if not backups :
                return await ctx .send ("<:icon_cross:1372375094336425986> No backups found.")
            embed =discord .Embed (
            title ="📦 Your Server Backups",
            color =0x5865f2 ,
            description ="*Here are all your saved server backups:*"
            )

            backup_list =[]
            for b in backups :
                created_date =b .get ('created_at',datetime .utcnow ()).strftime ("%m/%d/%Y")
                backup_list .append (f"🔹 **`{b['backup_id']}`**\n   🏠 *{b['guild_name']}*\n   📅 *Created: {created_date}*")

            embed .add_field (
            name ="💾 Available Backups",
            value ="\n\n".join (backup_list )if backup_list else "No backups found",
            inline =False 
            )
            embed .set_footer (text ="💡 Use 'backup info <id>' for detailed information")
            await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="delete",description ="Delete a server backup by ID")
    async def delete (self ,ctx ,backup_id :str ):
        try :
            backup =collection .find_one ({"backup_id":backup_id ,"$or":[{"creator_id":ctx .author .id },{"creator_id":str (ctx .author .id )}]})
            if not (self .is_admin (ctx )or backup ):
                return await ctx .send ("<:icon_cross:1372375094336425986> Must be creator, admin, or owner to delete.")
            logger .debug (f"Deleting backup {backup_id} for user {ctx.author.id}")
            result =collection .delete_one ({"backup_id":backup_id ,"$or":[{"creator_id":ctx .author .id },{"creator_id":str (ctx .author .id )}]})
            if result .deleted_count :
                embed =discord .Embed (
                title ="🗑️ Backup Deleted Successfully",
                color =0x27ae60 ,
                description =f"**Backup ID:** `{backup_id}`\n*The backup has been permanently removed from the system.*"
                )
                embed .set_footer (text ="💡 You now have an available backup slot")
                await ctx .send (embed =embed )
            else :
                embed =discord .Embed (
                title ="❌ Deletion Failed",
                color =0xe74c3c ,
                description =f"**Backup ID:** `{backup_id}`\n*Backup not found or you don't have permission to delete it.*"
                )
                await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="info",description ="View details of a server backup by ID")
    async def info (self ,ctx ,backup_id :str ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        try :
            backup =collection .find_one ({"backup_id":backup_id })
            if not backup :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup not found.")
            embed =discord .Embed (
            title =f"📋 Backup Information",
            color =0x45b7d1 ,
            description =f"**Backup ID:** `{backup_id}`"
            )


            embed .add_field (
            name ="🏠 Server Details",
            value =f"**Name:** {backup['guild_name']}\n**Creator:** <@{backup['creator_id']}>\n**Created:** {backup['created_at'].strftime('%B %d, %Y at %H:%M UTC')}",
            inline =False 
            )


            embed .add_field (name ="🎭 Roles",value =f"**{len(backup['roles'])}** roles",inline =True )
            embed .add_field (name ="📁 Categories",value =f"**{len(backup['categories'])}** categories",inline =True )
            embed .add_field (name ="📺 Channels",value =f"**{len(backup['channels'])}** channels",inline =True )
            embed .add_field (name ="😀 Emojis",value =f"**{len(backup['emojis'])}** emojis",inline =True )
            embed .add_field (name ="💾 Total Size",value ="Complete backup",inline =True )
            embed .add_field (name ="🔒 Status",value ="✅ Ready to load",inline =True )

            embed .set_footer (text ="💡 Use 'backup load' to restore this backup to your server")
            embed .timestamp =backup ["created_at"]
            await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="transfer",description ="Transfer a server backup to another user")
    async def transfer (self ,ctx ,backup_id :str ,user :discord .User ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        try :
            backup =collection .find_one ({"backup_id":backup_id ,"$or":[{"creator_id":ctx .author .id },{"creator_id":str (ctx .author .id )}]})
            if not backup :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup not found or not owned.")
            result =collection .update_one ({"backup_id":backup_id },{"$set":{"creator_id":int (user .id )}})
            if result .modified_count :
                embed =discord .Embed (
                title ="🔄 Backup Transferred Successfully",
                color =0x27ae60 ,
                description =f"**Backup ID:** `{backup_id}`\n*Ownership has been transferred to {user.mention}*"
                )
                embed .add_field (name ="Transfer Details",value =f"**From:** {ctx.author.mention}\n**To:** {user.mention}\n**Status:** ✅ Complete",inline =False )
                embed .set_footer (text ="The new owner can now manage this backup")
                await ctx .send (embed =embed )
            else :
                embed =discord .Embed (
                title ="❌ Transfer Failed",
                color =0xe74c3c ,
                description =f"**Backup ID:** `{backup_id}`\n*The transfer could not be completed.*"
                )
                await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="preview",description ="Preview the contents of a server backup")
    async def preview (self ,ctx ,backup_id :str ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        try :
            backup =collection .find_one ({"backup_id":backup_id })
            if not backup :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup not found.")
            embed =discord .Embed (
            title =f"👀 Backup Preview",
            color =0xf39c12 ,
            description =f"**Backup ID:** `{backup_id}`\n**Server:** {backup['guild_name']}\n**Creator:** <@{backup['creator_id']}>\n**Created:** {backup['created_at'].strftime('%B %d, %Y')}"
            )
            def truncate_list (items ,key ,max_chars =1000 ):
                result =[]
                total_chars =0 
                for item in items :
                    line =f"- {item[key]} (Position: {item['position']})"if key =="name"and "position"in item else f"- {item[key]}"
                    if total_chars +len (line )+1 >max_chars :
                        break 
                    result .append (line )
                    total_chars +=len (line )+1 
                if len (items )>len (result ):
                    result .append (f"...and {len(items) - len(result)} more")
                return "\n".join (result )or "None"
            embed .add_field (name ="Roles",value =truncate_list (backup ["roles"],"name"),inline =False )
            embed .add_field (name ="Categories",value =truncate_list (backup ["categories"],"name"),inline =False )
            embed .add_field (name ="Channels",value =truncate_list (backup ["channels"],"name"),inline =False )
            embed .add_field (name ="Emojis",value =truncate_list (backup ["emojis"],"name"),inline =False )
            await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="export",description ="Export a server backup as a JSON file")
    async def export (self ,ctx ,backup_id :str ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        try :
            backup =collection .find_one ({"backup_id":backup_id ,"$or":[{"creator_id":ctx .author .id },{"creator_id":str (ctx .author .id )}]})
            if not backup :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup not found or not owned.")
            backup .pop ("_id",None )
            backup_data =json .dumps (backup ,indent =2 ,default =str ).encode ()
            if len (backup_data )>8 *1024 *1024 :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup too large to export.")
            file =discord .File (io .BytesIO (backup_data ),filename =f"backup_{backup_id}.json")
            embed =discord .Embed (
            title ="📤 Backup Exported Successfully",
            color =0x3498db ,
            description =f"**Backup ID:** `{backup_id}`\n*Your backup has been exported as a JSON file.*"
            )
            embed .add_field (name ="📁 File Details",value =f"**Filename:** `backup_{backup_id}.json`\n**Format:** JSON\n**Size:** {len(backup_data):,} bytes",inline =False )
            embed .set_footer (text ="💾 You can import this file on any server with the backup import command")
            await ctx .send (embed =embed ,file =file )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="import",description ="Import a server backup from a JSON file")
    @commands .cooldown (1 ,30 ,commands .BucketType .user )
    async def import_backup (self ,ctx ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        if not ctx .message .attachments :
            return await ctx .send ("<:icon_cross:1372375094336425986> Attach a JSON file.")
        attachment =ctx .message .attachments [0 ]
        if not attachment .filename .endswith (".json"):
            return await ctx .send ("<:icon_cross:1372375094336425986> Must be a JSON file.")
        try :
            backup_data =json .loads (await attachment .read ())
            required_fields =["guild_id","guild_name","roles","categories","channels","emojis"]
            for field in required_fields :
                if field not in backup_data or not isinstance (backup_data [field ],(list ,int ,str )):
                    return await ctx .send (f"<:icon_cross:1372375094336425986> Invalid backup: '{field}' missing or incorrect.")
            for role in backup_data ["roles"]:
                if not isinstance (role .get ("position",-1 ),int )or role ["position"]<1 :
                    role ["position"]=1 
            for channel in backup_data ["channels"]:
                if channel ["type"]=="voice":
                    channel ["bitrate"]=min (channel .get ("bitrate",64000 ),96000 )
            backup_data ["backup_id"]=generate_backup_id ()
            backup_data ["creator_id"]=int (ctx .author .id )
            backup_data ["created_at"]=datetime .utcnow ()
            if collection .count_documents ({"creator_id":int (ctx .author .id )})>=2 :
                return await ctx .send ("<:icon_cross:1372375094336425986> You have 2 backups. Delete one first.")
            collection .insert_one (backup_data )
            embed =discord .Embed (
            title ="📥 Backup Imported Successfully",
            color =0x27ae60 ,
            description =f"**New Backup ID:** `{backup_data['backup_id']}`\n*Your backup file has been imported and is ready to use!*"
            )
            embed .add_field (name ="📋 Import Details",value =f"**Server:** {backup_data['guild_name']}\n**Roles:** {len(backup_data['roles'])}\n**Channels:** {len(backup_data['channels'])}\n**Emojis:** {len(backup_data['emojis'])}",inline =False )
            embed .set_footer (text ="🚀 Use 'backup load' to restore this backup to your server")
            await ctx .send (embed =embed )
        except json .JSONDecodeError :
            await ctx .send ("<:icon_cross:1372375094336425986> Invalid JSON file.")
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="verify",description ="Verify the integrity of a server backup")
    async def verify (self ,ctx ,backup_id :str ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions required.")
        try :
            backup =collection .find_one ({"backup_id":backup_id })
            if not backup :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup not found.")
            issues =[]
            if not backup .get ("roles"):
                issues .append ("No roles found.")
            if not backup .get ("channels"):
                issues .append ("No channels found.")
            if not backup .get ("categories"):
                issues .append ("No categories found.")
            if not backup .get ("emojis"):
                issues .append ("No emojis found.")
            for role in backup ["roles"]:
                if not isinstance (role .get ("position"),int )or role ["position"]<1 :
                    issues .append (f"Invalid position for role {role['name']}.")
            for channel in backup ["channels"]:
                if channel ["type"]=="voice"and channel .get ("bitrate",64000 )>96000 :
                    issues .append (f"Invalid bitrate for channel {channel['name']}.")
            if issues :
                embed =discord .Embed (
                title ="⚠️ Backup Verification Failed",
                color =0xe74c3c ,
                description =f"**Backup ID:** `{backup_id}`\n*Found {len(issues)} issue(s) that need attention:*"
                )
                embed .add_field (name ="🚨 Issues Found",value ="\n".join (f"• {issue}"for issue in issues ),inline =False )
                embed .set_footer (text ="🔧 These issues may cause problems during restoration")
                await ctx .send (embed =embed )
            else :
                embed =discord .Embed (
                title ="✅ Backup Verification Passed",
                color =0x27ae60 ,
                description =f"**Backup ID:** `{backup_id}`\n*This backup is valid and ready for restoration!*"
                )
                embed .add_field (name ="🔍 Verification Results",value ="• All roles have valid positions\n• All channels are properly configured\n• All data integrity checks passed",inline =False )
                embed .set_footer (text ="✨ This backup can be safely loaded")
                await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="stats",description ="View statistics about server backups")
    async def stats (self ,ctx ):
        try :
            total_backups =collection .count_documents ({})
            user_backups =collection .count_documents ({"$or":[{"creator_id":ctx .author .id },{"creator_id":str (ctx .author .id )}]})
            latest_backup =collection .find_one (sort =[("created_at",-1 )])
            embed =discord .Embed (
            title ="📊 Backup Statistics",
            color =0x9b59b6 ,
            description ="*System-wide backup statistics and information*"
            )

            embed .add_field (name ="🌐 Global Stats",value =f"**Total Backups:** {total_backups:,}\n**Latest Backup:** `{latest_backup['backup_id'] if latest_backup else 'None'}`",inline =True )
            embed .add_field (name ="👤 Your Stats",value =f"**Your Backups:** {user_backups}/2\n**Remaining Slots:** {2-user_backups}",inline =True )
            embed .add_field (name ="💡 System Info",value ="**Max per user:** 2\n**Storage:** Unlimited",inline =True )

            if latest_backup :
                embed .set_footer (text =f"Most recent backup created: {latest_backup['created_at'].strftime('%B %d, %Y')}")

            await ctx .send (embed =embed )
        except pymongo .errors .PyMongoError :
            pass 

    @commands .command (name ="backupdatabase",description ="Reset the entire backup database (bot owner only)")
    @commands .guild_only ()
    async def backupdatabase (self ,ctx ):
        if not self .is_owner (ctx .author .id ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Bot owner only.")
        if ctx .guild .id !=GUILD_ID :
            return await ctx .send (f"<:icon_cross:1372375094336425986> Only usable in guild ID: {GUILD_ID}.")
        if not await self .check_db_connection ():
            return await ctx .send ("<:icon_cross:1372375094336425986> Database unavailable.")
        try :
            logger .debug (f"Bot owner {ctx.author.id} resetting database")
            result =collection .delete_many ({})
            await ctx .send (f"<:icon_tick:1372375089668161597> {result.deleted_count} backups deleted.")
        except pymongo .errors .PyMongoError :
            pass 

    @backup .command (name ="load",description ="Restore a server backup by ID")
    @commands .cooldown (1 ,30 ,commands .BucketType .user )
    async def load (self ,ctx ,backup_id :str ):
        if not self .is_admin (ctx ):
            return await ctx .send ("<:icon_cross:1372375094336425986> Administrator permissions needed.")
        try :
            backup =collection .find_one ({"backup_id":backup_id })
            if not backup :
                return await ctx .send ("<:icon_cross:1372375094336425986> Backup not found.")
        except pymongo .errors .PyMongoError :
            pass 

        class ConfirmView (View ):
            def __init__ (self ):
                super ().__init__ (timeout =180 )
                self .selection =None 
                self .timed_out =False 
                select =Select (
                placeholder ="Select what to delete before loading backup",
                min_values =1 ,
                max_values =5 ,
                options =[
                discord .SelectOption (label ="Roles",value ="roles",emoji ="🧷"),
                discord .SelectOption (label ="Channels",value ="channels",emoji ="📺"),
                discord .SelectOption (label ="Categories",value ="categories",emoji ="🗂️"),
                discord .SelectOption (label ="Emojis",value ="emojis",emoji ="🙂"),
                discord .SelectOption (label ="All",value ="all",emoji ="🗃️"),
                ]
                )
                select .callback =self .select_callback 
                self .add_item (select )
                confirm_button =Button (label ="Confirm",style =discord .ButtonStyle .green )
                confirm_button .callback =self .confirm_callback 
                self .add_item (confirm_button )
                cancel_button =Button (label ="Cancel",style =discord .ButtonStyle .red )
                cancel_button .callback =self .cancel_callback 
                self .add_item (cancel_button )

            async def select_callback (self ,interaction :discord .Interaction ):
                if interaction .user !=ctx .author :
                    await interaction .response .send_message ("<:icon_cross:1372375094336425986> Only the command author can choose.",ephemeral =True )
                    return 
                await interaction .response .defer (ephemeral =True )
                self .selection =interaction .data ["values"]
                await interaction .followup .send (f"<:icon_tick:1372375089668161597> Selected: {', '.join(self.selection)}. Click Confirm.",ephemeral =True )

            async def confirm_callback (self ,interaction :discord .Interaction ):
                if interaction .user !=ctx .author :
                    await interaction .response .send_message ("<:icon_cross:1372375094336425986> Only the command author can confirm.",ephemeral =True )
                    return 
                await interaction .response .defer (ephemeral =True )
                self .stop ()

            async def cancel_callback (self ,interaction :discord .Interaction ):
                if interaction .user !=ctx .author :
                    await interaction .response .send_message ("<:icon_cross:1372375094336425986> Only the command author can cancel.",ephemeral =True )
                    return 
                await interaction .response .send_message ("<:icon_cross:1372375094336425986> Backup loading cancelled.",ephemeral =True )
                self .selection =None 
                self .stop ()

            async def on_timeout (self ):
                self .timed_out =True 
                for item in self .children :
                    item .disabled =True 

        view =ConfirmView ()
        try :
            await ctx .send ("Select parts to delete before loading backup:",view =view )
        except discord .HTTPException as e :
            logger .error (f"Failed to send view: {e}")
            return 

        await view .wait ()
        if view .selection is None :
            return await ctx .send ("<:icon_cross:1372375094336425986> Backup loading timed out."if view .timed_out else "<:icon_cross:1372375094336425986> Backup loading cancelled.")

        if not ctx .guild .me .guild_permissions .manage_channels :
            return await ctx .send ("<:icon_cross:1372375094336425986> Bot lacks manage channels permission.")

        status =discord .utils .get (ctx .guild .channels ,name ="backup-status")
        if not status :
            try :
                status =await ctx .guild .create_text_channel ("backup-status")
            except discord .HTTPException as e :
                logger .error (f"Failed to create status channel: {e}")
                return 

        await self .post_status (status ,"🧹 Deleting selected parts...")
        try :
            if "all"in view .selection or "channels"in view .selection :
                for ch in ctx .guild .channels :
                    if ch .name !="backup-status":
                        await self .safe_delete (ch ,status )
            if "all"in view .selection or "roles"in view .selection :
                for r in ctx .guild .roles :
                    if not r .is_default ():
                        await self .safe_delete (r ,status )
            if "all"in view .selection or "emojis"in view .selection :
                for e in ctx .guild .emojis :
                    await self .safe_delete (e ,status )
            if "all"in view .selection or "categories"in view .selection :
                for cat in ctx .guild .categories :
                    await self .safe_delete (cat ,status )
        except Exception as e :
            logger .error (f"Deletion error: {e}")
            await self .post_status (status ,f"<:icon_danger:1372375135604047902> Error deleting parts: {e}",0x000000 )
            return 

        await self .post_status (status ,"🎭 Restoring roles...")
        old_to_new_role ={}
        bot_member =ctx .guild .get_member (self .bot .user .id )
        if not bot_member :
            await self .post_status (status ,"<:icon_danger:1372375135604047902> Bot member not found.",0x000000 )
            return 

        bot_top_pos =bot_member .top_role .position 
        if bot_top_pos <len (backup ["roles"]):
            await self .post_status (status ,"ℹ️ Adjusting role positions below bot's top role.",0x000000 )

        for r in sorted (backup ["roles"],key =lambda x :x ["position"],reverse =True ):
            if not isinstance (r ["position"],int )or r ["position"]<1 :
                await self .post_status (status ,f"<:icon_danger:1372375135604047902> Invalid position for role {r['name']}. Setting to 1.",0x000000 )
                r ["position"]=1 
            try :
                logger .debug (f"Creating role: {r['name']} (Position: {r['position']})")
                new_role =await ctx .guild .create_role (name =r ["name"],colour =discord .Colour (r ["color"]),hoist =r ["hoist"],mentionable =r ["mentionable"])
                old_to_new_role [r ["id"]]=new_role 
                await asyncio .sleep (0.5 )
            except discord .HTTPException as e :
                await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to create role {r['name']}: {e}",0x000000 )

        try :
            role_positions =[]
            max_available_pos =bot_top_pos -1 
            sorted_roles =sorted (backup ["roles"],key =lambda x :x ["position"],reverse =True )
            for idx ,r_data in enumerate (sorted_roles ):
                new_role =old_to_new_role .get (r_data ["id"])
                if new_role :
                    orig_pos =max (r_data ["position"],1 )
                    new_pos =orig_pos if orig_pos <=max_available_pos else max_available_pos -idx 
                    if new_pos <1 :
                        new_pos =1 
                    role_positions .append ((new_role ,new_pos ,orig_pos ))

            for role ,pos ,orig_pos in sorted (role_positions ,key =lambda x :x [1 ],reverse =True ):
                try :
                    await role .edit (position =pos )
                    logger .debug (f"Set role {role.name} to position {pos} (original: {orig_pos})")
                    await asyncio .sleep (2 )
                    if role .position !=pos :
                        logger .warning (f"Role {role.name} position mismatch: set {pos}, got {role.position}")
                        await self .post_status (status ,f"<:icon_danger:1372375135604047902> Role {role.name} at {role.position}, expected {pos}",0x000000 )
                except discord .HTTPException as e :
                    logger .error (f"Failed to position role {role.name}: {e}")
                    await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to position role {role.name}: {e}",0x000000 )
        except Exception as e :
            logger .error (f"Role positioning error: {e}")
            await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to set role positions: {e}",0x000000 )

        await self .post_status (status ,"🗂️ Restoring categories...")
        category_map ={}
        for cat_data in sorted (backup ["categories"],key =lambda x :x ["position"]):
            try :
                category =await ctx .guild .create_category (cat_data ["name"])
                category_map [cat_data ["name"]]=category 
                await asyncio .sleep (0.5 )
            except discord .HTTPException as e :
                await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to create category {cat_data['name']}: {e}",0x000000 )

        await self .post_status (status ,"📺 Restoring channels...")
        for ch_data in backup ["channels"]:
            try :
                category =category_map .get (ch_data ["category"])
                overwrites ={}
                for perm in ch_data ["overwrites"]:
                    target_id =perm ["id"]
                    target =old_to_new_role .get (target_id )if perm ["type"]=="role"else ctx .guild .get_member (target_id )
                    if target :
                        overwrites [target ]=discord .PermissionOverwrite .from_pair (discord .Permissions (perm ["allow"]),discord .Permissions (perm ["deny"]))
                channel_name =ch_data ["name"][:100 ]
                if ch_data ["type"]=="text":
                    await ctx .guild .create_text_channel (name =channel_name ,topic =ch_data .get ("topic"),slowmode_delay =ch_data .get ("slowmode"),nsfw =ch_data .get ("nsfw",False ),category =category ,overwrites =overwrites )
                elif ch_data ["type"]=="voice":
                    bitrate =min (ch_data .get ("bitrate",64000 ),96000 )
                    await ctx .guild .create_voice_channel (name =channel_name ,bitrate =bitrate ,user_limit =ch_data .get ("user_limit"),category =category ,overwrites =overwrites )
                await asyncio .sleep (0.5 )
            except discord .HTTPException as e :
                await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to create channel {ch_data['name']}: {e}",0x000000 )

        await self .post_status (status ,"🙂 Restoring emojis...")
        for e_data in backup ["emojis"]:
            try :
                async with self .session .get (e_data ["url"])as resp :
                    if resp .status ==200 :
                        image =await resp .read ()
                        await self .create_emoji_with_retry (ctx .guild ,e_data ["name"],image ,status )
                    else :
                        await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to fetch emoji {e_data['name']} image: HTTP {resp.status}",0x000000 )
            except aiohttp .ClientError as e :
                await self .post_status (status ,f"<:icon_danger:1372375135604047902> Failed to fetch emoji {e_data['name']} image: {e}",0x000000 )

        await self .post_status (status ,"<:icon_tick:1372375089668161597> Backup restoration complete!",0x000000 )

async def setup (bot ):
    await bot .add_cog (Backup (bot ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
