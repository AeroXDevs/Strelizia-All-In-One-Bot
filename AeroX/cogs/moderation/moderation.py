import discord 
import asyncio 
import datetime 
import re 
import typing 
import typing as t 
from typing import *
from utils .Tools import *
from core import Cog ,Strelizia ,Context 
from discord .ext .commands import Converter 
from discord .ext import commands ,tasks 
from discord .ui import Button ,View 
from typing import Union ,Optional 
from utils import Paginator ,DescriptionEmbedPaginator ,FieldPagePaginator ,TextPaginator 
from typing import Union ,Optional 
from io import BytesIO 
import requests 
import aiohttp 
import time 
from datetime import datetime ,timezone ,timedelta 
import sqlite3 
from typing import *
from discord .utils import utcnow 



time_regex =re .compile (r"(?:(\d{1,5})(h|s|m|d))+?")
time_dict ={"h":3600 ,"s":1 ,"m":60 ,"d":86400 }


def convert (argument ):
  args =argument .lower ()
  matches =re .findall (time_regex ,args )
  time =0 
  for key ,value in matches :
    try :
      time +=time_dict [value ]*float (key )
    except KeyError :
      raise commands .BadArgument (
      f"{value} is an invalid time key! h|m|s|d are valid arguments")
    except ValueError :
      raise commands .BadArgument (f"{key} is not a number!")
  return round (time )

async def do_removal (ctx ,limit ,predicate ,*,before =None ,after =None ):
    if limit >2000 :
        return await ctx .error (f"Too many messages to search given ({limit}/2000)")

    if before is None :
        before =ctx .message 
    else :
        before =discord .Object (id =before )

    if after is not None :
        after =discord .Object (id =after )

    try :
        deleted =await ctx .channel .purge (limit =limit ,before =before ,after =after ,check =predicate )
    except discord .Forbidden as e :
        return await ctx .error ("I do not have permissions to delete messages.")
    except discord .HTTPException as e :
        return await ctx .error (f"Error: {e} (try a smaller search?)")

    spammers =Counter (m .author .display_name for m in deleted )
    deleted =len (deleted )
    messages =[f'<:icon_tick:1372375089668161597> | {deleted} message{" was" if deleted == 1 else "s were"} removed.']
    if deleted :
        messages .append ("")
        spammers =sorted (spammers .items (),key =lambda t :t [1 ],reverse =True )
        messages .extend (f"**{name}**: {count}"for name ,count in spammers )

    to_send ="\n".join (messages )

    if len (to_send )>2000 :
        await ctx .send (f"<:icon_tick:1372375089668161597> | Successfully removed {deleted} messages.",delete_after =7 )
    else :
        await ctx .send (to_send ,delete_after =7 )




class Moderation (commands .Cog ):

  def __init__ (self ,bot ):
    self .bot =bot 
    self .color =0x000000 
    self .sniped ={}

  def convert (self ,time ):
    pos =["s","m","h","d"]

    time_dict ={"s":1 ,"m":60 ,"h":3600 ,"d":3600 *24 }
    unit =time [-1 ]
    if unit not in pos :
      return -1 
    try :
      val =int (time [:-1 ])
    except :
      return -2 
    return val *time_dict [unit ]



  @commands .command ()
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def enlarge (self ,ctx ,emoji :Union [discord .Emoji ,discord .PartialEmoji ,str ]):
    url =emoji .url 
    await ctx .send (url )




  @commands .hybrid_command (name ="unlockall",
  help ="Unlocks all channels in the Guild.",
  usage ="unlockall")
  @blacklist_check ()
  @ignore_check ()
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  @commands .has_permissions (administrator =True )
  @commands .cooldown (1 ,15 ,commands .BucketType .channel )
  async def unlockall (self ,ctx ):
      if ctx .author ==ctx .guild .owner or ctx .author .top_role .position >ctx .guild .me .top_role .position :
          button =Button (label ="Confirm",
          style =discord .ButtonStyle .green ,
          emoji ="<:icon_tick:1372375089668161597>")
          button1 =Button (label ="Cancel",
          style =discord .ButtonStyle .red ,
          emoji ="<:warning:1372989665115901994>")
          async def button_callback (interaction :discord .Interaction ):
              a =0 
              if interaction .user ==ctx .author :
                  if interaction .guild .me .guild_permissions .manage_roles :
                      embed1 =discord .Embed (
                      color =self .color ,
                      description =f"Unlocking all channels in {ctx.guild.name} .")
                      await interaction .response .edit_message (
                      embed =embed1 ,view =None )
                      for channel in interaction .guild .channels :
                          try :
                              await channel .set_permissions (
                              ctx .guild .default_role ,
                              overwrite =discord .PermissionOverwrite (send_messages =True ,
                              read_messages =True ),
                              reason ="Unlockall Command Executed By: {}".format (ctx .author ))
                              a +=1 
                          except Exception as e :
                              print (e )
                      await interaction .channel .send (
                      content =f"<:icon_tick:1372375089668161597> | Successfully Unlocked {a} Channels")
                      return 
                  else :
                    await interaction .response .edit_message (
                    content =
                    "<:warning:1372989665115901994> | It seems I'm missing the necessary permissions. Please grant me the `manage roles` permissions and try again.",
                    embed =None ,
                    view =None )
              else :
                await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                embed =None ,
                view =None ,
                ephemeral =True )

          async def button1_callback (interaction :discord .Interaction ):
              if interaction .user ==ctx .author :
                  embed2 =discord .Embed (
                  color =self .color ,
                  description =f"Cancelled, I won't proceed with unlocking any channel.")
                  await interaction .response .edit_message (
                  embed =embed2 ,view =None )
              else :
                  await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                  embed =None ,
                  view =None ,
                  ephemeral =True )
          embed =discord .Embed (
          color =self .color ,
          description =f'**Do you really want to unlock all channels in {ctx.guild.name}**')
          view =View ()
          button .callback =button_callback 
          button1 .callback =button1_callback 
          view .add_item (button )
          view .add_item (button1 )
          embed .set_footer (text ="Please click either 'Confirm' or 'Cancel' to proceed. You have 30 seconds to decide!")
          await ctx .reply (embed =embed ,view =view ,mention_author =False ,delete_after =30 )


      else :
          embed5 =discord .Embed (title ="<:warning:1372989665115901994> Access Denied",
          description ="Your role should be above my top role.",
          color =0x000000 )
          embed5 .set_footer (text =f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
          icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
          await ctx .send (embed =embed5 ,mention_author =False )



  @commands .hybrid_command (name ="lockall",
  help ="locks all the channels in Guild.",
  usage ="lockall")
  @blacklist_check ()
  @ignore_check ()
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  @commands .has_permissions (administrator =True )
  @commands .cooldown (1 ,15 ,commands .BucketType .channel )
  async def lockall (self ,ctx ):
      if ctx .author ==ctx .guild .owner or ctx .author .top_role .position >ctx .guild .me .top_role .position :
          button =Button (label ="Confirm",
          style =discord .ButtonStyle .green ,
          emoji ="<:icon_tick:1372375089668161597>")
          button1 =Button (label ="Cancel",
          style =discord .ButtonStyle .red ,
          emoji ="<:CrossIcon:1327829124894429235>")
          async def button_callback (interaction :discord .Interaction ):
              a =0 
              if interaction .user ==ctx .author :
                  if interaction .guild .me .guild_permissions .manage_roles :
                      embed1 =discord .Embed (
                      color =self .color ,
                      description =f"Locking all channels in {ctx.guild.name}...")
                      await interaction .response .edit_message (
                      embed =embed1 ,view =None )
                      for channel in interaction .guild .channels :
                          try :
                              await channel .set_permissions (ctx .guild .default_role ,
                              overwrite =discord .PermissionOverwrite (
                              send_messages =False ,
                              read_messages =True ),
                              reason ="Lockall command executed by: {}".format (ctx .author ))
                              a +=1 
                          except Exception as e :
                              print (e )
                      await interaction .channel .send (
                      content =f"<:icon_tick:1372375089668161597>| Successfully locked {a} Channels")
                      return 
                  else :
                    await interaction .response .edit_message (
                    content =
                    "<:warning:1372989665115901994> | It seems I'm missing the necessary permissions. Please grant me the `manage roles` permissions and try again.",
                    embed =None ,
                    view =None )
              else :
                await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                embed =None ,
                view =None ,
                ephemeral =True )

          async def button1_callback (interaction :discord .Interaction ):
              if interaction .user ==ctx .author :
                  embed2 =discord .Embed (
                  color =self .color ,
                  description =f"Cancelled, I won't proceed with locking any channel.")
                  await interaction .response .edit_message (
                  embed =embed2 ,view =None )
              else :
                  await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                  embed =None ,
                  view =None ,
                  ephemeral =True )
          embed =discord .Embed (
          color =self .color ,
          description =f'**Do you really want to lock all channels in {ctx.guild.name}**')
          view =View ()
          button .callback =button_callback 
          button1 .callback =button1_callback 
          view .add_item (button )
          view .add_item (button1 )
          embed .set_footer (text =f"Please click either 'Confirm' or 'Cancel' to proceed. You have 30 seconds to decide!")
          await ctx .reply (embed =embed ,view =view ,mention_author =False ,delete_after =30 )

      else :
          denied =discord .Embed (title ="<:warning:1372989665115901994> Access Denied",
          description ="Your role should be above my top role.",
          color =0x000000 )
          denied .set_footer (text =f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
          icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
          await ctx .send (embed =denied ,mention_author =False )


  @commands .hybrid_command (name ="give",
  help ="Gives the mentioned user a role.",
  usage ="give <user> <role>",
  aliases =["addrole"])
  @blacklist_check ()
  @ignore_check ()
  @top_check ()
  @commands .cooldown (1 ,10 ,commands .BucketType .user )
  @commands .has_permissions (manage_roles =True )
  @commands .bot_has_permissions (manage_roles =True )
  async def give (self ,ctx ,member :discord .Member ,*,role :discord .Role ):
    if not ctx .guild .me .guild_permissions .manage_roles :
        return await ctx .send ("<:Denied:1294218790082711553> I don't have permission to manage roles!")

    if role >=ctx .guild .me .top_role :
        error =discord .Embed (
        color =self .color ,
        description ="I can't manage roles for a user with a higher or equal role!"
        )

        error .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        return 

    if ctx .author !=ctx .guild .owner and ctx .author .top_role <=member .top_role :
        error =discord .Embed (
        color =self .color ,
        description ="You can't manage roles for a user with a higher or equal role than yours!"
        )
        error .set_author (name ="Access Denied",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        return 

    try :
        if role not in member .roles :
            await member .add_roles (role ,reason =f"Role added by {ctx.author} (ID: {ctx.author.id})")
            success =discord .Embed (
            color =self .color ,
            description =f"Successfully **added** role {role.name} to {member.mention}."
            )
            success .set_author (name ="Role Added",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
            success .set_footer (text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        else :
            await member .remove_roles (role ,reason =f"Role removed by {ctx.author} (ID: {ctx.author.id})")
            success =discord .Embed (
            color =self .color ,
            description =f"Successfully **removed** role {role.name} from {member.mention}."
            )
            success .set_author (name ="Role Removed",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
            success .set_footer (text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =success )
    except discord .Forbidden :
        error =discord .Embed (
        color =self .color ,
        description ="<:warning:1372989665115901994> I don't have permission to manage roles for this user!"
        )
        pass 
    except Exception as e :
        error =discord .Embed (
        color =self .color ,
        )
        pass 



  @commands .hybrid_command (name ="hideall",help ="Hides all the channels .",
  usage ="hideall")
  @blacklist_check ()
  @ignore_check ()
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  @commands .has_permissions (administrator =True )
  @commands .cooldown (1 ,15 ,commands .BucketType .channel )
  async def hideall (self ,ctx ):
      if ctx .author ==ctx .guild .owner or ctx .author .top_role .position >ctx .guild .me .top_role .position :
          button =Button (label ="Confirm",
          style =discord .ButtonStyle .green ,
          emoji ="<:icon_tick:1372375089668161597>")
          button1 =Button (label ="Cancel",
          style =discord .ButtonStyle .red ,
          emoji ="<:CrossIcon:1327829124894429235>")
          async def button_callback (interaction :discord .Interaction ):
              a =0 
              if interaction .user ==ctx .author :
                  if interaction .guild .me .guild_permissions .manage_roles :
                      embed1 =discord .Embed (
                      color =self .color ,
                      description =f"Hiding all channels in {ctx.guild.name} ...")
                      await interaction .response .edit_message (
                      embed =embed1 ,view =None )
                      for channel in interaction .guild .channels :
                          try :
                              await channel .set_permissions (ctx .guild .default_role ,view_channel =False ,
                              reason ="Hideall Executed by: {}".format (ctx .author ))
                              a +=1 
                          except Exception as e :
                              print (e )
                      await interaction .channel .send (
                      content =f"<:icon_tick:1372375089668161597> | Successfully Hidden {a} Channel(s) .")
                      return 
                  else :
                    await interaction .response .edit_message (
                    content =
                    "<:warning:1372989665115901994> | It seems I'm missing the necessary permissions. Please grant me the `manage channels` permissions and try again.",
                    embed =None ,
                    view =None )
              else :
                await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                embed =None ,
                view =None ,
                ephemeral =True )

          async def button1_callback (interaction :discord .Interaction ):
              if interaction .user ==ctx .author :
                  embed2 =discord .Embed (
                  color =self .color ,
                  description =f"Cancelled, I won't proceed with hiding any channel.")
                  await interaction .response .edit_message (
                  embed =embed2 ,view =None )
              else :
                  await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                  embed =None ,
                  view =None ,
                  ephemeral =True )
          embed =discord .Embed (
          color =self .color ,
          description =f'**Do you really want to hide all channels in {ctx.guild.name}**')
          view =View ()
          button .callback =button_callback 
          button1 .callback =button1_callback 
          view .add_item (button )
          view .add_item (button1 )
          embed .set_footer (text =f"Please click either 'Confirm' or 'Cancel' to proceed. You have 30 seconds to decide!")
          await ctx .reply (embed =embed ,view =view ,mention_author =False ,delete_after =30 )

      else :
          denied =discord .Embed (title ="<:warning:1372989665115901994> Access Denied",
          description ="Your role should be above my top role.",
          color =0x000000 )
          denied .set_footer (text =f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
          icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
          await ctx .send (embed =denied ,mention_author =False )

  @commands .hybrid_command (name ="unhideall",help ="Unhides all the channels in the server.",
  usage ="unhideall")
  @blacklist_check ()
  @ignore_check ()
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  @commands .has_permissions (administrator =True )
  @commands .cooldown (1 ,15 ,commands .BucketType .channel )
  async def unhideall (self ,ctx ):
      if ctx .author ==ctx .guild .owner or ctx .author .top_role .position >ctx .guild .me .top_role .position :
          button =Button (label ="Confirm",
          style =discord .ButtonStyle .green ,
          emoji ="<:icon_tick:1372375089668161597>")
          button1 =Button (label ="Cancel",
          style =discord .ButtonStyle .red ,
          emoji ="<:CrossIcon:1327829124894429235>")
          async def button_callback (interaction :discord .Interaction ):
              a =0 
              if interaction .user ==ctx .author :
                  if interaction .guild .me .guild_permissions .manage_roles :
                      embed1 =discord .Embed (
                      color =self .color ,
                      description =f"Unhiding all channels in {ctx.guild.name} .")
                      await interaction .response .edit_message (
                      embed =embed1 ,view =None )
                      for channel in interaction .guild .channels :
                          try :
                              await channel .set_permissions (ctx .guild .default_role ,view_channel =True ,
                              reason ="Unhideall Command Executed By: {}".format (ctx .author ))
                              a +=1 
                          except Exception as e :
                              print (e )
                      await interaction .channel .send (
                      content =f"<:icon_tick:1372375089668161597> | Successfully Unhidden {a} Channel(s) .")
                      return 
                  else :
                    await interaction .response .edit_message (
                    content =
                    "<:warning:1372989665115901994> | It seems I'm missing the necessary permissions. Please grant me the `manage channels` permissions and try again.",
                    embed =None ,
                    view =None )
              else :
                await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                embed =None ,
                view =None ,
                ephemeral =True )

          async def button1_callback (interaction :discord .Interaction ):
              if interaction .user ==ctx .author :
                  embed2 =discord .Embed (
                  color =self .color ,
                  description =f"Cancelled, I won't proceed with unhiding any channel.")
                  await interaction .response .edit_message (
                  embed =embed2 ,view =None )
              else :
                  await interaction .response .send_message ("Oops! It looks like that message isn't from you. You need to run the command yourself to interact with it.",
                  embed =None ,
                  view =None ,
                  ephemeral =True )
          embed =discord .Embed (
          color =self .color ,
          description =f'**Do you really want to unhide all channels in {ctx.guild.name}**')
          view =View ()
          button .callback =button_callback 
          button1 .callback =button1_callback 
          view .add_item (button )
          view .add_item (button1 )
          embed .set_footer (text =f"Please click either 'Confirm' or 'Cancel' to proceed. You have 30 seconds to decide!")
          await ctx .reply (embed =embed ,view =view ,mention_author =False ,delete_after =30 )

      else :
          denied =discord .Embed (title ="<:warning:1372989665115901994> Access Denied",
          description ="Your role should be above my top role.",
          color =0x000000 )
          denied .set_footer (text =f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
          icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
          await ctx .send (embed =denied ,mention_author =False )



  @commands .hybrid_command (
  name ="prefix",
  aliases =["setprefix","prefixset"],
  help ="Allows you to change the prefix of the bot for this server"
  )
  @blacklist_check ()
  @ignore_check ()
  @commands .has_permissions (administrator =True )
  @commands .cooldown (1 ,10 ,commands .BucketType .user )
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  async def _prefix (self ,ctx :commands .Context ,prefix :str ):
      if not prefix :
          await ctx .reply (embed =discord .Embed (description ="Prefix cannot be empty. Please provide a valid prefix.",
          color =self .color 
          ))
          return 

      data =await getConfig (ctx .guild .id )
      if ctx .author ==ctx .guild .owner or ctx .author .top_role .position >ctx .guild .me .top_role .position :
          data ["prefix"]=str (prefix )
          await updateConfig (ctx .guild .id ,data )
          embed1 =discord .Embed (title ="<:icon_tick:1372375089668161597> Success",
          description =f"Changed Prefix For this guild to `{prefix}`\n\nNew Prefix for **{ctx.guild.name}** is : `{prefix}`\nUse `{prefix}help` For More.",
          color =self .color 
          )
          await ctx .reply (embed =embed1 )
      else :
          denied =discord .Embed (title ="<:warning:1372989665115901994> Access Denied",
          description ="Your role should be above my top role.",
          color =0x000000 )
          denied .set_footer (text =f"“{ctx.command.qualified_name}” Command executed by {ctx.author}",
          icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
          await ctx .send (embed =denied ,mention_author =False )



  @commands .hybrid_command (name ="clone",help ="Clones a channel.")
  @blacklist_check ()
  @ignore_check ()
  @commands .has_permissions (manage_channels =True )
  async def clone (self ,ctx :commands .Context ,channel :discord .TextChannel ):

    if not ctx .guild .me .guild_permissions .manage_channels :
        error =discord .Embed (
        color =self .color ,
        description ="I don't have permission to manage channels!"
        )
        error .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        return 


    try :

        await channel .clone ()
        success =discord .Embed (
        color =self .color ,
        description =f"{channel.name} has been successfully cloned"
        )
        success .set_author (name ="Success",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        success .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =success )
    except discord .Forbidden :
        error =discord .Embed (
        color =self .color ,
        description ="I don't have permission to clone channels!"
        )
        error .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        pass 
    except Exception as e :
        error =discord .Embed (
        color =self .color ,
        )
        error .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        pass 


  @commands .hybrid_command (name ="nick",
  aliases =['setnick'],
  help ="To change someone's nickname.",
  usage ="nick [member]")
  @blacklist_check ()
  @ignore_check ()
  @commands .has_permissions (manage_nicknames =True )
  @commands .bot_has_permissions (manage_nicknames =True )
  async def changenickname (self ,ctx :commands .Context ,member :discord .Member ,*,name :str =None ):


    if member ==ctx .guild .owner :
        error =discord .Embed (
        color =self .color ,
        description ="I can't change the nickname of the server owner!"
        )
        error .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.pnghttps://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        return 


    if member .top_role >=ctx .guild .me .top_role :
        error =discord .Embed (
        color =self .color ,
        description ="I can't change the nickname of a user with a higher or equal role than mine!"
        )
        error .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        return 


    if ctx .author !=ctx .guild .owner and ctx .author .top_role <=member .top_role :
        error =discord .Embed (
        color =self .color ,
        description ="You can't change the nickname of a user with a higher or equal role than you!"
        )
        error .set_author (name ="Access Denied",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        return 

    try :
        await member .edit (nick =name )
        if name :
            success =discord .Embed (
            color =self .color ,
            description =f"Successfully changed nickname of {member.mention} to {name}."
            )
            success .set_author (name ="Nickname Updated",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
            success .set_footer (text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        else :
            success =discord .Embed (
            color =self .color ,
            description =f"Successfully cleared nickname of {member.mention}."
            )
            success .set_author (name ="Nickname Cleared",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
            success .set_footer (text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =success )
    except discord .Forbidden :
        error =discord .Embed (
        color =self .color ,
        description ="<:warning:1372989665115901994> | I don't have permission to manage this user's nickname!"
        )
        pass 
    except Exception as e :
        error =discord .Embed (
        color =self .color ,
        )
        pass 


  @commands .hybrid_command (name ="nuke",help ="Nukes a channel",usage ="nuke")
  @blacklist_check ()
  @ignore_check ()
  @top_check ()
  @commands .cooldown (1 ,7 ,commands .BucketType .user )
  @commands .has_permissions (manage_channels =True )
  async def _nuke (self ,ctx :commands .Context ):

    delete_button =Button (label ="Delete",
    style =discord .ButtonStyle .red ,
    emoji ="🗑️")
    remake_button =Button (label ="Remake",
    style =discord .ButtonStyle .green ,
    emoji ="🔄")

    async def delete_callback (interaction :discord .Interaction ):
      if interaction .user ==ctx .author :

        yes_button =Button (label ="Yes",
        style =discord .ButtonStyle .red ,
        emoji ="<:icon_tick:1372375089668161597>")
        no_button =Button (label ="No",
        style =discord .ButtonStyle .grey ,
        emoji ="<:CrossIcon:1327829124894429235>")

        async def yes_delete_callback (confirm_interaction :discord .Interaction ):
          if confirm_interaction .user ==ctx .author :
            if confirm_interaction .guild .me .guild_permissions .manage_channels :
              channel =confirm_interaction .channel 
              await channel .delete ()

            else :
              await confirm_interaction .response .edit_message (
              content ="<:warning:1372989665115901994> | I don't have permission to manage channels.",
              embed =None ,view =None )
          else :
            await confirm_interaction .response .send_message (
            "Only the command author can use this button.",ephemeral =True )

        async def no_delete_callback (confirm_interaction :discord .Interaction ):
          if confirm_interaction .user ==ctx .author :
            await confirm_interaction .response .edit_message (
            content ="Cancelled channel deletion.",embed =None ,view =None )
          else :
            await confirm_interaction .response .send_message (
            "Only the command author can use this button.",ephemeral =True )

        confirm_embed =discord .Embed (
        color =self .color ,
        description ='**Are you sure you want to DELETE this channel permanently?**')
        confirm_embed .set_footer (text ="This action cannot be undone!")

        confirm_view =View ()
        yes_button .callback =yes_delete_callback 
        no_button .callback =no_delete_callback 
        confirm_view .add_item (yes_button )
        confirm_view .add_item (no_button )

        await interaction .response .edit_message (embed =confirm_embed ,view =confirm_view )
      else :
        await interaction .response .send_message (
        "Only the command author can use this button.",ephemeral =True )

    async def remake_callback (interaction :discord .Interaction ):
      if interaction .user ==ctx .author :

        yes_button =Button (label ="Yes",
        style =discord .ButtonStyle .green ,
        emoji ="<:icon_tick:1372375089668161597>")
        no_button =Button (label ="No",
        style =discord .ButtonStyle .grey ,
        emoji ="<:CrossIcon:1327829124894429235>")

        async def yes_remake_callback (confirm_interaction :discord .Interaction ):
          if confirm_interaction .user ==ctx .author :
            if confirm_interaction .guild .me .guild_permissions .manage_channels :
              channel =confirm_interaction .channel 
              newchannel =await channel .clone ()
              await newchannel .edit (position =channel .position )
              await channel .delete ()

              embed =discord .Embed (
              description =f"Channel has been successfully nuked by **`{ctx.author}`**",
              color =self .color )
              embed .set_author (name ="Channel Nuked",
              icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
              embed .set_footer (text =f"Requested by {ctx.author}",
              icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
              await newchannel .send (embed =embed )
            else :
              await confirm_interaction .response .edit_message (
              content ="<:warning:1372989665115901994> | I don't have permission to manage channels.",
              embed =None ,view =None )
          else :
            await confirm_interaction .response .send_message (
            "Only the command author can use this button.",ephemeral =True )

        async def no_remake_callback (confirm_interaction :discord .Interaction ):
          if confirm_interaction .user ==ctx .author :
            await confirm_interaction .response .edit_message (
            content ="Cancelled channel remake.",embed =None ,view =None )
          else :
            await confirm_interaction .response .send_message (
            "Only the command author can use this button.",ephemeral =True )

        confirm_embed =discord .Embed (
        color =self .color ,
        description ='**Are you sure you want to REMAKE this channel?**')
        confirm_embed .set_footer (text ="This will delete and recreate the channel with same settings!")

        confirm_view =View ()
        yes_button .callback =yes_remake_callback 
        no_button .callback =no_remake_callback 
        confirm_view .add_item (yes_button )
        confirm_view .add_item (no_button )

        await interaction .response .edit_message (embed =confirm_embed ,view =confirm_view )
      else :
        await interaction .response .send_message (
        "Only the command author can use this button.",ephemeral =True )


    embed =discord .Embed (
    color =self .color ,
    description ='**What would you like to do with this channel?**')
    embed .set_footer (text ="Choose Delete to permanently remove or Remake to recreate!")

    view =View ()
    delete_button .callback =delete_callback 
    remake_button .callback =remake_callback 
    view .add_item (delete_button )
    view .add_item (remake_button )

    await ctx .reply (embed =embed ,view =view ,mention_author =False ,delete_after =60 )



  @commands .hybrid_command (name ="slowmode",
  help ="Changes the slowmode",
  usage ="slowmode [seconds]",
  aliases =["slow"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,2 ,commands .BucketType .user )
  @commands .has_permissions (manage_messages =True )
  async def _slowmode (self ,ctx :commands .Context ,seconds :int =0 ):
    if seconds >120 :
      embed =discord .Embed (description ="Slowmode can not be over 2 minutes",
      color =self .color )
      embed .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
      embed .set_footer (text =f"Requested by {ctx.author}",
      icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
      return await ctx .send (embed =embed )
    if seconds ==0 :
      await ctx .channel .edit (slowmode_delay =seconds )
      await ctx .send (embed =discord .Embed (
      title ="Slowmode",description ="Slowmode is disabled",color =self .color ))
    else :
      await ctx .channel .edit (slowmode_delay =seconds )
      embed =discord .Embed (description ="Successfully Set slowmode to **`%s`**"%(seconds ),
      color =self .color )
      embed .set_author (name ="Slowmode Activated",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
      embed .set_footer (text =f"Requested by {ctx.author}",
      icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
      await ctx .send (embed =embed )


  @commands .hybrid_command (name ="unslowmode",
  help ="Disables slowmode",
  usage ="unslowmode",
  aliases =["unslow"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,2 ,commands .BucketType .user )
  @commands .has_permissions (manage_messages =True )
  @commands .bot_has_permissions (manage_messages =True )
  async def _unslowmode (self ,ctx :commands .Context ):
    await ctx .channel .edit (slowmode_delay =0 )
    embed =discord .Embed (description ="Successfully Disabled slowmode",color =self .color )
    embed .set_author (name ="Unslowmode",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
    embed .set_footer (text =f"Requested by {ctx.author}",
    icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
    await ctx .send (embed =embed )

  @commands .hybrid_command (name ="calc",
  help ="Calculator command for basic math operations",
  usage ="calc [expression]",
  aliases =["calculate","math"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def _calc (self ,ctx :commands .Context ,*,expression :str ):
    try :

        allowed_chars ="0123456789+-*/.() "
        cleaned_expression =''.join (char for char in expression if char in allowed_chars )

        if not cleaned_expression .strip ():
            embed =discord .Embed (
            description ="<:warning:1372989665115901994> | Invalid expression! Only basic math operations are allowed.",
            color =self .color 
            )
            embed .set_author (name ="Calculator Error",
            icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
            embed .set_footer (text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
            return await ctx .send (embed =embed )


        result =eval (cleaned_expression )


        if isinstance (result ,float ):
            if result .is_integer ():
                result =int (result )
            else :
                result =round (result ,10 )

        embed =discord .Embed (
        description =f"**Expression:** `{expression}`\n**Result:** `{result}`",
        color =self .color 
        )
        embed .set_author (name ="Calculator",
        icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        embed .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =embed )

    except ZeroDivisionError :
        embed =discord .Embed (
        description ="<:warning:1372989665115901994> | Cannot divide by zero!",
        color =self .color 
        )
        embed .set_author (name ="Calculator Error",
        icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        embed .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =embed )
    except (ValueError ,SyntaxError ,TypeError ):
        embed =discord .Embed (
        description ="<:warning:1372989665115901994> | Invalid mathematical expression! Please use basic operations like +, -, *, /, (), etc.",
        color =self .color 
        )
        embed .set_author (name ="Calculator Error",
        icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        embed .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =embed )
    except Exception :
        embed =discord .Embed (
        description ="<:warning:1372989665115901994> | An error occurred while calculating. Please check your expression.",
        color =self .color 
        )
        embed .set_author (name ="Calculator Error",
        icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        embed .set_footer (text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url )
        await ctx .send (embed =embed )



  @commands .command (aliases =["deletesticker","removesticker"],description ="Delete the sticker from the server")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  @commands .has_permissions (manage_emojis =True )
  @commands .bot_has_permissions (manage_emojis =True )
  async def delsticker (self ,ctx :commands .Context ,*,name =None ):
        if ctx .message .reference is None :
            return await ctx .reply ("No replied message found")
        msg =await ctx .channel .fetch_message (ctx .message .reference .message_id )
        if len (msg .stickers )==0 :
            return await ctx .reply ("No sticker found")
        try :
            name =""
            for i in msg .stickers :
                name =i .name 
                await ctx .guild .delete_sticker (i )
            await ctx .reply (f"<:icon_tick:1372375089668161597> Sucessfully deleted sticker named `{name}`")
        except :
            await ctx .reply ("Failed to delete the sticker")


  @commands .command (aliases =["deleteemoji","removeemoji"],description ="Deletes the emoji from the server")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  @commands .has_permissions (manage_emojis =True )
  async def delemoji (self ,ctx ,emoji :str =None ):
    init_message =await ctx .reply ("Processing to delete emojis...",mention_author =False )
    message_content =None 


    if ctx .message .reference is not None :
        referenced_message =await ctx .channel .fetch_message (ctx .message .reference .message_id )
        message_content =str (referenced_message .content )
    else :
        message_content =str (ctx .message .content )


    if message_content :

        emoji_pattern =r"<a?:\w+:(\d+)>"
        found_emojis =re .findall (emoji_pattern ,message_content )
        delete_count =0 

        if len (found_emojis )!=0 :

            if len (found_emojis )>15 :
                await init_message .delete ()
                return await ctx .reply ("Maximum 15 emojis can be deleted at a time.")


            for emoji_id in found_emojis :
                try :
                    emoji_to_delete =await ctx .guild .fetch_emoji (int (emoji_id ))
                    await emoji_to_delete .delete (reason =f"Deleted by {ctx.author}")
                    delete_count +=1 
                except discord .NotFound :
                    continue 
                except discord .Forbidden :
                    continue 
            await init_message .delete ()
            return await ctx .reply (f"<:icon_tick:1372375089668161597> | Successfully deleted {delete_count}/{len(found_emojis)} emoji(s).")


    await init_message .delete ()
    return await ctx .reply ("No valid emoji found to delete.")




  @commands .command (description ="Changes the icon for the role.")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  @commands .has_permissions (administrator =True )
  @commands .bot_has_guild_permissions (manage_roles =True )
  async def roleicon (self ,ctx :commands .Context ,role :discord .Role ,*,icon :Union [discord .Emoji ,discord .PartialEmoji ,str ]=None ):

    if role .position >=ctx .guild .me .top_role .position :
        error_embed =discord .Embed (
        description =f"{role.mention} is higher than my role. Please move my role above it.",
        color =self .color 
        )
        error_embed .set_author (name ="Error",icon_url ="https://i.ibb.co/TxtQNnyH/2400e46b-9674-4142-b2dc-73244e769c3b.png")
        error_embed .set_footer (
        text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
        )
        return await ctx .send (embed =error_embed )


    if ctx .author !=ctx .guild .owner and ctx .author .top_role .position <=role .position :
        error_embed =discord .Embed (
        description =f"{role.mention} has the same or a higher position than your top role!",
        color =self .color 
        )
        error_embed .set_author (name ="Error")
        error_embed .set_footer (
        text =f"Requested by {ctx.author}",
        icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
        )
        return await ctx .send (embed =error_embed )


    if icon is None :
        attachment_found =False 
        attachment_url =None 
        for attachment in ctx .message .attachments :
            attachment_url =attachment .url 
            attachment_found =True 

        if attachment_found :
            try :
                async with aiohttp .request ("GET",attachment_url )as r :
                    image_data =await r .read ()
                await role .edit (display_icon =image_data )
                success_embed =discord .Embed (
                description =f"Successfully changed the icon of {role.mention}.",
                color =self .color 
                )
                success_embed .set_author (name ="Icon Updated")
                success_embed .set_footer (
                text =f"Requested by {ctx.author}",
                icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                )
                return await ctx .send (embed =success_embed )
            except Exception as e :
                print (e )
                return await ctx .reply ("Failed to change the icon of the role.")
        else :
            await role .edit (display_icon =None )
            removal_embed =discord .Embed (
            description =f"Successfully removed the icon from {role.mention}.",
            color =self .color 
            )
            removal_embed .set_author (name ="Icon Removed")
            removal_embed .set_footer (
            text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            return await ctx .reply (embed =removal_embed ,mention_author =False )


    if isinstance (icon ,discord .Emoji )or isinstance (icon ,discord .PartialEmoji ):
        emoji_url =f"https://cdn.discordapp.com/emojis/{icon.id}.png"
        try :
            async with aiohttp .request ("GET",emoji_url )as r :
                image_data =await r .read ()
            await role .edit (display_icon =image_data )
            success_embed =discord .Embed (
            description =f"Successfully changed the icon for {role.mention} to {icon}.",
            color =self .color 
            )
            success_embed .set_author (name ="Icon Updated")
            success_embed .set_footer (
            text =f"Requested by {ctx.author}",
            icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
            )
            return await ctx .reply (embed =success_embed ,mention_author =False )
        except Exception as e :
            print (e )
            return await ctx .reply ("Failed to change the icon of the role.")


    else :
        if not icon .startswith ("https://"):
            return await ctx .reply ("Please provide a valid link.")
        try :
            async with aiohttp .request ("GET",icon )as r :
                image_data =await r .read ()
            await role .edit (display_icon =image_data )
            success_embed =discord .Embed (
            description =f"<:icon_tick:1372375089668161597>| Successfully changed the icon for {role.mention}.",
            color =self .color 
            )
            return await ctx .reply (embed =success_embed ,mention_author =False )
        except Exception as e :
            print (e )
            return 



  @commands .hybrid_command (name ="unbanall",
  help ="Unbans Everyone In The Guild!",
  aliases =['massunban'],
  usage ="Unbanall",
  with_app_command =True )
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,30 ,commands .BucketType .user )
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  @commands .has_permissions (ban_members =True )
  async def unbanall (self ,ctx ):
    button =Button (label ="Confirm",
    style =discord .ButtonStyle .green ,
    emoji ="<:icon_tick:1372375089668161597>")
    button1 =Button (label ="Cancel",
    style =discord .ButtonStyle .red ,
    emoji ="<:CrossIcon:1327829124894429235>")

    async def button_callback (interaction :discord .Interaction ):
      a =0 
      if interaction .user ==ctx .author :
        if interaction .guild .me .guild_permissions .ban_members :
          await interaction .response .edit_message (
          content ="Unbanning All Banned Members...",embed =None ,view =None )
          async for idk in interaction .guild .bans (limit =None ):
            await interaction .guild .unban (
            user =idk .user ,
            reason ="Unbanall Command Executed By: {}".format (ctx .author ))
            a +=1 
          await interaction .channel .send (
          content =f"<:icon_tick:1372375089668161597> Successfully Unbanned {a} Members")
        else :
          await interaction .response .edit_message (
          content =
          "I am missing `ban members` in this Guil.",
          embed =None ,
          view =None )
      else :
        await interaction .response .send_message ("Uh oh! That message doesn't belong to you.\nYou must run this command to interact with it.",
        embed =None ,
        view =None ,
        ephemeral =True )

    async def button1_callback (interaction :discord .Interaction ):
      if interaction .user ==ctx .author :
        await interaction .response .edit_message (
        content ="Cancelled, I will Not unban anyone.",embed =None ,view =None )
      else :
        await interaction .response .send_message ("Uh oh! That message doesn't belong to you.\nYou must run this command to interact with it.",
        embed =None ,
        view =None ,
        ephemeral =True )

    embed =discord .Embed (
    color =self .color ,
    description ='**Are you sure you want to unban all members in this guild?**')

    view =View ()
    button .callback =button_callback 
    button1 .callback =button1_callback 
    view .add_item (button )
    view .add_item (button1 )
    await ctx .reply (embed =embed ,view =view ,mention_author =False )

  @commands .hybrid_command (name ="audit",
  help ="See recents audit log action in the server .")
  @blacklist_check ()
  @ignore_check ()
  @commands .has_permissions (view_audit_log =True )
  @commands .bot_has_permissions (view_audit_log =True )
  @commands .cooldown (1 ,5 ,commands .BucketType .user )
  @commands .max_concurrency (1 ,per =commands .BucketType .default ,wait =False )
  @commands .guild_only ()
  async def auditlog (self ,ctx ,limit :int ):
    if limit >=31 :
      await ctx .reply (
      "Action rejected, you are not allowed to fetch more than `30` entries.",
      mention_author =False )
      return 
    idk =[]
    str =""
    async for entry in ctx .guild .audit_logs (limit =limit ):
      idk .append (f'''User: `{entry.user}`
Action: `{entry.action}`
Target: `{entry.target}`
Reason: `{entry.reason}`\n\n''')
    for n in idk :
      str +=n 
    str =str .replace ("AuditLogAction.","")
    embed =discord .Embed (title =f"Audit Logs Of {ctx.guild.name}",
    description =f">>> {str}",
    color =0x000000 )
    embed .set_footer (text =f"Audit Log Actions For {ctx.guild.name}")
    await ctx .reply (embed =embed ,mention_author =False )

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
