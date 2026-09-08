import unittest
from core.extractor import parse_message, register_rule, remove_rule, list_rules


class TestExtractor(unittest.TestCase):

    def test_banking_code_extraction(self):
        result = parse_message("Chase", "Your Chase verification code is 123456.")
        self.assertEqual(result.category, "banking")
        self.assertEqual(result.extracted_code, "123456")

    def test_tech_code_extraction(self):
        result = parse_message("GitHub", "Your GitHub authentication code is 987654.")
        self.assertEqual(result.category, "tech")
        self.assertEqual(result.extracted_code, "987654")

    def test_general_fallback(self):
        result = parse_message("Unknown", "Your code is 5555.")
        self.assertEqual(result.category, "general")
        self.assertEqual(result.extracted_code, "5555")

    def test_no_general_fallback(self):
        result = parse_message("Unknown", "Your code is 5555.", general_fallback=False)
        self.assertIsNone(result.extracted_code)

    def test_multiple_candidates(self):
        result = parse_message("Chase", "Codes: 1111 and 2222")
        self.assertEqual(result.all_candidates, ("1111", "2222"))

    def test_register_custom_rule(self):
        register_rule("crypto", ["Coinbase"], r"(?:code|verify)[^0-9]{0,10}([0-9]{4,8})")
        result = parse_message("Coinbase", "Your Coinbase code 90210")
        self.assertEqual(result.category, "crypto")
        self.assertEqual(result.extracted_code, "90210")
        remove_rule("crypto")

    def test_cannot_remove_general(self):
        with self.assertRaises(ValueError):
            remove_rule("general")

    def test_list_rules(self):
        rules = list_rules()
        self.assertIn("banking", rules)
        self.assertIn("general", rules)


if __name__ == "__main__":
    unittest.main()
