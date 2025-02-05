import time

with open("ticks.txt", "w") as fh:
    i = 0
    while True:
        i += 1
        fh.write(f"{i}\n")
        fh.flush()
        time.sleep(1)
