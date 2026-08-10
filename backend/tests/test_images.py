def _auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_upload_valid_image(client, registered_user_token, sample_image_bytes):
    resp = client.post(
        "/api/images/upload",
        headers=_auth_headers(registered_user_token),
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 202
    body = resp.json()
    assert body["status"] == "pending"
    assert "processing_id" in body


def test_upload_rejects_unsupported_file_type(client, registered_user_token):
    resp = client.post(
        "/api/images/upload",
        headers=_auth_headers(registered_user_token),
        files={"file": ("test.txt", b"not an image", "text/plain")},
    )
    assert resp.status_code == 400


def test_upload_rejects_corrupted_image(client, registered_user_token):
    resp = client.post(
        "/api/images/upload",
        headers=_auth_headers(registered_user_token),
        files={"file": ("fake.jpg", b"\xff\xd8\xff not really a jpeg", "image/jpeg")},
    )
    assert resp.status_code == 400


def test_upload_requires_auth(client, sample_image_bytes):
    resp = client.post(
        "/api/images/upload",
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )
    assert resp.status_code == 401


def test_status_endpoint_for_uploaded_image(client, registered_user_token, sample_image_bytes):
    upload_resp = client.post(
        "/api/images/upload",
        headers=_auth_headers(registered_user_token),
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )
    processing_id = upload_resp.json()["processing_id"]

    status_resp = client.get(f"/api/images/{processing_id}/status", headers=_auth_headers(registered_user_token))
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] in ("pending", "processing", "completed", "failed")


def test_result_endpoint_for_uploaded_image(client, registered_user_token, sample_image_bytes):
    upload_resp = client.post(
        "/api/images/upload",
        headers=_auth_headers(registered_user_token),
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )
    processing_id = upload_resp.json()["processing_id"]

    result_resp = client.get(f"/api/images/{processing_id}/result", headers=_auth_headers(registered_user_token))
    assert result_resp.status_code == 200
    assert result_resp.json()["image"]["filename"]


def test_status_not_found_for_unknown_id(client, registered_user_token):
    fake_id = "00000000-0000-0000-0000-000000000000"
    resp = client.get(f"/api/images/{fake_id}/status", headers=_auth_headers(registered_user_token))
    assert resp.status_code == 404


def test_vehicle_endpoint_before_processing_completes(client, registered_user_token, sample_image_bytes):
    """Before the worker has run (no worker in the test env), the vehicle
    endpoint should degrade gracefully rather than error.
    """
    upload_resp = client.post(
        "/api/images/upload",
        headers=_auth_headers(registered_user_token),
        files={"file": ("test.jpg", sample_image_bytes, "image/jpeg")},
    )
    processing_id = upload_resp.json()["processing_id"]

    resp = client.get(f"/api/images/{processing_id}/vehicle", headers=_auth_headers(registered_user_token))
    assert resp.status_code == 200
    body = resp.json()
    assert body["state"] == "Unknown"
    assert body["valid_format"] is False


def test_state_wise_analytics_endpoint(client, registered_user_token):
    resp = client.get("/api/analytics/state-wise", headers=_auth_headers(registered_user_token))
    assert resp.status_code == 200
    body = resp.json()
    assert "total_vehicles_detected" in body
    assert "by_state" in body


def test_state_wise_export_returns_csv(client, registered_user_token):
    resp = client.get("/api/analytics/state-wise/export", headers=_auth_headers(registered_user_token))
    assert resp.status_code == 200
    assert "text/csv" in resp.headers["content-type"]
    assert "state,vehicle_count" in resp.text
