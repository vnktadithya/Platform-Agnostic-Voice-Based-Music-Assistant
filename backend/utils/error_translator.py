"""
Error Translation Module

Translates technical API errors into user-friendly messages suitable for TTS output.
Maps HTTP status codes and error types to natural, conversational responses.
"""
import logging

logger = logging.getLogger(__name__)


# User-friendly error messages mapped by HTTP status code and action context
ERROR_MESSAGES = {
    # 401 - Unauthorized (token expired, invalid credentials)
    401: {
        "default": "It looks like your {platform} connection has expired. Please reconnect your account.",
        "play_song": "I can't play that right now because your {platform} session expired. Please reconnect your account.",
        "add_to_playlist": "I can't modify playlists because your {platform} session expired. Please reconnect your account.",
    },
    
    # 403 - Forbidden (permission denied, premium required, collaborative playlist)
    403: {
        "default": "I don't have permission to do that on {platform}. Please check your account settings.",
        "add_to_playlist": "I don't have permission to modify that playlist. Please check if you have edit access.",
        "delete_playlist": "I can't delete that playlist. You might not be the owner, or it might be protected.",
        "play_song": "I can't play that content. This might require {platform} Premium or special permissions.",
        "play_playlist_by_name": "I don't have access to that playlist. It might be private or require special permissions.",
        "set_volume": "I can't control the volume. This feature might require {platform} Premium.",
    },
    
    # 404 - Not Found (resource doesn't exist)
    404: {
        "default": "I couldn't find that on {platform}. Could you try with a different name?",
        "play_song": "I couldn't find that song. Could you try with a different name or artist?",
        "play_playlist_by_name": "I couldn't find a playlist with that name. Could you check the name and try again?",
        "add_to_playlist": "I couldn't find that playlist or song. Please check the names and try again.",
        "delete_playlist": "I couldn't find a playlist with that name in your library.",
    },
    
    # 429 - Too Many Requests (rate limiting)
    429: {
        "default": "I'm making too many requests to {platform} right now. Please wait a moment and try again.",
        "play_song": "I'm sending requests too quickly. Let me take a quick break, then you can try again.",
    },
    
    # 500, 502, 503 - Server Errors
    500: {
        "default": "{platform} is having some technical difficulties right now. Please try again in a moment.",
    },
    502: {
        "default": "{platform} seems to be having connection issues. Please try again shortly.",
    },
    503: {
        "default": "{platform} is temporarily unavailable. Please try again in a few moments.",
    },
    
    # Network/Connection Errors
    "network": {
        "default": "I'm having trouble connecting to {platform}. Please check your internet connection.",
    },
    
    # Device Errors (Spotify-specific)
    "no_device": {
        "default": "I can't find an active {platform} device. Please open {platform} on your phone, computer, or speaker and start playing something.",
    },
}


def get_user_friendly_error_message(
    error_code: int | str,
    platform: str = "Spotify",
    action: str = None,
    original_message: str = None
) -> str:
    """
    Translate a technical error code into a user-friendly message.
    
    Args:
        error_code: HTTP status code (int) or error type (str like 'network', 'no_device')
        platform: Platform name (e.g., 'Spotify', 'SoundCloud')
        action: The action that failed (e.g., 'play_song', 'add_to_playlist')
        original_message: The original error message (for logging/fallback)
    
    Returns:
        User-friendly error message suitable for TTS
    """
    try:
        # Format platform name nicely
        platform_display = platform.capitalize() if platform else "the music service"
        
        # Get the error messages for this code
        messages = ERROR_MESSAGES.get(error_code, {})
        
        if not messages:
            # Unknown error code - use generic fallback
            logger.warning(f"Unknown error code: {error_code}. Using generic message.")
            return f"I encountered an issue with {platform_display}. Please try again."
        
        # Try to get action-specific message first, then fall back to default
        if action and action in messages:
            message = messages[action]
        else:
            message = messages.get("default", f"I encountered an issue with {platform_display}. Please try again.")
        
        # Format with platform name
        return message.format(platform=platform_display)
    
    except Exception as e:
        logger.error(f"Error translating error message: {e}", exc_info=True)
        # Ultimate fallback
        return "I encountered an unexpected issue. Please try again."


def extract_spotify_error_code(exception) -> int | None:
    """
    Extract HTTP status code from a SpotifyException.
    
    Args:
        exception: SpotifyException instance
    
    Returns:
        HTTP status code or None if not found
    """
    try:
        # SpotifyException has an http_status attribute
        if hasattr(exception, 'http_status'):
            return exception.http_status
        
        # Fallback: try to parse from the string representation
        error_str = str(exception)
        if 'http status:' in error_str.lower():
            # Extract number after "http status:"
            parts = error_str.lower().split('http status:')
            if len(parts) > 1:
                status_part = parts[1].strip().split(',')[0].strip()
                return int(status_part)
    
    except Exception as e:
        logger.warning(f"Could not extract error code from exception: {e}")
    
    return None
