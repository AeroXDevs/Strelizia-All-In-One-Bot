import discord 
from discord .ext import commands 
import aiohttp 
import random 
from core import Context 
from core .Cog import Cog 
from core .Strelizia import Strelizia 
from utils .Tools import *

class Roleplay (Cog ,name ="roleplay"):
    def __init__ (self ,client :Strelizia ):
        self .client =client 

    def help_custom (self ):
        emoji ='🎭'
        label ="Roleplay"
        description ="Interactive roleplay commands"
        return emoji ,label ,description 

    async def get_roleplay_gif (self ,action ):
        """Fetch animated GIF from nekos.best and Tenor APIs with fallback"""

        try :
            async with aiohttp .ClientSession ()as session :
                url =f"https://nekos.best/api/v2/{action}"
                async with session .get (url )as response :
                    if response .status ==200 :
                        data =await response .json ()
                        if data .get ("results")and len (data ["results"])>0 :
                            return data ["results"][0 ].get ("url")
        except Exception as e :
            print (f"Nekos.best API error: {e}")


        try :
            async with aiohttp .ClientSession ()as session :
                url =f"https://tenor.googleapis.com/v2/search"
                params ={
                "q":f"anime {action}",
                "key":"AIzaSyAyimkuYQYF_FXVALexPuGQctUWRURdCYQ",
                "limit":25 ,
                "contentfilter":"medium",
                "media_filter":"gif"
                }

                async with session .get (url ,params =params )as response :
                    if response .status ==200 :
                        data =await response .json ()
                        if data .get ("results"):

                            all_gifs =[result .get ("media_formats",{}).get ("gif",{}).get ("url")
                            for result in data ["results"]
                            if result .get ("media_formats",{}).get ("gif",{}).get ("url")]

                            if all_gifs :
                                return random .choice (all_gifs )

        except Exception as e :
            print (f"Tenor API error: {e}")


        action_fallbacks ={
        "hug":[
        "https://media.tenor.com/VBXfHaXXK8UAAAAC/anime-hug.gif",
        "https://media.tenor.com/KAplWFVgZcMAAAAC/anime-hug-cute.gif",
        "https://media.tenor.com/x6xj9CyH_TYAAAAC/wholesome-hug.gif"
        ],
        "kiss":[
        "https://media.tenor.com/X2n2sz4wNYMAAAAC/anime-kiss.gif",
        "https://media.tenor.com/pK3lBkhH4EIAAAAC/anime-kiss-cute.gif"
        ],
        "cuddle":[
        "https://media.tenor.com/7vy_3CQrN8IAAAAC/anime-cuddle.gif",
        "https://media.tenor.com/YCEuJQT6_qsAAAAC/cuddle-anime.gif"
        ],
        "pat":[
        "https://media.tenor.com/efzrKPH-xeYAAAAC/anime-pat.gif",
        "https://media.tenor.com/d2bhHySVT9QAAAAC/anime-pat-head.gif"
        ],
        "slap":[
        "https://media.tenor.com/R_rjwlEH7zMAAAAC/anime-slap.gif",
        "https://media.tenor.com/HJZp5MrYHmMAAAAC/anime-slap-funny.gif"
        ],
        "tickle":[
        "https://media.tenor.com/rggT2ROoFpYAAAAC/anime-tickle.gif"
        ],
        "poke":[
        "https://media.tenor.com/1MoLS3INZuEAAAAC/anime-poke.gif"
        ],
        "wave":[
        "https://media.tenor.com/E3b2EAFV_pIAAAAC/anime-wave.gif"
        ],
        "dance":[
        "https://media.tenor.com/EAK-sPw8aRMAAAAC/anime-dance.gif"
        ],
        "cry":[
        "https://media.tenor.com/WZ8P6_LQQ2AAAAAC/anime-cry.gif"
        ],
        "laugh":[
        "https://media.tenor.com/84fgtyXgqTUAAAAC/anime-laugh.gif"
        ],
        "smile":[
        "https://media.tenor.com/Wn9X2FKr3PEAAAAC/anime-smile.gif"
        ],
        "blush":[
        "https://media.tenor.com/Mc8KFXbSJXUAAAAC/anime-blush.gif"
        ],
        "wink":[
        "https://media.tenor.com/YzWbgGF2sIEAAAAC/anime-wink.gif"
        ],
        "thumbsup":[
        "https://media.tenor.com/7hKJhE2gzGEAAAAC/anime-thumbs-up.gif"
        ],
        "clap":[
        "https://media.tenor.com/cxeBKKIqz8oAAAAC/anime-clap.gif"
        ],
        "bow":[
        "https://media.tenor.com/8KYAj3b2JO4AAAAC/anime-bow.gif"
        ],
        "salute":[
        "https://media.tenor.com/7w8WaOVY5T8AAAAC/anime-salute.gif"
        ],
        "facepalm":[
        "https://media.tenor.com/wQ0jLkfWgDYAAAAC/anime-facepalm.gif"
        ],
        "shrug":[
        "https://media.tenor.com/QIFq7g4r79EAAAAC/anime-shrug.gif"
        ],
        "sleep":[
        "https://media.tenor.com/W45_Xl9-enoAAAAC/anime-sleep.gif"
        ],
        "eat":[
        "https://media.tenor.com/qA7wC6Z3oAQAAAAC/anime-eating.gif"
        ],
        "drink":[
        "https://media.tenor.com/BHJqPnXiZdEAAAAC/anime-drink.gif"
        ],
        "run":[
        "https://media.tenor.com/Vq8MbpQlhWEAAAAC/anime-running.gif"
        ]
        }

        fallback_gifs =action_fallbacks .get (action ,action_fallbacks ["hug"])
        return random .choice (fallback_gifs )

    async def create_action_embed (self ,ctx ,action ,target =None ):
        if target and target .id ==ctx .author .id :
            embed =discord .Embed (
            title ="<:icon_danger:1372375135604047902> Invalid Action",
            description ="You can't perform this action on yourself! Try targeting someone else.",
            color =0xff6b6b 
            )
            embed .set_footer (text ="Choose a different target")
            return await ctx .reply (embed =embed ,mention_author =False )


        gif_url =await self .get_roleplay_gif (action )


        action_emojis ={
        "hug":"🤗","kiss":"💋","cuddle":"🫂","pat":"👋","slap":"✋",
        "tickle":"🤭","poke":"👉","wave":"👋","dance":"💃","cry":"😢",
        "laugh":"😂","smile":"😊","blush":"😊","wink":"😉","thumbsup":"👍",
        "clap":"👏","bow":"🙇","salute":"🫡","facepalm":"🤦","shrug":"🤷",
        "sleep":"😴","eat":"🍽️","drink":"🥤","run":"🏃"
        }

        emoji =action_emojis .get (action ,"✨")


        action_colors ={
        "hug":0xff9ff3 ,"kiss":0xff69b4 ,"cuddle":0xffa07a ,"pat":0x98fb98 ,
        "slap":0xff6347 ,"tickle":0xffd700 ,"poke":0x87ceeb ,"wave":0x90ee90 ,
        "dance":0xda70d6 ,"cry":0x4169e1 ,"laugh":0xffd700 ,"smile":0xffb6c1 ,
        "blush":0xffb6c1 ,"wink":0xdda0dd ,"thumbsup":0x32cd32 ,"clap":0xffa500 ,
        "bow":0xd2691e ,"salute":0x4682b4 ,"facepalm":0xf0e68c ,"shrug":0xc0c0c0 ,
        "sleep":0x9370db ,"eat":0xff8c00 ,"drink":0x20b2aa ,"run":0xff4500 
        }

        color =action_colors .get (action ,0x7289da )


        action_descriptions ={
        "hug":[
        f"{ctx.author.display_name} hugs {target.display_name if target else 'everyone'}! 🤗",
        f"{ctx.author.display_name} gives {target.display_name if target else 'everyone'} a warm hug~",
        f"{ctx.author.display_name} wraps {target.display_name if target else 'everyone'} in a loving embrace!"
        ],
        "kiss":[
        f"{ctx.author.display_name} kisses {target.display_name if target else 'the air'}'s lips~"if target else f"{ctx.author.display_name} kisses the air",
        f"{ctx.author.display_name} kissed {target.display_name if target else 'someone'}! Cute!",
        f"{ctx.author.display_name} gives {target.display_name if target else 'everyone'} a sweet kiss 💋"
        ],
        "cuddle":[
        f"{ctx.author.display_name} cuddles {target.display_name if target else 'a pillow'} warmly~",
        f"{ctx.author.display_name} snuggles up to {target.display_name if target else 'someone'}!",
        f"{ctx.author.display_name} gives {target.display_name if target else 'everyone'} cozy cuddles!"
        ],
        "pat":[
        f"{ctx.author.display_name} pats {target.display_name if target else 'someone'} gently",
        f"{ctx.author.display_name} gives {target.display_name if target else 'someone'} headpats~",
        f"{ctx.author.display_name} softly pats {target.display_name if target else 'someone'}"
        ],
        "slap":[
        f"{ctx.author.display_name} slaps {target.display_name if target else 'the air'} playfully!",
        f"{ctx.author.display_name} gives {target.display_name if target else 'someone'} a light slap",
        f"{ctx.author.display_name} playfully slaps {target.display_name if target else 'around'}!"
        ]
        }


        descriptions =action_descriptions .get (action ,[f"{ctx.author.display_name} {action}s {target.display_name if target else ''}!"])
        author_text =random .choice (descriptions )

        embed =discord .Embed (color =0x000000 )
        embed .set_image (url =gif_url )
        embed .set_author (name =author_text ,icon_url =ctx .author .display_avatar .url )

        await ctx .reply (embed =embed ,mention_author =False )

    @commands .hybrid_group (invoke_without_command =True )
    async def roleplay (self ,ctx :Context ):
        """Interactive roleplay commands"""
        if ctx .invoked_subcommand is None :
            await ctx .send_help (ctx .command )

    @roleplay .command ()
    async def hug (self ,ctx :Context ,target :discord .Member =None ):
        """Hug someone sweetly"""
        await self .create_action_embed (ctx ,"hug",target )

    @roleplay .command ()
    async def kiss (self ,ctx :Context ,target :discord .Member =None ):
        """Kiss someone lovingly"""
        await self .create_action_embed (ctx ,"kiss",target )

    @roleplay .command ()
    async def cuddle (self ,ctx :Context ,target :discord .Member =None ):
        """Cuddle someone warmly"""
        await self .create_action_embed (ctx ,"cuddle",target )

    @roleplay .command ()
    async def pat (self ,ctx :Context ,target :discord .Member =None ):
        """Pat someone gently"""
        await self .create_action_embed (ctx ,"pat",target )

    @roleplay .command ()
    async def slap (self ,ctx :Context ,target :discord .Member =None ):
        """Slap someone playfully"""
        await self .create_action_embed (ctx ,"slap",target )

    @roleplay .command ()
    async def tickle (self ,ctx :Context ,target :discord .Member =None ):
        """Tickle someone playfully"""
        await self .create_action_embed (ctx ,"tickle",target )

    @roleplay .command ()
    async def poke (self ,ctx :Context ,target :discord .Member =None ):
        """Poke someone gently"""
        await self .create_action_embed (ctx ,"poke",target )

    @roleplay .command ()
    async def wave (self ,ctx :Context ,target :discord .Member =None ):
        """Wave at someone"""
        await self .create_action_embed (ctx ,"wave",target )

    @roleplay .command ()
    async def dance (self ,ctx :Context ):
        """Dance with joy"""
        await self .create_action_embed (ctx ,"dance")

    @roleplay .command ()
    async def cry (self ,ctx :Context ):
        """Cry sadly"""
        await self .create_action_embed (ctx ,"cry")

    @roleplay .command ()
    async def laugh (self ,ctx :Context ):
        """Laugh heartily"""
        await self .create_action_embed (ctx ,"laugh")

    @roleplay .command ()
    async def smile (self ,ctx :Context ):
        """Smile happily"""
        await self .create_action_embed (ctx ,"smile")

    @roleplay .command ()
    async def blush (self ,ctx :Context ):
        """Blush shyly"""
        await self .create_action_embed (ctx ,"blush")

    @roleplay .command ()
    async def wink (self ,ctx :Context ,target :discord .Member =None ):
        """Wink at someone"""
        await self .create_action_embed (ctx ,"wink",target )

    @roleplay .command ()
    async def thumbsup (self ,ctx :Context ):
        """Give thumbs up"""
        await self .create_action_embed (ctx ,"thumbsup")

    @roleplay .command ()
    async def clap (self ,ctx :Context ):
        """Clap enthusiastically"""
        await self .create_action_embed (ctx ,"clap")

    @roleplay .command ()
    async def bow (self ,ctx :Context ,target :discord .Member =None ):
        """Bow respectfully"""
        await self .create_action_embed (ctx ,"bow",target )

    @roleplay .command ()
    async def salute (self ,ctx :Context ,target :discord .Member =None ):
        """Salute formally"""
        await self .create_action_embed (ctx ,"salute",target )

    @roleplay .command ()
    async def facepalm (self ,ctx :Context ):
        """Facepalm in frustration"""
        await self .create_action_embed (ctx ,"facepalm")

    @roleplay .command ()
    async def shrug (self ,ctx :Context ):
        """Shrug casually"""
        await self .create_action_embed (ctx ,"shrug")

    @roleplay .command ()
    async def sleep (self ,ctx :Context ):
        """Sleep peacefully"""
        await self .create_action_embed (ctx ,"sleep")

    @roleplay .command ()
    async def eat (self ,ctx :Context ):
        """Eat something delicious"""
        await self .create_action_embed (ctx ,"eat")

    @roleplay .command ()
    async def drink (self ,ctx :Context ):
        """Drink something refreshing"""
        await self .create_action_embed (ctx ,"drink")

    @roleplay .command ()
    async def run (self ,ctx :Context ):
        """Run quickly"""
        await self .create_action_embed (ctx ,"run")

async def setup (client :Strelizia ):
    await client .add_cog (Roleplay (client ))
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
