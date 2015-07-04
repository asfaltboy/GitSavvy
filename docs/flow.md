# git-flow

The excellent [git-flow][https://github.com/nvie/gitflow] extension is fully supported, allowing to run flow commands with sublime commands.

Most commands attempt to mirror `git-flow` 's interface with the added ability to select a target from local branches/remotes.

## `git flow: init`

A required step when you wish to setup a project to use `git-flow`. This will present a series of prompts to configure `git-flow` very much like the interactive shell command does.

## `git flow: feature/release/hotfix/support start`

When running this command, you will prompted first for the feature/release/hotfix/support name (without the prefix), and then the branch will be created and checked out.

## `git flow: feature/release/hotfix/support finish`

When running this command when an existing feature/release/hotfix/support branch is checked out, you will asked to confirm finish. Otherwise, you will be asked to select the relevant branch. This flow merges the changes from this branch into the "develop" branch (without fast-forwarding, unless branch has only a single commit).

## `git flow: feature/release/hotfix publish`

When running this command when an existing feature/release/hotfix branch is checked out, you will asked to confirm publish. Otherwise, you will be asked to select the relevant branch. This flow pushes the target branch to the configured remote.

## `git flow: feature pull`

This will pull the feature from given remote. You will be first prompted to select a remote and then to provide a feature name.
