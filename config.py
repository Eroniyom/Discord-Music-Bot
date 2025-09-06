import os
from dotenv import load_dotenv

load_dotenv()

# Bot Configuration
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
DISCORD_PREFIX = os.getenv('DISCORD_PREFIX', '!')
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

# Spotify Configuration
SPOTIFY_CLIENT_ID = os.getenv('SPOTIFY_CLIENT_ID')
SPOTIFY_CLIENT_SECRET = os.getenv('SPOTIFY_CLIENT_SECRET')

# Music Configuration
MAX_QUEUE_SIZE = 50
MAX_SONG_LENGTH = 600  # 10 minutes in seconds
DEFAULT_VOLUME = 0.5

# Bot Settings
BOT_NAME = "MusicBot"
BOT_VERSION = "1.0.0"
BOT_DESCRIPTION = "A powerful Discord music bot with queue management and high-quality audio"

# Error Messages
ERROR_MESSAGES = {
    'not_in_voice': '❌ You need to be in a voice channel to use this command!',
    'bot_not_in_voice': '❌ I\'m not currently in a voice channel!',
    'different_voice_channel': '❌ You need to be in the same voice channel as me!',
    'no_permissions': '❌ I don\'t have permission to join or speak in that voice channel!',
    'no_song_playing': '❌ There\'s no song currently playing!',
    'queue_empty': '❌ The queue is empty!',
    'invalid_url': '❌ Invalid URL or search query!',
    'song_too_long': f'❌ Song is too long! Maximum length is {MAX_SONG_LENGTH // 60} minutes.',
    'queue_full': f'❌ Queue is full! Maximum {MAX_QUEUE_SIZE} songs allowed.',
    'invalid_volume': '❌ Volume must be between 0 and 100!',
    'no_results': '❌ No results found for your search!',
    'spotify_not_configured': '❌ Spotify API not configured. Please add SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET to your .env file.',
    'spotify_invalid_link': '❌ Invalid Spotify link!',
    'spotify_playlist_too_large': '❌ Playlist is too large! Maximum 20 songs can be added at once.',
    'spotify_album_too_large': '❌ Album is too large! Maximum 20 songs can be added at once.'
}
