from backend.app.core.rate_limiter import SlidingWindowRateLimiter

def test_security_headers_present(client):
    res = client.get("/health")
    assert res.status_code == 200
    assert res.headers.get("x-frame-options") == "DENY"
    assert res.headers.get("x-content-type-options") == "nosniff"
    assert res.headers.get("x-xss-protection") == "1; mode=block"
    assert "x-process-time-ms" in res.headers

def test_student_forbidden_from_admin_escalation_endpoint(client, student_auth_headers):
    # Student attempts to access admin-only escalation logs
    res = client.get("/api/escalation/logs", headers=student_auth_headers)
    assert res.status_code == 403
    assert "Operation not permitted" in res.json()["detail"]

def test_student_forbidden_from_status_update(client, student_auth_headers):
    # Student attempts to update alert status
    res = client.patch("/api/alerts/1/status", json={"status": "RESOLVED_GENUINE"}, headers=student_auth_headers)
    assert res.status_code == 403

def test_sliding_window_rate_limiter_unit():
    limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=10)
    limiter.check("key1")
    limiter.check("key1")
    limiter.check("key1")
    try:
        limiter.check("key1")
        assert False, "Should have raised 429"
    except Exception as exc:
        assert getattr(exc, "status_code", None) == 429
