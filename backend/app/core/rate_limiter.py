import time
from collections import defaultdict
from fastapi import HTTPException, status

class SlidingWindowRateLimiter:
    """In-memory rate limiter using sliding timestamp window."""
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = defaultdict(list)

    def check(self, key: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds
        # Evict timestamps older than cutoff window
        self.requests[key] = [t for t in self.requests[key] if t > cutoff]
        
        if len(self.requests[key]) >= self.max_requests:
            retry_after = int(self.window_seconds - (now - self.requests[key][0]))
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_seconds}s. Try again in {max(1, retry_after)} seconds.",
                headers={"Retry-After": str(max(1, retry_after))}
            )
        self.requests[key].append(now)

# Specific limiters
alert_rate_limiter = SlidingWindowRateLimiter(max_requests=10, window_seconds=60) # 10 alerts/min
login_rate_limiter = SlidingWindowRateLimiter(max_requests=15, window_seconds=60) # 15 login attempts/min
