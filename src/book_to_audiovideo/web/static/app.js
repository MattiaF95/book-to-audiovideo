const jobsList = document.getElementById("jobs-list");
const jobsCount = document.getElementById("jobs-count");
const jobStatus = document.getElementById("job-status");
const jobExplainer = document.getElementById("job-explainer");
const jobSummary = document.getElementById("job-summary");
const jobDetail = document.getElementById("job-detail");
const uploadForm = document.getElementById("upload-form");
const fileInput = document.getElementById("file-input");
const fileLabel = document.getElementById("file-label");
const uploadStatus = document.getElementById("upload-status");
const submitButton = document.getElementById("submit-button");
let selectedJobId = null;
let uploadInFlight = false;

const stages = [
  "ingestion",
  "text_cleanup",
  "narrative_context",
  "dialogue_segmentation",
  "speaker_registry",
  "speaker_attribution",
  "narrative_annotation",
  "voice_casting",
  "pronunciation_planning",
  "prosody_planning",
  "media_planning",
  "media_fetch",
  "tts",
  "audio_mix",
  "video_compose",
  "qa",
  "manifest"
];

const stageDescriptions = {
  ingestion: "Legge il file sorgente senza modificarne il contenuto.",
  text_cleanup: "Applica solo una pulizia minima e conservativa del testo.",
  narrative_context: "Ricava il contesto narrativo globale utile ai passaggi successivi.",
  dialogue_segmentation: "Divide il testo in segmenti ordinati di narrazione o dialogo.",
  speaker_registry: "Costruisce il registro stabile di narratore e personaggi ricorrenti.",
  speaker_attribution: "Assegna ogni segmento allo speaker corretto usando il registro stabile.",
  narrative_annotation: "Aggiunge solo annotazioni leggere come emozione e importanza.",
  voice_casting: "Sceglie una voce stabile per ogni speaker riusabile in ElevenLabs.",
  pronunciation_planning: "Identifica solo i rischi di pronuncia davvero utili al TTS.",
  prosody_planning: "Definisce i suggerimenti minimi di resa vocale per segmento.",
  media_planning: "Prepara solo il piano media di sfondo e gli eventuali SFX.",
  media_fetch: "Cerca il video di sfondo.",
  tts: "Genera l'audio parlato per ogni segmento.",
  audio_mix: "Mixa voce ed effetti con voce dominante.",
  video_compose: "Combina audio finale e video di sfondo.",
  qa: "Controlla durata e loudness del risultato.",
  manifest: "Scrive manifest e riepilogo finale del job."
};

function renderEmptyDashboard() {
  jobStatus.textContent = "Nessun job selezionato";
  jobExplainer.classList.add("empty");
  jobExplainer.innerHTML = "Seleziona un job dalla colonna sinistra per vedere fase corrente, significato dello step attivo e stato finale atteso.";
  jobSummary.classList.add("empty");
  jobSummary.innerHTML = "La home resta pulita finché non apri un job dalla lista a sinistra.";
  jobDetail.classList.add("empty");
  jobDetail.innerHTML = "Seleziona un job per vedere agent, eventi e risultato finale.";
}

async function fetchJobs() {
  const response = await fetch("/api/jobs");
  const jobs = await response.json();
  jobsCount.textContent = jobs.length;
  jobsList.innerHTML = jobs.map(job => `
    <button class="job-pill ${job.job_id === selectedJobId ? "active" : ""}" data-job-id="${job.job_id}">
      <strong>${job.source_name}</strong>
      <span>${job.status} · ${job.current_stage}</span>
    </button>
  `).join("");
}

function getStageState(job, stage) {
  const match = [...job.events].reverse().find(item => item.stage === stage);
  return match ? match.status : "pending";
}

function computeProgress(job) {
  const completed = stages.filter(stage => getStageState(job, stage) === "completed").length;
  return Math.round((completed / stages.length) * 100);
}

function humanStatus(job) {
  if (job.status === "running") {
    return `In lavorazione: ${job.current_stage}`;
  }
  if (job.status === "queued") {
    return "In coda, in attesa di avvio";
  }
  if (job.status === "needs_attention") {
    return `In attesa di approvazione: ${job.current_stage}`;
  }
  if (job.status === "completed") {
    return "Completato";
  }
  if (job.status === "failed") {
    return "Fallito";
  }
  if (job.status === "cancelled") {
    return "Interrotto manualmente";
  }
  if (job.status === "rejected") {
    return "Rifiutato";
  }
  return job.status;
}

function renderJob(job) {
  const progress = computeProgress(job);
  jobStatus.textContent = humanStatus(job);
  jobExplainer.classList.remove("empty");
  const currentDescription = stageDescriptions[job.current_stage] || "Stage non ancora avviato o già concluso.";
  jobExplainer.innerHTML = `
    <div class="explainer-grid">
      <div class="explainer-card">
        <span class="summary-label">Fase attiva</span>
        <strong>${job.current_stage}</strong>
        <small>${currentDescription}</small>
      </div>
      <div class="explainer-card">
        <span class="summary-label">Cosa aspettarsi</span>
        <strong>${job.status === "completed" ? "Video pronto" : job.status === "failed" ? "Stop con errore" : job.status === "needs_attention" ? "Attesa decisione" : "Il job continua da solo"}</strong>
        <small>${job.status === "completed" ? "Puoi aprire il video finale." : job.status === "failed" ? "Controlla l'errore mostrato sotto." : job.status === "needs_attention" ? "Devi approvare o rifiutare." : "Aggiorna automaticamente ogni pochi secondi."}</small>
      </div>
    </div>
  `;
  jobSummary.classList.remove("empty");
  jobSummary.innerHTML = `
    <div class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">File</span>
        <strong>${job.source_name}</strong>
        <small>${job.source_uploaded ? "caricato correttamente" : "non caricato"}</small>
      </div>
      <div class="summary-card">
        <span class="summary-label">Progresso</span>
        <strong>${progress}%</strong>
        <small>${job.current_stage}</small>
      </div>
      <div class="summary-card">
        <span class="summary-label">Stato</span>
        <strong>${humanStatus(job)}</strong>
        <small>ultimo update ${new Date(job.metrics.last_updated_at).toLocaleString("it-IT")}</small>
      </div>
    </div>
    <div class="progress-track"><div class="progress-bar" style="width:${progress}%"></div></div>
  `;
  const stageCards = stages.map((stage, index) => {
    const state = getStageState(job, stage);
    const activeClass = job.current_stage === stage && job.status === "running" ? "active" : "";
    return `<div class="stage-row ${activeClass}">
      <strong>${index + 1}. ${stage}</strong>
      <span class="badge ${state}">${state}</span>
    </div>`;
  }).join("");

  const attention = job.status === "needs_attention" && job.attention_request ? `
    <div class="attention-box">
      <strong>Intervento richiesto</strong>
      <p>${job.attention_request.reason}</p>
      <pre>${JSON.stringify(job.attention_request.details || {}, null, 2)}</pre>
      <div class="actions">
        <button onclick="reviewJob('${job.job_id}', 'approve')">Approva</button>
        <button class="secondary" onclick="reviewJob('${job.job_id}', 'reject')">Rifiuta</button>
      </div>
    </div>` : "";

  const stopAction = ["running", "queued", "needs_attention"].includes(job.status) ? `
    <div class="actions top-actions">
      <button class="danger-button" onclick="stopJob('${job.job_id}')">Blocca tutto</button>
    </div>` : "";

  const result = job.final_video_path ? `
    <a class="result-link" href="/artifacts/${job.job_id}/final/${job.book_id}.mp4" target="_blank" rel="noreferrer">Apri video finale</a>` : "";

  const errors = job.errors && job.errors.length ? `
    <h3>Errori</h3>
    <pre>${job.errors.join("\n")}</pre>` : "";

  const events = [...job.events]
    .filter(event => !(stages.includes(event.stage) && ["running", "completed"].includes(event.status)))
    .sort((left, right) => new Date(left.timestamp) - new Date(right.timestamp))
    .slice(-18)
    .map(event => `
    <div class="event-row">
      <strong>${event.stage}</strong>
      <span class="badge ${event.status}">${event.status}</span>
      <small>${new Date(event.timestamp).toLocaleString("it-IT")}</small>
      <p>${event.message}</p>
    </div>
  `).join("");

  jobDetail.classList.remove("empty");
  jobDetail.innerHTML = `
    ${stopAction}
    ${attention}
    <div class="stage-list">${stageCards}</div>
    ${result}
    ${errors}
    <h3>Cronologia</h3>
    <div class="event-list">${events}</div>
  `;
}

async function fetchSelectedJob() {
  if (!selectedJobId) {
    renderEmptyDashboard();
    return;
  }
  const response = await fetch(`/api/jobs/${selectedJobId}`);
  if (!response.ok) {
    renderEmptyDashboard();
    return;
  }
  const job = await response.json();
  renderJob(job);
  document.querySelectorAll(".job-pill").forEach(item => {
    item.classList.toggle("active", item.dataset.jobId === selectedJobId);
  });
}

async function reviewJob(jobId, action) {
  const formData = new FormData();
  formData.append("action", action);
  const response = await fetch(`/api/jobs/${jobId}/review`, { method: "POST", body: formData });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Review fallita" }));
    window.alert(payload.detail || "Review fallita");
    return;
  }
  await refreshAll();
}

async function stopJob(jobId) {
  const confirmed = window.confirm("Bloccare subito il job corrente?");
  if (!confirmed) {
    return;
  }
  await fetch(`/api/jobs/${jobId}/stop`, { method: "POST" });
  await refreshAll();
}

async function refreshAll() {
  await fetchJobs();
  await fetchSelectedJob();
}

jobsList.addEventListener("click", (event) => {
  const button = event.target.closest(".job-pill");
  if (!button) {
    return;
  }
  selectedJobId = button.dataset.jobId;
  fetchSelectedJob();
});

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (uploadInFlight) {
    return;
  }
  if (!fileInput.files || !fileInput.files.length) {
    uploadStatus.textContent = "Seleziona prima un file valido.";
    return;
  }
  uploadInFlight = true;
  submitButton.disabled = true;
  uploadStatus.textContent = "Upload in corso...";
  const formData = new FormData(uploadForm);
  const response = await fetch("/api/jobs", { method: "POST", body: formData });
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ detail: "Upload fallito" }));
    uploadStatus.textContent = payload.detail || "Upload fallito";
    uploadInFlight = false;
    submitButton.disabled = false;
    return;
  }
  const payload = await response.json();
  uploadStatus.textContent = "File caricato, job avviato.";
  uploadInFlight = false;
  uploadForm.reset();
  fileInput.value = "";
  fileLabel.textContent = "Trascina o seleziona un file `.txt`, `.md`, `.pdf`, `.docx`";
  submitButton.disabled = true;
  await refreshAll();
});

fileInput.addEventListener("change", () => {
  const file = fileInput.files && fileInput.files[0];
  if (!file) {
    fileLabel.textContent = "Trascina o seleziona un file `.txt`, `.md`, `.pdf`, `.docx`";
    uploadStatus.textContent = "Nessun file selezionato";
    submitButton.disabled = true;
    return;
  }
  fileLabel.textContent = file.name;
  uploadStatus.textContent = `Pronto: ${file.name}`;
  submitButton.disabled = false;
});

renderEmptyDashboard();
refreshAll();
setInterval(refreshAll, 4000);
window.reviewJob = reviewJob;
window.stopJob = stopJob;
