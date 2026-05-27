import sqlite3
import pandas as pd


def load_samples() -> pd.DataFrame:
    with sqlite3.connect("cell_counts.db") as conn:
        query = "SELECT * FROM samples"
        samples = pd.read_sql_query(query, conn)
    return samples


def create_cell_type_frequency_table():
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


def main():
    create_cell_type_frequency_table()


if __name__ == "__main__":
    main()
