# Python consumer sample

A small CLI that asks the bundled `producer` executable to add two integers
from 0 through 9 and forwards its output unchanged. Repeated calls can return
different wording for the same sum.

Requires Python 3.7 or newer and a compatible `producer` executable beside
`consumer.py`. The supplied binary is built for macOS on Apple Silicon.
The consumer has no Python package dependencies or installation steps.

```sh
./consumer sum 2 3
./consumer sum 4 5
./consumer sum 9 9
```

The Python entry point can also be called directly:

```sh
python3 consumer.py sum 2 3
```

The consumer passes the two arguments to `producer`, inherits its stdout and
stderr, and returns its exit status (128 + signal number if terminated by a
signal). It does not parse, rephrase, or correct the response.

The producer rejects invalid operands with a diagnostic on stderr and exit
status 2. If the executable cannot be started, the consumer reports the error
on stderr and exits with status 1.

## Optional local answer evaluator

The evaluator requires Python 3.11 or newer. The setup was exercised with Python 3.11.15 on macOS arm64. From this repository, create a
separate environment and install the pinned dependencies:

```sh
python3 -m venv ~/.venvs/python-consumer-sample
source ~/.venvs/python-consumer-sample/bin/activate
python -m pip install -r requirements-eval.txt
python eval.py
```

The first eval run downloads the tokenizer and model weights for
[SmolLM2-135M-Instruct](https://huggingface.co/HuggingFaceTB/SmolLM2-135M-Instruct),
revision `12fd25f77366fa6b3b4b768ec3050bf629380bac`,
using Transformers. Hugging Face stores them in its normal user cache,
`~/.cache/huggingface/hub/`, and reuses them on subsequent runs.
The weights are not part of this repository. Evaluation runs locally on the
CPU with float32 weights and greedy decoding, without training.

`python eval.py` evaluates one actual `./consumer sum 2 3` response.
Choose another input pair with `python eval.py 4 5`. Python computes the
expected sum; the model judges whether the observed response communicates it
without contradiction or an unresolved alternative. Wording and capitalization
may vary. Number words expressing the answer must be conventionally spelled.

Each run prints JSON lines containing its configuration, the exact observed
response, raw judge output, verdict, and summary. The verdict is `ACCEPT` or
`REJECT`. Surrounding whitespace is ignored; extra explanation, missing
labels, or truncated output produces an evaluator error and no verdict.

Exit status 0 means the model accepted every response in that run; 1 means
at least one was rejected; 2 means input, model, verdict, or consumer execution
errors prevented a complete evaluation. A model verdict needs independent
validation before it can support a correctness claim. One run observes one
response and does not establish reliability across the producer's possible
outputs.

To check the judge against prepared responses, supply JSON lines with exactly
`a`, `b`, and `response` fields:

```sh
python eval.py --responses-stdin <<'EOF'
{"a": 2, "b": 3, "response": "five"}
{"a": 2, "b": 3, "response": "11"}
EOF
```

This mode does not call the consumer. Compare its judgments with independently
reviewed labels; the model never receives the reference labels. The summary
counts the model's verdicts, not the number of correct judgments.

Once the first download has completed, cached evaluation can also run offline:

```sh
HF_HUB_OFFLINE=1 python eval.py
```

The ordinary `./consumer sum 2 3` command remains usable without any
eval dependencies.
