# Environment

This project uses **uv** for dependency management. 

- **Always** use `uv add <package>` to install dependencies, never `pip install`.
- **Always** use `uv run python <script>` to run scripts, never bare `python` or `python3`.
- Do NOT use Anaconda's Python at `/c/ProgramData/anaconda3/`. If a command falls back to it, that indicates a missing dependency in the uv environment that needs `uv add`.