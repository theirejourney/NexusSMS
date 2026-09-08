import unittest
import os
import tempfile
from core.listener import MessageHandler, handle_incoming_sms


class TestListener(unittest.TestCase):

    def setUp(self):
        self.db_fd, self.db_path = tempfile.mkstemp(suffix=".db")
        os.close(self.db_fd)
        self.callbacks_called = []

    def tearDown(self):
        os.unlink(self.db_path)

    def test_handle_message(self):
        handler = MessageHandler(db_path=self.db_path, print_output=False)
        result = handler.handle("Chase", "Your code is 1234", message_sid="SM001")
        self.assertEqual(result.extracted_code, "1234")
        self.assertEqual(handler.processed, 1)

    def test_callback_invoked(self):
        def my_cb(result, inserted):
            self.callbacks_called.append((result, inserted))
        handler = MessageHandler(db_path=self.db_path, callbacks=[my_cb], print_output=False)
        handler.handle("Chase", "Code 5678", message_sid="SM002")
        self.assertEqual(len(self.callbacks_called), 1)
        self.assertTrue(self.callbacks_called[0][1])

    def test_duplicate_no_callback_on_second(self):
        calls = []
        def my_cb(result, inserted):
            calls.append(inserted)
        handler = MessageHandler(db_path=self.db_path, callbacks=[my_cb], print_output=False)
        handler.handle("Chase", "Code 9999", message_sid="SM003")
        handler.handle("Chase", "Code 9999", message_sid="SM003")
        self.assertEqual(handler.duplicates, 1)

    def test_handle_incoming_sms_global(self):
        result = handle_incoming_sms("AWS", "Auth code 7777", db_path=self.db_path)
        self.assertEqual(result.extracted_code, "7777")


if __name__ == "__main__":
    unittest.main()
