import sys
import select
from subprocess import Popen, PIPE
from threading import Lock, Event

from helpers import Timestamp


class Task:
    """Support deploying background tasks by the web server.

    A singleton object manages threads and events for tasks.

    Care is taken that tasks can be started in the background,
    can be killed, and that the output and return status of tasks is communicated
    via web sockets.
    """

    def __init__(self, socketio):
        """Create a task object.

        Parameters
        ----------
        socketio: object
            The socketio object corresponding to the Flask app.
        """
        self.socketio = socketio
        self.threads = {}
        self.stopEvents = {}
        self.threadLock = Lock()

    def start(self, key, task, *args, **kwargs):
        """Start a task in a new thread.

        Each task has a key, and the thread for this task is
        stored under that key.
        A task can only start if there is no active thread under
        that key.

        Each task also has a thread event under its key, which
        will be used to signal to the task that it should stop.

        This is a low-level function.
        See also `startTask()`

        Parameters
        ----------
        key: string
            A name associated with a task, used to lookup its
            thread and stop event.
        task: function
            A python function that runs a task. This function may
            wrap a shell command by means of the standard module
            `subprocess`
        *args, **kwargs: any
            Additional arguments to pass to the task function.
        """
        socketio = self.socketio
        threads = self.threads
        stopEvents = self.stopEvents
        threadLock = self.threadLock

        with threadLock:
            threads[key] = socketio.start_background_task(task, *args, **kwargs)
            stopEvents[key] = Event()

    def stop(self, key):
        """Signal to a task that it should stop.

        This happens by setting the stop event associated with the task.
        The task function should check this event regularly and stop voluntarily
        when it is set.

        Parameters
        ----------
        key: string
            The key associated with a task.
        """
        stopEvents = self.stopEvents

        if not self.isIdle(key):
            stopEvents[key].set()

    def isStopped(self, key):
        """Check whether the stop signal has been issued for a task.

        Parameters
        ----------
        key: string
            The key associated with a task.

        Returns
        -------
        boolean
            Whether a running task has its stop event set.
            False if the task is not running (anymore).
        """
        stopEvents = self.stopEvents
        return not self.isIdle(key) and stopEvents[key].is_set()

    def clear(self, key):
        """Remove the thread and stop event of a task.

        Parameters
        ----------
        key: string
            The key associated with a task.
        """
        threads = self.threads
        stopEvents = self.stopEvents
        threads[key] = None
        stopEvents[key] = None

    def isIdle(self, key):
        """Check whether a task is running.

        Parameters
        ----------
        key: string
            The key associated with a task.

        Returns
        -------
        boolean
            True if there is no active thread for the task
        """
        return self.threads.get(key, None) is None

    def startTask(self, key):
        self.start(key, self.doTask, key)

    def doTask(self, task):
        """Function to implement tasks.

        There are two tasks:

        *   `task='function'`: run a python function, programmed inside here.
        *   `task='script'`: run a python script via the shell (script.py)

        Tasks will run asynchronically.

        It will emit progress messages during execution and a return code upon
        completion.  It will also emit an error message if it does not complete
        successfully.

        Progress messages come in two kinds: `info` and `error`.

        When the task is a script, its stdout and stderr are catched in real time and
        emitted as progress messages of kinds `info` and `error` respectively.

        In each iteration of the loop that emits the progress messages, the stop
        event will be examined. If it is set, execution of the task will be ended.

        !!! caution "async mode"
            Choosing `eventlet` as async mode leads to problems.

            When scripts are executed via subprocess, the mechanism of catching the
            stderr and stdout data causes blocking. While the server log shows
            the emit messages in proper order and timing, the clients tell
            another story: all emits arrive in one batch *after* the task has finished.

            I have tried several workarounds, like making the readline of
            stderr and stdout asynchronous via `fcntl`, or bypassing the
            message queue for emit messages, or using an eventlet message queue
            explicitly, but to no avail!

            However, the problem disappears by choosing `threading` as async mode.

        Parameters
        ----------
        task: string
            Either `function` or `script`.
            This selects which task will be executed.
        """
        socketio = self.socketio
        TM = Timestamp()
        socketio.emit("status", dict(tm=TM.elapsed(), task=task, stat="start"))
        interrupted = False

        def flush(toEnd=False):
            """Read stderr and stdout of a process in parallel without blocking.

            Parameters
            ----------
            toEnd: boolean, optional False
                If True, the complete remainders on stderr and stdout is read.
                Meant for when the process has stopped.
                If False, at most a single line of stderr and/or stdout will be read.
            """
            # trick: use select to wait for stdout and stderr in parallel
            readyStreams = select.select([proc.stdout, proc.stderr], [], [], 0.5)[0]

            for stream in readyStreams:
                kind = "info" if stream is proc.stdout else "error"
                text = stream.read() if toEnd else stream.readline()

                if not text:
                    continue

                # text = text.rstrip("\n")

                socketio.emit(
                    "progress",
                    dict(
                        tm=TM.elapsed(),
                        task=task,
                        kind=kind,
                        text=text,
                    ),
                )

        try:
            if task == "function":

                # start function code

                errorSteps = {2, 4}
                longSteps = {8: 5, 9: 8}

                for i in range(1, 11):
                    if self.isStopped(task):
                        # here is the check on the kill signal
                        interrupted = True
                        break

                    kind = "error" if i in errorSteps else "info"
                    interval = longSteps.get(i, 1)
                    socketio.emit(
                        "progress",
                        dict(
                            tm=TM.elapsed(),
                            task=task,
                            kind=kind,
                            text=f"function step {i}",
                        ),
                    )
                    socketio.sleep(interval)

                stat = "success"
                msg = "ok"

                # end function code

            elif task == "script":

                # start wrapper to run a script in a subprocess

                proc = Popen(
                    "python script.py",
                    shell=True,
                    text=True,
                    bufsize=None,
                    stdout=PIPE,
                    stderr=PIPE,
                )

                while True:
                    flush()
                    if self.isStopped(task):
                        # here is the check on the kill signal
                        interrupted = True
                        proc.kill()
                        break

                    returnCode = proc.poll()
                    sys.stderr.write(f"{returnCode=}\n")
                    sys.stderr.flush()

                    if returnCode is not None:
                        # script has ended, return code is known
                        break

                flush(toEnd=True)
                stat = "success" if returnCode == 0 else "failure"
                msg = f"exit with {returnCode}" if returnCode else ""

                # end wrapper

            if interrupted:
                stat = "interrupt"
                msg = "interrupted by user"

        except Exception as e:
            stat = "failure"
            msg = f"exception script {str(e)}"

        # emit a status message that the task has finished
        socketio.emit("status", dict(tm=TM.elapsed(), task=task, stat=stat, msg=msg))
        # removed the thread and stop event of this task
        self.clear(task)
