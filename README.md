# MTAA Project - Backend

## Requirements
- [uv](https://docs.astral.sh/uv/) for Python package and environment management.


## General Workflow
By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From ./mtaa-backend/ you can install all the dependencies with:

```bash
$ uv sync
```
Then you can activate the virtual environment with:

```bash
$ source .venv/bin/activate
```
Run project with:

```bash
fastapi dev app/api/main.py
```