# Opportunity Finder

> Stop scrolling for opportunities. A pipeline that keeps watching the places where opportunities are posted, throws away the noise, and delivers the ones you can actually apply to, ranked by fit, before they are gone.

**Status:** Working proof of concept with a FastAPI backend, React frontend, SQLite persistence, ChromaDB retrieval, LLM-powered extraction and candidate matching, and a locally scheduled Prefect pipeline.
**Author:** Irene, built step by step as a hands-on project for an LLM engineering course.

---

## 1. Problem

Many opportunities (jobs, internships, fellowships) are announced as **feed posts**, especially on LinkedIn, rather than on the jobs page. Someone who is job hunting ends up scrolling the feed for hours, wading through posts that are not opportunities, and still:

- **misses** opportunities that scrolled past unnoticed,
- finds others **too late**, after the application window has closed,
- reads a whole post only to learn that it is for a seniority level or location that does not fit.

Why this is hard to automate:

1. **Mostly noise.** Most posts in a feed are not opportunities at all.
2. **No structure.** Every post is written differently, so there are no searchable fields (role, location, deadline).
3. **Buried requirements.** Seniority, location rules and visa wording are scattered through free text: *Remote (US only)*, *Senior*, *We can't sponsor visas*. Reading them post by post is slow.
4. **Timing.** Value is lost when a post is found late, so collection has to be continuous, not occasional.

## 2. Solution

A pipeline that **runs on a schedule**, so you don't have to go looking:

1. **Collect:** on a schedule, pull new posts from the sources where opportunities appear.
2. **Detect:** discard everything that is not an opportunity.
3. **Extract:** turn each opportunity into structured fields (role, company, location, remote rules, visa, salary, deadline, how to apply).
4. **Apply preferences (optional):** if the user set any hard preferences (e.g. only remote, no onsite), filter on them. Off by default.
5. **Rank:** how well does it fit the user's CV?
6. **Deliver:** send a short digest of new, ranked opportunities, each with a one-line reason it fits and what is missing.

## 3. What the final product is

A system that:
1. Collects job and internship opportunities from Hacker News.
2. Identifies posts that contain genuine opportunities.
3. Extracts structured information about each opportunity.
4. Stores opportunities and makes them searchable.
5. Allows users to upload their resumes.
6. Uses an AI agent to find and recommend opportunities based on the user's qualifications and preferences.
7. Uses RAG to retrieve relevant information from the original opportunity posts.
8. Helps users shortlist opportunities and check their application status.

| Source | Role |
|---|---|
| Hacker News "Who is hiring?" | PoC stand-in for a feed: public, free API, a new thread every month |
| Later: job-alert emails, public Telegram channels, RSS (e.g. ReliefWeb), company career pages | Permitted, automatable sources for the real product |
| LinkedIn feed | **Open problem.** LinkedIn offers no sanctioned way to read the feed automatically, and scraping it risks account bans and breaks its Terms of Service. The design leaves a slot for it (see Limitations) but does not depend on it. |

A "share a post to the tool" option can exist as a small fallback adapter for posts that no automatic source reaches, but it is not the product.

## 4. What the real data looks like

First look at 5 real posts from *Ask HN: Who is hiring? (October 2026)*. This is a small sample, so treat these as hypotheses to confirm on 50+ posts.

| Observation | Example in the data | Design consequence |
|---|---|---|
| Header formats are inconsistent | `Shepherd (Series B) \| ONSITE \| San Francisco...` vs `PrairieLearn (Remote US) — Full-Stack Software Engineer — ...` | Rules and regexes are not enough. Use an LLM extractor. |
| **One post, several roles** | Shepherd lists 4 role types across 2 cities; Sidekick lists 3; Neon lists 4 | Schema is *company-level fields + a list of roles*, not one flat record. |
| **Remote has a scope** | `Remote (US only)`, `REMOTE (Germany)`, `REMOTE (US Timezones)` | Extract `remote_scope` as written, so the digest can show it. |
| Visa and residency rules are in free text | "We're not able to sponsor visas", "You must be based in Germany", "no visa sponsorship" | Extract `visa_sponsorship` (often "unclear": only ~5% of posts mention visas). |
| Language requirements | A Dutch post that says Dutch is *strictly required*; a German post requiring business-fluent German | Extract `language_required`; detect post language. |
| Salary is sometimes there, in different currencies | `$100k-$180k`, `€75k–80k`, `$170k to $230k Base + Equity` | Store min, max, currency as optional fields. |
| Apply instructions vary | Web form, email with a subject-line rule, "mention you heard via HN" | Extract `apply_method` and `apply_target`. |
| Fields that are often absent | Deadline appears in none of the five | Every field must be allowed to be `null`. The extractor must never invent values. |
| Not every post is English | One post switches to Dutch mid-text | The pipeline cannot assume English. |

Replies are mostly empty (`n_replies` is 0 on 4 of 5), so top-level comments are clean job posts and we ignore replies.

## 5. Extraction schema (v0, will change after labeling)

```
Post
├── is_opportunity: bool
├── post_language: str
├── company: str
├── company_stage: str | null          (e.g. "Series B", "bootstrapped")
├── remote_policy: remote | hybrid | onsite | unclear
├── remote_scope: str | null           (e.g. "US only", "Germany")
├── visa_sponsorship: yes | no | unclear
├── language_required: list[str]
├── apply_method: url | email | other
├── apply_target: str
├── deadline: date | null
└── roles: list[Role]
      ├── title: str
      ├── seniority: str | null
      ├── location: str | null
      ├── employment_type: str | null
      ├── salary_min / salary_max / currency: optional
      └── skills: list[str]
```

This is a starting point. After hand-labeling 50 posts we will see which fields are reliably present and which are noise, and trim or add fields.

## 6. Architecture

```
 [Prefect scheduler]  runs the pipeline every six hours
        ▼
 [Source adapters]  HN today; email / Telegram / RSS later
        ▼
  clean + de-duplicate (skip posts already seen)  ──► raw posts (JSONL)
        ▼
  [Classifier]  is it an opportunity?            (noise is dropped here)
        ▼
  [LLM extractor]  post ──► structured JSON      (schema above, validated)
        ▼
  structured opportunities  ──►  [Embed] ──► Chroma
                                              ▲
  User profile: CV + constraints ──► embed ───┤
        ▼                                     │
  [Preference filter]  optional hard rules (remote only, language, ...), off by default
        ▼
  [Semantic ranking]  nearest opportunities to the CV
        ▼
  [RAG explanation]  LLM sees CV chunks + the post ──► "fits because..., missing..."
        ▼
  [Delivery]  FastAPI endpoints + React dashboard
```

Design decisions worth noting:

- **Only new posts move forward.** The store remembers every post ID it has seen, so each run delivers only what is new. This is what prevents "found it too late" and repeated alerts.
- **Hard rules are not similarity scores.** If a user sets a hard preference (say, remote only), it is applied as a filter before ranking, never as part of the similarity score. Seniority is different: it is a strong signal for ranking, since most posts are for senior roles.
- **Evaluation is built in, not added at the end.** Every stage is measured against hand-labeled data.

## 7. Tools and where each course topic is used

| Course topic | Where it is used |
|---|---|
| **Tokenizers / AutoTokenizer** | Measure post length in tokens; check posts fit the model's context; choose chunk sizes for the CV; understand why long multi-role posts cost more. |
| **Hugging Face pipelines** | A zero-shot or fine-tuned classifier for "is this an opportunity?", and a baseline to compare against the LLM approach. |
| **LangChain** | Structured-output extraction chain (prompt, model, validated schema); the CV-to-opportunity explanation chain. |
| **Tools** | Small helper tools the LLM can call, e.g. a salary-currency normalizer or a link checker. |
| **Embeddings + Chroma (RAG)** | Index opportunities and the CV; retrieve the best matches and the relevant CV passages for the explanation. |
| **React + Vite** | The web dashboard: onboard candidates, browse opportunities, manage profiles, search, and view personalized matches. |
| **FastAPI** | HTTP API consumed by the React frontend for onboarding, profile management, opportunity browsing, search, and matching. |
| **Prefect** | Orchestrates and schedules the collection, extraction, indexing, and cleanup pipeline locally. |
| **SQLite + ChromaDB** | SQLite stores candidate and opportunity records; ChromaDB supports semantic retrieval. |

## 8. Data plan

| Source | Used for | Why |
|---|---|---|
| **Hacker News "Who is hiring?" threads** | Main source: building and measuring the extractor | Public, free API, real messy text, one post = one opportunity |
| **Bluesky posts** | Negative examples for the classifier ("not an opportunity") | Real social-media text that is not job-related |
| **Synthetic LinkedIn-style posts** | Testing robustness to feed-style writing | Generated from Kaggle LinkedIn job rows where the true fields are known |
| **30–50 posts copied by hand from my own feed** | Final honest test | The real target format; kept out of all tuning |

Hacker News API (no key needed):
- Find threads: `https://hn.algolia.com/api/v1/search_by_date?tags=story,author_whoishiring`
- Get a whole thread: `https://hn.algolia.com/api/v1/items/<story_id>`

## 9. Step-by-step plan

Each step has one thing to build and one thing to learn. We finish and check a step before the next.

| Step | Build | Learn / check |
|---|---|---|
| **1. Look at the data** (done on 5 posts) | `hn_fetch.py`: fetch a thread, clean, save JSONL | HTML cleaning; reading real data before designing |
| **2. Collect** | Fetch ~6 monthly threads; basic stats | Dataset sizes; token counts with a tokenizer |
| **3. Label** | Hand-label 50 posts against the schema | Where the schema breaks; what "ground truth" costs |
| **4. Extract** | LangChain extractor with a validated schema; score it field by field | Structured output; prompt iteration; measuring instead of eyeballing |
| **5. Match** | Embed CV and extracted summaries into Chroma; optional preference filter; ranked list | Embeddings, retrieval, hard filters vs similarity |
| **6. Explain** | RAG explanation of fit and gaps | Retrieval-augmented generation |
| **7. Automate** | Scheduled run: fetch new posts, skip ones already seen, run the pipeline, write a digest | Idempotent pipelines; "only what's new" |
| **8. Deliver** | FastAPI API + React dashboard for onboarding, browsing, search, and personalized recommendations | Delivery; interfaces |
| **9. Classifier** | "Is this an opportunity?" with HN positives and Bluesky negatives, placed before the extractor | HF pipelines; class imbalance |
| **10. Harder tests** | Synthetic LinkedIn-style posts, then my hand-collected feed posts | Generalization: how much drops when the format changes |
| **11. More sources** | A second adapter (e.g. Telegram channel or RSS) | Whether the pipeline really is source-agnostic |

## 10. How success is measured

- **Extraction:** per-field accuracy against hand labels. Report each field separately (company and apply link will score high; seniority and remote scope will not), plus how often the model invents a value that is not in the post.
- **Seniority and scope fields:** accuracy on `seniority`, `remote_policy` and `remote_scope`, since a wrong value sends the user to a role that does not fit.
- **Ranking:** for a handful of real queries, do the top 10 results look right to me?
- **Classifier:** precision and recall on a mix of HN positives and Bluesky negatives, then re-tested on hand-collected feed posts.
- **Generalization gap:** the score on HN versus the score on feed-style posts. This is the honest answer to "does it work on LinkedIn-style text?"

## 11. Limitations and ethics

- HN posts are a cleaner and more tech-focused format than LinkedIn posts. Results on HN will overestimate real-world performance, which is why the hand-collected test set exists.
- **LinkedIn is the original motivation but the hardest source.** It has no sanctioned way to read the feed automatically, and scraping it risks account bans and Terms-of-Service violations. The PoC proves the hard parts (detect, extract, filter, rank, deliver) on Hacker News. Getting LinkedIn posts in is a separate decision for later, through a permitted route.
- The PoC therefore does not yet solve "LinkedIn posts reach me automatically". It shows that, once posts arrive, the rest works.
- The PoC covers mostly tech roles. Other fields (grants, fellowships) need their own labeled examples.
- The extractor must return `null` rather than guess.

## 12. Repository layout

The project is organized around the API, domain services, agents, persistence, and pipeline orchestration. The frontend is a separate React application.

```text
opportunity-finder/
├── agents/                 # LLM agents for extraction and candidate matching
├── database/               # SQLite database setup and persistence
├── data/                   # Local raw posts and generated application data
├── frontend/               # React + Vite application
│   ├── src/
│   ├── .env.example
│   └── package.json
├── models/                 # Pydantic/domain models
├── orchestration/          # Prefect pipeline and scheduled flow
├── services/               # Collection, extraction, retrieval, embeddings, etc.
├── api.py                  # FastAPI application
├── requirements.txt        # Python dependencies
├── .env.example            # Backend environment variable template
└── README.md
```

## 13. Run locally

This section describes how to run the complete application locally: the Prefect orchestration server, scheduled opportunity pipeline, FastAPI backend, and React frontend.

### Prerequisites

- Python version supported by the project dependencies
- [`uv`](https://docs.astral.sh/uv/) for Python environment and dependency management
- Node.js and npm for the React frontend
- An API key for the LLM provider used by the extraction and matching agents

Run the commands below from the repository root unless a command says otherwise.

### 1. Set up the Python environment

Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate
```

Install the Python dependencies:

```bash
uv pip install -r requirements.txt
```

If you already use an active virtual environment for this project, you can keep using it; the `uv run --active` commands below run inside that active environment.

### 2. Configure backend environment variables

Create your local environment file from the template:

```bash
cp .env.example .env
```

Open `.env` and provide the required values, especially the LLM provider API key. Use the variable names in `.env.example` as the source of truth; do not commit `.env` or put secrets in the frontend environment file.

### 3. Set up the React frontend

In a separate terminal, from the repository root:

```bash
cd frontend
cp .env.example .env
npm install
```

The frontend `.env` should point to the local API:

```env
VITE_API_URL=http://localhost:8000
```

Start the development server:

```bash
npm run dev
```

Open the frontend at `http://localhost:5173`.

### 4. Start the local Prefect server

Open another terminal at the repository root and start the Prefect server:

```bash
uv run --active prefect server start
```

The Prefect UI is available at `http://127.0.0.1:4200`.

In another terminal, configure the local Prefect API URL:

```bash
uv run --active prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api
```

This points the pipeline to the local Prefect server. You only need to configure this setting once for the environment unless you change the Prefect server address.

### 5. Run the opportunity pipeline

To execute the pipeline once:

```bash
uv run --active python -m orchestration.opportunity_pipeline
```

To serve the scheduled flow locally:

```bash
uv run --active python -m orchestration.opportunity_pipeline --serve
```

The current schedule is every six hours (00:00, 06:00, 12:00, and 18:00, using the machine's local timezone; configure your machine to Kigali time if you want the schedule to follow Kigali time). Keep the serving process running for scheduled executions to occur. The Prefect server must also remain running.

### 6. Start the FastAPI backend

Open another terminal at the repository root:

```bash
uv run --active uvicorn api:app --reload
```

The API is available at `http://localhost:8000`.

Useful URLs:

- Health check: `http://localhost:8000/api/health`
- Interactive API documentation: `http://localhost:8000/docs`

### 7. Run the full application

For the complete local setup, keep these processes running in separate terminals:

| Terminal | Command / process | Local address |
|---|---|---|
| 1 | `uv run --active prefect server start` | Prefect UI: `http://127.0.0.1:4200` |
| 2 | `uv run --active python -m orchestration.opportunity_pipeline --serve` | Scheduled pipeline process |
| 3 | `uv run --active uvicorn api:app --reload` | API: `http://localhost:8000` |
| 4 | `cd frontend && npm run dev` | Web app: `http://localhost:5173` |

The frontend calls the FastAPI backend. The Prefect serving process runs the collection and processing flow on its schedule; it is separate from the API server. You can also trigger a one-time pipeline run with the command in Step 5.

### Local data and generated files

The application creates or updates local persistence and vector-store data as it runs. These files are runtime data, not source code. Keep your `.env`, SQLite database, raw collected posts, and ChromaDB data out of version control. The `.gitignore` file should exclude local secrets, generated data, caches, and virtual environments.

### Troubleshooting

- **Frontend cannot reach the API:** confirm FastAPI is running on port `8000` and `frontend/.env` contains `VITE_API_URL=http://localhost:8000`. Restart Vite after changing `.env`.
- **Backend cannot call the LLM provider:** check that the required API key and other backend settings are present in the root `.env` file.
- **Pipeline does not run on schedule:** confirm both the Prefect server and the `--serve` process are still running, and that `PREFECT_API_URL` points to `http://127.0.0.1:4200/api`.
- **Port already in use:** stop the process already using the port or configure the service to use another port, then update the corresponding frontend/API setting.


## 14. Upcoming workflow

> **Status: Planned — not started.** The phases below describe the next stages of development. They are included as the intended workflow, not as features that are already implemented.

The next stages will build on the working proof of concept in a deliberate order: first improve the quality and trustworthiness of recommendations, then add job-search workspace features, strengthen the engineering foundations, and finally expand the product.

### Phase 1 — Product quality

**Goal:** Make sure the recommendations are trustworthy and useful.

1. **Matching explanations:** Show users why an opportunity is confirmed or potential, including matching skills, missing qualifications, and possible concerns.
2. **Matching evaluation:** Build a small manually reviewed dataset to measure whether the top recommendations are actually relevant.
3. **Duplicate detection:** Ensure the same opportunity is not presented multiple times, even if collected from different posts.
4. **Opportunity freshness:** Make expired opportunities clearly identifiable and prevent them from appearing as active recommendations.

### Phase 2 — User functionality

**Goal:** Turn the recommendation dashboard into a useful job-search workspace.

1. **Save opportunities:** Let users bookmark interesting roles.
2. **Application tracking:** Track saved, applied, interviewing, rejected, and offered opportunities.
3. **Match feedback:** Let users indicate whether a recommendation is relevant. Use this feedback to improve future matching.
4. **Profile refinement:** Allow users to update skills, experience, preferences, and resumes.

### Phase 3 — Engineering maturity

**Goal:** Make the system maintainable, observable, and scalable.

1. **Automated tests:** Add unit tests for extraction, retrieval, matching, and candidate services, along with integration tests for API endpoints.
2. **Observability:** Add structured logging, pipeline execution metrics, extraction-failure tracking, API error tracking, and latency monitoring.
3. **Data reliability:** Introduce database migrations, retry handling, idempotency, and recovery from failed pipeline runs.
4. **Security:** Add authentication and authorization, secure resume storage, upload validation, and protection of candidate information.

### Phase 4 — Expansion

**Goal:** Increase the value and reach of the product.

1. **More sources:** Add RSS feeds, company career pages, job-alert emails, and other permitted sources.
2. **Notifications:** Notify users by email or through other channels when relevant opportunities are discovered.
3. **Deployment:** Deploy the API, frontend, database, and scheduled pipeline.
4. **Multi-user support:** Support multiple candidates with isolated profiles, preferences, and application histories.

### Planned implementation order

The intended order is Phase 1 → Phase 2 → Phase 3 → Phase 4. This sequence prioritizes recommendation quality before adding more user-facing functionality, scaling the system, or expanding its sources.

These phases are a forward-looking plan. No work in this roadmap should be considered started or completed until it is implemented and verified.

---

## 15. Open decisions

- Which LLM to use for extraction (hosted API vs open-source via Hugging Face), decided at Step 4 by comparing both on the labeled set.
- Which embedding model to use for matching, decided at Step 5 with the tokenizer's length limits in mind.
- Final schema fields, decided after labeling at Step 3.

---

## 16. The Picture
## Architecture

```mermaid
flowchart TD
    HN["Hacker News<br/>(internet)"] --> fetch["<b>fetch.py</b><br/>get new posts, clean, skip ones already seen"]
    fetch --> raw[("data/raw.jsonl")]
    raw --> extract["<b>extract.py</b><br/>read each post, fill in the form"]
    schema["<b>schema.py</b><br/>the blank form"] -.-> extract
    extract --> extracted[("data/extracted.jsonl")]

    subgraph matchbox ["match.py"]
        direction TB
        elig["1. eligibility filter"] --> rank["2. rank by fit"]
        rank --> explain["3. explain fit and gaps (RAG)"]
    end

    profile["profile.yaml"] --> elig
    extracted --> elig
    chroma[("<b>Chroma</b> (data/chroma)<br/>opportunities + cv_chunks")]
    rank <--> chroma
    explain <--> chroma
    cv["data/cv.pdf"] --> chroma

    explain --> ranked["ranked list + reasons"]
    ranked --> daily["<b>run_daily.py</b><br/>builds the digest"]
    ranked --> app["<b>frontend/</b><br/>React dashboard"]

    labeled[("data/labeled.jsonl<br/>hand labels")] -.-> evaluate["<b>evaluate.py</b><br/>how often was the extractor right?"]
    extracted -.-> evaluate
```

`evaluate.py` sits to the side. It is not part of the daily run; it is used while building to check that changes improve extraction.

<details>
<summary>Plain-text version</summary>

```
        WHERE THINGS COME FROM                    WHAT YOU PROVIDE
        ──────────────────────                    ────────────────
        Hacker News (internet)                    cv.pdf   profile.yaml
                 │                                   │         │
                 ▼                                   │         │
   ┌──────────────────────┐                          │         │
   │ fetch.py             │                          │         │
   │ "go get new posts"   │                          │         │
   └──────────┬───────────┘                          │         │
              ▼                                      │         │
        data/raw.jsonl                               │         │
              │                                      │         │
              ▼                                      │         │
   ┌──────────────────────┐     uses the form        │         │
   │ extract.py           │◄──── schema.py           │         │
   │ "read each post,     │      (the blank form     │         │
   │  fill in the form"   │       to fill in)        │         │
   └──────────┬───────────┘                          │         │
              ▼                                      ▼         ▼
      data/extracted.jsonl ─────────────►  ┌──────────────────────┐
                                           │ match.py             │
                                           │ "can you apply? how  │
                                           │  well do you fit?"   │
                                           └──────────┬───────────┘
                                                      ▼
                                           ranked list + reasons
                                                      │
                          ┌───────────────────────────┴───────────┐
                          ▼                                       ▼
                ┌───────────────────┐                  ┌───────────────────┐
                │ run_daily.py      │                  │ app.py            │
                │ builds the digest │                  │ Gradio dashboard  │
                └───────────────────┘                  └───────────────────┘

   evaluate.py sits to the side: it compares extracted.jsonl with your
   hand-made labeled.jsonl and tells you how often the extractor was right.
```

</details>
