#!/usr/bin/env python3
import copy
import unittest
from verify_br8_matrix import browser_report,native_report,SCENARIOS,EXPECTED_CHECKS,MATRIX_TESTS,BASELINE_TESTS

class EvidenceTests(unittest.TestCase):
    def setUp(self):
        self.actual={"sourceCommit":"a"*40,"githubRunId":"1","githubRunAttempt":"2","candidateManifestSha256":"b"*64,"canonicalPackages":{"Taktera.UI.Avalonia.4.0.0.nupkg":"c"*64}}
        self.digest="d"*64
        self.lock="e"*64
        identity={**self.actual,"dossierSha256":self.digest,"status":"passed","publicationAllowed":False}
        self.browser={**identity,"engine":"firefox","consumerLockSha256":self.lock,"errors":[],
                      "scenarios":[{"product":p,"theme":t,"status":"passed"} for p,t in sorted(SCENARIOS)],
                      "axe":[{"product":p,"theme":t,"page":"registry","violations":[],"incomplete":[]} for p,t in sorted(SCENARIOS)],
                      "checks":[{"name":n,"ok":True} for n in sorted(EXPECTED_CHECKS)]}
        self.browser["localizedAxe"]=[{"product":p,"theme":t,"locale":l,"surface":s,"violations":[],"incomplete":[]} for p,t in sorted(SCENARIOS) for l in ("en","ru") for s in ("transport","operations","web")]
        self.browser["performance"]={k:[{"product":p,"theme":t,"ms":10,**({"locale":l} if l else {})} for p,t in sorted(SCENARIOS) for l in (("en","ru") if k.endswith("SaveMs") else ("",))] for k in ("reactNavigationMs","webNavigationMs","reactSaveMs","webSaveMs")}
        self.native={**identity,"os":"windows","dependencyGraphMatch":True,
                     "package":{"name":"Taktera.UI.Avalonia.4.0.0.nupkg","sha256":"c"*64},
                     "scenarios":{n:"Passed" for n in MATRIX_TESTS},"totalTests":len(MATRIX_TESTS|BASELINE_TESTS),"performance":{"cleanConsumerWallSeconds":30}}
    def browser_ok(self,r):return browser_report(r,"firefox",self.actual,self.digest,self.lock)
    def native_ok(self,r):return native_report(r,"windows",self.actual,self.digest)
    def test_valid(self):
        self.assertEqual(self.browser_ok(self.browser)["axeScans"],12)
        self.assertEqual(self.browser_ok(self.browser)["performance"]["reactSaveMs"]["p50Ms"],10)
        self.assertEqual(self.native_ok(self.native)["tests"],29)
    def test_browser_negatives(self):
        for label,mutate in (
            ("wrong attempt",lambda r:r.update(githubRunAttempt="3")),
            ("wrong engine",lambda r:r.update(engine="chromium")),
            ("wrong digest",lambda r:r.update(dossierSha256="0"*64)),
            ("wrong lock",lambda r:r.update(consumerLockSha256="0"*64)),
            ("wrong packages",lambda r:r.update(canonicalPackages={})),
            ("publication",lambda r:r.update(publicationAllowed=True)),
            ("missing scenario",lambda r:r["scenarios"].pop()),
            ("duplicate scan",lambda r:r["axe"].__setitem__(0,r["axe"][1])),
            ("violation",lambda r:r["axe"][0].update(violations=[{"id":"x"}])),
            ("missing check",lambda r:r["checks"].pop()),
            ("missing RU transport",lambda r:r["checks"].__setitem__(next(i for i,c in enumerate(r["checks"]) if " ru transport " in c["name"]),{"name":"unrelated","ok":True})),
            ("extra space in transport name",lambda r:next(c for c in r["checks"] if " en transport locale" in c["name"]).update(name="beauty/dark en transport  locale")),
            ("duplicate check",lambda r:r["checks"].__setitem__(0,copy.deepcopy(r["checks"][1]))),
            ("missing localized CSV",lambda r:r["checks"].__setitem__(next(i for i,c in enumerate(r["checks"]) if c["name"].endswith("ru operations csv exact bytes")),{"name":"unrelated","ok":True})),
            ("missing standalone transport",lambda r:r["checks"].__setitem__(next(i for i,c in enumerate(r["checks"]) if c["name"].endswith("ru web transport retry")),{"name":"unrelated","ok":True})),
            ("missing series",lambda r:r["checks"].__setitem__(next(i for i,c in enumerate(r["checks"]) if c["name"].endswith("ru operations atomic series create")),{"name":"unrelated","ok":True})),
            ("missing keyboard check",lambda r:r["checks"].pop(next(i for i,c in enumerate(r["checks"]) if c["name"].endswith("keyboard save")))),
            ("boolean perf",lambda r:r["performance"]["webSaveMs"][0].update(ms=True)),
            ("missing perf sample",lambda r:r["performance"]["reactSaveMs"].pop()),
            ("slow perf",lambda r:[v.update(ms=99999) for v in r["performance"]["webNavigationMs"]]),
            ("nonfinite perf",lambda r:r["performance"]["webSaveMs"][0].update(ms=float("nan"))),
            ("missing localized axe",lambda r:r["localizedAxe"].pop()),
            ("localized axe violation",lambda r:r["localizedAxe"][0].update(violations=[{"id":"test"}])),
            ("failed check",lambda r:r["checks"][0].update(ok=False)),
            ("errors",lambda r:r.update(errors=["crash"]))):
            with self.subTest(label=label):
                record=copy.deepcopy(self.browser);mutate(record)
                with self.assertRaises(ValueError):self.browser_ok(record)
    def test_native_negatives(self):
        for label,mutate in (
            ("wrong OS",lambda r:r.update(os="macos")),
            ("wrong run",lambda r:r.update(githubRunId="8")),
            ("bad graph",lambda r:r.update(dependencyGraphMatch=False)),
            ("wrong package",lambda r:r["package"].update(sha256="0"*64)),
            ("missing test",lambda r:r["scenarios"].pop(next(iter(r["scenarios"])))),
            ("slow native",lambda r:r["performance"].update(cleanConsumerWallSeconds=901)),
            ("false count",lambda r:r.update(totalTests=28))):
            with self.subTest(label=label):
                record=copy.deepcopy(self.native);mutate(record)
                with self.assertRaises(ValueError):self.native_ok(record)
if __name__=="__main__":unittest.main()
