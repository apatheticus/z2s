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
#:
#: Twenty rather than ten because ten was measured too short for the thing this
#: period exists for. A worker's checks stand up real infrastructure, and a
#: container holding an open database connection is not reliably a ten-second
#: teardown; a worker killed before its own cleanup finished leaves what it
#: started up on the host. The run reports what it finds still running and
#: removes none of it, so the grace period is the only thing standing between an
#: orderly shutdown and a leak somebody clears by hand.
GRACE = 20

#: Every process this module has started and not yet reaped, with the lock that
#: keeps the set honest while several dispatch threads add to and take from it.
#:
#: Held here because this is the only place a handle exists at all. `launch`
#: waits on its own process inside the calling thread, so the `Popen` never
#: leaves this frame — the orchestrator holds futures, which can be waited on
#: and cannot be signalled.
_LIVE = set()
_GUARD = threading.Lock()

#: Set once the run is stopping, and never cleared here — the orchestrator
#: clears it as it starts. Two things read it: `pause`, so a five-minute backoff
#: ends when somebody asks the run to stop rather than five minutes later, and
#: the run itself, which settles nothing and dispatches nothing further once it
#: is set.
STOPPING = threading.Event()


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

    Nothing waits here by accident: `seconds` of zero or less returns at once,
    and neither does anything wait through a stop — the shared `STOPPING` event
    is what is waited on, so a run asked to stop during a five-minute backoff
    stops now rather than in five minutes.
    """
    if seconds and seconds > 0:
        STOPPING.wait(seconds)


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


def halt():
    """End every process this module started. Returns how many there were.

    The one path that reaches a worker from outside its own dispatch. Every
    worker is launched into its own session, which is what keeps a worker from
    signalling the operator's shell — and keeps the operator from signalling the
    worker. A `kill -TERM` on a run was measured leaving four `claude -p`
    processes alive across two stops of a real build, still editing the working
    tree the operator had stopped the run in order to look at. Each had to be
    found and killed by hand.

    Signal everything first, then wait on all of it, then kill whatever is left.
    Doing the three per process in turn would bound a stop at one `GRACE` PER
    WORKER, and an operator who has just asked a run to stop is watching it.

    Safe to call from a signal handler and safe to call twice: `_end` treats
    already-gone and not-permitted alike, and a process reaped by the thread
    that launched it is gone from the set by then.
    """
    STOPPING.set()
    with _GUARD:
        held = list(_LIVE)
    for popen in held:
        _end(popen, signal.SIGTERM)
    for popen in held:
        try:
            popen.wait(timeout=GRACE)
        except subprocess.TimeoutExpired:
            _end(popen, signal.SIGKILL)
    return len(held)


def launch(command, cwd, env=None, timeout=None, log=None):
    """Run one command to its end or to its deadline.

    Returns `(exit status, whether it ran out of time)`. A command given no
    bound runs for as long as it likes, which is what a project asking for
    `null` is asking for. `OSError` is left to the caller: a command that could
    not be started at all is a different thing from one that failed, and every
    caller here already tells those two apart.

    Nothing starts once the run is stopping, and the guard is here because this
    is the one door: a killed worker leaves no report, and the caller's answer to
    a worker that left no report is to ask it what it built — so a stop that
    ended four workers started four more, in a run the operator had just stopped.
    An `OSError` because that is what every caller already reads as "this host
    will not start this command", which is exactly what has happened.
    """
    if STOPPING.is_set():
        raise OSError("the run is stopping; nothing further is started")
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
        # Registered the moment there is something to register and dropped
        # however this returns, so `halt` never signals a process identifier
        # the operating system has already handed to somebody else.
        with _GUARD:
            _LIVE.add(popen)
        try:
            return popen.wait(timeout=timeout), False
        except subprocess.TimeoutExpired:
            stop(popen)
            return popen.returncode, True
        finally:
            with _GUARD:
                _LIVE.discard(popen)
    finally:
        if sink is not None:
            sink.close()
