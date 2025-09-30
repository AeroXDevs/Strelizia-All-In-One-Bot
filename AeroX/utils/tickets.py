import discord 
import logging 
import aiosqlite 
from typing import Optional 

logger =logging .getLogger ('discord')

async def check_database_connection ():
    try :
        async with aiosqlite .connect ("db/tickets.db")as db :
            await db .execute ("SELECT 1")
            return True 
    except Exception as e :
        logger .error (f"Database connection failed: {e}")
        return False 

async def get_ticket_channel (bot ,guild_id :int )->Optional [discord .TextChannel ]:
    try :
        if not await check_database_connection ():
            return None 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute ("SELECT channel_id FROM tickets WHERE guild_id = ?",(guild_id ,))as cursor :
                result =await cursor .fetchone ()
                if result and result [0 ]:
                    channel =bot .get_channel (result [0 ])
                    if not channel :
                        logger .warning (f"Ticket channel {result[0]} not found for guild {guild_id}")
                    return channel 
                return None 
    except Exception as e :
        logger .error (f"Error getting ticket channel for guild {guild_id}: {e}")
        return None 

async def get_ticket_role (bot ,guild_id :int )->Optional [discord .Role ]:
    try :
        if not await check_database_connection ():
            return None 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute ("SELECT role_id FROM tickets WHERE guild_id = ?",(guild_id ,))as cursor :
                result =await cursor .fetchone ()
                if result and result [0 ]:
                    guild =bot .get_guild (guild_id )
                    if guild :
                        role =guild .get_role (result [0 ])
                        if not role :
                            logger .warning (f"Ticket role {result[0]} not found for guild {guild_id}")
                        return role 
                return None 
    except Exception as e :
        logger .error (f"Error getting ticket role for guild {guild_id}: {e}")
        return None 

async def get_additional_support_roles (bot ,guild_id :int )->list :
    """Get additional support roles for the guild"""
    try :
        if not await check_database_connection ():
            return []
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute ("SELECT role_id FROM ticket_support_roles WHERE guild_id = ?",(guild_id ,))as cursor :
                results =await cursor .fetchall ()
                guild =bot .get_guild (guild_id )
                if not guild :
                    return []
                roles =[]
                for result in results :
                    role =guild .get_role (result [0 ])
                    if role :
                        roles .append (role )
                return roles 
    except Exception as e :
        logger .error (f"Error getting additional support roles for guild {guild_id}: {e}")
        return []

async def is_ticket_channel (bot ,channel :discord .TextChannel )->bool :
    """Check if the channel is a valid ticket channel using database validation"""
    try :
        if not await check_database_connection ():
            return False 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute (
            "SELECT channel_id FROM ticket_instances WHERE channel_id = ?",
            (channel .id ,)
            )as cursor :
                result =await cursor .fetchone ()
                return result is not None 
    except Exception as e :
        logger .error (f"Error checking if channel {channel.id} is a ticket channel: {e}")
        return False 

async def validate_ticket_data (bot ,guild_id :int )->tuple [bool ,str ]:
    """Validate ticket system configuration"""
    try :
        if not await check_database_connection ():
            return False ,"Database connection failed"

        ticket_channel =await get_ticket_channel (bot ,guild_id )
        ticket_role =await get_ticket_role (bot ,guild_id )

        if not ticket_channel :
            return False ,"Ticket channel not configured"
        if not ticket_role :
            return False ,"Support role not configured"

        return True ,"Ticket system is properly configured"
    except Exception as e :
        logger .error (f"Error validating ticket data for guild {guild_id}: {e}")
        return False ,f"Validation error: {str(e)}"

async def user_has_support_role (bot ,user )->bool :
    """Check if user has the support role for tickets (including additional support roles)"""
    try :
        if not user or not hasattr (user ,'guild')or not user .guild :
            return False 


        ticket_role =await get_ticket_role (bot ,user .guild .id )
        if ticket_role and ticket_role in user .roles :
            return True 


        additional_roles =await get_additional_support_roles (bot ,user .guild .id )
        for role in additional_roles :
            if role in user .roles :
                return True 

        return False 
    except (TypeError ,AttributeError )as e :
        logger .error (f"Error checking support role for user {user.id if user else 'None'}: {e}")
        return False 
    except Exception as e :
        logger .error (f"Unexpected error checking support role for user {user.id if user else 'None'}: {e}")
        return False 

async def get_ticket_creator (bot ,channel_id :int )->Optional [int ]:
    """Get the ticket creator ID from the database"""
    try :
        if not await check_database_connection ():
            return None 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute (
            "SELECT creator_id FROM ticket_instances WHERE channel_id = ?",
            (channel_id ,)
            )as cursor :
                result =await cursor .fetchone ()
                return result [0 ]if result else None 
    except Exception as e :
        logger .error (f"Error getting ticket creator for channel {channel_id}: {e}")
        return None 

async def get_all_support_roles (bot ,guild_id :int )->list :
    """Get all support roles (main + additional) for the guild"""
    try :
        roles =[]


        main_role =await get_ticket_role (bot ,guild_id )
        if main_role :
            roles .append (main_role )


        additional_roles =await get_additional_support_roles (bot ,guild_id )
        roles .extend (additional_roles )

        return roles 
    except Exception as e :
        logger .error (f"Error getting all support roles for guild {guild_id}: {e}")
        return []

async def get_ticket_stats (bot ,guild_id :int )->Optional [dict ]:
    """Get ticket statistics for the guild"""
    try :
        if not await check_database_connection ():
            return None 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute (
            "SELECT COUNT(*) FROM ticket_instances WHERE guild_id = ?",
            (guild_id ,)
            )as cursor :
                total_tickets =(await cursor .fetchone ())[0 ]

            async with db .execute (
            "SELECT COUNT(*) FROM ticket_instances WHERE guild_id = ? AND closed_at IS NULL",
            (guild_id ,)
            )as cursor :
                open_tickets =(await cursor .fetchone ())[0 ]

            async with db .execute (
            "SELECT AVG(rating) FROM ticket_ratings WHERE guild_id = ?",
            (guild_id ,)
            )as cursor :
                avg_rating =await cursor .fetchone ()
                avg_rating =round (avg_rating [0 ],1 )if avg_rating [0 ]else 0 

            return {
            'total_tickets':total_tickets ,
            'open_tickets':open_tickets ,
            'closed_tickets':total_tickets -open_tickets ,
            'average_rating':avg_rating 
            }
    except Exception as e :
        logger .error (f"Error getting ticket stats for guild {guild_id}: {e}")
        return None 

async def get_category_discord_channel (bot ,guild_id :int ,category_name :str )->Optional [discord .CategoryChannel ]:
    """Get the Discord category channel for a ticket category"""
    try :
        if not await check_database_connection ():
            return None 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute (
            "SELECT discord_category_id FROM ticket_categories WHERE guild_id = ? AND category_name = ?",
            (guild_id ,category_name )
            )as cursor :
                result =await cursor .fetchone ()
                if result and result [0 ]:
                    return bot .get_channel (result [0 ])
                return None 
    except Exception as e :
        logger .error (f"Error getting category Discord channel: {e}")
        return None 

async def get_ticket_info (bot ,channel_id :int )->Optional [dict ]:
    """Get comprehensive ticket information"""
    try :
        if not await check_database_connection ():
            return None 
        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute (
            "SELECT guild_id, creator_id, category, reason, urgency, created_at, ticket_number FROM ticket_instances WHERE channel_id = ?",
            (channel_id ,)
            )as cursor :
                result =await cursor .fetchone ()
                if result :
                    return {
                    'guild_id':result [0 ],
                    'creator_id':result [1 ],
                    'category':result [2 ],
                    'reason':result [3 ],
                    'urgency':result [4 ],
                    'created_at':result [5 ],
                    'ticket_number':result [6 ]
                    }
            return None 
    except Exception as e :
        logger .error (f"Error getting ticket info for channel {channel_id}: {e}")
        return None 

async def validate_ticket_data (bot ,guild_id :int )->tuple [bool ,str ]:
    """Validate that all ticket system data is properly configured"""
    try :
        if not await check_database_connection ():
            return False ,"Database connection failed"

        async with aiosqlite .connect ("db/tickets.db")as db :
            async with db .execute ("SELECT channel_id, role_id FROM tickets WHERE guild_id = ?",(guild_id ,))as cursor :
                result =await cursor .fetchone ()

            if not result :
                return False ,"Ticket system not configured"

            channel_id ,role_id =result 
            if not channel_id or not role_id :
                return False ,"Missing channel or role configuration"

            return True ,"Ticket system is properly configured"
    except Exception as e :
        logger .error (f"Error validating ticket data for guild {guild_id}: {e}")
        return False ,f"Validation error: {str(e)}"
"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
