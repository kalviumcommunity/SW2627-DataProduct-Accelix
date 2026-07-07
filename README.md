# SW2627-DataProduct-Accelix

This workspace is set up as a reproducible Python data-project scaffold. It includes an isolated virtual environment pattern, pinned dependencies, a standard folder layout, and a notebook lesson covering the setup process.

## Setup

1. Create a virtual environment.

	```bash
	python -m venv venv
	```

2. Activate it.

	```bash
	# Windows PowerShell
	venv\Scripts\Activate.ps1
	```

3. Install dependencies.

	```bash
	pip install -r requirements.txt
	```

4. Copy the environment template if you need secrets or configuration.

	```bash
	copy .env.example .env
	```

## Project Structure

- `data/raw/` for source data that is never modified in place
- `data/processed/` for cleaned and transformed data
- `notebooks/` for exploration and reporting notebooks
- `scripts/` for repeatable Python automation
- `output/` for generated reports, figures, and exports

## Files In This Workspace

- `development_environment_workspace_setup.ipynb` contains the lesson content for the assignment
- `notebooks/github_repository_team_workflow_setup.ipynb` contains the GitHub workflow lesson
- `.gitignore` excludes virtual environments, secrets, caches, and generated artifacts
- `requirements.txt` pins the project dependencies
- `.env.example` documents required environment variables without exposing secrets

## Notes

- Do not commit `venv/` or `.env`.
- Regenerate `requirements.txt` with `pip freeze > requirements.txt` after dependency changes.
- Keep notebooks exploratory and move reusable logic into scripts.