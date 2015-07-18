import os
from itertools import groupby

import sublime
from sublime_plugin import WindowCommand, TextCommand

from ..commands.flow import FlowCommon
from ..interfaces.branch import BranchInterface
from ..git_command import GitCommand
from ...common import ui
from ...common import util


class GsShowFlowCommand(WindowCommand, GitCommand):

    """
    Open the Flow dashboard for the active Git repository.
    """

    def run(self):
        FlowInterface(repo_path=self.repo_path)


class FlowInterface(BranchInterface, FlowCommon):

    """
    Flow dashboard.
    """

    interface_type = "flow"
    read_only = True
    syntax_file = "Packages/GitSavvy/syntax/flow.tmLanguage"
    word_wrap = False

    template = """\

      BRANCH:  {branch_status}
      ROOT:    {git_root}
      HEAD:    {head}

    {features}{releases}{hotfixes}{supports}
      #############
      ## ACTIONS ##
      #############

      [c] checkout                                  [i] init
      [s,f] start new feature                       [s,s] start new support
      [s,r] start new release                       [s,h] start new hotfix
      [f] finish feature/release/support/hotfix

      [p] publish feature/release/hotfix            [u] pull feature
      [t] track feature/release

      [r] refresh

    -
    """

    template_flow = """
      {flow}:
    {flow_list}"""

    def title(self):
        return "GIT-FLOW: {}".format(os.path.basename(self.repo_path))

    def pre_render(self):
        self.get_flow_settings()
        self._branches = filter(lambda b: not b.remote, self.get_branches())

    def _generic_flow_render(self, flow):
        prefix = self.flow_settings['prefix.%s' % flow]
        branches = [b for b in self._branches if b.startswith(prefix)]
        if not branches:
            return "\n"
        flow_list = self.render_branch_list(branches)
        return self.template_flow.format(
            flow=flow.uppercase(), flow_list=flow_list)

    @ui.partial("features")
    def render_features(self):
        return self._generic_flow_render("feature")

# ui.register_listeners(FlowInterface)
