## Notes

GPT - Generative Pre-Trained Transformer

Context Window is the maximum number of tokens that the model can consider when generating the next token. It governs how well
the model can remember references, content and context

### Tools
Allows frontier models to connect with external functions

### Agents
LLM that controls workflow
An LLM agent runs tools in a loop to achieve a goal.

Common features include memory, planning capabilities, autonomy, LLM orchestration, functionality via tools


### HuggingFace
- Models
- Datasets
- Spaces: apps, many built gradio

The two API levels of hugging face:
1. Pipelines - higher level APIs to carry out standard tasks incredibly quickly
2. Tokenizers & Models - lower level APIs to provide the most power and control


**Training** is when you provide a model with data for it to adapt to get better at a task in the future.
**Inference** is when you are working with a model that has already been trained


### Tokenizers
Maps between text and tokens for a particular model
- Translates between text, tokens and token IDs with encode() and decode() medthods
- Contains a vocab that can include special tokens to signal information to the LLM like start a prompt


## What's the right LLM for the task at hand?
1. Start with the basics - parameters, context length, pricing, etc. You want to compare features.
2. Look at the results - benchmarks, leaderboards, arenas, etc


### The Chinchilla scaling law
Number of paramters ~ proportional to the number of training tokens

### Benchmarks
1, GPQA
2. MMLU-PRO
3, AIME
4. LiveCode Bench
5. MuSR
6. HLE


### 5 Steps Strategy
1. Understand the business requirements
2. Prepare
3. Select the model you are going to use
4. Customize
5. Productionize

4731100

## How to evaluate the performance of a GenAI solution
1. Model-centric or Technical metrics - Loss, perplexity, accuracy, precision, recall, AUC-ROC
2. Business-centric or Outcome metrics - KPI, Customer satisfaction, benchmark comparisons, etc


## RAG - Encoding LLMs & Vector Embeddings
**Auto-regressive LLMs** predicts a future token from the past.
**Auto-encoding or vector embedding models** produce output based on the full input. The encoder model turns text into a Vector Embedding, then stored in a vector database like Chroma. Examples, BERT, word2vec, OpenAI text embedding 3 small & large, gemini-embedding-001.

Chat(Question) -> Code -> Encoding LLM(Vectorize) -> Code -> Vector Datastore(retrieve) -> Code -> LLM


### LangChain
Open source framework that provides a common framework for interfacing with manu LLMs



