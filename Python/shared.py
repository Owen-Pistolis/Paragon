from queue import Queue
from threading import Event

# Queue for log messages
log_queue = Queue()

# Queue for workflow status updates
workflow_status_queue = Queue()

# Event for workflow updates
update_workflows = Event()