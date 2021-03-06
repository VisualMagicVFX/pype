import os

from . import ftrack_server
from .ftrack_server import FtrackServer, check_ftrack_url
from .lib import BaseHandler, BaseEvent, BaseAction, ServerAction

from pype.api import get_system_settings

# TODO: set in ftrack module
os.environ["FTRACK_SERVER"] = (
    get_system_settings()["modules"]["Ftrack"]["ftrack_server"]
)
__all__ = (
    "ftrack_server",
    "FtrackServer",
    "check_ftrack_url",
    "BaseHandler",
    "BaseEvent",
    "BaseAction",
    "ServerAction"
)
