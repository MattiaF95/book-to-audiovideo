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
const detailsModal = document.getElementById("details-modal");
const detailsTitle = document.getElementById("details-title");
const detailsFile = document.getElementById("details-file");
const detailsJson = document.getElementById("details-json");
let selectedJobId = null;
let uploadInFlight = false;

const stages = ["ingestion", "text_cleanup", "narrative_context", "dialogue_segmentation", "speaker_registry", "speaker_attribution", "narrative_annotation", "voice_casting", "pronunciation_planning", "prosody_planning", "media_planning", "media_fetch", "tts", "audio_mix", "video_compose", "qa", "manifest"];
const legacyLabels = { cleanup: "Pulizia testo", text_preparation: "Preparazione testo", story_structure: "Struttura narrativa", audio_planning: "Piano audio", voice_assignment: "Assegnazione voce" };
const stageDescriptions = {
  ingestion: "Legge il file sorgente.", text_cleanup: "Pulisce il testo in modo conservativo.", narrative_context: "Ricava scena, tono e ambientazione.", dialogue_segmentation: "Divide narrazione e dialoghi.", speaker_registry: "Crea il registro stabile degli speaker.", speaker_attribution: "Assegna ogni segmento allo speaker.", narrative_annotation: "Aggiunge emozione e importanza.", voice_casting: "Sceglie le voci per gli speaker.", pronunciation_planning: "Prepara le pronunce utili al TTS.", prosody_planning: "Definisce ritmo e intonazione.", media_planning: "Prepara il piano video.", media_fetch: "Cerca il video di sfondo.", tts: "Genera l'audio parlato.", audio_mix: "Mixa e normalizza l'audio.", video_compose: "Compone il video finale.", qa: "Controlla il risultato.", manifest: "Scrive il riepilogo finale."
};

function escapeHtml(value) { const node = document.createElement("div"); node.textContent = String(value ?? ""); return node.innerHTML; }
function labelFor(stage) { return legacyLabels[stage] || stage.replaceAll("_", " "); }
function renderEmptyDashboard() {
  selectedJobId = null;
  jobStatus.textContent = "Nessuna selezionata";
  [jobExplainer, jobSummary, jobDetail].forEach((element) => element.classList.add("empty"));
  jobExplainer.textContent = "Seleziona una pipeline per vedere fase corrente e significato dello step attivo.";
  jobSummary.textContent = "La visualizzazione è stata azzerata. Lo storico locale resta disponibile nella colonna a sinistra.";
  jobDetail.textContent = "Apri una pipeline e clicca Dettagli su un agente per leggere il JSON prodotto.";
  document.querySelectorAll(".job-pill").forEach((item) => item.classList.remove("active"));
}
async function fetchJobs() {
  const response = await fetch("/api/jobs");
  const jobs = await response.json();
  jobsCount.textContent = jobs.length;
  jobsList.innerHTML = jobs.map((job) => `<button class="job-pill ${job.job_id === selectedJobId ? "active" : ""}" data-job-id="${escapeHtml(job.job_id)}"><strong>${escapeHtml(job.source_name)}</strong><span><i class="status-dot ${escapeHtml(job.status)}"></i>${escapeHtml(humanStatus(job))}</span><small>${escapeHtml(new Date(job.metrics.last_updated_at).toLocaleString("it-IT"))}</small></button>`).join("") || `<p class="muted">Nessuna pipeline salvata.</p>`;
}
function stageNames(job) {
  const seen = [];
  job.events.forEach((event) => { if (!["queued", "completed"].includes(event.stage) && !seen.includes(event.stage)) seen.push(event.stage); });
  return seen.length ? seen : stages;
}
function getStageState(job, stage) { const match = [...job.events].reverse().find((item) => item.stage === stage); return match ? match.status : "pending"; }
function computeProgress(job, names) { return Math.round((names.filter((stage) => getStageState(job, stage) === "completed").length / names.length) * 100); }
function humanStatus(job) { return { running: `In lavorazione: ${labelFor(job.current_stage)}`, queued: "In coda", needs_attention: `Richiede attenzione: ${labelFor(job.current_stage)}`, completed: "Completata", failed: "Fallita", cancelled: "Interrotta", rejected: "Rifiutata" }[job.status] || job.status; }
function renderJob(job) {
  const names = stageNames(job); const progress = computeProgress(job, names);
  jobStatus.textContent = humanStatus(job);
  jobExplainer.classList.remove("empty"); jobExplainer.innerHTML = `<div class="explainer-grid"><div class="explainer-card accent-card"><span class="summary-label">Fase corrente</span><strong>${escapeHtml(labelFor(job.current_stage))}</strong><small>${escapeHtml(stageDescriptions[job.current_stage] || legacyLabels[job.current_stage] || "Stage storico della pipeline.")}</small></div><div class="explainer-card"><span class="summary-label">Output</span><strong>${job.status === "completed" ? "Video pronto" : job.status === "failed" ? "Serve revisione" : "Monitoraggio attivo"}</strong><small>${job.errors?.length ? escapeHtml(job.errors[job.errors.length - 1]) : "Gli aggiornamenti arrivano automaticamente."}</small></div></div>`;
  jobSummary.classList.remove("empty"); jobSummary.innerHTML = `<div class="summary-grid"><div class="summary-card"><span class="summary-label">Sorgente</span><strong>${escapeHtml(job.source_name)}</strong><small>${job.segments.length} segmenti · ${job.speakers.length} speaker</small></div><div class="summary-card"><span class="summary-label">Avanzamento</span><strong>${progress}%</strong><small>${names.length} stage visualizzati</small></div><div class="summary-card"><span class="summary-label">Ultimo aggiornamento</span><strong>${escapeHtml(new Date(job.metrics.last_updated_at).toLocaleTimeString("it-IT"))}</strong><small>${escapeHtml(humanStatus(job))}</small></div></div><div class="progress-track"><div class="progress-bar" style="width:${progress}%"></div></div>`;
  const stageCards = names.map((stage, index) => { const state = getStageState(job, stage); const active = job.current_stage === stage && ["running", "needs_attention"].includes(job.status); return `<article class="stage-row ${active ? "active" : ""} ${state}"><div class="stage-index">${String(index + 1).padStart(2, "0")}</div><div class="stage-main"><strong>${escapeHtml(labelFor(stage))}</strong><small>${escapeHtml(stageDescriptions[stage] || "Stage storico")}</small></div><span class="badge ${escapeHtml(state)}">${escapeHtml(state)}</span><button class="details-button" data-stage="${escapeHtml(stage)}" data-label="${escapeHtml(labelFor(stage))}">Dettagli</button></article>`; }).join("");
  const attention = job.status === "needs_attention" && job.attention_request ? `<div class="attention-box"><strong>Intervento richiesto</strong><p>${escapeHtml(job.attention_request.reason)}</p><pre>${escapeHtml(JSON.stringify(job.attention_request.details || {}, null, 2))}</pre><div class="actions"><button onclick="reviewJob('${job.job_id}', 'approve')">Approva</button><button class="secondary" onclick="reviewJob('${job.job_id}', 'reject')">Rifiuta</button></div></div>` : "";
  const stopAction = ["running", "queued", "needs_attention"].includes(job.status) ? `<div class="actions top-actions"><button class="danger-button" onclick="stopJob('${job.job_id}')">Blocca tutto</button></div>` : "";
  const result = job.final_video_path ? `<a class="result-link" href="/artifacts/${job.job_id}/final/${encodeURIComponent(job.book_id)}.mp4" target="_blank" rel="noreferrer">Apri video finale →</a>` : "";
  const events = [...job.events].filter((event) => !(names.includes(event.stage) && ["running", "completed"].includes(event.status))).slice(-12).reverse().map((event) => `<div class="event-row"><strong>${escapeHtml(labelFor(event.stage))}</strong><span class="badge ${escapeHtml(event.status)}">${escapeHtml(event.status)}</span><small>${escapeHtml(new Date(event.timestamp).toLocaleString("it-IT"))}</small><p>${escapeHtml(event.message)}</p></div>`).join("");
  jobDetail.classList.remove("empty"); jobDetail.innerHTML = `${stopAction}${attention}<div class="pipeline-head"><div><span class="section-kicker">Execution map</span><h3>Sequenza agent</h3></div><span class="pipeline-count">${names.length} step</span></div><div class="stage-list">${stageCards}</div>${result}${job.errors?.length ? `<h3>Errori</h3><pre>${escapeHtml(job.errors.join("\n"))}</pre>` : ""}<h3>Cronologia</h3><div class="event-list">${events || `<p class="muted">Nessun evento aggiuntivo.</p>`}</div>`;
}
async function fetchSelectedJob() { if (!selectedJobId) return renderEmptyDashboard(); const response = await fetch(`/api/jobs/${selectedJobId}`); if (!response.ok) return renderEmptyDashboard(); renderJob(await response.json()); }
async function showDetails(stage, label) { detailsModal.hidden = false; detailsTitle.textContent = label; detailsFile.textContent = "Ricerca output locale…"; detailsJson.textContent = "Caricamento…"; const response = await fetch(`/api/jobs/${selectedJobId}/stage-details/${encodeURIComponent(stage)}`); if (!response.ok) { detailsFile.textContent = "Questo stage storico non ha un JSON leggibile."; detailsJson.textContent = "Nessun dettaglio disponibile."; return; } const data = await response.json(); detailsFile.textContent = data.file_name; detailsJson.textContent = JSON.stringify(data.payload, null, 2); }
function closeDetails() { detailsModal.hidden = true; }
async function reviewJob(jobId, action) { const formData = new FormData(); formData.append("action", action); const response = await fetch(`/api/jobs/${jobId}/review`, { method: "POST", body: formData }); if (!response.ok) { window.alert("Review fallita"); return; } await refreshAll(); }
async function stopJob(jobId) { if (!window.confirm("Bloccare subito il job corrente?")) return; await fetch(`/api/jobs/${jobId}/stop`, { method: "POST" }); await refreshAll(); }
async function refreshAll() { await fetchJobs(); if (selectedJobId) await fetchSelectedJob(); }
jobsList.addEventListener("click", (event) => { const button = event.target.closest(".job-pill"); if (button) { selectedJobId = button.dataset.jobId; fetchSelectedJob(); return; } const detailButton = event.target.closest(".details-button"); if (detailButton) showDetails(detailButton.dataset.stage, detailButton.dataset.label); });
jobDetail.addEventListener("click", (event) => { const detailButton = event.target.closest(".details-button"); if (detailButton) showDetails(detailButton.dataset.stage, detailButton.dataset.label); });
document.getElementById("reset-dashboard").addEventListener("click", renderEmptyDashboard);
document.querySelectorAll("[data-close-details]").forEach((element) => element.addEventListener("click", closeDetails));
document.addEventListener("keydown", (event) => { if (event.key === "Escape") closeDetails(); });
uploadForm.addEventListener("submit", async (event) => { event.preventDefault(); if (uploadInFlight || !fileInput.files?.length) return; uploadInFlight = true; submitButton.disabled = true; uploadStatus.textContent = "Upload in corso…"; const response = await fetch("/api/jobs", { method: "POST", body: new FormData(uploadForm) }); if (!response.ok) { uploadStatus.textContent = "Upload fallito"; uploadInFlight = false; submitButton.disabled = false; return; } const payload = await response.json(); uploadStatus.textContent = "Pipeline avviata"; uploadInFlight = false; uploadForm.reset(); fileLabel.textContent = "Trascina o seleziona un file `.txt`, `.md`, `.pdf`, `.docx`"; submitButton.disabled = true; selectedJobId = payload.job_id; await refreshAll(); });
fileInput.addEventListener("change", () => { const file = fileInput.files?.[0]; fileLabel.textContent = file ? file.name : "Trascina o seleziona un file `.txt`, `.md`, `.pdf`, `.docx`"; uploadStatus.textContent = file ? `Pronto: ${file.name}` : "Nessun file selezionato"; submitButton.disabled = !file; });
renderEmptyDashboard(); refreshAll(); setInterval(refreshAll, 4000); window.reviewJob = reviewJob; window.stopJob = stopJob;
