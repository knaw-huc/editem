import sys
import time

errorSteps = {2, 4}

for i in range(5):
    stream = sys.stderr if i in errorSteps else sys.stdout
    stream.write(f"step {i}\n")
    stream.flush()
    time.sleep(0.5)

sys.exit(0)
