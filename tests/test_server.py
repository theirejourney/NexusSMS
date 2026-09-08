import unittest
import os
import tempfile
import json
from fastapi.testclient import TestClient
from core.database import init_db


class TestServer(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        os.environ["NEXUSSMS_DB"] = self.db_path

        self.config_fd, self.config_path = tempfile.mkstemp(suffix=".json")
        os.close(self.config_fd)
        config = {
            "providers": {
                "generic": {
                    "enabled": True,
                    "secret": "test-secret",
                    "auth_type": "api_key"
                }
            }
        }
        with open(self.config_path, "w") as f:
            json.dump(config, f)
        os.environ["NEXUSSMS_CONFIG"] = self.config_path

        init_db(self.db_path)

        from core.server import app
        self.client = TestClient(app)

    def tearDown(self):
        os.unlink(self.db_path)
        os.unlink(self.config_path)

    def test_health_endpoint(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_webhook_invalid_provider(self):
        response = self.client.post("/webhook/unknown_provider", json={})
        self.assertEqual(response.status_code, 404)

    def test_webhook_generic_api_key(self):
        response = self.client.post(
            "/webhook/generic",
            json={"id": "msg-001", "from": "Test", "to": "+1", "body": "Code 1234", "text": "Code 1234"},
            headers={"X-API-Key": "test-secret"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_webhook_generic_bad_auth(self):
        response = self.client.post(
            "/webhook/generic",
            json={"id": "msg-002", "from": "Test", "body": "Code 1234"},
            headers={"X-API-Key": "wrong-secret"}
        )
        self.assertEqual(response.status_code, 401)

    def test_query_messages(self):
        self.client.post(
            "/webhook/generic",
            json={"id": "msg-003", "from": "Chase", "body": "Code 5555", "text": "Code 5555"},
            headers={"X-API-Key": "test-secret"}
        )
        response = self.client.get("/messages?sender=chase")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["extracted_code"], "5555")


if __name__ == "__main__":
    unittest.main()
