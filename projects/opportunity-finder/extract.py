
"""Turn raw job posts into structured records with an LLM.
 
Second stage of the Opportunity Finder pipeline. Reads each post from
``data/raw.jsonl``, asks an LLM to fill in the ``Extraction`` fields, checks the
answer against ``schema.py``, and appends the result to ``data/extracted.jsonl``.
 
Pipeline:  data/raw.jsonl -> extract.py -> data/extracted.jsonl -> index.py
 
How it works:
    1. Posts already in the output file (same ``source`` and ``post_id``) are skipped.
    2. The prompt holds the extraction rules and the post text. The field
       descriptions in ``schema.py`` are the instructions for each field.
    3. LangChain's ``with_structured_output(Extraction)`` makes the model return
       the ``Extraction`` shape; pydantic checks types and rules.
    4. An invalid answer is retried once, then logged and skipped, so one bad
       post never stops a scheduled run.
    5. Code attaches the original ``text``, the model name and the time. The LLM
       never rewrites the post.
 
Setup:
    Set the ``OPENAI_API_KEY`` environment variable. The model name is a
    command-line option, so a different model can be tried without editing code.
 
Usage:
    python extract.py [--limit N] [--model NAME] [--in PATH] [--out PATH]
 
    Defaults: --in data/raw.jsonl, --out data/extracted.jsonl. Exit code 1 if
    the API key is missing or the input file does not exist.
 
Output (``data/extracted.jsonl``, one JSON object per line):
    Each line is an ``ExtractedPost`` (see ``schema.py``): every ``RawPost``
    field, plus ``extraction`` and ``extracted_with``.
"""


# libraries
import argparse
from pathlib import Path
from langchain_core.runnables import Runnable
from schema import Extraction, ExtractedPost, RawPost
from dotenv import load_dotenv
import os


DEFAULT_MODEL = 'gpt-4o'
DEFAULT_IN = Path("data/raw.jsonl")
DEFAULT_OUT = Path('data/extracted.jsonl')


load_dotenv(override=True)
openai_api_key = os.getenv('OPENAI_API_KEY')


def build_chain(model_name: str) -> Runnable:
    """Build the prompt + """


