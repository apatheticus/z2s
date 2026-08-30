# -*- coding: utf-8 -*-
"""Running one command, bounded, and ending everything it started.

Three callers need this and each of them needed it for the same reason: a run
that cannot end a process that has stopped moving is a run that does not end.
Attempts bound a unit that keeps failing and the gauntlet bounds one that keeps
being wrong, but neither bounds one that is simply sitting there — a real build
idled for two hours and twenty-two minutes with the work finished on disk and
nothing in the method that was ever going to notice.

Three things here are load-bearing and must not be tidied apart:

* **The command gets its own session.** A worker starts a test runner, which
  starts workers of its own. Ending the handle this module holds ends the one
  process it can see and leaves the rest of the tree running in the project's
  files, where the next unit will trip over it.
* **Output goes to a FILE, never a pipe.** Once the children outlive the first
  signal, anything holding the write end of a pipe blocks whoever is reading it
  — which is exactly what `subprocess.run`'s own `timeout=` does when it reaps,
  and why this uses `Popen` and waits itself. The log and the group kill are one
  design decision, not two that happen to sit together.
* **The grace period is a wait, not a nap.** Nothing in this package may read
  the clock (NFR-GEN-01), and `wait(timeout=)` asks the operating system how
  long it has been rather than asking the clock twice.

A stated ceiling: a bound is wall-clock, so a worker that is genuinely slow and
a worker that is wedged look the same from here. That is why a dispatch that
runs out of time is not counted against the unit — `z2s/execute.py` asks it for
its account instead, and the unit pays only for silence it chose.

This module runs commands and judges none of them. Whether a command is allowed
to run at all is `z2s/safety.py`'s question, asked by the caller before it gets
here, and it stays the caller's question: a runner that vetted its own input
would be a second place the rules are written down.
"""

import os
import signal
import subprocess
import threading

#: How long a process group is given to end on its own after being asked. Long
#: enough for a test runner to put its own children down and flush what it was
#: writing; short enough that a run stopping is something a person sees happen.
GRACE = 10


def pause(seconds):
    """Wait, for a caller that has just failed to start something.

    A run that could not launch a worker and immediately tries again is not
    retrying — it is asking the same unanswerable question three times in the
    same second. A build watched doing exactly that spent a unit's whole misfire
    budget in under five seconds and blocked three units for the state of the
    host, which nothing about any of them had anything to do with.

    Here rather than in the orchestrator, and for the reason `stop` waits the
    way it does: nothing in this package may read the clock (NFR-GEN-01), and an
    `Event` that is never set asks the operating system to hold this thread for
    a stated interval instead of asking the clock twice. `time.sleep` would do
    the same thing while breaking the rule the ban exists to enforce, so it is
    not a near miss — it is the wrong call.

    Nothing waits here by accident: `seconds` of zero or less returns at once.
    """
    if seconds and seconds > 0:
        threading.Event().wait(seconds)


def _end(popen, sign):
    """Signal the whole group, and fall back to the one process we hold.

    Everything here is already-gone or not-permitted, and both mean the same
    thing to a caller that is about to wait: there is nothing left to signal.
    `AttributeError` is the platform without process groups at all.
    """
    try:
        os.killpg(os.getpgid(popen.pid), sign)
        return
    except (OSError, AttributeError):
        pass
    try:
        popen.kill()
    except OSError:
        pass


def stop(popen):
    """End a process and everything it started: asked first, then not asked."""
    _end(popen, signal.SIGTERM)
    try:
        popen.wait(timeout=GRACE)
        return
    except subprocess.TimeoutExpired:
        pass
    _end(popen, signal.SIGKILL)
    popen.wait()


def launch(command, cwd, env=None, timeout=None, log=None):
    """Run one command to its end or to its deadline.

    Returns `(exit status, whether it ran out of time)`. A command given no
    bound runs for as long as it likes, which is what a project asking for
    `null` is asking for. `OSError` is left to the caller: a command that could
    not be started at all is a different thing from one that failed, and every
    caller here already tells those two apart.
    """
    sink = None
    if log:
        directory = os.path.dirname(log)
        if directory and not os.path.isdir(directory):
            os.makedirs(directory)
        # Not through `z2s/writer.py`, and the exemption is named in
        # `tests/test_writer.py`: that module takes finished text and writes it
        # once, and this needs a live descriptor a child process writes into
        # while it runs. A log that only appears afterwards answers none of the
        # questions a log is for.
        sink = open(log, "wb")
    try:
        popen = subprocess.Popen(
            list(command), cwd=os.path.abspath(cwd), env=env,
            stdout=sink, stderr=(subprocess.STDOUT if sink else None),
            start_new_session=True)
        try:
            return popen.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            stop(popen)
            return popen.returncode, True
    finally:
        if sink is not None:
            sink.close()
