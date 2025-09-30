from __future__ import annotations 
from core import Strelizia 
from colorama import Fore ,Style ,init 
import asyncio 
import traceback 


init (autoreset =True )


from .commands .help import Help 
from .commands .helpslash import HelpSlash 
from .commands .general import General 
from .commands .tracking import TrackingCog 
from .commands .unblacklist import Unblacklist 
from .commands .counting import Counting 
from .commands .music import Music 
from .commands .automod import Automod 
from .commands .welcomer import Welcomer 
from .commands .leveling import Leveling 
from .commands .fun import Fun 

from .commands .Games import Games 
from .commands .extra import Extra 
from .commands .owner import Owner 
from .commands .voice import Voice 
from .commands .afk import afk 
from .commands .ignore import Ignore 
from .commands .discordlogging import Logging 
from .commands .Media import Media 
from .commands .Invc import Invcrole 
from .commands .giveaway import Giveaway 
from .commands .Embed import Embed 
from .commands .steal import Steal 
from .commands .ticket import AdvancedTicketSystem 
from .commands .timer import Timer 
from .commands .staff import Staff 
from .commands .verification import Verification 
from .commands .ytverify import YTVerify 
from .commands .roleplay import Roleplay 
from .commands .blacklist import Blacklist 
from .commands .block import Block 
from .commands .nightmode import Nightmode 
from .commands .ai import AI 
from .commands .owner import Badges 
from .commands .autoresponder import AutoResponder 
from .commands .customrole import Customrole 
from .commands .autorole import AutoRole 
from .commands .antinuke import Antinuke 
from .commands .extraown import Extraowner 
from .commands .anti_wl import Whitelist 
from .commands .anti_unwl import Unwhitelist 
from .commands .slots import Slots 
from .commands .blackjack import Blackjack 
from .commands .autoreact import AutoReaction 
from .commands .stats import Stats 
from .commands .emergency import Emergency 
from .commands .notify import NotifCommands 
from .commands .status import Status 
from .commands .np import NoPrefix 
from .commands .filters import FilterCog 
from .commands .owner2 import Global 
from .commands .backup_final import Backup 
from .commands .stickymessage import StickyMessage 
from .commands .booster import Booster 
from .commands .vanityroles import VanityRoles 




from .events .autoblacklist import AutoBlacklist 
from .events .Errors import Errors 
from .events .on_guild import Guild 
from .events .autorole import Autorole2 
from .events .auto import Autorole 
from .events .greet2 import greet 
from .events .mention import Mention 
from .events .ai import AIResponses 
from .events .booster import BoosterListener 
from .events .react import React 
from .events .autoreact import AutoReactListener 
from .events .stickymessage import StickyMessageListener 




from .strelizia .main_menu .general import _general 
from .strelizia .main_menu .voice import _voice 
from .strelizia .main_menu .games import _games 
from .strelizia .main_menu .welcome import _welcome 
from .strelizia .main_menu .stickymessage import __sticky 
from .strelizia .main_menu .booster import __boost 
from .strelizia .main_menu .ticket import ticket 


from .strelizia .extra_menu .antinuke import _antinuke 
from .strelizia .extra_menu .automod import _automod 
from .strelizia .extra_menu .leveling import _leveling 
from .strelizia .extra_menu .music import _music 
from .strelizia .extra_menu .extra import _extra 
from .strelizia .extra_menu .fun import _fun 

from .strelizia .extra_menu .ai import _ai 
from .strelizia .extra_menu .giveaway import _giveaway 
from .strelizia .extra_menu .moderation import _moderation 
from .strelizia .extra_menu .server import _server 
from .strelizia .extra_menu .roleplay import RoleplayHelp 
from .strelizia .extra_menu .verification import VerificationHelp 
from .strelizia .extra_menu .ytverify import YTVerifyHelp 
from .strelizia .extra_menu .tracking import _tracking 
from .strelizia .extra_menu .logging import _logging 
from .strelizia .extra_menu .counting import _counting 
from .strelizia .extra_menu .backup import _Backup 
from .strelizia .extra_menu .crew import _crew 
from .strelizia .extra_menu .ignore import _ignore 
from .commands .staff import Staff as staff 

from .antinuke .anti_member_update import AntiMemberUpdate 
from .antinuke .antiban import AntiBan 
from .antinuke .antibotadd import AntiBotAdd 
from .antinuke .antichcr import AntiChannelCreate 
from .antinuke .antichdl import AntiChannelDelete 
from .antinuke .antichup import AntiChannelUpdate 
from .antinuke .antieveryone import AntiEveryone 
from .antinuke .antiguild import AntiGuildUpdate 
from .antinuke .antiIntegration import AntiIntegration 
from .antinuke .antikick import AntiKick 
from .antinuke .antiprune import AntiPrune 
from .antinuke .antirlcr import AntiRoleCreate 
from .antinuke .antirldl import AntiRoleDelete 
from .antinuke .antirlup import AntiRoleUpdate 
from .antinuke .antiwebhook import AntiWebhookUpdate 
from .antinuke .antiwebhookcr import AntiWebhookCreate 
from .antinuke .antiwebhookdl import AntiWebhookDelete 









from .automod .antispam import AntiSpam 
from .automod .anticaps import AntiCaps 
from .automod .antilink import AntiLink 
from .automod .anti_invites import AntiInvite 
from .automod .anti_mass_mention import AntiMassMention 
from .automod .anti_emoji_spam import AntiEmojiSpam 

from .moderation .ban import Ban 
from .moderation .unban import Unban 
from .moderation .timeout import Mute 
from .moderation .unmute import Unmute 
from .moderation .lock import Lock 
from .moderation .unlock import Unlock 
from .moderation .hide import Hide 
from .moderation .unhide import Unhide 
from .moderation .kick import Kick 
from .moderation .warn import Warn 
from .moderation .role import Role 
from .moderation .message import Message 
from .moderation .moderation import Moderation 
from .moderation .topcheck import TopCheck 
from .moderation .snipe import Snipe 


async def setup (bot :Strelizia ):

    cogs_to_load =[
    (Help ,"Help"),
    (HelpSlash ,"HelpSlash"),
    (Leveling ,"Leveling"),
    (TrackingCog ,"TrackingCog"),
    (Counting ,"Counting"),
    (Unblacklist ,"Unblacklist"),
    (General ,"General"),
    (Music ,"Music"),
    (Automod ,"Automod"),
    (Backup ,"Backup"),

    (Welcomer ,"Welcomer"),
    (StickyMessage ,"StickyMessage"),
    (StickyMessageListener ,"StickyMessageListener"),
    (Booster ,"Booster"),
    (BoosterListener ,"BoosterListener"),
    (Fun ,"Fun"),
    (Games ,"Games"),
    (Logging ,"Logging"),
    (Extra ,"Extra"),
    (Voice ,"Voice"),
    (Owner ,"Owner"),
    (Customrole ,"Customrole"),
    (afk ,"afk"),
    (Embed ,"Embed"),
    (Media ,"Media"),
    (Ignore ,"Ignore"),
    (Invcrole ,"Invcrole"),
    (Giveaway ,"Giveaway"),
    (Steal ,"Steal"),
    (AdvancedTicketSystem ,"AdvancedTicketSystem"),
    (Timer ,"Timer"),
    (Staff ,"Staff"),
    (Verification ,"Verification"),
    (YTVerify ,"YTVerify"),
    (Roleplay ,"Roleplay"),
    (Blacklist ,"Blacklist"),
    (Block ,"Block"),
    (Nightmode ,"Nightmode"),
    (AI ,"AI"),
    (Badges ,"Badges"),
    (Antinuke ,"Antinuke"),
    (Whitelist ,"Whitelist"),
    (Unwhitelist ,"Unwhitelist"),
    (Extraowner ,"Extraowner"),
    (Slots ,"Slots"),
    (Blackjack ,"Blackjack"),
    (Stats ,"Stats"),
    (Emergency ,"Emergency"),
    (Status ,"Status"),
    (NoPrefix ,"NoPrefix"),
    (FilterCog ,"FilterCog"),
    (Global ,"Global"),
    (VanityRoles ,"VanityRoles"),


    (_general ,"_general"),
    (_voice ,"_voice"),
    (_games ,"_games"),
    (_welcome ,"_welcome"),
    (__sticky ,"__sticky"),
    (__boost ,"__boost"),
    (ticket ,"_ticket"),


    (_antinuke ,"_antinuke"),
    (_automod ,"_automod"),
    (_leveling ,"_leveling"),
    (_music ,"_music"),
    (_extra ,"_extra"),
    (_fun ,"_fun"),

    (_ai ,"_ai"),
    (_giveaway ,"_giveaway"),
    (_moderation ,"_moderation"),
    (_server ,"_server"),
    (RoleplayHelp ,"RoleplayHelp"),
    (VerificationHelp ,"VerificationHelp"),
    (YTVerifyHelp ,"YTVerifyHelp"),
    (_tracking ,"_tracking"),
    (_logging ,"_logging"),
    (_counting ,"_counting"),
    (_Backup ,"_Backup"),
    (_crew ,"_crew"),
    (_ignore ,"_ignore"),
    (AutoBlacklist ,"AutoBlacklist"),
    (Guild ,"Guild"),
    (Errors ,"Errors"),
    (Autorole2 ,"Autorole2"),
    (Autorole ,"Autorole"),
    (greet ,"greet"),
    (AutoResponder ,"AutoResponder"),
    (Mention ,"Mention"),
    (AutoRole ,"AutoRole"),
    (React ,"React"),
    (AutoReaction ,"AutoReaction"),
    (AutoReactListener ,"AutoReactListener"),
    (NotifCommands ,"NotifCommands"),
    (AntiMemberUpdate ,"AntiMemberUpdate"),
    (AntiBan ,"AntiBan"),
    (AntiBotAdd ,"AntiBotAdd"),
    (AntiChannelCreate ,"AntiChannelCreate"),
    (AntiChannelDelete ,"AntiChannelDelete"),
    (AntiChannelUpdate ,"AntiChannelUpdate"),
    (AntiEveryone ,"AntiEveryone"),
    (AntiGuildUpdate ,"AntiGuildUpdate"),
    (AntiIntegration ,"AntiIntegration"),
    (AntiKick ,"AntiKick"),
    (AntiPrune ,"AntiPrune"),
    (AntiRoleCreate ,"AntiRoleCreate"),
    (AntiRoleDelete ,"AntiRoleDelete"),
    (AntiRoleUpdate ,"AntiRoleUpdate"),
    (AntiWebhookUpdate ,"AntiWebhookUpdate"),
    (AntiWebhookCreate ,"AntiWebhookCreate"),
    (AntiWebhookDelete ,"AntiWebhookDelete"),
    (AntiSpam ,"AntiSpam"),
    (AntiCaps ,"AntiCaps"),
    (AntiLink ,"AntiLink"),
    (AntiInvite ,"AntiInvite"),
    (AntiMassMention ,"AntiMassMention"),
    (AntiEmojiSpam ,"AntiEmojiSpam"),
    (Ban ,"Ban"),
    (Unban ,"Unban"),
    (Mute ,"Mute"),
    (Unmute ,"Unmute"),
    (Lock ,"Lock"),
    (Unlock ,"Unlock"),
    (Hide ,"Hide"),
    (Unhide ,"Unhide"),
    (Kick ,"Kick"),
    (Warn ,"Warn"),
    (Role ,"Role"),
    (Message ,"Message"),
    (Moderation ,"Moderation"),
    (TopCheck ,"TopCheck"),
    (Snipe ,"Snipe"),

    ]

    failed_cogs =[]
    loaded_cogs =0 

    for cog_class ,cog_name in cogs_to_load :
        try :
            await bot .add_cog (cog_class (bot ))
            loaded_cogs +=1 
        except Exception as e :
            failed_cogs .append (cog_name )
            print (f"{Fore.RED}✗ Failed to load cog {cog_name}: {str(e)}{Style.RESET_ALL}")

            if "database"in str (e ).lower ()or "import"in str (e ).lower ():
                traceback .print_exc ()


    if failed_cogs :
        print (f"{Fore.RED}✗ Failed to load {len(failed_cogs)} cogs: {', '.join(failed_cogs)}{Style.RESET_ALL}")
    else :
        print (f"{Fore.GREEN}✓ All {loaded_cogs} cogs loaded successfully{Style.RESET_ALL}")



"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""