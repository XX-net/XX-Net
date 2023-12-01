# Recommended number of workers based on instance size:
# https://cloud.google.com/appengine/docs/standard/python3/runtime#entrypoint_best_practices
workers = 1
# Use an asynchronous worker as most of the work is waiting for websites to load
worker_class = 'gevent'