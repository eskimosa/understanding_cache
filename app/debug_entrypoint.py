import debugpy
import os

# Listen on all interfaces (0.0.0.0) so we can connect from outside the container
debugpy.listen(("0.0.0.0", 5678))
print("Debugger listening on port 5678, waiting for client to connect...")
# Wait for debugger to attach before starting the app
# Comment out the next line if you want the app to start immediately
debugpy.wait_for_client()
print("Debugger attached! Starting application...")

# Now start uvicorn
import uvicorn
uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=False)

