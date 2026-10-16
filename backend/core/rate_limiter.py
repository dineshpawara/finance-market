"""
Rate Limiter Configuration
==========================
Protects authentication and critical API endpoints against brute-force
and volumetric denial-of-service attacks using SlowAPI.
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

# Global Limiter configured by client remote IP address
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["120/minute"],
    headers_enabled=False,
)
