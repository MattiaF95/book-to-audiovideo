<h1 align="center">Book to Audiovideo</h1>

<p align="center">
  <img src="src/assets/img/text-to-audiovideo-copertina.png" alt="Book to Audiovideo copertina" width="1200">
</p>

Questo è un **flusso di agenti AI (agentic workflow)** il cui compito finale è trasformare del semplice **testo di narrativa** (perchè contiene sia dialogo che narrazione) in un contenuto **audio-video** con voci per ogni personaggio/narratore ed un video (al momento casuale ma inerente al contesto) come sfondo.

Ogni agente segue lo stesso pattern:

- riceve un oggetto di contesto chiamato PipelineContext
- legge o aggiorna lo stato della pipeline
- se serve, chiama un provider esterno (LLM, TTS, media, ffmpeg)
- salva un JSON di output nella cartella artefatti (data/output/jobs-id)

Quindi **ogni agente è un piccolo step della pipeline**.

## 🔥 Motivazioni progetto

L'idea del progetto è nata da alcuni primi test con **LLM-TTS** (modelli AI addestrati per text-to-speech). Mi sono chiesto: perchè non ideare un workflow agentico (in alcuni casi anche solo codice python) che prendono un testo con narratore e vari personaggi, lo spacchettano, definiscono i ruoli con genere e voce, li assegnano e restituiscono un audio narrato con tanto di video come sfondo?

**<h3>Tempi di realizzazione (comprensivi di test per raffinare la pipeline ed i prompt): 2/3 giorni</h3>**

E' stata un'idea per smanettare un po' con i vari modelli AI (ad esempio **llama-3** e **qwen3**) e capire che a volte tutto dipende da divisione compiti, orchestrazione e *prompt brevi ma mirati*. 

All'inizio avevo strutturato pochi agenti nel codice rispetto a quello attuale, quindi il modello AI non dava risultati ottimali perchè doveva svolgere troppi compiti. Fino ad arrivare al modello attuale dove addirittura ho deciso di togliere la segmentazione del testo all'agente AI e di farlo manualmente con codice python (usando « » per dividere il testo in modo deterministico). Questo perchè, anche provando LLM diversi non riuscivano mai a segmentare bene il testo, unendo dialogo e narrazione in alcuni punti.
Nel progetto ho inserito anche alcuni **AGENTS.md** per dare contesto, ruolo e descrizione per chi usa **CODEX**, ma sono usabili anche da altri agenti con opportune modifiche.

Pipeline locale MVP-first per trasformare un libro in un video narrato usando solo provider API esterni: Groq via API OpenAI-compatible per analisi testo, ElevenLabs per TTS, Pixabay per video e FFmpeg per il compositing finale.

| Componente | Scelta | Installazione
|---|---|---|
| 🧠 Agenti AI | `qwen/qwen3.6-27b` via Groq API (provider per usare LLM anche gratuitamente) OpenAI-compatible | Per creare la propria API KEY andare qui https://console.groq.com/keys (serve registrarsi prima) |
| 🔊 LLM-TTS | `eleven_v3` di ElevenLabs tramite API KEY | Per creare la propria API KEY andare qui https://elevenlabs.io/app/api/api-keys (serve registrarsi prima) |
| 🎬 Media | Pixabay (sito web che fornisce audio/video/img senza copyright)| Qui troverete la vostra API KEY gratuita per fare le query https://pixabay.com/api/docs/ (serve registrarsi prima) |
| 🎞️ Compositing | FFmpeg | FFmpeg non è una dipendenza Python e quindi non viene gestito dal venv: deve essere installato a livello di sistema |

---

## 🎬 Installazione FFmpeg

Verifica se FFmpeg è già installato:

```bash
ffmpeg -version
ffprobe -version
```

Se manca, installalo con uno dei comandi seguenti:

- Linux (Debian/Ubuntu):
  ```bash
  sudo apt update && sudo apt install -y ffmpeg
  ```

- Linux (Fedora):
  ```bash
  sudo dnf install -y ffmpeg
  ```

- Linux (Arch):
  ```bash
  sudo pacman -S ffmpeg
  ```

- Windows (winget):
  ```powershell
  winget install Gyan.dev.FFmpeg
  ```

- Windows (Chocolatey):
  ```powershell
  choco install ffmpeg
  ```

In alternativa puoi scaricarlo manualmente da qui https://www.ffmpeg.org/download.html.

---

## 🧱 Architettura
### 📂 Struttura cartelle
| Cartella | Contenuto |
|---|---|
| `src/book_to_audiovideo/agents/` | Gli agent che eseguono i singoli step della pipeline |
| `src/book_to_audiovideo/prompts/` | I prompt usati dagli agent per le richieste AI |
| `src/book_to_audiovideo/providers/` | I connettori verso Groq, ElevenLabs e Pixabay |
| `src/book_to_audiovideo/services/` | Funzioni helper per file, media, FFmpeg e durata |
| `src/book_to_audiovideo/web/` | La dashboard locale per avviare, monitorare e controllare i job |

### 📄 File strutturali
| File | Ruolo | Cosa fa |
|---|---|---|
| `src/book_to_audiovideo/pipeline/orchestrator.py` | Il cuore che avvia la pipeline, gestisce lo stato e i job | <ul><li>costruisce la lista degli agenti</li><li>li esegue in sequenza</li><li>aggiorna lo stato del job</li><li>salva gli eventi</li><li>gestisce errori, pause, approval e completamento</li></ul> |
| `src/book_to_audiovideo/agents/base.py` | E' la classe BaseAgent che definisce il comportamento comune che tutti gli agenti devono avere | <ul><li>riceve il contesto della pipeline</li><li>imposta lo stage corrente</li><li>chiama il metodo esecutivo specifico di ogni agente</li><li>scrive il manifest dello stage</li></ul> |

---

## 🤖 Pipeline / AI Agent

| Step | AI Agent | Usa LLM | Ruolo |
|---|---|---|---|
| 1 | 📥 ingestion_agent.py | No | <ul><li>Legge il file sorgente e carica il testo grezzo nello stato della pipeline.</li><li>È il primo step del flusso e prepara l’input per gli agent successivi.</li></ul> |
| 2 | ✨ text_cleanup_agent.py | Sì | <ul><li>Pulisce il testo grezzo e prepara una versione più ordinata per l’analisi.</li><li>Registra correzioni e warning quando il testo va normalizzato.</li></ul> |
| 3 | 🧭 narrative_context_agent.py | Sì | <ul><li>Genera il contesto narrativo globale del testo.</li><li>Estrae informazioni come scena, tono e ambientazione.</li></ul> |
| 4 | ✂️ dialogue_segmentation_agent.py | **No** | <ul><li>Divide il testo in segmenti di narrazione e dialogo.</li><li>Usa i delimitatori « » per creare confini deterministici.</li><li>Non richiede chiamate LLM.</li></ul> |
| 5 | 👥 speaker_registry_agent.py | Sì | <ul><li>Identifica narratore e personaggi.</li><li>Costruisce il registro dei speaker con identificativi stabili.</li></ul> |
| 6 | 🗣️ speaker_attribution_agent.py | Sì | <ul><li>Assegna ogni segmento a un speaker.</li><li>Se un dialogo non è chiaro, lascia il valore vuoto e segnala un warning.</li><li>Garantisce che la narrazione venga attribuita al narratore.</li></ul> |
| 7 | 🏷️ narrative_annotation_agent.py | Sì | <ul><li>Aggiunge suggerimenti emotivi a ogni segmento.</li><li>Calcola un punteggio di importanza per priorizzare i momenti più rilevanti.</li></ul> |
| 8 | 🎙️ voice_casting_agent.py | Sì | <ul><li>Sceglie la voce più adatta per ogni speaker.</li><li>Considera ruolo, genere e preferenze vocali.</li></ul> |
| 9 | 🔤 pronunciation_planning_agent.py | Sì | <ul><li>Prepara indicazioni su come pronunciare parole difficili.</li><li>Aiuta il TTS a rendere il parlato più naturale.</li></ul> |
| 10 | 🎚️ prosody_planning_agent.py | Sì | <ul><li>Aggiunge tag di intonazione.</li><li>Fa sì che il parlato abbia ritmo, enfasi e naturalezza.</li></ul> |
| 11 | 🎞️ media_planning_agent.py | Sì | <ul><li>Definisce keyword video, mood, scena e intensità per ogni segmento.</li><li>Serve a scegliere i media più adatti al contenuto.</li></ul> |
| 12 | 🎥 media_fetch_agent.py | No | <ul><li>Cerca e scarica i video di sfondo da Pixabay.</li><li>Prova più query fino a trovare un risultato utilizzabile.</li></ul> |
| 13 | 🔊 tts_agent.py | No | <ul><li>Genera l’audio sintetizzato per ogni segmento.</li><li>Usa la voce assegnata e il contesto prosodico del segmento.</li></ul> |
| 14 | 🎚️ audio_mix_agent.py | No | <ul><li>Mescola la voce TTS con eventuali effetti sonori (logica esistente ma media_fetch fornisce solo tracce video) o tracce secondarie.</li><li>Normalizza i livelli audio per il risultato finale.</li></ul> |
| 15 | 🎬 video_compose_agent.py | No | <ul><li>Compone il video finale unendo audio e media visivi.</li><li>Produce il file MP4 finale della pipeline.</li></ul> |
| 16 | 🧪 qa_agent.py | No | <ul><li>QA (Quality Assurance)</li><li>Controlla durata e loudness del video finale.</li><li>Segnala warning se il risultato non rientra nei parametri attesi.</li></ul> |
| 17 | 📦 manifest_agent.py | No | <ul><li>Scrive il manifest finale con lo stato completo del job.</li><li>Racchiude i risultati di tutte le fasi eseguite.</li></ul> |


> **Step 4 — dialogue_segmentation_agent.py - nessuna chiamata LLM.** La segmentazione dialogo/narrazione è deterministica perchè garantisce confini esatti tra dialogo e narrazione senza possibilità di errori (perlomeno con testi semplici). Scelta fatta dopo svariati fallimenti da parte dei modelli. Questo repo rimane comunque un prototipo senza finalità di produzione.

> `dialogue_segmentation_agent` non usa prompt LLM — la segmentazione è interamente in codice per il problema appena descritto. Il prompt è stato comunque lasciato come documentazione e/o futuro reintegro.

> In una fase iniziale sono stati provati modelli diversi, tra cui llama-3.1-8b-instant, llama-3.3-70b-versatile e qwen/qwen3.6-27b, ma la separazione dialogo/narrazione risultava troppo instabile.

> **Step 6 — fallback sicuro.** La narrazione viene sempre assegnata al narratore. I dialoghi non attribuibili (nessun verbo di dire adiacente, alternanza ambigua) ricevono `resolved_speaker_id: null` e generano un `warning` nello state invece di essere silenziosamente assegnati al narratore.

> **Step 14 - mancanza effetti sonori.** All'inizio era previsto recuperare anche effetti sonori da Pixabay e quindi era stata inclusa la logica in audio_mix_agent, ma in fase di test mi sono accorto che Pixabay ha query solo per contenuti video. Logica lasciata perchè non produce regressioni o bug.

---

## 🖥️ Dashboard locale

La dashboard permette di:

- caricare il file sorgente.
- vedere lo stato di ogni agent e gli eventi del job.
- avere una cronologia in locale dei test effettuati (creata in data/output/)
- approvare o rifiutare stop manuali `needs_attention`.
- aprire il video finale generato. 🎬
- visualizzare una mappa compatta e leggibile della pipeline, anche per gli stage delle pipeline storiche.
- azzerare la sola visualizzazione corrente con `Reset`, senza cancellare gli artefatti locali.
- aprire con `Dettagli` il JSON prodotto dal singolo agente; il sistema cerca sia i file numerati sia i manifest.

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
python -m book_to_audiovideo.main run data/input/file-da-analizzare
```
Nella directory **data/input/** trovate già alcuni file da testare in vari formati.
File accettati in ingresso **txt**, **md**, **pdf**, **docx**.

---

## 🔐 Variabili ambiente (.env.example)

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

## 📁 Artefatti output

Ogni job crea `data/output/<job_id>/` con:

| Cartella/File | Contenuto |
|---|---|
| `state.json` | Stato completo del job |
| `0N_<stage>.json` | Output JSON di ogni fase, nell'ordine di esecuzione |
| `source/` | File sorgente e normalizzazioni |
| `media/video/` | Video selezionati da Pixabay |
| `tts/` | File audio generati da ElevenLabs |
| `mix/` | Mix audio voce per segmento |
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
- La segmentazione dialogo/narrazione è deterministica (regex su `« »`) e non consuma token Groq.
- Il narratore è uno speaker unico e stabile per tutto il progetto.
- Ogni speaker ricorrente mantiene `speaker_id` e `continuity_anchor` stabili, riusati da ElevenLabs per la continuità vocale tra segmenti.
- ElevenLabs seleziona una voce tra quelle disponibili nel catalogo globale/shared e, se la voce scelta non è ancora presente nell’account, la aggiunge automaticamente tramite API prima di usarla per la sintesi vocale. In pratica: il progetto non si limita a scegliere una voce “a caso”, ma prova a usare una voce compatibile con lo speaker, poi la rende disponibile nel proprio account per continuare il lavoro.
- ElevenLabs request stitching serve a dare continuità al parlato tra segmenti consecutivi: invece di trattare ogni frase come un blocco isolato, il client invia `previous_request_ids` e `previous_history_item_ids` ai modelli che lo supportano, così la sintesi può mantenere un tono più naturale e coerente.
- Il contesto di stitching mantiene una coda fissa di massimo 3 elementi (`request_id` + `history_item_id`) per evitare che la storia cresca oltre la finestra utile.
- Il QA (Quality Assurance) finale è una verifica di qualità finale, non un blocco hard-stop: controlla soprattutto il risultato audio/video e, se ad esempio loudness o durata non rientrano nei valori attesi, registra un `warning` senza fermare il job. In pratica è un controllo di sanità del prodotto finale, non una validazione “secca” di successo/insuccesso.

---

## 📌 Limiti MVP (Minimum Viable Product)

| Limite | Dettaglio |
|---|---|
| Test | Offline e mock, non API reali |
| Delimitatori dialogo | Solo `« »` supportati; testi con `—` o `"` usano il prompt di fallback |
| Pixabay | Solo ricerca video; scaricato nella variante `medium` quando disponibile. Nel codice è presente anche logica per gli effetti audio ma questo provider (nonostante abbia nel suo catalogo anche contenuti audio) fornisce solo video tramite le query |
| Voce | La scelta dipende dalle voci disponibili nel tuo account ElevenLabs |
| Dashboard | Solo upload, monitoraggio, approve/reject e apertura output finale |

---

## ➡️ Implementazioni future

- Possibilità di dare un prompt direttamente in dashboard se l'agent ai si blocca per qualche motivo, cosi da non bloccare la pipeline e correggere al momento.
- Si può aggiungere un servizio che oltre il video aggiunge anche degli effetti sonori in base a cosa succede nel racconto.
- Avere direttamente in dashboard lo storico di ogni pipeline più dettagliato, senza andare a leggere i json nel codice.
- Deployare l'app cosi da poterla usare ovunque.
- Inserire validazione amdin/user per avere più controllo su chi la utilizza.

---

## ⭐ Autore

[MattiaF95](https://github.com/MattiaF95)
