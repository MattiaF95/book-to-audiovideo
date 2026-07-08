# 📚 Book to Audiovideo

Pipeline locale MVP-first per trasformare un libro in un video narrato usando solo provider API esterni: Groq via API OpenAI-compatible per analisi testo, ElevenLabs per TTS, Pixabay per video e FFmpeg per il compositing finale.

| Area | Scelta | Ruolo |
|---|---|---|
| 🧠 LLM | `qwen/qwen3.6-27b` via Groq API OpenAI-compatible | Cleanup testo, analisi narrativa, casting voci, pronuncia, prosodia e media planning in pass separati |
| 🔊 TTS | ElevenLabs | Sintesi vocale per i segmenti narrati e dialogati |
| 🎬 Media | Pixabay | Video di sfondo |
| 🎞️ Compositing | FFmpeg | Mix audio, loop video, export finale |

---

## 🤖 Pipeline / AI Agent

| # | Fase | Agente | Usa LLM | Input principale | Output prodotto |
|---|---|---|---|---|---|
| 1 | 📥 Ingestion | `IngestionAgent` | No | File sorgente su disco | Testo grezzo in `state` |
| 2 | ✨ Text cleanup | `TextCleanupAgent` | Sì | Testo grezzo | Testo corretto, lista correzioni |
| 3 | 🧭 Narrative context | `NarrativeContextAgent` | Sì | Testo corretto | Scena, tono, ambientazione globale |
| 4 | ✂️ Dialogue segmentation | `DialogueSegmentationAgent` | **No** | Testo corretto | Lista segmenti `narration`/`dialogue` con offset — **divisione deterministica via regex su `«»`** |
| 5 | 👥 Speaker registry | `SpeakerRegistryAgent` | Sì | Testo corretto + context | Registro stabile di narratore e personaggi con `speaker_id` e `continuity_key` |
| 6 | 🗣️ Speaker attribution | `SpeakerAttributionAgent` | Sì | Segmenti + registry | Ogni segmento associato a un `speaker_id`; dialoghi non attribuibili → `null` + warning |
| 7 | 🏷️ Narrative annotation | `NarrativeAnnotationAgent` | Sì | Segmenti attribuiti | `emotion_hint` e `importance_score` per ogni segmento |
| 8 | 🎙️ Voice casting | `VoiceCastingAgent` | Sì | Registry + voci ElevenLabs disponibili | Voce stabile per ogni speaker con `delivery_style` e `tts_prompt_tags` |
| 9 | 🔤 Pronunciation planning | `PronunciationPlanningAgent` | Sì | Segmenti | Override di testo e hint fonetici IPA per termini a rischio |
| 10 | 🎚️ Prosody planning | `ProsodyPlanningAgent` | Sì | Segmenti + annotazioni | Tag SSML inline (`<emphasis>`, `<break>`, `<prosody>`) per ogni segmento |
| 11 | 🎞️ Media planning | `MediaPlanningAgent` | Sì | Segmenti + annotazioni | Keyword video/SFX, mood e intensità per ogni segmento |
| 12 | 🎥 Media fetch | `MediaFetchAgent` | No | Piano media | Video Pixabay scaricati localmente |
| 13 | 🔊 TTS | `TTSAgent` | No | Segmenti + voice casting + prosody + pronunciation | File audio `.mp3` per ogni segmento via ElevenLabs |
| 14 | 🎚️ Mix | `AudioMixAgent` | No | Audio TTS + SFX | Mix voce + tracce secondarie per ogni segmento |
| 15 | 🎬 Video | `VideoComposeAgent` | No | Mix audio + video Pixabay | Video finale `.mp4` |
| 16 | 🧪 QA | `QAAgent` | No | Video finale | Report loudness, durata, coerenza tecnica |
| 17 | 📦 Manifest | `ManifestAgent` | No | Intero `state` | `manifest.json` riepilogativo del job |

> **Step 4 — nessuna chiamata LLM.** La segmentazione dialogo/narrazione è deterministica: il codice Python spezza il testo su ogni `«` e `»`, garantendo confini esatti senza possibilità di errore del modello.

> Sono stati fatti vari tentativi con svariati modelli tra cui llama-3.1-8b-instant, llama-3.3-70b-versatile e quello attuale qwen/qwen3.6-27b. Tutte e tre i modelli non riescono sempre a dividere la narrazione dal dialogo, nonostante prompt precisi (anche qui ho provato diversi prompt, dai più "liberi" ai più "dettagliati". Ad esempio specificando che il testo dentro le parentesi << dialogo >> è da considerare dialogo) i modelli sbagliavano divisione, unendo segmente di testo (dialogo + narrazione) perchè nella "stessa frase". Per questo, per fare un primo test di funzionamento ho deciso di dare al modelli LLM il testo in ingresso già segmentato. 

> **Stage 6 — fallback sicuro.** La narrazione viene sempre assegnata al narratore. I dialoghi non attribuibili (nessun verbo di dire adiacente, alternanza ambigua) ricevono `resolved_speaker_id: null` e generano un `warning` nello state invece di essere silenziosamente assegnati al narratore.

### Prompt attivi

Ogni agente LLM ha un prompt dedicato in `src/book_to_audiovideo/prompts/`:

| Agente | Prompt | Compito in una riga |
|---|---|---|
| `TextCleanupAgent` | `text_cleanup.md` | Corregge typo, OCR noise (perchè in input può ricevere formati diversi), spaziatura |
| `NarrativeContextAgent` | `narrative_context.md` | Estrae scena, tono, ambientazione, periodo |
| `SpeakerRegistryAgent` | `speaker_registry.md` | Identifica narratore e personaggi ricorrenti |
| `SpeakerAttributionAgent` | `speaker_attribution.md` | Attribuisce ogni segmento a uno speaker_id |
| `NarrativeAnnotationAgent` | `narrative_annotation.md` | Aggiunge emotion_hint e importance_score |
| `VoiceCastingAgent` | `voice_casting.md` | Sceglie voce stabile per ogni speaker |
| `PronunciationPlanningAgent` | `pronunciation_planning.md` | Override testo e hint IPA per TTS (per correggere eventuali errori di pronuncia del LLM-TTS) |
| `ProsodyPlanningAgent` | `prosody_planning.md` | Tag SSML per ritmo, enfasi e pause |
| `MediaPlanningAgent` | `media_planning.md` | Keyword video e mood per segmento |

> `DialogueSegmentationAgent` non usa prompt LLM — la segmentazione è interamente in codice per il problema descritto sopra (vedi info step 4). Il prompt è stato comunque lasciato come documentazione e/o futuro reintegro.

---

## 🧱 Architettura

| Cartella | Contenuto |
|---|---|
| `src/book_to_audiovideo/agents/` | Agent piccoli con compiti separati |
| `src/book_to_audiovideo/prompts/` | Prompt Markdown uno-per-agent, caricati a runtime |
| `src/book_to_audiovideo/providers/` | Adapter live Groq, ElevenLabs, Pixabay |
| `src/book_to_audiovideo/services/` | Parsing file, FFmpeg, durata, query media |
| `src/book_to_audiovideo/pipeline/orchestrator.py` | Stato job, persistenza, resume e pause manuali |
| `src/book_to_audiovideo/web/` | Dashboard locale FastAPI + template/static frontend |

---

## 🖥️ Dashboard locale

La dashboard permette di:

- caricare il file sorgente.
- vedere lo stato di ogni agent e gli eventi del job.
- avere una cronologia in locale dei test effettuati (creata in data/output/)
- approvare o rifiutare stop manuali `needs_attention`.
- aprire il video finale generato. 🎬

Avvio:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m book_to_audiovideo.main serve
```

Poi apri `http://127.0.0.1:8000`.

---

## 🏃 Esecuzione CLI

Per eseguire un job senza dashboard:

```bash
python -m book_to_audiovideo.main run path/al/libro.txt
```

---

## 🔐 Variabili ambiente

| Variabile | Uso |
|---|---|
| `GROQ_API_KEY` | Accesso a Groq |
| `ELEVENLABS_API_KEY` | Accesso a ElevenLabs |
| `PIXABAY_API_KEY` | Accesso a Pixabay |
| `OUTPUT_DIR` | Directory output |
| `CACHE_DIR` | Cache locale |
| `LOG_LEVEL` | Livello log |
| `DEFAULT_TTS_MODEL` | Modello TTS di default |
| `DEFAULT_LLM_MODEL` | Modello LLM di default |
| `LLM_MIN_INTERVAL_SECONDS` | Rate limit globale tra chiamate LLM consecutive |
| `FFMPEG_BIN` | Path binario FFmpeg |
| `FFPROBE_BIN` | Path binario ffprobe |

---

## 🔁 Flusso pipeline

| # | Stage | Tipo |
|---|---|---|
| 1 | `ingestion` | I/O locale |
| 2 | `text_cleanup` | LLM |
| 3 | `narrative_context` | LLM |
| 4 | `dialogue_segmentation` | **Regex Python** |
| 5 | `speaker_registry` | LLM |
| 6 | `speaker_attribution` | LLM |
| 7 | `narrative_annotation` | LLM |
| 8 | `voice_casting` | LLM + ElevenLabs metadata |
| 9 | `pronunciation_planning` | LLM |
| 10 | `prosody_planning` | LLM |
| 11 | `media_planning` | LLM |
| 12 | `media_fetch` | Pixabay API |
| 13 | `tts` | ElevenLabs API |
| 14 | `audio_mix` | FFmpeg locale |
| 15 | `video_compose` | FFmpeg locale |
| 16 | `qa` | FFmpeg locale |
| 17 | `manifest` | I/O locale |

---

## 📁 Artefatti output

Ogni job crea `data/output/<job_id>/` con:

| Cartella/File | Contenuto |
|---|---|
| `state.json` | Stato completo del job |
| `0N_<stage>.json` | Output JSON di ogni fase, nell'ordine di esecuzione |
| `source/` | File sorgente e normalizzazioni |
| `media/video/` | Video selezionati da Pixabay |
| `tts/` | File audio generati da ElevenLabs |
| `mix/` | Mix audio voce + SFX per segmento |
| `final/<book_id>.mp4` | Video finale |
| `manifest.json` | Riepilogo completo del job |

---

## 📝 Note operative

- La pipeline non continua in loop quando un provider fallisce.
- Se Pixabay non restituisce un video utilizzabile, il job entra in `needs_attention`.
- Il video di sfondo è unico; se più corto del necessario viene loopato da FFmpeg.
- Groq usa lo SDK ufficiale con Chat Completions in streaming e forza output JSON con `response_format`.
- Le chiamate Groq sono serializzate con un rate limiter globale (`LLM_MIN_INTERVAL_SECONDS`) tra richieste consecutive.
- Il flusso LLM è separato in passaggi piccoli a compito singolo per ridurre errori di validazione JSON e problemi di coreference.
- La segmentazione dialogo/narrazione è deterministica (regex su `<< >>`) e non consuma token Groq.
- Il narratore è uno speaker unico e stabile per tutto il progetto.
- Ogni speaker ricorrente mantiene `speaker_id` e `continuity_anchor` stabili, riusati da ElevenLabs per la continuità vocale tra segmenti.
- ElevenLabs request stitching è usato solo con modelli compatibili; non viene usato con `eleven_v3`.
- Il contesto di stitching mantiene una coda fissa di massimo 3 elementi (`request_id` + `history_item_id`).
- Il QA finale non blocca il job: scrive `warning` se loudness o durata non rientrano nei valori attesi. ⚠️

---

## 📌 Limiti MVP

| Limite | Dettaglio |
|---|---|
| Test | Offline e mock, non API reali |
| Delimitatori dialogo | Solo `<<>>` supportati; testi con `—` o `"` usano il prompt di fallback |
| Pixabay | Solo ricerca video; scaricato nella variante `medium` quando disponibile |
| Voce | La scelta dipende dalle voci disponibili nel tuo account ElevenLabs |
| Dashboard | Solo upload, monitoraggio, approve/reject e apertura output finale |

## ➡️ Implementazioni future

- Possibilità di dare un prompt direttamente in dashboard se l'agent ai si blocca per qualche motivo, cosi da non bloccare la pipeline e correggere al momento.
- Si può aggiungere un servizio che oltre il video aggiunge anche degli effetti sonori in base a cosa succede nel racconto.
- Avere direttamente in dashboard lo storico di ogni pipeline più dettagliato, senza andare a leggere i json nel codice.
- Deployare l'app cosi da poterla usare ovunque.
- Inserire validazione amdin/user per avere più controllo su chi la utilizza.

---

## ⭐ Crediti

Autore: **MattiaF95**