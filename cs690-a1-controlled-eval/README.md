# CS 690 Assignment 1: Controlled Evaluation Harness

This repository holds the complete evaluation harness for Assignment 1. What you submit, and how it is graded, is described in `A1_HANDOUT.md`, which came in the same download. This file tells you how to install everything, how to run every command, and how to read the code.

Read this file from top to bottom before you run anything. The steps are in the order you need them.

If you are stuck on installation for more than about thirty minutes, stop and contact the instructor with the exact error message. Setup problems are normal on a first assignment, and they are much quicker to solve together.

## What you will do with this repository

You will not write or change any code. Every function is finished, commented, and tested. You will:

1. install the tools and put this code in a private GitHub repository (sections 1 to 6);
2. confirm your setup with one command (section 7);
3. run the test suite (section 8);
4. read the code until you can explain how it works (section 9);
5. run the fixed experiment that compares two models on the same 20 problems (sections 10 to 13);
6. write your report and provenance ledger (section 14).

## Before you start: the terminal

Every step below is a command typed into a terminal, a window where you type instructions instead of clicking.

- **Windows:** use PowerShell. Open the Start menu, type `PowerShell`, and open Windows PowerShell. The Windows commands in this file are written for PowerShell, not for Command Prompt.
- **macOS:** open Terminal, which is in Applications, then Utilities.
- **Linux:** open your distribution's terminal application.

Once Visual Studio Code is installed (section 4), you can use the terminal built into it instead: open the repository folder in VS Code, then choose Terminal, then New Terminal. It starts in the right folder, and it handles GitHub sign-in for you (section 5). We recommend it.

Rules for every command in this file:

- Enter one command at a time, press Enter, and wait for it to finish before the next one.
- Do not type the prompt your terminal shows before the cursor, such as `$`, `%`, or `PS C:\Users\you>`.
- Run commands from the repository folder, `cs690-a1-controlled-eval`, unless a step says otherwise. Use `cd` to move into a folder, and `pwd` to see which folder you are in. Both work on every operating system.
- If a path contains spaces, put it in quotes, for example `cd "C:\Users\Jane Doe\cs690"`.

### Where to put the files

Unzip the download into a folder that is not synced by OneDrive, iCloud Drive, Dropbox, or Google Drive. Sync services interfere with the thousands of small files the Python environment creates. Good choices are `C:\Users\<your name>\cs690` on Windows and `~/cs690` on macOS and Linux, where `~` means your home folder.

Inside the unzipped files, find the folder `cs690-a1-controlled-eval`, which sits next to `A1_HANDOUT.md`, and move into it. For example:

```text
cd ~/cs690/Assignment-1/cs690-a1-controlled-eval
```

Depending on how your computer unzipped the download, your path may have one more or one fewer `Assignment-1` folder. What matters is that you end up inside `cs690-a1-controlled-eval`.

## 1. What you need, and where to get it

| What | Where to get it | What it is for |
| --- | --- | --- |
| Python 3.14 | Section 2 | Runs the harness. |
| Docker Desktop (Docker Engine on Linux) | https://www.docker.com/products/docker-desktop/ | Runs model-written code in a sealed container. |
| Git | https://git-scm.com/downloads | Records your work and submits it. |
| Visual Studio Code | https://code.visualstudio.com/ | Reading the code, with a built-in terminal. |
| A GitHub account | https://github.com/ | Holds your private repository. |
| An OpenAI API account with prepaid credit | https://platform.openai.com/ | Access to the two models you compare. |
| A way to make a PDF | Word, Google Docs, or a Markdown editor | Your report. |

Your computer needs:

- **Windows:** 64-bit Windows 11, or Windows 10 version 22H2, with at least 8 GB of memory and hardware virtualization turned on. Section 3 shows how to check.
- **macOS:** one of the three most recent versions of macOS, on Apple silicon or Intel, with at least 4 GB of memory.
- **Linux:** a current 64-bit distribution supported by Docker Engine.
- Several gigabytes of free disk space, and permission to install software.

The API account is the only part that costs money. OpenAI's smallest credit purchase is $5, and at the prices OpenAI listed in September 2026 the whole experiment uses well under one dollar of it.

## 2. Install Python 3.14

Any Python from 3.11 through 3.14 works. Install 3.14 unless you already have one of those.

**Do not use Python 3.15.** It is scheduled for release on October 1, 2026, and a library that the OpenAI client depends on had no Python 3.15 build when this assignment was prepared. If you try, section 6 stops with the message `requires a different Python`.

### Windows

1. Install the **Python install manager** from the Microsoft Store (search for "Python Install Manager"), or from https://www.python.org/downloads/windows/.
2. Close PowerShell, open a new window, and install Python 3.14:

   ```powershell
   py install 3.14
   ```

   The first time you use `py`, it may ask setup questions, such as whether to add a folder to your PATH. Accepting its suggestions is fine.

3. Confirm it:

   ```powershell
   py -3.14 --version
   ```

   The answer should begin with `Python 3.14`.

Until you create the environment in section 6, you start Python 3.14 on Windows with `py -3.14`.

### macOS

1. Open https://www.python.org/downloads/macos/ and download the macOS installer for the newest **Python 3.14** release. Do not choose 3.15.
2. Run the installer.
3. In Finder, open Applications, then the Python 3.14 folder, and double-click `Install Certificates.command`.
4. Open a new Terminal window and confirm:

   ```bash
   python3.14 --version
   ```

If you use Homebrew, `brew install python@3.14` works too.

Until you create the environment in section 6, you start Python 3.14 on macOS with `python3.14`.

### Linux

Check the Python you already have:

```bash
python3 --version
```

If it shows 3.11, 3.12, 3.13, or 3.14, you will use `python3` in section 6. Otherwise, install Python 3.14 from your distribution and use `python3.14`. On Ubuntu and Debian, the environment module is a separate package:

```bash
sudo apt install python3-venv
```

## 3. Install and start Docker

The harness runs every piece of model-written code inside a Docker container: a sealed, temporary Linux system with no network, no access to your files, and strict limits on memory and time. You are about to run code that a model wrote and nobody has read. The container is what makes that safe. Section 9 shows where this happens in the code.

### Windows

1. Check that virtualization is on. Open Task Manager, choose Performance, then CPU, and find the line "Virtualization". If it says Disabled, it has to be turned on in your computer's BIOS or UEFI settings. Search the web for your laptop model and "enable virtualization", or ask the instructor.
2. Download Docker Desktop from https://www.docker.com/products/docker-desktop/ and run the installer with its default choices, including the WSL 2 option. The default per-user installation does not need administrator rights, but turning on WSL 2 for the first time does, and Windows may ask you to restart.
3. If Docker Desktop reports that WSL is missing or out of date, open PowerShell as administrator (right-click PowerShell, then Run as administrator) and run `wsl --update`, or `wsl --install` if WSL is not installed at all. Restart when asked.

### macOS

Download Docker Desktop from https://www.docker.com/products/docker-desktop/, choosing the build for your chip. To check which chip you have, open the Apple menu, choose About This Mac, and read the Chip or Processor line. Open the downloaded file and drag Docker into Applications.

### Linux

Install Docker Engine by following https://docs.docker.com/engine/install/ for your distribution. Then allow your account to use Docker without `sudo`, and log out and back in:

```bash
sudo usermod -aG docker $USER
```

### Start Docker and confirm that it works

Docker has two parts: the `docker` command, and a background engine that actually runs containers. Having the command installed does not mean the engine is running. This is the most common setup problem in this course.

- **Windows and macOS:** open the Docker Desktop application. The first time, accept the subscription agreement; Docker Desktop is free for personal and educational use. Wait until Docker Desktop shows that the engine is running.
- **Linux:** run `sudo systemctl start docker`.

Then, in a new terminal:

```text
docker run --rm hello-world
```

If the output includes `Hello from Docker!`, Docker works.

If you see `Cannot connect to the Docker daemon`, `error during connect`, or a message that the engine is not running, Docker Desktop has not finished starting. Wait a minute and try again.

**Docker Desktop must be running whenever you use this repository.** You never build the sandbox image yourself. The harness builds it the first time it needs it (section 7).

## 4. Install Git and Visual Studio Code

### Git

Check whether Git is installed:

```text
git --version
```

If that fails:

- **Windows:** install Git for Windows from https://git-scm.com/downloads, keeping the default choices. It includes Git Credential Manager, which handles GitHub sign-in.
- **macOS:** the command above offers to install Apple's command line developer tools, which include Git. Accept, wait for the install to finish, and run `git --version` again.
- **Linux:** install the `git` package, for example with `sudo apt install git`.

Then tell Git who you are. You do this once per computer. Use the email address of your GitHub account:

```text
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### Visual Studio Code

Install VS Code from https://code.visualstudio.com/. Open the repository with File, then Open Folder, and choose the `cs690-a1-controlled-eval` folder. If VS Code asks whether you trust the authors of the files, choose Yes. If it suggests the Python extension, install it.

From now on you can run every command in VS Code's terminal (Terminal, then New Terminal), which opens in the repository folder.

## 5. Put the code in your private GitHub repository

You will submit a link to a private GitHub repository. Create it now, before you run anything, so that your commits and ledger entries record the work as you do it.

1. Sign in to GitHub and open https://github.com/new.
2. Name the repository, for example `cs690-a1`, and choose **Private**. Do not add a README, a .gitignore file, or a license, because this folder already has what it needs. Click Create repository.
3. Copy the HTTPS address that GitHub shows. It looks like `https://github.com/YOUR-USERNAME/cs690-a1.git`.
4. In the terminal, from the repository folder, run these commands one at a time. Use your own address in the fifth command.

   ```text
   git init
   git add .
   git commit -m "Assignment 1 code as distributed"
   git branch -M main
   git remote add origin https://github.com/YOUR-USERNAME/cs690-a1.git
   git push -u origin main
   ```

5. Reload the repository page on GitHub. You should see the files.
6. Give the instructor access. On the repository page, open Settings, then Collaborators, choose Add people, and enter the instructor's GitHub username from Canvas.

**Signing in when you push.** GitHub does not accept your account password in a terminal.

- In VS Code's terminal, VS Code asks to sign you in to GitHub through your browser. Allow it.
- In PowerShell on Windows, Git Credential Manager opens a browser sign-in window.
- In any other terminal, Git asks for a username and a password. Enter your GitHub username, and in place of the password paste a personal access token, which you create on GitHub under Settings, then Developer settings, then Personal access tokens. Treat the token like a password.

On Windows, `git add` may print warnings that contain `LF will be replaced by CRLF`. They are harmless.

Commit and push as you work; sections 7 and 13 say when. The repository link you submit must show the final commit you want graded.

**Never commit an API key.** Not in a file, a prompt, `LEDGER.md`, or a commit message. If a key ever ends up somewhere it should not be, delete it on the OpenAI website immediately and create a new one.

## 6. Create the Python environment

A virtual environment is a private copy of Python inside this folder, in a subfolder named `.venv`, holding exactly the package versions this harness needs. Git ignores `.venv`, so it never goes into your repository.

Run these commands from the repository folder.

**Windows (PowerShell):**

```powershell
py -3.14 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

If PowerShell refuses to run `Activate.ps1` and mentions an execution policy, run the following line once, then run the activate line again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**macOS:**

```bash
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

**Linux:** the same as macOS, except that the first line uses the command you chose in section 2, for example `python3 -m venv .venv`.

The last line installs the OpenAI and Anthropic client libraries and pytest, at the exact versions listed in `pyproject.toml`, and makes the `harness` package runnable. It takes a minute or two.

While the environment is active, your prompt begins with `(.venv)`. Check the version:

```text
python --version
```

It must show a version from 3.11 through 3.14. **From here on, every command uses plain `python`, on every operating system,** because the active environment provides it.

**Activate the environment again in every new terminal,** using only the activate line: `.venv\Scripts\Activate.ps1` on Windows, or `source .venv/bin/activate` on macOS and Linux. If a command suddenly reports `No module named harness`, or says that `pytest` is not recognized, the environment is not active.

If VS Code asks whether to use the new environment for this folder, choose Yes. Its terminals will then activate the environment for you.

## 7. Verify the setup

This command checks the whole setup at once. It needs Docker running, but no API key, and it costs nothing.

```text
python -m harness.verify
```

**The first run builds the sandbox image.** Docker downloads a small official Python image and prints its build progress, which takes two to five minutes depending on your connection. Do not interrupt it. Later runs take a few seconds.

A successful run ends with these five lines, which are identical for everyone:

```text
OK: loaded 20 frozen tasks
OK: dataset sha256 5d84176547cb679f4145676d1f4dfd5061bf3b9600904911da8e5700e82eee3b
OK: generated Python executed in Docker sandbox
OK: candidate network probe was blocked
OK: model/configuration metadata written to results/verification.json
```

In order, they confirm that the 20 problems loaded, that the problem file is byte for byte the distributed one (the long string is its fingerprint), that code ran inside the sandbox, that the sandbox blocked a network connection, and that a small run record was written. Paste the five lines into Part 1 of your report, then commit the record:

```text
git add results/verification.json
git commit -m "Verification run"
git push
```

If the output instead ends with an error that mentions `docker build` and `returned non-zero exit status`, Docker is installed but not running. Start Docker Desktop and run the command again. For any other error, see Troubleshooting.

## 8. Run the test suite

With Docker running:

```text
pytest -q
```

The last line should be `20 passed`, followed by the time taken. The tests check the scoring math (`tests/test_metrics.py`), the summary file format (`tests/test_report.py`), the sandbox (`tests/test_sandbox.py`), and the problem file (`tests/test_tasks.py`). Paste the last line into Part 2 of your report.

Two other results mean that Docker is not usable yet:

- `18 passed, 2 skipped`: the `docker` command was not found, so the two sandbox tests did not run. A skip is not a pass. Install Docker, open a new terminal, activate the environment, and run the tests again.
- `2 failed, 18 passed`, with `Cannot connect to the Docker daemon` in the output: Docker is installed but not running. Start Docker Desktop and run the tests again.

Any other failure means that a file differs from what was distributed. See Troubleshooting.

## 9. How the code fits together

Every file begins with a comment that explains its job and which files it works with, and every function says what it does. Read the files in the order below. The order follows one attempt from the problem, to the model, to the sandbox, to the score.

| Step | File | What to look for |
| ---: | --- | --- |
| 1 | `conditions.json` | The two model conditions and every fixed setting. |
| 2 | `tasks/cs690_eval20.json` | The 20 problems. Each has a function name, a prompt, and the tests that decide pass or fail. |
| 3 | `harness/__init__.py` | A one-page map of every module. |
| 4 | `harness/tasks.py` | How the problems are loaded, and why the harness refuses to run if the file changed. |
| 5 | `harness/provider.py` | What is sent to the model, and what is kept from its reply. |
| 6 | `harness/grader.py` | How the code is taken out of the model's answer. |
| 7 | `harness/sandbox.py`, `harness/docker_entry.py`, `Dockerfile` | How that code runs in a sealed container, and how a verdict comes back out. |
| 8 | `harness/metrics.py`, next to `tests/test_metrics.py` | pass@k and the bootstrap interval, and the tests that define exactly how they must behave. |
| 9 | `harness/report.py` | How each summary file is checked and saved. |
| 10 | `harness/runner.py` | The main program. It calls everything above, in order. Read it last. |
| 11 | `harness/verify.py` | The setup check from section 7. |

Three habits help:

- Read the comment at the top of a file before its code.
- In VS Code, hold Ctrl (Cmd on a Mac) and click a function name to jump to where it is defined.
- Follow the `import` lines. For example, `from .sandbox import run_source` near the top of `grader.py` tells you that the grader relies on the sandbox. Tracing these lines is how you follow an attempt through the harness.

The table "How the repository connects to Week 2" in the handout shows which lecture slide each part puts into practice.

## 10. Get your OpenAI API key and set it

You need the key in section 12. Set up billing early, because a first payment can take a while to go through.

### Create the account and add credit

1. Create an account at https://platform.openai.com. The API is billed separately from ChatGPT, so a ChatGPT subscription does not cover it.
2. Open the Billing page and add credit. The smallest purchase is $5, far more than this assignment uses.
3. **Turn off auto-reload** during that step. It is on by default, and it buys more credit automatically whenever your balance runs low.
4. Open the API keys page and create a new secret key.
5. **Copy the key immediately.** OpenAI shows it in full only once. If you lose it, delete that key and create a new one.

A key with no credit behind it fails on every request. That is the most common reason the experiment does not start.

### Set the key in your terminal

The harness reads the key from an environment variable, a setting that exists only in the terminal window where you set it. The harness never reads the key from a file, so the key cannot slip into your repository.

macOS and Linux:

```bash
export OPENAI_API_KEY="paste-your-key-here"
```

Windows PowerShell:

```powershell
$env:OPENAI_API_KEY = "paste-your-key-here"
```

Check that it is set, without showing the key on screen:

```text
python -c "import os; print('key is set' if os.environ.get('OPENAI_API_KEY') else 'key is NOT set')"
```

**The key lasts only until you close that terminal window.** In a new window, set it again. That is deliberate.

Never print the key with `echo`, and never paste it into your report, your ledger, a prompt, or a chat window. If it leaks, delete it on the API keys page and create a new one.

If the instructor gives the whole class an Anthropic configuration instead, set `ANTHROPIC_API_KEY` the same way, with a key from https://console.anthropic.com.

## 11. Check the plan before you spend anything

```text
python -m harness.runner --config conditions.json --plan
```

This makes no API calls, needs no key, and costs nothing. It prints:

```text
dataset: CS690-Eval20 (20 tasks)
dataset sha256: 5d84176547cb679f4145676d1f4dfd5061bf3b9600904911da8e5700e82eee3b
conditions: A=gpt-5.6-luna, B=gpt-5.6-terra
samples per task: 3
planned candidate generations: 20 x 3 x 2 = 120
plan only: no API requests were made
```

Confirm that it plans 120 generations: 20 problems, 3 attempts each, 2 models.

## 12. Run the experiment

With Docker running, the environment active, and the key set in this terminal:

```text
python -m harness.runner --config conditions.json
```

The runner prints the same plan, then one line for each attempt as it is graded, for example:

```text
A A1-001 sample 1: PASS
A A1-001 sample 2: FAIL
```

There are 120 such lines, first for condition A and then for condition B, and your pattern of PASS and FAIL will differ from everyone else's. The run usually takes five to fifteen minutes and ends with:

```text
complete: 120 candidate rows
raw results: results/experiment/raw_results.jsonl
summaries: results/experiment/summary_A.json, results/experiment/summary_B.json
```

**If the run stops partway,** from a dropped connection, a closed laptop, or an error, run the exact same command again. Each attempt is saved the moment it is graded, so the runner skips everything already recorded and pays only for what is missing. Never delete `results/` to start over. That costs money and destroys evidence.

**Change nothing** in the code, `conditions.json`, the problem file, or any file the runner writes. The runner refuses to continue if the configuration changes after results exist.

When the run is complete, open the Usage page of your OpenAI account and write down the dollars spent. The page can take a while to update.

## 13. What the run produces, and committing it

| Path | What it holds |
| --- | --- |
| `prompts/a1-controlled-eval-fall2026/A/` and `prompts/a1-controlled-eval-fall2026/B/` | The exact prompt sent for each problem, one file per problem. |
| `results/experiment/manifest.json` | What was run: the problem set, its fingerprint, and a fingerprint of the configuration. |
| `results/experiment/raw_results.jsonl` | One line per attempt, 120 in all: the settings sent, the model version that answered, the date, the token counts, why the answer ended, and whether it passed. |
| `results/experiment/candidates/` | Every answer, saved twice: the model's full reply (`.raw.txt`) and the code taken from it (`.py`). |
| `results/experiment/summary_A.json` and `results/experiment/summary_B.json` | The scores for each condition. Your report table comes from these two files. |

Where each number in your report table comes from:

| Report column | Key in the summary file |
| --- | --- |
| Requested model | `requested_model` |
| Returned model version | `returned_models` |
| Attempts per task | `samples_per_task` |
| Total attempts | `candidate_count` |
| pass@1 | `pass_at_1` |
| 95 percent interval for pass@1 | `ci95_pass_at_1`, written as low and high |
| pass@2 | `pass_at_2` |
| Input tokens and output tokens | `input_tokens` and `output_tokens` |
| Dollars spent | Your OpenAI Usage page. The key `cost_usd` is always `null`, because the API reports tokens, not dollars. |

All of these files are evidence, and all of them go in your repository:

```text
git add results prompts
git commit -m "Controlled comparison run"
git push
git status
```

The last command should report that there is nothing to commit. Then open your repository on GitHub and check that `results/experiment/` is there.

## 14. Write the report and the ledger, then submit

- **Report:** use `REPORT_TEMPLATE.md` as the outline for your PDF, and take every number from the two summary files, not from what scrolled past in the terminal.
- **Ledger:** delete the sample entry in `LEDGER.md` and add your own entries as you finish each piece of work, as Part 6 of the handout describes. If you use an AI tool, save the prompts you gave it in `prompts/ai-use/` and refer to those files in your ledger.
- **Submit:** commit and push everything, run `git status` to confirm that nothing is left, and turn in the PDF and your repository link on Canvas.

The handout gives the full requirements for each part.

## What you must not change

This is a replication. Your results mean something only if you ran exactly what everyone else ran, so leave all of these as distributed:

- the code in `harness/` and `tests/`;
- `conditions.json`, `tasks/cs690_eval20.json`, `Dockerfile`, and `pyproject.toml`;
- every file the harness writes under `results/` and `prompts/a1-controlled-eval-fall2026/`.

The harness enforces much of this itself. It stops if the problem file changes, if any fixed setting in `conditions.json` changes, or if the configuration changes after results were written. If something fails and running the command again does not fix it, contact the instructor instead of working around it.

## Troubleshooting

Find the message you see, then apply the fix.

### Installing and setting up

- **`py` is not recognized (Windows).** The Python install manager is not installed, or PowerShell was already open during the install. Open a new PowerShell window. If that does not help, reinstall the install manager from the Microsoft Store.
- **`python3.14: command not found` (macOS).** Python 3.14 is not installed, or Terminal was already open during the install. Open a new Terminal window, or run the python.org installer again.
- **`requires a different Python` during section 6.** The environment was made with an unsupported Python, usually 3.15. Delete the `.venv` folder, install Python 3.14 (section 2), and repeat section 6.
- **An error that mentions `pydantic-core`, Rust, or `cargo` during section 6.** Same cause and same fix as the previous item.
- **`No module named harness`, `No module named pytest`, or `pytest` is not recognized.** The environment is not active in this terminal, or section 6 did not finish. Activate the environment, and if the error remains, run `python -m pip install -e ".[dev]"` again.
- **PowerShell will not run `Activate.ps1`.** Run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once, then activate again.

### Git and GitHub

- **`Please tell me who you are` when committing.** Set your name and email (section 4).
- **GitHub rejects your password when you push.** Push from VS Code's terminal, or use a personal access token (section 5).
- **`LF will be replaced by CRLF` (Windows).** Harmless. Continue.

### Docker

- **`Cannot connect to the Docker daemon`, `error during connect`, a message that the engine is not running, or `docker build` returned non-zero exit status.** Docker Desktop is not running. Open it, wait until the engine is running, and try again.
- **`Docker was not found on PATH`, or `18 passed, 2 skipped`.** Docker is not installed, or this terminal was opened before the install finished. Open a new terminal, activate the environment, and check with `docker run --rm hello-world`.
- **Docker Desktop on Windows reports a WSL or virtualization problem.** Run `wsl --update` in PowerShell opened as administrator, then restart. If Task Manager shows virtualization as Disabled, it must be turned on in the BIOS or UEFI settings (section 3).
- **`toomanyrequests`, or a pull rate limit, while the image builds.** Docker Hub limits downloads for users who are not signed in. Sign in to a free Docker account in Docker Desktop, or run `docker login`, and try again.
- **The first verification run seems frozen.** It is building the sandbox image. Give it five minutes.

### The harness

- **`CS690-Eval20 changed`.** The problem file is no longer byte for byte the distributed file, usually because it was opened and saved in an editor. Replace `tasks/cs690_eval20.json` with the copy from the original download.
- **An error that begins `A1 requires`, or `Both conditions must use the same sampling configuration`.** `conditions.json` was edited. Replace it with the copy from the original download.
- **`Experiment configuration changed after results were written`.** The configuration no longer matches the one recorded in `results/experiment/manifest.json`. Restore the original `conditions.json` and run the command exactly as written in section 12. Do not delete your results.
- **`OPENAI_API_KEY is not set`.** The key was set in a different terminal window, or the window was closed. Set it again (section 10).
- **`API generation failed after 3 attempts`, with `401` in the message.** The key is wrong or was deleted. Create a new key and set it again.
- **The same message with `429`, or with a mention of quota or credit.** The account has no credit yet, or the first payment is still processing. Check the Billing page, wait a few minutes, and run the same command again.
- **The same message with `404`, or saying that the model does not exist.** Check that `conditions.json` is unchanged. If it is, contact the instructor.
- **The run stopped partway for any other reason.** Run the same command again. It resumes where it stopped. If the same error keeps coming back, contact the instructor with the last few lines of the output.
