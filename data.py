"""
data.py
-------
Yahan project ki saari details aur survey ka data store hai.
Team members, teacher ka naam, date wagairah sirf yahin se badalna hai.
"""
import io
import numpy as np
import pandas as pd

# ----------------------------------------------------------------------
# 1) PROJECT DETAILS  (apne hisaab se edit karo)
# ----------------------------------------------------------------------
PROJECT_TITLE = "Statistical Analysis of Social Media Usage vs Academic Performance"
PROJECT_SUBTITLE = "Using the Chi-Square Test of Independence"

TEAM = [  # (name, roll no)
    ("Amarjeet Singh Ghurrani", "05"),
    ("Rohit Kumar", "41"),
    ("Anand Raj", "08"),
    ("Shaurya Vishwakarma", "44"),
    ("Prince Yadav", "34"),
    ("Shailendra Prajapati", "43"),
    ("Vicky Verma", "57"),
    ("Anurag Pal", "16"),
    ("Rajan Singh", "40"),
    ("Nitin Yadav", "Lateral"),
    ("Vivek Yadav", "60"),
]
SUBJECT = "Mathematics / Statistics (PBL)"
TEACHER = "Mamta Dasani"      # <-- badlo
CLASS_NAME = "AI/ML"   # <-- badlo
SUBMISSION_DATE = "23 Monday Nov 2026"           # <-- badlo (e.g. "24 Nov 2026")

# ----------------------------------------------------------------------
# 2) LABELS
# ----------------------------------------------------------------------
USAGE_4 = ["Less than 2 hrs", "2 to 4 hrs", "4 to 6 hrs", "More than 6 hrs"]
MARKS_4 = ["Below 50%", "50-70%", "70-80%", "80%+"]

USAGE_3 = ["Low (<2 hrs)", "Medium (2-6 hrs)", "High (6+ hrs)"]
MARKS_3 = ["Below 70%", "70-80%", "80%+"]

USAGE_2 = ["Under 4 hrs", "4 hrs or more"]
MARKS_2 = ["Below 80%", "80%+"]

# ----------------------------------------------------------------------
# 3) REAL SURVEY DATA (n = 42) - original 4x4 table
# ----------------------------------------------------------------------
_DEFAULT_4x4 = [
    [0, 2, 3, 8],   # Less than 2 hrs
    [0, 0, 2, 3],   # 2 to 4 hrs
    [0, 4, 5, 3],   # 4 to 6 hrs
    [1, 3, 7, 1],   # More than 6 hrs
]


def default_table_4x4() -> pd.DataFrame:
    return pd.DataFrame(_DEFAULT_4x4, index=USAGE_4, columns=MARKS_4)


# ----------------------------------------------------------------------
# 4) MERGING FUNCTIONS (4x4 -> 3x3 and 4x4 -> 2x2)
# ----------------------------------------------------------------------
def merge_to_3x3(t4: pd.DataFrame) -> pd.DataFrame:
    """Usage: 2-4 aur 4-6 ko Medium banao. Marks: <50 aur 50-70 ko 'Below 70%' banao."""
    v = t4.values
    usage_merged = np.vstack([v[0], v[1] + v[2], v[3]])
    marks_merged = np.column_stack([usage_merged[:, 0] + usage_merged[:, 1],
                                    usage_merged[:, 2], usage_merged[:, 3]])
    return pd.DataFrame(marks_merged, index=USAGE_3, columns=MARKS_3)


def merge_to_2x2(t4: pd.DataFrame) -> pd.DataFrame:
    """Usage: under 4 hrs vs 4 hrs or more. Marks: below 80% vs 80%+."""
    v = t4.values
    usage = np.vstack([v[0] + v[1], v[2] + v[3]])
    marks = np.column_stack([usage[:, 0] + usage[:, 1] + usage[:, 2], usage[:, 3]])
    return pd.DataFrame(marks, index=USAGE_2, columns=MARKS_2)


def get_all_tables(t4: pd.DataFrame) -> dict:
    """Teeno tables ek dictionary me."""
    return {
        "3x3 (merged, main test)": merge_to_3x3(t4),
        "2x2 (extra check)": merge_to_2x2(t4),
        "4x4 (original)": t4,
    }


# ----------------------------------------------------------------------
# 5) CSV SUPPORT (naye real responses add karne ke liye)
# ----------------------------------------------------------------------
def table_to_rows(t4: pd.DataFrame) -> pd.DataFrame:
    """4x4 table ko 'ek student = ek row' wale format me badlo (template CSV ke liye)."""
    rows = []
    for u in t4.index:
        for m in t4.columns:
            rows += [(u, m)] * int(t4.loc[u, m])
    return pd.DataFrame(rows, columns=["Usage", "Marks"])


def template_csv_bytes() -> bytes:
    buf = io.StringIO()
    table_to_rows(default_table_4x4()).to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")


def table_from_csv(raw: pd.DataFrame) -> pd.DataFrame:
    """
    Uploaded CSV (columns: Usage, Marks) se 4x4 contingency table banao.
    Errors ValueError ke roop me raise hote hain (app unhe dikha deta hai).
    """
    if raw is None or raw.empty:
        raise ValueError("The uploaded file is empty.")
    raw = raw.rename(columns=lambda c: str(c).strip())
    if not {"Usage", "Marks"}.issubset(raw.columns):
        raise ValueError("CSV must have two columns named exactly 'Usage' and 'Marks'.")
    raw = raw[["Usage", "Marks"]].dropna()
    raw["Usage"] = raw["Usage"].astype(str).str.strip()
    raw["Marks"] = raw["Marks"].astype(str).str.strip()
    if raw.empty:
        raise ValueError("No valid rows found in the file.")
    bad_u = sorted(set(raw["Usage"]) - set(USAGE_4))
    bad_m = sorted(set(raw["Marks"]) - set(MARKS_4))
    if bad_u or bad_m:
        raise ValueError(
            f"Unknown values found. Usage must be one of {USAGE_4}; Marks must be one of {MARKS_4}. "
            f"Problem values -> Usage: {bad_u}, Marks: {bad_m}"
        )
    table = pd.crosstab(raw["Usage"], raw["Marks"]).reindex(index=USAGE_4, columns=MARKS_4, fill_value=0)
    return table.astype(int)
