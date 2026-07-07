# 📚 Book to Audiovideo

Pipeline locale MVP-first per trasformare un libro in un video narrato usando solo provider API esterni: Groq per analisi testo, ElevenLabs per TTS, Pixabay per video e FFmpeg per il compositing finale.

| Area | Scelta | Ruolo |
|---|---|---|
| 🧠 LLM | `openai/gpt-oss-20b` via Groq | Pulizia testo, analisi contesto/emozioni, segmentazione speaker-aware, voice planning e media planning |
| 🔊 TTS | ElevenLabs | Sintesi vocale per i segmenti narrati e dialogati |
| 🎬 Media | Pixabay | Video di sfondo |
| 🎞️ Compositing | FFmpeg | Mix audio, loop video, export finale |

---

## 🤖 Pipeline / AI Agent

| # | Fase | Agente | Usa LLM | Provider / modello | Ruolo | Solo chiamate? |
|---|---|---|---|---|---|---|
| 1 | 📥 Ingestion | `IngestionAgent` | No | Nessuno | Carica il file sorgente grezzo senza manipolarlo | No, solo lettura file |
| 2 | ✨ Text prep | `TextPreparationAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Corregge refusi, mantiene lo stile e deduce contesto/emozioni | No, usa LLM |
| 3 | 🗣️ Story structure | `StoryStructureAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` | Identifica narratore, personaggi, dialoghi e ordine dei segmenti | No, usa LLM |
| 4 | 🎭 Audio planning | `AudioPlanningAgent` | Sì | Groq, `DEFAULT_LLM_MODEL` + ElevenLabs metadata | Sceglie voci, tono, pronuncia e media hints per ogni segmento | No, usa LLM + metadata provider |
| 5 | 🎙️ TTS | `TTSAgent` | Sì | ElevenLabs API | Genera i file audio finali dei segmenti | Sì, fa solo chiamate al provider LLM-TTS |
| 6 | 🎥 Media | `MediaFetchAgent` | No | Pixabay API | Cerca e scarica il video di sfondo per i segmenti pianificati | Sì, fa solo chiamate a un provider non-LLM |
| 7 | 🎚️ Mix | `AudioMixAgent` | No | FFmpeg locale | Miscela voce e SFX/track secondarie | No, usa FFmpeg locale |
| 8 | 🎬 Video | `VideoComposeAgent` | No | FFmpeg locale | Unisce audio finale e video Pixabay | No, usa FFmpeg locale |
| 9 | 🧪 QA | `QAAgent` | No | FFmpeg locale | Controlla durata, loudness e coerenza tecnica | No, analisi locale |
| 10 | 📦 Manifest | `ManifestAgent` | No | Nessuno | Scrive il riepilogo finale del job | No, serializzazione locale |

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
| 2 | `text_preparation` |
| 3 | `story_structure` |
| 4 | `audio_planning` |
| 5 | `tts` |
| 6 | `media_fetch` |
| 7 | `audio_mix` |
| 8 | `video_compose` |
| 9 | `qa` |
| 10 | `manifest` |

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
- Text prep, story structure e audio planning sono stati separati in pass LLM dedicati per ridurre gli errori di coreference senza usare chunking codice.
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
