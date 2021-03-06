from collections import namedtuple


LogEntry = namedtuple("LogEntry", (
    "short_hash",
    "long_hash",
    "summary",
    "raw_body",
    "author",
    "email",
    "datetime"
    ))


class HistoryMixin():

    def log(self, author=None, branch=None, file_path=None, start_end=None,
            cherry=None, limit=6000, skip=None, reverse=False,
            msg_regexp=None, diff_regexp=None):

        log_output = self.git(
            "log",
            "-{}".format(limit) if limit else None,
            "--skip={}".format(skip) if skip else None,
            "--reverse" if reverse else None,
            '--format=%h%n%H%n%s%n%an%n%ae%n%at%x00%B%x00%x00%n',
            "--author={}".format(author) if author else None,
            "--grep={}".format(msg_regexp) if msg_regexp else None,
            "--cherry" if cherry else None,
            "--G" if diff_regexp else None,
            diff_regexp if diff_regexp else None,
            "--" if file_path else None,
            file_path if file_path else None,
            "{}..{}".format(*start_end) if start_end else None,
            branch if branch else None
        ).strip("\x00")

        entries = []
        for entry in log_output.split("\x00\x00\n"):
            entry = entry.strip()
            if not entry:
                continue
            entry, raw_body = entry.split("\x00")

            short_hash, long_hash, summary, author, email, datetime = entry.split("\n")
            entries.append(LogEntry(short_hash, long_hash, summary, raw_body, author, email, datetime))

        return entries
