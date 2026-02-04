class AuthenticationError(Exception):
    """Raised when a user is not authenticated or a token is invalid/expired."""
    def __init__(self, message: str = "Authentication failed"):
        self.message = message
        super().__init__(self.message)

class DeviceNotFoundException(Exception):
    """Raised when no active playback device is found."""
    def __init__(self, message: str = "No active device found"):
        self.message = message
        super().__init__(self.message)

class ExternalAPIError(Exception):
    """Raised when an external service (Spotify/SoundCloud) fails."""
    def __init__(
        self, 
        message: str = "External service error",
        error_code: int | str = None,
        platform: str = None,
        action: str = None
    ):
        self.message = message
        self.error_code = error_code
        self.platform = platform
        self.action = action
        super().__init__(self.message)
    
    def user_friendly_message(self) -> str:
        """
        Get a user-friendly error message suitable for TTS.
        
        Returns:
            Human-readable error message
        """
        from backend.utils.error_translator import get_user_friendly_error_message
        
        return get_user_friendly_error_message(
            error_code=self.error_code,
            platform=self.platform,
            action=self.action,
            original_message=self.message
        )
