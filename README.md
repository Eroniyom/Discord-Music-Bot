# 🎵 Discord Music Bot

A powerful Discord music bot built with Python and discord.py that provides high-quality audio streaming from YouTube with advanced queue management features.

## ✨ Features

- 🎵 **High-Quality Audio**: Stream music directly from YouTube with excellent audio quality
- 🎧 **Spotify Integration**: Play songs, albums, and playlists from Spotify (requires API setup)
- 📋 **Queue Management**: Add multiple songs to queue, shuffle, and manage your playlist
- 🎛️ **Playback Controls**: Play, pause, resume, skip, and stop music
- 🔊 **Volume Control**: Adjust volume from 0-100%
- 🔍 **Smart Search**: Search for songs by name or paste YouTube/Spotify URLs
- ⏱️ **Duration Limits**: Configurable maximum song length to prevent extremely long tracks
- 🎨 **Rich Embeds**: Beautiful Discord embeds with thumbnails and song information
- 🛡️ **Error Handling**: Comprehensive error handling with user-friendly messages
- 🚀 **Easy Setup**: Simple configuration and deployment

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system
- A Discord bot token

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/Eroniyom/discord-music-bot.git
   cd discord-music-bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg**
   
   **Windows:**
   - Download from [FFmpeg website](https://ffmpeg.org/download.html)
   - Add to your system PATH
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

4. **Configure the bot**
   ```bash
   cp env_example.txt .env
   ```
   
   Edit `.env` file and add your Discord bot token:
   ```
   DISCORD_TOKEN=your_bot_token_here
   DISCORD_PREFIX=!
   
   # Optional: For Spotify support
   SPOTIFY_CLIENT_ID=your_spotify_client_id_here
   SPOTIFY_CLIENT_SECRET=your_spotify_client_secret_here
   ```

5. **Run the bot**
   ```bash
   python run.py
   ```

## 🤖 Bot Setup

### Creating a Discord Bot

1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Click "New Application" and give it a name
3. Go to the "Bot" section
4. Click "Add Bot"
5. Copy the bot token and add it to your `.env` file
6. Under "Privileged Gateway Intents", enable:
   - Message Content Intent
   - Server Members Intent (optional)

### Bot Permissions

When inviting the bot to your server, make sure it has these permissions:
- Send Messages
- Use Slash Commands
- Connect (to voice channels)
- Speak (in voice channels)
- Embed Links
- Attach Files

## 📋 Commands

### 🎵 Music Commands
- `!play <song/url>` - Play a song from YouTube or Spotify
- `!pause` - Pause the current song
- `!resume` - Resume the paused song
- `!skip` - Skip the current song
- `!stop` - Stop music and clear queue
- `!nowplaying` - Show current song info

### 📋 Queue Commands
- `!queue` - Show the current queue
- `!shuffle` - Shuffle the queue
- `!clear` - Clear the queue

### 🔊 Audio Commands
- `!volume <0-100>` - Set volume
- `!join` - Join your voice channel
- `!leave` - Leave voice channel

### ℹ️ Utility Commands
- `!help` - Show all available commands

## ⚙️ Configuration

You can customize the bot behavior by modifying `config.py`:

```python
# Music Configuration
MAX_QUEUE_SIZE = 50          # Maximum songs in queue
MAX_SONG_LENGTH = 600        # Maximum song length in seconds (10 minutes)
DEFAULT_VOLUME = 0.5         # Default volume (0.0 to 1.0)

# Bot Settings
BOT_NAME = "MusicBot"
DISCORD_PREFIX = "!"         # Command prefix

# Spotify Configuration (Optional)
SPOTIFY_CLIENT_ID = "your_client_id"
SPOTIFY_CLIENT_SECRET = "your_client_secret"
```

## 🎧 Spotify Setup (Optional)

To enable Spotify support:

1. **Create a Spotify App:**
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)
   - Click "Create App"
   - Fill in app details
   - Copy Client ID and Client Secret

2. **Add to Environment:**
   ```bash
   SPOTIFY_CLIENT_ID=your_client_id_here
   SPOTIFY_CLIENT_SECRET=your_client_secret_here
   ```

3. **Supported Spotify URLs:**
   - `https://open.spotify.com/track/...` - Single tracks
   - `https://open.spotify.com/album/...` - Albums (max 20 tracks)
   - `https://open.spotify.com/playlist/...` - Playlists (max 20 tracks)
   - `spotify:track:...` - Spotify URI format

## 🛠️ Development

### Project Structure

```
discord-music-bot/
├── music_bot.py          # Main bot file
├── spotify_handler.py    # Spotify API integration
├── config.py             # Configuration settings
├── run.py                # Bot launcher
├── setup.py              # Package setup
├── requirements.txt      # Python dependencies
├── env_example.txt       # Environment variables template
├── .gitignore           # Git ignore rules
└── README.md            # This file
```

### Adding New Features

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 🐛 Troubleshooting

### Common Issues

**Bot doesn't join voice channel:**
- Check if the bot has "Connect" and "Speak" permissions
- Ensure you're in a voice channel when using commands

**Audio quality issues:**
- Make sure FFmpeg is properly installed
- Check your internet connection
- Try adjusting the volume settings

**Commands not working:**
- Verify the bot has "Send Messages" permission
- Check if Message Content Intent is enabled
- Ensure you're using the correct command prefix

**Queue issues:**
- The queue has a maximum size limit (default: 50 songs)
- Songs longer than 10 minutes are automatically rejected

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. For major changes, please open an issue first to discuss what you would like to change.

## ⚠️ Disclaimer

This bot is for educational purposes. Please respect YouTube's Terms of Service and Discord's Terms of Service when using this bot. The developers are not responsible for any misuse of this software.

## 📞 Support

If you encounter any issues or have questions:

1. Check the [Issues](https://github.com/Eroniyom/discord-music-bot/issues) page
2. Create a new issue with detailed information
3. Join our Discord server for community support: [Discord Server](https://discord.gg/ptZ5B3s3)

## 🙏 Acknowledgments

- [discord.py](https://github.com/Rapptz/discord.py) - Discord API wrapper
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube downloader
- [spotipy](https://github.com/plamere/spotipy) - Spotify Web API wrapper
- [FFmpeg](https://ffmpeg.org/) - Audio processing

---

Made with ❤️ by [Eroniyom](https://github.com/Eroniyom)
