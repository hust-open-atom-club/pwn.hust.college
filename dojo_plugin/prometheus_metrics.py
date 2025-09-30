from prometheus_client import Counter, Histogram, Gauge, Summary
from flask import request, g
import time

# 请求计数器
REQUEST_COUNT = Counter(
    'ctfd_http_requests_total',
    'Total number of HTTP requests',
    ['method', 'endpoint', 'status']
)

# 请求延迟直方图
REQUEST_LATENCY = Histogram(
    'ctfd_http_request_duration_seconds',
    'HTTP request latency in seconds',
    ['method', 'endpoint']
)

# 活跃用户数
ACTIVE_USERS = Gauge(
    'ctfd_active_users',
    'Number of active users'
)

# 挑战解决计数器
CHALLENGE_SOLVES = Counter(
    'ctfd_challenge_solves_total',
    'Total number of challenge solves',
    ['challenge_name', 'category']
)

# 用户注册计数器
USER_REGISTRATIONS = Counter(
    'ctfd_user_registrations_total',
    'Total number of user registrations'
)

# 登录尝试计数器
LOGIN_ATTEMPTS = Counter(
    'ctfd_login_attempts_total',
    'Total number of login attempts',
    ['status']  # success, failure
)

# 系统信息
SYSTEM_INFO = Gauge(
    'ctfd_system_info',
    'CTFd system information',
    ['version', 'environment']
)

def init_metrics():
    """初始化系统信息指标"""
    SYSTEM_INFO.labels(version='1.0.0', environment='production').set(1)

def record_request_metrics(response):
    """记录请求指标"""
    if hasattr(g, 'start_time'):
        duration = time.time() - g.start_time
        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=request.endpoint
        ).observe(duration)
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.endpoint,
        status=response.status_code
    ).inc()

def before_request():
    """请求前处理"""
    g.start_time = time.time()

def after_request(response):
    """请求后处理"""
    record_request_metrics(response)
    return response 