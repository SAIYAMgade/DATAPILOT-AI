import pytest


def test_health_check(client):
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["database_connected"] is True


def test_metrics_summary_endpoint(client, seed_controlled_data):
    res = client.get("/api/metrics/summary")
    assert res.status_code == 200
    data = res.json()
    assert "metrics" in data
    assert "total_revenue" in data["metrics"]


def test_customers_list_endpoint(client, seed_controlled_data):
    res = client.get("/api/customers?page=1&page_size=10")
    assert res.status_code == 200
    data = res.json()
    assert "customers" in data
    assert len(data["customers"]) == 3
    assert data["total_count"] == 3


def test_cohorts_matrix_endpoint(client, seed_controlled_data):
    res = client.get("/api/cohorts/matrix")
    assert res.status_code == 200
    data = res.json()
    assert "retention_matrix" in data


def test_segmentation_endpoint(client, seed_controlled_data):
    res = client.get("/api/segmentation/rfm")
    assert res.status_code == 200
    data = res.json()
    assert "summary" in data


def test_stats_endpoint(client, seed_controlled_data):
    res = client.get("/api/stats/confidence-intervals")
    assert res.status_code == 200
    data = res.json()
    assert "average_order_value" in data


def test_assistant_query_endpoint(client, seed_controlled_data):
    res = client.post("/api/assistant/query", json={"question": "What is total revenue?"})
    assert res.status_code == 200
    data = res.json()
    assert "answer" in data
    assert "revenue" in data["answer"].lower()
