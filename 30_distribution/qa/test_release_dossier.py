#!/usr/bin/env python3
"""Regression tests: API contract data survives a JSON artifact round trip."""
import copy
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from verify_version_policy import contract, inventory, compare
from verify_candidate_download import sha
from generate_release_dossier import validate_reports, PLAN_NEG, ROLLBACK_NEG, ROLLBACK_CONSUMERS, VERSION_NEG, BLOCKERS

class DossierTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.path=self.root/"Taktera.UI.Avalonia.4.0.0-beta-readiness.3.nupkg"
        with zipfile.ZipFile(self.path,"w") as z:
            z.writestr("Taktera.UI.Avalonia.nuspec",'<package xmlns="http://schemas.microsoft.com/packaging/2013/05/nuspec.xsd"><metadata><id>Taktera.UI.Avalonia</id><version>4.0.0-beta-readiness.3</version><dependencies><group targetFramework="net10.0"><dependency id="Avalonia" version="[11.3.22, )" /></group><dependency id="Example" version="1.0.0" /></dependencies></metadata></package>')
            z.writestr("lib/net10.0/Taktera.UI.Avalonia.xml",'<doc><assembly><name>Taktera.UI.Avalonia</name></assembly><members><member name="T:Taktera.UI.Example" /></members></doc>')
            z.writestr("lib/net10.0/Taktera.UI.Avalonia.dll",b"synthetic fixture; not a real DLL")
        hashes={self.path.name:sha(self.path.read_bytes())}
        self.packages=inventory(self.root,hashes)
        self.actual={"sourceCommit":"a"*40,"githubRunId":"123","githubRunAttempt":"1","canonicalPackages":hashes,"candidateManifestSha256":"b"*64}
        common={k:self.actual[k] for k in ("sourceCommit","githubRunId","githubRunAttempt")}
        self.baseline={"canonicalPackages":dict(hashes),"sourceCommit":"c"*40,"githubRunId":"122"}
        self.plan=dict(common,status="preflight-passed",mode="plan-only",publicationAllowed=False,
                       canonicalPackages=hashes,candidateManifestSha256="b"*64,signed=False,licenseReview="pending",registryPublished=False,
                       blockers=BLOCKERS,negativeControls=sorted(PLAN_NEG))
        self.rollback=dict(common,status="passed",publicationAllowed=False,currentPackages=hashes,historicalPackages=hashes,
                           historicalSourceCommit="c"*40,historicalRunId="122",productionRollbackTested=False,
                           registryOverwriteAllowed=False,negativeControls=sorted(ROLLBACK_NEG),
                           restoredConsumerChecks=sorted(ROLLBACK_CONSUMERS),sameVersionDifferentBytes=[])
        self.versions=dict(common,status="passed",publicationAllowed=False,canonicalPackages=hashes,candidateManifestSha256="b"*64,
                           historicalSourceCommit="c"*40,apiDifferences={},promotionAllowed=False,signed=False,
                           versions={k:v["version"] for k,v in self.packages.items()},
                           apiContracts={k:v["api"] for k,v in self.packages.items()},sameVersionDifferentBytes=[],
                           negativeControls=sorted(VERSION_NEG))
    def test_native_contract_json_roundtrip(self):
        key,version,api=contract(self.path)
        self.assertEqual(api,json.loads(json.dumps(api)))
        self.assertEqual(api["dependencyGroups"],[["net10.0","avalonia","[11.3.22, )"]])
        self.assertEqual(api["directDependencies"],[["example","1.0.0"]])
    def test_inventory_json_roundtrip(self):
        self.assertEqual(compare(self.packages,json.loads(json.dumps(self.packages))),{})
    def test_cross_job_dossier_accepts_serialized_contract(self):
        validate_reports(self.actual,self.packages,*json.loads(json.dumps([self.plan,self.rollback,self.versions])),self.baseline)
    def test_cross_job_dossier_rejects_changed_dependency(self):
        modified=json.loads(json.dumps(self.versions))
        modified["apiContracts"]["nuget:taktera.ui.avalonia"]["dependencyGroups"][0][2]="99.0.0"
        with self.assertRaisesRegex(ValueError,"Version archive contracts differ"):
            validate_reports(self.actual,self.packages,self.plan,self.rollback,modified,self.baseline)
    def test_cross_job_dossier_rejects_missing_member(self):
        modified=copy.deepcopy(self.versions)
        modified["apiContracts"]["nuget:taktera.ui.avalonia"]["documentedMemberIds"]=[]
        with self.assertRaisesRegex(ValueError,"Version archive contracts differ"):
            validate_reports(self.actual,self.packages,self.plan,self.rollback,modified,self.baseline)

if __name__=="__main__": unittest.main(verbosity=2)
