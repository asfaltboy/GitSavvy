import sublime
from sublime_plugin import WindowCommand

from ..git_command import GitCommand


INIT_REQUIRED_MSG = "Please run `git: flow init` first"

GITFLOW_CONF = ['branch.master', 'branch.develop', 'prefix.feature',
                'prefix.release', 'prefix.hotfix', 'prefix.versiontag',
                'prefix.support', 'origin', ]


class GsFlowCommon(WindowCommand, GitCommand):
    def get_flow_settings(self):
        flow_ver = self.git("flow", "version")
        self.flow_settings = {
            'flow.version': flow_ver,
        }
        for conf in GITFLOW_CONF:
            self.flow_settings[conf] = self.git(
                "config", "gitflow.%s" % conf, throw_on_stderr=False
            ).strip()

    def run(self, **kwargs):
        self.get_flow_settings()
        if not self.flow_settings['branch.master']:
            self.window.show_quick_panel([INIT_REQUIRED_MSG], None)

    def _generic_select(self, help_text, options, callback,
                        no_opts="There are no branches available"):
        if not options:
            self.window.show_quick_panel([no_opts], None)
        else:
            self.window.show_quick_panel(
                [help_text] + options,
                callback,
                flags=sublime.MONOSPACE_FONT
            )

    def get_value(self, options, index):
        # If the user pressed `esc` or otherwise cancelled.
        if index == -1 or index == 0:
            return None
        selected = options[index - 1]  # skipping help query
        if selected.startswith('* '):
            selected = selected[2:]
        return selected

    def get_local_branches(self):
        branches = self.get_branches()
        return [b.name for b in branches if not b.remote]


class GsGitFlowInitCommand(GsFlowCommon):
    """
    Through a series of panels, allow the user to initialize git-flow.
    """

    def configure_gitflow(self, conf, value):
        self.git("config", "gitflow.%s" % conf, value)

        if conf.startswith('branch'):
            # remove this branch from branches available to next command
            self.branches = [b for b in self.branches if b != value]

    def run(self, reinit=False, **kwargs):
        self.get_flow_settings()
        if self.flow_settings['branch.master'] and not reinit:
            def confirm_reinit(index):
                if index == 1:  # Yes
                    return self.run(reinit=True)
            self._generic_select('Git flow is already initialized, re-init?',
                                 ['Yes', 'No'], confirm_reinit)
            return

        self.remotes = list(self.get_remotes().keys())
        self._generic_select('Remote to use as origin in git flow?',
                             self.remotes, self.on_origin_selected,
                             no_opts="There are no remotes available.")

    def on_origin_selected(self, index):
        value = self.get_value(self.remotes, index)
        if not value:
            return
        self.configure_gitflow('origin', value)

        self.branches = self.get_local_branches()

        self._generic_select('Branch for production releases (master)',
                             self.branches, self.on_master_selected)

    def on_master_selected(self, index):
        value = self.get_value(self.branches, index)
        if not value:
            return
        self.configure_gitflow('branch.master', value)

        if not self.branches:
            self._generic_select('No branches found, create branch "develop"?',
                                 ['Yes', 'No'], self.create_develop_branch)
        self._generic_select('Branch for "next release" development',
                             self.branches, self.on_develop_selected)

    def create_develop_branch(self, index):
        if index == 1:
            self.git('branch', 'develop')
            self.branches = self.get_local_branches()
            self.on_develop_selected(1)

    def on_develop_selected(self, index):
        value = self.get_value(self.branches, index)
        if not value:
            return

        # TODO: create develop branch if does not exist yet
        self.configure_gitflow('branch.develop', value)

        self.window.show_input_panel("Feature branches prefix?: ", "feature/",
                                     self.on_feature_selected, None, None)

    def on_feature_selected(self, value):
        self.configure_gitflow('prefix.feature', value)

        self.window.show_input_panel("Release branches prefix?: ", "release/",
                                     self.on_release_selectes, None, None)

    def on_release_selectes(self, value):
        self.configure_gitflow('prefix.release', value)
        self.window.show_input_panel("Hotfix branches prefix?: ", "hotfix/",
                                     self.on_hotfix_selected, None, None)

    def on_hotfix_selected(self, value):
        self.configure_gitflow('prefix.hotfix', value)
        self.window.show_input_panel("Support branches prefix?: ", "support/",
                                     self.on_support_selected, None, None)

    def on_support_selected(self, value):
        self.configure_gitflow('prefix.support', value)
        self.window.show_input_panel("Version tag prefix?: ", " ",
                                     self.on_versiontag_selected, None, None)

    def on_versiontag_selected(self, tag):
        self.configure_gitflow('prefix.versiontag', tag)
        sublime.status_message("git flow initialized")


class CompleteMixin(object):
    def complete_flow(self, name=None):
        self.git("flow", self.flow, self.command, name)
        self.show_status_update()

    def show_status_update(self):
        sublime.status_message("%s %sed, checked out %s" %
                               (self.flow.capitalize(), self.command,
                                self.get_current_branch_name()))


class GenericStartMixin(CompleteMixin):
    command = 'start'

    def run(self, **kwargs):
        super(GenericStartMixin, self).run(**kwargs)
        self.prefix = self.flow_settings[self.prefix_setting]
        self.window.show_input_panel(self.query, "", self.complete_flow,
                                     None, None)


class GenericSelectTargetBranch(object):
    def run(self, name=None, **kwargs):
        super(GenericSelectTargetBranch, self).run(**kwargs)
        self.prefix = self.flow_settings[self.prefix_setting]
        self.curbranch = self.get_current_branch_name()

        if name is None:
            if self.curbranch.startswith(self.prefix):
                name = self.curbranch.replace(self.prefix, '')
            else:
                self.branches = [b.replace(self.prefix, '')
                                 for b in self.get_local_branches()
                                 if b.startswith(self.prefix)]
                self._generic_select(
                    self.name_prompt,
                    self.branches,
                    self.on_name_selected,
                )

        self._generic_select(self.query % name, ['Yes', 'No'],
                             self.on_select_current)

    def on_select_current(self, index):
        if index != 1:
            return None
        return self.complete_flow()

    def on_name_selected(self, index):
        value = self.get_value(self.branches, index)
        if not value:
            return
        return self.complete_flow(name=value)


class GenericFinishMixin(CompleteMixin, GenericSelectTargetBranch):
    command = 'finish'


class GenericPublishMixin(CompleteMixin, GenericSelectTargetBranch):
    command = 'publish'

    def show_status_update(self):
        sublime.status_message("%s %sed" % (self.flow.capitalize(),
                                            self.command))


class GenericTrackCommand(CompleteMixin, GsFlowCommon):
    command = 'track'

    def run(self, name=None, **kwargs):
        super(GenericTrackCommand, self).run(**kwargs)
        if name:
            self.complete_flow(name)
        self.window.show_input_panel(self.query, "", self.complete_flow,
                                     None, None)


class GsGitFlowFeatureStartCommand(GenericStartMixin, GsFlowCommon):
    prefix_setting = 'prefix.feature'
    query = "Feature name?: "
    flow = "feature"


class GsGitFlowFeatureFinishCommand(GenericFinishMixin, GsFlowCommon):
    prefix_setting = 'prefix.feature'
    query = 'Finish feature: %s?'
    name_prompt = 'Finish which feature?'
    flow = "feature"


class GsGitFlowFeaturePublishCommand(GenericPublishMixin, GsFlowCommon):
    prefix_setting = 'prefix.feature'
    query = 'Publish feature: %s?'
    name_prompt = 'Publish which feature?'
    flow = "feature"


class GsGitFlowFeatureTrackCommand(GenericTrackCommand, GsFlowCommon):
    query = 'Track which feature?:'
    flow = "feature"


class GsGitFlowFeaturePullCommand(CompleteMixin, GsFlowCommon):
    prefix_setting = 'prefix.feature'
    query = 'Pull which feature?:'
    flow = "feature"
    command = 'pull'

    def run(self, name=None, **kwargs):
        super(GsGitFlowFeaturePullCommand, self).run(**kwargs)
        self.remotes = list(self.get_remotes().keys())
        self._generic_select('Remote to pull feature from?',
                             self.remotes, self.on_remote_selected,
                             no_opts="There are no remotes available.")

    def on_remote_selected(self, index):
        value = self.get_value(self.remotes, index)
        if not value:
            return
        self.remote = value
        self.window.show_input_panel(self.query, "", self.complete_flow,
                                     None, None)

    def complete_flow(self, name=None):
        self.git("flow", self.flow, "pull", self.remote, name)
        self.show_status_update()


class GsGitFlowReleaseStartCommand(GenericStartMixin, GsFlowCommon):
    prefix_setting = 'prefix.release'
    query = "Release version?: "
    flow = "release"


class GsGitFlowReleaseFinishCommand(GenericFinishMixin, GsFlowCommon):
    prefix_setting = 'prefix.release'
    query = 'Finish release: %s?'
    name_prompt = 'Finish which release?'
    flow = "release"


class GsGitFlowReleasePublishCommand(GenericPublishMixin, GsFlowCommon):
    prefix_setting = 'prefix.release'
    query = 'Publish release: %s?'
    name_prompt = 'Publish which release?'
    flow = "release"


class GsGitFlowReleaseTrackCommand(GenericTrackCommand, GsFlowCommon):
    query = 'Track which release?:'
    flow = "release"


class GsGitFlowHotfixStartCommand(GenericStartMixin, GsFlowCommon):
    prefix_setting = 'prefix.hotfix'
    query = "Hotfix name?: "
    flow = "hotfix"


class GsGitFlowHotfixFinishCommand(GenericFinishMixin, GsFlowCommon):
    prefix_setting = 'prefix.hotfix'
    query = 'Finish hotfix: %s?'
    name_prompt = 'Finish which hotfix?'
    flow = "hotfix"


class GsGitFlowHotfixPublishCommand(GenericPublishMixin, GsFlowCommon):
    prefix_setting = 'prefix.hotfix'
    query = 'Publish hotfix: %s?'
    name_prompt = 'Publish which hotfix?'
    flow = "hotfix"


class GsGitFlowSupportStartCommand(GenericStartMixin, GsFlowCommon):
    prefix_setting = 'prefix.support'
    query = "Support name?: "
    flow = "support"
