
import discord 
import requests 
import aiohttp 
from datetime import datetime 
import random 
import os 
from discord .ext import commands 
from random import randint 
from utils .Tools import *
from core import Cog ,Strelizia ,Context 
from utils .config import *
from pathlib import Path 
import json 
from PIL import Image ,ImageDraw ,ImageOps 
import io 


def RandomColor ():
  randcolor =discord .Color (random .randint (0x000000 ,0xFFFFFF ))
  return randcolor 

RAPIDAPI_HOST ="truth-dare.p.rapidapi.com"
RAPIDAPI_KEY ="1cd7c71534msh2544b357ec07ad8p18fa0bjsn1358eef1f8e9"

class Fun (commands .Cog ):

  def __init__ (self ,bot ):
    self .bot =bot 
    self .giphy_token ='y3KcqQTdiS0RYcpNJrWn8hFGglKqX4is'
    self .google_api_key ='AIzaSyA022fwm_TOQcYTg1N_ohqqIj_RUFUM9BY'
    self .search_engine_id ='2166875ec165a6c21'


  async def download_avatar (self ,url ):
      async with aiohttp .ClientSession ()as session :
          async with session .get (url )as resp :
              if resp .status !=200 :
                  return None 
              data =await resp .read ()
              return Image .open (io .BytesIO (data )).convert ("RGBA")

  def circle_avatar (self ,avatar ):
      mask =Image .new ("L",avatar .size ,0 )
      draw =ImageDraw .Draw (mask )
      draw .ellipse ((0 ,0 )+avatar .size ,fill =255 )
      avatar =ImageOps .fit (avatar ,mask .size ,centering =(0.5 ,0.5 ))
      avatar .putalpha (mask )
      return avatar 

  async def add_role (self ,*,role :int ,member :discord .Member ):
    if member .guild .me .guild_permissions .manage_roles :
      role =discord .Object (id =int (role ))
      await member .add_roles (role ,reason =f"{NAME} | Role Added ")

  async def remove_role (self ,*,role :int ,member :discord .Member ):
    if member .guild .me .guild_permissions .manage_roles :
      role =discord .Object (id =int (role ))
      await member .remove_roles (role ,reason =f"{NAME} | Role Removed")


  async def fetch_data (self ,endpoint ):
        async with aiohttp .ClientSession ()as session :
            headers ={
            "X-RapidAPI-Host":RAPIDAPI_HOST ,
            "X-RapidAPI-Key":RAPIDAPI_KEY 
            }
            async with session .get (f"https://{RAPIDAPI_HOST}{endpoint}",headers =headers )as response :
                if response .status ==200 :
                    return await response .json ()
                else :
                    return None 


  async def fetch_image (self ,ctx ,endpoint ):
    async with aiohttp .ClientSession ()as session :
        async with session .get (f"https://nekos.life/api/v2/img/{endpoint}")as response :
            if response .status ==200 :
                data =await response .json ()
                return data ["url"]
            else :
                pass 




  async def fetch_action_image (self ,action ):
        url =f"https://api.waifu.pics/sfw/{action}"
        try :
            response =requests .get (url )
            response .raise_for_status ()
            return response .json ().get ('url')
        except requests .exceptions .RequestException :
            return None 

  @commands .command ()
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def mydog (self ,ctx ,user :discord .User ):
      processing =await ctx .reply ("<a:Loading:1328740531907461233> Processing Image...")
      base_image_path ="data/pictures/mydog.jpg"
      base_image =Image .open (base_image_path ).convert ("RGBA")

      author_avatar_url =ctx .author .display_avatar .url 
      user_avatar_url =user .display_avatar .url 

      author_avatar =await self .download_avatar (author_avatar_url )
      user_avatar =await self .download_avatar (user_avatar_url )

      if author_avatar is None or user_avatar is None :
          pass 
          return 

      author_avatar =self .circle_avatar (author_avatar .resize ((230 ,230 )))
      user_avatar =self .circle_avatar (user_avatar .resize ((310 ,310 )))

      base_image .paste (author_avatar ,(370 ,0 ),author_avatar )
      base_image .paste (user_avatar ,(0 ,220 ),user_avatar )

      final_buffer =io .BytesIO ()
      base_image .save (final_buffer ,"PNG")
      final_buffer .seek (0 )

      file =discord .File (fp =final_buffer ,filename ="mydog.png")
      await ctx .reply (file =file )
      await processing .delete ()


  @commands .command (name ="image",help ="Search for an image and display a random one.",aliases =["img"],with_app_command =True )
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def image (self ,ctx ,*,search_query :str ):
        if not ctx .channel .is_nsfw ():
            await ctx .reply ("This command can only be used in NSFW (age-restricted) channels.",ephemeral =True )
            return 
        async with aiohttp .ClientSession ()as session :
            async with session .get (f"https://www.googleapis.com/customsearch/v1?key={self.google_api_key}&cx={self.search_engine_id}&q={search_query}&searchType=image")as response :
                data =await response .json ()
                if "items"in data :
                    image =discord .Embed (title =f"Random Image for '{search_query}'",color =discord .Color .random ())
                    image .set_image (url =random .choice (data ["items"])["link"])
                    await ctx .reply (embed =image )
                else :
                    await ctx .reply ("No images found for that search query.")




  @commands .command (name ="howgay",
  aliases =['gay'],
  help ="check someone gay percentage",
  usage ="Howgay <person>")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def howgay (self ,ctx ,*,person ):
    embed =discord .Embed (title ="About your gayness",color =discord .Color .random ())
    responses =random .randrange (1 ,150 )
    embed .description =f'**{person} is {responses}% Gay** :rainbow:'
    embed .set_footer (text =f'How gay are you? - {ctx.author.name}')
    await ctx .reply (embed =embed )


  @commands .command (name ="lesbian",
  aliases =['lesbo'],
  help ="check someone lesbian percentage",
  usage ="lesbian <person>")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def lesbian (self ,ctx ,*,person ):
    embed =discord .Embed (title =" Lesbian Meter",color =discord .Color .random ())
    responses =random .randrange (1 ,150 )
    embed .description =f'**{person} is {responses}% Lesbian** '
    embed .set_footer (text =f'How lesbian are you? - {ctx.author.name}')
    await ctx .reply (embed =embed )

  @commands .command (name ="horny",
  aliases =['horniness'],
  help ="check someone horniness percentage",
  usage ="Horny <person>")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def horny (self ,ctx ,*,person ):
    embed =discord .Embed (title ="about your horniness",color =discord .Color .random ())
    responses =random .randrange (1 ,150 )
    embed .description =f'**{person} is {responses}% Horny** 😳'
    embed .set_footer (text =f'How horny are you? - {ctx.author.name}')
    await ctx .reply (embed =embed )

  @commands .command (name ="cute",
  aliases =['cuteness'],
  help ="check someone cuteness percentage",
  usage ="Cute <person>")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def cute (self ,ctx ,*,person ):
    embed =discord .Embed (title =" About your cuteness",color =discord .Color .random ())
    responses =random .randrange (1 ,150 )
    embed .description =f'**{person} is {responses}% Cute** 🥰'
    embed .set_footer (text =f'How cute are you? - {ctx.author.name}')
    await ctx .reply (embed =embed )

  @commands .command (name ="intelligence",
  aliases =['iq'],
  help ="check someone intelligence percentage",
  usage ="Intelligence <person>")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def intelligence (self ,ctx ,*,person ):
    embed =discord .Embed (title =" About your intelligence",color =discord .Color .random ())
    responses =random .randrange (1 ,150 )
    embed .description =f'**{person} has an IQ of {responses}%** '
    embed .set_footer (text =f'How intelligent are you? - {ctx.author.name}')
    await ctx .reply (embed =embed )

  @commands .command (name ="gif",help ="Search for a gif and display a random one.",with_app_command =True )
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,5 ,commands .BucketType .user )
  async def gif (self ,ctx ,*,search_query :str ):
      async with aiohttp .ClientSession ()as session :
          async with session .get (f"https://api.giphy.com/v1/gifs/search?api_key={self.giphy_token}&q={search_query}&limit=10")as response :
              data =await response .json ()
              if "data"in data :
                  gif =discord .Embed (title =f"Random GIF for '{search_query}'",color =discord .Color .random ())
                  gif .set_image (url =random .choice (data ["data"])["images"]["original"]["url"])
                  await ctx .reply (embed =gif )
              else :
                  await ctx .reply ("No GIFs found for that search query.")




  @commands .command (name ="iplookup",
  aliases =['ip'],
  help ="Get accurate IP info",
  usage ="iplookup [ip]")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def iplookup (self ,ctx ,*,ip ):
    async with aiohttp .ClientSession ()as session :
      try :
        async with session .get (f"http://ip-api.com/json/{ip}")as response :
          data =await response .json ()

          if data ['status']=='fail':
            embed =discord .Embed (
            description ="Failed to retrieve data. Please check the IP address and try again.",
            color =0xFF0000 )
            await ctx .send (embed =embed )
            return 


          query =data .get ('query','N/A')
          continent =data .get ('continent','N/A')
          continent_code =data .get ('continentCode','N/A')
          country =data .get ('country','N/A')
          country_code =data .get ('countryCode','N/A')
          region_name =data .get ('regionName','N/A')
          region =data .get ('region','N/A')
          city =data .get ('city','N/A')
          district =data .get ('district','N/A')
          zip_code =data .get ('zip','N/A')
          latitude =data .get ('lat','N/A')
          longitude =data .get ('lon','N/A')
          timezone =data .get ('timezone','N/A')
          offset =data .get ('offset','N/A')
          isp =data .get ('isp','N/A')
          organization =data .get ('org','N/A')
          asn =data .get ('as','N/A')
          asname =data .get ('asname','N/A')
          mobile =data .get ('mobile','N/A')
          proxy =data .get ('proxy','N/A')
          hosting =data .get ('hosting','N/A')

          embed =discord .Embed (
          title =f"IP: {query}",
          description =(
          f"\n"
          f"🌏 __**Location Info:**__ \n"
          f"IP: **{query}**\n"
          f"Continent: {continent} ({continent_code})\n"
          f"Country: {country} ({country_code})\n"
          f"Region: **{region_name}** ({region})\n"
          f"City: {city}\n"
          f"District: {district}\n"
          f"Zip: {zip_code}\n"
          f"Latitude: {latitude}\n"
          f"Longitude: {longitude}\n"
          f"Lat/Long: {latitude}, {longitude}\n"
          f"\n"
          f"📡 __**Timezone Info:**__\n"
          f"Timezone: {timezone}\n"
          f"Offset: {offset}\n"
          f"\n"
          f"🛜 __**Network Info:**__ \n"
          f"ISP: **{isp}**\n"
          f"Organization: {organization}\n"
          f"AS: **{asn}**\n"
          f"AS Name: **{asname}**\n"
          f"\n"
          f"<:icon_danger:1372375135604047902> __**Miscellaneous Info:**__ \n"
          f"Mobile: {mobile}\n"
          f"Proxy: {proxy}\n"
          f"Hosting: {hosting}\n"
          f""
          ),
          color =0x000000 
          )

          embed .set_footer (
          text =f'Made by AeroX Development',
          icon_url =self .bot .user .avatar 
          )

          await ctx .reply (embed =embed )

      except Exception as e :
        pass 



  @commands .command ()
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def weather (self ,ctx ,*,city :str ):
      api_key ="b81e2218c328686836ab6d9d31ce97d0"
      base_url ="http://api.openweathermap.org/data/2.5/weather?"
      city_name =city 
      complete_url =f"{base_url}q={city_name}&APPID={api_key}"

      async with aiohttp .ClientSession ()as session :
          async with session .get (complete_url )as response :
              data =await response .json ()
              if data ["cod"]!="404":
                  main =data ['main']
                  temperature =main ['temp']
                  temp_celsius =temperature -273.15 
                  humidity =main ['humidity']
                  pressure =main ['pressure']
                  report =data ['weather']
                  weather_desc =report [0 ]['description']

                  weather_embed =discord .Embed (
                  title =f"☁️ Weather in {city_name}",
                  color =0x000000 
                  )
                  weather_embed .add_field (name ="Description",value =weather_desc .capitalize (),inline =False )
                  weather_embed .add_field (name ="Temperature (Celsius)",value =f"{temp_celsius:.2f} °C",inline =False )
                  weather_embed .add_field (name ="Humidity",value =f"{humidity}%",inline =False )
                  weather_embed .add_field (name ="Pressure",value =f"{pressure} hPa",inline =False )
                  weather_embed .set_footer (
                  text =f"Requested By {ctx.author}",
                  icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
                  )

                  await ctx .reply (embed =weather_embed )
              else :
                  await ctx .reply ("City not found. Please enter a valid city name.")

  @commands .command (name ="fakeban",aliases =['fban'],usage ="fakeban <member>")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def fake_ban (self ,ctx ,user :discord .Member ):
    embed =discord .Embed (
    title ="Successfully Banned!",
    description =f"<:icon_tick:1372375089668161597>| {user.mention} has been successfully banned",
    color =0x000000 
    )
    embed .set_footer (
    text =f"Banned By {ctx.author}",
    icon_url =ctx .author .avatar .url if ctx .author .avatar else ctx .author .default_avatar .url 
    )
    await ctx .reply (embed =embed )


  @commands .command (name ="hug")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def hug (self ,ctx ,user :discord .Member =None ):
      if user is None :
          user =ctx .author 
          description =f"{ctx.author.mention} hugged themselves 🥺"
      else :
          description =f"{ctx.author.mention} hugged {user.mention} 🥰"

      image_url =await self .fetch_image (ctx ,"hug")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )

  @commands .command (name ="kiss")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def kiss (self ,ctx ,user :discord .Member =None ):
      if user is None :
          user =ctx .author 
          description =f"{ctx.author.mention} kissed someone in their dream 💀"
      else :
          description =f"{ctx.author.mention} kissed {user.mention} 😳"

      image_url =await self .fetch_image (ctx ,"kiss")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )

  @commands .command (name ="pat")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def pat (self ,ctx ,user :discord .Member =None ):
      if user is None :
          user =ctx .author 
          description =f"{ctx.author.mention} pats themselves 🥺"
      else :
          description =f"{ctx.author.mention} pats {user.mention} 🫠"

      image_url =await self .fetch_image (ctx ,"pat")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )

  @commands .command (name ="cuddle")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def cuddle (self ,ctx ,user :discord .Member =None ):
      if user is None :
          user =ctx .author 
          description =f"{ctx.author.mention} cuddles themselves 🥺"
      else :
          description =f"{ctx.author.mention} cuddles {user.mention} 🥰"

      image_url =await self .fetch_image (ctx ,"cuddle")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )

  @commands .command (name ="slap")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def slap (self ,ctx ,user :discord .Member =None ):
      if user is None :
          await ctx .reply (f"{ctx.author.mention}, you can't slap the air! Find someone to slap.")
          return 

      description =f"{ctx.author.mention} slaps {user.mention} 😡"
      image_url =await self .fetch_image (ctx ,"slap")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )

  @commands .command (name ="tickle")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def tickle (self ,ctx ,user :discord .Member =None ):
      if user is None :
          user =ctx .author 
          description =f"{ctx.author.mention} tickles themselves 🤪"
      else :
          description =f"{ctx.author.mention} tickles {user.mention} 😆"

      image_url =await self .fetch_image (ctx ,"tickle")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )

  @commands .command (name ="spank")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def spank (self ,ctx ,user :discord .Member =None ):
      if not ctx .channel .is_nsfw ():
            await ctx .reply ("This command can only be used in NSFW (age-restricted) channels.")
            return 
      if user is None :
          user =ctx .author 
          description =f"{ctx.author.mention} spanked themselves 😵‍💫"
      else :
          description =f"{ctx.author.mention} spanked {user.mention} 😹"

      image_url =await self .fetch_image (ctx ,"spank")
      if image_url :
          embed =discord .Embed (description =description ,color =RandomColor ())
          embed .set_image (url =image_url )
          await ctx .send (embed =embed )

  @commands .command (name ="kill")
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def kill (self ,ctx ,user :discord .Member =None ):
      if user is None :
          await ctx .send (f"{ctx.author.mention}, you can't kill the air! Find someone to kill.")
          return 

      description =f"{ctx.author.mention} kills {user.mention} ☠️"
      image_url =await self .fetch_action_image ("kill")
      if image_url :
          embed =discord .Embed (description =description ,color =discord .Color .random ())
          embed .set_image (url =image_url )
          await ctx .reply (embed =embed )



  @commands .command (name ="8ball",aliases =["8b"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  async def eight_ball (self ,ctx ,*,question :str =None ):
      if question is None :
          await ctx .send ("You need to ask a question!")
          return 

      async with aiohttp .ClientSession ()as session :
          async with session .get ("https://nekos.life/api/v2/8ball")as response :
              data =await response .json ()
              if "response"in data :
                  embed =discord .Embed (
                  description =f"🎱 {data['response']}",
                  color =discord .Color .random ()
                  )
                  if "url"in data :
                      embed .set_image (url =data ["url"])
                  await ctx .reply (embed =embed )
              else :
                  await ctx .reply ("Couldn't retrieve a response from the magic 8ball.")



  @commands .command (name ="truth",aliases =["t"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  @commands .max_concurrency (5 ,per =commands .BucketType .default ,wait =False )
  async def truth (self ,ctx ):
      async with aiohttp .ClientSession ()as session :
          async with session .get ("https://api.truthordarebot.xyz/api/truth")as response :
              if response .status ==200 :
                  data =await response .json ()
                  question =data .get ("question")
                  if question :
                      embed =discord .Embed (title ="__**TRUTH**__",description =f"{question}",color =0x000000 )
                      await ctx .reply (embed =embed )
                  else :
                      await ctx .send ("Couldn't retrieve a truth question. Please try again.")
              else :
                  pass 

  @commands .command (name ="dare",aliases =["d"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,3 ,commands .BucketType .user )
  @commands .max_concurrency (5 ,per =commands .BucketType .default ,wait =False )
  async def dare (self ,ctx ):
      async with aiohttp .ClientSession ()as session :
          async with session .get ("https://api.truthordarebot.xyz/api/dare")as response :
              if response .status ==200 :
                  data =await response .json ()
                  question =data .get ("question")
                  if question :
                      embed =discord .Embed (title ="__**DARE**__",description =f"{question}",color =0x000000 )
                      await ctx .reply (embed =embed )
                  else :
                      await ctx .send ("Couldn't retrieve a dare question. Please try again.")
              else :
                  pass 




  @commands .command (name ="translate",aliases =["tl"])
  @blacklist_check ()
  @ignore_check ()
  @commands .cooldown (1 ,5 ,commands .BucketType .user )
  async def translate_command (self ,ctx ,*,message =None ):
    """AI-powered translation command"""


    target_language ="English"
    text_to_translate =None 

    if message is None :

      if ctx .message .reference :
        try :
          replied_msg =await ctx .fetch_message (ctx .message .reference .message_id )
          if replied_msg and replied_msg .content :
            text_to_translate =replied_msg .content 
          else :
            await ctx .reply ("<:icon_cross:1372375094336425986> No content found in the replied message.")
            return 
        except :
          await ctx .reply ("<:icon_cross:1372375094336425986> Could not fetch the replied message.")
          return 
      else :
        await ctx .reply ("<:icon_cross:1372375094336425986> Please provide text to translate or reply to a message.")
        return 
    else :

      message_lower =message .lower ()


      language_patterns ={
      'hindi':['hindi','hi'],
      'spanish':['spanish','es','español'],
      'french':['french','fr','français'],
      'german':['german','de','deutsch'],
      'italian':['italian','it'],
      'portuguese':['portuguese','pt'],
      'russian':['russian','ru'],
      'japanese':['japanese','jp'],
      'chinese':['chinese','cn','mandarin'],
      'korean':['korean','ko'],
      'arabic':['arabic','ar'],
      'dutch':['dutch','nl'],
      'polish':['polish','pl'],
      'turkish':['turkish','tr'],
      'swedish':['swedish','sv'],
      'norwegian':['norwegian','no'],
      'danish':['danish','da'],
      'finnish':['finnish','fi'],
      'greek':['greek','el'],
      'hebrew':['hebrew','he'],
      'thai':['thai','th'],
      'vietnamese':['vietnamese','vi']
      }


      detected_language =None 
      for lang ,patterns in language_patterns .items ():
        for pattern in patterns :
          if f"to {pattern}"in message_lower or f"into {pattern}"in message_lower :
            detected_language =lang 
            target_language =lang .capitalize ()


            if ctx .message .reference :
              try :
                replied_msg =await ctx .fetch_message (ctx .message .reference .message_id )
                if replied_msg and replied_msg .content :
                  text_to_translate =replied_msg .content 
                else :
                  await ctx .reply ("<:icon_cross:1372375094336425986> No content found in the replied message.")
                  return 
              except :
                await ctx .reply ("<:icon_cross:1372375094336425986> Could not fetch the replied message.")
                return 
            else :

              text_to_translate =message .replace (f"to {pattern}","").replace (f"into {pattern}","").replace (f"to {pattern.capitalize()}","").replace (f"into {pattern.capitalize()}","").strip ()
            break 
        if detected_language :
          break 


      if not detected_language :
        text_to_translate =message 

    if not text_to_translate or not text_to_translate .strip ():
      await ctx .reply ("<:icon_cross:1372375094336425986> No text provided for translation.")
      return 

    processing_message =await ctx .send ("<a:Strelizia_loading:1373173756113195081> Translating...")

    try :

      prompt =f"Translate the following text to {target_language}. Only provide the translation without any explanations or additional text:\n\n{text_to_translate}"


      import aiohttp 
      groq_api_key =os .getenv ("GROQ_API_KEY")

      if not groq_api_key :
        await processing_message .delete ()
        await ctx .reply ("<:icon_cross:1372375094336425986> Translation service is not configured.")
        return 

      url ="https://api.groq.com/openai/v1/chat/completions"
      headers ={
      "Authorization":f"Bearer {groq_api_key}",
      "Content-Type":"application/json"
      }

      data ={
      "model":"llama-3.3-70b-versatile",
      "messages":[{"role":"user","content":prompt }],
      "temperature":0.3 
      }

      async with aiohttp .ClientSession ()as session :
        async with session .post (url ,headers =headers ,json =data )as response :
          if response .status ==200 :
            json_response =await response .json ()
            translation =json_response ['choices'][0 ]['message']['content'].strip ()

            embed =discord .Embed (
            title ="<a:star:1251876754516349059> AI Translation",
            color =0x000000 ,
            timestamp =datetime .now ()
            )
            embed .add_field (
            name ="<:headmod:1367348948720816220> Original Text",
            value =text_to_translate [:1024 ]+("..."if len (text_to_translate )>1024 else ""),
            inline =False 
            )
            embed .add_field (
            name =f"<a:GIFD:1275850452323401789> Translated to {target_language}",
            value =translation [:1024 ]+("..."if len (translation )>1024 else ""),
            inline =False 
            )
            embed .set_author (
            name =ctx .author .display_name ,
            icon_url =ctx .author .display_avatar .url 
            )
            embed .set_thumbnail (url =self .bot .user .display_avatar .url )
            embed .set_footer (
            text =f"Powered by AeroX Development • Requested by {ctx.author}",
            icon_url =self .bot .user .display_avatar .url 
            )

            await ctx .reply (embed =embed )
            await processing_message .delete ()
          else :
            error_message =await response .text ()
            await processing_message .delete ()
            pass 

    except Exception as e :
      await processing_message .delete ()
      pass 

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
