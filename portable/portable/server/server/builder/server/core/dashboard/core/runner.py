import api
import threading

threading.Thread(target=api.run, daemon=True).start()

while True:
    pass
