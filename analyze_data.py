import sqlite3
import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from scipy import stats

sns.set_theme()


def load_samples() -> pd.DataFrame:
    with sqlite3.connect("cell_counts.db") as conn:
        query = "SELECT * FROM samples"
        samples = pd.read_sql_query(query, conn)
    return samples


def create_cell_type_frequency_table() -> pd.DataFrame:
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
    summary.to_csv("outputs/cell_type_frequency.csv")
    return summary


def load_miraclib_samples() -> pd.DataFrame:
    """Returns `sample` and `response` columns for subjects with melanoma that underwent miraclib treatment. Only considers PBMC samples."""
    with sqlite3.connect("cell_counts.db") as conn:
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
    # Get sample and response information
    samples = load_miraclib_samples()
    # Join with relative frequencies
    samples = samples.join(pops, on="sample")

    # Create boxplot
    fig, ax = plt.subplots(1, 1, figsize=(10, 8), dpi=200)

    sns.boxplot(ax=ax, data=samples, x="population", y="percentage", hue="response")
    ax.set_ylabel("Relative Frequency (%)")
    fig.suptitle("Cell Type Frequency for Miralib Responders and Non-Responders")
    fig.savefig("outputs/miraclib_effects.png")

    # Perform statistical analysis
    pct_df = samples.pivot(index=["response", "sample"], columns="population", values="percentage")
    by_response = pct_df.groupby(level="response")
    
    a = by_response.get_group("yes")
    b = by_response.get_group("no")
    
    result = stats.ttest_ind(a, b, axis=0)
    
    ALPHA = 0.05
    print("T-TEST RESULTS BY POPULATION")
    for cell_type, p in zip(a.columns, result.pvalue):
        if p < 0.05:
            print(f"SIGNIFICANT change in {cell_type} frequency (p={p})")
        else:
            print(f"NO significant change for {cell_type} (p={p})")
        



def main():
    pop_freqs = create_cell_type_frequency_table()
    analyze_miraclib(pop_freqs)


if __name__ == "__main__":
    main()
