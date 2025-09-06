import discord
from discord.ext import commands
import asyncio
import yt_dlp
import os
import re
from config import *
from spotify_handler import SpotifyHandler

# Suppress noise about console usage from errors
yt_dlp.utils.bug_reports_message = lambda: ''

class MusicBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.voice_states = True
        
        super().__init__(
            command_prefix=DISCORD_PREFIX,
            intents=intents,
            description=BOT_DESCRIPTION
        )
        
        self.queues = {}  # Guild ID -> List of songs
        self.current_song = {}  # Guild ID -> Current song info
        self.voice_clients = {}  # Guild ID -> Voice client
        self.spotify_handler = SpotifyHandler()  # Spotify API handler
        
    async def on_ready(self):
        print(f'🎵 {BOT_NAME} v{BOT_VERSION} is online!')
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')
        
        # Set bot status
        activity = discord.Activity(type=discord.ActivityType.listening, name="music | !help")
        await self.change_presence(activity=activity)

    def get_ytdl_options(self):
        return {
            'format': 'bestaudio/best',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0',
            'extract_flat': False,
        }

    def get_ffmpeg_options(self):
        return {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

    async def join_voice_channel(self, ctx):
        """Join the user's voice channel"""
        if not ctx.author.voice:
            await ctx.send(ERROR_MESSAGES['not_in_voice'])
            return False
            
        channel = ctx.author.voice.channel
        
        if ctx.voice_client is None:
            try:
                await channel.connect()
            except discord.Forbidden:
                await ctx.send(ERROR_MESSAGES['no_permissions'])
                return False
        elif ctx.voice_client.channel != channel:
            await ctx.send(ERROR_MESSAGES['different_voice_channel'])
            return False
            
        return True

    async def play_next_song(self, ctx):
        """Play the next song in the queue"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            return
            
        song_info = self.queues[guild_id].pop(0)
        self.current_song[guild_id] = song_info
        
        try:
            with yt_dlp.YoutubeDL(self.get_ytdl_options()) as ydl:
                info = ydl.extract_info(song_info['url'], download=False)
                url = info['formats'][0]['url']
                
            source = discord.FFmpegPCMAudio(url, **self.get_ffmpeg_options())
            ctx.voice_client.play(source, after=lambda e: asyncio.run_coroutine_threadsafe(
                self.play_next_song(ctx), self.loop
            ))
            
            embed = discord.Embed(
                title="🎵 Now Playing",
                description=f"**{song_info['title']}**\nDuration: {song_info['duration']}",
                color=0x00ff00
            )
            embed.set_thumbnail(url=song_info['thumbnail'])
            embed.add_field(name="Requested by", value=song_info['requester'], inline=True)
            embed.add_field(name="Queue", value=f"{len(self.queues[guild_id])} songs", inline=True)
            
            await ctx.send(embed=embed)
            
        except Exception as e:
            print(f"Error playing song: {e}")
            await ctx.send("❌ Error playing the song. Skipping to next...")
            await self.play_next_song(ctx)

    @commands.command(name='join', aliases=['j'])
    async def join(self, ctx):
        """Join the voice channel"""
        if await self.join_voice_channel(ctx):
            await ctx.send(f"✅ Joined {ctx.author.voice.channel.name}")

    @commands.command(name='leave', aliases=['disconnect', 'dc'])
    async def leave(self, ctx):
        """Leave the voice channel"""
        if ctx.voice_client:
            await ctx.voice_client.disconnect()
            await ctx.send("👋 Left the voice channel")
            
            # Clear queue and current song
            guild_id = ctx.guild.id
            if guild_id in self.queues:
                del self.queues[guild_id]
            if guild_id in self.current_song:
                del self.current_song[guild_id]
        else:
            await ctx.send(ERROR_MESSAGES['bot_not_in_voice'])

    async def handle_spotify_url(self, ctx, url, search_msg):
        """Handle Spotify URLs"""
        if not self.spotify_handler.is_configured():
            await search_msg.edit(content=ERROR_MESSAGES['spotify_not_configured'])
            return
        
        if not self.spotify_handler.is_spotify_url(url):
            await search_msg.edit(content=ERROR_MESSAGES['spotify_invalid_link'])
            return
        
        url_type, spotify_id = self.spotify_handler.extract_spotify_id(url)
        if not url_type or not spotify_id:
            await search_msg.edit(content=ERROR_MESSAGES['spotify_invalid_link'])
            return
        
        guild_id = ctx.guild.id
        
        try:
            if url_type == 'track':
                # Single track
                track_info = self.spotify_handler.get_track_info(spotify_id)
                if not track_info:
                    await search_msg.edit(content=ERROR_MESSAGES['no_results'])
                    return
                
                search_query = self.spotify_handler.create_search_query(track_info)
                await search_msg.edit(content=f"🎵 Found on Spotify: **{track_info['title']}** by {track_info['artist']}\n🔍 Searching on YouTube...")
                
                # Search on YouTube
                await self.search_and_play_youtube(ctx, search_query, search_msg, track_info)
                
            elif url_type == 'album':
                # Album
                album_info = self.spotify_handler.get_album_tracks(spotify_id, limit=20)
                if not album_info or not album_info['tracks']:
                    await search_msg.edit(content=ERROR_MESSAGES['no_results'])
                    return
                
                if len(album_info['tracks']) > 20:
                    await search_msg.edit(content=ERROR_MESSAGES['spotify_album_too_large'])
                    return
                
                await search_msg.edit(content=f"🎵 Found album: **{album_info['name']}** by {album_info['artist']}\n🔍 Adding {len(album_info['tracks'])} songs to queue...")
                
                # Add all tracks to queue
                added_count = 0
                for track in album_info['tracks']:
                    if len(self.queues[guild_id]) >= MAX_QUEUE_SIZE:
                        break
                    
                    search_query = f"{track['title']} {track['artist']}"
                    success = await self.search_and_add_to_queue(ctx, search_query, track)
                    if success:
                        added_count += 1
                
                await search_msg.edit(content=f"✅ Added {added_count} songs from album **{album_info['name']}** to queue!")
                
            elif url_type == 'playlist':
                # Playlist
                playlist_info = self.spotify_handler.get_playlist_tracks(spotify_id, limit=20)
                if not playlist_info or not playlist_info['tracks']:
                    await search_msg.edit(content=ERROR_MESSAGES['no_results'])
                    return
                
                if len(playlist_info['tracks']) > 20:
                    await search_msg.edit(content=ERROR_MESSAGES['spotify_playlist_too_large'])
                    return
                
                await search_msg.edit(content=f"🎵 Found playlist: **{playlist_info['name']}** by {playlist_info['owner']}\n🔍 Adding {len(playlist_info['tracks'])} songs to queue...")
                
                # Add all tracks to queue
                added_count = 0
                for track in playlist_info['tracks']:
                    if len(self.queues[guild_id]) >= MAX_QUEUE_SIZE:
                        break
                    
                    search_query = f"{track['title']} {track['artist']}"
                    success = await self.search_and_add_to_queue(ctx, search_query, track)
                    if success:
                        added_count += 1
                
                await search_msg.edit(content=f"✅ Added {added_count} songs from playlist **{playlist_info['name']}** to queue!")
                
        except Exception as e:
            print(f"Error handling Spotify URL: {e}")
            await search_msg.edit(content=ERROR_MESSAGES['invalid_url'])
    
    async def search_and_play_youtube(self, ctx, search_query, search_msg, spotify_info=None):
        """Search and play from YouTube"""
        try:
            with yt_dlp.YoutubeDL(self.get_ytdl_options()) as ydl:
                info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                if not info['entries']:
                    await search_msg.edit(content=ERROR_MESSAGES['no_results'])
                    return
                info = info['entries'][0]
                
                # Check song length
                duration = info.get('duration', 0)
                if duration > MAX_SONG_LENGTH:
                    await search_msg.edit(content=ERROR_MESSAGES['song_too_long'])
                    return
                
                # Format duration
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}" if duration else "Unknown"
                
                song_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('webpage_url', search_query),
                    'duration': duration_str,
                    'thumbnail': info.get('thumbnail', ''),
                    'requester': ctx.author.mention,
                    'spotify_info': spotify_info
                }
                
                guild_id = ctx.guild.id
                self.queues[guild_id].append(song_info)
                
                # If nothing is playing, start playing
                if not ctx.voice_client.is_playing():
                    await search_msg.edit(content="✅ Song added to queue!")
                    await self.play_next_song(ctx)
                else:
                    embed = discord.Embed(
                        title="✅ Added to Queue",
                        description=f"**{song_info['title']}**\nDuration: {song_info['duration']}",
                        color=0x00ff00
                    )
                    if spotify_info and spotify_info.get('album_art'):
                        embed.set_thumbnail(url=spotify_info['album_art'])
                    elif song_info['thumbnail']:
                        embed.set_thumbnail(url=song_info['thumbnail'])
                    
                    embed.add_field(name="Position in queue", value=len(self.queues[guild_id]), inline=True)
                    embed.add_field(name="Requested by", value=song_info['requester'], inline=True)
                    
                    if spotify_info:
                        embed.add_field(name="From Spotify", value=f"🎵 {spotify_info['title']} by {spotify_info['artist']}", inline=False)
                    
                    await search_msg.edit(content="", embed=embed)
                    
        except Exception as e:
            print(f"Error searching YouTube: {e}")
            await search_msg.edit(content=ERROR_MESSAGES['invalid_url'])
    
    async def search_and_add_to_queue(self, ctx, search_query, spotify_info=None):
        """Search and add to queue without playing"""
        try:
            with yt_dlp.YoutubeDL(self.get_ytdl_options()) as ydl:
                info = ydl.extract_info(f"ytsearch:{search_query}", download=False)
                if not info['entries']:
                    return False
                info = info['entries'][0]
                
                # Check song length
                duration = info.get('duration', 0)
                if duration > MAX_SONG_LENGTH:
                    return False
                
                # Format duration
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}" if duration else "Unknown"
                
                song_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('webpage_url', search_query),
                    'duration': duration_str,
                    'thumbnail': info.get('thumbnail', ''),
                    'requester': ctx.author.mention,
                    'spotify_info': spotify_info
                }
                
                guild_id = ctx.guild.id
                self.queues[guild_id].append(song_info)
                return True
                
        except Exception as e:
            print(f"Error adding to queue: {e}")
            return False

    @commands.command(name='play', aliases=['p'])
    async def play(self, ctx, *, query):
        """Play a song from YouTube or Spotify"""
        if not await self.join_voice_channel(ctx):
            return
            
        guild_id = ctx.guild.id
        if guild_id not in self.queues:
            self.queues[guild_id] = []
            
        if len(self.queues[guild_id]) >= MAX_QUEUE_SIZE:
            await ctx.send(ERROR_MESSAGES['queue_full'])
            return
            
        # Show searching message
        search_msg = await ctx.send("🔍 Searching for your song...")
        
        # Check if it's a Spotify URL
        if self.spotify_handler.is_spotify_url(query):
            await self.handle_spotify_url(ctx, query, search_msg)
            return
        
        # Handle regular YouTube search or URL
        try:
            with yt_dlp.YoutubeDL(self.get_ytdl_options()) as ydl:
                # Check if it's a URL or search query
                if query.startswith(('http://', 'https://')):
                    info = ydl.extract_info(query, download=False)
                else:
                    info = ydl.extract_info(f"ytsearch:{query}", download=False)
                    if not info['entries']:
                        await search_msg.edit(content=ERROR_MESSAGES['no_results'])
                        return
                    info = info['entries'][0]
                
                # Check song length
                duration = info.get('duration', 0)
                if duration > MAX_SONG_LENGTH:
                    await search_msg.edit(content=ERROR_MESSAGES['song_too_long'])
                    return
                
                # Format duration
                minutes, seconds = divmod(duration, 60)
                duration_str = f"{minutes}:{seconds:02d}" if duration else "Unknown"
                
                song_info = {
                    'title': info.get('title', 'Unknown Title'),
                    'url': info.get('webpage_url', query),
                    'duration': duration_str,
                    'thumbnail': info.get('thumbnail', ''),
                    'requester': ctx.author.mention
                }
                
                self.queues[guild_id].append(song_info)
                
                # If nothing is playing, start playing
                if not ctx.voice_client.is_playing():
                    await search_msg.edit(content="✅ Song added to queue!")
                    await self.play_next_song(ctx)
                else:
                    embed = discord.Embed(
                        title="✅ Added to Queue",
                        description=f"**{song_info['title']}**\nDuration: {song_info['duration']}",
                        color=0x00ff00
                    )
                    embed.set_thumbnail(url=song_info['thumbnail'])
                    embed.add_field(name="Position in queue", value=len(self.queues[guild_id]), inline=True)
                    embed.add_field(name="Requested by", value=song_info['requester'], inline=True)
                    
                    await search_msg.edit(content="", embed=embed)
                    
        except Exception as e:
            print(f"Error in play command: {e}")
            await search_msg.edit(content=ERROR_MESSAGES['invalid_url'])

    @commands.command(name='pause')
    async def pause(self, ctx):
        """Pause the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.pause()
            await ctx.send("⏸️ Paused")
        else:
            await ctx.send(ERROR_MESSAGES['no_song_playing'])

    @commands.command(name='resume')
    async def resume(self, ctx):
        """Resume the paused song"""
        if ctx.voice_client and ctx.voice_client.is_paused():
            ctx.voice_client.resume()
            await ctx.send("▶️ Resumed")
        else:
            await ctx.send("❌ Nothing is paused!")

    @commands.command(name='skip', aliases=['s'])
    async def skip(self, ctx):
        """Skip the current song"""
        if ctx.voice_client and ctx.voice_client.is_playing():
            ctx.voice_client.stop()
            await ctx.send("⏭️ Skipped")
        else:
            await ctx.send(ERROR_MESSAGES['no_song_playing'])

    @commands.command(name='stop')
    async def stop(self, ctx):
        """Stop the music and clear the queue"""
        if ctx.voice_client:
            ctx.voice_client.stop()
            guild_id = ctx.guild.id
            if guild_id in self.queues:
                self.queues[guild_id] = []
            if guild_id in self.current_song:
                del self.current_song[guild_id]
            await ctx.send("⏹️ Stopped and cleared queue")
        else:
            await ctx.send(ERROR_MESSAGES['no_song_playing'])

    @commands.command(name='queue', aliases=['q'])
    async def queue(self, ctx):
        """Show the current queue"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or not self.queues[guild_id]:
            await ctx.send(ERROR_MESSAGES['queue_empty'])
            return
            
        embed = discord.Embed(title="🎵 Music Queue", color=0x00ff00)
        
        # Show current song
        if guild_id in self.current_song:
            current = self.current_song[guild_id]
            embed.add_field(
                name="🎵 Now Playing",
                value=f"**{current['title']}**\nDuration: {current['duration']}",
                inline=False
            )
        
        # Show next 10 songs in queue
        queue_text = ""
        for i, song in enumerate(self.queues[guild_id][:10], 1):
            queue_text += f"{i}. **{song['title']}** ({song['duration']})\n"
        
        if queue_text:
            embed.add_field(name="📋 Up Next", value=queue_text, inline=False)
        
        if len(self.queues[guild_id]) > 10:
            embed.set_footer(text=f"... and {len(self.queues[guild_id]) - 10} more songs")
        
        await ctx.send(embed=embed)

    @commands.command(name='volume', aliases=['vol'])
    async def volume(self, ctx, volume: int = None):
        """Set the volume (0-100)"""
        if volume is None:
            if ctx.voice_client and ctx.voice_client.source:
                current_volume = int(ctx.voice_client.source.volume * 100)
                await ctx.send(f"🔊 Current volume: {current_volume}%")
            else:
                await ctx.send("❌ No audio source found")
            return
            
        if not 0 <= volume <= 100:
            await ctx.send(ERROR_MESSAGES['invalid_volume'])
            return
            
        if ctx.voice_client and ctx.voice_client.source:
            ctx.voice_client.source.volume = volume / 100
            await ctx.send(f"🔊 Volume set to {volume}%")
        else:
            await ctx.send(ERROR_MESSAGES['no_song_playing'])

    @commands.command(name='nowplaying', aliases=['np'])
    async def nowplaying(self, ctx):
        """Show the currently playing song"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.current_song:
            await ctx.send(ERROR_MESSAGES['no_song_playing'])
            return
            
        song = self.current_song[guild_id]
        embed = discord.Embed(
            title="🎵 Now Playing",
            description=f"**{song['title']}**\nDuration: {song['duration']}",
            color=0x00ff00
        )
        embed.set_thumbnail(url=song['thumbnail'])
        embed.add_field(name="Requested by", value=song['requester'], inline=True)
        
        if guild_id in self.queues:
            embed.add_field(name="Queue", value=f"{len(self.queues[guild_id])} songs", inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name='shuffle')
    async def shuffle(self, ctx):
        """Shuffle the queue"""
        guild_id = ctx.guild.id
        
        if guild_id not in self.queues or len(self.queues[guild_id]) < 2:
            await ctx.send("❌ Need at least 2 songs in queue to shuffle!")
            return
            
        import random
        random.shuffle(self.queues[guild_id])
        await ctx.send("🔀 Queue shuffled!")

    @commands.command(name='clear')
    async def clear(self, ctx):
        """Clear the queue"""
        guild_id = ctx.guild.id
        
        if guild_id in self.queues:
            self.queues[guild_id] = []
            await ctx.send("🗑️ Queue cleared!")
        else:
            await ctx.send(ERROR_MESSAGES['queue_empty'])

    @commands.command(name='help')
    async def help_command(self, ctx):
        """Show all available commands"""
        embed = discord.Embed(
            title=f"🎵 {BOT_NAME} Commands",
            description="Here are all the available commands:",
            color=0x00ff00
        )
        
        commands_list = [
            ("🎵 Music Commands", [
                f"`{DISCORD_PREFIX}play <song/url>` - Play a song from YouTube or Spotify",
                f"`{DISCORD_PREFIX}pause` - Pause the current song",
                f"`{DISCORD_PREFIX}resume` - Resume the paused song",
                f"`{DISCORD_PREFIX}skip` - Skip the current song",
                f"`{DISCORD_PREFIX}stop` - Stop music and clear queue",
                f"`{DISCORD_PREFIX}nowplaying` - Show current song info"
            ]),
            ("📋 Queue Commands", [
                f"`{DISCORD_PREFIX}queue` - Show the current queue",
                f"`{DISCORD_PREFIX}shuffle` - Shuffle the queue",
                f"`{DISCORD_PREFIX}clear` - Clear the queue"
            ]),
            ("🔊 Audio Commands", [
                f"`{DISCORD_PREFIX}volume <0-100>` - Set volume",
                f"`{DISCORD_PREFIX}join` - Join your voice channel",
                f"`{DISCORD_PREFIX}leave` - Leave voice channel"
            ])
        ]
        
        for category, cmds in commands_list:
            embed.add_field(
                name=category,
                value="\n".join(cmds),
                inline=False
            )
        
        embed.set_footer(text=f"{BOT_NAME} v{BOT_VERSION} | Made with ❤️")
        await ctx.send(embed=embed)

    # Error handling
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"❌ Missing required argument: {error.param}")
        elif isinstance(error, commands.BadArgument):
            await ctx.send("❌ Invalid argument provided!")
        else:
            print(f"Error: {error}")
            await ctx.send("❌ An unexpected error occurred!")

def main():
    if not DISCORD_TOKEN:
        print("❌ Error: DISCORD_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        return
        
    bot = MusicBot()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
