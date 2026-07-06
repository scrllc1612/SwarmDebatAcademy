const state = {
  debates: [],
  activeDebateId: null,
  generatingRound: null,
  videoStage: {},
  videoLibrary: {},
  activeVideoRound: null,
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
  videoModal: document.querySelector("#videoModal"),
  videoGrid: document.querySelector("#videoGrid"),
  videoRoundTitle: document.querySelector("#videoRoundTitle"),
  videoLayoutStatus: document.querySelector("#videoLayoutStatus"),
  proVideo: document.querySelector("#proVideo"),
  contraVideo: document.querySelector("#contraVideo"),
  closeVideoModal: document.querySelector("#closeVideoModal"),
  previousRoundBtn: document.querySelector("#previousRoundBtn"),
  nextRoundBtn: document.querySelector("#nextRoundBtn"),
};

const videoCards = {
  pro: document.querySelector('[data-stance="pro"]'),
  contra: document.querySelector('[data-stance="contra"]'),
};

const loadingMessages = {
  loading: ["Cargando debate", "Recuperando argumentos y metricas guardadas."],
  debate: ["Generando argumentos", "Los agentes estan construyendo el intercambio."],
  evaluation: ["Evaluando consenso", "Calculando calidad Toulmin, coherencia y puntaje final."],
  video: ["Preparando avatar", "Renderizando la intervencion seleccionada."],
};

function showToast(message) {
  els.toast.textContent = message;
  els.toast.classList.add("show");
  window.setTimeout(() => els.toast.classList.remove("show"), 3200);
}

function setStatus(text, mode = "ok") {
  els.apiStatus.innerHTML = `<span class="status-dot" aria-hidden="true"></span>${escapeHtml(text)}`;
  els.apiStatus.className = `status-pill ${mode}`;
}

function setButtonLoading(button, isLoading) {
  if (!button) {
    return;
  }

  button.classList.toggle("is-loading", isLoading);
  button.setAttribute("aria-busy", String(isLoading));
}

function renderLoadingPanel(kind) {
  const [title, copy] = loadingMessages[kind] || loadingMessages.loading;
  els.detail.insertAdjacentHTML(
    "afterbegin",
    `
      <div class="loading-panel" id="loadingPanel">
        <span class="loading-indicator" aria-hidden="true"></span>
        <div>
          <strong>${title}</strong>
          <p>${copy}</p>
        </div>
      </div>
    `
  );
}

function removeLoadingPanel() {
  document.querySelector("#loadingPanel")?.remove();
}

function setBusy(isBusy, message = "Procesando", kind = "loading") {
  els.generateBtn.disabled = isBusy;
  els.refreshDebates.disabled = isBusy;
  setButtonLoading(els.generateBtn, isBusy && kind === "debate");
  setButtonLoading(els.refreshDebates, isBusy && kind === "loading");
  setStatus(isBusy ? message : "Conectado", isBusy ? "loading" : "ok");

  if (isBusy && ["debate", "evaluation", "video"].includes(kind)) {
    removeLoadingPanel();
    renderLoadingPanel(kind);
  } else if (!isBusy) {
    removeLoadingPanel();
  }
}

function setRoundVideoBusy(button, isBusy) {
  if (!button) {
    return;
  }

  button.disabled = isBusy;
  setButtonLoading(button, isBusy);
  if (isBusy) {
    button.dataset.previousLabel = button.textContent;
    button.innerHTML = `<span class="btn-icon" aria-hidden="true">...</span> Generando video`;
  } else {
    updateVideoButton(button, Number(button.dataset.round));
  }
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

function videoKey(debateId, roundNumber) {
  return `${debateId}:${roundNumber}`;
}

function stageKey(roundNumber) {
  return `${state.activeDebateId || "active"}:${roundNumber}`;
}

function getVideoSlot(debateId, roundNumber) {
  const key = videoKey(debateId, roundNumber);
  if (!state.videoLibrary[key]) {
    state.videoLibrary[key] = {};
  }
  return state.videoLibrary[key];
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
          <span>${debate.total_rounds} rondas &middot; ${status}</span>
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

function scoreRows(metrics = {}) {
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
      <div>
        <strong>Moderador</strong>
        <p>${escapeHtml(summary.main_conflict || summary.pro_main_point || "")}</p>
      </div>
    </aside>
  `;
}

function messageBlock(type, roundNumber, text) {
  const isPro = type === "pro";
  const speaker = isPro ? "Proponente" : "Oponente";
  const initial = isPro ? "P" : "O";
  return `
    <section class="message ${type}">
      <div class="speaker">
        <div class="speaker-main">
          <span class="avatar ${type}" aria-hidden="true">${initial}</span>
          <span>${speaker}</span>
        </div>
        <span class="round-chip">Ronda ${roundNumber}</span>
      </div>
      <p>${escapeHtml(text)}</p>
    </section>
  `;
}

function renderDebate(debate) {
  const metadata = debate.metadata || {};
  const metricsByRound = new Map(
    (debate.round_metrics || []).map((item) => [item.round_number, item])
  );

  state.activeDebateId = metadata.debate_id || state.activeDebateId;

  const rounds = (debate.rounds || [])
    .map((round) => {
      const pro = round.pro_argument || {};
      const contra = round.contra_argument || {};
      return `
        <article class="round" data-round="${round.round_number}">
          <div class="round-title">Ronda ${round.round_number}</div>
          ${messageBlock("pro", round.round_number, pro.speech || pro.claim || "")}
          ${messageBlock("contra", round.round_number, contra.speech || contra.claim || "")}
          ${moderatorBlock(round.moderator_summary)}
          ${roundMetricBlock(metricsByRound.get(round.round_number))}
          <button class="video-btn" data-round="${round.round_number}" type="button"></button>
        </article>
      `;
    })
    .join("");

  els.detail.innerHTML = `
    <div class="debate-header">
      <div>
        <h2>${escapeHtml(metadata.topic || "Debate sin tema")}</h2>
        <p class="meta-line">ID: ${escapeHtml(metadata.debate_id || "")} &middot; ${metadata.total_rounds || 0} rondas</p>
      </div>
      <button class="btn btn-primary" id="evaluateBtn" type="button">
        <span class="btn-icon" aria-hidden="true">OK</span>
        ${debate.evaluation ? "Reevaluar debate" : "Evaluar debate"}
      </button>
    </div>
    ${metricCards(debate.evaluation)}
    ${rounds}
  `;

  document.querySelector("#evaluateBtn").addEventListener("click", () => {
    evaluateDebate(metadata.debate_id);
  });

  document.querySelectorAll(".video-btn").forEach((button) => {
    const round = Number(button.dataset.round);
    const key = stageKey(round);

    if (!state.videoStage[key]) {
      state.videoStage[key] = "pro";
    }

    updateVideoButton(button, round);
    button.addEventListener("click", () => {
      generateRoundVideo(metadata.debate_id, round, button);
    });
  });
}

async function loadDebates() {
  state.debates = await api("/api/debates");
  renderDebateList();
}

async function loadDebate(debateId) {
  setBusy(true, "Cargando", "loading");
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

  setBusy(true, "Generando argumentos", "debate");
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

  const evaluateBtn = document.querySelector("#evaluateBtn");
  setButtonLoading(evaluateBtn, true);
  evaluateBtn.disabled = true;
  setBusy(true, "Evaluando consenso", "evaluation");
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

async function generateRoundVideo(debateId, roundNumber, button) {
  if (state.generatingRound) {
    showToast("Ya se esta generando un video.");
    return;
  }

  state.generatingRound = roundNumber;
  setRoundVideoBusy(button, true);
  setBusy(true, "Preparando avatar", "video");

  try {
    const key = stageKey(roundNumber);
    const stage = state.videoStage[key] || "pro";
    const endpoint =
      stage === "pro"
        ? `/api/debates/${debateId}/rounds/${roundNumber}/video/pro`
        : `/api/debates/${debateId}/rounds/${roundNumber}/video/contra`;

    const response = await api(endpoint, {
      method: "POST",
    });

    if (response.eta) {
      setStatus(`Renderizando video (${Math.ceil(response.eta)} s)`, "loading");
      await new Promise((resolve) =>
        setTimeout(resolve, (Math.ceil(response.eta) + 2) * 1000)
      );
    }

    const slot = getVideoSlot(debateId, roundNumber);
    slot[response.stance] = response.hls;

    openVideoModal(response, roundNumber, debateId);

    state.videoStage[key] = stage === "pro" ? "contra" : "done";
    updateVideoButton(button, roundNumber);
    showToast("Video generado correctamente.");
  } catch (error) {
    showToast(error.message);
  } finally {
    state.generatingRound = null;
    setRoundVideoBusy(button, false);
    setBusy(false);
  }
}

async function bootstrap() {
  try {
    await api("/api/health");
    setStatus("Conectado", "ok");
    await loadDebates();
  } catch (error) {
    setStatus("API no disponible", "error");
    showToast("Inicia FastAPI para conectar el frontend.");
  }
}

function updateVideoButton(button, round) {
  const stage = state.videoStage[stageKey(round)];

  switch (stage) {
    case "pro":
      button.innerHTML = `<span class="btn-icon" aria-hidden="true">&gt;</span> Generar proponente`;
      button.disabled = false;
      break;
    case "contra":
      button.innerHTML = `<span class="btn-icon" aria-hidden="true">&gt;</span> Generar oponente`;
      button.disabled = false;
      break;
    case "done":
      button.innerHTML = `<span class="btn-icon" aria-hidden="true">OK</span> Videos generados`;
      button.disabled = true;
      break;
    default:
      button.innerHTML = `<span class="btn-icon" aria-hidden="true">&gt;</span> Generar proponente`;
      button.disabled = false;
  }
}

function clearVideo(videoElement) {
  videoElement.pause();

  if (videoElement._hls) {
    videoElement._hls.destroy();
    videoElement._hls = null;
  }

  videoElement.removeAttribute("src");
  videoElement.load();
}

function setVideoCardState(stance, hasVideo, visible) {
  const card = videoCards[stance];
  card.classList.toggle("has-video", hasVideo);
  card.classList.toggle("is-hidden", !visible);
}

function openVideoModal(response, roundNumber, debateId = state.activeDebateId) {
  const slot = getVideoSlot(debateId, roundNumber);
  const hasPro = Boolean(slot.pro);
  const hasContra = Boolean(slot.contra);
  const hasBoth = hasPro && hasContra;

  state.activeVideoRound = roundNumber;
  els.videoModal.classList.remove("hidden");
  els.videoModal.setAttribute("aria-hidden", "false");
  els.videoRoundTitle.textContent = `Ronda ${roundNumber}`;
  els.videoLayoutStatus.textContent = hasBoth ? "Dos participantes" : "Un participante";
  els.videoGrid.classList.toggle("single", !hasBoth);

  clearVideo(els.proVideo);
  clearVideo(els.contraVideo);

  setVideoCardState("pro", hasPro, hasPro || response.stance === "pro");
  setVideoCardState("contra", hasContra, hasContra || response.stance === "contra");

  if (hasPro) {
    loadHlsVideo(els.proVideo, slot.pro);
  }

  if (hasContra) {
    loadHlsVideo(els.contraVideo, slot.contra);
  }

  els.closeVideoModal.focus();
}

function closeVideoModal() {
  clearVideo(els.proVideo);
  clearVideo(els.contraVideo);
  setVideoCardState("pro", false, true);
  setVideoCardState("contra", false, true);
  els.videoModal.classList.add("hidden");
  els.videoModal.setAttribute("aria-hidden", "true");
}

function loadHlsVideo(videoElement, hlsUrl) {
  if (!hlsUrl) {
    showToast("No se recibio la URL del video.");
    return;
  }

  if (videoElement._hls) {
    videoElement._hls.destroy();
    videoElement._hls = null;
  }

  if (window.Hls && Hls.isSupported()) {
    const hls = new Hls({
      enableWorker: true,
      lowLatencyMode: true,
    });

    hls.loadSource(hlsUrl);
    hls.attachMedia(videoElement);

    hls.on(Hls.Events.MANIFEST_PARSED, () => {
      videoElement.play().catch(() => { });
    });

    hls.on(Hls.Events.ERROR, (_, data) => {
      if (!data.fatal) {
        return;
      }

      switch (data.type) {
        case Hls.ErrorTypes.NETWORK_ERROR:
          hls.startLoad();
          break;
        case Hls.ErrorTypes.MEDIA_ERROR:
          hls.recoverMediaError();
          break;
        default:
          hls.destroy();
          showToast("No se pudo reproducir el video.");
          break;
      }
    });

    videoElement._hls = hls;
  } else if (videoElement.canPlayType("application/vnd.apple.mpegurl")) {
    videoElement.src = hlsUrl;
    videoElement.addEventListener(
      "loadedmetadata",
      () => {
        videoElement.play().catch(() => { });
      },
      { once: true }
    );
  } else {
    showToast("Este navegador no soporta HLS.");
  }
}

els.generateBtn.addEventListener("click", generateDebate);
els.refreshDebates.addEventListener("click", loadDebates);
els.closeVideoModal.addEventListener("click", closeVideoModal);
els.previousRoundBtn.addEventListener("click", () => showToast("Usa los botones de cada ronda para generar su video."));
els.nextRoundBtn.addEventListener("click", () => showToast("Usa los botones de cada ronda para generar su video."));

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

els.videoModal.addEventListener("click", (event) => {
  if (event.target === els.videoModal) {
    closeVideoModal();
  }
});

document.addEventListener("keydown", (event) => {
  if (event.key === "Escape" && !els.videoModal.classList.contains("hidden")) {
    closeVideoModal();
  }
});

bootstrap();
