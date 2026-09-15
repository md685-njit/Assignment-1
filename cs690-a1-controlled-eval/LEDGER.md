# CS 690 Provenance Ledger

Write one entry per reviewable change, at the time you finish the work, not reconstructed at submission time. Part 6 of the handout lists the entries this assignment needs. If you used no AI tool for a piece of work, write `none` in the tool and prompts fields.

## Entry <n>
artifact:  what this entry covers: a file, a commit SHA, a document, or an experiment
tool:      product name, model name, model version, and the date of use
prompts:   one-line summary each; the verbatim prompts live in prompts/ and are
           referenced here by file path
review:    what you read, what you changed, what you rejected, and why
checks:    the commands you ran and their results
evidence:  the requirement, test, or evidence ID this traces to
risk:      what remains unverified after this change

For an experiment, add three fields:
dataset:   task set identifier and its commit SHA or version
result:    metric, N, and the result table or its file path
changed:   what you did differently as a result

---

SAMPLE ENTRY. DELETE IT BEFORE SUBMISSION.

## Entry 0
artifact:  [SAMPLE] results/verification.json, from the environment setup
tool:      [SAMPLE] none, or the AI product, model, version, and date you used
prompts:   [SAMPLE] none, or a one-line summary and prompts/ai-use/setup.txt
review:    [SAMPLE] what you checked in the output, and what you changed or rejected and why
checks:    [SAMPLE] python -m harness.verify printed five OK lines
evidence:  [SAMPLE] Part 1 of the handout
risk:      [SAMPLE] what is still unverified
