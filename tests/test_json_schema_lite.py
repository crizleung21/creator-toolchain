from __future__ import annotations
import unittest
from scripts.json_schema_lite import validate
class JsonSchemaLiteTests(unittest.TestCase):
    def test_required_const_and_additional_properties(self):
        schema={"type":"object","additionalProperties":False,"required":["version"],"properties":{"version":{"const":"0.4.0"}}}
        self.assertEqual(validate({"version":"0.4.0"},schema),[])
        findings=validate({"version":"0.3.0","extra":1},schema)
        self.assertTrue(any("must equal" in f for f in findings)); self.assertTrue(any("unexpected property" in f for f in findings))
    def test_arrays_enforce_uniqueness_and_items(self):
        schema={"type":"array","uniqueItems":True,"items":{"type":"string"}}
        self.assertTrue(validate(["a","a"],schema)); self.assertTrue(validate([1],schema))
if __name__=='__main__': unittest.main()
