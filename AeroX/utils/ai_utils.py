import aiohttp 
import io 
import time 
import os 
import random 
import json 
from langdetect import detect 
from gtts import gTTS 
from urllib .parse import quote 
from utils .config_loader import load_current_language ,config 
from openai import AsyncOpenAI 
from duckduckgo_search import AsyncDDGS 
from dotenv import load_dotenv 

load_dotenv ()

current_language =load_current_language ()
internet_access =config ['INTERNET_ACCESS']


groq_client =AsyncOpenAI (
base_url ="https://api.groq.com/openai/v1",
api_key =os .getenv ("GROQ_API_KEY"),
)


client =AsyncOpenAI (
base_url =config ['API_BASE_URL'],
api_key ="nah-ha",
)

async def generate_response (instructions ,history ):
    messages =[
    {"role":"system","content":instructions },
    *history ,
    ]

    try :

        response =await groq_client .chat .completions .create (
        model ="llama-3.3-70b-versatile",
        messages =messages ,
        max_tokens =2048 ,
        temperature =0.7 
        )
        return response .choices [0 ].message .content 
    except Exception as e :
        print (f"Groq API error: {e}")

        try :
            tools =[
            {
            "type":"function",
            "function":{
            "name":"searchtool",
            "description":"Searches the internet.",
            "parameters":{
            "type":"object",
            "properties":{
            "query":{
            "type":"string",
            "description":"The query for search engine",
            }
            },
            "required":["query"],
            },
            },
            }
            ]
            response =await client .chat .completions .create (
            model =config ['MODEL_ID'],
            messages =messages ,
            tools =tools ,
            tool_choice ="auto",
            )
            response_message =response .choices [0 ].message 
            tool_calls =response_message .tool_calls 

            if tool_calls :
                available_functions ={
                "searchtool":duckduckgotool ,
                }
                messages .append (response_message )

                for tool_call in tool_calls :
                    function_name =tool_call .function .name 
                    function_to_call =available_functions [function_name ]
                    function_args =json .loads (tool_call .function .arguments )
                    function_response =await function_to_call (
                    query =function_args .get ("query")
                    )
                    messages .append (
                    {
                    "tool_call_id":tool_call .id ,
                    "role":"tool",
                    "name":function_name ,
                    "content":function_response ,
                    }
                    )
                second_response =await client .chat .completions .create (
                model =config ['MODEL_ID'],
                messages =messages 
                )
                return second_response .choices [0 ].message .content 
            return response_message .content 
        except Exception as fallback_error :
            return f"Both Groq and fallback API failed: {fallback_error}"

async def duckduckgotool (query )->str :
    if config ['INTERNET_ACCESS']:
        return "internet access has been disabled by user"
    blob =''
    results =await AsyncDDGS (proxy =None ).text (query ,max_results =6 )
    try :
        for index ,result in enumerate (results [:6 ]):
            blob +=f'[{index}] Title : {result["title"]}\nSnippet : {result["body"]}\n\n\n Provide a cohesive response base on provided Search results'
    except Exception as e :
        blob +=f"Search error: {e}\n"
    return blob 


async def poly_image_gen (session ,prompt ):
    seed =random .randint (1 ,100000 )
    image_url =f"https://image.pollinations.ai/prompt/{prompt}?seed={seed}"
    async with session .get (image_url )as response :
        image_data =await response .read ()
        return io .BytesIO (image_data )

async def generate_image_prodia (prompt ,model ,sampler ,seed ,neg ):
    print ("\033[1;32m(Prodia) Creating image for :\033[0m",prompt )
    start_time =time .time ()
    async def create_job (prompt ,model ,sampler ,seed ,neg ):
        url ='https://api.prodia.com/generate'
        params ={
        'new':'true',
        'prompt':f'{quote(prompt)}',
        'model':model ,
        'steps':'100',
        'cfg':'9.5',
        'seed':f'{seed}',
        'sampler':sampler ,
        'upscale':'True',
        'aspect_ratio':'square'
        }
        async with aiohttp .ClientSession ()as session :
            async with session .get (url ,params =params )as response :
                data =await response .json ()
                return data ['job']

    job_id =await create_job (prompt ,model ,sampler ,seed ,neg )
    url =f'https://api.prodia.com/job/{job_id}'
    headers ={
    'authority':'api.prodia.com',
    'accept':'*/*',
    }

    async with aiohttp .ClientSession ()as session :
        while True :
            async with session .get (url ,headers =headers )as response :
                json =await response .json ()
                if json ['status']=='succeeded':
                    async with session .get (f'https://images.prodia.xyz/{job_id}.png?download=1',headers =headers )as response :
                        content =await response .content .read ()
                        img_file_obj =io .BytesIO (content )
                        duration =time .time ()-start_time 
                        print (f"\033[1;34m(Prodia) Finished image creation\n\033[0mJob id : {job_id}  Prompt : ",prompt ,"in",duration ,"seconds.")
                        return img_file_obj 

async def groq_chat_response (message ,history =None ):
    """Generate response using Groq's Llama model"""
    messages =[]

    if history :
        messages .extend (history )

    messages .append ({"role":"user","content":message })

    try :
        response =await groq_client .chat .completions .create (
        model ="llama-3.3-70b-versatile",
        messages =messages ,
        max_tokens =2048 ,
        temperature =0.7 ,
        top_p =1 ,
        stream =False 
        )
        return response .choices [0 ].message .content 
    except Exception as e :
        print (f"Groq API error in chat response: {e}")
        return f"Sorry, I encountered an error: {str(e)}"

async def text_to_speech (text ):
    bytes_obj =io .BytesIO ()
    detected_language =detect (text )
    tts =gTTS (text =text ,lang =detected_language )
    tts .write_to_fp (bytes_obj )
    bytes_obj .seek (0 )
    return bytes_obj 
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
