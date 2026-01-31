import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your-secret-key")
    ALGORITHM: str = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", 7))
    GEMINI_API_KEY: str = os.getenv("GEMINI_KEY", "")
    
    # Support multiple Gemini API keys (comma-separated in environment variable)
    @property
    def GEMINI_API_KEYS(self) -> list[str]:
        """Get list of Gemini API keys from environment.
        
        Can be set as:
        - GEMINI_KEY_1, GEMINI_KEY_2, GEMINI_KEY_3, etc.
        - GEMINI_KEYS (comma-separated list)
        - GEMINI_KEY (single key, backward compatible)
        """
        keys = []
        
        # Check for GEMINI_KEY_1, GEMINI_KEY_2, etc.
        i = 1
        while True:
            key = os.getenv(f"GEMINI_KEY_{i}", "").strip()
            if not key:
                break
            keys.append(key)
            i += 1
        
        # If no numbered keys, check for comma-separated GEMINI_KEYS
        if not keys:
            keys_str = os.getenv("GEMINI_KEYS", "").strip()
            if keys_str:
                keys = [k.strip() for k in keys_str.split(",") if k.strip()]
        
        # Fallback to single GEMINI_KEY
        if not keys and self.GEMINI_API_KEY:
            keys = [self.GEMINI_API_KEY]
        
        return keys

settings = Settings()