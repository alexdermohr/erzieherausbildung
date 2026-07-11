function sitePath(path) {
  return String(path).replace(/^\/+/, "");
}

const learningMapUrl = sitePath("/data/learning-map.v1.json");
const knowledgeNetworkUrl = sitePath("/data/knowledge-network.v1.json");
const sourceSummaryUrl = sitePath("/data/source-summary.json");
const excerptIndexUrl = sitePath("/data/excerpts/pilot-v1.jsonl");
const detailIndexUrl = sitePath("/data/details/index.v1.json");
const detailBridgeIndexUrl = sitePath("/data/detail-bridge-index.v1.json");
const learningFieldFocusUrl = sitePath("/data/learning-field-focus.v1.json");
const theoryCatalogUrl = sitePath("/data/theory-catalog.v1.json");
const currentWorkIndexUrl = sitePath("/data/current-work/index.v1.json");

const baseCanvasViews = [
  {
    id: "learning-map",
    label: "Lernlandkarte",
    url: sitePath("/visuals/learning-map-v1.canvas"),
    role: "Denkfläche",
  },
];

let canvasViews = [...baseCanvasViews];

function focusCanvasViews(focusModel) {
  return (focusModel?.fields ?? []).map((field) => ({
    id: field.id,
    label: `${field.label} – Fokuskarte`,
    url: sitePath(`/${field.canvas}`),
    role: "Fokuskarte",
  }));
}

const state = {
  map: null,
  network: null,
  excerpts: [],
  details: [],
  detailCoverage: null,
  detailBacklog: null,
  detailBridgeIndex: null,
  learningFieldFocus: null,
  theoryCatalog: null,
  currentWorkIndex: null,
  currentWorks: [],
  activeContentLayer: "canon",
  activeAxis: "all",
  activeCluster: "all",
  activeDetailBridgeAxis: "all",
  activeDetailBridgeTarget: "",
  activeDetailBridgeDetail: "",
  activeTheoryAxis: "all",
  activeTheoryKind: "all",
  theoryQuery: "",
  canvas: {
    activeView: baseCanvasViews[0].id,
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

function topicAnchorId(topicId) {
  return `topic-${normalizeText(topicId)}`;
}

function axisAnchorId(axisId) {
  return `axis-${normalizeText(axisId)}`;
}

function scrollToSection(id) {
  document.querySelector(`#${id}`)?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function flashElement(element) {
  if (!element) return;
  element.classList.remove("link-highlight");
  void element.offsetWidth;
  element.classList.add("link-highlight");
}

function actionButton(text, onClick, className = "inline-action") {
  const button = el("button", className, text);
  button.type = "button";
  button.addEventListener("click", onClick);
  return button;
}

function allTopics() {
  return state.map.axes.flatMap((axis) => axis.topics.map((topic) => ({ ...topic, axisId: axis.id, axisTitle: axis.title })));
}
function currentTerm() {
  return state.currentWorkIndex?.terms?.find((term) => term.id === state.currentWorkIndex.currentTermId) ?? null;
}

function publishedCurrentWorks() {
  const termId = state.currentWorkIndex?.currentTermId;
  return state.currentWorks
    .filter((work) => work.termId === termId)
    .filter((work) => work.publicationStatus === "published")
    .filter((work) => ["active", "canon-candidate"].includes(work.lifecycle))
    .sort((left, right) => left.title.localeCompare(right.title, "de"));
}

function currentWorksForTopic(topicId) {
  return publishedCurrentWorks().filter((work) => (work.topicIds ?? []).includes(topicId));
}

const currentWorkLifecycleLabels = {
  active: "In Arbeit",
  "canon-candidate": "Kandidat für den Kanon",
};

function currentWorkLifecycleLabel(lifecycle) {
  return currentWorkLifecycleLabels[lifecycle] ?? lifecycle;
}

function openCurrentWork(workId) {
  setContentLayer("current-work");
  const target = document.querySelector(`#current-work-${normalizeText(workId)}`);
  target?.scrollIntoView({ behavior: "smooth", block: "center" });
  setTimeout(() => flashElement(target), 120);
}

function setContentLayer(layer, { scroll = false } = {}) {
  state.activeContentLayer = layer === "current-work" ? "current-work" : "canon";
  document.querySelectorAll("#content-layer-switch [data-content-layer]").forEach((button) => {
    button.setAttribute("aria-pressed", String(button.dataset.contentLayer === state.activeContentLayer));
  });
  const currentSection = document.querySelector("#aktuell");
  if (currentSection) currentSection.hidden = state.activeContentLayer !== "current-work";
  const note = document.querySelector("#content-layer-note");
  if (note) {
    note.textContent = state.activeContentLayer === "current-work"
      ? "Freigegebene aktuelle Arbeiten werden eingeblendet. Sie sind noch nicht automatisch Teil des Kanons."
      : "Der geprüfte Ausbildungskanon ist sichtbar. Aktuelle Arbeiten bleiben ausgeblendet.";
  }
  renderTopics();
  renderCurrentWork();
  if (scroll && state.activeContentLayer === "current-work") scrollToSection("aktuell");
}

function renderContentLayerSwitch() {
  document.querySelectorAll("#content-layer-switch [data-content-layer]").forEach((button) => {
    button.addEventListener("click", () => setContentLayer(button.dataset.contentLayer, { scroll: button.dataset.contentLayer === "current-work" }));
  });
  setContentLayer(state.activeContentLayer);
}

function renderCurrentWorkCard(work, term) {
  const card = el("article", `current-work-card ${work.lifecycle}`);
  card.id = `current-work-${normalizeText(work.id)}`;
  card.append(el("p", "module-meta", `${term?.label ?? "Aktuelles Halbjahr"} · ${currentWorkLifecycleLabel(work.lifecycle)}`));
  card.append(el("h3", "", work.title));
  card.append(el("p", "current-work-summary", work.summary));
  appendListSection(card, "Erkenntnisse", work.keyFindings);
  appendListSection(card, "Offene Fragen", work.openQuestions);
  const actions = el("div", "action-row compact-actions");
  (work.topicIds ?? []).forEach((topicId) => {
    const topic = topicById(topicId);
    if (topic) actions.append(actionButton(`Zum Thema „${topic.title}“`, () => openTopic(topic.id), "text-link-action"));
  });
  if (actions.childElementCount) card.append(actions);
  return card;
}

function renderCurrentWork() {
  const section = document.querySelector("#aktuell");
  const target = document.querySelector("#current-work-list");
  const empty = document.querySelector("#current-work-empty");
  const label = document.querySelector("#current-term-label");
  if (!section || !target || !empty || !label || !state.currentWorkIndex) return;
  section.hidden = state.activeContentLayer !== "current-work";
  const term = currentTerm();
  label.textContent = term?.label ?? "Aktuelles Halbjahr";
  target.innerHTML = "";
  const works = publishedCurrentWorks();
  works.forEach((work) => target.append(renderCurrentWorkCard(work, term)));
  empty.hidden = works.length > 0;
  empty.textContent = works.length ? "" : state.currentWorkIndex.emptyState;
}

async function loadCurrentWork() {
  const response = await fetch(currentWorkIndexUrl);
  if (!response.ok) throw new Error(`Aktuelle Arbeit konnte nicht geladen werden: ${response.status}`);
  const index = await response.json();
  const visibleEntries = (index.works ?? [])
    .filter((entry) => entry.termId === index.currentTermId)
    .filter((entry) => entry.publicationStatus === "published")
    .filter((entry) => ["active", "canon-candidate"].includes(entry.lifecycle));
  const works = await Promise.all(visibleEntries.map(async (entry) => {
    const itemResponse = await fetch(sitePath(entry.path));
    if (!itemResponse.ok) throw new Error(`Aktuelle Arbeit ${entry.id} konnte nicht geladen werden: ${itemResponse.status}`);
    return await itemResponse.json();
  }));
  return { index, works };
}


function topicById(topicId) {
  return allTopics().find((topic) => topic.id === topicId) ?? null;
}

function topicByTitle(title) {
  const titleNorm = normalizeText(title);
  return allTopics().find((topic) => normalizeText(topic.title) === titleNorm) ?? null;
}

function setAxisFilter(axisId, { clearCluster = true } = {}) {
  state.activeAxis = axisId;
  if (clearCluster) state.activeCluster = "all";
  const select = document.querySelector("#axis-filter");
  if (select && [...select.options].some((option) => option.value === axisId)) select.value = axisId;
  renderClusters();
  renderTopics();
  renderRelations();
}

function openAxis(axisId, { showInMap = false } = {}) {
  setAxisFilter(axisId);
  if (showInMap) {
    openCanvasNode(`axis-${axisId}`);
    return;
  }
  const axisCard = document.querySelector(`#${axisAnchorId(axisId)}`);
  scrollToSection("achsen");
  setTimeout(() => flashElement(axisCard), 120);
}

function detailForTopic(topic) {
  return state.details.find((detail) => (detail.topicIds ?? []).includes(topic.id)) ?? matchingDetails(topic.sources, topic.title, topic.id, topic.axisId)[0] ?? null;
}

function openTopic(topicId, { showInMap = false } = {}) {
  const topic = topicById(topicId);
  if (!topic) return;
  setAxisFilter(topic.axisId, { clearCluster: true });
  const topicCard = document.querySelector(`#${topicAnchorId(topic.id)}`);
  if (showInMap) {
    openCanvasNode(`topic-${topic.id}`);
    return;
  }
  topicCard?.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  setTimeout(() => flashElement(topicCard), 120);
}

function openTopicByTitle(title) {
  const topic = topicByTitle(title);
  if (topic) openTopic(topic.id);
}

function focusCluster(clusterId) {
  state.activeCluster = clusterId;
  state.activeAxis = "all";
  const select = document.querySelector("#axis-filter");
  if (select) select.value = "all";
  rerenderFocusViews();
  scrollToSection("index");
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
  communicates: "verbindet durch Kommunikation",
};

function bridgeTypeLabel(type) {
  return bridgeTypeLabels[type] ?? type;
}

function rerenderFocusViews() {
  renderClusters();
  renderTopics();
  renderRelations();
  renderDetailBridgeIndex();
  renderCoverage();
}

function renderSourceSummary(summary) {
  const target = document.querySelector("#source-note");
  const map = state.map;
  const network = state.network;
  const topicTotal = allTopics().length;
  const fileCount = summary?.totals?.files ?? "29";
  const words = summary?.totals?.word_count ?? "325.811";
  target.textContent = `${map.axes.length} Wissensbereiche, ${topicTotal} Themen, ${network.clusters.length} Lernwege und ${network.bridges.length} Beziehungen zwischen Lernwegen aus ${fileCount} PDFs. Rohtexte bleiben lokal.`;
  const detail = document.querySelector("#source-detail");
  detail.textContent = `Arbeitsstand: ${words.toLocaleString?.("de-DE") ?? words} Wörter laut Inventar; sichtbar sind Lernkarten, Themen und begründete Zusammenhänge.`;
}

function renderStats() {
  const target = document.querySelector("#map-stats");
  if (!target) return;
  const topics = allTopics();
  target.innerHTML = "";
  [["Wissensbereiche", state.map.axes.length], ["Themen", topics.length], ["Vertiefungen", detailCoverageLabel()], ["Lernwege", state.network.clusters.length], ["Lernweg-Beziehungen", state.network.bridges.length]].forEach(([label, value]) => {
    const item = el("span", "meta-stat");
    item.append(el("strong", "", String(value)));
    item.append(el("span", "", label));
    target.append(item);
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
  select.addEventListener("change", () => setAxisFilter(select.value));
}

function renderAxes() {
  const target = document.querySelector("#axis-list");
  target.innerHTML = "";
  state.map.axes.forEach((axis) => {
    const card = el("article", `axis-card ${axis.status}`);
    card.id = axisAnchorId(axis.id);
    card.append(el("h3", "", axis.title));
    card.append(el("p", "", axis.summary));
    const actions = el("div", "action-row");
    actions.append(actionButton("Themen dieses Bereichs", () => {
      setAxisFilter(axis.id);
      scrollToSection("index");
    }, "link-action"));
    actions.append(actionButton("In der Karte ansehen", () => openAxis(axis.id, { showInMap: true }), "text-link-action"));
    card.append(actions);
    target.append(card);
  });
}

function appendClusterButton(card, clusterId, text) {
  const button = el("button", "cluster-action", text);
  button.type = "button";
  button.addEventListener("click", () => focusCluster(clusterId));
  card.append(button);
}

function renderClusters() {
  const target = document.querySelector("#cluster-list");
  target.innerHTML = "";

  const allCard = el("article", `cluster-card ${state.activeCluster === "all" ? "active" : ""}`);
  allCard.append(el("p", "module-meta", "Gesamtblick"));
  allCard.append(el("h3", "", "Alle Lernwege"));
  allCard.append(el("p", "", "Zeigt alle Themen ohne Lernweg-Filter."));
  appendClusterButton(allCard, "all", "Alle Themen zeigen");
  target.append(allCard);

  state.network.clusters.forEach((cluster) => {
    const card = el("article", `cluster-card ${state.activeCluster === cluster.id ? "active" : ""}`);
    card.append(el("p", "module-meta", "Lernweg"));
    card.append(el("h3", "", cluster.title));
    card.append(el("p", "", cluster.insight));
    appendClusterButton(card, cluster.id, "Themen dieses Lernwegs zeigen");
    const details = document.createElement("details");
    const summary = document.createElement("summary");
    summary.textContent = "Themen dieses Lernwegs";
    details.append(summary);
    const topicList = el("ul", "compact-list");
    cluster.topics.forEach((topic) => {
      const item = el("li");
      item.append(actionButton(topic, () => openTopicByTitle(topic), "text-link-action"));
      topicList.append(item);
    });
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
        card.id = topicAnchorId(topic.id);
        card.append(el("p", "module-meta", axis.title));
        card.append(el("h3", "", topic.title));
        const detail = detailForTopic({ ...topic, axisId: axis.id, axisTitle: axis.title });
        if (detail?.summary) card.append(el("p", "topic-summary", detail.summary));
        if (topic.status === "background") {
          const tags = el("div", "tag-row");
          tags.append(el("span", "tag", "Rahmen"));
          card.append(tags);
        }
        if (state.activeContentLayer === "current-work") {
          const linkedWorks = currentWorksForTopic(topic.id);
          if (linkedWorks.length) {
            const currentBlock = el("div", "current-work-inline");
            currentBlock.append(el("h4", "", "Aktuelle Arbeit"));
            linkedWorks.forEach((work) => {
              currentBlock.append(actionButton(work.title, () => openCurrentWork(work.id), "text-link-action"));
            });
            card.append(currentBlock);
          }
        }
        if (detail) {
          const disclosure = el("details", "topic-detail");
          disclosure.append(el("summary", "", "Vertiefen"));
          renderKnowledgeDetail(disclosure, detail, { showTitle: false });
          card.append(disclosure);
        }
        const actions = el("div", "action-row compact-actions");
        actions.append(actionButton("In der Karte verorten", () => openTopic(topic.id, { showInMap: true }), "text-link-action"));
        card.append(actions);
        grid.append(card);
      });
  });
}

function bridgeRole(bridge) {
  if (state.activeCluster === "all") return "";
  if (bridge.from === state.activeCluster && bridge.to === state.activeCluster) return "innerhalb dieses Lernwegs";
  if (bridge.from === state.activeCluster) return "führt weiter";
  if (bridge.to === state.activeCluster) return "führt hierher";
  return "";
}

function bridgeClass(role) {
  if (role === "führt weiter") return "outgoing";
  if (role === "führt hierher") return "incoming";
  if (role === "innerhalb dieses Lernwegs") return "internal";
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
    if (role) roleLine.append(el("span", "bridge-role-badge", role));
    roleLine.append(el("span", "bridge-type", bridgeTypeLabel(bridge.type)));
    card.append(roleLine);
    card.append(el("h3", "", `${clusterById.get(bridge.from)} → ${clusterById.get(bridge.to)}`));
    card.append(el("p", "", bridge.relation));
    const actions = el("div", "action-row");
    actions.append(actionButton(`Zu „${clusterById.get(bridge.from)}“`, () => focusCluster(bridge.from), "text-link-action"));
    actions.append(actionButton(`Zu „${clusterById.get(bridge.to)}“`, () => focusCluster(bridge.to), "text-link-action"));
    card.append(actions);
    target.append(card);
  });
}

function targetAxisForHub(index, hub) {
  return index.byTarget?.[hub.targetId]?.axisId ?? "";
}

function bridgeTargetMeta(index, targetId) {
  return index?.byTarget?.[targetId] ?? null;
}

function bridgeTargetTitle(index, targetId) {
  return bridgeTargetMeta(index, targetId)?.targetTitle ?? targetId;
}

function visibleDetailBridgeHubs(index, activeAxis) {
  return (index.hubs ?? [])
    .filter((hub) => activeAxis === "all" || targetAxisForHub(index, hub) === activeAxis)
    .sort((left, right) => {
      const axisOrder = axisTitleById(targetAxisForHub(index, left)).localeCompare(axisTitleById(targetAxisForHub(index, right)), "de");
      return axisOrder || left.targetTitle.localeCompare(right.targetTitle, "de");
    });
}

function activeDetailBridgeAxisTitle(index) {
  if (state.activeDetailBridgeAxis === "all") return "alle Wissensbereiche";
  return (index.byTargetAxis ?? []).find((axis) => axis.axisId === state.activeDetailBridgeAxis)?.axisTitle ?? state.activeDetailBridgeAxis;
}

function renderDetailBridgeAxisFilter() {
  const select = document.querySelector("#detail-bridge-axis-filter");
  if (!select || !state.detailBridgeIndex) return;
  const current = select.value || state.activeDetailBridgeAxis;
  select.innerHTML = "";
  const allOption = el("option", "", "Alle Wissensbereiche");
  allOption.value = "all";
  select.append(allOption);
  (state.detailBridgeIndex.byTargetAxis ?? []).forEach((axis) => {
    const option = el("option", "", axis.axisTitle);
    option.value = axis.axisId;
    select.append(option);
  });
  state.activeDetailBridgeAxis = [...select.options].some((option) => option.value === current) ? current : "all";
  select.value = state.activeDetailBridgeAxis;
  select.onchange = () => {
    state.activeDetailBridgeAxis = select.value;
    state.activeDetailBridgeTarget = "";
    renderDetailBridgeIndex();
  };
}

function bridgeIncomingForTarget(index, targetId) {
  return (index.bridges ?? []).filter((bridge) => bridge.targetId === targetId);
}

function axisTitleById(axisId) {
  return state.map.axes.find((axis) => axis.id === axisId)?.title ?? axisId;
}

function hubRelationPreview(index, targetId) {
  const bridges = bridgeIncomingForTarget(index, targetId);
  return bridges.find((bridge) => bridge.relation?.trim()) ?? null;
}

function sourcePerspectivesForTarget(index, targetId) {
  const perspectives = new Map();
  bridgeIncomingForTarget(index, targetId).forEach((bridge) => {
    (bridge.sourceAxisIds ?? []).forEach((axisId) => {
      if (!perspectives.has(axisId)) perspectives.set(axisId, new Set());
      perspectives.get(axisId).add(bridge.sourceTitle);
    });
  });
  return [...perspectives.entries()]
    .map(([axisId, sourceTitles]) => ({ axisId, axisTitle: axisTitleById(axisId), sourceTitles: [...sourceTitles].sort((a, b) => a.localeCompare(b, "de")) }))
    .sort((left, right) => left.axisTitle.localeCompare(right.axisTitle, "de"));
}

function detailById(detailId) {
  return state.details.find((detail) => detail.id === detailId) ?? null;
}

function renderBridgeDetailCard(detailId) {
  const target = document.querySelector("#detail-bridge-detail-card");
  if (!target) return;
  target.innerHTML = "";
  if (!detailId) return;
  const detail = detailById(detailId);
  if (!detail) {
    target.append(el("p", "fineprint", "Die Vertiefung konnte nicht geladen werden."));
    return;
  }
  target.append(el("h4", "", "Geöffnete Vertiefung"));
  renderKnowledgeDetail(target, detail);
}

function openBridgeDetailCard(detailId) {
  state.activeDetailBridgeDetail = detailId;
  renderDetailBridgeIndex();
  document.querySelector("#detail-bridge-detail-card")?.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

function renderIncomingBridgeDetails(index, targetId) {
  const target = document.querySelector("#detail-bridge-incoming-list");
  if (!target) return;
  target.innerHTML = "";
  if (!targetId) {
    target.append(el("p", "fineprint", "Wähle einen zentralen Begriff, um die begründeten Zusammenhänge zu lesen."));
    renderBridgeDetailCard("");
    return;
  }

  const targetTitle = bridgeTargetTitle(index, targetId);
  const bridges = bridgeIncomingForTarget(index, targetId);
  if (!bridges.some((bridge) => bridge.sourceDetailId === state.activeDetailBridgeDetail)) {
    state.activeDetailBridgeDetail = "";
  }
  target.append(el("h4", "", `So hängt „${targetTitle}“ mit anderen Themen zusammen`));
  target.append(el("p", "fineprint", "Jede Aussage stammt aus einer fachlichen Vertiefung und erklärt eine konkrete Beziehung."));

  bridges.forEach((bridge) => {
    const card = el("article", "incoming-bridge-card");
    card.append(el("h5", "", `${bridge.sourceTitle} → ${targetTitle}`));
    card.append(el("p", "", bridge.relation));
    const button = el("button", `inline-action ${bridge.sourceDetailId === state.activeDetailBridgeDetail ? "active" : ""}`, `„${bridge.sourceTitle}“ vertiefen`);
    button.type = "button";
    button.onclick = () => openBridgeDetailCard(bridge.sourceDetailId);
    card.append(button);
    target.append(card);
  });
}

function renderDetailBridgeIndex() {
  const summary = document.querySelector("#detail-bridge-summary");
  const hubsTarget = document.querySelector("#detail-bridge-hub-list");
  const contextTarget = document.querySelector("#detail-bridge-axis-list");
  if (!summary || !hubsTarget || !contextTarget) return;
  hubsTarget.innerHTML = "";
  contextTarget.innerHTML = "";

  const index = state.detailBridgeIndex;
  if (!index) {
    summary.textContent = "Die Zusammenhänge konnten nicht geladen werden.";
    return;
  }

  const activeAxis = state.activeDetailBridgeAxis;
  let hubs = visibleDetailBridgeHubs(index, activeAxis);
  if (state.activeDetailBridgeTarget && !hubs.some((hub) => hub.targetId === state.activeDetailBridgeTarget)) {
    state.activeDetailBridgeTarget = "";
    state.activeDetailBridgeDetail = "";
    hubs = visibleDetailBridgeHubs(index, activeAxis);
  }
  const axisTitle = activeDetailBridgeAxisTitle(index);
  summary.textContent = activeAxis === "all"
    ? "Zentrale Begriffe bündeln Beziehungen aus mehreren Wissensbereichen. Die Karten zeigen jeweils eine konkrete Beispielaussage statt einer Rangzahl."
    : `Gezeigt werden zentrale Begriffe aus „${axisTitle}“. Die Beispielaussagen erklären, warum andere Themen dorthin führen.`;

  if (!hubs.length) {
    hubsTarget.append(el("p", "fineprint", "Für diesen Wissensbereich sind keine zentralen Begriffe hinterlegt."));
  }

  hubs.forEach((hub) => {
    const card = el("button", `relation-card hub-button network ${hub.targetId === state.activeDetailBridgeTarget ? "active" : ""}`);
    card.type = "button";
    card.setAttribute("aria-pressed", hub.targetId === state.activeDetailBridgeTarget ? "true" : "false");
    card.onclick = () => {
      state.activeDetailBridgeTarget = hub.targetId;
      state.activeDetailBridgeDetail = "";
      renderDetailBridgeIndex();
    };
    const targetMeta = bridgeTargetMeta(index, hub.targetId);
    card.append(el("span", "hub-axis", axisTitleById(targetMeta?.axisId ?? "")));
    card.append(el("span", "hub-title", hub.targetTitle));
    const preview = hubRelationPreview(index, hub.targetId);
    if (preview) {
      card.append(el("span", "hub-insight", preview.relation));
      card.append(el("span", "hub-source", `Beispiel aus „${preview.sourceTitle}“`));
    }
    hubsTarget.append(card);
  });

  const perspectives = sourcePerspectivesForTarget(index, state.activeDetailBridgeTarget);
  if (!state.activeDetailBridgeTarget) {
    contextTarget.append(el("p", "fineprint", "Wähle links einen Begriff, um seine fachlichen Herkunftsbereiche zu sehen."));
  } else if (!perspectives.length) {
    contextTarget.append(el("p", "fineprint", "Für diesen Begriff sind keine Herkunftsbereiche hinterlegt."));
  }
  perspectives.forEach((perspective) => {
    const card = el("article", "connection-context-card");
    card.append(el("h4", "", perspective.axisTitle));
    const examples = perspective.sourceTitles.slice(0, 4);
    const suffix = perspective.sourceTitles.length > examples.length ? " und weitere" : "";
    card.append(el("p", "", `${examples.join(", ")}${suffix}`));
    contextTarget.append(card);
  });

  renderIncomingBridgeDetails(index, state.activeDetailBridgeTarget);
  renderBridgeDetailCard(state.activeDetailBridgeDetail);
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
  target.textContent = `${coverage.linked_doc_ids.length} Quellen sind an Themen gebunden. Das Wissensnetz ordnet ${netCoverage.topic_count} Themen in ${netCoverage.cluster_count} Lernwege.${focus}${detailLine} Bewusst nicht als eigenes Thema modelliert: ${omitted}.`;
}

function renderSurfaces() {
  const target = document.querySelector("#surface-list");
  if (!target) return;
  target.innerHTML = "";
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
        const detailResponse = await fetch(sitePath(entry.path));
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
  const scored = state.details.map((detail) => {
    const topicExact = Boolean(topicNorm) && (detail.topicIds ?? []).some((topic) => normalizeText(topic) === topicNorm);
    const topicTitle = (detail.topicIds ?? []).some((topic) => normalizeText(topic) === titleNorm);
    const titleMatch = Boolean(titleNorm) && (normalizeText(detail.title).includes(titleNorm) || titleNorm.includes(normalizeText(detail.title)));
    const axisMatch = Boolean(axisNorm) && (detail.axisIds ?? []).some((axis) => normalizeText(axis) === axisNorm);
    const sourceMatch = (detail.sourceRefs ?? []).some((source) => sourceSet.has(String(source)));
    let score = 0;
    if (topicExact) score += 100;
    if (topicTitle) score += 60;
    if (titleMatch) score += 50;
    if (axisMatch) score += 10;
    if (sourceMatch) score += 1;
    return { detail, score };
  }).filter((entry) => entry.score > 0);
  scored.sort((left, right) => right.score - left.score || left.detail.title.localeCompare(right.detail.title, "de"));
  return scored.map((entry) => entry.detail);
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

function renderKnowledgeDetail(target, detail, { showTitle = true } = {}) {
  const card = el("article", "knowledge-detail-card");
  if (showTitle) card.append(el("h4", "", detail.title));
  card.append(el("p", "", detail.summary));
  appendListSection(card, "Kernideen", detail.coreIdeas);
  appendListSection(card, "Praxisanker", detail.practiceAnchors);
  appendListSection(card, "Typische Fehlannahmen", detail.commonMisunderstandings);
  appendListSection(card, "Offene Fragen", detail.openQuestions);
  if (detail.bridges?.length) {
    const section = el("div", "detail-subsection");
    section.append(el("h5", "", "Brücken"));
    detail.bridges.forEach((bridge) => {
      const item = el("div", "bridge-target-row");
      const label = el("span");
      label.append(el("strong", "", bridgeTargetTitle(state.detailBridgeIndex, bridge.targetId)));
      label.append(document.createTextNode(`: ${bridge.relation}`));
      item.append(label);
      section.append(item);
    });
    card.append(section);
  }
  const meta = el("details", "detail-meta");
  meta.append(el("summary", "", "Nachweise"));
  meta.append(el("p", "fineprint", `Quellen: ${(detail.sourceRefs ?? []).join(", ")} · Exzerpte: ${(detail.excerptRefs ?? []).join(", ")} · Stand: ${detail.detailStatus ?? "draft"}`));
  card.append(meta);
  target.append(card);
}

const theoryKindLabels = {
  theory: "Theorie",
  model: "Modell",
  approach: "Pädagogischer Ansatz",
  concept: "Theoretisches Kernkonzept",
};

const theoryEvidenceLabels = {
  explained: "im Korpus erklärt",
  applied: "angewandt oder knapp eingeordnet",
  "named-only": "nur genannt",
};

function theoryAxisTitle(axisId) {
  return state.theoryCatalog?.vocabulary?.axes?.[axisId] ?? axisTitleById(axisId);
}

function theorySearchText(entry) {
  return normalizeText([
    entry.title,
    ...(entry.aliases ?? []),
    ...(entry.attributedTo ?? []),
    entry.summary,
    ...(entry.coreIdeas ?? []),
    ...(entry.pedagogicalRelevance ?? []),
    ...(entry.cautions ?? []),
  ].join(" "));
}

function visibleTheories(status) {
  const query = normalizeText(state.theoryQuery);
  return (state.theoryCatalog?.entries ?? [])
    .filter((entry) => entry.evidenceStatus === status || (status === "substantive" && entry.evidenceStatus !== "named-only"))
    .filter((entry) => state.activeTheoryAxis === "all" || (entry.axisIds ?? []).includes(state.activeTheoryAxis))
    .filter((entry) => state.activeTheoryKind === "all" || entry.kind === state.activeTheoryKind)
    .filter((entry) => !query || theorySearchText(entry).includes(query))
    .sort((left, right) => {
      const axisOrder = theoryAxisTitle(left.axisIds[0]).localeCompare(theoryAxisTitle(right.axisIds[0]), "de");
      return axisOrder || left.title.localeCompare(right.title, "de");
    });
}

function theorySourceLabel(source) {
  return `${source.docId} · Zeilen ${source.startLine}–${source.endLine}`;
}

function openTheory(theoryId) {
  let target = document.querySelector(`#theory-${normalizeText(theoryId)}`);
  if (!target) {
    state.activeTheoryAxis = "all";
    state.activeTheoryKind = "all";
    state.theoryQuery = "";
    const axisSelect = document.querySelector("#theory-axis-filter");
    const kindSelect = document.querySelector("#theory-kind-filter");
    const search = document.querySelector("#theory-search");
    if (axisSelect) axisSelect.value = "all";
    if (kindSelect) kindSelect.value = "all";
    if (search) search.value = "";
    renderTheories();
    target = document.querySelector(`#theory-${normalizeText(theoryId)}`);
  }
  target?.closest(".theory-named-only")?.setAttribute("open", "");
  target?.scrollIntoView({ behavior: "smooth", block: "center", inline: "nearest" });
  setTimeout(() => flashElement(target), 120);
}

function renderTheoryCard(entry) {
  const card = el("article", "theory-card");
  card.id = `theory-${normalizeText(entry.id)}`;
  const meta = el("p", "theory-meta");
  meta.append(el("span", "theory-kind", theoryKindLabels[entry.kind] ?? entry.kind));
  meta.append(el("span", "theory-evidence", theoryEvidenceLabels[entry.evidenceStatus] ?? entry.evidenceStatus));
  card.append(meta);
  card.append(el("p", "theory-axis", theoryAxisTitle(entry.axisIds[0])));
  card.append(el("h3", "", entry.title));
  if (entry.attributedTo?.length) card.append(el("p", "theory-people", entry.attributedTo.join(", ")));
  card.append(el("p", "theory-summary", entry.summary));

  const disclosure = el("details", "theory-detail");
  disclosure.append(el("summary", "", "Einordnung lesen"));
  appendListSection(disclosure, "Kernideen", entry.coreIdeas);
  appendListSection(disclosure, "Pädagogische Bedeutung", entry.pedagogicalRelevance);
  appendListSection(disclosure, "Einordnung und Grenzen", entry.cautions);
  if (entry.sourceMentions?.length) {
    const sourceSection = el("div", "detail-subsection");
    sourceSection.append(el("h5", "", "Fundstellen im Korpus"));
    const sourceList = el("ul", "compact-list theory-sources");
    entry.sourceMentions.forEach((source) => sourceList.append(el("li", "", theorySourceLabel(source))));
    sourceSection.append(sourceList);
    disclosure.append(sourceSection);
  }
  if (entry.relatedIds?.length) {
    const related = el("div", "detail-subsection");
    related.append(el("h5", "", "Verwandte Positionen"));
    const actions = el("div", "action-row");
    const byId = new Map((state.theoryCatalog?.entries ?? []).map((item) => [item.id, item]));
    entry.relatedIds.forEach((id) => {
      const item = byId.get(id);
      if (item) actions.append(actionButton(item.title, () => openTheory(id), "text-link-action"));
    });
    related.append(actions);
    disclosure.append(related);
  }
  card.append(disclosure);
  return card;
}

function renderTheoryFilters() {
  const axisSelect = document.querySelector("#theory-axis-filter");
  const kindSelect = document.querySelector("#theory-kind-filter");
  const search = document.querySelector("#theory-search");
  if (!axisSelect || !kindSelect || !search || !state.theoryCatalog) return;

  axisSelect.querySelectorAll("option:not([value='all'])").forEach((option) => option.remove());
  Object.entries(state.theoryCatalog.vocabulary.axes).forEach(([id, title]) => {
    const option = el("option", "", title);
    option.value = id;
    axisSelect.append(option);
  });
  kindSelect.querySelectorAll("option:not([value='all'])").forEach((option) => option.remove());
  Object.entries(theoryKindLabels).forEach(([id, title]) => {
    const option = el("option", "", title);
    option.value = id;
    kindSelect.append(option);
  });
  axisSelect.onchange = () => {
    state.activeTheoryAxis = axisSelect.value;
    renderTheories();
  };
  kindSelect.onchange = () => {
    state.activeTheoryKind = kindSelect.value;
    renderTheories();
  };
  search.oninput = () => {
    state.theoryQuery = search.value;
    renderTheories();
  };
}

function renderTheories() {
  const target = document.querySelector("#theory-list");
  const namedTarget = document.querySelector("#theory-named-list");
  const intro = document.querySelector("#theory-intro");
  const empty = document.querySelector("#theory-empty");
  if (!target || !namedTarget || !intro || !empty) return;
  target.innerHTML = "";
  namedTarget.innerHTML = "";
  if (!state.theoryCatalog) {
    intro.textContent = "Der Theoriekatalog konnte nicht geladen werden.";
    return;
  }

  const substantive = visibleTheories("substantive");
  const namedOnly = visibleTheories("named-only");
  intro.textContent = "Kurzthesen zeigen den im Quellenkorpus belegten Ausschnitt. Kernideen, pädagogische Bedeutung, Grenzen und Fundstellen lassen sich jeweils aufklappen.";
  substantive.forEach((entry) => target.append(renderTheoryCard(entry)));
  empty.hidden = substantive.length > 0;

  if (!namedOnly.length) {
    namedTarget.append(el("p", "fineprint", "Für diese Auswahl gibt es keine nur erwähnte Position."));
  } else {
    namedOnly.forEach((entry) => namedTarget.append(renderTheoryCard(entry)));
  }
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

function renderCanvasDetail(node) {
  const target = document.querySelector("#canvas-detail");
  target.innerHTML = "";
  if (!node) {
    target.append(el("h3", "", "Begriff auswählen"));
    target.append(el("p", "", "Klicke einen Begriff in der Lernkarte. Rechts erscheinen Erklärung und Vertiefung."));
    return;
  }

  const context = findNodeContext(node);
  const label = canvasNodeLabel(node);
  const heading = context.topic?.title ?? context.axis?.title ?? label;
  const sources = context.topic?.sources ?? context.axis?.sources ?? [];
  const summary = context.topic
    ? `Dieser Inhalt gehört zum Wissensbereich „${context.topic.axisTitle}“.`
    : context.axis?.summary ?? "Dieser Begriff gehört zur ausgewählten Lernkarte, ist aber noch keinem Wissensbereich eindeutig zugeordnet.";
  const topicOrAxisId = context.topic?.id ?? context.axis?.id ?? node.id;
  const excerpts = matchingExcerpts(sources, heading, topicOrAxisId);
  const details = matchingDetails(sources, heading, context.topic?.id ?? "", context.axis?.id ?? "");

  target.append(el("h3", "", heading));
  target.append(el("p", "", summary));
  if (context.axis) {
    const actions = el("div", "action-row");
    actions.append(actionButton("Themen dieses Bereichs", () => {
      setAxisFilter(context.axis.id);
      scrollToSection("index");
    }, "link-action"));
    target.append(actions);
  }

  const detailBlock = el("article", "detail-note");
  detailBlock.append(el("h4", "", "Vertiefung"));
  if (details.length) {
    details.slice(0, 2).forEach((detail) => renderKnowledgeDetail(detailBlock, detail));
  } else {
    detailBlock.append(el("p", "", "Zu diesem Begriff ist noch keine Vertiefung hinterlegt."));
  }
  target.append(detailBlock);

  if (excerpts.length) {
    const excerptMeta = el("details", "detail-meta");
    excerptMeta.append(el("summary", "", "Quellenhinweise"));
    excerpts.slice(0, 3).forEach((excerpt) => {
      const item = el("div", "excerpt-card");
      item.append(el("strong", "", excerptTitle(excerpt)));
      item.append(el("p", "", excerptBody(excerpt)));
      const practiceUse = excerptPracticeUse(excerpt);
      if (practiceUse) item.append(el("p", "", practiceUse));
      item.append(el("p", "fineprint", `${excerptDocId(excerpt) || "doc-ID offen"} · ${excerptLocator(excerpt)} · ${excerptStatus(excerpt)}`));
      excerptMeta.append(item);
    });
    target.append(excerptMeta);
  }
}

async function openCanvasNode(nodeId) {
  const needsLoad = state.canvas.activeView !== "learning-map" || !state.canvas.data?.nodes?.length;
  state.canvas.activeView = "learning-map";
  const select = document.querySelector("#canvas-view-select");
  if (select) select.value = state.canvas.activeView;
  if (needsLoad) await loadCanvasView();
  const node = state.canvas.data?.nodes?.find((item) => item.id === nodeId);
  if (!node) return;
  state.canvas.activeNodeId = node.id;
  renderCanvasSurface();
  renderCanvasDetail(node);
  scrollToSection("karte");
}

async function loadCanvasView() {
  const view = activeCanvasView();
  const status = document.querySelector("#canvas-status");
  status.hidden = false;
  status.textContent = `${view.label} wird geladen…`;
  try {
    const response = await fetch(view.url);
    if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
    state.canvas.data = await response.json();
    state.canvas.activeNodeId = null;
    renderCanvasSurface();
    renderCanvasDetail(null);
    status.textContent = "";
    status.hidden = true;
  } catch (error) {
    state.canvas.data = null;
    document.querySelector("#canvas-viewer").textContent = "Die Lernkarte konnte nicht geladen werden.";
    status.hidden = false;
    status.textContent = "Diese Lernkarte ist derzeit nicht verfügbar.";
    console.error("Fehler beim Laden der Lernkarte", view.url, error);
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
    target.textContent = "Diese Lernkarte enthält keine Begriffe.";
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
  svg.setAttribute("aria-label", "Interaktive Lernkarte");

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

    nodeLayer.append(group);
  });
  svg.append(nodeLayer);
  target.append(svg);
}

async function boot() {
  const [map, network, detailBridgeIndex, learningFieldFocus, theoryCatalog, sourceSummary, excerpts, details, currentWork] = await Promise.all([
    fetch(learningMapUrl).then((res) => res.json()),
    fetch(knowledgeNetworkUrl).then((res) => res.json()),
    fetch(detailBridgeIndexUrl).then((res) => res.json()),
    fetch(learningFieldFocusUrl).then((res) => res.json()),
    fetch(theoryCatalogUrl).then((res) => res.json()),
    fetch(sourceSummaryUrl).then((res) => res.json()).catch(() => null),
    loadExcerpts(),
    loadDetails(),
    loadCurrentWork(),
  ]);
  state.map = map;
  state.network = network;
  state.detailBridgeIndex = detailBridgeIndex;
  state.learningFieldFocus = learningFieldFocus;
  state.theoryCatalog = theoryCatalog;
  state.currentWorkIndex = currentWork.index;
  state.currentWorks = currentWork.works;
  canvasViews = [...baseCanvasViews, ...focusCanvasViews(learningFieldFocus)];
  state.excerpts = excerpts;
  state.details = details;
  renderSourceSummary(sourceSummary);
  renderStats();
  renderCanvasSelector();
  await loadCanvasView();
  renderAxisFilter();
  renderAxes();
  renderClusters();
  renderContentLayerSwitch();
  renderCurrentWork();
  renderTopics();
  renderTheoryFilters();
  renderTheories();
  renderRelations();
  renderDetailBridgeAxisFilter();
  renderDetailBridgeIndex();
  renderCoverage();
  renderSurfaces();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>Fehler beim Laden der Lernlandkarte: ${error.message}</pre>`;
});
