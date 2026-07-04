const learningMapUrl = "/data/learning-map.v1.json";
const sourceSummaryUrl = "/data/source-summary.json";

const state = {
  map: null,
  activeAxis: "all",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function unique(values) {
  return [...new Set(values.filter(Boolean))];
}

function topicCount(axis) {
  return axis.topics?.length ?? 0;
}

function allTopics() {
  return state.map.axes.flatMap((axis) => axis.topics.map((topic) => ({ ...topic, axisId: axis.id, axisTitle: axis.title })));
}

function renderSourceSummary(summary) {
  const target = document.querySelector("#source-note");
  const map = state.map;
  const topicTotal = allTopics().length;
  const linkedDocs = map.coverage?.linked_doc_ids?.length ?? 0;
  const fileCount = summary?.totals?.files ?? "29";
  const words = summary?.totals?.word_count ?? "325.811";
  target.textContent = `${map.axes.length} Sinnachsen, ${topicTotal} Themenknoten, ${linkedDocs} Quellenbezüge aus ${fileCount} PDFs. Rohtexte bleiben lokal.`;
  const detail = document.querySelector("#source-detail");
  detail.textContent = `Maschinenlesbarer Arbeitsstand: ${words.toLocaleString?.("de-DE") ?? words} Wörter laut Inventar; diese Webfläche zeigt keine Rohtexte, sondern strukturierte Wissensknoten.`;
}

function renderStats() {
  const target = document.querySelector("#map-stats");
  const topics = allTopics();
  const background = topics.filter((topic) => topic.status === "background").length;
  const learned = topics.filter((topic) => topic.status === "learned").length;
  target.innerHTML = "";
  [
    ["Sinnachsen", state.map.axes.length],
    ["Themen", topics.length],
    ["Gelernt", learned],
    ["Rahmen", background],
  ].forEach(([label, value]) => {
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
    const sources = el("p", "source-line", `Quellen: ${axis.sources.join(", ")}`);
    card.append(sources);
    target.append(card);
  });
}

function renderTopics() {
  const grid = document.querySelector("#topic-grid");
  grid.innerHTML = "";
  const axes = state.activeAxis === "all" ? state.map.axes : state.map.axes.filter((axis) => axis.id === state.activeAxis);
  axes.forEach((axis) => {
    axis.topics.forEach((topic) => {
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

function renderRelations() {
  const target = document.querySelector("#relation-list");
  target.innerHTML = "";
  const axisById = new Map(state.map.axes.map((axis) => [axis.id, axis.title]));
  state.map.edges.forEach((edge) => {
    const card = el("article", "relation-card");
    card.append(el("h3", "", `${axisById.get(edge.from)} → ${axisById.get(edge.to)}`));
    card.append(el("p", "", edge.label));
    target.append(card);
  });
}

function renderCoverage() {
  const target = document.querySelector("#coverage-note");
  const coverage = state.map.coverage;
  const omitted = coverage?.intentionally_unmodeled_doc_ids?.join(", ") || "keine";
  target.textContent = `${coverage.linked_doc_ids.length} doc-IDs sind an Themen gebunden. Bewusst nicht als Themenknoten modelliert: ${omitted}. ${coverage.reason}`;
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
  const [map, sourceSummary] = await Promise.all([
    fetch(learningMapUrl).then((res) => res.json()),
    fetch(sourceSummaryUrl).then((res) => res.json()).catch(() => null),
  ]);
  state.map = map;
  renderSourceSummary(sourceSummary);
  renderStats();
  renderAxisFilter();
  renderAxes();
  renderTopics();
  renderRelations();
  renderCoverage();
  renderSurfaces();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>Fehler beim Laden der Lernlandkarte: ${error.message}</pre>`;
});
