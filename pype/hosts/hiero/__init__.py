import os
from pype.api import Logger
from avalon import api as avalon
from pyblish import api as pyblish
from pype import PLUGINS_DIR

from .workio import (
    open_file,
    save_file,
    current_file,
    has_unsaved_changes,
    file_extensions,
    work_root
)

from .menu import (
    install as menu_install,
    _update_menu_task_label
)

from .lib import (
    get_track_items,
    get_current_project,
    get_current_sequence,
    get_pype_track_item_tag,
    add_publish_attribute,
    set_publish_attribute,
    get_publish_attribute,
    imprint
)

from .events import register_hiero_events

__all__ = [
    # Workfiles API
    "open_file",
    "save_file",
    "current_file",
    "has_unsaved_changes",
    "file_extensions",
    "work_root",

    # Lib functions
    "get_track_items",
    "get_current_project",
    "get_current_sequence",
    "get_pype_track_item_tag",
    "add_publish_attribute",
    "set_publish_attribute",
    "get_publish_attribute",
    "imprint"
]

# get logger
log = Logger().get_logger(__name__, "hiero")


''' Creating all important host related variables '''
AVALON_CONFIG = os.getenv("AVALON_CONFIG", "pype")

# plugin root path
PUBLISH_PATH = os.path.join(PLUGINS_DIR, "hiero", "publish")
LOAD_PATH = os.path.join(PLUGINS_DIR, "hiero", "load")
CREATE_PATH = os.path.join(PLUGINS_DIR, "hiero", "create")
INVENTORY_PATH = os.path.join(PLUGINS_DIR, "hiero", "inventory")

# registering particular pyblish gui but `lite` is recomended!!
if os.getenv("PYBLISH_GUI", None):
    pyblish.register_gui(os.getenv("PYBLISH_GUI", None))


def install():
    """
    Installing Hiero integration for avalon

    Args:
        config (obj): avalon config module `pype` in our case, it is not
        used but required by avalon.api.install()

    """

    # adding all events
    _register_events()

    log.info("Registering Hiero plug-ins..")
    pyblish.register_host("hiero")
    pyblish.register_plugin_path(PUBLISH_PATH)
    avalon.register_plugin_path(avalon.Loader, LOAD_PATH)
    avalon.register_plugin_path(avalon.Creator, CREATE_PATH)
    avalon.register_plugin_path(avalon.InventoryAction, INVENTORY_PATH)

    # Disable all families except for the ones we explicitly want to see
    family_states = [
        "write",
        "review",
        "plate"
    ]

    avalon.data["familiesStateDefault"] = False
    avalon.data["familiesStateToggled"] = family_states

    # install menu
    menu_install()

    # register hiero events
    register_hiero_events()


def uninstall():
    """
    Uninstalling Hiero integration for avalon

    """
    log.info("Deregistering Hiero plug-ins..")
    pyblish.deregister_host("hiero")
    pyblish.deregister_plugin_path(PUBLISH_PATH)
    avalon.deregister_plugin_path(avalon.Loader, LOAD_PATH)
    avalon.deregister_plugin_path(avalon.Creator, CREATE_PATH)


def _register_events():
    """
    Adding all callbacks.
    """

    # if task changed then change notext of hiero
    avalon.on("taskChanged", _update_menu_task_label)
    log.info("Installed event callback for 'taskChanged'..")


def ls():
    """List available containers.

    This function is used by the Container Manager in Nuke. You'll
    need to implement a for-loop that then *yields* one Container at
    a time.

    See the `container.json` schema for details on how it should look,
    and the Maya equivalent, which is in `avalon.maya.pipeline`
    """
    # TODO: listing all availabe containers form sequence
    return
