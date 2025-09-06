import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import re
from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET, ERROR_MESSAGES

class SpotifyHandler:
    def __init__(self):
        self.sp = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Spotify client with credentials"""
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            try:
                client_credentials_manager = SpotifyClientCredentials(
                    client_id=SPOTIFY_CLIENT_ID,
                    client_secret=SPOTIFY_CLIENT_SECRET
                )
                self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
            except Exception as e:
                print(f"Error initializing Spotify client: {e}")
                self.sp = None
        else:
            self.sp = None
    
    def is_spotify_url(self, url):
        """Check if the URL is a Spotify URL"""
        spotify_patterns = [
            r'https://open\.spotify\.com/track/([a-zA-Z0-9]+)',
            r'https://open\.spotify\.com/album/([a-zA-Z0-9]+)',
            r'https://open\.spotify\.com/playlist/([a-zA-Z0-9]+)',
            r'spotify:track:([a-zA-Z0-9]+)',
            r'spotify:album:([a-zA-Z0-9]+)',
            r'spotify:playlist:([a-zA-Z0-9]+)'
        ]
        
        for pattern in spotify_patterns:
            if re.match(pattern, url):
                return True
        return False
    
    def extract_spotify_id(self, url):
        """Extract Spotify ID from URL"""
        patterns = {
            'track': r'(?:https://open\.spotify\.com/track/|spotify:track:)([a-zA-Z0-9]+)',
            'album': r'(?:https://open\.spotify\.com/album/|spotify:album:)([a-zA-Z0-9]+)',
            'playlist': r'(?:https://open\.spotify\.com/playlist/|spotify:playlist:)([a-zA-Z0-9]+)'
        }
        
        for type_name, pattern in patterns.items():
            match = re.search(pattern, url)
            if match:
                return type_name, match.group(1)
        
        return None, None
    
    def get_track_info(self, track_id):
        """Get track information from Spotify"""
        if not self.sp:
            return None
        
        try:
            track = self.sp.track(track_id)
            return {
                'title': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'external_urls': track['external_urls'],
                'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None
            }
        except Exception as e:
            print(f"Error getting track info: {e}")
            return None
    
    def get_album_tracks(self, album_id, limit=20):
        """Get tracks from an album"""
        if not self.sp:
            return None
        
        try:
            album = self.sp.album(album_id)
            tracks = self.sp.album_tracks(album_id, limit=limit)
            
            album_info = {
                'name': album['name'],
                'artist': ', '.join([artist['name'] for artist in album['artists']]),
                'total_tracks': album['total_tracks'],
                'tracks': []
            }
            
            for track in tracks['items']:
                track_info = {
                    'title': track['name'],
                    'artist': ', '.join([artist['name'] for artist in track['artists']]),
                    'duration_ms': track['duration_ms'],
                    'external_urls': track['external_urls']
                }
                album_info['tracks'].append(track_info)
            
            return album_info
        except Exception as e:
            print(f"Error getting album tracks: {e}")
            return None
    
    def get_playlist_tracks(self, playlist_id, limit=20):
        """Get tracks from a playlist"""
        if not self.sp:
            return None
        
        try:
            playlist = self.sp.playlist(playlist_id)
            tracks = self.sp.playlist_tracks(playlist_id, limit=limit)
            
            playlist_info = {
                'name': playlist['name'],
                'owner': playlist['owner']['display_name'],
                'total_tracks': playlist['tracks']['total'],
                'tracks': []
            }
            
            for item in tracks['items']:
                if item['track'] and item['track']['type'] == 'track':
                    track = item['track']
                    track_info = {
                        'title': track['name'],
                        'artist': ', '.join([artist['name'] for artist in track['artists']]),
                        'duration_ms': track['duration_ms'],
                        'external_urls': track['external_urls']
                    }
                    playlist_info['tracks'].append(track_info)
            
            return playlist_info
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return None
    
    def format_duration(self, duration_ms):
        """Format duration from milliseconds to MM:SS"""
        seconds = duration_ms // 1000
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}:{seconds:02d}"
    
    def create_search_query(self, track_info):
        """Create a search query for YouTube from Spotify track info"""
        if isinstance(track_info, dict):
            # Single track
            return f"{track_info['title']} {track_info['artist']}"
        else:
            # Multiple tracks
            queries = []
            for track in track_info:
                queries.append(f"{track['title']} {track['artist']}")
            return queries
    
    def is_configured(self):
        """Check if Spotify API is configured"""
        return self.sp is not None
