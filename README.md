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


## Evaluating a RAG Pipeline
1. Curate a Test Set. Example questions set with the right context identified and reference answers provided
2. Measure Retrieval - Mean Reciprocal Rank(MRR), Normalized Discount Cumulative Gain(nDCG), Recall@K, Precision@K, where is a number. How good is the RAG at retrieving content?
    - Recall @ K. The Proportion of tests where relevant context was in the top K chunks
    - Precision @ K. Proportion of the top K chunks that relevant
3. Measure Answers. For example, use LLM-as-a-judge to score provided answers against criteria like accuracy, completeness and
relevance


### 10 RAG Advanced Techniques
1. Chunking R&D - experimenting with chunking strategy
2. Encoder R&D - select the best encoder model based on a test set
3. Improve prompts - general content, the current date, relevant context and history
4. Document pre-processing - use an LLM to make the chunks and/or text for encoding
5. Query rewriting/preprocessing - use an LLM to convert the user's question to a RAG query
6. Query expansion - use an LLM to turn the question into multiple RAG queries
7. Re-ranking - use an LLM to sub-select from RAG results
8. Hierarchical - use an LLM to summarize at multiple levels
9. Graph RAG - retrieve content closely related to similar document
10. Agentic RAG - use agents for retrieval, combining with memory and tools such as SQL


## Fine-tuning a Frontier Model
Transfer Learning - taking a pretrained model as base, and use additional training data to fine-tune it for our task.

## 5 Step Strategy for Selecting and Applying LLMs to Business
**1. Understand:** This includes gathering business requirements for the task, identifying performance criteria(model and business centric metrics), understanding the data(quantity, quality & format), and determining non-functionals(cost constraints, scalability, latency)

**2. Prepare:** The step include researching existing or non-LLM solutions(potential baseline model), comparing relevant LLMs and curating data(clean, preprocess & split)


**3. Select:** Choose LLM(s), experiment, train and validate with curated data

**4. Customize:** Four techniques to optimize the performance of the model - prompt, RAG, Agents(Inference time) & fine-tune (training time).

**5. Productionize** 


## The Four Steps Of Training Neural Network
1. Forward Pass: predict the output given inputs
2. Loss Calculation: how different was the prediction to the ground truth
3. Backward Pass: how should we tweak parameters to do better next time (the gradients)
4. Optimization: update parameters a tiny step to do better next time


## Three Stages to fine-tune with OpenAI
1. Create training dataset in jsonl format and upload to OpenAI
2. Run training - training loss and validation loss should decrease
3. Evaluate result, tweak and repeat


## LoRA - Low Rank Adaptor
Llama 3.2 with 3 billion weights.
1. Freeze the weights. We will not optimize them
2. Select some layers to target, called "Target Modules"
3. Create new "adaptor" matrices with lower dimensions, fewer parameters
4. Apply these adaptors to the 'Target Modules' to adjust them - and these get trained

### 3 Essential Hyperparameters for LoRA Fine-tuning
1. **r** - the rank or how many dimensions in the low-rank matrices. Start with 8, then double to 16, then 32 until diminishing returns.

2. **alpha** - the scaling factor that multiplies the lower rank matrices. Rule of thumb: choose alpha twice the value of r.

3. **Target Modules** - the layers of the neural network to be adapted. Rule of thumb: start by targeting the attention heads.


### Quantization - the Q in QLoRA
Intuition: keep the number of weights but reduce their precision. Model performance is worse, but the impact is surprisingly small.
Instead of 32 bits, reduce to 8 bits, or even to 4 bits. We are quantizing the base model to 4-bits, not the LoRA matrice.


P.S: There are base models, chat/instruct variant models and reasoning models. The base models are good for problems that doesn't require instruct-response format.


### Five Important Hyper-parameters for QLoRA
1. Target Modules
2. dimension, r
3. Alpha
4. Quantization
5. Dropout - randomly, 10/20% of the matrix zero-out


### Five Important Hyper-parameter for Training
1. Epochs
2. Batch size
3. Learning Rate
4. Gradient Accumulation - speed up the training
5. Optimizer 
