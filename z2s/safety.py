# -*- coding: utf-8 -*-
"""The never-do rules: no secret in an artefact, no destructive operation unattended.

Everything else in this toolchain is about what a document must SAY. This file is
about what a run must never DO, which is why it is not part of the schema: a
prohibited operation is not a property of any document.

Two rules live here, and they are the same rule family — the things that are
prohibited outright rather than merely checked.

  * **No secret value in any artefact** (FR-GEN-04, NFR-SEC-01). A credential may
    appear as a NAME and never as a value. Checked over raw text rather than over
    an embedded specification, because the requirement names documents, plans,
    prompts, ledgers and commit messages, and only the first of those has a
    specification in it — and because a report a person can act on says which
    file and which line, which an extracted object cannot (M6-05).

  * **No destructive operation unattended** (FR-EXE-12, NFR-SEC-04). The
    prohibited operations are a tuple of records, and `prohibited()` is the one
    routine that judges a command against them. The execution layer calls that
    routine rather than restating the rules, so adding a fifth prohibition is a
    data edit that the guard covers the moment it lands (M6-08).

What a secret is, exactly (M6-06). Two families, because neither is enough alone:

  * a value with a **known credential shape** — a provider's key, a private key
    block, a signed web token, a password inside a web address. Unambiguous
    wherever it appears, and it needs no context at all;
  * a **setting whose name says secret, handed a quoted literal**. This is what
    makes "secrets shall appear only as variable names" checkable: `TOKEN` on its
    own is a name, `TOKEN = "…"` is a value. Placeholders and values too short to
    be a credential are let through, because a rule that flags
    `token: "<your-token>"` teaches an author to switch it off.

Deliberately NOT here: a randomness measure. It catches the most and also flags
every checksum, identifier and embedded image in the set, and each false alarm
costs more trust than the one homemade password it finds.

Two ceilings worth stating rather than discovering. The name-and-value rule reads
QUOTED values only, so an unquoted configuration line (`password: hunter2`) is
caught only if its value has a known shape. And a command is split on shell
separators and whitespace rather than parsed, so a path hidden inside a variable
is not seen; the guard is a gate on the obvious, not a sandbox.

Nothing here ever prints the value it found. A report that quotes the secret has
copied it into a log, a terminal and whatever collects them.

Traces: FR-GEN-04, FR-EXE-12, NFR-SEC-01, NFR-SEC-04.
"""

import collections
import os
import re
import sys

from z2s import schema

USAGE = ("usage: python3 -m z2s.safety <file> [file ...]\n"
         "       git log -1 --pretty=%B | python3 -m z2s.safety -")

#: How a caller asks for standard input, so a commit message can be piped in
#: without being written to disk first.
STDIN = "-"


# ------------------------------------------------------------------- secrets

#: One recognisable credential shape. `title` is what a person is told; the
#: pattern is never shown to them.
Shape = collections.namedtuple("Shape", "id title pattern")

#: The shapes a value can have that make it a credential wherever it appears.
#: Provider prefixes rather than general randomness: a prefix is a fact about the
#: value, and a fact does not have false alarms.
#:
#: The private-key expression is written with its middle as a group so that this
#: file does not itself contain the literal header it is looking for. A scanner
#: that trips over its own source is a scanner people exclude.
SHAPES = (
    Shape("github-token", "a GitHub access token",
          re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}")),
    Shape("openai-key", "an OpenAI-style API key",
          re.compile(r"\bsk-(?:proj-|ant-)?[A-Za-z0-9_-]{24,}")),
    Shape("aws-access-key", "an AWS access key identifier",
          re.compile(r"\b(?:AKIA|ASIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA)[0-9A-Z]{16}\b")),
    Shape("google-api-key", "a Google API key",
          re.compile(r"\bAIza[0-9A-Za-z_-]{35}\b")),
    Shape("slack-token", "a Slack token",
          re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    Shape("private-key", "a private key block",
          re.compile(r"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----")),
    Shape("web-token", "a signed web token",
          re.compile(r"\beyJ[A-Za-z0-9_-]{8,}\.eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}")),
    Shape("url-credentials", "a password inside a web address",
          re.compile(r"\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@")),
)

#: Words that make a setting's name a secret on their own.
SECRET_WORDS = ("password", "passwd", "passphrase", "secret", "token",
                "credential", "credentials", "apikey")

#: Words that make the word "key" mean a credential rather than a sort order.
#: "key" alone is one of the commonest field names there is, and flagging it
#: would flag half of every data model in the method.
KEY_QUALIFIERS = ("api", "access", "private", "secret", "signing", "encryption",
                  "auth", "session")

#: Below this, a value is too short to be a credential anyone would use. Set so
#: that a real-but-weak password is still caught: "hunter2" is seven characters.
MINIMUM = 6

#: What a value says when it is standing in for a secret rather than being one.
#: Substrings, because "your-api-token-here" and "REPLACE_WITH_YOUR_TOKEN" are
#: the same intention written twice.
PLACEHOLDERS = ("your", "example", "changeme", "change-me", "change_me",
                "placeholder", "replace", "redacted", "dummy", "fake", "sample",
                "todo", "none", "null", "env", "environ", "getenv", "secret_name")

#: A setting being given a quoted literal. The optional quote after the name is
#: what makes this read JSON (`"api_key": "…"`) as well as a shell or Python
#: assignment; the back-reference makes the value end on the quote it opened on.
ASSIGNMENT = re.compile(r"""([A-Za-z_][A-Za-z0-9_.\-]{0,60})["']?\s*[:=]\s*(["'])(.*?)\2""")

#: A name split into the words it is made of, however it was joined:
#: GITHUB_TOKEN, apiKey and api-key all become the same two words.
_WORDS = re.compile(r"[A-Z]+(?![a-z])|[A-Za-z][a-z0-9]*")


def words_of(name):
    """The words a setting's name is made of, lower-cased."""
    return [word.lower() for word in _WORDS.findall(name or "")]


def names_a_secret(name):
    """Whether a setting's name says the thing it holds is a credential."""
    words = words_of(name)
    if any(word in SECRET_WORDS for word in words):
        return True
    return any(words[index] in KEY_QUALIFIERS and words[index + 1] == "key"
               for index in range(len(words) - 1))


def is_placeholder(value):
    """Whether a quoted value is standing in for a secret rather than being one."""
    if not isinstance(value, str):
        return True
    stripped = value.strip()
    if len(stripped) < MINIMUM:
        return True
    if stripped[0] in "<{[$" or stripped[-1] in ">}]":
        return True
    if set(stripped) <= set("x*.-_ "):
        return True
    low = stripped.lower()
    return any(word in low for word in PLACEHOLDERS)


def secrets_in(text, source="<text>"):
    """Every credential-shaped literal in this text, by file and line.

    Reports the rule that fired and how long the value was, never the value.
    One finding per shape per line: a line holding the same token twice is one
    mistake, and a line holding two different tokens is two.
    """
    found = []
    for number, line in enumerate((text or "").splitlines(), 1):
        where = "%s:%d" % (source, number)
        for shape in SHAPES:
            match = shape.pattern.search(line)
            if match is None:
                continue
            found.append(schema.Finding(
                schema.FAILURE, "secret-literal", where,
                "%s: this line holds %s (%d characters); a secret belongs in the "
                "environment and may appear in an artefact only as a name"
                % (where, shape.title, len(match.group(0)))))
        for match in ASSIGNMENT.finditer(line):
            name, value = match.group(1), match.group(3)
            if any(shape.pattern.search(value) for shape in SHAPES):
                continue        # already reported by its shape; one mistake, one finding
            if names_a_secret(name) and not is_placeholder(value):
                found.append(schema.Finding(
                    schema.FAILURE, "secret-literal", where,
                    "%s: %s is given a literal %d-character value; a secret "
                    "belongs in the environment and may appear in an artefact "
                    "only as a name" % (where, name, len(value))))
    return found


def scan(sources, stdin=None):
    """Every named artefact, scanned. An ordered map of source to findings.

    A source of "-" reads standard input, which is how a commit message is
    checked before it becomes a commit.
    """
    grouped = collections.OrderedDict()
    for source in sources:
        grouped[source] = []
        if source == STDIN:
            grouped[source].extend(
                secrets_in((sys.stdin if stdin is None else stdin).read(), "commit"))
            continue
        try:
            with open(source, encoding="utf-8", errors="replace") as handle:
                text = handle.read()
        except OSError as error:
            grouped[source].append(schema.Finding(
                schema.FAILURE, "unreadable", source, "%s: %s" % (source, error)))
            continue
        grouped[source].extend(secrets_in(text, source))
    return grouped


# --------------------------------------------------------- banned operations

#: One thing an unattended run may never do. `matches` takes the command and the
#: working area the run owns, and answers whether this command would do it.
Operation = collections.namedtuple("Operation", "id title why matches")

#: Where one shell statement ends and the next begins. Splitting first means a
#: pattern cannot match a verb in one statement and its flag in the next.
_SEPARATORS = re.compile(r"(?:\|\||&&|[;&|\n])")

#: The commands that remove things.
_REMOVES = re.compile(r"(?<![\w./-])(?:rm|rmdir|unlink|shred)(?![\w-])(.*)$")


def _statements(command):
    return [part.strip() for part in _SEPARATORS.split(command or "") if part.strip()]


def _any(*sources):
    """A matcher that fires when any of these expressions matches a statement."""
    patterns = tuple(re.compile(one) for one in sources)
    def matches(command, area=None):
        return any(pattern.search(statement)
                   for statement in _statements(command) for pattern in patterns)
    return matches


def _arguments(text):
    """The words of a command line that are paths rather than flags.

    Split rather than parsed: a path built out of a variable is invisible to this
    and to any other check that is not a shell.
    """
    found = []
    for word in text.split():
        word = word.strip("'\"")
        if word and not word.startswith("-"):
            found.append(word)
    return found


def _outside(command, area=None):
    """Whether a command removes something outside the area the run owns.

    With no area named, any absolute path is outside: a run that has not said
    where it works has not earned the benefit of the doubt.
    """
    root = os.path.abspath(area) if area else None
    for statement in _statements(command):
        match = _REMOVES.search(statement)
        if match is None:
            continue
        for path in _arguments(match.group(1)):
            if path.startswith("~") or ".." in path.replace("\\", "/").split("/"):
                return True
            if not os.path.isabs(path):
                continue
            if root is None:
                return True
            full = os.path.abspath(path)
            if full != root and not full.startswith(root.rstrip(os.sep) + os.sep):
                return True
    return False


#: The operations no unattended run may perform (NFR-SEC-04). Data, so that the
#: execution layer reads this rather than restating it (M6-P2-T2-C2), and so that
#: a fifth prohibition is one more record rather than one more code path.
#:
#: `git branch -d` is deliberately absent: it refuses an unmerged branch by
#: itself, so it is the safe form and prohibiting it would prohibit the cleanup
#: every run is supposed to do.
PROHIBITED = (
    Operation(
        "force-push", "Force-push",
        "Overwrites work on the shared branch that nobody has seen yet, and the "
        "overwritten commits are reachable from nowhere afterwards.",
        _any(r"\bgit\b[^\n]*\bpush(?![\w-])[^\n]*(?:--force(?![\w])|--force-with-lease"
             r"|(?<![\w-])-f(?![\w-]))",
             r"\bgit\b[^\n]*\bpush(?![\w-])[^\n]*\s\+[^\s:]+:")),
    Operation(
        "rewrite-history", "Rewrite shared history",
        "Gives already-published commits new identifiers, so every other copy of "
        "the branch disagrees with the shared one and can never converge again.",
        _any(r"\bgit\s+rebase(?![\w-])",
             r"\bgit\b[^\n]*\bcommit(?![\w-])[^\n]*--amend(?![\w-])",
             r"\bgit\s+filter-branch(?![\w-])",
             r"\bgit\s+filter-repo(?![\w-])",
             r"\bgit\b[^\n]*\bpush(?![\w-])[^\n]*--mirror(?![\w-])")),
    Operation(
        "delete-unmerged-branch", "Delete a branch holding unmerged work",
        "The work on it is reachable from nothing once the branch is gone, and "
        "the forced form of the command is precisely the one that skips the "
        "check for whether that is true.",
        _any(r"\bgit\s+branch(?![\w-])[^\n]*(?<![\w-])-D(?![\w-])",
             r"\bgit\s+branch(?![\w-])[^\n]*--delete(?![\w-])[^\n]*--force(?![\w-])",
             r"\bgit\s+branch(?![\w-])[^\n]*--force(?![\w-])[^\n]*--delete(?![\w-])",
             r"\bgit\b[^\n]*\bpush(?![\w-])[^\n]*--delete(?![\w-])",
             r"\bgit\b[^\n]*\bpush(?![\w-])[^\n]*\s:[^\s]")),
    Operation(
        "delete-outside-area", "Delete outside the working area",
        "A run owns its own working area and nothing else; a path that climbs "
        "out of it belongs to somebody who did not ask for this.",
        _outside),
)


def prohibited(command, area=None):
    """Every prohibition this command would break, in the order they are declared.

    The one routine that judges a command. A caller that reads PROHIBITED and
    writes its own matching has made a second definition of the rules, which is
    the thing NFR-SEC-04 is trying to prevent.
    """
    if not isinstance(command, str) or not command.strip():
        return []
    return [operation for operation in PROHIBITED
            if operation.matches(command, area)]


def refusal(command, area=None):
    """Why this command is refused, written for the person who has to act on it."""
    return ["%s is prohibited unattended: %s" % (operation.title, operation.why)
            for operation in prohibited(command, area)]


# ------------------------------------------------------------------ the command

def format_report(grouped):
    """The same results, written for a person."""
    lines = []
    for source in grouped:
        found = grouped[source]
        if not found:
            continue
        lines.append("commit message" if source == STDIN else source)
        for finding in found:
            lines.append("  %-7s %-16s %s"
                         % (finding.severity.upper(), finding.code, finding.message))
        lines.append("")

    total = sum(len(found) for found in grouped.values())
    if not total:
        lines.append("OK: no secret value in %d artefact%s"
                     % (len(grouped), "" if len(grouped) == 1 else "s"))
    else:
        lines.append("%d secret%s found" % (total, "" if total == 1 else "s"))
    return "\n".join(lines)


def main(argv, out=sys.stdout, stdin=None):
    """The command. Its exit status is the answer, as the validator's is."""
    if not argv:
        out.write(USAGE + "\n")
        return 2
    grouped = scan(argv, stdin)
    out.write(format_report(grouped) + "\n")
    return 1 if any(grouped.values()) else 0


if __name__ == "__main__":       # pragma: no cover - the command line entry point
    sys.exit(main(sys.argv[1:]))
