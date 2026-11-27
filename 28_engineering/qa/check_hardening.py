#!/usr/bin/env python3
"""BR4 regression guards. Does not replace native XAML compiler or runtime QA."""
import shutil, subprocess, sys, tempfile, xml.etree.ElementTree as ET
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
A = ROOT / "17_packages/avalonia"
NS = "{https://github.com/avaloniaui}"
def require(ok, message):
    if not ok:
        raise AssertionError(message)
def root(p): return ET.parse(p).getroot()
for name, expected in (("TkControls.axaml", "ResourceDictionary"), ("TkFieldStyles.axaml", "Styles")):
    canonical, sample = A/name, A/"sample/Assets"/name
    require(canonical.read_bytes() == sample.read_bytes(), f"Sample drift: {name}")
    for path in (canonical, sample):
        doc = root(path)
        require(doc.tag == NS+expected, f"Wrong root: {path}")
        if expected == "ResourceDictionary":
            require(not any(child.tag == NS+"Style" for child in doc), f"Unkeyed top-level Style: {path}")
app = root(A/"sample/App.axaml")
require(any(e.tag == NS+"StyleInclude" and e.get("Source","").endswith("/TkFieldStyles.axaml") for e in app.iter()), "Missing StyleInclude")
require(any(e.tag == NS+"ResourceInclude" and e.get("Source","").endswith("/TkControls.axaml") for e in app.iter()), "Missing ResourceInclude")
# Synthetic negative control for the exact AVLN3000 regression.
def valid_resource(doc): return doc.tag == NS+"ResourceDictionary" and not any(e.tag == NS+"Style" for e in doc)
require(not valid_resource(ET.fromstring('<ResourceDictionary xmlns="https://github.com/avaloniaui"><Style Selector="Button"/></ResourceDictionary>')), "Negative control failed")
require(valid_resource(root(A/"TkControls.axaml")), "Control themes invalid")
with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    for rel in ("25_internal_completion/src","25_internal_completion/generated","27_beta_readiness_3/avalonia_compat"):
        shutil.copytree(ROOT/rel,tmp/rel)
    rel = "27_beta_readiness_3/generate_avalonia_compat.py"
    shutil.copy2(ROOT/rel,tmp/rel)
    for script in ("25_internal_completion/src/build_tokens.py",rel):
        subprocess.run([sys.executable,str(tmp/script)],check=True,cwd=tmp)
    for rel in ("25_internal_completion/generated","27_beta_readiness_3/avalonia_compat"):
        old,new=ROOT/rel,tmp/rel
        old_files={p.relative_to(old) for p in old.rglob("*") if p.is_file()}
        new_files={p.relative_to(new) for p in new.rglob("*") if p.is_file()}
        require(old_files == new_files,f"Generated file set drift: {rel}")
        for f in old_files:
            require((old/f).read_bytes() == (new/f).read_bytes(),f"Generated token drift: {rel}/{f}")
require((A/"sample/Assets/Taktera.Clinic.Light.axaml").read_bytes()==(ROOT/"27_beta_readiness_3/avalonia_compat/Taktera.Clinic.Light.axaml").read_bytes(),"Sample token dictionary drift")
print("BR4 XAML / deterministic tokens / negative control: PASS")
