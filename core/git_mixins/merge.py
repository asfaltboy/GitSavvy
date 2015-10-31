import os
import re
import subprocess

import sublime


class MergeMixin():
    def launch_after_tool_selected(self, tool_index=0, merge_tool=None):
        """
        Determine the absolute path and launch tool in subprocess.
        """
        if not merge_tool:
            if tool_index < 1:
                return
            merge_tool = self.tools[tool_index - 1]
        print("Tool selected: %s" % merge_tool)
        merge_path = os.path.join(self.repo_path, self._merge_fpath)
        startupinfo = None
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        p = subprocess.Popen(
            ["git", "mergetool", "--tool=%s" % merge_tool, merge_path],
            cwd=self.repo_path,
            env=os.environ,
            startupinfo=startupinfo
        )
        stdout, stderr = p.communicate(None)

    def launch_tool_for_file(self, fpath):
        """
        Given the relative path to a tracked file with a merge conflict,
        launch a merge tool.
        """
        self._merge_fpath = fpath
        self.get_merge_tool(self.launch_after_tool_selected)

    def get_merge_tool(self, callback):
        """
        Query Git for a configured or available merge tool.
        """
        tool = self.git("config", "merge.tool", throw_on_stderr=False).strip()
        if not tool:
            # parse mergetool --tool-help output
            help_text = self.git("mergetool", "--tool-help")
            # print(help_text, type(help_text))
            tools = re.match(r".*one of the following:(.*)The following tools.*",
                             help_text, flags=re.DOTALL).groups()
            if not tools:
                sublime.error_message("Git cannot locate any tools")
            else:
                self.tools = [t for t in tools[0].split() if t != 'user-defined:']
                print("Found tools: %s" % ' '.join(self.tools))

                # display menu to choose a tool
                window = self.window if hasattr(self, "window") else self.view.window()
                window.show_quick_panel(
                    ["Kindly select a tool to use"] + self.tools,
                    callback,
                    flags=sublime.MONOSPACE_FONT
                )
                return

        if not tool:
            sublime.error_message("You have not configured a merge tool for Git.")
            return
        return callback(tool=tool)
