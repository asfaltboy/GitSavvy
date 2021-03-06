import re
import sublime
from sublime_plugin import TextCommand

from ..git_command import GitCommand
from ...common import util


class GsRemoteAddCommand(TextCommand, GitCommand):
    """
    Add remotes
    """

    def run(self, edit):
        # Get remote name from user
        self.view.window().show_input_panel("Remote URL", "", self.on_select_remote, None, None)

    def on_select_remote(self, input_url):
        self.url = input_url
        owner = self.username_from_url(input_url)

        self.view.window().show_input_panel("Remote name", owner, self.on_select_name, None, None)

    def on_select_name(self, remote_name):
        self.git("remote", "add", remote_name, self.url)
        if sublime.ok_cancel_dialog("Your remote was added successfully.  Would you like to fetch from this remote?"):
            self.view.window().run_command("gs_fetch", {"remote": remote_name})


class GsRemoteRemoveCommand(TextCommand, GitCommand):
    """
    Remove remotes
    """

    def run(self, edit):
        self.remotes = list(self.get_remotes().keys())

        if not self.remotes:
            self.view.window().show_quick_panel(["There are no remotes available."], None)
        else:
            self.view.window().show_quick_panel(
                self.remotes,
                self.on_selection,
                flags=sublime.MONOSPACE_FONT,
                selected_index=0
                )

    def on_selection(self, remotes_index):
        if remotes_index == -1:
            return

        @util.actions.destructive(description="remove a remote")
        def remove():
            self.git("remote", "remove", remote)

        remote = self.remotes[remotes_index]
        remove()
