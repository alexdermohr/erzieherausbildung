const moduleDataUrl = "/data/module-map.json";
const sourceSummaryUrl = "/data/source-summary.json";

const state = {
  modules: [],
  axes: [],
  recommendedVisuals: [],
  activeAxis: "all",
};

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function axisLabel(id) {
  const axis = state.axes.find((item) => item.id === id);
  return axis ? axis.label : id;
}

function renderAxisFilter() {
  const select = document.querySelector("#axis-filter");
  state.axes.forEach((axis) => {
    const option = el("option", "", axis.label);
    option.value = axis.id;
    select.appendChild(option);
  });
  select.addEventListener("change", () => {
    state.activeAxis = select.value;
    renderModules();
  });
}

function renderAxes() {
  const target = document.querySelector("#axis-list");
  target.innerHTML = "";
  state.axes.forEach((axis) => {
    const card = el("article", "axis-card");
    card.append(el("h3", "", axis.label));
    card.append(el("p", "", axis.question));
    target.append(card);
  });
}

function renderModules() {
  const grid = document.querySelector("#module-grid");
  grid.innerHTML = "";
  const filtered = state.activeAxis === "all"
    ? state.modules
    : state.modules.filter((module) => module.axes.includes(state.activeAxis));

  filtered
    .slice()
    .sort((a, b) => b.visualWeight - a.visualWeight || a.id.localeCompare(b.id))
    .forEach((module) => {
      const card = el("article", "module-card");
      card.dataset.module = module.id;
      const meta = el("p", "module-meta", `${module.semester} · ${module.id.toUpperCase()} · Gewicht ${module.visualWeight}/5`);
      const title = el("h3", "", module.title);
      const role = el("p", "", module.role);
      const tags = el("div", "tag-row");
      module.axes.forEach((axisId) => tags.append(el("span", "tag", axisLabel(axisId))));
      const questions = el("ul", "question-list");
      module.coreQuestions.forEach((question) => questions.append(el("li", "", question)));
      const confidence = el("p", "confidence", `Strukturvertrauen: ${Math.round(module.confidence * 100)}%`);
      card.append(meta, title, role, tags, questions, confidence);
      grid.append(card);
    });
}

function renderVisuals() {
  const target = document.querySelector("#visuals-list");
  state.recommendedVisuals.forEach((visual) => {
    const card = el("article", "visual-card");
    card.append(el("h3", "", visual.surface));
    card.append(el("p", "", visual.use));
    card.append(el("span", "status", visual.status));
    target.append(card);
  });
}

function renderSourceSummary(summary) {
  const target = document.querySelector("#source-note");
  if (!summary || summary.status === "placeholder-before-local-scan") {
    target.textContent = "Noch keine lokale Aggregation erzeugt. Scanner ausführen, um Modul- und Dateityp-Zählungen zu aktualisieren.";
    return;
  }

  const moduleCount = summary.semesters?.reduce((acc, semester) => acc + semester.modules.length, 0) ?? 0;
  const fileCount = summary.totals?.files ?? "unbekannt";
  target.textContent = `${moduleCount} Modul-/Ordnercluster, ${fileCount} Dateien aggregiert. Keine Rohdateien im Repo.`;
}

async function boot() {
  const [moduleMap, sourceSummary] = await Promise.all([
    fetch(moduleDataUrl).then((res) => res.json()),
    fetch(sourceSummaryUrl).then((res) => res.json()).catch(() => null),
  ]);

  state.modules = moduleMap.modules;
  state.axes = moduleMap.axes;
  state.recommendedVisuals = moduleMap.recommendedVisuals;

  renderSourceSummary(sourceSummary);
  renderAxisFilter();
  renderAxes();
  renderModules();
  renderVisuals();
}

boot().catch((error) => {
  document.body.innerHTML = `<pre>Fehler beim Laden der Lernlandkarte: ${error.message}</pre>`;
});
