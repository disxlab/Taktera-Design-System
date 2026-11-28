#!/usr/bin/env python3
"""Regression controls for signed vs unsigned NuGet hash semantics."""
import base64
import hashlib
import unittest
from dependency_licenses import verify_nuget_hashes

def b64(value):
    return base64.b64encode(value).decode("ascii")

class HashTests(unittest.TestCase):
    def setUp(self):
        self.archive=b"synthetic signed archive bytes"
        self.raw=hashlib.sha512(self.archive).digest()
        self.content=hashlib.sha512(b"synthetic unsigned content").digest()

    def verify(self, archive=None, raw=None, metadata=None, locked=None, sbom=None):
        return verify_nuget_hashes(
            self.archive if archive is None else archive,
            b64(self.raw) if raw is None else raw,
            {"contentHash":b64(self.content)} if metadata is None else metadata,
            b64(self.content) if locked is None else locked,
            self.content.hex() if sbom is None else sbom,"test/1")

    def test_signed_distinct_hashes(self):
        result=self.verify()
        self.assertFalse(result["contentHashMatchesRawArchive"])
        self.assertEqual(result["rawArchiveSha512"],self.raw.hex())

    def test_unsigned_equal_hashes(self):
        result=self.verify(metadata={"contentHash":b64(self.raw)},locked=b64(self.raw),sbom=self.raw.hex())
        self.assertTrue(result["contentHashMatchesRawArchive"])

    def test_modified_archive_rejected(self):
        with self.assertRaisesRegex(ValueError,"raw archive"):
            self.verify(archive=b"modified")

    def test_wrong_sidecar_rejected(self):
        with self.assertRaisesRegex(ValueError,"raw archive"):
            self.verify(raw=b64(self.content))

    def test_wrong_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError,"locked content"):
            self.verify(metadata={"contentHash":b64(self.raw)})

    def test_missing_metadata_rejected(self):
        with self.assertRaisesRegex(ValueError,"locked content"):
            self.verify(metadata={})

    def test_wrong_sbom_rejected(self):
        with self.assertRaisesRegex(ValueError,"SBOM content"):
            self.verify(sbom=self.raw.hex())

if __name__=="__main__":
    unittest.main(verbosity=2)
