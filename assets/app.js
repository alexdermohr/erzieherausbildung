const learningMapUrl = "/data/learning-map.v1.json";
const knowledgeNetworkUrl = "/data/knowledge-network.v1.json";
const sourceSummaryUrl = "/data/source-summary.json";

const state = {
  map: null,
  network: null,
  activeAxis: "all",
  activeCluster: "all",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
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
  [["Sinnachsen", state.map.axes.length], ["Themen", topics.length], ["Cluster", state.network.clusters.length], ["Brücken", state.network.bridges.length]].forEach(([label, value]) => {
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
  const netCoverage = state.network.coverage;
  const omitted = coverage?.intentionally_unmodeled_doc_ids?.join(", ") || "keine";
  const cluster = selectedCluster();
  const focus = cluster ? ` Fokus: ${cluster.title} mit ${cluster.topics.length} Themen.` : "";
  target.textContent = `${coverage.linked_doc_ids.length} doc-IDs sind an Themen gebunden. Das Wissensnetz clustert ${netCoverage.topic_count} Themen in ${netCoverage.cluster_count} Erkenntnisgruppen.${focus} Bewusst nicht als Themenknoten modelliert: ${omitted}.`;
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

async function boot() {
  const [map, network, sourceSummary] = await Promise.all([
    fetch(learningMapUrl).then((res) => res.json()),
    fetch(knowledgeNetworkUrl).then((res) => res.json()),
    fetch(sourceSummaryUrl).then((res) => res.json()).catch(() => null),
  ]);
  state.map = map;
  state.network = network;
  renderSourceSummary(sourceSummary);
  renderStats();
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
