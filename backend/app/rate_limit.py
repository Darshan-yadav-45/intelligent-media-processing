"""
Shared slowapi Limiter instance, keyed by client IP.
Wired into the FastAPI app in main.py.
"""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
