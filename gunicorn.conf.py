import multiprocessing
import os

# Server socket
bind = "0.0.0.0:5000"
backlog = 2048

# Worker processes
workers = 2  # Reduced from 4 to 2
worker_class = "gevent"
worker_connections = 1000
timeout = 30
keepalive = 2

# Memory optimization
max_requests = 1000
max_requests_jitter = 50
worker_tmp_dir = "/dev/shm"  # Use RAM for temporary files
worker_class = "gevent"
preload_app = True  # Preload application code

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Process naming
proc_name = "dopp"

# SSL
keyfile = None
certfile = None

# Server mechanics
daemon = False
pidfile = None
umask = 0
user = None
group = None
tmp_upload_dir = None

# Server hooks
def on_starting(server):
    pass

def on_exit(server):
    pass 