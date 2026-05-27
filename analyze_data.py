import sqlite3
import pandas as pd
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # Allow rendering for headless environments

import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats

sns.set_theme()
DB_PATH = "cell_counts.db"

def prep_outputs_dir():
    """Create output directories and subdirectories if they don't yet exist."""
    outputs = Path.cwd() / "outputs"
    for i in (2, 3, 4):
        subdir = outputs / f"part_{i}"
        subdir.mkdir(parents=True, exist_ok=True)


def load_samples() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        query = "SELECT * FROM samples"
        samples = pd.read_sql_query(query, conn)
    return samples


def create_cell_type_frequency_table() -> pd.DataFrame:
    print("### Part 2: Data Overview ###")
    print("Results are in `outputs/part_2`\n")
    samples = load_samples()

    samples = samples[
        ["sample", "b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]
    ].set_index("sample")

    pops = samples.melt(var_name="population", value_name="count", ignore_index=False)
    pops["total_count"] = pops.groupby("sample")["count"].sum()
    pops["percentage"] = pops["count"] * 100 / pops["total_count"]
    pops["percentage"] = pops["percentage"].round(2)
    summary = pops[["total_count", "population", "count", "percentage"]].sort_values(
        ["sample", "population"]
    )
    summary.to_csv("outputs/part_2/cell_type_frequency.csv")
    return summary


def load_miraclib_samples() -> pd.DataFrame:
    """Returns `sample` and `response` columns for subjects with melanoma that underwent miraclib treatment. Only considers PBMC samples."""
    with sqlite3.connect(DB_PATH) as conn:
        query = """SELECT samples.sample, subjects.response 
        FROM subjects 
        INNER JOIN samples
            ON samples.subject = subjects.subject 
        WHERE condition = "melanoma"
            AND treatment = "miraclib" 
            AND sample_type = "PBMC"
        """

        samples = pd.read_sql_query(query, conn)

    return samples


def analyze_miraclib(pops: pd.DataFrame):
    print("### Part 3: Analyzing Miraclib ###")
    print("Results are in `outputs/part_3`\n")
    # Get sample and response information
    samples = load_miraclib_samples()
    # Join with relative frequencies
    samples = samples.join(pops, on="sample")

    # Create boxplot
    fig, ax = plt.subplots(1, 1, figsize=(10, 8), dpi=200)

    sns.boxplot(ax=ax, data=samples, x="population", y="percentage", hue="response")
    ax.set_ylabel("Relative Frequency (%)")
    fig.suptitle("Cell Type Frequency for Miralib Responders and Non-Responders")
    fig.savefig("outputs/part_3/miraclib_effects.png")

    # Perform statistical analysis
    pct_df = samples.pivot(
        index=["response", "sample"], columns="population", values="percentage"
    )
    by_response = pct_df.groupby(level="response")

    a = by_response.get_group("yes")
    b = by_response.get_group("no")

    result = stats.ttest_ind(a, b, axis=0)

    ALPHA = 0.05

    stat_df = pd.DataFrame(
        {
            "cell_type": a.columns.to_list(),
            "p_value": result.pvalue,
        }
    )
    stat_df["significant"] = stat_df["p_value"] < ALPHA
    stat_df.to_csv("outputs/part_3/t_test_results.csv", index=False)
    print(stat_df)
    print()

    print("CELL TYPES WITH SIGNIFICANT CHANGE:\n")
    for cell_type, p in zip(a.columns, result.pvalue):
        if p < 0.05:
            print(f"SIGNIFICANT change in {cell_type} frequency (p={p:.4f})")


def analyze_subsets():

    print("### Part 4: Analyzing Subsets ###")
    print("Results are in `outputs/part_4`\n")

    query = """SELECT *
    FROM subjects
    INNER JOIN samples
        ON subjects.subject = samples.subject
    WHERE condition = "melanoma" 
        AND treatment = "miraclib"
        AND sample_type = "PBMC"
        AND time_from_treatment_start = 0
    """
    with sqlite3.connect(DB_PATH) as conn:
        baseline = pd.read_sql_query(query, conn)

    print(f"There are {len(baseline)} baseline samples.")

    # Remaining subqueries can be grouped/filtered from DataFrame; don't need to reaccess the DB

    samples_per_proj = baseline.groupby("project").size()
    samples_per_proj.to_csv("outputs/part_4/samples_per_project.csv")
    print("Samples per project: ")
    print(samples_per_proj)
    print()

    sex_and_response = pd.crosstab(baseline["response"], baseline["sex"], margins=True)
    sex_and_response.to_csv("outputs/part_4/sex_and_response.csv")
    print(sex_and_response)

def calculate_avg_b_cells():
    query = """SELECT AVG(b_cell) as avg_b_cells
    FROM subjects
    INNER JOIN samples
        ON subjects.subject = samples.subject
    WHERE condition = "melanoma" 
        AND treatment = "miraclib"
        AND response = "yes"
        AND sample_type = "PBMC"
        AND time_from_treatment_start = 0
        AND sex = "M"
    """

    with sqlite3.connect(DB_PATH) as conn:
        avg_b_cells = pd.read_sql_query(query, conn)

    assert len(avg_b_cells) == 1
    avg_b_cells = avg_b_cells.loc[0, "avg_b_cells"]

    print()
    
    print(f"Average B Cells for male melanoma miraclib responders (time=0, sample_type=PBMC): {avg_b_cells:.2f}")


def main():
    prep_outputs_dir()
    pop_freqs = create_cell_type_frequency_table()
    analyze_miraclib(pop_freqs)
    analyze_subsets()
    calculate_avg_b_cells()


if __name__ == "__main__":
    main()
