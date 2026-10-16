"""
Controller package initialization
"""

from .news_controller import NewsController, news_controller
from .auth_controller import AuthController
from .master_key_controller import MasterKeyController

__all__ = ["NewsController", "news_controller", "AuthController", "MasterKeyController"]
