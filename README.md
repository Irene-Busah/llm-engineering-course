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


