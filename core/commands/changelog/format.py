from collections import OrderedDict

CHANGELOG_TEMPLATE = {

    'default': """Changes since {ref}:
{changes}""",

    'rst': """Changes since {ref}
================

{changes}""",

}

GROUP_TEMPLATE = {

    'default': """
  {group}:
{messages}
""",

    'rst': """
{group}
-------

{messages}
"""

}


def get_message_groups(messages):
    """
    Create message groups from log entries.

    The returned message group is a dictionary of:

        {group name: messages, ...}

    """
    grouped_msgs = OrderedDict()

    for message in messages:
        first_colon = message.find(":")
        first_space = message.find(" ")

        # YES "fix: some summary info"
        # YES "feature: some summary info"
        #  NO "feature some summary info"
        #  NO " some summary info"
        if first_space > 0 and first_space == first_colon + 1:
            group = message[:first_colon]
            message = message[first_space + 1:]
        else:
            group = "Other"

        if group not in grouped_msgs:
            grouped_msgs[group] = []

        grouped_msgs[group].append(message)

    return grouped_msgs


def get_messages(entries, ancestor):
    for entry in entries:
        if entry.long_hash in ancestor:
            yield "{} (Merge {})".format(
                entry.summary,
                ancestor[entry.long_hash],
            )
        elif entry.raw_body.find('BREAKING:') >= 0:
            pos_start = entry.raw_body.find('BREAKING:')
            key_length = len('BREAKING:')
            indented_sub_msg = (
                '\n\t\t' + ' ' * key_length + ' '
            ).join(entry.raw_body[pos_start:].split('\n'))
            yield "{}\n\t\t{})".format(entry.summary, indented_sub_msg)
        else:
            yield entry.summary


def render_changelog(entries, ancestor, ref, format):
    messages = get_messages(entries, ancestor)
    msg_groups = get_message_groups(messages)
    contributors = set(entry.author for entry in entries)
    msg_groups["Contributors"] = set(contributors)

    # ref, msg_groups, format='default'
    group_strings = (
        GROUP_TEMPLATE[format].format(
            group=group_name,
            messages="\n".join("   - " + message for message in messages)
        )
        for group_name, messages in msg_groups.items()
    )

    changelog = CHANGELOG_TEMPLATE[format].format(
        ref=ref,
        changes="".join(group_strings)
    )
    return changelog
