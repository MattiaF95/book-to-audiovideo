# 📚 Book to Audiovideo

Pipeline locale MVP-first per trasformare un libro in un video narrato usando solo provider API esterni: Groq per analisi testo, ElevenLabs per TTS, Pixabay per video e FFmpeg per il compositing finale.

| Area | Scelta | Ruolo |
|---|---|---|
| 🧠 LLM | `llama-3.1-8b-instant` via Groq | Analisi testo, pulizia conservativa, segmentazione, speaker resolution, media planning |
| 🔊 TTS | ElevenLabs | Sintesi vocale per i segmenti narrati e dialogati |
| 🎬 Media | Pixabay | Video di sfondo |
| 🎞️ Compositing | FFmpeg | Mix audio, loop video, export finale |

---

## 🤖 Pipeline / AI Agent

| # | Fase | Agente | Usa LLM | Provider / modello | Ruolo | Solo chiamate? |
|---|---|---|---|---|---|---|
| 1 | 📥 Ingestion | `IngestionAgent` | No | Nessuno | Carica il file sorgente e normalizza l'ingresso | No, logica locale |
| 2 | ✨ Cleanup | `CleanupAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Pulisce il testo grezzo in modo conservativo | No, usa LLM + merge locale |
| 3 | 🔪 Chunking | `ChunkingAgent` | No | Nessuno | Divide il testo in chunk gestibili | No, logica locale |
| 4 | 🗣️ Dialogue | `DialogueSegmentationAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Divide ogni chunk in segmenti narratore/personaggio con ordine esplicito | No, usa LLM + validazione locale |
| 5 | 👥 Speaker | `SpeakerResolutionAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Riconcilia i personaggi e assegna speaker stabili | No, usa LLM + normalizzazione locale |
| 6 | 🎭 Voice | `VoiceAssignmentAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` + ElevenLabs API | Assegna una voce coerente a ogni speaker e risolve la voce finale TTS | No, usa LLM + chiamate provider |
| 7 | 🧩 Enrichment | `SegmentEnrichmentAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Estrae pronuncia, tono e piano media per ogni segmento | No, usa LLM + validazione locale |
| 8 | 🎥 Media | `MediaFetchAgent` | No | Pixabay API | Cerca e scarica il video di sfondo per i segmenti pianificati | Sì, fa solo chiamate a un provider non-LLM |
| 9 | 🎙️ TTS | `TTSAgent` | Sì | ElevenLabs API | Genera i file audio dei segmenti con il modello TTS del provider | Sì, fa solo chiamate a un provider LLM-TTS |
| 10 | 🎚️ Mix | `AudioMixAgent` | No | FFmpeg locale | Miscela voce e SFX/track secondarie | No, usa FFmpeg locale |
| 11 | 🎬 Video | `VideoComposeAgent` | No | FFmpeg locale | Unisce audio finale e video Pixabay | No, usa FFmpeg locale |
| 12 | 🧪 QA | `QAAgent` | No | FFmpeg locale | Controlla durata, loudness e coerenza tecnica | No, analisi locale |
| 13 | 📦 Manifest | `ManifestAgent` | No | Nessuno | Scrive il riepilogo finale del job | No, serializzazione locale |

---

## 🧱 Architettura

| Cartella | Contenuto |
|---|---|
| `src/book_to_audiovideo/agents/` | Agent piccoli con compiti separati |
| `src/book_to_audiovideo/providers/` | Adapter live Groq, ElevenLabs, Pixabay |
| `src/book_to_audiovideo/services/` | Parsing file, chunking, FFmpeg, durata, query media |
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
pip install -e ".[dev]"
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
| 2 | `cleanup` |
| 3 | `chunking` |
| 4 | `dialogue_segmentation` |
| 5 | `speaker_resolution` |
| 6 | `voice_assignment` |
| 7 | `segment_enrichment` |
| 8 | `media_fetch` |
| 9 | `tts` |
| 10 | `audio_mix` |
| 11 | `video_compose` |
| 12 | `qa` |
| 13 | `manifest` |

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
- Groq usa l'endpoint OpenAI-compatible Chat Completions e forza output JSON con `response_format`.
- Le chiamate Groq sono serializzate con un rate limiter globale `LLM_MIN_INTERVAL_SECONDS` tra richieste consecutive.
- Pronunciation, tone tagging e media planning sono stati accorpati in un solo pass LLM per ridurre il rischio di `429`.
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
