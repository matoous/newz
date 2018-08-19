# Create a metric to track time spent and requests made.
from prometheus_client import Summary, Counter, Gauge, Histogram

CACHE_HITS = Counter('cache_hits_total', 'Total cache hits')
CACHE_MISSES = Counter('cache_miss_total', 'Total cache misses')
RATELIMIT_HITS = Counter('ratelimit_hits', 'Total hits of ratelimit')
QUEUE_STATE = Gauge('tasks_in_queue', 'Total tasks in queue')
REQUEST_TIME = Histogram('request_processing_seconds', 'Time spent processing request')