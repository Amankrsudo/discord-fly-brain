# Fly Brain

Fly Brain is a Python project combining an interactive Discord simulation of a fruit-fly-like agent with a research workspace exploring Drosophila neural circuits and connectome evidence.

> **Status:** The code imports in an isolated Python environment, but the current standalone bot package has not yet passed Discord authentication or end-to-end runtime verification. Treat the bot instructions as a test setup, not a claim of a verified production release.

## What is in this repository?

- **Discord simulation:** `fly_bot.py`, `fly_controller.py`, `group_brain.py`, `social_simulation.py`, and `experiment_runner.py`.
- **Dashboard and visual assets:** `brain_dashboard.py`, `dashboard_animation.py`, `sprites/`, and `dashboard assests/`.
- **Biological-brain modules:** `biological_brain/`. The optional product switch `ENABLE_BIOLOGICAL_3_0` defaults off.
- **Research and reproducibility materials:** `research/`, `research_archive/`, `methods/`, `data/`, and `paper/`. These materials are research artifacts, not a claim that every hypothesis or model parameter has been experimentally validated.

## Run the Discord bot locally

### Requirements

- Python 3.10 or newer (use a current supported Python release).
- A Discord application and bot token created in the [Discord Developer Portal](https://discord.com/developers/applications).
- Permission to add the bot to a test Discord server.

### Setup

1. Clone or download this repository.
2. Open a terminal in the repository root.
3. Create and activate a virtual environment:

   **Windows PowerShell**
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

   **macOS/Linux**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

4. Install dependencies:

   ```bash
   python -m pip install -r requirements.txt
   ```

5. Create a private `.env` file from the example:

   **Windows PowerShell**
   ```powershell
   Copy-Item .env.example .env
   notepad .env
   ```

   **macOS/Linux**
   ```bash
   cp .env.example .env
   ```

6. Put your bot token after `DISCORD_TOKEN=` in `.env`. Do not share it, add it to screenshots, or commit the file.
7. Start the bot from the repository root:

   ```bash
   python fly_bot.py
   ```

If login returns `401 Unauthorized`, Discord rejected the token. Confirm that you used the Bot token (not an Application ID or Client Secret), that the `.env` file is in the same directory as `fly_bot.py`, and that the token has not been reset or exposed.

### Important runtime data

The bot may create or use `fly_state.json` and `bot_config.json` in the project directory. These are local runtime files; keep them out of public commits. Start with a fresh local state when testing a downloaded copy.

### Optional biological 3.0 layer

The optional `ENABLE_BIOLOGICAL_3_0` setting is disabled by default. Do not enable it unless you understand the experimental status and limitations documented in the repository's release specification and research materials.

## Research status and scientific limits

Fly Brain's research artifacts distinguish public-data reanalysis, modeled demonstrations, and evidence that is not yet authorized or established. In particular, do not interpret exploratory PSI→MN5 attenuation or transfer values as validated biological measurements. Read the relevant audit and evidence files before reusing scientific claims.

## Development and verification

Install the runtime dependencies with `python -m pip install -r requirements.txt`. The full test suite may contain computationally heavy research tests; report exactly which tests were run and passed rather than treating collection success as a complete test pass.

Before calling a bot package a release, test it from a clean extracted folder and verify token loading, Discord login, slash-command registration, dashboard/asset rendering, restart behavior, and runtime-state isolation. A successful Python import alone does not establish end-to-end functionality.

## License and citation

See [LICENSE](LICENSE) for licensing terms and [CITATION.cff](CITATION.cff) for citation metadata.
