import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

from app.main import app
from app.models.campaign import Campaign, create_campaign, get_campaign
from app.models.prospect import get_prospect, get_all_prospects

client = TestClient(app)


@pytest.fixture
def setup_test_campaign():
    """Sets up a test campaign for discovery tests."""
    c_id = "test_discovery_camp"
    existing = get_campaign(c_id)
    if not existing:
        c = Campaign(
            id=c_id,
            name="Test Discovery Campaign",
            description="Testing prospect discovery ingestion and pipeline trigger",
            icp="CTO / VP Engineering at SaaS companies, 50-500 employees, US-based",
            status="LIVE",
        )
        from app.models.campaign import _campaigns
        _campaigns[c_id] = c
    return c_id


class TestProspectDiscoveryIngestion:
    """Test suite for Prospect Discovery Ingestion endpoint."""

    def test_ingest_discovered_prospects_with_raw_data(self, setup_test_campaign):
        import uuid
        camp_id = setup_test_campaign
        rand_suffix = uuid.uuid4().hex[:4]
        test_email = f"sarah.{rand_suffix}@datacorp.io"
        payload = {
            "discovery_source": "LinkedIn Sales Nav Agent",
            "prospects": [
                {
                    "name": f"Sarah Jenkins {rand_suffix}",
                    "title": "VP of Engineering",
                    "company": f"DataCorp Systems {rand_suffix}",
                    "email": test_email,
                    "phone": "+14155551234",
                    "linkedin_url": f"https://linkedin.com/in/sarah-jenkins-{uuid.uuid4().hex[:4]}",
                    "company_size": "150 employees",
                    "domain": "datacorp.io",
                    "metadata": {
                        "funding": "Series B",
                        "tech_stack": ["Kubernetes", "AWS", "Python"],
                        "hiring": True,
                    },
                    "custom_discovery_score": 94,
                }
            ]
        }

        resp = client.post(f"/api/campaigns/{camp_id}/discovered-prospects", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["stored_count"] >= 1

        # Check saved prospect in database
        prospects = client.get(f"/api/campaigns/{camp_id}/discovered-prospects").json()
        matched = next((p for p in prospects if p["email"] == test_email), None)
        assert matched is not None
        assert matched["status"] == "DISCOVERED"
        assert matched["discovery_source"] == "LinkedIn Sales Nav Agent"
        assert matched["raw_data"]["custom_discovery_score"] == 94
        assert matched["raw_data"]["metadata"]["funding"] == "Series B"

    def test_deduplication_updates_existing_record(self, setup_test_campaign):
        camp_id = setup_test_campaign
        # First ingestion
        p1 = {
            "name": "Duplicate Test Lead",
            "title": "CTO",
            "company": "DupCorp",
            "email": "dup.test@dupcorp.com",
            "metadata": {"initial_scan": True},
        }
        client.post(f"/api/campaigns/{camp_id}/discovered-prospects", json={"prospects": [p1]})

        # Second ingestion with updated phone and new metadata
        p2 = {
            "name": "Duplicate Test Lead",
            "title": "CTO & Co-founder",
            "company": "DupCorp",
            "email": "dup.test@dupcorp.com",
            "phone": "+14155559999",
            "metadata": {"enrichment_round": 2},
        }
        resp = client.post(f"/api/campaigns/{camp_id}/discovered-prospects", json={"prospects": [p2]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated_count"] >= 1

        # Verify no duplicate was created
        all_prospects = client.get(f"/api/campaigns/{camp_id}/discovered-prospects").json()
        dup_matches = [p for p in all_prospects if p["email"] == "dup.test@dupcorp.com"]
        assert len(dup_matches) == 1
        assert dup_matches[0]["phone"] == "+14155559999"

    def test_ingest_missing_campaign_returns_404(self):
        resp = client.post("/api/campaigns/non_existent_camp_id/discovered-prospects", json={"prospects": []})
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestRunDiscoveryAgentCount:
    """Test suite for on-demand discovery agent trigger with user-specified count."""

    def test_run_discovery_with_specified_count(self, setup_test_campaign):
        camp_id = setup_test_campaign
        resp = client.post(
            f"/api/campaigns/{camp_id}/run-discovery",
            json={"count": 3, "criteria": "CTO at Series A SaaS"}
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["requested_count"] == 3
        assert len(data["prospects"]) == 3
        for p in data["prospects"]:
            assert p["status"] == "DISCOVERED"


class TestProspectStatusUpdate:
    """Test suite for PATCH /api/discovered-prospects/{prospect_id}."""

    def test_manager_select_and_reject_prospect(self, setup_test_campaign):
        camp_id = setup_test_campaign
        # Create a lead
        ingest_res = client.post(
            f"/api/campaigns/{camp_id}/discovered-prospects",
            json={"prospects": [{"name": "Status Lead", "email": "status.lead@test.com", "company": "TestCo"}]}
        ).json()
        prospect_id = ingest_res["prospects"][0]["id"]

        # 1. Mark as SELECTED
        patch_res = client.patch(f"/api/discovered-prospects/{prospect_id}", json={"status": "SELECTED"})
        assert patch_res.status_code == 200
        assert patch_res.json()["status"] == "SELECTED"

        # 2. Mark as REJECTED
        patch_res2 = client.patch(f"/api/discovered-prospects/{prospect_id}", json={"status": "REJECTED"})
        assert patch_res2.status_code == 200
        assert patch_res2.json()["status"] == "REJECTED"


class TestStartSdrPipelineAction:
    """Test suite for POST /api/campaigns/{campaign_id}/start-pipeline."""

    def test_start_pipeline_empty_prospects_validation(self, setup_test_campaign):
        camp_id = setup_test_campaign
        resp = client.post(f"/api/campaigns/{camp_id}/start-pipeline", json={"prospect_ids": []})
        assert resp.status_code == 400
        assert "at least one prospect" in resp.json()["detail"].lower()

    def test_start_pipeline_cross_campaign_isolation(self, setup_test_campaign):
        # Ingest prospect in us_saas_cto
        ingest_res = client.post(
            "/api/campaigns/us_saas_cto/discovered-prospects",
            json={"prospects": [{"name": "Isolated Lead", "email": "iso@test.com", "company": "IsoCorp"}]}
        ).json()
        p_id = ingest_res["prospects"][0]["id"]

        # Attempt to start in another campaign
        resp = client.post(f"/api/campaigns/{setup_test_campaign}/start-pipeline", json={"prospect_ids": [p_id]})
        assert resp.status_code == 400
        assert "belongs to campaign" in resp.json()["detail"].lower()

    @patch("app.routes.discovery.execute_sdr_pipeline")
    def test_start_pipeline_triggers_existing_sdr(self, mock_execute_sdr, setup_test_campaign):
        camp_id = setup_test_campaign
        # Create prospect
        ingest_res = client.post(
            f"/api/campaigns/{camp_id}/discovered-prospects",
            json={"prospects": [{"name": "Pipeline Lead", "email": "pipe@test.com", "company": "PipeCorp"}]}
        ).json()
        p_id = ingest_res["prospects"][0]["id"]

        # Mock SDR execution
        mock_rec = MagicMock()
        mock_rec.status = "SENT"
        mock_rec.execution_id = "mock-exec-001"
        mock_rec.actual_channel = "EMAIL"
        mock_rec.error = None
        mock_execute_sdr.return_value = mock_rec

        # Start SDR pipeline
        resp = client.post(f"/api/campaigns/{camp_id}/start-pipeline", json={"prospect_ids": [p_id]})
        assert resp.status_code == 200
        data = resp.json()
        assert data["success"] is True
        assert data["queued_count"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["status"] == "COMPLETED"
        assert mock_execute_sdr.called
