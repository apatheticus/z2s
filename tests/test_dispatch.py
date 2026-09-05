# -*- coding: utf-8 -*-
"""Stopping a run has to reach the workers the run started (R3-02).

Every worker is launched into its own session, which is deliberate: a worker's
own test runner starts children, and ending the one handle this module holds
would leave the rest of that tree running in the project's files. The cost of
that isolation is the thing this module now has an answer for — a `kill -TERM`
on the orchestrator reaches none of them, and four `claude -p` processes were
measured outliving each of two stops of a real build, still editing the working
tree the operator had stopped the run in order to inspect.

The child scripts here may sleep. The clock ban (NFR-GEN-01) is on `z2s/*.py`,
and a test that needs a process which is genuinely still running needs one.
"""

import os
import subprocess
import sys
import tempfile
import threading
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from z2s import dispatch  # noqa: E402

#: A child that outlives any test, and starts a grandchild in the same group so
#: a stop that reached only the handle would be visible as a survivor.
PATIENT = ("import subprocess, sys, time; "
           "subprocess.Popen([sys.executable, '-c', 'import time; time.sleep(600)']); "
           "time.sleep(600)")


class Live(unittest.TestCase):

    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="z2s-dispatch-")
        dispatch.STOPPING.clear()
        self.addCleanup(dispatch.STOPPING.clear)

    def background(self, command):
        """Run `launch` off the main thread and hand back the thread."""
        held = []
        thread = threading.Thread(
            target=lambda: held.append(dispatch.launch(command, self.root)))
        thread.daemon = True
        thread.start()
        return thread, held


class TestEveryLiveProcessIsKnown(Live):

    def test_a_finished_launch_leaves_nothing_registered(self):
        before = len(dispatch._LIVE)
        dispatch.launch([sys.executable, "-c", "pass"], self.root)
        self.assertEqual(len(dispatch._LIVE), before,
                         "a process the operating system has already reaped is "
                         "an identifier it may hand to somebody else")

    def test_a_launch_that_could_not_start_registers_nothing(self):
        with self.assertRaises(OSError):
            dispatch.launch([os.path.join(self.root, "not-a-binary")], self.root)
        self.assertEqual(dispatch._LIVE, set())

    def test_a_running_process_is_registered_while_it_runs(self):
        thread, _ = self.background([sys.executable, "-c", PATIENT])
        try:
            self.assertTrue(_settled(lambda: len(dispatch._LIVE) == 1),
                            "the orchestrator holds futures, which can be "
                            "waited on and cannot be signalled; this set is the "
                            "only place a handle exists")
        finally:
            dispatch.halt()
            thread.join(timeout=60)


class TestAStopReachesTheWorkers(Live):

    def test_halt_ends_a_live_process_and_says_how_many(self):
        thread, held = self.background([sys.executable, "-c", PATIENT])
        self.assertTrue(_settled(lambda: len(dispatch._LIVE) == 1))
        self.assertEqual(dispatch.halt(), 1)
        thread.join(timeout=60)
        self.assertFalse(thread.is_alive(), "the launch returned, so the child "
                                            "it was waiting on is gone")
        self.assertEqual(dispatch._LIVE, set())
        code, expired = held[0]
        self.assertNotEqual(code, 0)
        self.assertFalse(expired, "it was stopped, not timed out — a bound was "
                                  "never reached and none was set")

    def test_halt_with_nothing_running_is_not_an_error(self):
        self.assertEqual(dispatch.halt(), 0)

    def test_halt_ends_what_the_worker_itself_started(self):
        """`start_new_session=True` is what makes this possible and what makes
        it necessary: the group is signalled, not the one handle."""
        thread, _ = self.background([sys.executable, "-c", PATIENT])
        self.assertTrue(_settled(lambda: len(dispatch._LIVE) == 1))
        popen = next(iter(dispatch._LIVE))
        group = os.getpgid(popen.pid)
        dispatch.halt()
        thread.join(timeout=60)
        found = subprocess.run(["/bin/ps", "-o", "pid=", "-g", str(group)],
                               capture_output=True, text=True)
        self.assertEqual(found.stdout.split(), [],
                         "a grandchild left running is the leak this exists for")


class TestNothingWaitsThroughAStop(Live):

    def test_a_backoff_ends_the_moment_the_run_is_stopping(self):
        dispatch.STOPPING.set()
        dispatch.pause(600)     # would hang the suite if it waited

    def test_nothing_waits_by_accident(self):
        dispatch.pause(0)
        dispatch.pause(None)


def _settled(question, tries=200):
    """Whether something became true. A test may watch the clock; a module may not."""
    import time
    for _ in range(tries):
        if question():
            return True
        time.sleep(0.05)
    return question()


if __name__ == "__main__":
    unittest.main()
