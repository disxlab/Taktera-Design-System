#!/usr/bin/env python3
import copy
import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from prepare_br9_manual import template,verify_manual,cases
from verify_candidate_download import sha
class ManualEvidenceTests(unittest.TestCase):
    def test_fail_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            summary=p/"summary.json";record=p/"manual.json"
            summary.write_text(json.dumps({"status":"automated-matrix-passed","publicationAllowed":False,"sourceCommit":"a"*40,"githubRunId":"1","githubRunAttempt":"1","candidateManifestSha256":"b"*64,"canonicalPackages":{"example":"c"*64}}))
            with contextlib.redirect_stdout(io.StringIO()):template(summary,record)
            original=json.loads(record.read_text())
            self.assertEqual(len(original["records"]),726)
            self.assertEqual(len({c["id"] for c in cases()}),726)
            self.assertTrue(all(r["status"]=="NOT RUN" for r in original["records"]))
            with self.assertRaises(ValueError):verify_manual(summary,record,p)
            # Synthetic structural test only: these are never real acceptance records.
            evidence=p/"fixture.txt";evidence.write_text("Synthetic validator fixture; not acceptance evidence.")
            good=copy.deepcopy(original)
            for row in good["records"]:
                row.update(status="PASS",tester="synthetic fixture",date="2026-11-28",environment="synthetic",notes="validator only",evidence=[{"file":"fixture.txt","sha256":sha(evidence.read_bytes())}])
            record.write_text(json.dumps(good))
            with contextlib.redirect_stdout(io.StringIO()):verify_manual(summary,record,p)
            for label,change in (
                ("missing case",lambda r:r["records"].pop()),
                ("duplicate",lambda r:r["records"].append(r["records"][0])),
                ("failed",lambda r:r["records"][0].update(status="FAIL")),
                ("missing evidence",lambda r:r["records"][0].update(evidence=[])),
                ("wrong run",lambda r:r.update(githubRunId="2")),
                ("wrong digest",lambda r:r["records"][0]["evidence"][0].update(sha256="0"*64)),
                ("approval claim",lambda r:r.update(publicationAllowed=True))):
                with self.subTest(label=label):
                    bad=copy.deepcopy(good);change(bad);record.write_text(json.dumps(bad))
                    with self.assertRaises(ValueError):verify_manual(summary,record,p)
if __name__=="__main__":unittest.main()
