#!/usr/bin/env python3
"""Negative controls for the read-only static supply-chain gate."""
import copy
import json
import unittest
from check_supply_chain import ROOT, LOCK, inspect_workflow, inspect_npm_lock, inspect_nuget_lock
from verify_registry_fixture import npm_config, nuget_config

class PolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pins=json.loads(LOCK.read_text())["actions"]
        cls.wf=(ROOT/".github/workflows/taktera-beta-readiness.yml").read_text()
        cls.npm=json.loads((ROOT/"17_packages/react/package-lock.json").read_text())
        cls.native=json.loads((ROOT/"17_packages/avalonia/library/packages.lock.json").read_text())
    def reject_wf(self,text):
        with self.assertRaises(ValueError): inspect_workflow(text,self.pins)
    def test_real_workflow(self):
        self.assertGreater(inspect_workflow(self.wf,self.pins),0)
    def test_mutable_action(self):
        self.reject_wf(self.wf.replace("actions/checkout@"+self.pins["actions/checkout"]["sha"],"actions/checkout@v6",1))
    def test_unknown_commit(self):
        self.reject_wf(self.wf.replace(self.pins["actions/checkout"]["sha"],"0"*40,1))
    def test_write_permission(self):
        self.reject_wf(self.wf.replace("contents: read","contents: write",1))
    def test_checkout_credentials(self):
        self.reject_wf(self.wf.replace("persist-credentials: false","persist-credentials: true",1))
    def test_privileged_event(self):
        self.reject_wf(self.wf.replace("  pull_request:","  pull_request_target:",1))
    def test_secret_reference(self):
        self.reject_wf(self.wf+"\n      - run: echo $"+ "{{ secrets.TEST }}\n")
    def test_npm_wrong_source(self):
        lock=copy.deepcopy(self.npm)
        key=next(k for k in lock["packages"] if k)
        lock["packages"][key]["resolved"]="https://invalid.example/package.tgz"
        with self.assertRaises(ValueError): inspect_npm_lock(lock)
    def test_npm_missing_integrity(self):
        lock=copy.deepcopy(self.npm)
        key=next(k for k in lock["packages"] if k)
        lock["packages"][key]["integrity"]=""
        with self.assertRaises(ValueError): inspect_npm_lock(lock)
    def test_nuget_missing_hash(self):
        lock=copy.deepcopy(self.native)
        key=next(iter(lock["dependencies"]["net10.0"]))
        lock["dependencies"]["net10.0"][key]["contentHash"]=""
        with self.assertRaises(ValueError): inspect_nuget_lock(lock)
    def test_public_npm_fallback(self):
        with self.assertRaises(ValueError): npm_config("https://registry.npmjs.org/","TOKEN")
    def test_endpoint_newline(self):
        with self.assertRaises(ValueError): npm_config("https://registry.example/\nregistry=https://evil.example/","TOKEN")
    def test_token_variable_injection(self):
        with self.assertRaises(ValueError): npm_config("https://registry.example/","TOKEN}\nregistry=x")
    def test_non_loopback_http(self):
        with self.assertRaises(ValueError): nuget_config("http://192.0.2.1/index.json",["Avalonia"],loopback=True)
    def test_public_wildcard(self):
        with self.assertRaises(ValueError): nuget_config("https://registry.example/index.json",["*"])
    def test_private_public_mapping(self):
        with self.assertRaises(ValueError): nuget_config("https://registry.example/index.json",["TAKTERA.UI.AVALONIA"])
    def test_duplicate_public_mapping(self):
        with self.assertRaises(ValueError): nuget_config("https://registry.example/index.json",["Avalonia","avalonia"])

if __name__=="__main__": unittest.main(verbosity=2)
