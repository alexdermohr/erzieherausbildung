import json
import re
import sys
import importlib.util
from pathlib import Path

root = Path(__file__).resolve().parents[1]
DOC = re.compile(r"^doc-\d{3}$")
SKIP = {".git", "source-material.local", "machine-readable.local"}
RAW = {".pdf", ".docx", ".pptx", ".m4a", ".heic", ".jpg", ".jpeg", ".png"}
STATUS = {"learned", "background"}
BRIDGE_TYPES = {"enables", "frames", "requires_precision", "leads_to_action", "stabilizes", "communicates"}

def j(path):
    return json.loads((root / path).read_text(encoding="utf-8"))

def must_exist(path):
    assert (root / path).exists(), f"missing {path}"

def check_doc(value, valid, where):
    assert isinstance(value, str), f"{where}: source id must be string"
    assert DOC.match(value), f"{where}: invalid source id {value!r}"
    assert value in valid, f"{where}: unknown source id {value!r}"

required = [
    "README.md",
    "data/module-map.json",
    "data/source-summary.json",
    "data/source-health.v1.json",
    "data/machine-readable-inventory.json",
    "data/learning-map.v1.json",
    "data/pilot-index.v1.json",
    "data/detail-bridge-index.v1.json",
    "data/details/index.v1.json",
    "data/details/backlog.v1.json",
    "data/surface-policy.v1.json",
    "docs/implementation-plan.md",
    "docs/learning-map-v1.md",
    "docs/pilot-index-v1.md",
    "docs/detail-bridge-index-v1.md",
    "docs/surface-policy-v1.md",
    "schemas/learning-map.v1.schema.json",
    "schemas/detail.v1.schema.json",
    "schemas/detail-backlog.v1.schema.json",
    "schemas/surface-policy.v1.schema.json",
    "visuals/learning-map-v1.canvas",
    "scripts/obsidian_views.py",
    "scripts/build_pilot_index.py",
    "scripts/build_detail_bridge_index.py",
    "scripts/validate_details.py",
    "scripts/validate_detail_source_alignment.py",
    "scripts/validate_detail_backlog.py",
    "scripts/validate_view_export.py",
    "scripts/validate_source_health.py",
    "docs/obsidian-vault-spiegel.md",
]
for path in required:
    must_exist(path)

for path in root.rglob("*"):
    if any(part in SKIP for part in path.parts):
        continue
    if path.is_file() and path.suffix.lower() in RAW:
        raise AssertionError(f"raw artifact committed: {path}")

ss = j("data/source-summary.json")
assert ss["schema"] == "erzieherausbildung.source-summary.v2"
assert ss["sourceRootName"] == "erzieherausbildung"
assert ss["totals"]["files"] == 29
assert ss["totals"]["extensions"] == {"pdf": 29}

inv = j("data/machine-readable-inventory.json")
assert inv["schema"] == "erzieherausbildung.machine_readable_inventory.v2"
assert inv["raw_text_committed"] is False
assert inv["local_output_root"] == "machine-readable.local"
assert inv["document_count"] == 29
assert inv["totals"]["word_count"] == 325811
assert inv["totals"]["statuses"] == {"ok": 18, "ok-pagewise": 6, "ok-ocr": 5}
valid_docs = {"doc-%03d" % doc["ordinal"] for doc in inv["documents"]}

mm = j("data/module-map.json")
assert len(mm["modules"]) == 6
assert len(mm["axes"]) == 7

contract = j("schemas/learning-map.v1.schema.json")
assert contract["schema"] == "erzieherausbildung.learning_map.contract.v1"
assert contract["dataSchema"] == "erzieherausbildung.learning_map.v1"
assert contract["allowedStatuses"] == sorted(STATUS)
assert contract["sourceRefPattern"] == "doc-XXX"
assert contract["rawTextCommitted"] is False

# learning map validation follows
learning_path = "data/" + "learning-map.v1.json"
lrn = j(learning_path)
assert len(lrn) > 0
assert lrn["schema"] == "erzieherausbildung.learning_map.v1"
assert lrn["purpose"].strip()
policy = lrn["source_policy"]
assert policy["raw_text_committed"] is False
assert "committed_source_refs" in policy
axes = lrn["axes"]
assert len(axes) == 8
axis_ids = [a["id"] for a in axes]
assert len(axis_ids) == len(set(axis_ids))
topic_sources = set()
topic_count = 0
status_counts = {s: 0 for s in STATUS}
doc003_links = 0
for axis in axes:
    aid = axis.get("id", "?")
    for key in ["id", "title", "status", "sources", "summary", "topics"]:
        assert key in axis, f"axis missing {key}: {aid}"
    assert axis["status"] in STATUS
    status_counts[axis["status"]] += 1
    assert axis["sources"]
    for source in axis["sources"]:
        check_doc(source, valid_docs, "axis " + aid)
    assert axis["topics"]
    for item in axis["topics"]:
        iid = item.get("id", "?")
        topic_count += 1
        for key in ["id", "title", "status", "sources"]:
            assert key in item, f"topic missing {key}: {iid}"
        assert item["status"] in STATUS
        status_counts[item["status"]] += 1
        assert item["sources"]
        for source in item["sources"]:
            check_doc(source, valid_docs, "item " + iid)
            topic_sources.add(source)
        if "doc-003" in item["sources"]:
            pass

assert topic_count >= 40
coverage = lrn["coverage"]
assert coverage["linked_doc_ids"] == sorted(topic_sources)
canvas = j("visuals/learning-map-v1.canvas")
assert len(canvas["nodes"]) >= 40
assert len(canvas["edges"]) >= 8
system_canvas = j("visuals/erzieherausbildung-systemkarte.canvas")
required_system_nodes = {"source-boundary", "source-ids", "learning-map", "knowledge-network", "web-surface", "canvas-surface", "miro-surface", "docs-review", "validation"}
system_node_ids = {node["id"] for node in system_canvas["nodes"]}
assert required_system_nodes <= system_node_ids
required_system_edges = {("source-boundary", "source-ids"), ("source-ids", "learning-map"), ("learning-map", "knowledge-network"), ("knowledge-network", "web-surface"), ("learning-map", "canvas-surface"), ("canvas-surface", "miro-surface"), ("validation", "docs-review")}
system_edges = {(edge["fromNode"], edge["toNode"]) for edge in system_canvas["edges"]}
assert required_system_edges <= system_edges

net = j("data/knowledge-network.v1.json")
net_contract = j("schemas/knowledge-network.v1.schema.json")
assert net["schema"] == "erzieherausbildung.knowledge_network.v1"
assert net["source_model"] == "data/learning-map.v1.json"
assert net["source_policy"]["raw_text_committed"] is False
assert net_contract["dataSchema"] == net["schema"]
assert net_contract["bridgeTypeField"] == "type"
assert set(net_contract["allowedBridgeTypes"]) == BRIDGE_TYPES
assert len(net["clusters"]) == net_contract["clusterCount"] == 7
cluster_ids = {cluster["id"] for cluster in net["clusters"]}
network_topics = []
network_sources = set()
for cluster in net["clusters"]:
    assert cluster["topics"]
    assert cluster["insight"].strip()
    network_topics.extend(cluster["topics"])
    for source in cluster["sources"]:
        check_doc(source, valid_docs, "knowledge-network " + cluster["id"])
        network_sources.add(source)
assert len(network_topics) == net_contract["topicCount"] == 44
assert len(network_topics) == len(set(network_topics))
learning_topics = {topic["title"] for axis in axes for topic in axis["topics"]}
assert set(network_topics) == learning_topics
for bridge in net["bridges"]:
    assert bridge["from"] in cluster_ids
    assert bridge["to"] in cluster_ids
    assert bridge["type"] in BRIDGE_TYPES
    assert bridge["relation"].strip()
assert net["coverage"]["topic_count"] == len(network_topics)
assert (root / "docs/knowledge-network-v1.md").exists()
surface = j("data/surface-policy.v1.json")
surface_contract = j("schemas/surface-policy.v1.schema.json")
assert surface["schema"] == "erzieherausbildung.surface_policy.v1"
assert surface_contract["schema"] == "erzieherausbildung.surface_policy.contract.v1"
assert surface_contract["dataSchema"] == surface["schema"]
assert surface["source_policy"]["raw_text_committed"] is False
assert surface["source_policy"]["committed_source_refs"] == "doc-id-only"
assert surface["source_policy"]["not_by_exam_utility"] is True
assert surface["source_policy"]["bildungsleitlinien_role"] == surface_contract["bildungsleitlinienRole"]
surface_ids = [item["id"] for item in surface["surfaces"]]
assert surface_ids == surface_contract["surfaceIds"]
assert len(surface_ids) == len(set(surface_ids))
surface_by_id = {item["id"]: item for item in surface["surfaces"]}
assert surface_by_id[surface_contract["canonicalSurface"]]["authority"] == "canonical"
for surface_id in surface_contract["derivedSurfaceIds"]:
    assert surface_by_id[surface_id]["authority"] == "derived"
assert {item["role"] for item in surface["surfaces"]} == set(surface_contract["roles"])
assert surface_by_id["repo"]["status"] == "active"
assert surface_by_id["web"]["status"] == "active"
assert "data/detail-bridge-index.v1.json" in surface_by_id["web"]["data_sources"]
assert surface_by_id["obsidian"]["status"] == "active"
assert "docs/detail-bridge-index-v1.md" in surface_by_id["obsidian"]["data_sources"]
assert surface_by_id["schauwerk_miro"]["status"] == "planned"
surface_alignment = {entry["render_id"]: entry["surface_id"] for entry in surface["surface_alignment"]}
assert surface_alignment == surface_contract["surfaceAlignment"]
assert set(surface_alignment) == set(lrn["planned_renders"])
for item in surface["surfaces"]:
    assert item["title"].strip()
    assert item["data_sources"]
    assert item["outputs"]
    assert item["guards"]
    assert item["risk"].strip()
    assert item["next_use"].strip()
assert "dirty-vault-stop" in surface_by_id["obsidian"]["guards"]
assert "temp-vault CI validation" in surface_by_id["obsidian"]["guards"]
assert any("Keine Prüfungsnutzenlogik" in invariant for invariant in surface["invariants"])
assert any("Bildungsleitlinien" in invariant for invariant in surface["invariants"])

app_js = (root / "assets/app.js").read_text(encoding="utf-8")
index_html = (root / "index.html").read_text(encoding="utf-8")
assert "/data/learning-map.v1.json" in app_js
assert "/data/knowledge-network.v1.json" in app_js
assert "/data/detail-bridge-index.v1.json" in app_js
app_data_urls = set(re.findall(r'"(/data/[^"\n]+)"', app_js))
policy_web_urls = {"/" + source for source in surface_by_id["web"]["data_sources"]}
assert app_data_urls == policy_web_urls
for element_id in ["cluster-list", "relation-list", "topic-grid", "axis-list", "detail-bridge-summary", "detail-bridge-hub-list", "detail-bridge-axis-list"]:
    assert element_id in index_html
readme = (root / "README.md").read_text(encoding="utf-8")
for token in ["## Startpunkte", "index.html", "visuals/erzieherausbildung-systemkarte.canvas", "visuals/learning-map-v1.canvas", "docs/knowledge-network-v1.md", "docs/detail-bridge-index-v1.md", "docs/visualization-decision.md", "docs/obsidian-vault-spiegel.md", "docs/surface-policy-v1.md", "data/surface-policy.v1.json", "scripts/obsidian_views.py --dry-run"]:
    assert token in readme

obsidian_script = (root / "scripts/obsidian_views.py").read_text(encoding="utf-8")
obsidian_doc = (root / "docs/obsidian-vault-spiegel.md").read_text(encoding="utf-8")
view_export_validator = (root / "scripts/validate_view_export.py").read_text(encoding="utf-8")
workflow_validate = (root / ".github/workflows/validate.yml").read_text(encoding="utf-8")
obsidian_spec = importlib.util.spec_from_file_location("obsidian_views", root / "scripts/obsidian_views.py")
obsidian_views = importlib.util.module_from_spec(obsidian_spec)
assert obsidian_spec.loader is not None
sys.modules[obsidian_spec.name] = obsidian_views
obsidian_spec.loader.exec_module(obsidian_views)
for token in ["~/vault-gewebe/schule/erzieherausbildung", obsidian_views.POLICY, *obsidian_views.GENERATED_FILES]:
    assert token in obsidian_script
for view_file in obsidian_views.VIEW_FILES:
    assert view_file.source in obsidian_script
    assert view_file.target in obsidian_script
for token in [*obsidian_views.FORBIDDEN_PARTS, *obsidian_views.FORBIDDEN_SUFFIXES]:
    assert token in obsidian_script
assert "SPIEGELDATEI aus /home/alex/repos/erzieherausbildung" in obsidian_script
assert "git status" in obsidian_script
for token in ["TemporaryDirectory", "target outside vault", "read_bytes()", "obsidian export validation passed"]:
    assert token in view_export_validator
assert "python3 scripts/validate_view_export.py" in workflow_validate
assert "refusing to write: vault git status is not clean" in obsidian_script
for token in ["Repo bleibt kanonisch", "Vault", "Dry-Run", "kein gesamtes Repo", "machine-readable.local"]:
    assert token in obsidian_doc
surface_doc = (root / "docs/surface-policy-v1.md").read_text(encoding="utf-8")
for token in ["Repo bleibt Kanon", "Lesefläche", "Denkfläche", "Kollaborationsfläche", "Brücken-Hubs", "Keine Prüfungsnutzenlogik"]:
    assert token in surface_doc
assert "renderClusters" in app_js
assert "bridgeRole" in app_js
assert "bridgeClass" in app_js
assert "bridgeTypeLabel" in app_js
assert "bridge-role" in app_js
assert "bridge-type" in app_js
assert "activeCluster" in app_js


detail_schema = j("schemas/detail.v1.schema.json")
detail_index = j("data/details/index.v1.json")
assert detail_schema["schema"] == "erzieherausbildung.detail.contract.v1"
assert detail_schema["dataSchema"] == "erzieherausbildung.detail.v1"
assert detail_schema["indexSchema"] == detail_index["schema"]
assert detail_schema["sourcePolicy"]["raw_text_committed"] is False
assert len(detail_index["details"]) >= 5
detail_paths = [entry["path"] for entry in detail_index["details"]]
assert len(detail_paths) == len(set(detail_paths))
for entry in detail_index["details"]:
    assert entry["path"].startswith("/data/details/")
    detail = j(entry["path"].lstrip("/"))
    assert detail["schema"] == detail_schema["dataSchema"]
    assert detail["id"] == entry["id"]
    assert detail["sourcePolicy"]["raw_text_committed"] is False
    assert detail["sourcePolicy"]["source_refs_only"] is True
    assert detail["sourcePolicy"]["no_direct_citation"] is True
    assert detail["sourcePolicy"]["local_origin_material_only"] is True
    assert detail["topicIds"]
    assert detail["axisIds"]
    assert detail["sourceRefs"]
    assert detail["excerptRefs"]
assert "validate_details.py" in (root / ".github/workflows/validate.yml").read_text(encoding="utf-8")
assert "validate_detail_source_alignment.py" in (root / ".github/workflows/validate.yml").read_text(encoding="utf-8")

assert detail_index["coverage"]["topicCount"] == len(learning_topics)
assert detail_index["coverage"]["detailedTopicCount"] == len({topic for entry in detail_index["details"] for topic in entry["topicIds"]})
assert detail_index["coverage"]["missingTopicCount"] + detail_index["coverage"]["detailedTopicCount"] == detail_index["coverage"]["topicCount"]
assert detail_index["coverage"]["coverageStatus"] == "complete"
assert "vollständige Erstabdeckung" in detail_index["coverage"]["epistemicEmpty"]
assert "/data/details/index.v1.json" in app_js
assert "detailCoverageLabel" in app_js
assert "renderDetailBridgeIndex" in app_js
assert "detailBacklogUrl" not in app_js
assert "Detail-Brückenindex" in index_html
assert "Orientierung, keine neue Quelle" in index_html
assert "Detail offen" in app_js
assert "Detail vorhanden" in app_js

detail_backlog_schema = j("schemas/detail-backlog.v1.schema.json")
detail_backlog = j("data/details/backlog.v1.json")
assert detail_backlog_schema["schema"] == "erzieherausbildung.detail_backlog.contract.v1"
assert detail_backlog_schema["dataSchema"] == detail_backlog["schema"]
assert len(detail_backlog["entries"]) == detail_index["coverage"]["missingTopicCount"]
assert detail_backlog["coverageSnapshot"]["missingTopicCount"] == detail_index["coverage"]["missingTopicCount"]
assert detail_backlog["selectionRule"].strip()
assert "rawMaterial" in detail_backlog["blockedFields"]
assert "validate_detail_backlog.py" in workflow_validate
assert "cluster-action" in app_js
assert 'document.createElement("details")' in app_js

spec = importlib.util.spec_from_file_location("pilot_index_builder", root / "scripts/build_pilot_index.py")
pilot_index_builder = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(pilot_index_builder)
expected_pilot_json, expected_pilot_doc = pilot_index_builder.build_outputs()
assert (root / "data/pilot-index.v1.json").read_text(encoding="utf-8") == expected_pilot_json
assert (root / "docs/pilot-index-v1.md").read_text(encoding="utf-8") == expected_pilot_doc
pilot_index = json.loads(expected_pilot_json)
pilot_items = pilot_index_builder.load_items()
concrete_source_titles = sorted({item["sourceTitle"] for item in pilot_items if pilot_index_builder.has_concrete_locator(item)})
unresolved_source_work = [
    {
        "id": item["id"],
        "sourceTitle": item["sourceTitle"],
        "sourceLocator": item["sourceLocator"],
        "claimType": item["claimType"],
        "reviewStatus": item["reviewStatus"],
        "uncertainty": item["uncertainty"],
    }
    for item in pilot_items
    if not pilot_index_builder.has_concrete_locator(item)
]
assert "sourceTitles" not in pilot_index
assert pilot_index["concreteSourceTitles"] == concrete_source_titles
assert pilot_index["unresolvedSourceWork"] == unresolved_source_work
assert all(item["reviewStatus"] == "needs-source" for item in pilot_index["unresolvedSourceWork"])
assert all(item["claimType"] in {"question", "title-derived"} for item in pilot_index["unresolvedSourceWork"])
assert "Konkret lokalisierte Quellen im Pilot" in expected_pilot_doc
assert "Offene Quellenarbeit" in expected_pilot_doc

bridge_spec = importlib.util.spec_from_file_location("detail_bridge_index_builder", root / "scripts/build_detail_bridge_index.py")
bridge_index_builder = importlib.util.module_from_spec(bridge_spec)
assert bridge_spec.loader is not None
sys.modules[bridge_spec.name] = bridge_index_builder
bridge_spec.loader.exec_module(bridge_index_builder)
expected_bridge_json, expected_bridge_doc = bridge_index_builder.build_outputs()
assert (root / "data/detail-bridge-index.v1.json").read_text(encoding="utf-8") == expected_bridge_json
assert (root / "docs/detail-bridge-index-v1.md").read_text(encoding="utf-8") == expected_bridge_doc
bridge_index = json.loads(expected_bridge_json)
assert bridge_index["totals"]["details"] == len(detail_index["details"])
assert bridge_index["totals"]["bridges"] == sum(len(j(entry["path"].lstrip("/")).get("bridges", [])) for entry in detail_index["details"])
assert bridge_index["hubs"]
assert "Detail-Brückenindex v1" in expected_bridge_doc
assert "Orientierung, keine neue Quelle" in expected_bridge_doc
assert "python3 scripts/build_detail_bridge_index.py --check" in workflow_validate


for view_file in obsidian_views.VIEW_FILES:
    assert f"`{view_file.source}` -> `{view_file.target}`" in obsidian_doc
for generated in obsidian_views.GENERATED_FILES:
    assert f"`{generated}`" in obsidian_doc
assert "keine Rohquellenablage" in obsidian_doc

source_health = j("data/source-health.v1.json")
assert source_health["schema"] == "erzieherausbildung.source_health.v1"
assert source_health["sourcePolicy"]["raw_text_committed"] is False
assert source_health["sourcePolicy"]["diagnostic_metadata_only"] is True
assert source_health["summary"]["sourceCount"] == len(source_health["sources"])
assert "validate_source_health.py" in workflow_validate
print("repository validation passed")
