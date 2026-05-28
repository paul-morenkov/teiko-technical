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

Each target must be run from the project root directory. All tables/figures are created in a new `outputs/` directory in the project root. Previous results from my local testing are available in `outputs.bak/`, in case anything fails.

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

### Rationale

The schema was created with `sqlite3`, without relying on a more sophisticated ORM such as `SQLAlchemy`, because the data structure is fairly simple, and `SQLAlchemy` would cause unnecessary overhead. `subjects` was decoupled from `samples` to normalize the schema and reduce repetition of information. `subjects` captures all information that is specific to the subject and that would be repeated across multiple samples for the same subject. All the columns from `cell-count.csv` were kept, in case future analysis requires it. As more information is added, these tables can be extended. Additionally, a `projects` table could be created to store project structure information as the number of projects/subjects grows. This schema should scale fairly well with the number of projects/samples/treatments/conditions. Since each cell population type is a separate column, it is easy to add additional fields as the test panel capabilities improve. Joins from `subjects` (or `projects` in the future) can easily filter `samples` down to manageable row numbers for any particular analysis. With 100s of projects and 1,000s of samples there will be ~millions of rows, which will still be incredibly performant for any subsetting operations. However, as the database size scales it would make sense to switch from sqlite3 to a dedicated server-based SQL provider.
Any additional information (e.g. relative frequency) can be inexpensively computed from the 5 cell populations, so there is no point in storing that as additional fields in the database. Most fields allow null values to minimize assumptions about experimental data.

## Code Structure

The project is organized as three independent scripts, each responsible for a distinct stage of the pipeline:

- **`load_data.py`** - reads `cell-count.csv` and writes the normalized SQLite database. Run this first.
- **`analyze_data.py`** - queries the database, performs statistical analysis, and writes outputs to the `outputs/` directory.
- **`dashboard.py`** - a Streamlit app that queries the database directly and presents interactive visualizations of the analysis results.

These are kept as separate files because they are independent processes: the database only needs to be loaded once, analysis can be re-run without reloading, and the dashboard can be developed and iterated on independently. As the project scales, `analyze_data.py` and `dashboard.py` could each be split into multiple files (e.g. one module per analysis section) without changing the overall pipeline structure.

## Dashboard

Run `make dashboard` and open [http://localhost:8501](http://localhost:8501).
