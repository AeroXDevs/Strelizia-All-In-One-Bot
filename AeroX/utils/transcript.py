
import discord 
import datetime 
import logging 
from typing import Optional ,Dict ,Any 
import re 

logger =logging .getLogger ('discord')

async def user_has_support_role (bot ,user )->bool :
    """Check if user has the support role for tickets (including additional support roles)"""
    try :
        if not user or not hasattr (user ,'guild')or not user .guild :
            return False 


        from utils .tickets import get_ticket_role ,get_additional_support_roles 


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

def convert_custom_emojis (text :str )->str :
    """Convert custom Discord emojis to beautiful Unicode emojis"""
    emoji_replacements ={
    r'<:icon_tick:[^>]+>':'<:icon_tick:1372375089668161597>',
    r'<:icon_cross:[^>]+>':'<:icon_cross:1372375094336425986>',
    r'<:icon_danger:[^>]+>':'<:icon_danger:1372375135604047902>',
    r'<:icons_games:[^>]+>':'🎮',
    r'<:headmod:[^>]+>':'👤',
    r'<:AlphaEsportsBlack:[^>]+>':'🏆',
    r'<:land_yildiz:[^>]+>':'⭐',
    r'<:heart_em:[^>]+>':'💖',
    r'<:Heeriye:[^>]+>':'😊',
    r'<a:crown:[^>]+>':'👑',
    r'<a:star:[^>]+>':'⭐',
    r'<a:ban:[^>]+>':'🔨',
    r'<a:_rose:[^>]+>':'🌹',
    r'<a:37496alert:[^>]+>':'🚨',
    r'<a:GIFD:[^>]+>':'😄',
    r'<a:GIFN:[^>]+>':'😔',
    r'<a:max__A:[^>]+>':'✨',
    r'<a:Star:[^>]+>':'⭐',
    r'<a:sg_rd:[^>]+>':'❤️',
    r'<a:RedHeart:[^>]+>':'❤️',
    r'<:[^:]+:[^>]+>':'😊',
    r'<a:[^:]+:[^>]+>':'✨',
    }

    for pattern ,replacement in emoji_replacements .items ():
        text =re .sub (pattern ,replacement ,text )
    return text 

async def generate_transcript (bot ,channel :discord .TextChannel ,ticket_info :Optional [Dict [str ,Any ]]=None )->str :
    """Generate ultra-modern, responsive chat transcript with premium design and smooth navigation"""
    try :

        html_content =f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Ticket Transcript - {channel.name}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&family=Poppins:wght@400;500;600;700&display=swap" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">
    <style>
        :root {{
            /* Dark Theme */
            --bg-primary: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
            --bg-secondary: rgba(30, 30, 60, 0.95);
            --bg-tertiary: rgba(45, 45, 90, 0.8);
            --bg-quaternary: rgba(60, 60, 120, 0.6);
            --glass-bg: rgba(255, 255, 255, 0.05);
            --glass-border: rgba(255, 255, 255, 0.1);
            --border-primary: rgba(100, 200, 255, 0.2);
            --border-secondary: rgba(150, 150, 255, 0.15);
            --text-primary: #ffffff;
            --text-secondary: #b8c5d1;
            --text-muted: #8899a6;
            --text-accent: #64b5f6;
            --accent-blue: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-purple: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);
            --accent-green: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            --accent-orange: linear-gradient(135deg, #ffecd2 0%, #fcb69f 100%);
            --accent-red: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            --bubble-user: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --bubble-staff: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            --bubble-system: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            --shadow-primary: 0 8px 32px rgba(31, 38, 135, 0.37);
            --shadow-hover: 0 12px 40px rgba(31, 38, 135, 0.5);
            --backdrop-blur: blur(15px);
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            line-height: 1.6;
            overflow-x: hidden;
            scroll-behavior: smooth;
            position: relative;
        }}

        /* Animated background particles */
        body::before {{
            content: '';
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(120, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(255, 119, 198, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(120, 219, 255, 0.1) 0%, transparent 50%);
            z-index: -1;
            animation: floatParticles 20s ease-in-out infinite;
        }}

        @keyframes floatParticles {{
            0%, 100% {{ transform: translateY(0px) rotate(0deg); }}
            33% {{ transform: translateY(-10px) rotate(1deg); }}
            66% {{ transform: translateY(5px) rotate(-1deg); }}
        }}

        .chat-container {{
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            max-width: 1200px;
            margin: 0 auto;
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            overflow: hidden;
            box-shadow: var(--shadow-primary);
            position: relative;
        }}

        .chat-header {{
            position: sticky;
            top: 0;
            z-index: 1000;
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border-bottom: 1px solid var(--glass-border);
            padding: 25px 30px;
            margin: 0;
        }}

        .header-content {{
            display: flex;
            align-items: center;
            gap: 20px;
            margin-bottom: 20px;
        }}

        .channel-icon {{
            width: 56px;
            height: 56px;
            background: var(--accent-purple);
            border-radius: 16px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 24px;
            font-weight: 700;
            color: white;
            flex-shrink: 0;
            box-shadow: var(--shadow-primary);
            position: relative;
            overflow: hidden;
        }}

        .channel-icon img {{
            width: 100%;
            height: 100%;
            border-radius: 16px;
            object-fit: cover;
        }}

        .channel-icon::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
            transform: rotate(45deg);
            animation: shimmer 3s infinite;
        }}

        @keyframes shimmer {{
            0% {{ transform: translateX(-100%) rotate(45deg); }}
            100% {{ transform: translateX(100%) rotate(45deg); }}
        }}

        .header-info {{
            flex: 1;
        }}

        .channel-name {{
            font-size: 24px;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 6px;
            font-family: 'Poppins', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .channel-description {{
            font-size: 16px;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        .ticket-metadata {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 16px;
        }}

        .metadata-item {{
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            border-radius: 12px;
            padding: 16px 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            box-shadow: var(--shadow-primary);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }}

        .metadata-item::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 2px;
            background: var(--accent-blue);
            transform: scaleX(0);
            transition: transform 0.3s ease;
        }}

        .metadata-item:hover {{
            transform: translateY(-2px);
            box-shadow: var(--shadow-hover);
        }}

        .metadata-item:hover::before {{
            transform: scaleX(1);
        }}

        .metadata-label {{
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            font-weight: 600;
        }}

        .metadata-value {{
            font-size: 14px;
            color: var(--text-primary);
            font-weight: 600;
            font-family: 'JetBrains Mono', monospace;
        }}

        .messages-area {{
            flex: 1;
            padding: 30px;
            background: transparent;
            position: relative;
        }}

        .message-group {{
            margin-bottom: 35px;
        }}

        .message {{
            display: flex;
            gap: 18px;
            margin-bottom: 12px;
            position: relative;
            animation: messageSlideIn 0.4s ease-out;
        }}

        @keyframes messageSlideIn {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}

        .message:last-child {{
            margin-bottom: 0;
        }}

        .message.user {{
            flex-direction: row-reverse;
        }}

        .message-avatar {{
            width: 44px;
            height: 44px;
            border-radius: 50%;
            overflow: hidden;
            border: 3px solid var(--glass-border);
            flex-shrink: 0;
            position: relative;
            box-shadow: var(--shadow-primary);
        }}

        .message-avatar::after {{
            content: '';
            position: absolute;
            inset: -3px;
            border-radius: 50%;
            background: var(--accent-blue);
            z-index: -1;
            opacity: 0.8;
        }}

        .message-avatar img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
        }}

        .avatar-fallback {{
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: var(--accent-blue);
            color: white;
            font-weight: 700;
            font-size: 16px;
            font-family: 'Poppins', sans-serif;
        }}

        .avatar-fallback.staff {{
            background: var(--accent-purple);
        }}

        .avatar-fallback.system {{
            background: var(--accent-green);
        }}

        .message-content {{
            flex: 1;
            min-width: 0;
        }}

        .message.user .message-content {{
            display: flex;
            flex-direction: column;
            align-items: flex-end;
        }}

        .message-header {{
            display: flex;
            align-items: baseline;
            gap: 12px;
            margin-bottom: 6px;
        }}

        .message.user .message-header {{
            flex-direction: row-reverse;
        }}

        .message-author {{
            font-size: 16px;
            font-weight: 700;
            color: var(--text-primary);
            font-family: 'Poppins', sans-serif;
        }}

        .message-author.staff {{
            background: var(--accent-purple);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .message-author.system {{
            background: var(--accent-green);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .message-timestamp {{
            font-size: 12px;
            color: var(--text-muted);
            font-family: 'JetBrains Mono', monospace;
            font-weight: 500;
        }}

        .message-bubble {{
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 16px 20px;
            max-width: 75%;
            word-wrap: break-word;
            position: relative;
            overflow: hidden;
            box-shadow: var(--shadow-primary);
            transition: all 0.3s ease;
        }}

        .message-bubble:hover {{
            transform: translateY(-1px);
            box-shadow: var(--shadow-hover);
        }}

        .message.user .message-bubble {{
            background: var(--bubble-user);
            border: none;
            color: white;
            border-radius: 20px 20px 6px 20px;
        }}

        .message-bubble.staff {{
            background: var(--bubble-staff);
            border: none;
            color: white;
            border-radius: 20px 20px 20px 6px;
        }}

        .message-bubble.system {{
            background: var(--bubble-system);
            border: none;
            color: white;
            border-radius: 20px;
        }}

        .message-text {{
            font-size: 15px;
            line-height: 1.6;
            white-space: pre-wrap;
            font-weight: 500;
        }}

        .message-attachments {{
            margin-top: 12px;
        }}

        .attachment {{
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: var(--backdrop-blur);
            border-radius: 12px;
            padding: 12px 16px;
            margin-bottom: 8px;
            font-size: 14px;
            display: flex;
            align-items: center;
            gap: 12px;
            border: 1px solid rgba(255, 255, 255, 0.1);
            transition: all 0.3s ease;
        }}

        .attachment:hover {{
            background: rgba(255, 255, 255, 0.15);
            transform: translateX(4px);
        }}

        .attachment-icon {{
            width: 18px;
            height: 18px;
            opacity: 0.8;
        }}

        .attachment-image {{
            max-width: 100%;
            border-radius: 12px;
            margin-top: 12px;
            box-shadow: var(--shadow-primary);
        }}

        .date-separator {{
            display: flex;
            align-items: center;
            margin: 40px 0;
            gap: 20px;
        }}

        .date-separator::before,
        .date-separator::after {{
            content: '';
            flex: 1;
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--glass-border), transparent);
        }}

        .date-separator-text {{
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            border-radius: 25px;
            padding: 8px 20px;
            font-size: 13px;
            color: var(--text-secondary);
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
            box-shadow: var(--shadow-primary);
            font-family: 'Poppins', sans-serif;
        }}

        .theme-toggle {{
            position: fixed;
            top: 10px;
            right: 20px;
            width: 48px;
            height: 48px;
            border: none;
            border-radius: 12px;
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border: 1px solid var(--glass-border);
            color: var(--text-primary);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow-primary);
            z-index: 1002;
        }}

        .theme-toggle:hover {{
            transform: translateY(-2px) scale(1.05);
            box-shadow: var(--shadow-hover);
            background: var(--accent-blue);
            color: white;
        }}

        .theme-toggle:active {{
            transform: translateY(0) scale(1);
        }}

        /* Light theme styles */
        .light-theme {{
            --bg-primary: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 50%, #cbd5e1 100%);
            --bg-secondary: rgba(255, 255, 255, 0.95);
            --bg-tertiary: rgba(248, 250, 252, 0.8);
            --glass-bg: rgba(255, 255, 255, 0.8);
            --glass-border: rgba(0, 0, 0, 0.1);
            --border-primary: rgba(59, 130, 246, 0.2);
            --border-secondary: rgba(99, 102, 241, 0.15);
            --text-primary: #1e293b;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --shadow-primary: 0 8px 32px rgba(0, 0, 0, 0.1);
            --shadow-hover: 0 12px 40px rgba(0, 0, 0, 0.15);
            --backdrop-blur: blur(10px);
        }}

        .light-theme .message-author {{
            color: #1e293b !important;
        }}

        .light-theme .message-author.staff {{
            background: var(--accent-purple);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .light-theme .message-author.system {{
            background: var(--accent-green);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        .light-theme .message-avatar {{
            border: 3px solid rgba(0, 0, 0, 0.2);
        }}

        .light-theme .message-avatar::after {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            opacity: 0.6;
        }}

        .light-theme .message-bubble {{
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(0, 0, 0, 0.1);
            color: var(--text-primary);
        }}

        .light-theme .message.user .message-bubble {{
            background: var(--bubble-user);
            color: white;
        }}

        .light-theme .message-bubble.staff {{
            background: var(--bubble-staff);
            color: white;
        }}

        .light-theme .message-bubble.system {{
            background: var(--bubble-system);
            color: white;
        }}

        .progress-bar {{
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 4px;
            background: var(--accent-blue);
            z-index: 1001;
            transition: width 0.3s ease;
            box-shadow: 0 0 10px rgba(102, 126, 234, 0.5);
        }}

        .footer {{
            background: var(--glass-bg);
            backdrop-filter: var(--backdrop-blur);
            border-top: 1px solid var(--glass-border);
            padding: 25px 30px;
            text-align: center;
            position: relative;
        }}

        .footer-text {{
            font-size: 14px;
            color: var(--text-secondary);
            font-weight: 500;
        }}

        .footer-brand {{
            background: var(--accent-purple);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            text-decoration: none;
            font-weight: 700;
            transition: all 0.3s ease;
        }}

        .footer-brand:hover {{
            background: var(--accent-blue);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}

        /* Enhanced mobile responsiveness */
        @media (max-width: 768px) {{
            .chat-container {{
                border-radius: 0;
                border-left: none;
                border-right: none;
                margin: 0;
                max-width: 100%;
            }}

            .chat-header {{
                padding: 20px 16px;
            }}

            .messages-area {{
                padding: 20px 16px;
            }}

            .message-bubble {{
                max-width: 90%;
                font-size: 14px;
                padding: 12px 16px;
            }}

            .ticket-metadata {{
                grid-template-columns: 1fr;
            }}

            .header-content {{
                gap: 16px;
            }}

            .channel-icon {{
                width: 48px;
                height: 48px;
                font-size: 20px;
            }}

            .channel-name {{
                font-size: 20px;
            }}

            .navigation-bar {{
                bottom: 20px;
                padding: 8px 16px;
            }}

            .nav-button {{
                width: 44px;
                height: 44px;
                font-size: 16px;
            }}
        }}

        /* Smooth animations */
        * {{
            scroll-behavior: smooth;
        }}

        .message {{
            scroll-margin-top: 100px;
        }}

        /* Custom scrollbar */
        ::-webkit-scrollbar {{
            width: 8px;
        }}

        ::-webkit-scrollbar-track {{
            background: transparent;
        }}

        ::-webkit-scrollbar-thumb {{
            background: var(--glass-border);
            border-radius: 4px;
        }}

        ::-webkit-scrollbar-thumb:hover {{
            background: var(--border-primary);
        }}
    </style>
</head>
<body>
    <div class="progress-bar" id="progressBar"></div>
    
    <div class="chat-container">
        <div class="chat-header">
            <div class="header-content">
                <div class="channel-icon">
                    <img src="{bot.user.avatar.url if bot.user.avatar else 'https://cdn.discordapp.com/embed/avatars/0.png'}" alt="Bot Avatar" style="width: 100%; height: 100%; border-radius: 16px; object-fit: cover;">
                </div>
                <div class="header-info">
                    <div class="channel-name">#{channel.name}</div>
                    <div class="channel-description">Ticket Support • {channel.guild.name}</div>
                </div>
            </div>
            <div class="ticket-metadata">
                <div class="metadata-item">
                    <span class="metadata-label">Guild</span>
                    <span class="metadata-value">{channel.guild.name}</span>
                </div>"""

        if ticket_info :
            if ticket_info .get ('category'):
                html_content +=f"""
                <div class="metadata-item">
                    <span class="metadata-label">Category</span>
                    <span class="metadata-value">{ticket_info['category']}</span>
                </div>"""

            if ticket_info .get ('ticket_number'):
                html_content +=f"""
                <div class="metadata-item">
                    <span class="metadata-label">Ticket ID</span>
                    <span class="metadata-value">#{ticket_info['ticket_number']}</span>
                </div>"""

            if ticket_info .get ('created_at'):
                created_date =datetime .datetime .fromisoformat (ticket_info ['created_at']).strftime ('%b %d, %Y')
                html_content +=f"""
                <div class="metadata-item">
                    <span class="metadata-label">Created</span>
                    <span class="metadata-value">{created_date}</span>
                </div>"""

        current_time =datetime .datetime .utcnow ().strftime ('%b %d, %Y')
        html_content +=f"""
                <div class="metadata-item">
                    <span class="metadata-label">Generated</span>
                    <span class="metadata-value">{current_time}</span>
                </div>
            </div>
        </div>
        
        <div class="messages-area" id="messagesArea">"""


        last_date =None 
        message_count =0 


        async for message in channel .history (limit =None ,oldest_first =True ):

            if not message .content and not message .attachments :
                continue 

            message_count +=1 


            message_date =message .created_at .date ()
            if last_date !=message_date :
                if last_date is not None :
                    html_content +=f"""
            <div class="date-separator">
                <div class="date-separator-text">{message_date.strftime('%B %d, %Y')}</div>
            </div>"""
                last_date =message_date 


            is_user =not (message .author .bot or await user_has_support_role (bot ,message .author ))
            is_staff =await user_has_support_role (bot ,message .author )if not message .author .bot else False 
            is_system =message .author .bot 

            message_class ="user"if is_user else ""
            author_class ="staff"if is_staff else ("system"if is_system else "")
            bubble_class ="staff"if is_staff else ("system"if is_system else "")


            if message .author .avatar :
                avatar_html =f'<img src="{message.author.avatar.url}" alt="{message.author.display_name}">'
            else :
                initials ="".join ([name [0 ].upper ()for name in message .author .display_name .split ()[:2 ]])
                fallback_class ="staff"if is_staff else ("system"if is_system else "")
                avatar_html =f'<div class="avatar-fallback {fallback_class}">{initials}</div>'


            content =message .content if message .content else ""
            content =convert_custom_emojis (content )
            content =content .replace ("&","&amp;").replace ("<","&lt;").replace (">","&gt;")


            attachments_html =""
            if message .attachments :
                attachments_html +='<div class="message-attachments">'
                for attachment in message .attachments :
                    if attachment .content_type and attachment .content_type .startswith ('image/'):
                        attachments_html +=f'''
                        <div class="attachment">
                            <span class="attachment-icon">📎</span>
                            <span>{attachment.filename}</span>
                        </div>
                        <img src="{attachment.url}" alt="{attachment.filename}" class="attachment-image">'''
                    else :
                        attachments_html +=f'''
                        <div class="attachment">
                            <span class="attachment-icon">📎</span>
                            <span>{attachment.filename}</span>
                        </div>'''
                attachments_html +='</div>'

            timestamp =message .created_at .strftime ('%H:%M')

            html_content +=f"""
            <div class="message {message_class}" id="message-{message_count}">
                <div class="message-avatar">
                    {avatar_html}
                </div>
                <div class="message-content">
                    <div class="message-header">
                        <span class="message-author {author_class}">{message.author.display_name}</span>
                        <span class="message-timestamp">{timestamp}</span>
                    </div>
                    <div class="message-bubble {bubble_class}">
                        <div class="message-text">{content}</div>
                        {attachments_html}
                    </div>
                </div>
            </div>"""

        html_content +=f"""
        </div>
        
        <div class="footer">
            <div class="footer-text">
                Generated on {datetime.datetime.utcnow().strftime('%B %d, %Y at %H:%M UTC')} • 
                {message_count} messages
            </div>
        </div>
    </div>

    <button class="theme-toggle" id="toggleTheme" title="Toggle dark/light mode">
        <i class="fas fa-moon"></i>
    </button>

    <script>
        // Enhanced progress tracking and theme toggle
        const progressBar = document.getElementById('progressBar');
        const toggleThemeBtn = document.getElementById('toggleTheme');
        
        // Smooth scroll progress tracking
        function updateProgressBar() {{
            const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            const scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            const scrollPercent = (scrollTop / scrollHeight) * 100;
            progressBar.style.width = scrollPercent + '%';
        }}
        
        // Enhanced theme toggle functionality
        let isDarkTheme = true;
        
        function toggleTheme() {{
            const body = document.body;
            isDarkTheme = !isDarkTheme;
            
            if (isDarkTheme) {{
                body.classList.remove('light-theme');
                toggleThemeBtn.innerHTML = '<i class="fas fa-moon"></i>';
                toggleThemeBtn.title = 'Switch to light mode';
            }} else {{
                body.classList.add('light-theme');
                toggleThemeBtn.innerHTML = '<i class="fas fa-sun"></i>';
                toggleThemeBtn.title = 'Switch to dark mode';
            }}
            
            // Save theme preference
            localStorage.setItem('transcript-theme', isDarkTheme ? 'dark' : 'light');
        }}
        
        // Load saved theme preference
        function loadThemePreference() {{
            const savedTheme = localStorage.getItem('transcript-theme');
            if (savedTheme === 'light') {{
                isDarkTheme = true; // Will be toggled to false
                toggleTheme();
            }}
        }}
        
        toggleThemeBtn.addEventListener('click', toggleTheme);
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            switch(e.key) {{
                case 'Home':
                    e.preventDefault();
                    window.scrollTo({{ top: 0, behavior: 'smooth' }});
                    break;
                case 'End':
                    e.preventDefault();
                    window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
                    break;
                case 'PageUp':
                    e.preventDefault();
                    window.scrollBy({{ top: -window.innerHeight * 0.8, behavior: 'smooth' }});
                    break;
                case 'PageDown':
                    e.preventDefault();
                    window.scrollBy({{ top: window.innerHeight * 0.8, behavior: 'smooth' }});
                    break;
                case 't':
                case 'T':
                    if (e.ctrlKey || e.metaKey) {{
                        e.preventDefault();
                        toggleTheme();
                    }}
                    break;
            }}
        }});
        
        // Scroll event listener with throttling for performance
        let scrollTimeout;
        window.addEventListener('scroll', () => {{
            if (scrollTimeout) {{
                clearTimeout(scrollTimeout);
            }}
            scrollTimeout = setTimeout(updateProgressBar, 10);
        }});
        
        // Enhanced hover effects for message bubbles
        document.querySelectorAll('.message-bubble').forEach(bubble => {{
            bubble.addEventListener('mouseenter', () => {{
                bubble.style.transform = 'translateY(-2px) scale(1.02)';
            }});
            
            bubble.addEventListener('mouseleave', () => {{
                bubble.style.transform = 'translateY(0) scale(1)';
            }});
        }});
        
        // Initialize on load
        window.addEventListener('load', () => {{
            loadThemePreference();
            updateProgressBar();
            
            // Add entrance animation to messages
            const messages = document.querySelectorAll('.message');
            messages.forEach((message, index) => {{
                message.style.animationDelay = `${{index * 0.05}}s`;
            }});
        }});
        
        // Initialize immediately
        updateProgressBar();
    </script>
</body>
</html>"""

        return html_content 

    except Exception as e :
        logger .error (f"Error generating ultra-modern transcript: {e}")
        return f"<html><body><h1>Error generating transcript</h1><p>{str(e)}</p></body></html>"

"""
: ! Aegis !
    + Discord: root.exe
    + Community: https://discord.gg/meet (AeroX Development )
    + for any queries reach out Community or DM me.
"""
