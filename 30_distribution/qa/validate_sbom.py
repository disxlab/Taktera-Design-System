#!/usr/bin/env python3
"""Validate candidate SBOMs with pinned official JSON schemas, without remote $ref resolution."""
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import urlopen
from jsonschema import Draft7Validator
from referencing import Registry, Resource

SCHEMAS = {
    "cdx": ("https://raw.githubusercontent.com/CycloneDX/specification/1.6/schema/bom-1.6.schema.json", "3e92dddbc30cf7f6a02b80f0942b1a4cfd4fb1c26f1dfc4310afa9d613cafb93"),
    "cdx-spdx": ("https://raw.githubusercontent.com/CycloneDX/specification/1.6/schema/spdx.schema.json", "baa9d3bd1ed57b6751b0887edead6b5063ff53ff7429cf85d476c6c94af0166e"),
    "cdx-jsf": ("https://raw.githubusercontent.com/CycloneDX/specification/1.6/schema/jsf-0.82.schema.json", "8bae002c25e723db7ee1f26afde680ae1a2b1a8f6b4b4b0fd65dc3becb090aae"),
    "spdx": ("https://raw.githubusercontent.com/spdx/spdx-spec/v2.3/schemas/spdx-schema.json", "239208b7ac287b3cf5d9a9af23f9d69863971102a5e1587a27a398b43490b89b"),
}

def validate(out):
    registry = Registry()
    schemas = {}
    evidence = {}
    for key, (url, expected) in SCHEMAS.items():
        with urlopen(url, timeout=60) as response:
            data = response.read(2_000_001)
        if len(data)>2_000_000 or hashlib.sha256(data).hexdigest()!=expected:
            raise ValueError("Pinned schema checksum mismatch: "+key)
        doc = json.loads(data)
        Draft7Validator.check_schema(doc)
        registry = registry.with_resource(doc["$id"], Resource.from_contents(doc))
        schemas[key] = doc
        evidence[key] = {"url":url,"sha256":expected,"id":doc["$id"]}
    results = {}
    documents = sorted((out/"sbom").glob("*.cdx.json"))+[out/"sbom/product.cyclonedx.json",out/"sbom/product.spdx.json"]
    if len(documents)!=5:
        raise ValueError("Expected five SBOM documents")
    for path in documents:
        data=json.loads(path.read_text(encoding="utf-8"))
        validator=Draft7Validator(schemas["spdx" if path.name.endswith(".spdx.json") else "cdx"],registry=registry)
        validator.validate(data)
        results[path.name]={"status":"pass","sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
    summary=out/"sbom/product-summary.json"
    stats=json.loads(summary.read_text(encoding="utf-8"))
    stats["schemaValidation"]="passed"
    summary.write_text(json.dumps(stats,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    report={"status":"passed","schemaDialect":"draft-07","schemas":evidence,"documents":results,
            "scope":"JSON schema validation; not legal or semantic completeness certification"}
    (out/"sbom/schema-validation.json").write_text(json.dumps(report,indent=2,sort_keys=True)+"\n",encoding="utf-8")
    print(json.dumps({"schemaValidation":report},sort_keys=True))
    return stats
