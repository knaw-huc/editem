import os
from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit

from task import Task
from helpers import console

PORT = 5050
ASYNC_MODE = "threading"  # N.B. eventlet will not work fully with script tasks
TASKS = ("function", "script")


# Creating a flask app and using it to instantiate a socket object
app = Flask(__name__)
socketio = SocketIO(app, logger=True, engineio_logger=True, async_mode=ASYNC_MODE)
TT = Task(socketio)


@app.route("/")
def index():
    """Create the HTML for a task runner.

    We create buttons to run and kill two tasks,
    plus areas where the progress and status of each task are collected.
    """
    buttons = ["", ""]
    status = ["", ""]
    progress = ["", ""]

    for i, task in enumerate(TASKS):
        buttons[i] = (
            f"""
            <button id="run{task}" type="button">Run {task}</button>
            <button id="kill{task}" type="button">kill {task}</button>
            """
        )
        progress[i] = (
            f"""
            <div id="progress{task}" class="msg"></div>
            """
        )
        status[i] = (
            f"""
            <div id="status{task}" class="msg">not yet done</div>
            """
        )

    effects = f"""
        <table border=1>
            <tr>
                <th>{buttons[0]}</th>
                <th>{buttons[1]}</th>
            <tr>
                <td class="progress">{progress[0]}</td>
                <td>{progress[1]}</td>
            </tr>
            <tr>
                <td>{status[0]}</td>
                <td>{status[1]}</td>
            </tr>
        </table>
        """

    return render_template("index.html", buttons=buttons, effects=effects)


@app.route("/run/<string:task>/", methods=["GET", "POST"])
def run(task):
    """Reponds to clicking the run button of a specific task."""
    if TT.isIdle(task):
        console(f"start {task}")
        stat = "start-issued"
        msg = "about to start"

        TT.startTask(task)

    else:
        console("suppress workflow")
        stat = "start-prevented"
        msg = "already running"

    return dict(task=task, stat=stat, msg=msg)


@app.route("/kill/<string:task>/", methods=["GET", "POST"])
def kill(task):
    """Reponds to clicking the kill button of a specific task"""
    if TT.isIdle(task):
        stat = "kill-prevented"
        msg = "not running"
    else:
        TT.stop(task)
        socketio.emit("status", dict(stat="kill", task=task, msg="kill signalled"))
        stat = "kill-issued"
        msg = "about to kill"

    return dict(task=task, stat=stat, msg=msg)


@app.route("/<path:path>")
def staticFile(path):
    """Serve a static file."""
    if os.path.exists(path):
        return send_file(path)

    console(f"File not found: {path}")
    return "xxx"


@socketio.on("connect")
def test_connect():
    """Verify the websocket connection.
    """
    emit("after connect", {"data": "Ready to run"})


if __name__ == "__main__":
    # start the websocket-enabled flask app
    socketio.run(app, port=PORT, debug=True)
