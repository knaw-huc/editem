import os
import sys
import time
import fcntl
import errno
from subprocess import Popen, PIPE, STDOUT
from threading import Lock
from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit

PORT = 5050

# ASYNC_MODE = "eventlet"  # does not work well when running scripts
ASYNC_MODE = "threading"

WLABELS = dict(
    function="function",
    script="script",
    scriptnb="script (io does not block)",
)


def console(msg):
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


class Timestamp:
    def __init__(self):
        self.stamp = time.time()

    def elapsed(self):
        interval = time.time() - self.stamp
        if interval < 10:
            return f"{interval: 2.2f}s"
        interval = int(round(interval))
        if interval < 60:
            return f"{interval:>2d}s"
        if interval < 3600:
            return f"{interval // 60:>2d}m {interval % 60:>02d}s"
        return (
            f"{interval // 3600:>2d}h {(interval % 3600) // 60:>02d}m"
            f" {interval % 60:>02d}s"
        )


# Creating a flask app and using it to instantiate a socket object
app = Flask(__name__)
socketio = SocketIO(app, logger=True, engineio_logger=True, async_mode=ASYNC_MODE)
thread = {}
threadLock = Lock()


def doFunction(useQueue):
    TM = Timestamp()
    socketio.emit("status", dict(tm=TM.elapsed(), stat="start-inner"), **useQueue)

    errorSteps = {2, 4}

    try:
        for i in range(5):
            kind = "error" if i in errorSteps else "info"
            socketio.emit(
                "progress",
                dict(tm=TM.elapsed(), kind=kind, text=f"Step {i}"),
                **useQueue,
            )
            socketio.sleep(0.5)

        stat = "success-inner"
        msg = ""
    except Exception as e:
        msg = str(e)
        stat = "failure-inner"

    socketio.emit("status", dict(tm=TM.elapsed(), stat=stat, msg=msg), **useQueue)
    thread[""] = None


def doScript(useQueue):
    TM = Timestamp()
    socketio.emit("status", dict(tm=TM.elapsed(), stat="start-inner"), **useQueue)

    try:
        proc = Popen(
            "python script.py",
            shell=True,
            text=True,
            bufsize=None,
            stdout=PIPE,
            stderr=STDOUT,
        )

        while True:
            returnCode = proc.poll()

            if returnCode is not None:
                break

            text = proc.stdout.readline()
            socketio.emit(
                "progress",
                dict(tm=TM.elapsed(), kind="info", text=text.rstrip("\n"), **useQueue),
            )

        stat = "success-inner" if returnCode == 0 else "failure-inner"
        msg = f"exit with {returnCode}" if returnCode else ""
    except Exception as e:
        msg = str(e)
        stat = "failure-inner"

    socketio.emit("status", dict(tm=TM.elapsed(), stat=stat, msg=msg), **useQueue)
    thread[""] = None


# Helper function to add the O_NONBLOCK flag to a file descriptor
def makeAsync(fd):
    fcntl.fcntl(fd, fcntl.F_SETFL, fcntl.fcntl(fd, fcntl.F_GETFL) | os.O_NONBLOCK)


# Helper function to read some data from a file descriptor, ignoring EAGAIN errors
def readAsync(fd):
    try:
        return fd.read()
    except Exception as e:
        if e.errno != errno.EAGAIN:
            raise e
        else:
            return ""


def doScriptNB(useQueue):
    TM = Timestamp()
    socketio.emit("status", dict(tm=TM.elapsed(), stat="start-inner"), **useQueue)

    try:
        proc = Popen(
            "python script.py",
            shell=True,
            text=False,
            bufsize=None,
            stdout=PIPE,
            stderr=STDOUT,
        )
        makeAsync(proc.stdout)

        while True:
            text = readAsync(proc.stdout)

            if text:
                text = text.decode("utf8")
                socketio.emit(
                    "progress",
                    dict(
                        tm=TM.elapsed(),
                        kind="info",
                        text=text.rstrip("\n"),
                        **useQueue,
                    ),
                )
            returnCode = proc.poll()

            if returnCode is not None:
                break

        stat = "success-inner" if returnCode == 0 else "failure-inner"
        msg = f"exit with {returnCode}" if returnCode else ""
    except Exception as e:
        msg = str(e)
        stat = "failure-inner"

    socketio.emit("status", dict(tm=TM.elapsed(), stat=stat, msg=msg), **useQueue)
    thread[""] = None


WTASKS = dict(
    function=doFunction,
    script=doScript,
    scriptnb=doScriptNB,
)


@app.route("/")
def index():
    buttons = []

    for thr in ("t", "d"):
        tLabel = "Spawn with explicit thread" if thr == "t" else "Spawn directly"
        buttons.append(f"<h2>{tLabel}</h2>")

        for que in ("q", "d"):
            qLabel = "Use event queue" if que == "q" else "Bypass event queue"
            buttons.append(f"<h3>{qLabel}</h3>")

            for what in ("function", "script", "scriptnb"):
                wLabel = WLABELS[what]
                buttons.append(
                    f"""<button id="run{what}{thr}{que}" type="button">"""
                    f"""Run {wLabel}</button>"""
                )
    return render_template("index.html", buttons="\n".join(buttons))


@app.route("/run/<string:what>/<string:thr>/<string:que>/", methods=["GET", "POST"])
def run(what, thr, que):
    wLabel = WLABELS[what]
    wTask = WTASKS[what]
    useQueue = dict(ignore_queue=que != "q")

    if thr == "t":
        if thread.get("", None) is None:
            console(f"start {wLabel}")
            stat = "start-outer"

            with threadLock:
                thread[""] = socketio.start_background_task(wTask, useQueue)

        else:
            console("suppress workflow")
            stat = "start-outer-no"
    else:
        console(f"start {wLabel}")
        stat = "start-outer"
        socketio.start_background_task(wTask, useQueue)

    return dict(stat=stat)


@app.route("/<path:path>")
def staticFile(path):
    if os.path.exists(path):
        return send_file(path)

    console(f"File not found: {path}")
    return "xxx"


@socketio.on("connect")
def test_connect():
    emit("after connect", {"data": "Ready to run"})


if __name__ == "__main__":
    socketio.run(app, port=PORT, debug=True)
