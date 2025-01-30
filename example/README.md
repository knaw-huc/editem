# Task runner example

Websockets help to make a web-based task controller, where users can follow the
progress of a task in real time, and where different users can observe the same
task execution as it happens.

However, several things are far from trivial:

1.  if you let flask-socketio spawn shell command in the background with
    pythons `subprocess` module, how can I collect the output in real time
    without blocking?
2.  how can I collect both stderr and stdin in real time?
3.  how can I call such a task from the controlling website?

It took me a fair amount of research to find out the answers to these questions.

In short:

1.  do **not** use async mode `eventlet` but instead `threading`;
2.  use `select` from the python standardlib module `select`;
3.  kill a thread by setting up a stop event for the thread, and as you poll
    the stderr and stdout of the subprocess, inspect the status of that event,
    and if set, kill the process


# Hands on

```
git clone https://github.com/knaw-huc/editem
cd editem/example
python app.py
```

Then navigate to [localhost:5050](http://localhost:5050)
