const state = {
  debates: [],
  activeDebateId: null,
};

const els = {
  apiStatus: document.querySelector("#apiStatus"),
  debateList: document.querySelector("#debateList"),
  detail: document.querySelector("#detail"),
  topicInput: document.querySelector("#topicInput"),
  roundsInput: document.querySelector("#roundsInput"),
  generateBtn: document.querySelector("#generateBtn"),
  refreshDebates: document.querySelector("#refreshDebates"),
  toast: document.querySelector("#toast"),
};

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.setTimeout(() => els.toast.classList.remove("show"), 3200);
}

function setBusy(isBusy, message = "Procesando") {
  els.generateBtn.disabled = isBusy;
  els.refreshDebates.disabled = isBusy;
  els.apiStatus.textContent = isBusy ? message : "Conectado";
  els.apiStatus.className = "status-pill ok";
}

function formatScore(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "--";
  }
  return Number(value).toFixed(1);
}

function escapeHtml(value = "") {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    },
    ...options,
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || "No se pudo completar la solicitud");
  }

  return response.json();
}

function renderDebateList() {
  if (!state.debates.length) {
    els.debateList.innerHTML = `<p class="meta-line">Aun no hay debates guardados.</p>`;
    return;
  }

  els.debateList.innerHTML = state.debates
    .map((debate) => {
      const activeClass = debate.debate_id === state.activeDebateId ? " active" : "";
      const status = debate.has_evaluation ? "Evaluado" : "Sin evaluacion";
      return `
        <button class="debate-item${activeClass}" type="button" data-id="${escapeHtml(debate.debate_id)}">
          <strong>${escapeHtml(debate.topic)}</strong>
          <span>${debate.total_rounds} rondas - ${status}</span>
        </button>
      `;
    })
    .join("");
}

function metricCards(evaluation) {
  if (!evaluation) {
    return "";
  }

  return `
    <section class="metrics-grid" aria-label="Metricas globales">
      <div class="metric-card">
        <span>Calidad Toulmin</span>
        <strong>${formatScore(evaluation.tqs)}</strong>
      </div>
      <div class="metric-card">
        <span>Coherencia global</span>
        <strong>${formatScore(evaluation.sc)}</strong>
      </div>
      <div class="metric-card">
        <span>Puntaje final</span>
        <strong>${formatScore(evaluation.debate_score)}</strong>
      </div>
    </section>
  `;
}

function scoreRows(metrics) {
  const labels = [
    ["argument_score_100", "Score Toulmin"],
    ["claim_quality", "Claim"],
    ["data_relevance", "Data relevance"],
    ["data_sufficiency", "Data sufficiency"],
    ["warrant_strength", "Warrant"],
    ["backing_adequacy", "Backing"],
    ["rebuttal_effectiveness", "Rebuttal"],
  ];

  return labels
    .map(([key, label]) => {
      return `
        <div class="score-row">
          <span>${label}</span>
          <strong>${formatScore(metrics[key])}</strong>
        </div>
      `;
    })
    .join("");
}

function roundMetricBlock(roundMetric) {
  if (!roundMetric) {
    return "";
  }

  return `
    <div class="round-metrics">
      <div class="score-table">
        <h3>Metricas proponente</h3>
        ${scoreRows(roundMetric.pro)}
      </div>
      <div class="score-table">
        <h3>Metricas oponente</h3>
        ${scoreRows(roundMetric.contra)}
      </div>
    </div>
  `;
}

function moderatorBlock(summary) {
  if (!summary) {
    return "";
  }

  return `
    <aside class="moderator">
      <strong>Moderador</strong>
      <p>${escapeHtml(summary.main_conflict || summary.pro_main_point || "")}</p>
    </aside>
  `;
}

function renderDebate(debate) {
  const metadata = debate.metadata || {};
  const metricsByRound = new Map(
    (debate.round_metrics || []).map((item) => [item.round_number, item])
  );

  const rounds = (debate.rounds || [])
    .map((round) => {
      const pro = round.pro_argument || {};
      const contra = round.contra_argument || {};
      return `
        <article class="round">
          <div class="round-title">Ronda ${round.round_number}</div>
          <section class="message pro">
            <div class="speaker pro">
              <span>Proponente</span>
              <span>Ronda ${round.round_number}</span>
            </div>
            <p>${escapeHtml(pro.speech || pro.claim || "")}</p>
          </section>
          <section class="message contra">
            <div class="speaker contra">
              <span>Oponente</span>
              <span>Ronda ${round.round_number}</span>
            </div>
            <p>${escapeHtml(contra.speech || contra.claim || "")}</p>
          </section>
          ${moderatorBlock(round.moderator_summary)}
          ${roundMetricBlock(metricsByRound.get(round.round_number))}
        </article>
      `;
    })
    .join("");

  els.detail.innerHTML = `
    <div class="debate-header">
      <div>
        <h2>${escapeHtml(metadata.topic || "Debate sin tema")}</h2>
        <p class="meta-line">ID: ${escapeHtml(metadata.debate_id || "")} - ${metadata.total_rounds || 0} rondas</p>
      </div>
      <button class="primary-action" id="evaluateBtn" type="button">
        ${debate.evaluation ? "Reevaluar debate" : "Evaluar debate"}
      </button>
    </div>
    ${metricCards(debate.evaluation)}
    ${rounds}
  `;

  document.querySelector("#evaluateBtn").addEventListener("click", () => {
    evaluateDebate(metadata.debate_id);
  });
}

async function loadDebates() {
  state.debates = await api("/api/debates");
  renderDebateList();
}

async function loadDebate(debateId) {
  setBusy(true, "Cargando");
  try {
    const debate = await api(`/api/debates/${debateId}`);
    state.activeDebateId = debateId;
    renderDebateList();
    renderDebate(debate);
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

async function generateDebate() {
  const topic = els.topicInput.value.trim();
  const totalRounds = Number(els.roundsInput.value);

  if (topic.length < 5) {
    showToast("Escribe un tema de debate mas especifico.");
    els.topicInput.focus();
    return;
  }

  setBusy(true, "Generando");
  try {
    const debate = await api("/api/debates", {
      method: "POST",
      body: JSON.stringify({ topic, total_rounds: totalRounds }),
    });
    state.activeDebateId = debate.metadata.debate_id;
    els.topicInput.value = "";
    await loadDebates();
    renderDebate(debate);
    showToast("Debate generado y guardado.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

async function evaluateDebate(debateId) {
  if (!debateId) {
    return;
  }

  setBusy(true, "Evaluando");
  try {
    const debate = await api(`/api/debates/${debateId}/evaluate`, {
      method: "POST",
    });
    await loadDebates();
    state.activeDebateId = debateId;
    renderDebateList();
    renderDebate(debate);
    showToast("Evaluacion completada.");
  } catch (error) {
    showToast(error.message);
  } finally {
    setBusy(false);
  }
}

async function bootstrap() {
  try {
    await api("/api/health");
    els.apiStatus.textContent = "Conectado";
    els.apiStatus.className = "status-pill ok";
    await loadDebates();
  } catch (error) {
    els.apiStatus.textContent = "API no disponible";
    els.apiStatus.className = "status-pill error";
    showToast("Inicia FastAPI para conectar el frontend.");
  }
}

els.generateBtn.addEventListener("click", generateDebate);
els.refreshDebates.addEventListener("click", loadDebates);
els.topicInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter") {
    generateDebate();
  }
});
els.debateList.addEventListener("click", (event) => {
  const item = event.target.closest("[data-id]");
  if (item) {
    loadDebate(item.dataset.id);
  }
});

bootstrap();
