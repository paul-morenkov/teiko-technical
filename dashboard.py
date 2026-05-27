import sqlite3

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
import streamlit as st
from scipy import stats

DB_PATH = "cell_counts.db"
CELL_TYPES = ["b_cell", "cd8_t_cell", "cd4_t_cell", "nk_cell", "monocyte"]

sns.set_theme()

st.set_page_config(page_title="Cell Count Analysis", layout="wide")
st.title("Immune Cell Expression Analysis")


@st.cache_data
def load_data():
    with sqlite3.connect(DB_PATH) as conn:
        subjects = pd.read_sql_query("SELECT * FROM subjects", conn)
        samples = pd.read_sql_query("SELECT * FROM samples", conn)
    full = subjects.merge(samples, on="subject")
    full["total_cells"] = full[CELL_TYPES].sum(axis=1)
    for ct in CELL_TYPES:
        full[f"{ct}_pct"] = full[ct] * 100 / full["total_cells"]
    return full


PCT_COLS = [f"{ct}_pct" for ct in CELL_TYPES]
CELL_LABELS = {f"{ct}_pct": ct for ct in CELL_TYPES}

full = load_data()

tab2, tab3, tab4 = st.tabs(
    ["Part 2: Cell Type Frequencies", "Part 3: Miraclib Analysis", "Part 4: Subset Analysis"]
)

# ── Part 2: Cell Type Frequency Overview ──────────────────────────────────────
with tab2:
    st.header("Cell Type Frequency Overview")

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        sel_conditions = st.multiselect(
            "Condition", sorted(full["condition"].unique()), default=sorted(full["condition"].unique())
        )
    with col2:
        sel_treatments = st.multiselect(
            "Treatment", sorted(full["treatment"].unique()), default=sorted(full["treatment"].unique())
        )
    with col3:
        sel_times = st.multiselect(
            "Time from Treatment Start",
            sorted(full["time_from_treatment_start"].unique()),
            default=sorted(full["time_from_treatment_start"].unique()),
        )
    with col4:
        sel_types = st.multiselect(
            "Sample Type", sorted(full["sample_type"].unique()), default=sorted(full["sample_type"].unique())
        )

    filtered = full[
        full["condition"].isin(sel_conditions)
        & full["treatment"].isin(sel_treatments)
        & full["time_from_treatment_start"].isin(sel_times)
        & full["sample_type"].isin(sel_types)
    ]

    melted = filtered[["sample"] + PCT_COLS].melt(
        id_vars="sample", value_vars=PCT_COLS, var_name="population", value_name="percentage"
    )
    melted["population"] = melted["population"].map(CELL_LABELS)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.boxplot(data=melted, x="population", y="percentage", ax=ax)
    ax.set_xlabel("Cell Type")
    ax.set_ylabel("Relative Frequency (%)")
    ax.set_title(f"Cell Type Frequency Distribution ({len(filtered)} samples)")
    st.pyplot(fig)
    plt.close()

    st.subheader("Summary Statistics")
    summary = (
        melted.groupby("population")["percentage"]
        .describe()
        .round(2)
        .rename(columns={"count": "n_samples"})
    )
    st.dataframe(summary, use_container_width=True)

# ── Part 3: Miraclib Responder Analysis ───────────────────────────────────────
with tab3:
    st.header("Miraclib Responder Analysis")
    st.caption("Melanoma patients treated with miraclib — PBMC samples, all time points")

    miraclib = full[
        (full["condition"] == "melanoma")
        & (full["treatment"] == "miraclib")
        & (full["sample_type"] == "PBMC")
    ].copy()

    melted_m = miraclib[["sample", "response"] + PCT_COLS].melt(
        id_vars=["sample", "response"], value_vars=PCT_COLS, var_name="population", value_name="percentage"
    )
    melted_m["population"] = melted_m["population"].map(CELL_LABELS)

    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(data=melted_m, x="population", y="percentage", hue="response", ax=ax)
    ax.set_ylabel("Relative Frequency (%)")
    ax.set_title("Cell Type Frequency: Miraclib Responders vs Non-Responders")
    st.pyplot(fig)
    plt.close()

    yes_group = miraclib[miraclib["response"] == "yes"][PCT_COLS]
    no_group = miraclib[miraclib["response"] == "no"][PCT_COLS]
    result = stats.ttest_ind(yes_group, no_group)

    stat_df = pd.DataFrame(
        {
            "Cell Type": CELL_TYPES,
            "p-value": result.pvalue.round(4),
            "Significant (α=0.05)": result.pvalue < 0.05,
        }
    )

    st.subheader("Independent t-test: Responders vs Non-Responders")

    def highlight_significant(row):
        color = "background-color: #d4edda" if row["Significant (α=0.05)"] else ""
        return [color] * len(row)

    st.dataframe(
        stat_df.style.apply(highlight_significant, axis=1),
        use_container_width=True,
        hide_index=True,
    )

# ── Part 4: Subset Analysis ───────────────────────────────────────────────────
with tab4:
    st.header("Baseline Subset Analysis")
    st.caption("Melanoma patients treated with miraclib — PBMC samples at time = 0")

    baseline = full[
        (full["condition"] == "melanoma")
        & (full["treatment"] == "miraclib")
        & (full["sample_type"] == "PBMC")
        & (full["time_from_treatment_start"] == 0)
    ]

    avg_b = baseline[(baseline["response"] == "yes") & (baseline["sex"] == "M")]["b_cell"].mean()

    m1, m2 = st.columns(2)
    m1.metric("Total Baseline Samples", len(baseline))
    m2.metric("Avg B Cells — Male Responders (baseline)", f"{avg_b:.2f}")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Samples per Project")
        per_proj = baseline.groupby("project").size().rename("count")
        fig, ax = plt.subplots(figsize=(6, 4))
        per_proj.plot(kind="bar", ax=ax, color=sns.color_palette()[0])
        ax.set_xlabel("Project")
        ax.set_ylabel("Sample Count")
        ax.tick_params(axis="x", rotation=0)
        st.pyplot(fig)
        plt.close()

    with col2:
        st.subheader("Sex × Response Crosstab")
        crosstab = pd.crosstab(baseline["response"], baseline["sex"], margins=True)
        st.dataframe(crosstab, use_container_width=True)
