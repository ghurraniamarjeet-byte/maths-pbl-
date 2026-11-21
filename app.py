"""app.py
------
Main Streamlit app. Run karne ke liye:  streamlit run app.py
"""
import numpy as np
import pandas as pd
import streamlit as st

import data
import plots
from chi_utils import run_test, get_critical, get_p_value

# ----------------------------------------------------------------------
# PAGE SETUP + CSS
# ----------------------------------------------------------------------
st.set_page_config(page_title="Chi-Square PBL", page_icon="📊", layout="wide")

st.markdown("""
<style>
h1, h2, h3 { color: #1B1F4B; }
[data-testid="stMetric"] {
    background: #EEF0FA; border-radius: 12px; padding: 14px 18px; border: 1px solid #D5D8EE;
}
[data-testid="stMetricLabel"] { color: #3A3F7A; }
[data-testid="stMetricValue"] { color: #1B1F4B; }
.hero { background: #1B1F4B; color: white; padding: 28px 32px; border-radius: 16px; margin-bottom: 18px; }
.hero h1 { color: white; margin: 0; font-size: 2rem; }
.hero p { color: #CADCFC; margin: 6px 0 0 0; font-size: 1.1rem; }
.pill { display:inline-block; background:#1FA99A; color:white; padding:3px 12px; border-radius:20px; font-size:0.85rem; }
@media (max-width: 640px) { .hero h1 { font-size: 1.4rem; } }
</style>
""", unsafe_allow_html=True)


# ----------------------------------------------------------------------
# SMALL HELPERS (naye aur purane Streamlit versions dono ke liye)
# ----------------------------------------------------------------------
def show_plot(fig, key=None):
    try:
        st.plotly_chart(fig, width="stretch", key=key)
    except TypeError:
        st.plotly_chart(fig, use_container_width=True, key=key)


def show_df(obj):
    try:
        st.dataframe(obj, width="stretch")
    except (TypeError, ValueError):
        st.dataframe(obj, use_container_width=True)


def with_totals(obs: pd.DataFrame) -> pd.DataFrame:
    t = obs.copy()
    t["Total"] = t.sum(axis=1)
    t.loc["Total"] = t.sum(axis=0)
    return t.astype(int)


def decision_text(res, name=""):
    rel = "lies in the REJECTION region" if res["reject"] else "lies in the ACCEPTANCE region"
    act = "we REJECT H0 (usage and marks are associated)" if res["reject"] \
        else "we FAIL TO REJECT H0 (no significant association found)"
    return (f"Calculated chi2 ({res['chi2']:.2f}) {rel} (critical value = {res['critical']:.3f}, "
            f"p = {res['p']:.4f}), so {act}.")


def decision_box(res):
    (st.error if res["reject"] else st.success)(decision_text(res))


# ----------------------------------------------------------------------
# DATA LOADING (default ya uploaded CSV)
# ----------------------------------------------------------------------
@st.cache_data
def load_uploaded(file_bytes: bytes) -> pd.DataFrame:
    import io
    return data.table_from_csv(pd.read_csv(io.BytesIO(file_bytes)))


st.sidebar.title("📊 Chi-Square PBL")
PAGES = ["🏠 Home", "📘 Introduction", "📝 Data Collection", "🔢 Observed & Expected",
         "🧮 Step-by-Step Calculation", "📉 Rejection Region Diagram", "📊 Graphs", "✅ Conclusion"]
page = st.sidebar.radio("Go to page", PAGES)

st.sidebar.markdown("---")
st.sidebar.subheader("Data source")
uploaded = st.sidebar.file_uploader("Upload your own CSV (columns: Usage, Marks)", type="csv")
st.sidebar.download_button("⬇️ Download CSV template (current data)", data.template_csv_bytes(),
                           file_name="survey_template.csv", mime="text/csv")

table4 = data.default_table_4x4()
data_note = "Using the original survey data."
if uploaded is not None:
    try:
        table4 = load_uploaded(uploaded.getvalue())
        data_note = "Using YOUR uploaded CSV data."
        st.sidebar.success(f"Loaded {int(table4.values.sum())} responses.")
    except Exception as e:  # koi bhi galti ho to user ko dikhao, app band mat karo
        st.sidebar.error(f"Could not read file: {e}")

TABLES = data.get_all_tables(table4)
obs3, obs2 = TABLES["3x3 (merged, main test)"], TABLES["2x2 (extra check)"]
N = int(table4.values.sum())

# ----------------------------------------------------------------------
# EXTRA FEATURE: INTERACTIVE CALCULATOR (sidebar)
# ----------------------------------------------------------------------
with st.sidebar.expander("🧮 Interactive Chi-Square Calculator"):
    c1, c2 = st.columns(2)
    r = int(c1.number_input("Rows", 2, 6, 2, key="calc_r"))
    c = int(c2.number_input("Columns", 2, 6, 2, key="calc_c"))
    if (r, c) == (2, 2):
        start = [[20, 30], [30, 20]]
    else:
        start = [[10 + i + j for j in range(c)] for i in range(r)]
    base = pd.DataFrame(start, index=[f"Row {i+1}" for i in range(r)],
                        columns=[f"Col {j+1}" for j in range(c)])
    edited = st.data_editor(base, key=f"calc_editor_{r}_{c}")
    calc_alpha = st.select_slider("Significance level", [0.01, 0.05, 0.10], value=0.05, key="calc_alpha")
    try:
        cres = run_test(edited.apply(pd.to_numeric), calc_alpha)
        m1, m2 = st.columns(2)
        m1.metric("Chi2", f"{cres['chi2']:.3f}")
        m2.metric("df", cres["df"])
        m3, m4 = st.columns(2)
        m3.metric("p-value", f"{cres['p']:.4f}")
        m4.metric("Critical", f"{cres['critical']:.3f}")
        (st.error if cres["reject"] else st.success)("Reject H0" if cres["reject"] else "Fail to reject H0")
        show_plot(plots.rejection_region_fig(cres["chi2"], cres["df"], calc_alpha, height=340,
                                             title="Your table"), key="calc_plot")
    except Exception as e:
        st.warning(f"Enter valid counts: {e}")

st.sidebar.caption(data_note)


# ----------------------------------------------------------------------
# PAGES
# ----------------------------------------------------------------------
def page_home():
    st.markdown(f"""<div class="hero"><span class="pill">Maths PBL</span>
        <h1>{data.PROJECT_TITLE}</h1><p>{data.PROJECT_SUBTITLE}</p></div>""", unsafe_allow_html=True)
    m1, m2, m3 = st.columns(3)
    m1.metric("Sample size", N)
    m2.metric("Significance level", "0.05")
    m3.metric("Test", "Chi-Square")

    left, right = st.columns([3, 2])
    with left:
        st.subheader("Team Members")
        team_df = pd.DataFrame(data.TEAM, columns=["Name", "Roll No"])
        team_df.index = np.arange(1, len(team_df) + 1)
        show_df(team_df)
    with right:
        st.subheader("Project Details")
        st.markdown(f"**Subject:** {data.SUBJECT}  \n**Class:** {data.CLASS_NAME}  \n"
                    f"**Teacher:** {data.TEACHER}  \n**Date:** {data.SUBMISSION_DATE}")


def page_intro():
    st.header("Introduction and Objective")
    a, b = st.columns(2)
    with a:
        st.subheader("What is the Chi-Square Test of Independence?")
        st.write("It is a statistical test that checks whether two **categorical variables** are related "
                 "to each other or not. It compares what we actually **observed** in the survey with what "
                 "we would **expect** if the two variables had no relationship at all.")
        st.subheader("When do we use it?")
        st.markdown("- Both variables are categories (e.g. Low / Medium / High)\n"
                    "- Data is in counts (number of students), not percentages\n"
                    "- Each person belongs to exactly one cell\n"
                    "- Expected count in each cell should be at least 5")
    with b:
        st.subheader("Objective")
        st.write("To test whether students' **daily social media usage** and their **academic performance** "
                 "(last exam marks) are related, using the chi-square test of independence.")
        st.subheader("Hypotheses")
        st.info("**H0 (Null):** Social media usage and academic performance are independent.")
        st.warning("**H1 (Alternative):** They are dependent (associated).")
    st.subheader("Formulas")
    f1, f2, f3 = st.columns(3)
    f1.latex(r"\chi^2 = \sum \frac{(O - E)^2}{E}")
    f2.latex(r"E = \frac{\text{Row total} \times \text{Column total}}{\text{Grand total}}")
    f3.latex(r"df = (r - 1)(c - 1)")


def page_data():
    st.header("Data Collection")
    st.write("We collected data with an **anonymous Google Form** using multiple-choice questions:")
    st.markdown("1. *How much time do you spend on social media daily?*\n"
                "2. *What were your marks in the last exam / semester?*")
    m1, m2 = st.columns(2)
    m1.metric("Responses used", N)
    m2.metric("Form type", "Anonymous MCQ")

    choice = st.radio("Show table", ["4x4 (original)", "3x3 (merged)"], horizontal=True, key="data_toggle")
    if choice.startswith("4x4"):
        show_df(with_totals(table4))
    else:
        show_df(with_totals(obs3))
    st.info("**Why did we merge categories?** In the original 4x4 table many cells have an expected "
            "frequency below 5, which makes the chi-square test unreliable. So we merged neighbouring "
            "categories into a 3x3 table (Medium = 2-6 hrs, Below 70% = under 50% + 50-70%).")
    r4 = run_test(table4)
    st.caption(f"4x4 table: {r4['cells_below_5']} of 16 cells have expected frequency below 5.")


def page_obs_exp():
    st.header("Observed and Expected Frequencies")
    res = run_test(obs3)
    a, b = st.columns(2)
    with a:
        st.subheader("Observed (O)")
        show_df(with_totals(obs3))
    with b:
        st.subheader("Expected (E)")
        show_df(res["expected"].style.format("{:.3f}"))
    rt = int(obs3.iloc[0].sum())
    ct = int(obs3.iloc[:, 0].sum())
    st.subheader("Worked example (first cell)")
    st.latex(rf"E_{{11}} = \frac{{{rt} \times {ct}}}{{{N}}} = {res['expected'].iloc[0, 0]:.3f}")
    if res["cells_below_5"] == 0:
        st.success("All expected frequencies are 5 or more, so the test conditions are satisfied.")
    else:
        st.warning(f"{res['cells_below_5']} of {obs3.size} cells have expected frequency below 5 "
                   f"(smallest = {res['min_expected']:.2f}). Interpret the result with caution; "
                   "we also run a 2x2 check where all values are above 5.")


def page_calc():
    st.header("Step-by-Step Calculation (3x3 table)")
    alpha = st.select_slider("Significance level (alpha)", [0.01, 0.05, 0.10], value=0.05,
                             format_func=lambda a: f"{a:.2f}", key="calc_page_alpha")
    res = run_test(obs3, alpha)
    st.markdown("#### Step 1: Formula")
    st.latex(r"\chi^2 = \sum \frac{(O - E)^2}{E}")
    st.markdown("#### Step 2: Degrees of freedom")
    st.latex(rf"df = (3-1)(3-1) = {res['df']}")
    st.markdown("#### Step 3: Critical value")
    st.write(f"At alpha = {alpha:.2f} and df = {res['df']}, the critical value is **{res['critical']:.3f}**.")
    st.markdown("#### Step 4: Calculated chi-square")
    contrib = res["contrib"]
    thr = np.sort(contrib.values.ravel())[-2]  # sabse bade 2 cells highlight

    def highlight(df_):
        return pd.DataFrame(np.where(df_.values >= thr, "background-color:#F2545B;color:white;font-weight:bold", ""),
                            index=df_.index, columns=df_.columns)

    show_df(contrib.style.format("{:.3f}").apply(highlight, axis=None))
    st.caption("Highlighted cells contribute the most to the chi-square value.")
    st.latex(rf"\chi^2 = {res['chi2']:.3f}")
    m1, m2, m3 = st.columns(3)
    m1.metric("Calculated chi2", f"{res['chi2']:.3f}")
    m2.metric("Critical value", f"{res['critical']:.3f}")
    m3.metric("p-value", f"{res['p']:.4f}")
    st.markdown("#### Step 5: Decision")
    st.write("Reject H0 if calculated chi2 > critical value (or p < alpha).")
    decision_box(res)
    if res["verified"]:
        st.success("✅ Verified with scipy (chi2_contingency gives the same answer).")
    else:
        st.warning("scipy result differs from the manual calculation - please check the data.")


def page_rejection():
    st.header("Rejection Region Diagram")
    c1, c2, c3 = st.columns(3)
    which = c1.selectbox("Table", list(TABLES.keys()), key="rej_table")
    alpha = c2.select_slider("alpha", [0.01, 0.05, 0.10], value=0.05, key="rej_alpha")
    show_p = c3.toggle("Show p-value area", value=False, key="rej_p")
    res = run_test(TABLES[which], alpha)
    show_plot(plots.rejection_region_fig(res["chi2"], res["df"], alpha, show_p), key="rej_plot")
    decision_box(res)
    if res["cells_below_5"] > 0:
        st.caption(f"Note: {res['cells_below_5']} cell(s) in this table have expected frequency below 5, "
                   "so treat this result with caution.")
    with st.expander("How to read this diagram"):
        st.markdown(
            "- The curve shows how chi-square values behave **if H0 is true** (no relation).\n"
            "- The **red area** (right tail) is the rejection region. It starts at the critical value and "
            "has area = alpha.\n"
            "- If our **calculated chi2 (black line)** falls in the red area, we reject H0; "
            "if it falls in the blue area, we fail to reject H0.")


def page_graphs():
    st.header("Graphs (3x3 table)")
    tabs = st.tabs(["Stacked bar", "100% stacked", "Clustered bar", "Heatmap", "Pie chart"])
    res = run_test(obs3)
    with tabs[0]:
        show_plot(plots.stacked_bar(obs3), key="g1")
    with tabs[1]:
        show_plot(plots.percent_stacked_bar(obs3), key="g2")
    with tabs[2]:
        show_plot(plots.clustered_bar(obs3), key="g3")
    with tabs[3]:
        show_plot(plots.heatmap_obs_exp(obs3, res["expected"]), key="g4")
    with tabs[4]:
        show_plot(plots.usage_pie(obs3), key="g5")


def page_conclusion():
    st.header("Conclusion")
    r3, r2 = run_test(obs3), run_test(obs2)
    low = obs3.iloc[0, 2] / obs3.iloc[0].sum() * 100
    high = obs3.iloc[2, 2] / obs3.iloc[2].sum() * 100
    m1, m2, m3 = st.columns(3)
    m1.metric("Low usage scoring 80%+", f"{low:.0f}%")
    m2.metric("High usage scoring 80%+", f"{high:.0f}%")
    m3.metric("Sample size", N)

    st.subheader("3x3 test (main)")
    st.write(f"chi2 = {r3['chi2']:.2f}, df = {r3['df']}, critical = {r3['critical']:.3f}, p = {r3['p']:.4f}")
    decision_box(r3)
    st.subheader("2x2 check (usage under 4 hrs vs 4 hrs or more; marks under 80% vs 80%+)")
    st.write(f"chi2 = {r2['chi2']:.2f}, df = {r2['df']}, critical = {r2['critical']:.3f}, p = {r2['p']:.4f}, "
             f"Cramer's V = {r2['cramers_v']:.2f}")
    decision_box(r2)

    if r3["reject"] != r2["reject"]:
        st.info("**Honest note:** the two groupings give different decisions, so the result depends on how "
                "categories are grouped. Still, the trend is consistent: students with more social media "
                "time have fewer high scores.")
    else:
        st.info("Both groupings lead to the same decision, which makes the result more reliable.")

    a, b = st.columns(2)
    with a:
        st.subheader("Limitations")
        st.markdown("- Small sample size\n- Almost all respondents are 2nd-year students\n"
                    "- Self-reported data\n- Association is not causation")
    with b:
        st.subheader("Suggestions")
        st.markdown("- Set a daily screen-time limit\n- Plan fixed study hours before scrolling time\n"
                    "- Use social media for learning and study resources")
    st.success("Thank you! 🙏")


{"🏠 Home": page_home, "📘 Introduction": page_intro, "📝 Data Collection": page_data,
 "🔢 Observed & Expected": page_obs_exp, "🧮 Step-by-Step Calculation": page_calc,
 "📉 Rejection Region Diagram": page_rejection, "📊 Graphs": page_graphs,
 "✅ Conclusion": page_conclusion}[page]()
