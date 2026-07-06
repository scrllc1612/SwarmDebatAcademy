const state = {
  debates: [],
  activeDebateId: null,
  currentVideos: null,
  generatingRound: null,
  videoStage: {},
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

document.querySelector(".video-header h2").textContent = "Debate animado";
document.querySelector("#closeVideoModal").textContent = "x";
document.querySelectorAll(".video-card h3").forEach((title, index) => {
  title.textContent = index === 0 ? "Proponente" : "Oponente";
});

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

function setRoundVideoBusy(button, isBusy) {
  if (!button) {
    return;
  }

  button.disabled = isBusy;
  button.textContent = isBusy ? "Generando ronda..." : "Generar ronda";
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

  console.log("Path:", path);
  console.log("Options:", options);

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
          <button
            class="video-btn"
            data-round="${round.round_number}">
            🎬 Ver ronda animada
          </button>
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
  document.querySelectorAll(".video-btn").forEach((button) => {

    const round = Number(button.dataset.round);

    if (!state.videoStage[round]) {
      state.videoStage[round] = "pro";
    }

    updateVideoButton(button, round);

    button.type = "button";

    button.addEventListener("click", () => {

      generateRoundVideo(
        metadata.debate_id,
        round,
        button
      );

    });

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

async function generateRoundVideo(
  debateId,
  roundNumber,
  button,
) {
  console.log("=== NUEVA generateRoundVideo ===");

  if (state.generatingRound) {
    showToast("Ya se esta generando un video.");
    return;
  }

  state.generatingRound = roundNumber;

  setRoundVideoBusy(button, true);
  setBusy(true, "Generando video...");

  try {

    const stage = state.videoStage[roundNumber] || "pro";

    const endpoint =
      stage === "pro"
        ? `/api/debates/${debateId}/rounds/${roundNumber}/video/pro`
        : `/api/debates/${debateId}/rounds/${roundNumber}/video/contra`;

    console.log("Stage:", stage);
    console.log("Endpoint generado:", endpoint);

    const response = await api(endpoint, {
      method: "POST",
    });

    if (response.eta) {

      setBusy(
        true,
        `Renderizando video (${Math.ceil(response.eta)} s)...`
      );

      await new Promise(resolve =>
        setTimeout(
          resolve,
          (Math.ceil(response.eta) + 2) * 1000
        )
      );

    }

    openVideoModal(response, roundNumber);

    if (stage === "pro") {

      state.videoStage[roundNumber] = "contra";

    } else {

      state.videoStage[roundNumber] = "done";

    }

    updateVideoButton(button, roundNumber);

    showToast("Video generado correctamente.");

  }

  catch (error) {

    console.error(error);

    showToast(error.message);

  }

  finally {

    state.generatingRound = null;

    setRoundVideoBusy(button, false);

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

function openVideoModal(response, roundNumber) {

  const modal = document.querySelector("#videoModal");

  modal.classList.remove("hidden");
  modal.setAttribute("aria-hidden", "false");

  document.querySelector("#videoRoundTitle").textContent =
    `Ronda ${roundNumber}`;

  const proVideo = document.querySelector("#proVideo");
  const contraVideo = document.querySelector("#contraVideo");

  const proContainer = proVideo.parentElement;
  const contraContainer = contraVideo.parentElement;

  proVideo.pause();
  contraVideo.pause();

  if (proVideo._hls) {
    proVideo._hls.destroy();
    proVideo._hls = null;
  }

  if (contraVideo._hls) {
    contraVideo._hls.destroy();
    contraVideo._hls = null;
  }

  proVideo.removeAttribute("src");
  contraVideo.removeAttribute("src");

  if (response.stance === "pro") {

    proContainer.style.display = "";

    contraContainer.style.display = "none";

    loadHlsVideo(
      proVideo,
      response.hls,
    );

  }

  else {

    contraContainer.style.display = "";

    proContainer.style.display = "none";

    loadHlsVideo(
      contraVideo,
      response.hls,
    );

  }

}


function closeVideoModal() {

  const modal = document.querySelector("#videoModal");

  const proVideo = document.querySelector("#proVideo");
  const contraVideo = document.querySelector("#contraVideo");

  const proContainer = proVideo.parentElement;
  const contraContainer = contraVideo.parentElement;

  [proVideo, contraVideo].forEach(video => {

    video.pause();

    if (video._hls) {
      video._hls.destroy();
      video._hls = null;
    }

    video.removeAttribute("src");
    video.load();

  });

  proContainer.style.display = "";
  contraContainer.style.display = "";

  modal.classList.add("hidden");
  modal.setAttribute("aria-hidden", "true");

}

function updateVideoButton(button, round) {

  const stage = state.videoStage[round];

  switch (stage) {

    case "pro":
      button.textContent = "🎥 Ver Proponente";
      break;

    case "contra":
      button.textContent = "🎥 Ver Oponente";
      break;

    case "done":
      button.textContent = "✅ Videos generados";
      button.disabled = true;
      break;

    default:
      button.textContent = "🎥 Ver Proponente";

  }

}

function loadHlsVideo(videoElement, hlsUrl) {

  if (!hlsUrl) {
    showToast("No se recibió la URL del video.");
    return;
  }

  if (videoElement._hls) {
    videoElement._hls.destroy();
    videoElement._hls = null;
  }

  if (Hls.isSupported()) {

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

      console.error("HLS Error:", data);

      if (data.fatal) {

        switch (data.type) {

          case Hls.ErrorTypes.NETWORK_ERROR:
            console.error("Error de red HLS");
            hls.startLoad();
            break;

          case Hls.ErrorTypes.MEDIA_ERROR:
            console.error("Error de media HLS");
            hls.recoverMediaError();
            break;

          default:
            hls.destroy();
            showToast("No se pudo reproducir el video.");
            break;

        }

      }

    });

    videoElement._hls = hls;

  }

  else if (videoElement.canPlayType("application/vnd.apple.mpegurl")) {

    videoElement.src = hlsUrl;

    videoElement.addEventListener(
      "loadedmetadata",
      () => {
        videoElement.play().catch(() => { });
      },
      { once: true }
    );

  }

  else {

    showToast("Este navegador no soporta HLS.");

  }

}