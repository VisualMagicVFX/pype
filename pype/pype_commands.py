# -*- coding: utf-8 -*-
"""Implementation of Pype commands."""
import os
import subprocess
import sys


class PypeCommands:
    """Class implementing commands used by Pype.

    Most of its methods are called by :mod:`cli` module.
    """
    @staticmethod
    def launch_tray(debug=False):
        from pype.lib import PypeLogger as Logger
        from pype.lib import execute
        if debug:
            execute([
                sys.executable,
                "-m",
                "pype.tools.tray"
            ])
            return

        detached_process = 0x00000008  # noqa: N806

        args = [sys.executable, "-m", "pype.tools.tray"]
        if sys.platform.startswith('linux'):
            subprocess.Popen(
                args,
                universal_newlines=True,
                bufsize=1,
                env=os.environ,
                stdout=None,
                stderr=None,
                preexec_fn=os.setpgrp
            )

        if sys.platform == 'win32':
            args = ["pythonw", "-m", "pype.tools.tray"]
            subprocess.Popen(
                args,
                universal_newlines=True,
                bufsize=1,
                cwd=None,
                env=os.environ,
                stdout=open(Logger.get_file_path(), 'w+'),
                stderr=subprocess.STDOUT,
                creationflags=detached_process
            )

    @staticmethod
    def launch_settings_gui(dev):
        from pype.lib import execute

        args = [sys.executable, "-m", "pype.tools.settings"]
        if dev:
            args.append("--develop")
        return_code = execute(args)
        return return_code

    def launch_eventservercli(self, args):
        pass

    def publish(self, gui, paths):
        pass

    def texture_copy(self, project, asset, path):
        pass

    def run_pype_tests(self, keyword, id):
        pass

    def make_docs(self):
        pass

    def pype_setup_coverage(self):
        pass

    def run_application(self, app, project, asset, task, tools, arguments):
        pass

    def validate_jsons(self):
        pass
