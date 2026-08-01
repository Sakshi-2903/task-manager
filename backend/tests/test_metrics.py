def test_metrics_endpoint_exposes_prometheus_metrics(client):
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.mimetype.startswith("text/plain")
    assert "http_requests_total" in response.get_data(as_text=True)
