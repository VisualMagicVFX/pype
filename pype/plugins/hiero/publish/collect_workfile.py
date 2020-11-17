import os
import pyblish.api
from pype.hosts import hiero as phiero
from avalon import api as avalon


class CollectWorkfile(pyblish.api.ContextPlugin):
    """Inject the current working file into context"""

    label = "Collect Workfile"
    order = pyblish.api.CollectorOrder - 0.501

    def process(self, context):
        asset = avalon.Session["AVALON_ASSET"]
        subset = "workfile"

        project = phiero.get_current_project()
        active_sequence = phiero.get_current_sequence()
        current_file = project.path()
        staging_dir = os.path.dirname(current_file)
        base_name = os.path.basename(current_file)

        # get workfile's colorspace properties
        _clrs = {}
        _clrs["useOCIOEnvironmentOverride"] =  project.useOCIOEnvironmentOverride()  # noqa
        _clrs["lutSetting16Bit"] = project.lutSetting16Bit()
        _clrs["lutSetting8Bit"] = project.lutSetting8Bit()
        _clrs["lutSettingFloat"] = project.lutSettingFloat()
        _clrs["lutSettingLog"] = project.lutSettingLog()
        _clrs["lutSettingViewer"] = project.lutSettingViewer()
        _clrs["lutSettingWorkingSpace"] = project.lutSettingWorkingSpace()
        _clrs["lutUseOCIOForExport"] = project.lutUseOCIOForExport()
        _clrs["ocioConfigName"] = project.ocioConfigName()
        _clrs["ocioConfigPath"] = project.ocioConfigPath()

        from pprint import pformat
        print pformat(_clrs)

        # set main project attributes to context
        context.data["activeProject"] = project
        context.data["activeSequence"] = active_sequence
        context.data["currentFile"] = current_file
        context.data["colorspace"] = _clrs

        self.log.info("currentFile: {}".format(current_file))

        # creating workfile representation
        representation = {
            'name': 'hrox',
            'ext': 'hrox',
            'files': base_name,
            "stagingDir": staging_dir,
        }

        instance_data = {
            "name": "{}_{}".format(asset, subset),
            "asset": asset,
            "subset": "{}{}".format(asset, subset.capitalize()),
            "item": project,
            "family": "workfile",

            # version data
            "versionData": {
                "colorspace": _clrs
            },

            # source attribute
            "sourcePath": current_file,
            "representations": [representation]
        }

        instance = context.create_instance(**instance_data)
        self.log.info("Creating instance: {}".format(instance))
