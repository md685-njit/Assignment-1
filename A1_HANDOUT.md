# CS 690 Assignment 1: Replicating a Controlled Evaluation

**Total: 100 points. Individual assignment.**

This assignment builds on: Week 3, Foundations: Large Language Models for Code.

## Why this assignment exists

You have all seen claims like "this model scores 73 percent at coding." A number like that sounds like a fact about the model, the way height is a fact about a person. The Week 3 lecture argued that it is not. A score depends on which problems were asked, how they were worded, which settings were sent, how many attempts were allowed, how the answers were checked, and the date of the run. Change any of those and the number moves. The model is only one part of the result.

In this assignment you see that for yourself, on your own computer. You are given a complete, working evaluation harness, the kind of script described on the slide "Putting it together: your harness." You run it to compare two models on the same 20 small Python problems, and then you decide what the numbers do and do not allow you to say.

The slide "What you should be able to do by the end" promised that everything on it would be used in this homework. This is where each item is used:

- Explain what happens between typing a prompt and seeing an answer: Part 2, questions Q1 and Q2.
- Send the same request through code instead of a chat window, and know which settings you chose: Part 3 and question Q2.
- Say why the same prompt can give two different answers, and how to make a run repeatable: question Q3 and Part 4.
- Read a published coding score and ask the right four questions about it: Part 5.

## What "replicate" means here

All of the code is written, commented, and tested. You will not write or change any code. Your work has three parts:

1. **Reproduce.** Install the tools, then rerun the verification check, the test suite, and the experiment exactly as provided.
2. **Understand.** Read the code until you can explain what each file does, how the files connect, and which Week 3 idea each part puts into practice.
3. **Interpret.** Report what your results show and, just as important, what they do not show.

You write all of your answers in one file, `REPORT_TEMPLATE.md`, inside your repository. It is the only file you edit.

Your numbers will not match a classmate's exactly. Both models are sampled at temperature 1.0 with no seed, so every run draws different answers. That is expected, and explaining why is part of the assignment.

## Everything you will do, in order

1. Install the tools, create a public GitHub repository, and set up Python (README sections 1 to 6).
2. Run the verification command and commit its record (Part 1).
3. Run the tests, read the code, and answer Q1 to Q5 (Part 2).
4. Run the experiment and commit its results (Part 3).
5. Fill in the results table and write a short memo (Part 4).
6. Write a short note about one public benchmark (Part 5).
7. Push everything and submit your repository link on Canvas (Part 6).

## Why we start with replication

- **It moves you from asking to measuring.** Most of you have used these tools only through a chat window. But code gives you: a loop instead of retyping, settings written into every request, a file anyone can rerun, token counts on every call, and a fair comparison where one line changes. This harness does each of those things, and you will see where.
- **Later work builds on it.** Later assignments and the semester project ask you to change and extend a harness like this one. You need to be able to run one and read one first.
- **The setup carries forward.** Python, Docker, Git, and an API key are your working environment for the rest of the course. Getting them working now, with nothing else to worry about, is deliberate.

## How the repository connects to Week 3

| Week 3 idea (slide title) | Where it lives in the repository |
| --- | --- |
| "The same request, two ways," "What you send," "What comes back" | `harness/provider.py` sends each request and keeps the answer, the returned model version, the token usage, and the stop reason. |
| "A model name is not enough" | Every row of `results/experiment/raw_results.jsonl` records the requested model, the version string the API returned, the settings, and the date. |
| "Rule 2: temperature, the randomness dial" and "Settings to start from" | `conditions.json` sends temperature 1.0 to both models and asks for three attempts per problem, so the attempts differ on purpose. |
| "What a run record has to contain" | The rows of `results/experiment/raw_results.jsonl`, together with `results/experiment/manifest.json`, which records the problem set and the configuration. |
| "One run tells you very little," "pass@k, worked through," "The version people get wrong" | `pass_at_k` in `harness/metrics.py`. |
| "One number is still not a result" and "Where that range comes from" | `bootstrap_task_ci` in `harness/metrics.py`. |
| "What more attempts cannot fix" and "What that means for your own work" | The frozen tests in `tasks/cs690_eval20.json` decide every verdict, so every score measures the models and those tests together. |
| "Putting it together: your harness" | Problems: `tasks/cs690_eval20.json` and `harness/tasks.py`. Sampler: `harness/provider.py`. Runner: `harness/sandbox.py`, `harness/docker_entry.py`, and the `Dockerfile`. Grader: `harness/grader.py`. Report: `harness/metrics.py` and `harness/report.py`. `harness/runner.py` drives them in that order. |
| "What a benchmark is, and how to read one" through "Saying it at the right strength" | Part 5 of this assignment. |

## What you are given

The repository `cs690-a1-controlled-eval` contains:

- the complete harness in `harness/`, with every function finished and every file commented;
- `CS690-Eval20`, a frozen set of 20 small Python problems and their tests, in `tasks/cs690_eval20.json`;
- a Docker sandbox that runs model-written code with no network access and limited resources;
- `conditions.json`, which fixes the two model conditions and every setting;
- the test suite in `tests/`;
- `README.md`, which walks you through installation and every command, step by step;
- `REPORT_TEMPLATE.md`, the file where you write your answers.

`CS690-Eval20` was written for this course. It is not a public benchmark, and the course makes no claim that its problem types are new or absent from model training data. Its purpose is to give every student the same frozen measurement surface.

## What you need

- A 64-bit computer on which you can install software: Windows 11, or Windows 10 version 22H2; one of the three most recent versions of macOS; or Linux. Docker needs at least 8 GB of memory on Windows and 4 GB on a Mac, hardware virtualization turned on, and several gigabytes of free disk space.
- Python 3.14, Docker Desktop (Docker Engine on Linux), Git, and a code editor. Visual Studio Code is a good free choice. Any Python from 3.11 through 3.14 works. Python 3.15 does not work with this harness yet, because a library it depends on has not caught up.
- A GitHub account. The repository you create for this assignment is public, so anyone can read it.
- An OpenAI API account with prepaid credit. A ChatGPT subscription does not include API use. OpenAI's smallest credit purchase is $5, and at the prices OpenAI listed in September 2026 the full experiment uses well under one dollar of it.

`README.md` section 1 lists where to get each one.

## The task

### Part 1. Set up and verify the environment

1. Read `README.md` from start to finish before you run anything.
2. Follow README sections 1 through 6: install the tools, create your public repository, and create the Python environment.
3. Start Docker, then run the verification command from README section 7:

   ```text
   python -m harness.verify
   ```

4. Confirm that it prints five `OK` lines: 20 tasks loaded, the dataset fingerprint matched, code ran inside the Docker sandbox, the network probe was blocked, and `results/verification.json` was written.
5. Commit `results/verification.json`, and paste the five `OK` lines into Part 1 of `REPORT_TEMPLATE.md`.

### Part 2. Run the tests and read the code

1. With Docker running, run the test suite (README section 8):

   ```text
   pytest -q
   ```

   The expected result is `20 passed`. If the summary says `2 skipped`, Docker was not found; fix that and run the tests again. Paste the final summary line into Part 2 of `REPORT_TEMPLATE.md`.

2. Read the code in the order given in README section 9, "How the code fits together." Every file begins with a comment that explains its job and how it connects to the others.

3. Check the lecture's numbers against the code:

   ```text
   python -c "from harness.metrics import pass_at_k; print(pass_at_k(10, 3, 1), pass_at_k(10, 3, 5))"
   ```

   It prints `0.30000000000000004 0.9166666666666666`. These are the two values from the slide "pass@k, worked through": pass@1 = 0.30 and pass@5 = 11/12. The extra digits at the end of the first value are ordinary rounding in how computers store decimal numbers, not an error.

4. Answer the five questions below in Part 2 of `REPORT_TEMPLATE.md`. Write in your own words, about 75 to 150 words each, and base every answer on the code in this repository. Name the files and functions you describe.

**Q1. The path of one attempt.** Start from one task in `tasks/cs690_eval20.json` and describe each step until its result becomes one row in `results/experiment/raw_results.jsonl`. Name the file and function responsible for each step. Explain why the generated code runs inside the Docker sandbox rather than directly on your computer.

**Q2. What is sent and what comes back.** List the settings every request sends, using `conditions.json` and `harness/provider.py`, and say in one sentence what each one controls, using the Week 3 definitions. Then list what the harness keeps from each reply. Explain why the requested model name alone would not identify what answered you.

**Q3. Same prompt, different answers.** Both conditions use temperature 1.0 and ask for three attempts per problem. Explain why the three attempts on one problem can differ, and why that is intended in this experiment. Then name the files and fields the harness records so that someone else could rerun your experiment and check your work.

**Q4. pass@k by hand.** One task had n = 3 attempts, and c = 1 of them was correct. Using the formula on the slide "pass@k, worked through," compute pass@1 and pass@2 by hand and show your work. Confirm both values with `pass_at_k`. Then compute the shortcut `1 - (1 - c/n) ** k` for k = 2, and use the slide "The version people get wrong" to explain why the two answers differ.

**Q5. Why whole problems are redrawn.** Explain, step by step, what `bootstrap_task_ci` does. Explain why it draws whole problems instead of individual attempts. Name the test in `tests/test_metrics.py` that enforces this rule, and explain what that test checks and why it works.

### Part 3. Replicate the experiment

1. Set your API key as described in README section 10. Never put the key in a file.
2. Before spending anything, run:

   ```text
   python -m harness.runner --config conditions.json --plan
   ```

   Confirm that it reports `20 x 3 x 2 = 120` planned generations. This command makes no API calls.

3. Run the experiment:

   ```text
   python -m harness.runner --config conditions.json
   ```

4. If the run stops partway, run the same command again. It picks up where it stopped and does not pay again for finished work. Do not delete anything in `results/`.
5. Do not change any code, `conditions.json`, the task file, or any file the runner creates. In a replication, an unexplained change makes the result meaningless. If something fails and rerunning does not fix it, contact me instead of working around it. If a replacement `conditions.json` to the whole class, use that file.
6. Commit and push everything the run created under `results/` and `prompts/` (README section 13).
7. Write down the dollars you spent, from the Usage page of your OpenAI account. They go in the Part 4 table.

### Part 4. Interpret the results

Fill in Part 4 of `REPORT_TEMPLATE.md`. Take every number from `results/experiment/summary_A.json` and `results/experiment/summary_B.json`, not from the console. README section 13 shows which summary field goes in which column.

Your table must contain, for each condition:

- condition ID;
- requested model and returned model version;
- attempts per task and total attempts;
- pass@1;
- the 95 percent task-level bootstrap confidence interval for pass@1;
- pass@2;
- total input tokens and output tokens;
- dollars spent, from your usage page, or `not available` if your account does not show it.

Then write a memo of no more than 500 words, not counting the table, that addresses all five items:

1. State the observed ranking by pass@1 point estimate.
2. State whether the uncertainty evidence supports ranking the two conditions.
3. If it does not, include the exact sentence `The evidence does not support a ranking.`
4. State one external-validity limitation specific to `CS690-Eval20`: one reason a result on these 20 problems may not describe how the models would do on real software work.
5. State one likely source of variance specific to this experiment, and explain why a rerun, or a classmate's run, gives somewhat different numbers.

Overlapping intervals are not a formal significance test, and you are not asked to run one. When the evidence does not clearly separate the two conditions, the careful conclusion that they cannot be ranked on this evidence receives full credit. The slide "Saying it at the right strength" calls that a conclusion, not a failure.

### Part 5. Read a published score: the four questions

In Part 5 of `REPORT_TEMPLATE.md`, write 300 to 400 words applying the four questions from the slide "What a benchmark is, and how to read one" to exactly one public benchmark from the lecture: HumanEval, MBPP, LiveCodeBench, or SWE-bench.

1. What does it measure? State it as a task.
2. What does it not measure that a software project may depend on?
3. How can a reported score rise without the underlying model becoming better?
4. Could the model have seen the answers already? State the contamination status or risk based on evidence, not assumption.

Use the benchmark's primary paper, listed on the Week 3 References slide, or its official documentation for the task definition. Cite evidence for any contamination, saturation, or current-status claim, date any current-status source, and write each claim at the strength the slide "Saying it at the right strength" describes. Do not run the benchmark. End with at least one sentence explaining why its published score is not interchangeable with your `CS690-Eval20` result.

### Part 6. Submit

1. Check that every part of `REPORT_TEMPLATE.md` is filled in. At the top, give your name, your repository link, and the short SHA of the commit that added your experiment results. `git log --oneline` lists your commits with their short SHAs. A commit cannot contain its own SHA, so the results commit is the one to give.
2. Commit and push, then run `git status` and confirm that nothing is left uncommitted.
3. Open your repository link in a private or incognito browser window, where you are not signed in to GitHub. If you can see your files, including `results/experiment/` and your filled-in `REPORT_TEMPLATE.md`, the repository is public and ready. README section 14 explains what to do if it is not.
4. Submit the repository link on Canvas.

## Deliverables

One public GitHub repository, created from the provided code, containing:

- the code, unchanged;
- `results/verification.json`;
- the complete `results/experiment/` folder;
- the `prompts/` folder;
- `REPORT_TEMPLATE.md`, with every part filled in.

A repository with an empty `results/experiment/` folder cannot be graded.

## Turn-in instructions

Submit one item through Canvas: the link to your public GitHub repository. No PDF or other file is needed, because everything is graded from the repository. Push all of your work before the deadline.

This is an individual assignment: do not submit, or substitute results from, your team project repository.

## AI policy

AI tools are permitted on this assignment. You are responsible for every answer you submit, including any text an AI tool drafted for you, and for checking that it is correct and matches the code in this repository. Submitting AI-generated work you have not reviewed is misrepresentation of authorship and is treated as an academic-integrity violation under the course syllabus. You may be asked in class to explain any part of your submission.

## Rubric summary

This assignment is worth 100 points. Code changes, extra conditions, extra samples, or additional API spending do not earn extra credit.

## An example to keep in mind

Picture a spelling test for two students, A and B. Both get the same 20 words and three tries at each word. When the tests are marked, A spelled the word correctly on 62 percent of tries and B on 78 percent. B looks like the better speller.

But the test had only 20 words. A different 20 words could easily have changed the picture. So you ask a second question: how far could each score have moved if the words had been different? Suppose the answer is that A is somewhere between 50 and 73 percent and B is somewhere between 67 and 88 percent. Those ranges overlap. The honest conclusion is that this test cannot tell you who spells better. You would need more words.

This assignment is that spelling test.

- The 20 words are the 20 problems in `CS690-Eval20`.
- The two students are the two models.
- The three tries are the three attempts per problem.
- The teacher who marks every paper the same way is the Docker sandbox running the same tests.
- The percentage of correct tries is pass@1.
- The question "what would a different 20 words have done?" is the bootstrap interval, which answers it by redrawing whole problems, never single tries.

If your two intervals overlap, the correct conclusion is "The evidence does not support a ranking," and it earns full credit. In this assignment you are not really testing the models. You are testing whether you can trust your own test. Ask the same thing every time you read that a model scored some percentage on a coding benchmark: what was tested, how was it checked, how many problems were there, and how far could the number move?
