
import discord 
from discord import app_commands 
from discord .ext import commands 
import logging 
import asyncio 
import json 
from datetime import datetime ,timezone ,timedelta 
import time 
from typing import Optional ,List ,Dict ,Union 
import os 


logger =logging .getLogger ('discord')
logger .setLevel (logging .INFO )


APPLICATION_TIMEOUT =1800 
APPLICATION_COOLDOWN =86400 
STAFF_SETUP_TIMEOUT =1760 
MAX_QUESTIONS =15 
MAX_QUESTION_LENGTH =1000 
MAX_ANSWER_LENGTH =2000 


STAFF_CONFIG_FILE ='jsondb/staff_config.json'
STAFF_APPLICATIONS_FILE ='jsondb/staff_applications.json'
STAFF_BLACKLIST_FILE ='jsondb/staff_blacklist.json'


user_application_cooldowns ={}


def utc_to_ist (dt :datetime )->datetime :
    ist_offset =timedelta (hours =5 ,minutes =30 )
    return dt .replace (tzinfo =timezone .utc ).astimezone (timezone (ist_offset ))


def load_json_file (file_path :str )->dict :
    """Load JSON file, create if doesn't exist"""
    try :
        if os .path .exists (file_path ):
            with open (file_path ,'r',encoding ='utf-8')as f :
                data =json .load (f )
                return data if isinstance (data ,dict )else {}
        else :
            return {}
    except Exception as e :
        logger .error (f"Error loading {file_path}: {e}")
        return {}

def save_json_file (file_path :str ,data :dict )->bool :
    """Save data to JSON file"""
    try :
        with open (file_path ,'w',encoding ='utf-8')as f :
            json .dump (data ,f ,indent =2 ,ensure_ascii =False )
        return True 
    except Exception as e :
        logger .error (f"Error saving {file_path}: {e}")
        return False 


async def get_staff_config (bot ,guild_id :int )->Optional [dict ]:
    try :
        logger .debug (f"Getting staff config for guild {guild_id}")

        config_data =load_json_file (STAFF_CONFIG_FILE )
        guild_config =config_data .get (str (guild_id ))

        if guild_config :

            questions =guild_config .get ('questions',[])
            if not isinstance (questions ,list ):
                questions =[]

            return {
            'enabled':bool (guild_config .get ('enabled',False )),
            'review_channel_id':guild_config .get ('review_channel_id'),
            'staff_role_id':guild_config .get ('staff_role_id'),
            'ping_role_id':guild_config .get ('ping_role_id'),
            'auto_approve':bool (guild_config .get ('auto_approve',False )),
            'require_reactions':guild_config .get ('require_reactions',2 ),
            'questions':questions 
            }
        else :
            logger .debug (f"No config found for guild {guild_id}")
            return None 

    except Exception as e :
        logger .error (f"Error getting staff config for guild {guild_id}: {e}")
        return None 

async def save_staff_config (bot ,guild_id :int ,config :dict )->bool :
    try :
        logger .info (f"Starting save_staff_config for guild {guild_id}")
        logger .info (f"Config to save: {config}")


        config_data =load_json_file (STAFF_CONFIG_FILE )


        questions =config .get ('questions',[])
        if not isinstance (questions ,list ):
            questions =[]


        guild_config ={
        'enabled':bool (config .get ('enabled',False )),
        'review_channel_id':config .get ('review_channel_id'),
        'staff_role_id':config .get ('staff_role_id'),
        'ping_role_id':config .get ('ping_role_id'),
        'auto_approve':bool (config .get ('auto_approve',False )),
        'require_reactions':int (config .get ('require_reactions',2 )),
        'questions':questions ,
        'last_updated':datetime .utcnow ().isoformat ()
        }


        config_data [str (guild_id )]=guild_config 


        success =save_json_file (STAFF_CONFIG_FILE ,config_data )

        if success :
            logger .info (f"Successfully saved staff config for guild {guild_id}")
        else :
            logger .error (f"Failed to save staff config for guild {guild_id}")

        return success 

    except Exception as e :
        logger .error (f"Error saving staff config for guild {guild_id}: {e}")
        return False 

async def check_application_cooldown (user_id :int )->bool :
    """Check if user is on cooldown for applications"""
    current_time =time .time ()
    if user_id in user_application_cooldowns :
        if current_time -user_application_cooldowns [user_id ]<APPLICATION_COOLDOWN :
            return True 
    return False 

async def set_application_cooldown (user_id :int ):
    """Set cooldown for user"""
    user_application_cooldowns [user_id ]=time .time ()

async def save_application (bot ,guild_id :int ,user_id :int ,answers :Dict [str ,str ])->bool :
    try :
        logger .info (f"Saving application for user {user_id} in guild {guild_id}")


        applications_data =load_json_file (STAFF_APPLICATIONS_FILE )


        if str (guild_id )not in applications_data :
            applications_data [str (guild_id )]=[]


        application ={
        'user_id':user_id ,
        'answers':answers ,
        'status':'pending',
        'applied_at':datetime .utcnow ().isoformat (),
        'reviewed_at':None ,
        'reviewed_by':None 
        }


        applications_data [str (guild_id )].append (application )


        success =save_json_file (STAFF_APPLICATIONS_FILE ,applications_data )

        if success :
            logger .info (f"Application saved successfully for user {user_id} in guild {guild_id}")
        else :
            logger .error (f"Failed to save application for user {user_id} in guild {guild_id}")

        return success 

    except Exception as e :
        logger .error (f"Error saving application: {e}")
        return False 

async def update_application_status (bot ,guild_id :int ,user_id :int ,status :str ,reviewer_id :int =None )->bool :
    try :
        logger .info (f"Updating application status for user {user_id} in guild {guild_id} to {status}")


        applications_data =load_json_file (STAFF_APPLICATIONS_FILE )

        if str (guild_id )not in applications_data :
            return False 


        guild_applications =applications_data [str (guild_id )]
        for application in guild_applications :
            if application ['user_id']==user_id and application ['status']=='pending':
                application ['status']=status 
                application ['reviewed_at']=datetime .utcnow ().isoformat ()
                application ['reviewed_by']=reviewer_id 
                break 
        else :
            logger .warning (f"No pending application found for user {user_id} in guild {guild_id}")
            return False 


        success =save_json_file (STAFF_APPLICATIONS_FILE ,applications_data )

        if success :
            logger .info (f"Application status updated successfully for user {user_id} in guild {guild_id}")
        else :
            logger .error (f"Failed to update application status for user {user_id} in guild {guild_id}")

        return success 

    except Exception as e :
        logger .error (f"Error updating application status: {e}")
        return False 

async def get_application_stats (bot ,guild_id :int )->Dict [str ,int ]:
    try :

        applications_data =load_json_file (STAFF_APPLICATIONS_FILE )

        if str (guild_id )not in applications_data :
            return {'pending':0 ,'approved':0 ,'rejected':0 ,'total':0 }

        guild_applications =applications_data [str (guild_id )]
        stats ={'pending':0 ,'approved':0 ,'rejected':0 ,'total':0 }

        for application in guild_applications :
            status =application .get ('status','pending')
            if status in stats :
                stats [status ]+=1 
            stats ['total']+=1 

        return stats 

    except Exception as e :
        logger .error (f"Error getting application stats: {e}")
        return {'pending':0 ,'approved':0 ,'rejected':0 ,'total':0 }

async def check_user_blacklisted (guild_id :int ,user_id :int )->Optional [str ]:
    """Check if user is blacklisted, return reason if blacklisted"""
    try :
        blacklist_data =load_json_file (STAFF_BLACKLIST_FILE )

        if str (guild_id )not in blacklist_data :
            return None 

        guild_blacklist =blacklist_data [str (guild_id )]
        for entry in guild_blacklist :
            if entry ['user_id']==user_id :
                return entry .get ('reason','No reason provided')

        return None 

    except Exception as e :
        logger .error (f"Error checking blacklist: {e}")
        return None 

async def check_pending_application (guild_id :int ,user_id :int )->bool :
    """Check if user has pending application"""
    try :
        applications_data =load_json_file (STAFF_APPLICATIONS_FILE )

        if str (guild_id )not in applications_data :
            return False 

        guild_applications =applications_data [str (guild_id )]
        for application in guild_applications :
            if application ['user_id']==user_id and application ['status']=='pending':
                return True 

        return False 

    except Exception as e :
        logger .error (f"Error checking pending application: {e}")
        return False 

async def validate_staff_setup (bot ,guild_id :int )->tuple [bool ,str ]:
    """Validate that staff system is properly configured"""
    try :
        config =await get_staff_config (bot ,guild_id )
        if not config :
            return False ,"Staff system is not configured."
        if not config ['review_channel_id']:
            return False ,"Review channel is not configured."
        if not config ['staff_role_id']:
            return False ,"Staff role is not configured."
        if not config .get ('questions'):
            return False ,"No application questions configured."
        return True ,"Staff system is properly configured."
    except Exception as e :
        logger .error (f"Error validating staff setup for guild {guild_id}: {e}")
        return False ,f"Error validating setup: {str(e)}"


class StaffConfigModal (discord .ui .Modal ,title ="Staff System Setup"):
    def __init__ (self ,bot ,guild_id :int ,config :dict =None ):
        super ().__init__ (timeout =STAFF_SETUP_TIMEOUT )
        self .bot =bot 
        self .guild_id =guild_id 
        self .config =config or {}


        existing_questions ="|".join (self .config .get ('questions',[]))
        self .questions_input =discord .ui .TextInput (
        label ="Application Questions",
        placeholder ="Enter questions separated by | (up to 15 questions)",
        style =discord .TextStyle .paragraph ,
        max_length =4000 ,
        required =True ,
        default =existing_questions if existing_questions else ""
        )
        self .add_item (self .questions_input )

    async def on_submit (self ,interaction :discord .Interaction ):
        try :
            logger .info (f"StaffConfigModal.on_submit called for guild {self.guild_id}")
            await interaction .response .defer (ephemeral =True )


            questions_text =self .questions_input .value .strip ()
            logger .debug (f"Questions text received: {questions_text}")

            if not questions_text :
                logger .warning ("No questions text provided")
                await interaction .followup .send (
                "❌ | You must provide at least one question.",
                ephemeral =True 
                )
                return 

            questions =[q .strip ()for q in questions_text .split ('|')if q .strip ()]
            logger .debug (f"Parsed questions: {questions}")

            if len (questions )>MAX_QUESTIONS :
                logger .warning (f"Too many questions: {len(questions)} > {MAX_QUESTIONS}")
                await interaction .followup .send (
                f"❌ | Maximum {MAX_QUESTIONS} questions allowed. You provided {len(questions)}.",
                ephemeral =True 
                )
                return 

            if not questions :
                logger .warning ("No valid questions after parsing")
                await interaction .followup .send (
                "❌ | Please provide at least one valid question.",
                ephemeral =True 
                )
                return 


            logger .debug (f"Current config before validation: {self.config}")

            if not self .config .get ('review_channel_id'):
                logger .error ("Review channel ID not set in config")
                await interaction .followup .send (
                "❌ | Review channel is required. Please configure it first.",
                ephemeral =True 
                )
                return 

            if not self .config .get ('staff_role_id'):
                logger .error ("Staff role ID not set in config")
                await interaction .followup .send (
                "❌ | Staff role is required. Please configure it first.",
                ephemeral =True 
                )
                return 


            self .config ['questions']=questions 
            self .config .setdefault ('enabled',False )
            self .config .setdefault ('auto_approve',False )
            self .config .setdefault ('require_reactions',2 )

            logger .debug (f"Final config before saving: {self.config}")


            logger .info (f"Attempting to save staff config for guild {self.guild_id}")
            success =await save_staff_config (self .bot ,self .guild_id ,self .config )
            logger .info (f"Save result: {success}")

            if not success :
                logger .error (f"Failed to save configuration for guild {self.guild_id}")
                await interaction .followup .send (
                "❌ | Failed to save configuration. Please check the logs for details.",
                ephemeral =True 
                )
                return 

            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="✅ Staff System Configured",
            description ="Staff system has been successfully configured!",
            color =0x000000 ,
            timestamp =current_time 
            )

            guild =self .bot .get_guild (self .guild_id )
            review_channel =guild .get_channel (self .config ['review_channel_id'])if self .config .get ('review_channel_id')else None 
            staff_role =guild .get_role (self .config ['staff_role_id'])if self .config .get ('staff_role_id')else None 
            ping_role =guild .get_role (self .config ['ping_role_id'])if self .config .get ('ping_role_id')else None 

            embed .add_field (
            name ="🔧 Configuration",
            value =f"**Review Channel:** {review_channel.mention if review_channel else 'Not set'}\n"
            f"**Staff Role:** {staff_role.mention if staff_role else 'Not set'}\n"
            f"**Ping Role:** {ping_role.mention if ping_role else 'Not set'}\n"
            f"**Questions:** {len(questions)} configured",
            inline =False 
            )

            embed .add_field (
            name ="📋 Questions Preview",
            value ="\n".join ([f"{i+1}. {q[:80]}..."if len (q )>80 else f"{i+1}. {q}"for i ,q in enumerate (questions [:5 ])])+
            (f"\n... and {len(questions)-5} more"if len (questions )>5 else ""),
            inline =False 
            )

            embed .add_field (
            name ="📝 Next Steps",
            value ="• Run `/crew enable` to enable the system\n• Users can apply with `/crew apply`\n• Manage with other `/crew` commands",
            inline =False 
            )

            embed .set_footer (text =f"Configured at {current_time.strftime('%I:%M %p IST')}")
            await interaction .followup .send (embed =embed ,ephemeral =True )

        except Exception as e :
            logger .error (f"Error in StaffConfigModal.on_submit: {e}")
            await interaction .followup .send (
            f"❌ | An error occurred: {str(e)}",
            ephemeral =True 
            )


active_applications ={}


class ChatApplicationSession :
    def __init__ (self ,bot ,user :discord .Member ,guild_id :int ,questions :List [str ]):
        self .bot =bot 
        self .user =user 
        self .guild_id =guild_id 
        self .questions =questions 
        self .answers ={}
        self .current_question =0 
        self .channel =None 
        self .start_time =time .time ()

    async def start_application (self ,channel ):
        """Start the chat-based application process"""
        self .channel =channel 
        active_applications [self .user .id ]=self 

        current_time =utc_to_ist (discord .utils .utcnow ())
        embed =discord .Embed (
        title ="📋 Staff Application Started",
        description =f"Welcome to the staff application process!\n\n"
        f"**Instructions:**\n"
        f"• Answer each question honestly and in detail\n"
        f"• You have {APPLICATION_TIMEOUT // 60} minutes to complete\n"
        f"• Type `cancel` at any time to stop\n"
        f"• Questions: {len(self.questions)} total\n\n"
        f"Let's begin!",
        color =0x000000 ,
        timestamp =current_time 
        )
        embed .set_footer (text =f"Application expires in {APPLICATION_TIMEOUT // 60} minutes")

        await channel .send (embed =embed )
        await self .ask_next_question ()

    async def ask_next_question (self ):
        """Ask the next question in the sequence"""
        if self .current_question >=len (self .questions ):
            await self .submit_application ()
            return 

        question =self .questions [self .current_question ]

        embed =discord .Embed (
        title =f"❓ Question {self.current_question + 1} of {len(self.questions)}",
        description =question ,
        color =0x5865F2 
        )
        embed .add_field (
        name ="📝 Instructions",
        value ="Please type your answer below. Make it detailed and thoughtful.",
        inline =False 
        )
        embed .set_footer (text =f"Question {self.current_question + 1}/{len(self.questions)} • Type 'cancel' to stop")

        await self .channel .send (embed =embed )

    async def process_answer (self ,message ):
        """Process the user's answer"""
        if message .content .lower ()=='cancel':
            await self .cancel_application ()
            return 


        if len (message .content )>MAX_ANSWER_LENGTH :
            await message .reply (
            f"❌ | Your answer is too long! Please keep it under {MAX_ANSWER_LENGTH} characters. "
            f"Your answer was {len(message.content)} characters."
            )
            return 


        if len (message .content .strip ())<1 :
            await message .reply (
            "❌ | Please provide an answer."
            )
            return 


        question =self .questions [self .current_question ]
        self .answers [question ]=message .content .strip ()


        await message .add_reaction ("✅")

        self .current_question +=1 


        await asyncio .sleep (2 )
        await self .ask_next_question ()

    async def submit_application (self ):
        """Submit the completed application"""
        try :
            success =await save_application (self .bot ,self .guild_id ,self .user .id ,self .answers )
            if not success :
                await self .channel .send (
                "❌ | Failed to save your application. Please contact an administrator."
                )
                await self .cleanup ()
                return 

            config =await get_staff_config (self .bot ,self .guild_id )
            if not config or not config ['review_channel_id']:
                await self .channel .send (
                "❌ | Staff system is not properly configured."
                )
                await self .cleanup ()
                return 

            review_channel =self .bot .get_channel (config ['review_channel_id'])
            if not review_channel :
                await self .channel .send (
                "❌ | Review channel not found."
                )
                await self .cleanup ()
                return 


            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="📋 New Staff Application",
            color =0x000000 ,
            timestamp =current_time 
            )

            embed .set_thumbnail (url =self .user .avatar .url if self .user .avatar else self .user .default_avatar .url )
            embed .add_field (name ="👤 Applicant",value =f"{self.user.mention} (`{self.user.id}`)",inline =True )
            embed .add_field (name ="📅 Applied",value =current_time .strftime ('%I:%M %p IST, %A, %B %d, %Y'),inline =True )
            embed .add_field (name ="📊 Account Age",value =f"<t:{int(self.user.created_at.timestamp())}:R>",inline =True )

            for i ,(question ,answer )in enumerate (self .answers .items (),1 ):
                question_display =question [:200 ]+"..."if len (question )>200 else question 
                answer_display =answer [:800 ]+"..."if len (answer )>800 else answer 

                embed .add_field (
                name =f"❓ Question {i}",
                value =f"**{question_display}**\n{answer_display}",
                inline =False 
                )

            embed .set_footer (text =f"Application ID: {self.user.id} • Submitted at {current_time.strftime('%I:%M %p IST')}")

            view =ApplicationReviewView (self .bot ,self .user ,self .guild_id )

            ping_content =""
            if config .get ('ping_role_id'):
                guild =self .bot .get_guild (self .guild_id )
                ping_role =guild .get_role (config ['ping_role_id'])
                if ping_role :
                    ping_content =f"{ping_role.mention} New staff application received!"

            await review_channel .send (content =ping_content ,embed =embed ,view =view )
            await set_application_cooldown (self .user .id )


            completion_embed =discord .Embed (
            title ="✅ Application Submitted Successfully!",
            description ="Thank you for applying for staff! Your application has been submitted and will be reviewed by our team.\n\n"
            "You will receive a DM notification once your application has been reviewed.",
            color =0x00ff00 ,
            timestamp =current_time 
            )
            completion_embed .add_field (
            name ="📊 Application Summary",
            value =f"Questions Answered: {len(self.answers)}\n"
            f"Time Taken: {int((time.time() - self.start_time) / 60)} minutes\n"
            f"Status: Under Review",
            inline =False 
            )
            completion_embed .set_footer (text ="Good luck with your application!")

            await self .channel .send (embed =completion_embed )
            await self .cleanup ()

        except Exception as e :
            logger .error (f"Error submitting chat application: {e}")
            await self .channel .send (
            "❌ | An error occurred while submitting your application. Please contact an administrator."
            )
            await self .cleanup ()

    async def cancel_application (self ):
        """Cancel the application process"""
        embed =discord .Embed (
        title ="❌ Application Cancelled",
        description ="Your staff application has been cancelled. You can start a new application anytime using `/crew apply`.",
        color =0xff0000 
        )
        await self .channel .send (embed =embed )
        await self .cleanup ()

    async def cleanup (self ):
        """Clean up the application session"""
        if self .user .id in active_applications :
            del active_applications [self .user .id ]


class StaffSetupView (discord .ui .View ):
    def __init__ (self ,bot ,ctx ):
        super ().__init__ (timeout =STAFF_SETUP_TIMEOUT )
        self .bot =bot 
        self .ctx =ctx 
        self .config ={}

    @discord .ui .select (
    cls =discord .ui .ChannelSelect ,
    channel_types =[discord .ChannelType .text ],
    placeholder ="📢 Select the review channel where applications will be sent..."
    )
    async def channel_select (self ,interaction :discord .Interaction ,select :discord .ui .ChannelSelect ):
        await interaction .response .defer ()
        self .config ['review_channel_id']=select .values [0 ].id 

    @discord .ui .select (
    cls =discord .ui .RoleSelect ,
    placeholder ="👥 Select the staff role that will be given to approved applicants..."
    )
    async def staff_role_select (self ,interaction :discord .Interaction ,select :discord .ui .RoleSelect ):
        await interaction .response .defer ()
        self .config ['staff_role_id']=select .values [0 ].id 

    @discord .ui .select (
    cls =discord .ui .RoleSelect ,
    placeholder ="🔔 Select the ping role for notifications (optional)..."
    )
    async def ping_role_select (self ,interaction :discord .Interaction ,select :discord .ui .RoleSelect ):
        await interaction .response .defer ()
        self .config ['ping_role_id']=select .values [0 ].id 

    @discord .ui .button (label ="📝 Configure Questions",style =discord .ButtonStyle .green ,emoji ="📝")
    async def configure_questions (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        if not self .config .get ('review_channel_id')or not self .config .get ('staff_role_id'):
            await interaction .response .send_message (
            "❌ | Please select at least a review channel and staff role first.",
            ephemeral =True 
            )
            return 


        self .config .setdefault ('enabled',False )
        self .config .setdefault ('auto_approve',False )
        self .config .setdefault ('require_reactions',2 )

        modal =StaffConfigModal (self .bot ,self .ctx .guild .id ,self .config )
        await interaction .response .send_modal (modal )
        self .stop ()

    @discord .ui .button (label ="❌ Cancel",style =discord .ButtonStyle .red ,emoji ="❌")
    async def cancel_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        await interaction .response .send_message ("Staff setup cancelled.",ephemeral =True )
        self .stop ()

    async def on_timeout (self ):
        for item in self .children :
            item .disabled =True 
        try :
            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="⏰ Staff Setup Timed Out",
            description =f"The staff setup process has timed out after {STAFF_SETUP_TIMEOUT // 60} minutes. Please run `/crew setup` again to start over.",
            color =0x000000 ,
            timestamp =current_time 
            )
            embed .set_footer (text =f"Timed out at {current_time.strftime('%I:%M %p IST')}")
            if hasattr (self .ctx ,'interaction')and self .ctx .interaction :
                await self .ctx .interaction .followup .send (embed =embed ,ephemeral =True )
            else :
                await self .ctx .send (embed =embed )
        except Exception as e :
            logger .error (f"Failed to send timeout message: {e}")


class ApplicationReviewView (discord .ui .View ):
    def __init__ (self ,bot ,applicant :discord .Member ,guild_id :int ):
        super ().__init__ (timeout =None )
        self .bot =bot 
        self .applicant =applicant 
        self .guild_id =guild_id 

    @discord .ui .button (label ="Approve",style =discord .ButtonStyle .green ,emoji ="✅",custom_id ="staff_approve")
    async def approve_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :
            await interaction .response .defer (ephemeral =True )

            config =await get_staff_config (self .bot ,self .guild_id )
            if not config or not config ['staff_role_id']:
                await interaction .followup .send (
                "❌ | Staff role is not configured.",
                ephemeral =True 
                )
                return 

            guild =self .bot .get_guild (self .guild_id )
            if not guild :
                await interaction .followup .send (
                "❌ | Guild not found.",
                ephemeral =True 
                )
                return 

            staff_role =guild .get_role (config ['staff_role_id'])
            if not staff_role :
                await interaction .followup .send (
                "❌ | Staff role not found.",
                ephemeral =True 
                )
                return 

            member =guild .get_member (self .applicant .id )
            if not member :
                await interaction .followup .send (
                "❌ | Applicant is no longer in the server.",
                ephemeral =True 
                )
                return 

            await member .add_roles (staff_role ,reason =f"Staff application approved by {interaction.user}")
            await update_application_status (self .bot ,self .guild_id ,self .applicant .id ,'approved',interaction .user .id )

            try :
                current_time =utc_to_ist (discord .utils .utcnow ())
                dm_embed =discord .Embed (
                title ="🎉 Staff Application Approved!",
                description =f"Congratulations! Your staff application for **{guild.name}** has been approved by {interaction.user.mention}.\n\nYou have been assigned the {staff_role.mention} role and can now access staff channels and commands.",
                color =0x00ff00 ,
                timestamp =current_time 
                )
                dm_embed .add_field (name ="👥 Approved By",value =interaction .user .mention ,inline =True )
                dm_embed .add_field (name ="🎯 Role Assigned",value =staff_role .mention ,inline =True )
                dm_embed .set_footer (text =f"Approved at {current_time.strftime('%I:%M %p IST')}")
                await self .applicant .send (embed =dm_embed )
            except discord .Forbidden :
                logger .warning (f"Could not send DM to {self.applicant.id}")

            original_embed =interaction .message .embeds [0 ]
            original_embed .color =0x00ff00 
            original_embed .add_field (
            name ="✅ Status",
            value =f"**APPROVED** by {interaction.user.mention}\nApproved at: {utc_to_ist(discord.utils.utcnow()).strftime('%I:%M %p IST')}",
            inline =False 
            )

            for item in self .children :
                item .disabled =True 

            await interaction .message .edit (embed =original_embed ,view =self )
            await interaction .followup .send (
            f"✅ | Application approved! {member.mention} has been given the {staff_role.mention} role.",
            ephemeral =True 
            )

        except Exception as e :
            logger .error (f"Error approving application: {e}")
            await interaction .followup .send (
            f"❌ | An error occurred: {str(e)}",
            ephemeral =True 
            )

    @discord .ui .button (label ="Reject",style =discord .ButtonStyle .red ,emoji ="❌",custom_id ="staff_reject")
    async def reject_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :
            await interaction .response .defer (ephemeral =True )

            await update_application_status (self .bot ,self .guild_id ,self .applicant .id ,'rejected',interaction .user .id )

            try :
                guild =self .bot .get_guild (self .guild_id )
                current_time =utc_to_ist (discord .utils .utcnow ())
                dm_embed =discord .Embed (
                title ="❌ Staff Application Rejected",
                description =f"We're sorry to inform you that your staff application for **{guild.name if guild else 'the server'}** has been rejected by {interaction.user.mention}.\n\nThank you for your interest in joining our team. You may apply again after 24 hours.",
                color =0xff0000 ,
                timestamp =current_time 
                )
                dm_embed .add_field (name ="👤 Reviewed By",value =interaction .user .mention ,inline =True )
                dm_embed .add_field (name ="⏰ Cooldown",value ="24 hours",inline =True )
                dm_embed .set_footer (text =f"Rejected at {current_time.strftime('%I:%M %p IST')}")
                await self .applicant .send (embed =dm_embed )
            except discord .Forbidden :
                logger .warning (f"Could not send DM to {self.applicant.id}")

            original_embed =interaction .message .embeds [0 ]
            original_embed .color =0xff0000 
            original_embed .add_field (
            name ="❌ Status",
            value =f"**REJECTED** by {interaction.user.mention}\nRejected at: {utc_to_ist(discord.utils.utcnow()).strftime('%I:%M %p IST')}",
            inline =False 
            )

            for item in self .children :
                item .disabled =True 

            await interaction .message .edit (embed =original_embed ,view =self )
            await interaction .followup .send (
            "✅ | Application rejected and applicant has been notified.",
            ephemeral =True 
            )

        except Exception as e :
            logger .error (f"Error rejecting application: {e}")
            await interaction .followup .send (
            f"❌ | An error occurred: {str(e)}",
            ephemeral =True 
            )

    @discord .ui .button (label ="Request Interview",style =discord .ButtonStyle .blurple ,emoji ="🎤",custom_id ="staff_interview")
    async def interview_button (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :
            await interaction .response .defer (ephemeral =True )

            try :
                guild =self .bot .get_guild (self .guild_id )
                current_time =utc_to_ist (discord .utils .utcnow ())
                dm_embed =discord .Embed (
                title ="🎤 Interview Requested",
                description =f"Your staff application for **{guild.name if guild else 'the server'}** has been reviewed, and we would like to invite you for an interview.\n\nPlease contact {interaction.user.mention} to schedule your interview.",
                color =0x5865F2 ,
                timestamp =current_time 
                )
                dm_embed .add_field (name ="👤 Interviewer",value =interaction .user .mention ,inline =True )
                dm_embed .add_field (name ="📞 Contact",value =f"DM {interaction.user.mention}",inline =True )
                dm_embed .set_footer (text =f"Interview requested at {current_time.strftime('%I:%M %p IST')}")
                await self .applicant .send (embed =dm_embed )
            except discord .Forbidden :
                logger .warning (f"Could not send DM to {self.applicant.id}")

            original_embed =interaction .message .embeds [0 ]
            original_embed .add_field (
            name ="🎤 Interview Requested",
            value =f"Interview requested by {interaction.user.mention}\nRequested at: {utc_to_ist(discord.utils.utcnow()).strftime('%I:%M %p IST')}",
            inline =False 
            )

            await interaction .message .edit (embed =original_embed ,view =self )
            await interaction .followup .send (
            f"✅ | Interview request sent to {self.applicant.mention}.",
            ephemeral =True 
            )

        except Exception as e :
            logger .error (f"Error requesting interview: {e}")
            await interaction .followup .send (
            f"❌ | An error occurred: {str(e)}",
            ephemeral =True 
            )


class StartApplicationView (discord .ui .View ):
    def __init__ (self ,bot ,guild_id :int ,questions :List [str ]):
        super ().__init__ (timeout =APPLICATION_TIMEOUT )
        self .bot =bot 
        self .guild_id =guild_id 
        self .questions =questions 

    @discord .ui .button (label ="Start Application",style =discord .ButtonStyle .green ,emoji ="📝",custom_id ="staff_start_app")
    async def start_application (self ,interaction :discord .Interaction ,button :discord .ui .Button ):
        try :

            if interaction .user .id in active_applications :
                await interaction .response .send_message (
                "❌ | You already have an active application in progress!",
                ephemeral =True 
                )
                return 


            guild =self .bot .get_guild (self .guild_id )
            if not guild :
                await interaction .response .send_message (
                "❌ | Guild not found.",
                ephemeral =True 
                )
                return 

            member =guild .get_member (interaction .user .id )
            if not member :
                await interaction .response .send_message (
                "❌ | You must be in the server to apply.",
                ephemeral =True 
                )
                return 

            session =ChatApplicationSession (self .bot ,member ,self .guild_id ,self .questions )
            await session .start_application (interaction .channel )

            button .disabled =True 
            button .label ="Application Started"
            await interaction .response .edit_message (view =self )

        except Exception as e :
            logger .error (f"Error starting chat application: {e}")
            await interaction .response .send_message (
            "❌ | An error occurred while starting your application.",
            ephemeral =True 
            )

    async def on_timeout (self ):
        for item in self .children :
            item .disabled =True 
        try :
            await self .message .edit (view =self )
        except :
            pass 


class Staff (commands .Cog ):
    def __init__ (self ,bot ):
        self .bot =bot 

    async def cog_load (self ):
        """Initialize JSON files when cog loads"""
        try :

            for file_path in [STAFF_CONFIG_FILE ,STAFF_APPLICATIONS_FILE ,STAFF_BLACKLIST_FILE ]:
                if not os .path .exists (file_path ):
                    save_json_file (file_path ,{})
                    logger .info (f"Created {file_path}")

            pass 
        except Exception as e :
            logger .error (f"Error initializing staff system files: {e}")

    @commands .Cog .listener ()
    async def on_message (self ,message ):
        """Listen for application responses in DMs"""
        try :

            if not isinstance (message .channel ,discord .DMChannel ):
                return 


            if message .author .bot :
                return 


            if message .author .id not in active_applications :
                return 

            session =active_applications [message .author .id ]


            if time .time ()-session .start_time >APPLICATION_TIMEOUT :
                await session .cancel_application ()
                return 


            await session .process_answer (message )

        except Exception as e :
            logger .error (f"Error processing application message: {e}")

    @commands .hybrid_group (name ="crew",invoke_without_command =True ,description ="Staff application system commands")
    async def crew (self ,ctx ):
        """Staff application system commands"""
        await ctx .send_help (ctx .command )

    @crew .command (name ="setup",description ="Set up the staff application system for this server.")
    @commands .has_permissions (administrator =True )
    async def crew_setup (self ,ctx ):
        """Set up the staff application system"""
        try :
            if hasattr (ctx ,'response'):
                await ctx .response .defer (ephemeral =True )

            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="📋 Staff System Setup",
            description =f"Configure your staff application system below.\n\n"
            f"**Setup Steps:**\n"
            f"1. Select the review channel where applications will be sent\n"
            f"2. Select the staff role that approved applicants will receive\n"
            f"3. (Optional) Select a ping role for notifications\n"
            f"4. Configure application questions\n\n"
            f"**Note:** Setup expires after {STAFF_SETUP_TIMEOUT // 60} minutes.",
            color =0x000000 ,
            timestamp =current_time 
            )
            embed .set_footer (text =f"Started at {current_time.strftime('%I:%M %p IST')}")

            view =StaffSetupView (self .bot ,ctx )

            if hasattr (ctx ,'followup'):
                message =await ctx .followup .send (embed =embed ,view =view ,ephemeral =True )
            else :
                message =await ctx .send (embed =embed ,view =view )

            await view .wait ()

        except Exception as e :
            logger .error (f"Error in crew_setup: {e}")
            error_message =f"❌ | An error occurred: {e}"
            if hasattr (ctx ,'followup'):
                await ctx .followup .send (error_message ,ephemeral =True )
            else :
                await ctx .send (error_message )

    @crew .command (name ="clear",description ="Clear all pending staff applications")
    @commands .has_permissions (administrator =True )
    async def crew_clear (self ,ctx ):
        """Clear all pending staff applications"""
        try :
            if hasattr (ctx ,'response'):
                await ctx .response .defer (ephemeral =True )


            applications_data =load_json_file (STAFF_APPLICATIONS_FILE )

            if str (ctx .guild .id )not in applications_data :
                message ="❌ | No applications found for this server."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            guild_applications =applications_data [str (ctx .guild .id )]
            pending_count =len ([app for app in guild_applications if app ['status']=='pending'])

            if pending_count ==0 :
                message ="❌ | No pending applications to clear."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            applications_data [str (ctx .guild .id )]=[
            app for app in guild_applications if app ['status']!='pending'
            ]


            success =save_json_file (STAFF_APPLICATIONS_FILE ,applications_data )

            if success :
                current_time =utc_to_ist (discord .utils .utcnow ())
                embed =discord .Embed (
                title ="✅ Pending Applications Cleared",
                description =f"Successfully cleared {pending_count} pending staff application{'s' if pending_count != 1 else ''}.\n\nApproved and rejected applications have been preserved for record keeping.",
                color =0x00ff00 ,
                timestamp =current_time 
                )
                embed .add_field (name ="Cleared by",value =ctx .author .mention ,inline =True )
                embed .add_field (name ="Server",value =ctx .guild .name ,inline =True )
                embed .set_footer (text =f"Cleared at {current_time.strftime('%I:%M %p IST')}")

                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (embed =embed ,ephemeral =True )
                else :
                    await ctx .send (embed =embed )
            else :
                message ="❌ | Failed to clear pending applications. Please try again."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )

        except Exception as e :
            logger .error (f"Error clearing pending applications: {e}")
            error_message =f"❌ | An error occurred while clearing applications: {str(e)}"
            if hasattr (ctx ,'followup'):
                await ctx .followup .send (error_message ,ephemeral =True )
            else :
                await ctx .send (error_message )

    @crew .command (name ="apply",description ="Apply to become a staff member")
    @commands .cooldown (1 ,60 ,commands .BucketType .user )
    @commands .guild_only ()
    async def crew_apply (self ,ctx ):
        """Apply to become a staff member"""
        try :
            if hasattr (ctx ,'response'):
                await ctx .response .defer (ephemeral =True )


            if not ctx .guild :
                message ="❌ | This command can only be used in a server, not in DMs."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 

            user =ctx .author 


            blacklist_reason =await check_user_blacklisted (ctx .guild .id ,user .id )
            if blacklist_reason :
                message =f"❌ | You are blacklisted from staff applications.\n**Reason:** {blacklist_reason}"
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            config =await get_staff_config (self .bot ,ctx .guild .id )
            if not config or not config ['enabled']:
                message ="❌ | The staff application system is not enabled in this server."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            if await check_application_cooldown (user .id ):
                message ="❌ | You can only submit one application every 24 hours."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            if await check_pending_application (ctx .guild .id ,user .id ):
                message ="❌ | You already have a pending staff application."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            if config .get ('staff_role_id'):
                staff_role =ctx .guild .get_role (config ['staff_role_id'])
                if staff_role and staff_role in user .roles :
                    message ="❌ | You already have the staff role."
                    if hasattr (ctx ,'followup'):
                        await ctx .followup .send (message ,ephemeral =True )
                    else :
                        await ctx .send (message )
                    return 


            questions =config .get ('questions',[])
            if not questions :
                message ="❌ | No application questions have been configured. Please contact an administrator."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (message ,ephemeral =True )
                else :
                    await ctx .send (message )
                return 


            try :
                current_time =utc_to_ist (discord .utils .utcnow ())
                dm_embed =discord .Embed (
                title ="📋 Staff Application",
                description =f"You've requested to apply for staff in **{ctx.guild.name}**.\n\n"
                f"**Application Details:**\n"
                f"📝 Questions: {len(questions)}\n"
                f"⏰ Time Limit: 30 minutes\n"
                f"🔄 Cooldown: 24 hours\n\n"
                f"**Instructions:**\n"
                f"• Answer all questions honestly\n"
                f"• Take your time to provide detailed answers\n"
                f"• You will go through questions one by one\n\n"
                f"Click the button below to start your application.",
                color =0x000000 ,
                timestamp =current_time 
                )
                dm_embed .set_footer (text ="Application expires in 30 minutes")

                view =StartApplicationView (self .bot ,ctx .guild .id ,questions )
                await user .send (embed =dm_embed ,view =view )

                success_message ="✅ | Application instructions have been sent to your DMs!"
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (success_message ,ephemeral =True )
                else :
                    await ctx .send (success_message )

            except discord .Forbidden :
                error_message ="❌ | I couldn't send you a DM. Please enable DMs from server members and try again."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (error_message ,ephemeral =True )
                else :
                    await ctx .send (error_message )

        except Exception as e :
            logger .error (f"Error in crew_apply: {e}")
            error_message =f"❌ | An error occurred: {e}"
            if hasattr (ctx ,'followup'):
                await ctx .followup .send (error_message ,ephemeral =True )
            else :
                await ctx .send (error_message )

    @crew .command (name ="enable",description ="Enable the staff application system")
    @commands .has_permissions (administrator =True )
    async def crew_enable (self ,ctx ):
        """Enable the staff application system"""
        try :
            if hasattr (ctx ,'response'):
                await ctx .response .defer (ephemeral =True )

            valid ,validation_message =await validate_staff_setup (self .bot ,ctx .guild .id )
            if not valid :
                error_message =f"❌ | {validation_message} Please run `/crew setup` first."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (error_message ,ephemeral =True )
                else :
                    await ctx .send (error_message )
                return 

            config =await get_staff_config (self .bot ,ctx .guild .id )
            config ['enabled']=True 
            success =await save_staff_config (self .bot ,ctx .guild .id ,config )

            if not success :
                error_message ="❌ | Failed to enable the staff system."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (error_message ,ephemeral =True )
                else :
                    await ctx .send (error_message )
                return 

            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="✅ Staff System Enabled",
            description ="The crew application system has been enabled. Users can now apply using `/crew apply`.",
            color =0x000000 ,
            timestamp =current_time 
            )
            embed .set_footer (text =f"Enabled at {current_time.strftime('%I:%M %p IST')}")

            if hasattr (ctx ,'followup'):
                await ctx .followup .send (embed =embed ,ephemeral =True )
            else :
                await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error in crew_enable: {e}")
            error_message =f"❌ | An error occurred: {e}"
            if hasattr (ctx ,'followup'):
                await ctx .followup .send (error_message ,ephemeral =True )
            else :
                await ctx .send (error_message )

    @crew .command (name ="disable",description ="Disable the staff application system")
    @commands .has_permissions (administrator =True )
    async def crew_disable (self ,ctx ):
        """Disable the staff application system"""
        try :
            if hasattr (ctx ,'response'):
                await ctx .response .defer (ephemeral =True )

            config =await get_staff_config (self .bot ,ctx .guild .id )
            if not config :
                config ={}

            config ['enabled']=False 
            success =await save_staff_config (self .bot ,ctx .guild .id ,config )

            if not success :
                error_message ="❌ | Failed to disable the staff system."
                if hasattr (ctx ,'followup'):
                    await ctx .followup .send (error_message ,ephemeral =True )
                else :
                    await ctx .send (error_message )
                return 

            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="❌ Staff System Disabled",
            description ="The crew application system has been disabled.",
            color =0xff0000 ,
            timestamp =current_time 
            )
            embed .set_footer (text =f"Disabled at {current_time.strftime('%I:%M %p IST')}")

            if hasattr (ctx ,'followup'):
                await ctx .followup .send (embed =embed ,ephemeral =True )
            else :
                await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error in crew_disable: {e}")
            error_message =f"❌ | An error occurred: {e}"
            if hasattr (ctx ,'followup'):
                await ctx .followup .send (error_message ,ephemeral =True )
            else :
                await ctx .send (error_message )

    @crew .command (name ="status",description ="Check the current staff system configuration.")
    @commands .has_permissions (administrator =True )
    async def crew_status (self ,ctx ):
        """Check the current staff system configuration"""
        try :
            if hasattr (ctx ,'response'):
                await ctx .response .defer (ephemeral =True )

            config =await get_staff_config (self .bot ,ctx .guild .id )
            stats =await get_application_stats (self .bot ,ctx .guild .id )

            current_time =utc_to_ist (discord .utils .utcnow ())
            embed =discord .Embed (
            title ="📊 Staff System Status",
            color =0x000000 ,
            timestamp =current_time 
            )

            if config :
                review_channel =self .bot .get_channel (config ['review_channel_id'])if config ['review_channel_id']else None 
                staff_role =ctx .guild .get_role (config ['staff_role_id'])if config ['staff_role_id']else None 
                ping_role =ctx .guild .get_role (config ['ping_role_id'])if config ['ping_role_id']else None 

                embed .add_field (
                name ="🔧 System Status",
                value ="✅ Enabled"if config ['enabled']else "❌ Disabled",
                inline =True 
                )
                embed .add_field (
                name ="📢 Review Channel",
                value =review_channel .mention if review_channel else "❌ Not configured",
                inline =True 
                )
                embed .add_field (
                name ="👥 Staff Role",
                value =staff_role .mention if staff_role else "❌ Not configured",
                inline =True 
                )
                embed .add_field (
                name ="🔔 Ping Role",
                value =ping_role .mention if ping_role else "❌ Not configured",
                inline =True 
                )

                questions =config .get ('questions',[])
                embed .add_field (
                name ="📋 Questions",
                value =f"✅ {len(questions)} configured"if questions else "❌ No questions configured",
                inline =True 
                )
            else :
                embed .description ="❌ Staff system is not configured."

            embed .add_field (
            name ="📈 Statistics",
            value =f"Pending: {stats.get('pending', 0)}\n"
            f"Approved: {stats.get('approved', 0)}\n"
            f"Rejected: {stats.get('rejected', 0)}\n"
            f"Total: {stats.get('total', 0)}",
            inline =True 
            )

            valid ,validation_message =await validate_staff_setup (self .bot ,ctx .guild .id )
            embed .add_field (
            name ="🔧 Setup Status",
            value ="✅ Fully configured"if valid else f"❌ {validation_message}",
            inline =False 
            )

            embed .set_footer (text =f"Status checked at {current_time.strftime('%I:%M %p IST')}")

            if hasattr (ctx ,'followup'):
                await ctx .followup .send (embed =embed ,ephemeral =True )
            else :
                await ctx .send (embed =embed )

        except Exception as e :
            logger .error (f"Error in crew_status: {e}")
            error_message =f"❌ | An error occurred: {e}"
            if hasattr (ctx ,'followup'):
                await ctx .followup .send (error_message ,ephemeral =True )
            else :
                await ctx .send (error_message )

async def setup (bot ):
    await bot .add_cog (Staff (bot ))
    logger .info ("Staff cog has been loaded successfully.")

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
