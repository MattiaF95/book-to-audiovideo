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

| # | Fase | Agente | Usa LLM | Provider / modello | Ruolo | Solo chiamate? |
|---|---|---|---|---|---|---|
| 1 | 📥 Ingestion | `IngestionAgent` | No | Nessuno | Carica il file sorgente grezzo senza manipolarlo | No, solo lettura file |
| 2 | ✨ Text cleanup | `TextCleanupAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Corregge solo errori evidenti, preservando stile e significato | No, usa LLM |
| 3 | 🧭 Narrative context | `NarrativeContextAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Estrae solo il contesto globale minimo utile ai passaggi successivi | No, usa LLM |
| 4 | ✂️ Dialogue segmentation | `DialogueSegmentationAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Divide il testo in segmenti ordinati di narrazione o dialogo | No, usa LLM |
| 5 | 👥 Speaker registry | `SpeakerRegistryAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Costruisce il registro stabile di narratore e personaggi ricorrenti | No, usa LLM |
| 6 | 🗣️ Speaker attribution | `SpeakerAttributionAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Assegna ogni segmento a un solo speaker riusando gli speaker_id stabili | No, usa LLM |
| 7 | 🏷️ Narrative annotation | `NarrativeAnnotationAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Aggiunge solo annotazioni leggere per segmento | No, usa LLM |
| 8 | 🎙️ Voice casting | `VoiceCastingAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` + ElevenLabs metadata | Sceglie una voce stabile per narratore e personaggi ricorrenti | No, usa LLM + metadata provider |
| 9 | 🔤 Pronunciation planning | `PronunciationPlanningAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Produce solo hints di pronuncia davvero necessari | No, usa LLM |
| 10 | 🎚️ Prosody planning | `ProsodyPlanningAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Definisce solo tone tags minimi utili al TTS | No, usa LLM |
| 11 | 🎞️ Media planning | `MediaPlanningAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Prepara solo query e piano media di sfondo per segmento | No, usa LLM |
| 12 | 🎥 Media fetch | `MediaFetchAgent` | No | Pixabay API | Cerca e scarica il video di sfondo | Sì, fa solo chiamate a un provider non-LLM |
| 13 | 🔊 TTS | `TTSAgent` | Sì | ElevenLabs API | Genera l'audio finale riusando speaker reference e continuity anchor | Sì, fa solo chiamate al provider TTS |
| 14 | 🎚️ Mix | `AudioMixAgent` | No | FFmpeg locale | Miscela voce e SFX/track secondarie | No, usa FFmpeg locale |
| 15 | 🎬 Video | `VideoComposeAgent` | No | FFmpeg locale | Unisce audio finale e video Pixabay | No, usa FFmpeg locale |
| 16 | 🧪 QA | `QAAgent` | No | FFmpeg locale | Controlla durata, loudness e coerenza tecnica | No, analisi locale |
| 17 | 📦 Manifest | `ManifestAgent` | No | Nessuno | Scrive il riepilogo finale del job | No, serializzazione locale |

### Prompt attivi

Ogni agente LLM del flusso attivo ha un prompt dedicato in `src/book_to_audiovideo/prompts/`:

| Agente | Prompt |
|---|---|
| `TextCleanupAgent` | `text_cleanup.md` |
| `NarrativeContextAgent` | `narrative_context.md` |
| `DialogueSegmentationAgent` | `dialogue_segmentation.md` |
| `SpeakerRegistryAgent` | `speaker_registry.md` |
| `SpeakerAttributionAgent` | `speaker_attribution.md` |
| `NarrativeAnnotationAgent` | `narrative_annotation.md` |
| `VoiceCastingAgent` | `voice_casting.md` |
| `PronunciationPlanningAgent` | `pronunciation_planning.md` |
| `ProsodyPlanningAgent` | `prosody_planning.md` |
| `MediaPlanningAgent` | `media_planning.md` |

---

## 🧱 Architettura

| Cartella | Contenuto |
|---|---|
| `src/book_to_audiovideo/agents/` | Agent piccoli con compiti separati |
| `src/book_to_audiovideo/providers/` | Adapter live Groq, ElevenLabs, Pixabay |
| `src/book_to_audiovideo/services/` | Parsing file, FFmpeg, durata, query media |
| `src/book_to_audiovideo/pipeline/orchestrator.py` | Stato job, persistenza, resume e pause manuali |
| `src/book_to_audiovideo/web/` | Dashboard locale FastAPI + template/static frontend |

---

## 🖥️ Dashboard locale

La dashboard permette di:

- caricare il file sorgente.
- vedere lo stato di ogni agent e gli eventi del job.
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
| `LLM_MIN_INTERVAL_SECONDS` | Rate limit globale tra chiamate LLM |
| `FFMPEG_BIN` | Path binario FFmpeg |
| `FFPROBE_BIN` | Path binario ffprobe |

---

## 🔁 Flusso pipeline

| # | Stage |
|---|---|
| 1 | `ingestion` |
| 2 | `text_cleanup` |
| 3 | `narrative_context` |
| 4 | `dialogue_segmentation` |
| 5 | `speaker_registry` |
| 6 | `speaker_attribution` |
| 7 | `narrative_annotation` |
| 8 | `voice_casting` |
| 9 | `pronunciation_planning` |
| 10 | `prosody_planning` |
| 11 | `media_planning` |
| 12 | `media_fetch` |
| 13 | `tts` |
| 14 | `audio_mix` |
| 15 | `video_compose` |
| 16 | `qa` |
| 17 | `manifest` |

---

## 📁 Artefatti output

Ogni job crea `data/output/<job_id>/` con:

| Cartella/File | Contenuto |
|---|---|
| `state.json` | Stato completo del job |
| JSON stage-by-stage | Output di ogni fase |
| `source/` | File sorgente e normalizzazioni |
| `media/video/` | Video selezionati |
| `tts/` | Audio generati da ElevenLabs |
| `mix/` | Mix audio finali |
| `final/<book_id>.mp4` | Video finale |
| `manifest.json` | Riepilogo completo |

---

## 📝 Note operative

- La pipeline non continua in loop quando un provider fallisce.
- Se Pixabay non restituisce un video utilizzabile, il job entra in `needs_attention`.
- Il video di sfondo è unico; se più corto viene loopato da FFmpeg.
- Groq usa lo SDK ufficiale con Chat Completions in streaming e forza output JSON con `response_format`.
- Le chiamate Groq sono serializzate con un rate limiter globale `LLM_MIN_INTERVAL_SECONDS` tra richieste consecutive.
- Il flusso LLM è stato separato in pass piccoli a compito singolo per ridurre errori di validazione JSON e coreference.
- Il narratore è uno speaker unico e stabile in tutto il progetto.
- Ogni speaker ricorrente mantiene uno `speaker_id` stabile e una `continuity_anchor` riusabile nei segmenti successivi verso ElevenLabs.
- ElevenLabs request stitching è usato solo con modelli compatibili; non viene usato con `eleven_v3`.
- Nei modelli che supportano stitching, gli ID di contesto vengono mantenuti in una coda fissa di massimo 3 elementi.
- Il QA finale non blocca il job: scrive `warning` se loudness o durata non sono nei valori attesi. ⚠️

---

## 📌 Limiti MVP

| Limite | Dettaglio |
|---|---|
| Test | Offline e mock, non API reali |
| Pixabay | Solo ricerca video; il risultato viene scaricato nella variante `medium` quando disponibile |
| Voce | La scelta dipende dalle voci del tuo account |
| Dashboard | Solo upload, monitoraggio, approve/reject e apertura output finale |

## ⭐ Crediti

Autore: **MattiaF95**
