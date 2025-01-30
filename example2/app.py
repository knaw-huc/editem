import os
import sys
from threading import Lock
from flask import Flask, render_template, send_file
from flask_socketio import SocketIO, emit

PORT = 5050


def console(msg):
    sys.stderr.write(f"{msg}\n")
    sys.stderr.flush()


# Creating a flask app and using it to instantiate a socket object
app = Flask(__name__)
socketio = SocketIO(app, logger=True, engineio_logger=True)
console(f"{socketio.async_mode=}")
thread = {}
threadLock = Lock()


def runWorkflow(pid):
    """Example of how to send server generated events to clients."""
    socketio.emit("status", dict(pid=pid, stat="start-inner"))

    try:
        for i in range(10):
            socketio.sleep(1)
            socketio.emit("progress", dict(pid=pid, step=i))
        stat = "success-inner"
        msg = ""
    except Exception as e:
        msg = str(e)
        stat = "failure-inner"

    socketio.emit("status", dict(pid=pid, stat=stat, msg=msg))
    thread[pid] = None


@app.route("/")
def index():
    projectId = 1
    return render_template("index.html", projectId=projectId)


@app.route("/project/<string:projectId>/")
def project(projectId):
    return render_template("index.html", projectId=projectId)


@app.route("/project/<string:projectId>/run", methods=["GET", "POST"])
def runit(projectId):
    if thread.get(projectId, None) is None:
        console("start workflow")
        stat = "start-outer"

        with threadLock:
            thread[projectId] = socketio.start_background_task(runWorkflow, projectId)

    else:
        console("suppress workflow")
        stat = "start-outer-no"

    return dict(pid=projectId, stat=stat)


@app.route("/project/<string:projectId>/kill", methods=["GET", "POST"])
def killit(projectId):
    if thread.get(projectId, None) is None:
        console("nothing to kill")
        stat = "kill-outer-no"
    else:
        console("killing workflow")
        thread[projectId].g.kill()
        thread[projectId] = None
        stat = "kill-outer"
        socketio.emit("status", dict(pid=projectId, stat="kill-inner"))

    return dict(pid=projectId, stat=stat)


@app.route("/<path:path>")
def staticFile(path):
    if os.path.exists(path):
        console(f"Serving file: {path}")
        return send_file(path)

    console(f"File not found: {path}")
    return "xxx"


@socketio.on("connect")
def test_connect():
    emit("after connect", {"data": "Ready to run"})


if __name__ == "__main__":
    socketio.run(app, port=PORT, debug=True)
