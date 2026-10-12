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

## Application eval suite

Run all eight application cases with one command:

```sh
./eval
```

`eval_cases.json` makes each case's inputs and expected result visible:

```json
{"id": "A05", "a": 2, "b": 3, "expected_sum": 5}
```

Each case runs the actual `./consumer sum a b`, captures its response and exit
status, and asks the existing judge whether the response communicates the
case's `expected_sum`. Python first checks that every expected sum equals
`a + b`; missing or inconsistent expectations stop the run with an input error
before any consumer or API calls. It never silently replaces an expectation.
The judge accepts equivalent wording under the shared acceptance rule. The
cases run once each in this order:

| Inputs | Purpose |
|---|---|
| `0 + 0`, `9 + 9` | Minimum and maximum sums |
| `0 + 9`, `9 + 0` | Zero in either position |
| `2 + 3`, `3 + 2` | Ordinary addition and reversed operands |
| `4 + 5`, `4 + 6` | One-digit to two-digit answer boundary |

The terminal uses the same readable format as judge validation: PASS, FAIL,
or ERROR per case, with the operands, expected sum, actual response, judge
verdict, duration, and a final summary. PASS means ACCEPT; FAIL means REJECT;
ERROR means the consumer or evaluator could not supply a usable result.
All cases run even if an earlier case fails. Consumer calls time out after
10 seconds. There are no automatic retries.

The judge requires the API key and network setup described below. A normal run
makes eight API calls and consumes API credits. `./eval` prefers the installed
Homebrew Python 3.11 on this macOS setup, falling back to `python3` elsewhere.
To select an interpreter explicitly, run `python3 -B eval.py`.

Save full JSONL records while retaining readable terminal output:

```sh
./eval --evidence application-run.jsonl
```

The parent directory must exist and the evidence file must be new. Records
include the selected cases, source and binary checksums, commands, captured
stdout/stderr and exit status, judge requests/responses, timing, and summary.
Evidence write errors stop the run. Without `--evidence`, no file is written.
Exit 0 means all cases passed; 1 means at least one failed with no errors;
2 means an input, setup, consumer, evaluator, or evidence-file error.

This is a representative sample, not exhaustive input or output coverage.
Random wording can change between runs. A passing run reports the judge's
acceptance of these eight observed responses, not universal correctness or
repeatability. Inspect rejected responses because the judge is fallible.
The separate judge-validation command below continues to run only its fixed
reviewed examples.

## Judge validation

The fixed examples validate the judge independently against reviewed labels.
They do not tune the judge or exercise the consumer and producer. Use `./eval`
above to run the application suite.

The judge calls the pinned OpenAI model `gpt-4o-2024-11-20`. It needs Python
3.7 or newer, network access, and an OpenAI API key with model access and credits.
It uses Python's standard library; no extra Python packages are required.

Put the key in a local `.env` file beside `judge_validation.py`:

```dotenv
OPENAI_API_KEY=your-key-here
```

Alternatively, set `OPENAI_API_KEY` in the process environment. A value in the
local `.env` takes precedence. The file is read as data, not executed, and the
key is excluded from diagnostic output.

Run from this repository:

```sh
python3 -B judge_validation.py
python3 -B judge_validation.py 4 5
```

The first command runs the 11 reviewed examples in `judge_validation_cases.json`, making one
API call per example. These fixed responses test the judge's judgments; the
consumer and producer are not called. Five examples should be accepted and six
should be rejected. A case passes when the actual verdict matches its reviewed
expectation. Expected verdicts stay local and are not sent to the model.

The second command evaluates one actual `./consumer sum 4 5` response. Use
`python3 -B judge_validation.py 2 3` to check that pair. This optional mode
checks one live response; it is not a consumer/producer eval suite.

To judge supplied text, pass JSON lines containing exactly
integer `a` and `b` values from 0 through 9 and a string `response` to
`python3 -B judge_validation.py --responses-stdin`.

On the current Apple Silicon setup, the installed Homebrew Python has a working
TLS trust store:

```sh
/opt/homebrew/opt/python@3.11/libexec/bin/python3 -B judge_validation.py
/opt/homebrew/opt/python@3.11/libexec/bin/python3 -B judge_validation.py 4 5
```

Use this interpreter if the default `python3` reports
`CERTIFICATE_VERIFY_FAILED`; TLS verification stays enabled. It also supports
the `--responses-stdin` mode described above.

The terminal shows a running message, then PASS, FAIL, or ERROR for each case,
with the operands, expected sum, response, judge verdict, and duration. A final
summary counts passed, failed, and errored cases. The reviewed suite shows case
IDs and expected verdicts: PASS means the verdict matched; FAIL means it did not.
For a live consumer check or `--responses-stdin`, the expected verdict is ACCEPT.
ERROR means no usable verdict was obtained because the consumer or evaluator
failed. Input and setup errors stop the run with a readable message. Response
text is quoted, with newlines shown as `\n`.

To save full records while keeping the terminal readable, use `--evidence PATH`:

```sh
/opt/homebrew/opt/python@3.11/libexec/bin/python3 -B judge_validation.py --evidence run.jsonl
```

The parent directory must exist, and the file must be new; existing files are
never overwritten. Without this option, no evidence file is written. File
errors return exit status 2. An evidence write error stops the run; the file
may contain only the records saved before that error.

Python computes the expected sum. The model judges whether the response clearly
communicates it without contradiction or an unresolved alternative. Equivalent
wording and capitalization are acceptable; number words must be conventionally
spelled.

The verdict must be exactly ACCEPT or REJECT, ignoring surrounding whitespace.
Explanations, empty output, refusals, truncated output, and API failures are
evaluator errors and supply no acceptance verdict. Requests use temperature 0,
top_p 1, seed 0, a 256-token cap, and `store: false`. There are no automatic
retries. The seed and temperature do not guarantee identical future responses.

The optional JSONL evidence file records the request messages, raw API response,
model, backend fingerprint, token usage, termination reason, timing, and request ID.
Suite evidence also records the case IDs, expected verdicts, actual outcomes,
and suite checksum. Reference labels are stored in evidence, not API messages.
The API does not expose its internal rendered prompt or generated token IDs.
Requests send the judging instruction, expected sum, and response text to OpenAI
and consume API credits.

Exit status 0 means every verdict matched its expectation; 1 means at least one
mismatch without errors; 2 means an input, setup, API, verdict, consumer, or
evidence-file error.

The reviewed examples check agreement with development labels; passing them
does not establish general evaluator reliability or verify the live consumer.
Live-response statuses report model judgments and do not independently prove
those judgments correct.
