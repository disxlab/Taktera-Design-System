#!/usr/bin/env python3
"""Fail-closed native evidence tests using synthetic TRX only."""
import tempfile
import unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from verify_br8_native import validate_trx, BASELINE_TESTS, MATRIX_TESTS
class NativeEvidenceTests(unittest.TestCase):
    def exercise(self, rows):
        with tempfile.TemporaryDirectory() as temp:
            p=Path(temp)/"consumer.trx"
            root=ET.Element("TestRun",xmlns="http://microsoft.com/schemas/VisualStudio/TeamTest/2010")
            results=ET.SubElement(root,"Results")
            for name,outcome in rows:
                ET.SubElement(results,"UnitTestResult",testName="Taktera.HeadlessTests."+name,outcome=outcome)
            ET.ElementTree(root).write(p,encoding="utf-8")
            return validate_trx(p)
    def valid(self):
        return [(name,"Passed") for name in sorted(BASELINE_TESTS|MATRIX_TESTS)]
    def test_complete(self):
        self.assertEqual(set(self.exercise(self.valid())),MATRIX_TESTS)
    def test_missing_baseline(self):
        with self.assertRaises(ValueError):
            self.exercise([r for r in self.valid() if r[0] not in BASELINE_TESTS])
    def test_missing_matrix(self):
        rows=self.valid()
        with self.assertRaises(ValueError):
            self.exercise([r for r in rows if r[0]!="Clinic_Dark_ru"])
    def test_duplicate(self):
        rows=self.valid()
        with self.assertRaises(ValueError):
            self.exercise(rows+[rows[0]])
    def test_substituted_name(self):
        rows=self.valid()
        with self.assertRaises(ValueError):
            self.exercise(rows[:-1]+[("UnrelatedTest","Passed")])
    def test_failed(self):
        rows=self.valid()
        with self.assertRaises(ValueError):
            self.exercise(rows[:-1]+[(rows[-1][0],"Failed")])
    def test_skipped(self):
        rows=self.valid()
        with self.assertRaises(ValueError):
            self.exercise(rows[:-1]+[(rows[-1][0],"NotExecuted")])
if __name__=="__main__":
    unittest.main()
