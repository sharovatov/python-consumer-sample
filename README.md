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

## Judge validation

The fixed examples validate the judge independently against reviewed labels.
They do not tune the judge or exercise the consumer and producer. A suite that
runs multiple live consumer/producer cases has not yet been implemented.

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
