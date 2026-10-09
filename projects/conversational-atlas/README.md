# Conversation Atlas

## Product Concept

**Conversation Atlas is a source-linked conversation intelligence platform that transforms long-form conversations into a structured, searchable map of ideas, claims, positions, and emerging debates.**

The platform will begin with **African technology and business podcasts**, with every published insight traceable to the exact moment in the original audio from which it was derived.

The central premise is:

> **Podcasts contain a vast amount of valuable human knowledge, reasoning, and debate, but most of that knowledge remains difficult to search, compare, analyze, and reuse.**

Conversation Atlas transforms these conversations into structured knowledge while preserving the original source, context, and uncertainty.

The product is not primarily a podcast search engine, transcript database, or chatbot. Its differentiation lies in **what happens after retrieval**: understanding what people are saying, identifying where they agree or split on a defined proposition, explaining why, and eventually tracking how those conversations evolve over time.

---

# 1. The Problem

Long-form podcasts contain valuable discussions about technology, entrepreneurship, business, healthcare, finance, culture, and society. However, much of that information remains locked inside hours of audio.

Existing podcast tools make it possible to find episodes, transcripts, summaries, or individual moments. Conversation Atlas addresses a different question:

> **What can we learn when we analyze the ideas and positions expressed across many conversations rather than treating every episode as an isolated piece of content?**

For example, instead of simply answering:

> “Where did someone mention AI regulation?”

Conversation Atlas should eventually answer:

- What are people saying about AI adoption in African businesses?
- Where do speakers agree?
- Where do they split?
- Why do they take different positions?
- What arguments are emerging?
- Which ideas repeatedly appear across different conversations?
- How is the conversation around a topic changing over time?
- Which predictions have been made?
- Which positions appear to have changed?

The platform should always preserve the connection between an insight and its original source.

---

# 2. Initial Product Wedge

Conversation Atlas will not initially attempt to index the entire podcast ecosystem.

The first content and market wedge will be:

> **African technology and business podcasts.**

The first public experiment will focus on **one carefully defined topic or debate**, using approximately **10–15 episodes during validation** and expanding to **10–20 shows during the MVP**.

This focused approach allows the product to validate its core experience before investing in a much larger corpus.

---

# 3. Core Product Experience: The Conversation Map

The primary product experience is the **Conversation Map**.

A Conversation Map shows:

> **where people agree, where they split, and why.**

The user starts with a topic or debate.

For example:

> **African startups should build their own AI models.**

This sentence becomes a **Proposition**.

The system then identifies relevant claims from conversations and classifies each claim according to its stance toward that proposition:

```text
                    PROPOSITION

     "African startups should build
          their own AI models."

                    │
        ┌───────────┼───────────┐
        ▼           ▼           ▼

     SUPPORT       NEUTRAL      OPPOSE

       12             7            9
     claims         claims       claims
```

The map should then explain the major arguments behind each position.

For example:

```text
SUPPORT

• Local control over important infrastructure
• Sovereignty over data and models
• Development of local technical capability

OPPOSE

• Model development requires enormous capital
• Application-layer opportunities may be more practical
• Compute and talent constraints favor specialization
```

Every major claim links to its source.

The user should be able to move from:

> **Conversation Map → Claim → Speaker → Episode → Exact audio moment**

---

# 4. Core Intelligence Model

The central analytical unit is not simply a claim.

The system will model three related objects:

```text
Proposition
     │
     │ stance
     ▼
   Claim
     │
     │ sourced from
     ▼
 Conversation / Episode
```

### Proposition

A proposition defines the question or position around which a debate is being mapped.

Example:

```text
Proposition
─────────────────────────────
"AI will reduce entry-level
software engineering jobs."
```

### Claim

A claim is a meaningful statement extracted from a conversation.

Example:

```text
Claim
─────────────────────────────
"AI will significantly reduce
the number of junior developers
companies need."
```

### Stance

Each claim is linked to a proposition with one of three primary stances:

```text
SUPPORT
OPPOSE
NEUTRAL
```

The stance relationship becomes the core of the Conversation Map.

Pairwise Natural Language Inference (NLI) remains useful, but as a **supporting mechanism** for tasks such as:

- identifying near-duplicate claims
- detecting direct contradictions
- helping normalize related claims

It is not the primary representation of disagreement.

---

# 5. End-to-End Processing Architecture

The processing pipeline becomes:

```text
                         PODCAST RSS
                              │
                              ▼
                      Episode Ingestion
                              │
                              ▼
                         Transcription
                              │
                              ▼
                     Speaker Segmentation
                              │
                              ▼
                       Semantic Chunking
                              │
                    ┌─────────┴─────────┐
                    ▼                   ▼
               Embeddings            Metadata
                    │                   │
                    ▼                   ▼
                 Chroma             PostgreSQL
                    │                   │
                    └─────────┬─────────┘
                              ▼
                     Candidate Claim
                       Extraction
                              │
                              ▼
                     Claim Normalization
                              │
                              ▼
                       Claim Embeddings
                              │
                              ▼
                     Related Claim Search
                         via Chroma
                              │
                 ┌────────────┴────────────┐
                 ▼                         ▼
          Duplicate / Similarity       NLI Support
             Detection                 (when useful)
                 │                         │
                 └────────────┬────────────┘
                              ▼
                      Proposition Matching
                              │
                              ▼
                       Stance Classification
                              │
                    SUPPORT / OPPOSE / NEUTRAL
                              │
                              ▼
                         Human Review
                              │
                              ▼
                    Published Conversation Map
```

The architecture deliberately separates **extraction**, **retrieval**, **stance classification**, and **publication review**.

---

# 6. Claim and Proposition Representation

Claims should be treated as first-class objects rather than plain text.

### Claim

```text
Claim
├── claim_id
├── claim_text
├── speaker_id
├── episode_id
├── podcast_id
├── timestamp_start
├── timestamp_end
├── topic
├── claim_type
├── extraction_confidence
├── source_url
└── review_status
```

### Proposition

```text
Proposition
├── proposition_id
├── proposition_text
├── topic
├── created_at
└── review_status
```

### Stance relationship

```text
Claim
   │
   └── stance ──► Proposition

stance ∈ {
    SUPPORT,
    OPPOSE,
    NEUTRAL
}
```

This makes the analytical model explicit:

> **A disagreement is not simply two claims that contradict each other; it is a set of claims taking different positions toward a defined proposition.**

This representation also makes the Conversation Map much easier to explain to users.

---

# 7. Claim Extraction Evaluation

Because every downstream feature depends on extraction quality, **claim extraction must be evaluated independently**.

For an initial evaluation set, select **10 representative episodes**.

For each episode, manually identify the meaningful claims that should be extracted.

Then compare the manually identified claims against the system's extracted claims.

Measure:

- **Claim recall:** how many meaningful claims the system found.
- **Claim precision:** how many extracted claims correspond to real, meaningful claims.
- **Unsupported/invented claim rate:** how many claims the system introduced that are not actually supported by the conversation.

A simple evaluation structure is:

```text
10 Episodes
     ↓
Human-annotated claims
     ↓
System-extracted claims
     ↓
Match / Compare
     ↓
Precision
Recall
F1
Invented-claim rate
```

This evaluation should happen **before** relying on the extraction layer for public Conversation Maps.

---

# 8. Stance Detection Evaluation

Stance classification should be evaluated using **claim–proposition pairs**, not merely claim pairs.

Create a manually labeled evaluation set such as:

```text
200 claim–proposition pairs
```

Each pair receives one human label:

```text
SUPPORT
OPPOSE
NEUTRAL
```

The model's predictions can then be evaluated using:

- precision
- recall
- F1
- confusion matrix

This gives us a measurable foundation for the Conversation Map.

---

# 9. Human Review and Attribution

Because Conversation Atlas may publish statements attributed to real people, human review is a core safeguard during the early stages.

Every published claim should remain connected to:

- the original episode
- the source URL
- the timestamp
- transcript context
- speaker identity, where sufficiently verified

Attribution should have explicit states:

```text
VERIFIED
PROBABLE
UNKNOWN
```

Named attribution should not be publicly published solely because an AI model inferred it.

Anything that attributes a position to a real person should go through review during the early product stages.

---

# 10. Speaker Identity

Speaker diarization identifies separate speakers but does not, by itself, establish their names.

The speaker-resolution pipeline will therefore be treated as a distinct component:

```text
Audio
  ↓
Speaker Diarization
  ↓
Speaker 1 / Speaker 2 / Speaker 3
  ↓
Episode Metadata
  ↓
Guest / Host Candidates
  ↓
Identity Resolution
  ↓
Verified / Probable / Unknown
```

Speaker identity should be conservative.

When identity cannot be established reliably, the system should preserve the speaker segment without forcing a name.

---

# 11. Creator Experience

Podcast creators are both potential customers and an important distribution channel.

Conversation Atlas will provide **opt-in creator pages** framed as:

> **“Your archive, mapped and made discoverable.”**

The page may contain:

```text
Podcast
│
├── Episodes
├── Topics
├── Guests
├── Conversation Maps
├── Recurring ideas
└── Notable source moments
```

Creators should be able to:

- review their page before publication
- request corrections
- remove content
- opt out at any time

This makes creators participants in the product rather than passive content sources.

---

# 12. Creator Tools

Creator-facing tools will be developed progressively.

### Archive Revival

Identify older episodes that are relevant to conversations currently gaining attention.

Example:

> “AI regulation is being discussed widely this week. You covered the topic in Episode 42.”

### SEO Episode Pages

Create discoverable pages containing:

- transcripts
- chapters
- show notes
- important source moments

### Clip Studio

Suggest strong moments such as:

- sharp claims
- disagreements
- notable insights

Later versions can generate captioned vertical clips.

Multilingual caption support can eventually include:

- English
- French
- Swahili
- Kinyarwanda

### Coverage Gap Analysis

Identify important debates appearing across other shows that a creator has not covered.

### Guest Preparation Briefs

Summarize relevant topics a guest has previously discussed across available conversations.

### Debate Matchmaking

Suggest guests or other shows representing contrasting positions for potential crossover episodes.

### Sponsor Reports

Provide structured summaries of topics, recurring themes, and notable moments to support sponsorship discussions.

---

# 13. Public Distribution

Distribution should be part of the product rather than a separate marketing activity.

## Conversation Atlas Newsletter

The newsletter should not simply summarize podcasts.

It should surface **interesting developments in conversation**.

The initial format will focus on:

### Emerging Idea

What new idea is appearing across conversations?

### Disagreement

Where are speakers taking different positions?

### Surprising Connection

What unexpected connection exists between ideas, people, or topics?

### Source Moments

The strongest source-linked moments supporting the analysis.

Later, when sufficient longitudinal data exists, the newsletter can introduce:

- predictions
- changed minds
- topic evolution

---

# 14. Social Distribution

Conversation Atlas can automatically **draft** social posts from emerging conversations.

Publishing remains human-controlled.

For example:

> “Seven African technology podcasts discussed whether startups should build AI models or focus on applications. The disagreement wasn't simply about models—it was about where the continent's most valuable AI capability should sit.”

Social content should always follow the same source and attribution rules as the product.

No named claim about a real person should be published without review.

---

# 15. Email and WhatsApp Alerts

Users can eventually subscribe to topics rather than individual podcasts.

Examples:

```text
AI in healthcare
African fintech
AI adoption
Climate technology
Entrepreneurship
```

A topic alert may look like:

> **Conversation Atlas Alert**
>
> Three new conversations about AI in healthcare introduced different positions on clinical AI adoption.
>
> Explore the Conversation Map → [link]

Email is appropriate for weekly and deeper summaries.

WhatsApp can be used for shorter topic-based discovery and alerts.

SMS may later support high-value or concise notifications but will not be the primary distribution channel.

All messaging channels should be opt-in and support straightforward subscription management.

---

# 16. Business Model

Conversation Atlas will eventually serve three connected audiences through one underlying data engine.

## Public

Free access to:

- Conversation Maps
- topic exploration
- selected source moments
- newsletter
- topic alerts

## Podcast Creators

Freemium tools with paid capabilities such as:

- creator archive pages
- clip studio
- SEO episode pages
- archive revival
- sponsor reports
- advanced creator analytics

Creators are the first revenue test because the product directly improves the discoverability and utility of their existing archive while also creating a potential distribution relationship.

## Brands and Organizations

The first B2B direction will be:

> **brand and competitor mention monitoring across podcasts.**

This will be introduced only after the core conversation-analysis system is reliable.

---

# 17. MVP Scope

The MVP must remain realistic for a solo builder.

The core MVP will consist of:

```text
1 defined topic / proposition
        +
10–20 African technology and business shows
        +
Transcription
        +
Speaker segmentation
        +
Semantic chunking
        +
Multilingual embeddings
        +
Chroma retrieval
        +
Claim extraction
        +
Stance classification
        +
Conversation Map
        +
Source-linked claims
        +
Opt-in creator pages
        +
Human review
```

**Clip suggestions and the newsletter will be added toward the end of Phase 1**, after the core Conversation Map and creator experience are working.

---

# 18. Technology Direction

The initial implementation should remain a **modular monolith**.

### Core technologies

- Python
- Hugging Face Transformers and pipelines
- Whisper for transcription
- **BGE-M3 or multilingual-E5** for multilingual embeddings
- Chroma for semantic retrieval
- PostgreSQL for structured metadata and relationships
- LangChain where it simplifies retrieval and orchestration
- LLM APIs/models for claim extraction and normalization
- Gradio for early experimentation
- A conventional web application for the public product

The initial embedding model should be multilingual from the beginning so that later expansion into **French, Swahili, Kinyarwanda, and code-switched conversations** does not require rebuilding the entire embedding corpus.

Microservices and event-driven infrastructure can be introduced later when independent scaling or deployment requirements justify them.

---

# 19. Consent, Permissions, and Content Handling

Conversation Atlas will begin by indexing publicly available podcast metadata and feeds, while linking users back to the original publisher.

The initial operating principles are:

- Use public RSS feeds and publicly available metadata.
- Link back to the original podcast and episode.
- Preserve attribution to the original publisher.
- Make creator pages opt-in.
- Provide an accessible takedown process.
- Preserve original audio/source links rather than presenting Conversation Atlas as the owner of the underlying content.
- Obtain creator participation and feedback early.
- Seek appropriate legal advice before commercial launch, particularly regarding podcast audio, transcripts, excerpts, indexing, and redistribution.

The product should be designed around **discovery and source-linked analysis**, not unauthorized republishing of entire audio archives.

---

# 20. Demand Validation

## Phase 0 — Demand Test
**Weeks 1–3**

Select:

- one topic
- one proposition
- 10–15 episodes

Verify the relevant RSS feeds and create a semi-manual Conversation Map.

Show the result to:

- five podcast creators
- five target users

### Phase 0 success criteria

Move to MVP only if:

- at least **3 of 5 creators** express interest in having their show represented through an opt-in creator page; and
- at least **3 of 5 target users** say they would share or send the Conversation Map to someone else.

The goal is not merely positive feedback.

The goal is evidence that the product creates something people find worth **sharing and participating in**.

---

# 21. Phase 1 — MVP
**Approximately Months 1–4**

Build the core ingestion, extraction, retrieval, stance, review, and Conversation Map experience.

The first milestone is:

> **A reliable Conversation Map for one topic across 10–20 African technology and business shows.**

Creator pages should be included once the core mapping experience is working.

Clip suggestions and the newsletter should be added at the end of this phase.

### Phase 1 success criteria

The product should target:

- a defined minimum F1 for claim–proposition stance classification
- a defined minimum claim extraction precision/recall threshold from the 10-episode evaluation set
- at least **5 opted-in podcast creators**
- at least **250 newsletter subscribers**
- evidence that creators are sharing their Conversation Atlas pages

The exact model thresholds should be selected after establishing the baseline rather than choosing arbitrary numbers before seeing the data.

---

# 22. Phase 2 — Conversation Expansion
**Approximately Months 5–12**

Expand into:

- additional topics
- additional shows
- topic evolution
- email alerts
- WhatsApp alerts
- creator archive tools
- archive revival
- coverage-gap analysis
- guest preparation

The system should begin accumulating enough longitudinal data to support more advanced temporal analysis.

---

# 23. Phase 3 — Multilingual and B2B Intelligence
**Approximately Months 12–24**

Expand into:

- French
- Swahili
- Kinyarwanda
- code-switched conversations
- multilingual discovery
- prediction tracking
- brand monitoring

Original-language transcripts should always be preserved alongside translations.

The first major B2B product will focus on **brand and competitor conversations across podcasts**.

---

# 24. Phase 4 — Conversation Intelligence Platform
**24+ months**

Once the corpus and identity data are sufficiently deep, introduce:

- prediction ledger
- changed-minds tracking
- topic evolution at scale
- public API
- research briefings
- investor briefings

Then expand beyond podcasts into other forms of long-form public conversation, potentially including:

- YouTube
- live audio
- radio

This expansion is particularly important for reaching a wider African audience.

---

# 25. Long-Term Vision

The long-term ambition of Conversation Atlas is larger than podcast discovery.

The end state is:

> **The conversation intelligence layer for Africa — a place to understand what people are thinking, debating, predicting, and eventually changing their minds about, with every insight traceable to its source.**

Podcasts are the starting point because they contain rich, long-form conversations.

The enduring asset is not simply the audio collection.

It is the structured layer built from those conversations:

```text
Audio
  ↓
Conversation
  ↓
Claims
  ↓
Propositions
  ↓
Stances
  ↓
Arguments
  ↓
Agreement / Disagreement
  ↓
Emerging Ideas
  ↓
Temporal Change
  ↓
Conversation Intelligence
```

Conversation Atlas therefore aims to transform long-form public conversation from **something people listen to** into **something people can explore, compare, analyze, and learn from**.

---

# 26. First Concrete Build Step

The first build step is intentionally small:

```text
Choose one topic
       ↓
Write one proposition
       ↓
Identify 10–15 relevant episodes
       ↓
Verify RSS feeds
       ↓
Begin collecting the source material
```

Everything else follows from this first experiment.

The first question is not:

> **“Can we build the whole platform?”**

It is:

> **“Can we create one Conversation Map so compelling and trustworthy that creators and users want to share it?”**