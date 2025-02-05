import sys
import time
from subprocess import Popen

baseInterval = 1
errorSteps = {2, 4}
longSteps = {8: 5, 9: 8}

proc = Popen([sys.executable, "clock.py"], shell=False, text=True)

for i in range(1, 11):
    stream = sys.stderr if i in errorSteps else sys.stdout
    interval = longSteps.get(i, baseInterval)
    stream.write(f"step {i}\n")
    stream.flush()
    time.sleep(interval)

sys.exit(0)
