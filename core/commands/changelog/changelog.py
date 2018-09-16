import sublime
from sublime_plugin import WindowCommand

from ...git_command import GitCommand
from ...ui_mixins.input_panel import show_single_line_input_panel
from .format import render_changelog

REF_PROMPT = "Ref or commit hash:"


class GsGenerateChangeLogCommand(WindowCommand, GitCommand):

    """
    Prompt the user for a ref or commit hash.  Once provided,
    compile all commit summaries between provided ref and HEAD
    and display in new scratch view.
    """

    def run(self):
        sublime.set_timeout_async(self.run_async, 0)

    def run_async(self):
        view = show_single_line_input_panel(
            REF_PROMPT, self.get_last_local_tag(), self.on_done, None, None)
        view.run_command("select_all")

    def on_done(self, ref):
        merge_entries = self.log(
            start_end=(ref, "HEAD"),
            first_parent=True,
            merges=True
        )

        ancestor = {}
        for merge in merge_entries:
            merge_commits = self.commits_of_merge(merge.long_hash)
            if len(merge_commits) > 1:
                for entry in merge_commits:
                    ancestor[entry] = merge.short_hash

        entries = self.log(
            start_end=(ref, "HEAD"),
            no_merges=True,
            topo_order=True,
            reverse=True
        )

        changelog = render_changelog(entries, ancestor, ref, format='rst')

        view = self.window.new_file()
        view.set_scratch(True)
        view.run_command("gs_replace_view_text", {
            "text": changelog,
            "nuke_cursors": True
        })
