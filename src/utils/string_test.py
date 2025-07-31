import unittest

from .string import clean_json


class TestCleanJson(unittest.TestCase):
    def test_markdown_json_block(self):
        s = """Sure, here is the json:\n```json\n{\n  \"a\": 1, \"b\": 2\n}\n```"""
        self.assertEqual(clean_json(s), {"a": 1, "b": 2})

    def test_markdown_code_block(self):
        s = """Here is the data:\n```\n{\n  \"x\": 42, \"y\": [1,2,3]\n}\n```"""
        self.assertEqual(clean_json(s), {"x": 42, "y": [1, 2, 3]})

    def test_raw_json(self):
        s = '{"foo": "bar", "baz": 123}'
        self.assertEqual(clean_json(s), {"foo": "bar", "baz": 123})

    def test_json_in_middle_of_text(self):
        s = 'The answer is: {"k": 9, "l": 8} and that\'s it.'
        self.assertEqual(clean_json(s), {"k": 9, "l": 8})

    def test_json_array(self):
        s = """Here's a list:\n```json\n[1, 2, 3, 4]\n```"""
        self.assertEqual(clean_json(s), [1, 2, 3, 4])

    def test_json_array_raw(self):
        s = '[{"a":1},{"b":2}]'
        self.assertEqual(clean_json(s), [{"a": 1}, {"b": 2}])

    def test_json_with_trailing_comma(self):
        s = '{"a": 1, "b": 2,}'
        self.assertEqual(clean_json(s), {"a": 1, "b": 2})

    def test_json_with_extra_text(self):
        s = 'Some intro.\n```json\n{\n  "a": 1,\n  "b": 2\n}\n```\nSome outro.'
        self.assertEqual(clean_json(s), {"a": 1, "b": 2})

    def test_json_with_no_code_block(self):
        s = 'Here is the object: {\n  "a": 1,\n  "b": 2\n}'
        self.assertEqual(clean_json(s), {"a": 1, "b": 2})

    def test_json_with_array_in_text(self):
        s = "The data is: [1,2,3] and more text."
        self.assertEqual(clean_json(s), [1, 2, 3])

    def test_invalid_json(self):
        s = "not a json"
        with self.assertRaises(Exception):
            clean_json(s)


if __name__ == "__main__":
    unittest.main()
