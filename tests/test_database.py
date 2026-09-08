import unittest
import os
import tempfile
from core.database import init_db, insert_message, is_duplicate, get_messages, get_latest_code, log_message


class TestDatabase(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        init_db(self.db_path)

    def tearDown(self):
        os.unlink(self.db_path)

    def test_insert_and_retrieve(self):
        inserted = insert_message(
            provider="twilio", provider_message_id="SM123",
            sender="Chase", recipient="+1234567890", category="banking",
            extracted_code="1234", raw_body="Your code is 1234",
            raw_payload={"foo": "bar"}, db_path=self.db_path,
        )
        self.assertTrue(inserted)
        rows = get_messages(db_path=self.db_path)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["sender"], "Chase")

    def test_duplicate_prevention(self):
        insert_message(
            provider="twilio", provider_message_id="SM123",
            sender="Chase", recipient=None, category="banking",
            extracted_code="1234", raw_body="Code 1234", db_path=self.db_path,
        )
        inserted2 = insert_message(
            provider="twilio", provider_message_id="SM123",
            sender="Chase", recipient=None, category="banking",
            extracted_code="1234", raw_body="Code 1234", db_path=self.db_path,
        )
        self.assertFalse(inserted2)
        self.assertTrue(is_duplicate("twilio", "SM123", db_path=self.db_path))

    def test_log_message_backward_compat(self):
        log_message(
            sender="PayPal", category="banking", extracted_code="5678",
            raw_body="PayPal code: 5678", message_sid="SM999", db_path=self.db_path,
        )
        rows = get_messages(db_path=self.db_path)
        self.assertEqual(rows[0]["provider"], "twilio")

    def test_case_insensitive_sender_search(self):
        insert_message(
            provider="twilio", provider_message_id="SM003",
            sender="ChaseBank", recipient=None, category="banking",
            extracted_code="9999", raw_body="Code 9999", db_path=self.db_path,
        )
        rows = get_messages(sender="chase", db_path=self.db_path)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
