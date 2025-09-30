
import discord 
from discord .ext import commands 
import random 
import datetime 
import os 
import aiohttp 
from PIL import Image ,ImageDraw ,ImageFont ,ImageFilter 
import io 
import math 
from math import cos ,sin ,pi 
from utils .Tools import blacklist_check ,ignore_check 
from core import Cog 

class Ship (Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 
        self .color =0x000000 


        self .special_users ={1391354149815189564 ,1315815975651774557 }


        self .love_texts ={
        95 :[
        "💖✨ Perfect soulmates - written in destiny! ✨💖",
        "🌟💕 Cosmic love connection - the universe celebrates! 💕🌟",
        "💎💖 Flawless compatibility - diamond-level love! 💖💎",
        "🔥💕 Burning passion meets eternal devotion! 💕🔥",
        "👑💖 Royal love story - fit for a fairy tale! 💖👑"
        ],
        90 :[
        "💖🌟 Soulmates destined to be together forever! 🌟💖",
        "✨💕 A match made in heaven above! 💕✨",
        "💫💖 Perfect harmony - your hearts beat as one! 💖💫",
        "🌹💕 Epic love story waiting to unfold! 💕🌹",
        "💎✨ Rare and precious love connection! ✨💎"
        ],
        85 :[
        "💝🥰 Outstanding compatibility - pure magic! 🥰💝",
        "💖🌸 Beautiful souls meant to intertwine! 🌸💖",
        "✨💕 Sparkling chemistry lights up the stars! 💕✨",
        "🦋💖 Breathtaking romance in full bloom! 💖🦋",
        "🌟💝 Stellar connection beyond compare! 💝🌟"
        ],
        80 :[
        "💕🌹 Excellent compatibility - love blooms! 🌹💕",
        "😍💖 Strong romantic magnetism detected! 💖😍",
        "💝✨ Wonderful chemistry flowing between you! ✨💝",
        "🥰💕 Hearts dancing in perfect rhythm! 💕🥰",
        "💖🦋 Love is definitely painting the sky! 🦋💖"
        ],
        75 :[
        "💓🌸 Great potential for lasting love! 🌸💓",
        "💘💕 Sweet romantic possibilities blooming! 💕💘",
        "🌺💖 Lovely connection growing stronger! 💖🌺",
        "💝🦋 Cupid's arrows found their targets! 🦋💝",
        "✨💓 Magical moments await you both! 💓✨"
        ],
        70 :[
        "😍💐 Promising love on the horizon! 💐😍",
        "💕🌙 Romantic spark under moonlit skies! 🌙💕",
        "💖🌸 Sweet chemistry brewing beautifully! 🌸💖",
        "💝🌟 Tender connection worth nurturing! 🌟💝",
        "🦋💓 Gentle love taking flight! 💓🦋"
        ],
        65 :[
        "😊💌 Good compatibility with sweet potential! 💌😊",
        "💐💕 Nice romantic energy flowing! 💕💐",
        "🌺💖 Pleasant chemistry worth exploring! 💖🌺",
        "💝🌸 Charming connection developing! 🌸💝",
        "🌙💓 Soft romance under gentle stars! 💓🌙"
        ],
        60 :[
        "💭💕 Decent compatibility with effort! 💕💭",
        "🌤️💖 Fair weather love with potential! 💖🌤️",
        "💌🌸 Sweet possibilities if you work together! 🌸💌",
        "⚖️💝 Balanced energy needing nurturing! 💝⚖️",
        "🎯💓 Hit or miss but worth the try! 💓🎯"
        ],
        55 :[
        "🤔💭 Could work with understanding and patience! 💭🤔",
        "🌈💕 Mixed signals but colorful potential! 💕🌈",
        "📚💖 Learning curve ahead in love! 💖📚",
        "🎭💝 Complex but interesting dynamic! 💝🎭",
        "🌊💓 Emotional waves need navigation! 💓🌊"
        ],
        50 :[
        "😅🤝 Friendship foundation might be stronger! 🤝😅",
        "💭🌤️ Neutral ground - could go either way! 🌤️💭",
        "⚖️💫 Perfect balance of maybe! 💫⚖️",
        "🎲💝 Love's dice still rolling! 💝🎲",
        "🌸💭 Slow bloom requires patience! 💭🌸"
        ],
        45 :[
        "🤝💙 Better as supportive friends! 💙🤝",
        "📚🌈 Still discovering each other's wavelengths! 🌈📚",
        "🎭💫 Different energies creating interesting sparks! 💫🎭",
        "🌿💚 Platonic connection might flourish better! 💚🌿",
        "🎨💭 Creative tension but challenging romance! 💭🎨"
        ],
        40 :[
        "😬🎢 Bumpy ride ahead in romance! 🎢😬",
        "⛈️💙 Stormy emotional weather forecast! 💙⛈️",
        "🧩💭 Puzzle pieces struggling to fit! 💭🧩",
        "🌊⚡ Turbulent waters with electric tension! ⚡🌊",
        "🎪💫 Circus-level complexity in love! 💫🎪"
        ],
        35 :[
        "😰🔥 Major differences creating friction! 🔥😰",
        "❄️💙 Cold compatibility reading indeed! 💙❄️",
        "🌪️⚡ Chaotic energy collision detected! ⚡🌪️",
        "💥💔 Explosive but not romantic sparks! 💔💥",
        "🚧💭 Construction zone - proceed with caution! 💭🚧"
        ],
        30 :[
        "💔🌑 Heartbreak highway ahead! 🌑💔",
        "🚫💙 Universe flashing warning signals! 💙🚫",
        "❌🌪️ Destiny strongly advises against this! 🌪️❌",
        "🔮💔 Crystal ball shows romantic disaster! 💔🔮",
        "⛔💭 Better to retreat and regroup! 💭⛔"
        ],
        25 :[
        "💔❄️ Frozen hearts and bitter endings! ❄️💔",
        "🚫⚡ Electric fence around romance! ⚡🚫",
        "🌑💙 Dark void where love should be! 💙🌑",
        "💥🔥 Explosive incompatibility detected! 🔥💥",
        "⚠️💔 Danger: Heartbreak zone ahead! 💔⚠️"
        ],
        20 :[
        "💔🚫 Absolutely incompatible - run away! 🚫💔",
        "⚡💥 Disaster waiting to happen! 💥⚡",
        "🌪️💔 Tornado of tears and drama! 💔🌪️",
        "❌🔥 Toxic combination - avoid at all costs! 🔥❌",
        "💀💔 Love graveyard - nothing survives here! 💔💀"
        ],
        15 :[
        "💀⚰️ Romance is dead on arrival! ⚰️💀",
        "🚫💥 Nuclear-level incompatibility! 💥🚫",
        "⚡💔 Electric chair for any romantic feelings! 💔⚡",
        "🌋💀 Volcanic eruption of incompatibility! 💀🌋",
        "💔🎭 Tragic comedy of romantic errors! 🎭💔"
        ],
        10 :[
        "💔☠️ Absolute romantic apocalypse! ☠️💔",
        "🚫💀 Death sentence for any love hopes! 💀🚫",
        "⚡🌪️ Perfect storm of incompatibility! 🌪️⚡",
        "💥💔 Relationship atomic bomb! 💔💥",
        "🔥❌ Hellfire and eternal romantic damnation! ❌🔥"
        ],
        5 :[
        "💀☠️ Beyond hopeless - even fate gave up! ☠️💀",
        "🚫⚰️ Love is not just dead, it's cremated! ⚰️🚫",
        "💔🌋 Romantic Armageddon unleashed! 🌋💔",
        "⚡💀 Zeus himself forbids this union! 💀⚡",
        "🔮💔 Every fortune teller in the universe says NO! 💔🔮"
        ]
        }

    def get_love_text (self ,percentage ):
        """Get love text based on percentage with enhanced granularity"""
        if percentage >=95 :
            return random .choice (self .love_texts [95 ])
        elif percentage >=90 :
            return random .choice (self .love_texts [90 ])
        elif percentage >=85 :
            return random .choice (self .love_texts [85 ])
        elif percentage >=80 :
            return random .choice (self .love_texts [80 ])
        elif percentage >=75 :
            return random .choice (self .love_texts [75 ])
        elif percentage >=70 :
            return random .choice (self .love_texts [70 ])
        elif percentage >=65 :
            return random .choice (self .love_texts [65 ])
        elif percentage >=60 :
            return random .choice (self .love_texts [60 ])
        elif percentage >=55 :
            return random .choice (self .love_texts [55 ])
        elif percentage >=50 :
            return random .choice (self .love_texts [50 ])
        elif percentage >=45 :
            return random .choice (self .love_texts [45 ])
        elif percentage >=40 :
            return random .choice (self .love_texts [40 ])
        elif percentage >=35 :
            return random .choice (self .love_texts [35 ])
        elif percentage >=30 :
            return random .choice (self .love_texts [30 ])
        elif percentage >=25 :
            return random .choice (self .love_texts [25 ])
        elif percentage >=20 :
            return random .choice (self .love_texts [20 ])
        elif percentage >=15 :
            return random .choice (self .love_texts [15 ])
        elif percentage >=10 :
            return random .choice (self .love_texts [10 ])
        else :
            return random .choice (self .love_texts [5 ])

    def generate_ship_name (self ,name1 ,name2 ):
        """Generate a ship name from two names"""
        if len (name1 )<=2 or len (name2 )<=2 :
            return f"{name1}{name2}"


        mid1 =len (name1 )//2 
        mid2 =len (name2 )//2 

        return f"{name1[:mid1]}{name2[mid2:]}"

    async def fetch_user_avatar (self ,user_id ):
        """Fetch user avatar by ID, even if not in server"""
        try :
            user =await self .bot .fetch_user (user_id )
            avatar_url =user .display_avatar .url 

            async with aiohttp .ClientSession ()as session :
                async with session .get (avatar_url )as resp :
                    if resp .status ==200 :
                        return await resp .read ()
            return None 
        except :
            return None 

    def draw_heart (self ,draw ,x ,y ,size ,fill_color ,outline_color =None ,outline_width =0 ):
        """Draw a proper heart shape"""

        heart_width =size 
        heart_height =int (size *0.9 )


        points =[]
        center_x =x +heart_width //2 
        center_y =y +heart_height //3 


        for angle in range (0 ,360 ,5 ):
            t =angle *pi /180 


            heart_x =16 *(sin (t )**3 )
            heart_y =-(13 *cos (t )-5 *cos (2 *t )-2 *cos (3 *t )-cos (4 *t ))


            px =center_x +heart_x *(heart_width /40 )
            py =center_y +heart_y *(heart_height /40 )

            points .append ((px ,py ))


        if len (points )>2 :
            if outline_color and outline_width >0 :

                draw .polygon (points ,fill =outline_color )

                inner_points =[]
                for px ,py in points :
                    inner_px =center_x +(px -center_x )*0.85 
                    inner_py =center_y +(py -center_y )*0.85 
                    inner_points .append ((inner_px ,inner_py ))
                draw .polygon (inner_points ,fill =fill_color )
            else :
                draw .polygon (points ,fill =fill_color )

    def analyze_background_image (self ,background_path ):
        """Analyze background image to determine optimal sizing using PIL"""
        try :

            with Image .open (background_path )as background :
                width ,height =background .size 
                aspect_ratio =width /height 

                print (f"[SHIP DEBUG] Background: {background_path}")
                print (f"[SHIP DEBUG] Dimensions: {width}x{height}")
                print (f"[SHIP DEBUG] Aspect Ratio: {aspect_ratio:.3f}")



                if height >=600 :
                    avatar_size =int (height *0.55 )
                elif height >=400 :
                    avatar_size =int (height *0.60 )
                else :
                    avatar_size =int (height *0.65 )


                avatar_size =max (120 ,min (avatar_size ,250 ))


                heart_size =int (avatar_size *1.45 )

                print (f"[SHIP DEBUG] Calculated avatar size: {avatar_size}")
                print (f"[SHIP DEBUG] Heart size: {heart_size}")


                title_font_size =max (20 ,int (width *0.035 ))
                percentage_font_size =max (16 ,int (heart_size *0.25 ))


                margin =max (30 ,int ((width -2 *avatar_size -heart_size )/4 ))

                print (f"[SHIP DEBUG] Title font size: {title_font_size}")
                print (f"[SHIP DEBUG] Percentage font size: {percentage_font_size}")
                print (f"[SHIP DEBUG] Margin: {margin}")

                return {
                'width':width ,
                'height':height ,
                'avatar_size':avatar_size ,
                'heart_size':heart_size ,
                'aspect_ratio':aspect_ratio ,
                'title_font_size':title_font_size ,
                'percentage_font_size':percentage_font_size ,
                'margin':margin 
                }

        except Exception as e :
            print (f"[SHIP ERROR] Error analyzing background: {e}")

            return {
            'width':1200 ,
            'height':800 ,
            'avatar_size':200 ,
            'heart_size':120 ,
            'aspect_ratio':1.5 ,
            'title_font_size':32 ,
            'percentage_font_size':24 ,
            'margin':80 
            }

    async def create_ship_image (self ,user1 ,user2 ,percentage ,ship_name ):
        """Create beautiful ship image using full background with large avatars and heart"""
        try :

            import time 
            current_time =int (time .time ()*1000000 )
            random .seed (current_time )


            background_files =['ship1.jpg','ship2.jpg','ship3.jpg','ship4.jpg','ship5.jpg']
            background_file =random .choice (background_files )
            background_path =f"assets/ship/{background_file}"

            print (f"[SHIP DEBUG] Selected background: {background_file}")

            if not os .path .exists (background_path ):
                print (f"[SHIP ERROR] Background not found: {background_path}")
                return None 


            image_data =self .analyze_background_image (background_path )
            width =image_data ['width']
            height =image_data ['height']
            avatar_size =image_data ['avatar_size']
            heart_size =image_data ['heart_size']
            margin =image_data ['margin']
            title_font_size =image_data ['title_font_size']
            percentage_font_size =image_data ['percentage_font_size']


            background =Image .open (background_path ).convert ('RGBA')


            img =background .copy ()
            draw =ImageDraw .Draw (img )


            box_width =int (width *0.90 )
            box_height =int (height *0.80 )
            box_x =(width -box_width )//2 
            box_y =(height -box_height )//2 


            overlay_box =Image .new ('RGBA',(box_width ,box_height ),(0 ,0 ,0 ,0 ))
            overlay_draw =ImageDraw .Draw (overlay_box )
            overlay_draw .rounded_rectangle (
            [(0 ,0 ),(box_width ,box_height )],
            radius =25 ,
            fill =(0 ,0 ,0 ,140 )
            )
            img .paste (overlay_box ,(box_x ,box_y ),overlay_box )
            draw =ImageDraw .Draw (img )



            heart_x =width //2 -heart_size //2 
            heart_y =box_y +int (box_height *0.65 )-heart_size //2 


            avatar_margin =40 
            avatar1_x =box_x +avatar_margin 
            avatar2_x =box_x +box_width -avatar_margin -avatar_size 

            avatar_y =box_y +(box_height -avatar_size )//2 

            print (f"[SHIP DEBUG] Avatar 1 position: ({avatar1_x}, {avatar_y})")
            print (f"[SHIP DEBUG] Avatar 2 position: ({avatar2_x}, {avatar_y})")
            print (f"[SHIP DEBUG] Heart position: ({heart_x}, {heart_y})")


            avatar1_data =None 
            avatar2_data =None 

            if hasattr (user1 ,'display_avatar'):
                try :
                    async with aiohttp .ClientSession ()as session :
                        async with session .get (user1 .display_avatar .with_size (512 ).url )as resp :
                            if resp .status ==200 :
                                avatar1_data =await resp .read ()
                except :
                    pass 
            else :
                avatar1_data =await self .fetch_user_avatar (user1 )

            if hasattr (user2 ,'display_avatar'):
                try :
                    async with aiohttp .ClientSession ()as session :
                        async with session .get (user2 .display_avatar .with_size (512 ).url )as resp :
                            if resp .status ==200 :
                                avatar2_data =await resp .read ()
                except :
                    pass 
            else :
                avatar2_data =await self .fetch_user_avatar (user2 )


            if avatar1_data :
                avatar1 =Image .open (io .BytesIO (avatar1_data )).convert ('RGBA')
                avatar1 =avatar1 .resize ((avatar_size ,avatar_size ),Image .Resampling .LANCZOS )


                mask =Image .new ('L',(avatar_size ,avatar_size ),0 )
                mask_draw =ImageDraw .Draw (mask )
                mask_draw .ellipse ([0 ,0 ,avatar_size ,avatar_size ],fill =255 )
                avatar1 .putalpha (mask )


                ring_width =2 
                draw .ellipse ([avatar1_x -ring_width ,avatar_y -ring_width ,
                avatar1_x +avatar_size +ring_width ,avatar_y +avatar_size +ring_width ],
                outline =(255 ,255 ,255 ,255 ),width =ring_width )

                img .paste (avatar1 ,(avatar1_x ,avatar_y ),avatar1 )


            if avatar2_data :
                avatar2 =Image .open (io .BytesIO (avatar2_data )).convert ('RGBA')
                avatar2 =avatar2 .resize ((avatar_size ,avatar_size ),Image .Resampling .LANCZOS )


                mask =Image .new ('L',(avatar_size ,avatar_size ),0 )
                mask_draw =ImageDraw .Draw (mask )
                mask_draw .ellipse ([0 ,0 ,avatar_size ,avatar_size ],fill =255 )
                avatar2 .putalpha (mask )


                ring_width =2 
                draw .ellipse ([avatar2_x -ring_width ,avatar_y -ring_width ,
                avatar2_x +avatar_size +ring_width ,avatar_y +avatar_size +ring_width ],
                outline =(255 ,255 ,255 ,255 ),width =ring_width )

                img .paste (avatar2 ,(avatar2_x ,avatar_y ),avatar2 )


            self .draw_heart (draw ,heart_x ,heart_y ,heart_size ,(0 ,0 ,0 ,180 ))


            try :
                font =ImageFont .truetype ("utils/arial.ttf",percentage_font_size )
            except :
                font =ImageFont .load_default ()

            percent_text =f"{percentage}%"
            bbox =draw .textbbox ((0 ,0 ),percent_text ,font =font )
            text_width =bbox [2 ]-bbox [0 ]
            text_height =bbox [3 ]-bbox [1 ]


            text_x =width //2 -text_width //2 
            text_y =height //2 -text_height //2 -30 


            draw .text ((text_x ,text_y ),percent_text ,fill =(255 ,255 ,255 ,255 ),font =font )




            output_path ="ship_result.png"
            img .save (output_path ,"PNG",quality =100 ,optimize =True )
            return output_path 

        except Exception as e :
            print (f"Error creating ship image: {e}")
            return None 

    async def send_text_ship (self ,msg ,user1 ,user2 ,rate ,ship_name ,love_text ):
        """Send text-based ship result"""
        user1_name =user1 .name if hasattr (user1 ,'name')else f"User {user1}"
        user2_name =user2 .name if hasattr (user2 ,'name')else f"User {user2}"


        filled =int (rate /10 )
        empty =10 -filled 
        bar ="💖"*filled +"🤍"*empty 

        embed =discord .Embed (
        title =f"{ship_name}",
        description =f"**{user1_name}** + **{user2_name}**",
        color =self .color 
        )

        embed .add_field (
        name ="💘 Compatibility",
        value =f"{bar}\n**{rate}%** - {love_text}",
        inline =False 
        )


        if rate ==100 :
            embed .add_field (
            name ="✨ Special",
            value ="🌟 **Perfect Match!** The stars have aligned! 🌟",
            inline =False 
            )

        embed .set_footer (
        text =f"💝 Ship requested by {msg.author.display_name}",
        icon_url =msg .author .display_avatar .url 
        )

        await msg .edit (embed =embed )

    @commands .hybrid_command (
    name ="ship",
    help ="Ship two users together with advanced visual generation (supports user IDs)",
    usage ="ship [user1/@user1/user_id] [user2/@user2/user_id]"
    )
    @blacklist_check ()
    @ignore_check ()
    @commands .cooldown (1 ,5 ,commands .BucketType .user )
    async def ship (self ,ctx ,user1 =None ,user2 =None ):

        processing_embed =discord .Embed (
        title ="💕 Processing Ship Request...",
        description ="🔮 Consulting the love oracle...",
        color =self .color 
        )
        msg =await ctx .send (embed =processing_embed )

        try :

            if user1 is None :
                user1 =ctx .author 
                guild =ctx .guild 
                members =[m for m in guild .members if not m .bot and m !=ctx .author ]
                if not members :
                    embed =discord .Embed (
                    description ="No other members found in this server!",
                    color =0x000000 
                    )
                    return await msg .edit (embed =embed )
                user2 =random .choice (members )
            elif user2 is None :
                user2 =user1 
                user1 =ctx .author 
            else :

                if isinstance (user1 ,str )and user1 .isdigit ():

                    try :
                        user1 =int (user1 )
                    except :
                        user1 =ctx .author 
                elif not hasattr (user1 ,'id'):

                    try :
                        user1 =await commands .MemberConverter ().convert (ctx ,str (user1 ))
                    except :
                        user1 =ctx .author 

                if isinstance (user2 ,str )and user2 .isdigit ():

                    try :
                        user2 =int (user2 )
                    except :
                        guild =ctx .guild 
                        members =[m for m in guild .members if not m .bot ]
                        user2 =random .choice (members )
                elif not hasattr (user2 ,'id'):

                    try :
                        user2 =await commands .MemberConverter ().convert (ctx ,str (user2 ))
                    except :
                        guild =ctx .guild 
                        members =[m for m in guild .members if not m .bot ]
                        user2 =random .choice (members )


            user1_id =user1 .id if hasattr (user1 ,'id')else user1 
            user2_id =user2 .id if hasattr (user2 ,'id')else user2 


            if user1_id in self .special_users and user2_id in self .special_users :
                rate =100 
            else :
                now =datetime .datetime .now ()

                time_seed =(now .day +now .month +now .year +now .hour +now .minute )/5 
                seed =(float (user1_id )+float (user2_id ))/time_seed 
                random .seed (seed )
                rate =random .randint (1 ,100 )


            love_text =self .get_love_text (rate )


            user1_name =user1 .name if hasattr (user1 ,'name')else f"User{str(user1_id)[-4:]}"
            user2_name =user2 .name if hasattr (user2 ,'name')else f"User{str(user2_id)[-4:]}"
            ship_name =self .generate_ship_name (user1_name ,user2_name )

            print (f"[SHIP DEBUG] User 1: {user1_name} (ID: {user1_id})")
            print (f"[SHIP DEBUG] User 2: {user2_name} (ID: {user2_id})")
            print (f"[SHIP DEBUG] Ship name: {ship_name}")
            print (f"[SHIP DEBUG] Compatibility: {rate}%")


            image_path =await self .create_ship_image (user1 ,user2 ,rate ,ship_name )

            if image_path and os .path .exists (image_path ):

                embed =discord .Embed (
                title =f"Love Calculator - {ship_name}",
                description =f"**Compatibility Rating: {rate}%**\n\n{love_text}",
                color =self .color 
                )

                if rate ==100 :
                    embed .add_field (
                    name ="✨ Perfect Match!",
                    value ="🌟 The universe has spoken! 🌟",
                    inline =False 
                    )

                embed .set_footer (
                text =f"💝 Ship requested by {ctx.author.display_name}",
                icon_url =ctx .author .display_avatar .url 
                )


                file =discord .File (image_path ,filename ="ship.png")
                embed .set_image (url ="attachment://ship.png")

                await msg .edit (embed =embed ,attachments =[file ])


                os .remove (image_path )
            else :
                await self .send_text_ship (msg ,user1 ,user2 ,rate ,ship_name ,love_text )

        except Exception as e :
            print (f"Error in ship command: {e}")
            error_embed =discord .Embed (
            description ="Something went wrong while calculating compatibility!",
            color =0x000000 
            )
            await msg .edit (embed =error_embed )

async def setup (bot ):
    await bot .add_cog (Ship (bot ))
