import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
from typing import Optional, Dict, Any

class SpotifyController:
    def __init__(self, client_id: str, client_secret: str, redirect_uri: str):
        """
        Initialize Spotify controller with your app credentials.
        
        Args:
            client_id: Your Spotify app's client ID
            client_secret: Your Spotify app's client secret
            redirect_uri: Your app's redirect URI (e.g., 'http://localhost:8888/callback')
        """
        # Define the required scopes
        self.scope = "user-read-playback-state user-modify-playback-state user-read-currently-playing"
        
        # Initialize the Spotify client
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=self.scope
        ))
        
        # Cache for rate limiting
        self._last_api_call = 0
        self.MIN_API_CALL_INTERVAL = 1  # minimum seconds between API calls
        self._last_track_id = None
        self._last_track_progress = None
        self._last_playing_state = None
        
    def _rate_limit(self) -> None:
        """Implement basic rate limiting for API calls"""
        now = time.time()
        time_since_last_call = now - self._last_api_call
        if time_since_last_call < self.MIN_API_CALL_INTERVAL:
            time.sleep(self.MIN_API_CALL_INTERVAL - time_since_last_call)
        self._last_api_call = time.time()

    def get_current_track(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently playing track.
        
        Returns:
            Dict containing track information or None if no track is playing:
            {
                'name': track name,
                'artist': artist name,
                'album': album name,
                'album_art': URL to album art,
                'duration': track duration in ms,
                'progress': current playback progress in ms,
                'is_playing': boolean indicating if track is playing
            }
        """
        self._rate_limit()
        try:
            current = self.sp.current_playback()
            if current and current.get('item'):
                track = current['item']
                return {
                    'name': track['name'],
                    'artist': track['artists'][0]['name'],
                    'album': track['album']['name'],
                    'album_art': track['album']['images'][0]['url'] if track['album']['images'] else None,
                    'duration': track['duration_ms'],
                    'progress': current['progress_ms'],
                    'is_playing': current['is_playing']
                }
            return None
        except Exception as e:
            print(f"Error getting current track: {str(e)}")
            return None

    def toggle_playback(self,_) -> bool:
        """
        Toggle between play and pause states.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        self._rate_limit()
        try:
            current = self.sp.current_playback()
            if not current:
                return False
                
            if current['is_playing']:
                self.sp.pause_playback()
            else:
                self.sp.start_playback()
            return True
        except Exception as e:
            print(f"Error toggling playback: {str(e)}")
            return False

    def next_track(self) -> bool:
        """
        Skip to the next track in the playlist/queue.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        self._rate_limit()
        try:
            self.sp.next_track()
            return True
        except Exception as e:
            print(f"Error skipping to next track: {str(e)}")
            return False

    def previous_track(self) -> bool:
        """
        Go back to the previous track in the playlist/queue.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        self._rate_limit()
        try:
            self.sp.previous_track()
            return True
        except Exception as e:
            print(f"Error going to previous track: {str(e)}")
            return False

    def toggle_shuffle(self) -> Optional[bool]:
        """
        Toggle shuffle mode on/off.
        
        Returns:
            Optional[bool]: New shuffle state if successful, None if operation failed
        """
        self._rate_limit()
        try:
            current = self.sp.current_playback()
            if not current:
                return None
                
            new_state = not current['shuffle_state']
            self.sp.shuffle(new_state)
            return new_state
        except Exception as e:
            print(f"Error toggling shuffle: {str(e)}")
            return None

    def get_album_art_url(self) -> Optional[str]:
        """
        Get the URL of the current track's album art.
        
        Returns:
            Optional[str]: URL of the album art or None if not available
        """
        track_info = self.get_current_track()
        return track_info['album_art'] if track_info else None
    def check_track_change(self) -> dict:
        """
        Check if the track has changed or ended.
        Returns dict with change events:
        {
            'track_changed': bool,
            'track_ended': bool,
            'playing_state_changed': bool,
            'current_track': dict or None
        }
        """
        current = self.get_current_track()
        result = {
            'track_changed': False,
            'track_ended': False,
            'playing_state_changed': False,
            'current_track': current
        }
        
        if not current:
            if self._last_track_id:
                result['track_ended'] = True
                self._last_track_id = None
                self._last_track_progress = None
                self._last_playing_state = None
            return result
            
        current_id = f"{current['artist']}:{current['name']}"
        current_state = current['is_playing']
        
        # Detect track change
        if self._last_track_id and current_id != self._last_track_id:
            result['track_changed'] = True
            
        # Detect playing state change
        if self._last_playing_state is not None and current_state != self._last_playing_state:
            result['playing_state_changed'] = True
            
        # Detect track ending (progress reset)
        if (self._last_track_progress and current['progress'] and 
            self._last_track_progress > current['progress'] and 
            self._last_track_id == current_id):
            result['track_ended'] = True
            
        # Update last known states
        self._last_track_id = current_id
        self._last_track_progress = current['progress']
        self._last_playing_state = current_state
        
        return result
    
    def change_volume(self, increase: bool) -> bool:
        """
        Increase or decrease the playback volume by 10%.
        
        Args:
            increase: If True, increase volume by 10%. If False, decrease volume by 10%.
        
        Returns:
            bool: True if operation was successful, False otherwise
        """
        self._rate_limit()
        try:
            # Get the current playback state
            current = self.sp.current_playback()
            if not current:
                print("No active playback found.")
                return False

            # Get current volume level
            current_volume = current.get('device', {}).get('volume_percent', 50)
            
            # Adjust volume
            new_volume = current_volume + 10 if increase else current_volume - 10
            
            # Clamp volume to 0-100 range
            new_volume = max(0, min(100, new_volume))
            
            # Set new volume
            self.sp.volume(new_volume)
            return True
        except Exception as e:
            print(f"Error changing volume: {str(e)}")
            return False
