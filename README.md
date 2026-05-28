# Teiko Technical

## Running the Code

Requires **Python 3.12+**. The environment was originally created with [uv](https://docs.astral.sh/uv/) - if the `make` commands fail to set up the environment, you can fall back to uv directly:

```bash
uv sync
```

Otherwise, use the Makefile targets:

```bash
make setup     # create .venv and install dependencies
make pipeline  # load data into SQLite and run analysis
make dashboard # start the Streamlit dashboard at http://localhost:8501
```

Each target must be run from the project root directory.

## Database Schema

The pipeline loads `cell-count.csv` into a SQLite database (`cell_counts.db`) with two tables.

### `subjects`

One row per patient. Stores subject-level metadata that is constant across time points.

| Column | Type | Description |
|---|---|---|
| `subject` | TEXT (PK) | Unique subject identifier |
| `project` | TEXT | Project the subject belongs to |
| `condition` | TEXT | Diagnosis (e.g. melanoma, carcinoma, healthy) |
| `age` | INTEGER | Subject age |
| `sex` | TEXT | Subject sex (M/F) |
| `treatment` | TEXT | Treatment administered (e.g. miraclib, phauximab, none) |
| `response` | TEXT | Treatment response (yes/no; NULL for healthy controls) |

### `samples`

One row per sample. Stores time-varying and sample-level measurements, with a foreign key back to `subjects`.

| Column | Type | Description |
|---|---|---|
| `sample` | TEXT (PK) | Unique sample identifier |
| `subject` | TEXT (FK) | References `subjects.subject` |
| `sample_type` | TEXT | Type of sample (e.g. PBMC) |
| `time_from_treatment_start` | INTEGER | Days since treatment began |
| `b_cell` | INTEGER | B cell count |
| `cd8_t_cell` | INTEGER | CD8+ T cell count |
| `cd4_t_cell` | INTEGER | CD4+ T cell count |
| `nk_cell` | INTEGER | NK cell count |
| `monocyte` | INTEGER | Monocyte count |

## Code Structure

The project is organized as three independent scripts, each responsible for a distinct stage of the pipeline:

- **`load_data.py`** - reads `cell-count.csv` and writes the normalized SQLite database. Run this first.
- **`analyze_data.py`** - queries the database, performs statistical analysis, and writes outputs to the `outputs/` directory.
- **`dashboard.py`** - a Streamlit app that queries the database directly and presents interactive visualizations of the analysis results.

These are kept as separate files because they are independent processes: the database only needs to be loaded once, analysis can be re-run without reloading, and the dashboard can be developed and iterated on independently. As the project scales, `analyze_data.py` and `dashboard.py` could each be split into multiple files (e.g. one module per analysis section) without changing the overall pipeline structure.

## Dashboard

Run `make dashboard` and open [http://localhost:8501](http://localhost:8501).
