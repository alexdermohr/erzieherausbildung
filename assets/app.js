const learningMapUrl = "/data/learning-map.v1.json";
const knowledgeNetworkUrl = "/data/knowledge-network.v1.json";
const sourceSummaryUrl = "/data/source-summary.json";
const excerptIndexUrl = "/data/excerpts/pilot-v1.jsonl";
const detailIndexUrl = "/data/details/index.v1.json";
const detailBacklogUrl = "/data/details/backlog.v1.json";

const canvasViews = [
  {
    id: "learning-map",
    label: "Lernlandkarte",
    url: "/visuals/learning-map-v1.canvas",
    role: "Denkfläche",
  },
  {
    id: "system-map",
    label: "Systemkarte",
    url: "/visuals/erzieherausbildung-systemkarte.canvas",
    role: "Pipeline und Oberflächen",
  },
  {
    id: "lernfeld-4",
    label: "Lernfeld 4 – Bildungsbereiche",
    url: "/visuals/lernfeld-4-bildungsbereiche.canvas",
    role: "Fokuskarte",
  },
];

const state = {
  map: null,
  network: null,
  excerpts: [],
  details: [],
  detailCoverage: null,
  detailBacklog: null,
  activeAxis: "all",
  activeCluster: "all",
  canvas: {
    activeView: canvasViews[0].id,
    data: null,
    activeNodeId: null,
  },
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function svgEl(tag) {
  return document.createElementNS("http://www.w3.org/2000/svg", tag);
}

function normalizeText(value) {
  return String(value ?? "")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9äöüß]+/gi, "-")
    .replace(/^-+|-+$/g, "");
}

function firstLine(value) {
  return String(value ?? "").split(/\r?\n/).find((line) => line.trim())?.trim() ?? "";
}

function topicCount(axis) {
  return axis.topics?.length ?? 0;
}

function allTopics() {
  return state.map.axes.flatMap((axis) => axis.topics.map((topic) => ({ ...topic, axisId: axis.id, axisTitle: axis.title })));
}

function selectedCluster() {
  if (state.activeCluster === "all") return null;
  return state.network.clusters.find((cluster) => cluster.id === state.activeCluster) ?? null;
}

function activeClusterTopicSet() {
  const cluster = selectedCluster();
  return cluster ? new Set(cluster.topics) : null;
}

const bridgeTypeLabels = {
  enables: "ermöglicht / trägt",
  frames: "rahmt / ordnet",
  requires_precision: "braucht Genauigkeit",
  leads_to_action: "führt zu Handeln",
  stabilizes: "stabilisiert",
  communicates: "Kommunikation",
};

function bridgeTypeLabel(type) {
  return bridgeTypeLabels[type] ?? type;
}

function rerenderFocusViews() {
  renderClusters();
  renderTopics();
  renderRelations();
  renderCoverage();
}

function renderSourceSummary(summary) {
  const target = document.querySelector("#source-note");
  const map = state.map;
  const network = state.network;
  const topicTotal = allTopics().length;
  const fileCount = summary?.totals?.files ?? "29";
  const words = summary?.totals?.word_count ?? "325.811";
  target.textContent = `${map.axes.length} Sinnachsen, ${topicTotal} Themen, ${network.clusters.length} Cluster und ${network.bridges.length} Brücken aus ${fileCount} PDFs. Rohtexte bleiben lokal.`;
  const detail = document.querySelector("#source-detail");
  detail.textContent = `Maschinenlesbarer Arbeitsstand: ${words.toLocaleString?.("de-DE") ?? words} Wörter laut Inventar; sichtbar werden Struktur, Cluster und Beziehungen, nicht die Rohtexte.`;
}

function renderStats() {
  const target = document.querySelector("#map-stats");
  const topics = allTopics();
  target.innerHTML = "";
  [["Sinnachsen", state.map.axes.length], ["Themen", topics.length], ["Details", detailCoverageLabel()], ["Cluster", state.network.clusters.length], ["Brücken", state.network.bridges.length]].forEach(([label, value]) => {
    const card = el("article", "stat-card");
    card.append(el("strong", "", String(value)));
    card.append(el("span", "", label));
    target.append(card);
  });
}

function renderAxisFilter() {
  const select = document.querySelector("#axis-filter");
  select.querySelectorAll("option:not([value='all'])").forEach((option) => option.remove());
  state.map.axes.forEach((axis) => {
    const option = el("option", "", axis.title);
    option.value = axis.id;
    select.appendChild(option);
  });
  select.addEventListener("change", () => {
    state.activeAxis = select.value;
    renderTopics();
  });
}

function renderAxes() {
  const target = document.querySelector("#axis-list");
  target.innerHTML = "";
  state.map.axes.forEach((axis) => {
    const card = el("article", `axis-card ${axis.status}`);
    card.append(el("p", "module-meta", `${topicCount(axis)} Themen · ${axis.status}`));
    card.append(el("h3", "", axis.title));
    card.append(el("p", "", axis.summary));
    card.append(el("p", "source-line", `Quellen: ${axis.sources.join(", ")}`));
    target.append(card);
  });
}

function appendClusterButton(card, clusterId, text) {
  const button = el("button", "cluster-action", text);
  button.type = "button";
  button.addEventListener("click", () => {
    state.activeCluster = clusterId;
    rerenderFocusViews();
  });
  card.append(button);
}

function renderClusters() {
  const target = document.querySelector("#cluster-list");
  target.innerHTML = "";

  const allCard = el("article", `cluster-card ${state.activeCluster === "all" ? "active" : ""}`);
  allCard.append(el("p", "module-meta", "Gesamtblick"));
  allCard.append(el("h3", "", "Alle Cluster"));
  allCard.append(el("p", "", "Zeigt alle Themen und alle Brücken des Wissensnetzes."));
  appendClusterButton(allCard, "all", "Gesamtblick anzeigen");
  target.append(allCard);

  state.network.clusters.forEach((cluster) => {
    const card = el("article", `cluster-card ${state.activeCluster === cluster.id ? "active" : ""}`);
    card.append(el("p", "module-meta", `${cluster.topics.length} Themen · ${cluster.sources.length} Quellen`));
    card.append(el("h3", "", cluster.title));
    card.append(el("p", "", cluster.insight));
    appendClusterButton(card, cluster.id, "Cluster fokussieren");
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "Themen anzeigen";
    details.append(summary);
    const topicList = el("ul", "compact-list");
    cluster.topics.forEach((topic) => topicList.append(el("li", "", topic)));
    details.append(topicList);
    card.append(details);
    target.append(card);
  });
}

function renderTopics() {
  const grid = document.querySelector("#topic-grid");
  grid.innerHTML = "";
  const focusTopics = activeClusterTopicSet();
  const detailTopics = detailedTopicSet();
  const axes = state.activeAxis === "all" ? state.map.axes : state.map.axes.filter((axis) => axis.id === state.activeAxis);
  axes.forEach((axis) => {
    axis.topics
      .filter((topic) => !focusTopics || focusTopics.has(topic.title))
      .forEach((topic) => {
        const card = el("article", `topic-card ${topic.status}`);
        card.append(el("p", "module-meta", axis.title));
        card.append(el("h3", "", topic.title));
        const tags = el("div", "tag-row");
        tags.append(el("span", "tag", topic.status === "background" ? "Rahmen" : "Wissensinhalt"));
        tags.append(el("span", `tag ${detailTopics.has(topic.id) ? "detail-ready-tag" : "detail-missing-tag"}`, detailTopics.has(topic.id) ? "Detail vorhanden" : "Detail offen"));
        topic.sources.forEach((source) => tags.append(el("span", "tag muted-tag", source)));
        card.append(tags);
        grid.append(card);
      });
  });
}

function bridgeRole(bridge) {
  if (state.activeCluster === "all") return "Netzbrücke";
  if (bridge.from === state.activeCluster && bridge.to === state.activeCluster) return "Binnenbrücke";
  if (bridge.from === state.activeCluster) return "Ausgehend";
  if (bridge.to === state.activeCluster) return "Eingehend";
  return "Verwandt";
}

function bridgeClass(role) {
  if (role === "Ausgehend") return "outgoing";
  if (role === "Eingehend") return "incoming";
  if (role === "Binnenbrücke") return "internal";
  return "network";
}

function renderRelations() {
  const target = document.querySelector("#relation-list");
  target.innerHTML = "";
  const clusterById = new Map(state.network.clusters.map((cluster) => [cluster.id, cluster.title]));
  const bridges = state.activeCluster === "all" ? state.network.bridges : state.network.bridges.filter((bridge) => bridge.from === state.activeCluster || bridge.to === state.activeCluster);
  bridges.forEach((bridge) => {
    const role = bridgeRole(bridge);
    const card = el("article", `relation-card ${bridgeClass(role)}`);
    const roleLine = el("p", "bridge-role");
    roleLine.append(el("span", "bridge-role-badge", role));
    roleLine.append(el("span", "bridge-type", bridgeTypeLabel(bridge.type)));
    card.append(roleLine);
    card.append(el("h3", "", `${clusterById.get(bridge.from)} → ${clusterById.get(bridge.to)}`));
    card.append(el("p", "", bridge.relation));
    target.append(card);
  });
}

function renderCoverage() {
  const target = document.querySelector("#coverage-note");
  const coverage = state.map.coverage;
  const detailCoverage = state.detailCoverage;
  const netCoverage = state.network.coverage;
  const omitted = coverage?.intentionally_unmodeled_doc_ids?.join(", ") || "keine";
  const cluster = selectedCluster();
  const focus = cluster ? ` Fokus: ${cluster.title} mit ${cluster.topics.length} Themen.` : "";
  const detailOpenText = detailCoverage?.missingTopicCount === 0 ? "keine Themen bleiben offen" : `${detailCoverage.missingTopicCount} Themen bleiben offen`;
  const detailLine = detailCoverage ? ` Detailaufbereitung: ${detailCoverage.detailedTopicCount}/${detailCoverage.topicCount} Themen; ${detailOpenText}.` : "";
  target.textContent = `${coverage.linked_doc_ids.length} doc-IDs sind an Themen gebunden. Das Wissensnetz clustert ${netCoverage.topic_count} Themen in ${netCoverage.cluster_count} Erkenntnisgruppen.${focus}${detailLine} Bewusst nicht als Themenknoten modelliert: ${omitted}.`;
}

function renderSurfaces() {
  const target = document.querySelector("#surface-list");
  target.innerHTML = "";
  state.map.planned_renders.forEach((surface) => {
    const card = el("article", "visual-card");
    card.append(el("h3", "", surface));
    card.append(el("p", "", surface === "obsidian_canvas" ? "Denkfläche" : surface === "prepp_style_homepage" ? "Lesefläche" : "Kollaborationsfläche"));
    target.append(card);
  });
}

function parseJsonl(text) {
  return text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean)
    .map((line) => {
      try {
        return JSON.parse(line);
      } catch {
        return null;
      }
    })
    .filter(Boolean);
}

async function loadExcerpts() {
  try {
    const response = await fetch(excerptIndexUrl);
    if (!response.ok) return [];
    return parseJsonl(await response.text());
  } catch {
    return [];
  }
}

async function loadDetails() {
  try {
    const response = await fetch(detailIndexUrl);
    if (!response.ok) return [];
    const index = await response.json();
    const entries = Array.isArray(index.details) ? index.details : [];
    state.detailCoverage = index.coverage ?? null;
    return Promise.all(entries.map(async (entry) => {
      try {
        const detailResponse = await fetch(entry.path);
        if (!detailResponse.ok) return null;
        return await detailResponse.json();
      } catch {
        return null;
      }
    })).then((items) => items.filter(Boolean));
  } catch {
    return [];
  }
}

function detailedTopicSet() {
  if (state.detailCoverage?.detailedTopicIds) return new Set(state.detailCoverage.detailedTopicIds);
  return new Set(state.details.flatMap((detail) => detail.topicIds ?? []));
}

function detailCoverageLabel() {
  const coverage = state.detailCoverage;
  if (!coverage) return `${detailedTopicSet().size}/${allTopics().length}`;
  return `${coverage.detailedTopicCount}/${coverage.topicCount}`;
}

function matchingDetails(sources, title, topicId = "", axisId = "") {
  const sourceSet = new Set((sources ?? []).map(String));
  const titleNorm = normalizeText(title);
  const topicNorm = normalizeText(topicId);
  const axisNorm = normalizeText(axisId);
  return state.details.filter((detail) => {
    const sourceMatch = (detail.sourceRefs ?? []).some((source) => sourceSet.has(String(source)));
    const topicMatch = (detail.topicIds ?? []).some((topic) => normalizeText(topic) === topicNorm || normalizeText(topic) === titleNorm);
    const axisMatch = axisNorm && (detail.axisIds ?? []).some((axis) => normalizeText(axis) === axisNorm);
    const titleMatch = normalizeText(detail.title).includes(titleNorm) || titleNorm.includes(normalizeText(detail.title));
    return sourceMatch || topicMatch || axisMatch || titleMatch;
  });
}

function appendListSection(target, title, items) {
  if (!items?.length) return;
  const section = el("div", "detail-subsection");
  section.append(el("h5", "", title));
  const list = el("ul", "compact-list");
  items.forEach((item) => list.append(el("li", "", item)));
  section.append(list);
  target.append(section);
}

function renderKnowledgeDetail(target, detail) {
  const card = el("article", "knowledge-detail-card");
  card.append(el("p", "module-meta", `Detailstatus: ${detail.detailStatus ?? "draft"} · Unsicherheit ${detail.uncertainty ?? "?"} · Interpolation ${detail.interpolation ?? "?"}`));
  card.append(el("h4", "", detail.title));
  card.append(el("p", "", detail.summary));
  appendListSection(card, "Kernideen", detail.coreIdeas);
  appendListSection(card, "Praxisanker", detail.practiceAnchors);
  appendListSection(card, "Typische Fehlannahmen", detail.commonMisunderstandings);
  appendListSection(card, "Offene Fragen", detail.openQuestions);
  if (detail.bridges?.length) {
    const bridgeList = detail.bridges.map((bridge) => `${bridge.targetId}: ${bridge.relation}`);
    appendListSection(card, "Brücken", bridgeList);
  }
  card.append(el("p", "fineprint", `Beleganker: ${(detail.sourceRefs ?? []).join(", ")} · Exzerpte: ${(detail.excerptRefs ?? []).join(", ")}`));
  target.append(card);
}

function activeCanvasView() {
  return canvasViews.find((view) => view.id === state.canvas.activeView) ?? canvasViews[0];
}

function canvasNodeLabel(node) {
  return firstLine(node.text || node.label || node.id) || node.id;
}

function nodeCenter(node) {
  return {
    x: Number(node.x ?? 0) + Number(node.width ?? 240) / 2,
    y: Number(node.y ?? 0) + Number(node.height ?? 120) / 2,
  };
}

function wrapSvgText(text, maxChars) {
  const words = String(text).replace(/\s+/g, " ").trim().split(" ").filter(Boolean);
  const lines = [];
  let current = "";
  words.forEach((word) => {
    const next = current ? `${current} ${word}` : word;
    if (next.length > maxChars && current) {
      lines.push(current);
      current = word;
    } else {
      current = next;
    }
  });
  if (current) lines.push(current);
  return lines.slice(0, 4);
}

function findAxisForNode(node) {
  const id = String(node.id ?? "");
  const label = normalizeText(canvasNodeLabel(node));
  const directId = id.startsWith("axis-") ? id.slice(5) : id;
  return state.map.axes.find((axis) => axis.id === directId || normalizeText(axis.title) === label) ?? null;
}

function findTopicForNode(node) {
  const id = String(node.id ?? "");
  const label = normalizeText(canvasNodeLabel(node));
  const idCandidates = new Set([
    id,
    id.replace(/^topic-/, ""),
    id.replace(/^node-/, ""),
    normalizeText(id.replace(/^topic-/, "")),
  ]);
  return allTopics().find((topic) => idCandidates.has(topic.id) || idCandidates.has(normalizeText(topic.id)) || normalizeText(topic.title) === label) ?? null;
}

function findNodeContext(node) {
  const topic = findTopicForNode(node);
  if (topic) return { kind: "topic", topic, axis: state.map.axes.find((axis) => axis.id === topic.axisId) ?? null };
  const axis = findAxisForNode(node);
  if (axis) return { kind: "axis", axis };
  return { kind: "canvas", node };
}

function excerptDocId(excerpt) {
  const explicit = excerpt.docId ?? excerpt.doc_id ?? excerpt.sourceDocId ?? excerpt.source_doc_id ?? excerpt.sourceId ?? excerpt.source_id;
  if (explicit) return String(explicit);
  const haystack = `${excerpt.id ?? ""} ${excerpt.sourceLocator ?? ""} ${excerpt.source_locator ?? ""}`;
  return haystack.match(/doc-\d{3}/)?.[0] ?? "";
}

function excerptConcepts(excerpt) {
  if (Array.isArray(excerpt.concepts)) return excerpt.concepts.filter(Boolean);
  if (excerpt.concept) return [excerpt.concept];
  if (excerpt.topic) return [excerpt.topic];
  return [];
}

function excerptLinks(excerpt) {
  return Array.isArray(excerpt.links) ? excerpt.links.filter(Boolean) : [];
}

function excerptTitle(excerpt) {
  return excerpt.topic ?? excerpt.title ?? excerptConcepts(excerpt)[0] ?? excerpt.sourceTitle ?? excerpt.source_title ?? "Exzerpt";
}

function excerptBody(excerpt) {
  return excerpt.excerpted ?? excerpt.summary ?? excerpt.text ?? excerpt.content ?? excerpt.note ?? "Noch keine lesbare Zusammenfassung im Pilotexzerpt.";
}

function excerptLocator(excerpt) {
  return excerpt.sourceLocator ?? excerpt.source_locator ?? excerpt.locator ?? "Fundstelle noch nicht angegeben";
}

function excerptStatus(excerpt) {
  return excerpt.status ?? excerpt.reviewStatus ?? excerpt.review_status ?? "draft";
}

function excerptPracticeUse(excerpt) {
  return excerpt.practiceUse ?? excerpt.practice_use ?? "";
}

function matchingExcerpts(sources, title, topicId = "") {
  const sourceSet = new Set((sources ?? []).map(String));
  const titleNorm = normalizeText(title);
  const topicNorm = normalizeText(topicId);
  return state.excerpts.filter((excerpt) => {
    const docMatch = sourceSet.has(String(excerptDocId(excerpt)));
    const conceptMatch = excerptConcepts(excerpt).some((concept) => {
      const conceptNorm = normalizeText(concept);
      return conceptNorm === titleNorm || conceptNorm.includes(titleNorm) || titleNorm.includes(conceptNorm);
    });
    const linkMatch = excerptLinks(excerpt).some((link) => {
      const linkNorm = normalizeText(link);
      return linkNorm === topicNorm || linkNorm === titleNorm;
    });
    return docMatch || conceptMatch || linkMatch;
  });
}

function appendSourceTags(target, sources) {
  const row = el("div", "tag-row");
  if (!sources?.length) {
    row.append(el("span", "tag muted-tag", "keine doc-ID"));
  } else {
    sources.forEach((source) => row.append(el("span", "tag muted-tag", source)));
  }
  target.append(row);
}

function renderCanvasDetail(node) {
  const target = document.querySelector("#canvas-detail");
  target.innerHTML = "";
  if (!node) {
    target.append(el("p", "eyebrow", "Detailpfad"));
    target.append(el("h3", "", "Knoten auswählen"));
    target.append(el("p", "", "Klick auf einen Canvas-Knoten zeigt die aktuelle Rückbindung: Thema oder Achse, Quellen-IDs, vorhandene Pilotexzerpte und die noch fehlende Detailschicht."));
    target.append(el("p", "fineprint", "Epistemische Leere: Flächendeckende Detailaufbereitungen fehlen noch; nötig für den Sprung vom Überblick zum belastbaren Lerninhalt."));
    return;
  }

  const context = findNodeContext(node);
  const label = canvasNodeLabel(node);
  const heading = context.topic?.title ?? context.axis?.title ?? label;
  const status = context.topic?.status ?? context.axis?.status ?? "canvas";
  const sources = context.topic?.sources ?? context.axis?.sources ?? [];
  const summary = context.topic
    ? `Dieses Thema gehört zur Achse „${context.topic.axisTitle}“ und ist über Quellenanker mit der späteren Detailaufbereitung verbindbar.`
    : context.axis?.summary ?? "Dieser Canvas-Knoten ist noch nicht eindeutig an eine Sinnachse oder ein Thema gebunden.";
  const topicOrAxisId = context.topic?.id ?? context.axis?.id ?? node.id;
  const excerpts = matchingExcerpts(sources, heading, topicOrAxisId);
  const details = matchingDetails(sources, heading, context.topic?.id ?? "", context.axis?.id ?? "");

  target.append(el("p", "eyebrow", context.kind === "topic" ? "Themenknoten" : context.kind === "axis" ? "Sinnachse" : "Canvas-Knoten"));
  target.append(el("h3", "", heading));
  target.append(el("p", "module-meta", `Status: ${status}`));
  if (context.topic?.axisTitle) target.append(el("p", "fineprint", `Achse: ${context.topic.axisTitle}`));
  target.append(el("p", "", summary));
  appendSourceTags(target, sources);

  const detailBlock = el("article", "detail-note");
  detailBlock.append(el("h4", "", "Detailaufbereitung"));
  if (details.length) {
    details.slice(0, 3).forEach((detail) => renderKnowledgeDetail(detailBlock, detail));
  } else {
    detailBlock.append(el("p", "", "Für diesen Knoten gibt es noch keine Detaildatei. Das bleibt als Arbeitslücke sichtbar."));
  }
  target.append(detailBlock);

  const depth = el("article", "detail-note");
  depth.append(el("h4", "", "Detailtiefe"));
  depth.append(el("p", "", sources.length ? "Dieser Knoten ist bereits über doc-IDs an Ursprungswissen rückgebunden. Die spätere Ausbaustufe ergänzt daraus geprüfte Detailaufbereitungen." : "Dieser Knoten braucht noch stabile Quellen- oder Detailzuordnung."));
  target.append(depth);

  const excerptBlock = el("article", "detail-note");
  excerptBlock.append(el("h4", "", "Pilotexzerpte"));
  if (excerpts.length) {
    excerpts.slice(0, 4).forEach((excerpt) => {
      const item = el("div", "excerpt-card");
      item.append(el("strong", "", excerptTitle(excerpt)));
      item.append(el("p", "", excerptBody(excerpt)));
      const practiceUse = excerptPracticeUse(excerpt);
      if (practiceUse) item.append(el("p", "", practiceUse));
      item.append(el("p", "fineprint", `${excerptDocId(excerpt) || "doc-ID offen"} · ${excerptLocator(excerpt)} · ${excerptStatus(excerpt)}`));
      excerptBlock.append(item);
    });
  } else {
    excerptBlock.append(el("p", "", "Noch kein passendes Pilotexzerpt gefunden. Das ist kein Fehler, sondern die sichtbare Grenze der bisherigen Tiefenerschließung."));
  }
  target.append(excerptBlock);
}

async function loadCanvasView() {
  const view = activeCanvasView();
  const status = document.querySelector("#canvas-status");
  status.textContent = `${view.label} wird geladen…`;
  try {
    const response = await fetch(view.url);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    state.canvas.data = await response.json();
    state.canvas.activeNodeId = null;
    renderCanvasSurface();
    renderCanvasDetail(null);
    const nodeCount = state.canvas.data.nodes?.length ?? 0;
    const edgeCount = state.canvas.data.edges?.length ?? 0;
    status.textContent = `${view.label}: ${nodeCount} Knoten, ${edgeCount} Kanten · ${view.role} · read-only aus ${view.url}`;
  } catch (error) {
    state.canvas.data = null;
    document.querySelector("#canvas-viewer").textContent = "Canvas konnte nicht geladen werden.";
    status.textContent = `Fehler beim Laden von ${view.url}: ${error.message}`;
  }
}

function renderCanvasSelector() {
  const select = document.querySelector("#canvas-view-select");
  select.innerHTML = "";
  canvasViews.forEach((view) => {
    const option = el("option", "", view.label);
    option.value = view.id;
    select.append(option);
  });
  select.value = state.canvas.activeView;
  select.addEventListener("change", async () => {
    state.canvas.activeView = select.value;
    await loadCanvasView();
  });
}

function renderCanvasSurface() {
  const target = document.querySelector("#canvas-viewer");
  target.innerHTML = "";
  const data = state.canvas.data;
  if (!data?.nodes?.length) {
    target.textContent = "Keine Canvas-Knoten vorhanden.";
    return;
  }

  const nodes = data.nodes.map((node) => ({ width: 260, height: 120, ...node }));
  const nodeById = new Map(nodes.map((node) => [node.id, node]));
  const minX = Math.min(...nodes.map((node) => Number(node.x ?? 0))) - 80;
  const minY = Math.min(...nodes.map((node) => Number(node.y ?? 0))) - 80;
  const maxX = Math.max(...nodes.map((node) => Number(node.x ?? 0) + Number(node.width ?? 260))) + 80;
  const maxY = Math.max(...nodes.map((node) => Number(node.y ?? 0) + Number(node.height ?? 120))) + 80;

  const svg = svgEl("svg");
  svg.setAttribute("viewBox", `${minX} ${minY} ${maxX - minX} ${maxY - minY}`);
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", "Gerenderte Obsidian-Canvas-Lernlandkarte");

  const edgeLayer = svgEl("g");
  edgeLayer.setAttribute("class", "canvas-edge-layer");
  (data.edges ?? []).forEach((edge) => {
    const from = nodeById.get(edge.fromNode);
    const to = nodeById.get(edge.toNode);
    if (!from || !to) return;
    const start = nodeCenter(from);
    const end = nodeCenter(to);
    const line = svgEl("line");
    line.setAttribute("x1", start.x);
    line.setAttribute("y1", start.y);
    line.setAttribute("x2", end.x);
    line.setAttribute("y2", end.y);
    line.setAttribute("class", "canvas-edge");
    edgeLayer.append(line);
  });
  svg.append(edgeLayer);

  const nodeLayer = svgEl("g");
  nodeLayer.setAttribute("class", "canvas-node-layer");
  nodes.forEach((node) => {
    const group = svgEl("g");
    const isActive = state.canvas.activeNodeId === node.id;
    group.setAttribute("class", `canvas-node ${isActive ? "active" : ""}`);
    group.setAttribute("tabindex", "0");
    group.setAttribute("role", "button");
    group.setAttribute("aria-label", canvasNodeLabel(node));
    group.addEventListener("click", () => {
      state.canvas.activeNodeId = node.id;
      renderCanvasSurface();
      renderCanvasDetail(node);
    });
    group.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        state.canvas.activeNodeId = node.id;
        renderCanvasSurface();
        renderCanvasDetail(node);
      }
    });

    const rect = svgEl("rect");
    rect.setAttribute("x", Number(node.x ?? 0));
    rect.setAttribute("y", Number(node.y ?? 0));
    rect.setAttribute("width", Number(node.width ?? 260));
    rect.setAttribute("height", Number(node.height ?? 120));
    rect.setAttribute("rx", "18");
    group.append(rect);

    const label = wrapSvgText(canvasNodeLabel(node), Math.max(18, Math.floor(Number(node.width ?? 260) / 11)));
    label.forEach((line, index) => {
      const text = svgEl("text");
      text.setAttribute("x", Number(node.x ?? 0) + 18);
      text.setAttribute("y", Number(node.y ?? 0) + 30 + index * 20);
      text.textContent = line;
      group.append(text);
    });

    const context = findNodeContext(node);
    if (context.topic || context.axis) {
      const badge = svgEl("text");
      badge.setAttribute("x", Number(node.x ?? 0) + 18);
      badge.setAttribute("y", Number(node.y ?? 0) + Number(node.height ?? 120) - 16);
      badge.setAttribute("class", "canvas-node-badge");
      badge.textContent = context.topic ? "Thema · Quellenanker" : "Achse · Quellenanker";
      group.append(badge);
    }

    nodeLayer.append(group);
  });
  svg.append(nodeLayer);
  target.append(svg);
}

async function boot() {
  const [map, network, sourceSummary, excerpts, details] = await Promise.all([
    fetch(learningMapUrl).then((res) => res.json()),
    fetch(knowledgeNetworkUrl).then((res) => res.json()),
    fetch(sourceSummaryUrl).then((res) => res.json()).catch(() => null),
    loadExcerpts(),
    loadDetails(),
  ]);
  state.map = map;
  state.network = network;
  state.excerpts = excerpts;
  state.details = details;
  renderSourceSummary(sourceSummary);
  renderStats();
  renderCanvasSelector();
  await loadCanvasView();
  renderAxisFilter();
  renderAxes();
  renderClusters();
  renderTopics();
  renderRelations();
  renderCoverage();
  renderSurfaces();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>Fehler beim Laden der Lernlandkarte: ${error.message}</pre>`;
});
