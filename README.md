<div align="center">

# 🤖 Strelizia Discord Bot

<!-- Add your bot banner here -->
<!-- ![Bot Banner](assets/bot-banner.png) -->

*An all-in-one Discord bot with moderation, music, games, AI chat, and more!*

![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)
![Discord.py](https://img.shields.io/badge/discord.py-2.0+-green.svg)
![License](https://img.shields.io/badge/License-Open%20Source-green.svg)

</div>

---

## ✨ What is Strelizia?

Strelizia is a comprehensive Discord bot that brings everything you need to one place. From server moderation and music streaming to interactive games and AI chatbot features - it's your server's all-in-one solution.

**Features include:** Moderation tools, Music player, Interactive games (Chess, Connect4, Wordle, etc.), AI chat integration, Ticket system, Welcome messages, Logging system, and much more!

## 🚀 Quick Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/strelizia-bot.git
   cd strelizia-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure your bot**
   - Create a `.env` file
   - Add your Discord bot token: `DISCORD_TOKEN=your_token_here`
   - Add other API keys as needed (OpenAI, Spotify, etc.)

4. **Run the bot**
   ```bash
   python main.py
   ```

## ⚙️ Configuration

### Changing Bot Prefix
Edit the prefix in your `.env` file:
```env
BOT_PREFIX=!
```
Or use the command: `!prefix <new_prefix>` (Admin only)

### Adding API Keys
Add these to your `.env` file for full functionality:
```env
DISCORD_TOKEN=your_bot_token
BOT_PREFIX=!
OPENAI_API_KEY=your_openai_key (for AI chat)
SPOTIFY_CLIENT_ID=your_spotify_id (for music)
SPOTIFY_CLIENT_SECRET=your_spotify_secret (for music)
```

### Setting Up Permissions
Make sure your bot has these permissions:
- Send Messages, Embed Links, Manage Messages
- Manage Roles (for moderation)
- Connect & Speak (for music)
- Add Reactions (for games)

## 📸 Adding Images

To add your bot banner and server avatar:

1. **Create an `assets` folder** in your repository
2. **Add your images** to the folder (bot-banner.png, server-avatar.png)
3. **Update the README** by replacing the commented lines:
   ```markdown
   ![Bot Banner](assets/bot-banner.png)
   ![Server Avatar](assets/server-avatar.png)
   ```

**Quick tip:** You can also drag & drop images directly when editing on GitHub!

## ⚙️ Configuration Guide

### 🔑 Owner ID (No Prefix Commands)
Edit `utils/config.py` line 7:
```python
OWNER_IDS = [your_user_id_here, another_id]
```

### 🎵 Lavalink Settings
Add these to your `.env` file:
```env
LAVALINK_HOST=lava-v4.ajieblogs.eu.org
LAVALINK_PORT=443
LAVALINK_SECURE=true
LAVALINK_PASSWORD=https://dsc.gg/ajidevserver
```

### ⚡ Bot Prefix 
Edit `BOT_PREFIX` in `.env` file and restart bot to apply to all guilds:
```env
BOT_PREFIX=!
```

### 📁 File Organization
- **Database files (.db)**: Located in `db/` folder
- **Log files (.log)**: Located in `logs/` folder

## 🏆 Credits

<div align="center">

### 👨‍💻 Development Team

**Developer:** Aegis  
**Discord:** `._.aegis._.`  
**Community:** AeroX Development  
**Discord Server:** [discord.gg/aeroxdev](https://discord.gg/aeroxdev)

---

### 🏛️ Original Olympus Project

**🛡️ Olympus Bot License Agreement**

Based on the original Olympus Bot by Olympus Development.  
**Original Repository:** [olympus-bot](https://github.com/sonujana26/olympus-bot)  
**Discord Server:** [discord.gg/odx](https://discord.gg/odx) (Olympus Server)

*Original Olympus Bot © 2025 Olympus Development — All rights reserved.*

**License Terms:**
- Commercial Use: ❌ Not allowed without paid license from Olympus Team
- Redistribution: ❌ Forbidden. Do not host this code elsewhere  
- Modification: ❌ Not allowed unless licensed
- Patents/Derivatives: ❌ No rights to publish forks under any name

For licensing inquiries: https://discord.gg/odx

---

**Made with ❤️ by [AeroX Development](https://discord.gg/aeroxdev)**

*Based on Olympus • Powered by Python & Discord.py*

</div>