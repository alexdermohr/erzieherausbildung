import json
import re
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
    "data/machine-readable-inventory.json",
    "data/learning-map.v1.json",
    "docs/implementation-plan.md",
    "docs/learning-map-v1.md",
    "schemas/learning-map.v1.schema.json",
    "visuals/learning-map-v1.canvas",
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
app_js = (root / "assets/app.js").read_text(encoding="utf-8")
index_html = (root / "index.html").read_text(encoding="utf-8")
assert "/data/learning-map.v1.json" in app_js
assert "/data/knowledge-network.v1.json" in app_js
for element_id in ["cluster-list", "relation-list", "topic-grid", "axis-list"]:
    assert element_id in index_html
readme = (root / "README.md").read_text(encoding="utf-8")
for token in ["## Startpunkte", "index.html", "visuals/erzieherausbildung-systemkarte.canvas", "visuals/learning-map-v1.canvas", "docs/knowledge-network-v1.md", "docs/visualization-decision.md"]:
    assert token in readme
assert "renderClusters" in app_js
assert "bridgeRole" in app_js
assert "bridgeClass" in app_js
assert "bridgeTypeLabel" in app_js
assert "bridge-role" in app_js
assert "bridge-type" in app_js
assert "activeCluster" in app_js
assert "cluster-action" in app_js
assert 'document.createElement("details")' in app_js
print("repository validation passed")
