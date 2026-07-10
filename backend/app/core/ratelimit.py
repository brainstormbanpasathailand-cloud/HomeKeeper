"""Rate limiting for sensitive endpoints (auth, OTP) using slowapi."""
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.config import settings

limiter = Limiter(key_func=get_remote_address, default_limits=[])

AUTH_LIMIT = settings.RATE_LIMIT_AUTH
