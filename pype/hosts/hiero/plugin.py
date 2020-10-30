import re
import os
import hiero
from Qt import QtWidgets, QtCore
from avalon.vendor import qargparse
import avalon.api as avalon
import pype.api as pype

from . import lib

log = pype.Logger().get_logger(__name__, "hiero")


def load_stylesheet():
    path = os.path.join(os.path.dirname(__file__), "style.css")
    if not os.path.exists(path):
        print("Unable to load stylesheet, file not found in resources")
        return ""

    with open(path, "r") as file_stream:
        stylesheet = file_stream.read()
    return stylesheet


class CreatorWidget(QtWidgets.QDialog):

    # output items
    items = dict()

    def __init__(self, name, info, ui_inputs, parent=None):
        super(CreatorWidget, self).__init__(parent)

        self.setObjectName(name)

        self.setWindowFlags(
            QtCore.Qt.Window
            | QtCore.Qt.CustomizeWindowHint
            | QtCore.Qt.WindowTitleHint
            | QtCore.Qt.WindowCloseButtonHint
            | QtCore.Qt.WindowStaysOnTopHint
        )
        self.setWindowTitle(name or "Pype Creator Input")
        self.resize(500, 700)

        # Where inputs and labels are set
        self.content_widget = [QtWidgets.QWidget(self)]
        top_layout = QtWidgets.QFormLayout(self.content_widget[0])
        top_layout.setObjectName("ContentLayout")
        top_layout.addWidget(Spacer(5, self))

        # first add widget tag line
        top_layout.addWidget(QtWidgets.QLabel(info))

        # main dynamic layout
        self.scroll_area = QtWidgets.QScrollArea(self, widgetResizable=True)
        self.scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAsNeeded)
        self.scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOn)
        self.scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarAlwaysOff)
        self.scroll_area.setWidgetResizable(True)

        self.content_widget.append(self.scroll_area)

        scroll_widget = QtWidgets.QWidget(self)
        in_scroll_area = QtWidgets.QVBoxLayout(scroll_widget)
        self.content_layout = [in_scroll_area]

        # add preset data into input widget layout
        self.items = self.populate_widgets(ui_inputs)
        self.scroll_area.setWidget(scroll_widget)

        # Confirmation buttons
        btns_widget = QtWidgets.QWidget(self)
        btns_layout = QtWidgets.QHBoxLayout(btns_widget)

        cancel_btn = QtWidgets.QPushButton("Cancel")
        btns_layout.addWidget(cancel_btn)

        ok_btn = QtWidgets.QPushButton("Ok")
        btns_layout.addWidget(ok_btn)

        # Main layout of the dialog
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(0)

        # adding content widget
        for w in self.content_widget:
            main_layout.addWidget(w)

        main_layout.addWidget(btns_widget)

        ok_btn.clicked.connect(self._on_ok_clicked)
        cancel_btn.clicked.connect(self._on_cancel_clicked)

        stylesheet = load_stylesheet()
        self.setStyleSheet(stylesheet)

    def _on_ok_clicked(self):
        self.result = self.value(self.items)
        self.close()

    def _on_cancel_clicked(self):
        self.result = None
        self.close()

    def value(self, data, new_data=None):
        new_data = new_data or dict()
        for k, v in data.items():
            new_data[k] = {
                "target": None,
                "value": None
            }
            if v["type"] == "dict":
                new_data[k]["target"] = v["target"]
                new_data[k]["value"] = self.value(v["value"])
            if v["type"] == "section":
                new_data.pop(k)
                new_data = self.value(v["value"], new_data)
            elif getattr(v["value"], "currentText", None):
                new_data[k]["target"] = v["target"]
                new_data[k]["value"] = v["value"].currentText()
            elif getattr(v["value"], "isChecked", None):
                new_data[k]["target"] = v["target"]
                new_data[k]["value"] = v["value"].isChecked()
            elif getattr(v["value"], "value", None):
                new_data[k]["target"] = v["target"]
                new_data[k]["value"] = v["value"].value()
            elif getattr(v["value"], "text", None):
                new_data[k]["target"] = v["target"]
                new_data[k]["value"] = v["value"].text()

        return new_data

    def camel_case_split(self, text):
        matches = re.finditer(
            '.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', text)
        return " ".join([str(m.group(0)).capitalize() for m in matches])

    def create_row(self, layout, type, text, **kwargs):
        # get type attribute from qwidgets
        attr = getattr(QtWidgets, type)

        # convert label text to normal capitalized text with spaces
        label_text = self.camel_case_split(text)

        # assign the new text to lable widget
        label = QtWidgets.QLabel(label_text)
        label.setObjectName("LineLabel")

        # create attribute name text strip of spaces
        attr_name = text.replace(" ", "")

        # create attribute and assign default values
        setattr(
            self,
            attr_name,
            attr(parent=self))

        # assign the created attribute to variable
        item = getattr(self, attr_name)
        for func, val in kwargs.items():
            if getattr(item, func):
                func_attr = getattr(item, func)
                func_attr(val)

        # add to layout
        layout.addRow(label, item)

        return item

    def populate_widgets(self, data, content_layout=None):
        """
        Populate widget from input dict.

        Each plugin has its own set of widget rows defined in dictionary
        each row values should have following keys: `type`, `target`,
        `label`, `order`, `value` and optionally also `toolTip`.

        Args:
            data (dict): widget rows or organized groups defined
                         by types `dict` or `section`
            content_layout (QtWidgets.QFormLayout)[optional]: used when nesting

        Returns:
            dict: redefined data dict updated with created widgets

        """

        content_layout = content_layout or self.content_layout[-1]
        # fix order of process by defined order value
        ordered_keys = data.keys()
        for k, v in data.items():
            try:
                # try removing a key from index which should
                # be filled with new
                ordered_keys.pop(v["order"])
            except IndexError:
                pass
            # add key into correct order
            ordered_keys.insert(v["order"], k)

        # process ordered
        for k in ordered_keys:
            v = data[k]
            tool_tip = v.get("toolTip", "")
            if v["type"] == "dict":
                # adding spacer between sections
                self.content_layout.append(QtWidgets.QWidget(self))
                content_layout.addWidget(self.content_layout[-1])
                self.content_layout[-1].setObjectName("sectionHeadline")

                headline = QtWidgets.QVBoxLayout(self.content_layout[-1])
                headline.addWidget(Spacer(20, self))
                headline.addWidget(QtWidgets.QLabel(v["label"]))

                # adding nested layout with label
                self.content_layout.append(QtWidgets.QWidget(self))
                self.content_layout[-1].setObjectName("sectionContent")

                nested_content_layout = QtWidgets.QFormLayout(
                    self.content_layout[-1])
                nested_content_layout.setObjectName("NestedContentLayout")
                content_layout.addWidget(self.content_layout[-1])

                # add nested key as label
                data[k]["value"] = self.populate_widgets(
                    v["value"], nested_content_layout)

            if v["type"] == "section":
                # adding spacer between sections
                self.content_layout.append(QtWidgets.QWidget(self))
                content_layout.addWidget(self.content_layout[-1])
                self.content_layout[-1].setObjectName("sectionHeadline")

                headline = QtWidgets.QVBoxLayout(self.content_layout[-1])
                headline.addWidget(Spacer(20, self))
                headline.addWidget(QtWidgets.QLabel(v["label"]))

                # adding nested layout with label
                self.content_layout.append(QtWidgets.QWidget(self))
                self.content_layout[-1].setObjectName("sectionContent")

                nested_content_layout = QtWidgets.QFormLayout(
                    self.content_layout[-1])
                nested_content_layout.setObjectName("NestedContentLayout")
                content_layout.addWidget(self.content_layout[-1])

                # add nested key as label
                data[k]["value"] = self.populate_widgets(
                    v["value"], nested_content_layout)

            elif v["type"] == "QLineEdit":
                data[k]["value"] = self.create_row(
                    content_layout, "QLineEdit", v["label"],
                    setText=v["value"], setToolTip=tool_tip)
            elif v["type"] == "QComboBox":
                data[k]["value"] = self.create_row(
                    content_layout, "QComboBox", v["label"],
                    addItems=v["value"], setToolTip=tool_tip)
            elif v["type"] == "QCheckBox":
                data[k]["value"] = self.create_row(
                    content_layout, "QCheckBox", v["label"],
                    setChecked=v["value"], setToolTip=tool_tip)
            elif v["type"] == "QSpinBox":
                data[k]["value"] = self.create_row(
                    content_layout, "QSpinBox", v["label"],
                    setValue=v["value"], setMaximum=10000, setToolTip=tool_tip)
        return data


class Spacer(QtWidgets.QWidget):
    def __init__(self, height, *args, **kwargs):
        super(self.__class__, self).__init__(*args, **kwargs)

        self.setFixedHeight(height)

        real_spacer = QtWidgets.QWidget(self)
        real_spacer.setObjectName("Spacer")
        real_spacer.setFixedHeight(height)

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(real_spacer)

        self.setLayout(layout)


def get_reference_node_parents(ref):
    """Return all parent reference nodes of reference node

    Args:
        ref (str): reference node.

    Returns:
        list: The upstream parent reference nodes.

    """
    parents = []
    return parents


class SequenceLoader(avalon.Loader):
    """A basic SequenceLoader for Resolve

    This will implement the basic behavior for a loader to inherit from that
    will containerize the reference and will implement the `remove` and
    `update` logic.

    """

    options = [
        qargparse.Boolean(
            "handles",
            label="Include handles",
            default=0,
            help="Load with handles or without?"
        ),
        qargparse.Choice(
            "load_to",
            label="Where to load clips",
            items=[
                "Current timeline",
                "New timeline"
            ],
            default="Current timeline",
            help="Where do you want clips to be loaded?"
        ),
        qargparse.Choice(
            "load_how",
            label="How to load clips",
            items=[
                "Original timing",
                "Sequentially in order"
            ],
            default="Original timing",
            help="Would you like to place it at orignal timing?"
        )
    ]

    def load(
        self,
        context,
        name=None,
        namespace=None,
        options=None
    ):
        pass

    def update(self, container, representation):
        """Update an existing `container`
        """
        pass

    def remove(self, container):
        """Remove an existing `container`
        """
        pass


class ClipLoader:

    active_bin = None
    data = dict()

    def __init__(self, cls, context, **options):
        """ Initialize object

        Arguments:
            cls (avalon.api.Loader): plugin object
            context (dict): loader plugin context
            options (dict)[optional]: possible keys:
                projectBinPath: "path/to/binItem"

        """
        self.__dict__.update(cls.__dict__)
        self.context = context
        self.active_project = lib.get_current_project()

        # try to get value from options or evaluate key value for `handles`
        self.with_handles = options.get("handles") or bool(
            options.get("handles") is True)
        # try to get value from options or evaluate key value for `load_how`
        self.sequencial_load = options.get("sequencially") or bool(
            "Sequentially in order" in options.get("load_how", ""))
        # try to get value from options or evaluate key value for `load_to`
        self.new_sequence = options.get("newSequence") or bool(
            "New timeline" in options.get("load_to", ""))

        assert self._populate_data(), str(
            "Cannot Load selected data, look into database "
            "or call your supervisor")

        # inject asset data to representation dict
        self._get_asset_data()
        log.debug("__init__ self.data: `{}`".format(self.data))

        # add active components to class
        if self.new_sequence:
            self.active_sequence = lib.get_current_sequence(new=True)
        else:
            self.active_sequence = lib.get_current_sequence()

        self.active_track = lib.get_current_track(
            self.active_sequence, self.data["track_name"])

    def _populate_data(self):
        """ Gets context and convert it to self.data
        data structure:
            {
                "name": "assetName_subsetName_representationName"
                "path": "path/to/file/created/by/get_repr..",
                "binPath": "projectBinPath",
            }
        """
        # create name
        repr = self.context["representation"]
        repr_cntx = repr["context"]
        asset = str(repr_cntx["asset"])
        subset = str(repr_cntx["subset"])
        representation = str(repr_cntx["representation"])
        self.data["clip_name"] = "_".join([asset, subset, representation])
        self.data["track_name"] = "_".join([subset, representation])

        # gets file path
        file = self.fname
        if not file:
            repr_id = repr["_id"]
            log.warning(
                "Representation id `{}` is failing to load".format(repr_id))
            return None
        self.data["path"] = file.replace("\\", "/")

        # convert to hashed path
        if repr_cntx.get("frame"):
            self._fix_path_hashes()

        # solve project bin structure path
        hierarchy = str("/".join((
            "Loader",
            repr_cntx["hierarchy"].replace("\\", "/"),
            asset
        )))

        self.data["binPath"] = hierarchy

        return True

    def _fix_path_hashes(self):
        """ Convert file path where it is needed padding with hashes
        """
        file = self.data["path"]
        if "#" not in file:
            frame = self.context["representation"]["context"].get("frame")
            padding = len(frame)
            file = file.replace(frame, "#" * padding)
        self.data["path"] = file

    def _get_asset_data(self):
        """ Get all available asset data

        joint `data` key with asset.data dict into the representaion

        """
        asset_name = self.context["representation"]["context"]["asset"]
        self.data["assetData"] = pype.get_asset(asset_name)["data"]

    def _make_track_item(self, source_bin_item, audio=False):
        """ Create track item with """

        clip = source_bin_item.activeItem()

        # add to track as clip item
        if not audio:
            track_item = hiero.core.TrackItem(
                self.data["clip_name"], hiero.core.TrackItem.kVideo)
        else:
            track_item = hiero.core.TrackItem(
                self.data["clip_name"], hiero.core.TrackItem.kAudio)

        track_item.setSource(clip)

        track_item.setSourceIn(self.handle_start)
        track_item.setTimelineIn(self.clip_in)

        track_item.setSourceOut(self.media_duration - self.handle_end)
        track_item.setTimelineOut(self.clip_out)
        track_item.setPlaybackSpeed(1)
        self.active_track.addTrackItem(track_item)

        return track_item

    def load(self):
        # create project bin for the media to be imported into
        self.active_bin = lib.create_bin(self.data["binPath"])

        # create mediaItem in active project bin
        # create clip media
        self.media = hiero.core.MediaSource(self.data["path"])
        self.media_duration = int(self.media.duration())

        self.handle_start = int(self.data["assetData"]["handleStart"])
        self.handle_end = int(self.data["assetData"]["handleEnd"])

        self.clip_in = int(self.data["assetData"]["clipIn"])
        self.clip_out = int(self.data["assetData"]["clipOut"])

        log.debug("__ media_duration: `{}`".format(self.media_duration))
        log.debug("__ handle_start: `{}`".format(self.handle_start))
        log.debug("__ handle_end: `{}`".format(self.handle_end))
        log.debug("__ clip_in: `{}`".format(self.clip_in))
        log.debug("__ clip_out: `{}`".format(self.clip_out))

        # check if slate is included
        # either in version data families or by calculating frame diff
        slate_on = next(
            (f for f in self.context["version"]["data"]["families"]
             if "slate" in f),
            # if nothing was found then use default None
            # so other bool could be used
            None) or bool(((
                self.clip_out - self.clip_in + 1) \
                + self.handle_start \
                + self.handle_end
            ) - self.media_duration)

        log.debug("__ slate_on: `{}`".format(slate_on))

        # calculate slate differences
        if slate_on:
            self.media_duration -= 1
            self.handle_start += 1

        # create Clip from Media
        clip = hiero.core.Clip(self.media)
        clip.setName(self.data["clip_name"])

        # add Clip to bin if not there yet
        if self.data["clip_name"] not in [
                b.name() for b in self.active_bin.items()]:
            bin_item = hiero.core.BinItem(clip)
            self.active_bin.addItem(bin_item)

        # just make sure the clip is created
        # there were some cases were hiero was not creating it
        source_bin_item = None
        for item in self.active_bin.items():
            if self.data["clip_name"] in item.name():
                source_bin_item = item
        if not source_bin_item:
            log.warning("Problem with created Source clip: `{}`".format(
                self.data["clip_name"]))

        # make track item from source in bin as item
        track_item = self._make_track_item(source_bin_item)

        log.info("Loading clips: `{}`".format(self.data["clip_name"]))
        return track_item


class Creator(avalon.Creator):
    """Creator class wrapper
    """
    clip_color = "Purple"
    rename_add = None
    rename_index = None

    def __init__(self, *args, **kwargs):
        from pype.hosts import hiero as phiero
        super(Creator, self).__init__(*args, **kwargs)
        self.presets = pype.config.get_presets(
        )['plugins']["hiero"]["create"].get(self.__class__.__name__, {})

        # adding basic current context resolve objects
        self.project = phiero.get_current_project()
        self.sequence = phiero.get_current_sequence()

        if (self.options or {}).get("useSelection"):
            self.selected = phiero.get_track_items(selected=True)
        else:
            self.selected = phiero.get_track_items()

        self.widget = CreatorWidget


class PublishClip:
    """
    Convert a track item to publishable instance

    Args:
        track_item (hiero.core.TrackItem): hiero track item object
        kwargs (optional): additional data needed for rename=True (presets)

    Returns:
        hiero.core.TrackItem: hiero track item object with pype tag
    """
    vertical_clip_match = dict()
    tag_data = dict()
    types = {
        "shot": "shot",
        "folder": "folder",
        "episode": "episode",
        "sequence": "sequence",
        "track": "sequence",
    }

    # parents search patern
    parents_search_patern = r"\{([a-z]*?)\}"

    # default templates for non-ui use
    rename_default = False
    hierarchy_default = "{_folder_}/{_sequence_}/{_track_}"
    clip_name_default = "shot_{_trackIndex_:0>3}_{_clipIndex_:0>4}"
    subset_name_default = "<track_name>"
    subset_family_default = "plate"
    count_from_default = 10
    count_steps_default = 10
    vertical_sync_default = False
    driving_layer_default = ""

    def __init__(self, cls, track_item, **kwargs):
        # populate input cls attribute onto self.[attr]
        self.__dict__.update(cls.__dict__)

        # get main parent objects
        self.track_item = track_item
        sequence_name = lib.get_current_sequence().name()
        self.sequence_name = str(sequence_name).replace(" ", "_")

        # track item (clip) main attributes
        self.ti_name = track_item.name()
        self.ti_index = int(track_item.eventNumber())

        # get track name and index
        track_name = track_item.parent().name()
        self.track_name = str(track_name).replace(" ", "_")
        self.track_index = int(track_item.parent().trackIndex())

        # adding tag.family into tag
        if kwargs.get("avalon"):
            self.tag_data.update(kwargs["avalon"])

        # adding ui inputs if any
        self.ui_inputs = kwargs.get("ui_inputs", {})

        # populate default data before we get other attributes
        self._populate_track_item_default_data()

        # use all populated default data to create all important attributes
        self._populate_attributes()

        # create parents with correct types
        self._create_parents()

    def convert(self):
        # solve track item data and add them to tag data
        self._convert_to_tag_data()

        # deal with clip name
        new_name = self.tag_data.pop("newClipName")

        if self.rename:
            # rename track item
            self.track_item.setName(new_name)
            self.tag_data["asset"] = new_name
        else:
            self.tag_data["asset"] = self.ti_name

        # create pype tag on track_item and add data
        lib.imprint(self.track_item, self.tag_data)

        return self.track_item

    def _populate_track_item_default_data(self):
        """ Populate default formating data from track item. """

        self.track_item_default_data = {
            "_folder_": "shots",
            "_sequence_": self.sequence_name,
            "_track_": self.track_name,
            "_clip_": self.ti_name,
            "_trackIndex_": self.track_index,
            "_clipIndex_": self.ti_index
        }

    def _populate_attributes(self):
        """ Populate main object attributes. """
        # track item frame range and parent track name for vertical sync check
        self.clip_in = int(self.track_item.timelineIn())
        self.clip_out = int(self.track_item.timelineOut())

        # define ui inputs if non gui mode was used
        self.shot_num = self.ti_index

        # ui_inputs data or default values if gui was not used
        self.rename = self.ui_inputs.get(
            "rename", {}).get("value") or self.rename_default
        self.clip_name = self.ui_inputs.get(
            "clipName", {}).get("value") or self.clip_name_default
        self.hierarchy = self.ui_inputs.get(
            "hierarchy", {}).get("value") or self.hierarchy_default
        self.hierarchy_data = self.ui_inputs.get(
            "hierarchyData", {}).get("value") or \
            self.track_item_default_data.copy()
        self.count_from = self.ui_inputs.get(
            "countFrom", {}).get("value") or self.count_from_default
        self.count_steps = self.ui_inputs.get(
            "countSteps", {}).get("value") or self.count_steps_default
        self.subset_name = self.ui_inputs.get(
            "subsetName", {}).get("value") or self.subset_name_default
        self.subset_family = self.ui_inputs.get(
            "subsetFamily", {}).get("value") or self.subset_family_default
        self.vertical_sync = self.ui_inputs.get(
            "vSyncOn", {}).get("value") or self.vertical_sync_default
        self.driving_layer = self.ui_inputs.get(
            "vSyncTrack", {}).get("value") or self.driving_layer_default

        # build subset name from layer name
        if self.subset_name == "<track_name>":
            self.subset_name = self.track_name

        # create subset for publishing
        self.subset = self.subset_family + self.subset_name.capitalize()

    def _replace_hash_to_expression(self, name, text):
        """ Replace hash with number in correct padding. """
        _spl = text.split("#")
        _len = (len(_spl) - 1)
        _repl = "{{{0}:0>{1}}}".format(name, _len)
        new_text = text.replace(("#" * _len), _repl)
        return new_text

    def _convert_to_tag_data(self):
        """ Convert internal data to tag data.

        Populating the tag data into internal variable self.tag_data
        """

        # define vertical sync attributes
        master_layer = True
        if self.vertical_sync:
            # check if track name is not in driving layer
            if self.track_name not in self.driving_layer:
                # if it is not then define vertical sync as None
                master_layer = False

        # driving layer is set as positive match
        hierarchy_formating_data = dict()
        _data = self.track_item_default_data.copy()
        if self.ui_inputs:
            # adding tag metadata from ui
            for _k, _v in self.ui_inputs.items():
                if _v["target"] == "tag":
                    self.tag_data[_k] = _v["value"]

            if master_layer and self.vertical_sync:
                # reset rename_add
                if self.rename_add < self.count_from:
                    self.rename_add = self.count_from

                # shot num calculate
                if self.rename_index == 0:
                    self.shot_num = self.rename_add
                else:
                    self.shot_num = self.rename_add + self.count_steps

            # clip name sequence number
            _data.update({"shot": self.shot_num})
            self.rename_add = self.shot_num

            # solve # in test to pythonic expression
            for _k, _v in self.hierarchy_data.items():
                if "#" not in _v["value"]:
                    continue
                self.hierarchy_data[
                    _k]["value"] = self._replace_hash_to_expression(
                        _k, _v["value"])

            # fill up pythonic expresisons in hierarchy data
            for k, _v in self.hierarchy_data.items():
                hierarchy_formating_data[k] = _v["value"].format(**_data)
        else:
            # if no gui mode then just pass default data
            hierarchy_formating_data = self.hierarchy_data

        tag_hierarchy_data = self._solve_tag_hierarchy_data(
            hierarchy_formating_data
        )

        if master_layer and self.vertical_sync:
            tag_hierarchy_data.update({"masterLayer": True})
            self.vertical_clip_match.update({
                (self.clip_in, self.clip_out): tag_hierarchy_data
            })

        if not master_layer and self.vertical_sync:
            # driving layer is set as negative match
            for (_in, _out), master_data in self.vertical_clip_match.items():
                master_data.update({"masterLayer": False})
                if _in == self.clip_in and _out == self.clip_out:
                    data_subset = master_data["subset"]
                    # add track index in case duplicity of names in master data
                    if self.subset in data_subset:
                        master_data["subset"] = self.subset + str(
                            self.track_index)
                    # in case track name and subset name is the same then add
                    if self.subset_name == self.track_name:
                        master_data["subset"] = self.subset
                    # assing data to return hierarchy data to tag
                    tag_hierarchy_data = master_data

        # add data to return data dict
        self.tag_data.update(tag_hierarchy_data)

    def _solve_tag_hierarchy_data(self, hierarchy_formating_data):
        """ Solve tag data from hierarchy data and templates. """
        # fill up clip name and hierarchy keys
        hierarchy_filled = self.hierarchy.format(**hierarchy_formating_data)
        clip_name_filled = self.clip_name.format(**hierarchy_formating_data)

        return {
            "newClipName": clip_name_filled,
            "hierarchy": hierarchy_filled,
            "parents": self.parents,
            "hierarchyData": hierarchy_formating_data,
            "subset": self.subset,
            "families": [self.subset_family]
        }

    def _convert_to_entity(self, key):
        """ Converting input key to key with type. """
        # convert to entity type
        entity_type = self.types.get(key, None)

        assert entity_type, "Missing entity type for `{}`".format(
            key
        )

        return {
            "entity_type": entity_type,
            "entity_name": self.hierarchy_data[key]["value"].format(
                **self.track_item_default_data
            )
        }

    def _create_parents(self):
        """ Create parents and return it in list. """
        self.parents = list()

        patern = re.compile(self.parents_search_patern)
        par_split = [patern.findall(t).pop()
                     for t in self.hierarchy.split("/")]

        for key in par_split:
            parent = self._convert_to_entity(key)
            self.parents.append(parent)
