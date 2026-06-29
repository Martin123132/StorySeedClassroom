const pageTitles = {
  start: ["Start", "Ready for a classroom prompt"],
  setup: ["Class Setup", "Shape the class task"],
  generate: ["Generate", "Build the prompt"],
  review: ["Review", "Check, copy, print, or save"],
  seeds: ["Seed Bank", "Edit the local ingredients"],
  favourites: ["Favourites", "Reuse saved prompts"],
};

let state = null;
let currentPrompt = null;
let lastExport = null;
let currentPage = "start";
let currentReviewView = "student";
let safetyReport = null;
let lastTrafficItems = [];
let nextActionPage = "generate";
let favourites = [];

const zoneAssets = [
  "/static/assets/storyseed-app-icon.png",
  "/static/assets/storyseed-world-wallpaper.jpg",
  "/static/assets/storyseed-mission-lane.jpg",
  "/static/assets/storyseed-reuse-shelf.jpg",
  "/static/assets/storyseed-prompt-forge.jpg",
  "/static/assets/storyseed-route-map.jpg",
  "/static/assets/storyseed-zone-setup.jpg",
  "/static/assets/storyseed-zone-generate.jpg",
  "/static/assets/storyseed-zone-review.jpg",
  "/static/assets/storyseed-zone-seeds.jpg",
  "/static/assets/storyseed-zone-favourites.jpg",
];

const routeStops = [
  { label: "Setup", item: "setup", page: "setup", x: "18%", y: "68%" },
  { label: "Build", item: "settings", page: "generate", x: "42%", y: "47%" },
  { label: "Review", item: "generated", page: "review", x: "61%", y: "36%" },
  { label: "Print", item: "export", page: "review", x: "70%", y: "76%" },
  { label: "Reuse", item: "reuse", page: "favourites", x: "88%", y: "55%" },
];

const missionStops = [
  { label: "Setup", item: "setup", page: "setup", command: "Shape the class" },
  { label: "Build", item: "settings", page: "generate", command: "Choose the seed" },
  { label: "Review", item: "generated", page: "review", command: "Check the task" },
  { label: "Print", item: "export", page: "review", command: "Make a copy" },
  { label: "Reuse", item: "reuse", page: "favourites", command: "Save the win" },
];

const navStatusItems = {
  start: null,
  setup: "setup",
  generate: "settings",
  review: "generated",
  seeds: "safety",
  favourites: "reuse",
};

const zoneBriefs = {
  start: {
    step: "Checkpoint 1 of 6",
    title: "Start on the classroom route.",
    hint: "Generate fast, or choose a checkpoint from the route map.",
    item: "generated",
  },
  setup: {
    step: "Checkpoint 2 of 6",
    title: "Set the class shape.",
    hint: "Age, subject, and tone are enough. Then move to Generate.",
    item: "setup",
  },
  generate: {
    step: "Checkpoint 3 of 6",
    title: "Build one useful prompt.",
    hint: "Pick a mode, adjust creativity if needed, then generate the prompt.",
    item: "settings",
  },
  review: {
    step: "Checkpoint 4 of 6",
    title: "Check it before class.",
    hint: "Read the student view and teacher notes, then save or export.",
    item: "generated",
  },
  seeds: {
    step: "Optional workshop",
    title: "Tune the local seed bank.",
    hint: "Edit ingredients only when you want a different classroom world.",
    item: "safety",
  },
  favourites: {
    step: "Reuse shelf",
    title: "Return to saved prompts.",
    hint: "Open a favourite when you want to reuse a proven classroom task.",
    item: "reuse",
  },
};

const el = (id) => document.getElementById(id);

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "content-type": "application/json" },
    ...options,
  });
  const data = await response.json();
  if (!data.ok) {
    throw new Error(data.error || "StorySeed request failed");
  }
  return data;
}

function payload(value) {
  return { method: "POST", body: JSON.stringify(value) };
}

async function init() {
  preloadZoneAssets();
  bindNavigation();
  bindControls();
  await loadState();
  await loadSafety();
  await loadDoctor();
  await loadFavourites();
  renderTraffic();
  setPage("start");
}

function bindNavigation() {
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.addEventListener("click", () => setPage(button.dataset.page));
  });
  document.querySelectorAll(".tab").forEach((button) => {
    button.addEventListener("click", () => setTab(button.dataset.tab));
  });
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.addEventListener("click", () => setReviewView(button.dataset.reviewView));
  });
}

function bindControls() {
  el("nextStep").addEventListener("click", goNextStep);
  el("startGenerateButton").addEventListener("click", generatePrompt);
  el("generateButton").addEventListener("click", generatePrompt);
  el("sameSeedButton").addEventListener("click", regenerateSameSeed);
  el("reviewSameSeedButton").addEventListener("click", regenerateSameSeed);
  el("copyButton").addEventListener("click", copyPrompt);
  el("saveButton").addEventListener("click", saveFavourite);
  el("exportTxtButton").addEventListener("click", () => exportPrompt("txt"));
  el("exportHtmlButton").addEventListener("click", () => exportPrompt("html"));
  el("printWorksheetButton").addEventListener("click", printWorksheet);
  el("openLatestWorksheetButton").addEventListener("click", () => openLatestWorksheet());
  el("openExportsButton").addEventListener("click", openExports);
  el("saveSeedsButton").addEventListener("click", saveSeeds);
  el("resetSeedsButton").addEventListener("click", resetSeeds);
  el("creativityInput").addEventListener("input", () => {
    el("creativityValue").textContent = el("creativityInput").value;
    renderTraffic();
  });
  ["ageBandInput", "subjectInput", "toneInput", "modeInput", "seedInput", "lockSeedInput"].forEach((id) => {
    el(id).addEventListener("change", renderTraffic);
    el(id).addEventListener("input", renderTraffic);
  });
}

function setPage(page) {
  currentPage = pageTitles[page] ? page : "start";
  document.body.dataset.page = currentPage;
  document.querySelectorAll(".page").forEach((section) => {
    section.classList.toggle("active", section.id === `page-${currentPage}`);
  });
  document.querySelectorAll(".nav-button").forEach((button) => {
    button.classList.toggle("active", button.dataset.page === currentPage);
  });
  const [label, title] = pageTitles[currentPage] || pageTitles.start;
  el("sectionLabel").textContent = label;
  el("pageTitle").textContent = title;
  if (currentPage === "favourites") {
    renderFavourites(favourites);
  }
  renderTraffic();
}

function preloadZoneAssets() {
  zoneAssets.forEach((src) => {
    const image = new Image();
    image.decoding = "async";
    image.src = src;
  });
}

function goNextStep() {
  setPage(el("nextStep").dataset.page || nextActionPage || nextRoute(lastTrafficItems).target);
}

function setTab(tab) {
  document.querySelectorAll(".tab").forEach((button) => button.classList.toggle("active", button.dataset.tab === tab));
  document.querySelectorAll(".editor").forEach((editor) => editor.classList.toggle("active", editor.id === `${tab}Editor`));
}

async function loadState() {
  const data = await api("/api/state");
  state = data.state;
  renderSeedEditors();
}

async function loadDoctor() {
  const data = await api("/api/doctor");
  el("doctorStatus").textContent = `Local only - v${data.version}`;
}

async function loadSafety() {
  const data = await api("/api/safety");
  safetyReport = data.safety;
  renderSafety();
}

function setupValues() {
  return {
    age_band: el("ageBandInput").value,
    subject: el("subjectInput").value,
    tone: el("toneInput").value,
    mode: el("modeInput").value,
    creativity: Number(el("creativityInput").value),
    seed: el("seedInput").value.trim(),
  };
}

function generateOptions(forceSeed = false) {
  const values = setupValues();
  const shouldUseSeed = forceSeed || el("lockSeedInput").checked || values.seed;
  return {
    age_band: values.age_band,
    subject: values.subject,
    tone: values.tone,
    mode: values.mode,
    creativity: values.creativity,
    seed: shouldUseSeed ? Number(values.seed || Date.now() % 1000000) : undefined,
  };
}

async function generatePrompt() {
  const data = await api("/api/generate", payload(generateOptions(false)));
  currentPrompt = data.prompt;
  lastExport = null;
  el("seedInput").value = currentPrompt.seed;
  renderPrompt();
  renderTraffic();
  setPage("review");
}

async function regenerateSameSeed() {
  if (currentPrompt) {
    el("seedInput").value = currentPrompt.seed;
  }
  const data = await api("/api/generate", payload(generateOptions(true)));
  currentPrompt = data.prompt;
  lastExport = null;
  renderPrompt();
  renderTraffic();
  setPage("review");
}

function renderPrompt() {
  if (!currentPrompt) {
    return;
  }
  el("promptTitle").textContent = currentPrompt.title;
  el("promptMeta").textContent = `${currentPrompt.mode} | ${currentPrompt.age_band} | ${currentPrompt.subject} | seed ${currentPrompt.seed}`;
  el("promptOutput").textContent = currentPrompt.prompt;
  el("startPreview").textContent = currentPrompt.prompt.split("\n").slice(0, 9).join("\n");
  el("traceOutput").innerHTML = currentPrompt.trace_lines.map((line) => `<p>${escapeHtml(line)}</p>`).join("");
  el("teacherOutput").innerHTML = teacherMarkup(currentPrompt);
  el("actionMessage").textContent = "Prompt ready.";
  el("openExportsButton").hidden = true;
  el("openLatestWorksheetButton").hidden = true;
  renderReviewStation();
  setReviewView("student");
}

function renderTraffic() {
  const setup = setupValues();
  const safetyStatus = safetyReport?.status || "green";
  const safetyDetail = safetyReport ? safetyReport.summary : "Checking seed bank safety.";
  const favouriteCount = favourites.length;
  const items = [
    {
      id: "setup",
      name: "Class Setup",
      status: setup.age_band && setup.subject && setup.tone ? "green" : "red",
      detail: `${setup.age_band || "Age"} | ${setup.subject || "Subject"} | ${setup.tone || "Tone"}`,
      target: "setup",
    },
    {
      id: "settings",
      name: "Prompt Settings",
      status: setup.mode ? "green" : "red",
      detail: `${setup.mode || "Choose a mode"} | creativity ${setup.creativity}`,
      target: "generate",
    },
    {
      id: "generated",
      name: "Generated Prompt",
      status: currentPrompt ? "green" : "red",
      detail: currentPrompt ? currentPrompt.title : "Generate before review.",
      target: currentPrompt ? "review" : "generate",
    },
    {
      id: "safety",
      name: "Seed Bank Safety",
      status: safetyStatus,
      detail: safetyDetail,
      target: "seeds",
    },
    {
      id: "export",
      name: "Printable Export",
      status: lastExport ? "green" : currentPrompt ? "amber" : "red",
      detail: lastExport ? `Saved as ${lastExport.format.toUpperCase()}` : currentPrompt ? "Ready to export." : "Export appears after generation.",
      target: "review",
    },
    {
      id: "reuse",
      name: "Reuse Shelf",
      status: favouriteCount ? "green" : currentPrompt ? "amber" : "red",
      detail: favouriteCount ? favouriteCountText(favouriteCount) : currentPrompt ? "Save a favourite for later." : "Save appears after review.",
      target: favouriteCount ? "favourites" : "review",
    },
  ];
  lastTrafficItems = items;
  const route = nextRoute(items);
  nextActionPage = route.target;
  el("trafficList").innerHTML = items
    .map(
      (item) => `
      <button type="button" class="traffic-item" data-page="${item.target}" aria-label="Open ${escapeHtml(item.name)}">
        <span class="light ${item.status}"></span>
        <div><strong>${item.name}</strong><span>${escapeHtml(item.detail)}</span></div>
      </button>`,
    )
    .join("");
  el("trafficList").querySelectorAll(".traffic-item").forEach((button) => {
    button.addEventListener("click", () => setPage(button.dataset.page));
  });
  el("setupSummary").textContent = `Age ${setup.age_band}, ${setup.subject}, ${setup.tone} tone`;
  renderBuilderGuide(setup);
  const nextStep = el("nextStep");
  nextStep.textContent = route.label;
  nextStep.dataset.page = route.target;
  nextStep.classList.toggle("ready", route.ready);
  nextStep.setAttribute("aria-label", `${route.label}. Open ${pageTitles[route.target]?.[0] || "next page"}.`);
  renderSidebarRoute(items);
  renderZoneBrief(items);
  renderMissionStrip(items, route);
  renderRouteMap(items);
  renderSafety();
  renderReviewStation();
}

function renderReviewStation() {
  const checks = reviewStationChecks();
  el("reviewChecks").innerHTML = checks
    .map(
      (item) => `
      <div class="review-check" data-status="${item.status}">
        <span class="light ${item.status}"></span>
        <div><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.detail)}</span></div>
      </div>`,
    )
    .join("");
  const next = reviewNextAction(checks);
  el("reviewStationNext").textContent = next;
}

function reviewStationChecks() {
  if (!currentPrompt) {
    return [
      { name: "Prompt", status: "red", detail: "Generate a prompt before review." },
      { name: "Export", status: "red", detail: "Export appears after generation." },
      { name: "Reuse", status: "red", detail: "Save appears after review." },
    ];
  }
  const checklist = currentPrompt.checklist || [];
  const vocabulary = currentPrompt.vocabulary || [];
  const youngLearners = currentPrompt.age_band === "5-7";
  const longWords = vocabulary.filter((word) => String(word).length > 8);
  const saved = isCurrentPromptFavourite();
  const safetyStatus = safetyReport?.status || "green";
  const ageStatus = youngLearners && (currentPrompt.creativity > 80 || longWords.length > 1) ? "amber" : "green";
  const subjectStatus = currentPrompt.subject_focus && String(currentPrompt.teacher_note || "").includes(currentPrompt.subject_focus) ? "green" : "amber";
  const taskStatus = currentPrompt.task && currentPrompt.challenge && checklist.length >= 3 ? "green" : "amber";
  return [
    {
      name: "Classroom Safety",
      status: safetyStatus,
      detail: safetyReport?.summary || "Seed bank safety looks ready.",
    },
    {
      name: "Age Fit",
      status: ageStatus,
      detail:
        ageStatus === "green"
          ? `Age ${currentPrompt.age_band} with ${checklist.length} checklist steps.`
          : `Age ${currentPrompt.age_band}; read once before using this spark level.`,
    },
    {
      name: "Subject Fit",
      status: subjectStatus,
      detail: `${currentPrompt.subject}: ${currentPrompt.subject_focus || "general classroom focus"}.`,
    },
    {
      name: "Task Shape",
      status: taskStatus,
      detail: taskStatus === "green" ? "Task, challenge, vocabulary, and checklist are present." : "Read the task once before sharing.",
    },
    {
      name: "Export",
      status: lastExport ? "green" : "amber",
      detail: lastExport ? `${lastExport.format.toUpperCase()} ready.` : "Export TXT or HTML before class.",
    },
    {
      name: "Reuse",
      status: saved ? "green" : "amber",
      detail: saved ? "Saved on the reuse shelf." : "Save Favourite if this one works.",
    },
  ];
}

function reviewNextAction(checks) {
  if (!currentPrompt) return "Next: Generate";
  if (checks.some((item) => item.name === "Classroom Safety" && item.status === "red")) return "Next: Fix Seed Bank";
  if (!lastExport) return "Next: Export";
  if (!isCurrentPromptFavourite()) return "Next: Save Favourite";
  return "Ready for reuse";
}

function isCurrentPromptFavourite() {
  if (!currentPrompt) return false;
  return favourites.some((item) => String(item.seed) === String(currentPrompt.seed) && item.title === currentPrompt.title);
}

function renderSidebarRoute(items) {
  const itemMap = Object.fromEntries(items.map((item) => [item.id, item]));
  document.querySelectorAll(".nav-button").forEach((button) => {
    const page = button.dataset.page || "start";
    const statusItem = navStatusItems[page];
    const status = statusItem ? itemMap[statusItem]?.status || "red" : "green";
    const label = pageTitles[page]?.[0] || page;
    const light = button.querySelector(".light");
    if (light) {
      light.className = `light ${status}`;
    }
    button.dataset.status = status;
    button.setAttribute("aria-label", `${label}: ${status}`);
  });
}

function renderZoneBrief(items) {
  const itemMap = Object.fromEntries(items.map((item) => [item.id, item]));
  const brief = zoneBriefs[currentPage] || zoneBriefs.start;
  const status = itemMap[brief.item]?.status || "green";
  el("zoneBriefLight").className = `light ${status}`;
  el("zoneBriefStep").textContent = brief.step;
  el("zoneBriefTitle").textContent = brief.title;
  el("zoneBriefHint").textContent = zoneBriefHint(brief);
}

function zoneBriefHint(brief) {
  if (currentPage === "review" && !currentPrompt) {
    return "Nothing to review yet. Use Generate to create the first prompt.";
  }
  if (currentPage === "review" && currentPrompt && !lastExport) {
    return "Prompt ready. Save it, export it, or print a worksheet.";
  }
  if (currentPage === "review" && lastExport) {
    return "Classroom copy is ready. You can reuse the seed or open the export folder.";
  }
  if (currentPage === "favourites") {
    return favouriteHint();
  }
  return brief.hint;
}

function renderMissionStrip(items, route) {
  const itemMap = Object.fromEntries(items.map((item) => [item.id, item]));
  const activeItem = activeMissionItem(itemMap, route);
  el("missionLabel").textContent = route.ready ? "Route complete" : "Current mission";
  el("missionTitle").textContent = route.label.replace(/^Next: /, "");
  el("missionHint").textContent = missionHint(itemMap, route);
  el("missionSteps").innerHTML = missionStops
    .map((stop) => {
      const source = itemMap[stop.item] || {};
      const status = source.status || "amber";
      const isActive = stop.item === activeItem;
      return `
        <button
          type="button"
          class="mission-step ${isActive ? "active" : ""}"
          data-page="${stop.page}"
          data-status="${status}"
          aria-label="${escapeHtml(stop.label)}: ${status}. ${escapeHtml(stop.command)}"
        >
          <span class="light ${status}"></span>
          <span><strong>${escapeHtml(stop.label)}</strong><small>${escapeHtml(stop.command)}</small></span>
        </button>`;
    })
    .join("");
  el("missionSteps").querySelectorAll(".mission-step").forEach((button) => {
    button.addEventListener("click", () => setPage(button.dataset.page));
  });
}

function renderBuilderGuide(setup) {
  const seedValue = setup.seed || (currentPrompt ? String(currentPrompt.seed) : "");
  const seedDetail = seedValue ? `Seed ${seedValue}` : "Auto seed on generate";
  const seedStatus = seedValue || !el("lockSeedInput").checked ? "green" : "amber";
  const creativityText = creativityLabel(setup.creativity);
  el("builderReadout").innerHTML = [
    {
      name: "Mode",
      detail: setup.mode || "Choose a prompt mode",
      status: setup.mode ? "green" : "red",
    },
    {
      name: "Spark",
      detail: `${setup.creativity} | ${creativityText}`,
      status: setup.creativity >= 20 && setup.creativity <= 85 ? "green" : "amber",
    },
    {
      name: "Seed",
      detail: seedDetail,
      status: seedStatus,
    },
  ].map((item) => `
    <div class="builder-readout-row">
      <span class="light ${item.status}"></span>
      <div><strong>${escapeHtml(item.name)}</strong><span>${escapeHtml(item.detail)}</span></div>
    </div>`).join("");
}

function creativityLabel(value) {
  if (value < 35) return "steady";
  if (value < 70) return "playful";
  if (value < 86) return "bold";
  return "chaos edge";
}

function activeMissionItem(itemMap, route) {
  if (route.ready) return "reuse";
  if (itemMap.setup?.status === "red") return "setup";
  if (itemMap.settings?.status === "red") return "settings";
  if (itemMap.generated?.status === "red") return "settings";
  if (itemMap.export?.status !== "green") return "export";
  if (itemMap.reuse?.status !== "green") return "reuse";
  return "reuse";
}

function missionHint(itemMap, route) {
  if (route.ready) {
    return "The route is green. Open the reuse shelf when you want this prompt again.";
  }
  if (itemMap.generated?.status === "red") {
    return "Press Generate Prompt to create the classroom task.";
  }
  if (itemMap.export?.status !== "green") {
    return "Review the task, then export or print a classroom copy.";
  }
  if (itemMap.reuse?.status !== "green") {
    return "Save the prompt as a favourite so it is easy to reuse.";
  }
  return "Use the next green stop to keep moving.";
}

function renderRouteMap(items) {
  const itemMap = Object.fromEntries(items.map((item) => [item.id, item]));
  el("routeStops").innerHTML = routeStops
    .map((stop) => {
      const source = itemMap[stop.item] || {};
      const isActive = stop.page === currentPage || (currentPage === "review" && stop.label === "Print" && !lastExport);
      const detail = stop.label === "Reuse" ? source.detail || "Saved prompts" : source.name || stop.label;
      return `
        <button
          type="button"
          class="route-stop ${isActive ? "active" : ""}"
          data-page="${stop.page}"
          style="--x: ${stop.x}; --y: ${stop.y}"
          aria-label="Open ${escapeHtml(stop.label)}"
        >
          <span class="light ${source.status || "amber"}"></span>
          <span><strong>${escapeHtml(stop.label)}</strong><small>${escapeHtml(detail)}</small></span>
        </button>`;
    })
    .join("");
  el("routeStops").querySelectorAll(".route-stop").forEach((button) => {
    button.addEventListener("click", () => setPage(button.dataset.page));
  });
}

function nextRoute(items) {
  const byId = Object.fromEntries(items.map((item) => [item.id, item]));
  if (byId.setup?.status === "red") return { label: "Next: Class Setup", target: "setup", ready: false };
  if (byId.settings?.status === "red") return { label: "Next: Prompt Settings", target: "generate", ready: false };
  if (byId.safety?.status === "red") return { label: "Next: Fix Seed Bank", target: "seeds", ready: false };
  if (currentPage === "favourites" && byId.reuse?.status === "green") return { label: "Ready for reuse", target: "favourites", ready: true };
  if (!currentPrompt) return { label: "Next: Generate a prompt", target: "generate", ready: false };
  if (!lastExport) return { label: "Next: Review or export", target: "review", ready: false };
  if (byId.reuse?.status !== "green") return { label: "Next: Save Favourite", target: "review", ready: false };
  return { label: "Ready for reuse", target: "favourites", ready: true };
}

function favouriteCountText(count) {
  return `${count} saved ${count === 1 ? "prompt" : "prompts"}`;
}

function favouriteHint() {
  if (favourites.length) {
    return `${favouriteCountText(favourites.length)} ready. Open one to reuse or regenerate.`;
  }
  if (currentPrompt) {
    return "Save the current prompt first, then this shelf becomes reusable.";
  }
  return "Saved prompts will appear here after you press Save Favourite.";
}

function renderSafety() {
  if (!safetyReport) return;
  [el("safetyLight"), el("safetyMiniLight")].forEach((light) => {
    light.className = `light ${safetyReport.status}`;
  });
  el("safetyLabel").textContent = safetyReport.label;
  el("safetyMiniLabel").textContent = safetyReport.label;
  el("safetySummary").textContent = safetyReport.summary;
  el("safetyMiniSummary").textContent = safetyReport.summary;
  el("safetyCounts").innerHTML = Object.entries(safetyReport.counts || {})
    .map(([key, value]) => `<span><strong>${escapeHtml(value)}</strong>${escapeHtml(labelize(key))}</span>`)
    .join("");
  if (!safetyReport.issues?.length) {
    el("safetyIssues").innerHTML = "<p>No safety issues found.</p>";
    return;
  }
  el("safetyIssues").innerHTML = safetyReport.issues
    .map((issue) => `<p><span class="light ${issue.level}"></span><strong>${escapeHtml(issue.area)}:</strong> ${escapeHtml(issue.message)}</p>`)
    .join("");
}

async function copyPrompt() {
  if (!currentPrompt) return setMessage("Generate a prompt first.");
  await navigator.clipboard.writeText(currentPrompt.prompt);
  setMessage("Prompt copied.");
}

async function saveFavourite() {
  if (!currentPrompt) return setMessage("Generate a prompt first.");
  const data = await api("/api/favourites", payload({ prompt: currentPrompt }));
  favourites = data.favourites;
  setMessage("Favourite saved.");
  renderFavourites(favourites);
  renderReviewStation();
  renderTraffic();
}

async function exportPrompt(format, announce = true) {
  if (!currentPrompt) return setMessage("Generate a prompt first.");
  const data = await api("/api/export", payload({ prompt: currentPrompt, format }));
  lastExport = data.export;
  el("openExportsButton").hidden = false;
  el("openLatestWorksheetButton").hidden = data.export.format !== "html";
  if (announce) {
    setMessage(`Exported ${format.toUpperCase()}: ${data.export.path}`);
  }
  renderReviewStation();
  renderTraffic();
  return data.export;
}

async function printWorksheet() {
  if (!currentPrompt) return setMessage("Generate a prompt first.");
  const exportInfo = await ensureHtmlExport();
  await openLatestWorksheet(exportInfo, "Worksheet exported. Opened it for printing.");
}

async function ensureHtmlExport() {
  if (!lastExport || lastExport.format !== "html") {
    return exportPrompt("html", false);
  }
  return lastExport;
}

async function openLatestWorksheet(exportInfo = lastExport, successMessage = "Opened latest worksheet.") {
  if (!exportInfo || exportInfo.format !== "html") {
    return setMessage("Export HTML first, then open the worksheet.");
  }
  const data = await api("/api/open-export", payload({ path: exportInfo.path }));
  const result = data.export_file;
  setMessage(result.opened ? `${successMessage} ${result.path}` : `${result.error} Export path: ${result.path}`);
}

async function openExports() {
  const data = await api("/api/open-exports", payload({}));
  setMessage(data.export_folder.opened ? `Opened exports folder: ${data.export_folder.path}` : data.export_folder.error);
}

function setMessage(text) {
  el("actionMessage").textContent = text;
}

function renderSeedEditors() {
  el("charactersText").value = (state.characters || []).map((item) => `${item.name} | ${item.trait} | ${item.wish}`).join("\n");
  el("settingsText").value = (state.settings || []).map((item) => `${item.name} | ${item.texture}`).join("\n");
  el("objectsText").value = (state.objects || []).map((item) => `${item.name} | ${item.twist}`).join("\n");
  el("topicsText").value = (state.topics || []).join("\n");
  el("vocabularyText").value = Object.entries(state.vocabulary || {})
    .map(([age, words]) => `${age} | ${words.join(", ")}`)
    .join("\n");
}

async function saveSeeds() {
  state = {
    ...state,
    characters: parseObjects(el("charactersText").value, ["name", "trait", "wish"]),
    settings: parseObjects(el("settingsText").value, ["name", "texture"]),
    objects: parseObjects(el("objectsText").value, ["name", "twist"]),
    topics: lines(el("topicsText").value),
    vocabulary: parseVocabulary(el("vocabularyText").value),
  };
  const data = await api("/api/state", payload({ state }));
  state = data.state;
  renderSeedEditors();
  await loadSafety();
  renderTraffic();
  setPage(safetyReport?.status === "red" ? "seeds" : "generate");
}

async function resetSeeds() {
  const data = await api("/api/state", payload({ reset: true }));
  state = data.state;
  renderSeedEditors();
  await loadSafety();
  renderTraffic();
}

function parseObjects(text, keys) {
  return lines(text).map((line) => {
    const parts = line.split("|").map((part) => part.trim());
    const item = {};
    keys.forEach((key, index) => {
      item[key] = parts[index] || "";
    });
    return item;
  });
}

function setReviewView(view) {
  currentReviewView = view || "student";
  document.querySelectorAll(".view-tab").forEach((button) => {
    button.classList.toggle("active", button.dataset.reviewView === currentReviewView);
  });
  document.querySelectorAll(".review-view").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `${currentReviewView}Review`);
  });
}

function teacherMarkup(prompt) {
  const vocabulary = (prompt.vocabulary || []).join(", ");
  const checklist = (prompt.checklist || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const traces = (prompt.trace_lines || []).map((line) => `<li>${escapeHtml(line)}</li>`).join("");
  return `
    <section>
      <h4>Teacher Notes</h4>
      <p>${escapeHtml(prompt.teacher_note || "No teacher note supplied.")}</p>
    </section>
    <section>
      <h4>Prompt Ingredients</h4>
      <p><strong>Mode:</strong> ${escapeHtml(prompt.mode)} | <strong>Age:</strong> ${escapeHtml(prompt.age_band)} | <strong>Subject:</strong> ${escapeHtml(prompt.subject)} | <strong>Seed:</strong> ${escapeHtml(prompt.seed)}</p>
      <p><strong>Subject Focus:</strong> ${escapeHtml(prompt.subject_focus || "")}</p>
      <p><strong>Vocabulary:</strong> ${escapeHtml(vocabulary)}</p>
    </section>
    <section>
      <h4>Success Checklist</h4>
      <ul>${checklist}</ul>
    </section>
    <section>
      <h4>Prime Trace</h4>
      <ul>${traces}</ul>
    </section>`;
}

function labelize(value) {
  return String(value).replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function parseVocabulary(text) {
  const result = {};
  lines(text).forEach((line) => {
    const [age, words] = line.split("|").map((part) => part.trim());
    if (age && words) {
      result[age] = words.split(",").map((word) => word.trim()).filter(Boolean);
    }
  });
  return result;
}

function lines(text) {
  return text.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

async function loadFavourites() {
  const data = await api("/api/favourites");
  favourites = data.favourites;
  renderFavourites(favourites);
}

function renderFavourites(favourites) {
  if (!favourites.length) {
    renderEmptyFavourites();
    return;
  }
  el("favouritesList").innerHTML = favourites
    .map(
      (item) => `
      <div class="favourite-row">
        <div>
          <h4>${escapeHtml(item.title)}</h4>
          <p>${escapeHtml(item.mode || "")} | ${escapeHtml(item.age_band || "")} | seed ${escapeHtml(String(item.seed || ""))}</p>
        </div>
        <button data-fav="${item.id}">Open</button>
      </div>`,
    )
    .join("");
  el("favouritesList").querySelectorAll("button[data-fav]").forEach((button) => {
    button.addEventListener("click", () => {
      const item = favourites.find((fav) => fav.id === button.dataset.fav);
      if (!item) return;
      currentPrompt = item.prompt;
      lastExport = null;
      renderPrompt();
      renderTraffic();
      setPage("review");
    });
  });
}

function renderEmptyFavourites() {
  const hasPrompt = Boolean(currentPrompt);
  el("favouritesList").innerHTML = `
    <section class="reuse-empty" aria-label="Empty reuse shelf">
      <div class="reuse-empty-copy">
        <p>Reuse Shelf</p>
        <h4>No saved prompts yet.</h4>
        <span>${hasPrompt ? "The current prompt is ready. Save it here so the route stays reusable." : "Generate a prompt, check it, then save the useful ones here."}</span>
        <div class="reuse-empty-actions">
          <button type="button" class="primary-button" data-favourite-action="${hasPrompt ? "save" : "generate"}">${hasPrompt ? "Save Current Prompt" : "Generate Prompt"}</button>
          <button type="button" data-favourite-action="review" ${hasPrompt ? "" : "hidden"}>Review Current Prompt</button>
        </div>
        <ol class="reuse-route">
          <li><span class="light green"></span><span>Generate a classroom prompt.</span></li>
          <li><span class="light ${hasPrompt ? "green" : "red"}"></span><span>Review the student task.</span></li>
          <li><span class="light red"></span><span>Press Save Favourite.</span></li>
        </ol>
      </div>
    </section>`;
  el("favouritesList").querySelectorAll("button[data-favourite-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.favouriteAction;
      if (action === "save") {
        saveFavourite();
      } else if (action === "review") {
        setPage("review");
      } else {
        generatePrompt();
      }
    });
  });
}

function escapeHtml(value) {
  return String(value).replace(/[&<>"']/g, (char) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;",
  }[char]));
}

init().catch((error) => {
  console.error(error);
  document.body.innerHTML = `<pre>${escapeHtml(error.message)}</pre>`;
});
