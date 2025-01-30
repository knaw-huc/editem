import sys
import time

errorSteps = {2, 4}
longSteps = {3: 5, 8: 8}

for i in range(1, 11):
    stream = sys.stderr if i in errorSteps else sys.stdout
    interval = longSteps.get(i, 1)
    stream.write(f"step {i}\n")
    stream.flush()
    time.sleep(interval)

sys.exit(0)
