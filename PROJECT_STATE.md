# Discord Fly Brain — Project State

## Current Goal
Build a Discord bot containing a simulated fruit-fly brain.

## Current Stage
Discord bot + shared AI-agent workspace setup.

## Working
- Existing Fly project code
- Discord bot project
- GitHub repository
- Project animations/assets
- Git version control

## Brain
Current implementation:
- group_brain.py
- group_weights.json
- fly_controller.py
- fly_state.json

Next:
Integrate and validate the brain behavior with the Discord bot without unnecessarily rewriting the existing brain code.

## Assets
Current animations include:
- idle
- walk
- fly
- eat
- burn
- freeze
- shock
- scare
- love
- sleep
- dead
- hurt
- confused
- happy
- angry
- mating

## Architecture Rules
- Keep brain logic separate from Discord UI.
- Keep animation logic separate from brain logic.
- Do not delete existing brain code without checking first.
- Do not replace working assets unnecessarily.
- Keep the project lightweight and suitable for cheap/free hosting.
- Prefer small, maintainable changes.
- Test changes before committing.

## AI Agent Workflow
Claude Code and OpenAI Codex use this repository as the shared workspace.

Before making changes:
1. Read this file.
2. Read the relevant existing code.
3. Understand the current architecture.
4. Explain major architectural changes before making them.

After completing a task:
1. Test the code.
2. Update this file.
3. Summarize files changed.
4. List remaining issues.
5. State the next concrete task.

Do not have Claude and Codex edit the same files simultaneously.

Use Git commits as handoff points.

## Current Task
Set up the shared Claude Code + OpenAI Codex workflow in VS Code.

## Next Task
Create a clean handoff between the existing Fly brain code and the Discord bot.

## Known Problems
None currently recorded.

## Last Change
GitHub repository initialized and pushed to origin/main.
Claude Code and OpenAI Codex extensions installed in VS Code.

## Notes
The project should remain lightweight.
The goal is a simulated fruit-fly brain inside Discord, with visible fly behavior and interactive commands.
