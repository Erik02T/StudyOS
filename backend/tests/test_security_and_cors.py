def test_cors_allows_local_nextjs_origin_preflight(client):
    response = client.options(
        "/auth/register",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_cors_allows_vercel_origin_preflight(client):
    response = client.options(
        "/auth/register",
        headers={
            "Origin": "https://study-os-20.vercel.app",
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
    )
    assert response.status_code in (200, 204)
    assert response.headers.get("access-control-allow-origin") == "https://study-os-20.vercel.app"


def test_security_headers_present(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers.get("x-content-type-options") == "nosniff"
    assert response.headers.get("x-frame-options") == "DENY"
    assert response.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
    assert response.headers.get("permissions-policy") == "camera=(), microphone=(), geolocation=()"


def test_register_is_rate_limited(client):
    payload = {
        "email": "rate-register@example.com",
        "password": "Password123!",
        "available_hours_per_day": 2,
        "preferred_time_block": "19:00-21:00",
    }

    status_codes = []
    for _ in range(12):
        response = client.post("/auth/register", json=payload)
        status_codes.append(response.status_code)

    assert 201 in status_codes
    assert 429 in status_codes
