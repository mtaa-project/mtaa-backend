# MTAA Project - Backend

## Requirements
- [uv](https://docs.astral.sh/uv/) for Python package and environment management.

## Documentation
The API documentation is hosted at [https://mtaa-project.github.io/mtaa-backend/](https://mtaa-project.github.io/mtaa-backend/) and the source files can be found in the [`docs`](./docs/index.html) directory.

## General Workflow
By default, the dependencies are managed with [uv](https://docs.astral.sh/uv/), go there and install it.

From ./mtaa-backend/ you can install all the dependencies with:

```bash
uv sync
```
Then you can activate the virtual environment with:

```bash
source .venv/bin/activate
```
Run project with:

```bash
fastapi dev app/api/main.py
```


## Running Seeders

Seeders are used to populate the database with initial data. You can run seeders individually or all at once.

### Run a Single Seeder

To run a single seeder, use the following command, replacing `module_name` with the specific seeder module you want to run:

```bash
python -m app.seeders.module_name
```

For example, to run the `1_users` seeder:

```bash
python -m app.seeders.1_users
```

### Run All Seeders

To run all seeders in the predefined order, use the following command:

```bash
python app/seeders/run_all_seeders.py
```

This will execute all seeders in sequence, stopping if any seeder fails.


## Running Tests

Automated tests are located in the [`app/tests/`](./app/tests) directory. They are written using `pytest` and `pytest-asyncio`.

### Run Tests with uv (recommended)

```bash
uv run pytest
```

### CI Integration
Tests are automatically executed on push and pull requests to the main branch via GitHub Actions.
You can find the workflow definition in [.github/workflows](.github/workflows/pytest.yml).
