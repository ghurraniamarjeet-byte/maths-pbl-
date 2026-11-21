"""
plots.py
--------
Saare plotly charts yahan hain. Har function ek figure return karta hai.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy.stats import chi2

INDIGO, CORAL, TEAL, AMBER = "#1B1F4B", "#F2545B", "#1FA99A", "#E0A100"

# marks ke colors: red = low marks, amber = middle, teal = high
MARK_COLORS = {
    "Below 50%": "#C0392B", "50-70%": CORAL, "Below 70%": CORAL, "Below 80%": CORAL,
    "70-80%": AMBER, "80%+": TEAL,
}
USAGE_COLORS = {"Low (<2 hrs)": TEAL, "Medium (2-6 hrs)": AMBER, "High (6+ hrs)": CORAL}
FALLBACK = ["#5B6BDF", "#8A8FB5", "#3A3F7A", "#F4B942"]


def _colors(labels, table):
    return [table.get(l, FALLBACK[i % len(FALLBACK)]) for i, l in enumerate(labels)]


def _base_layout(fig, title, xtitle=None, ytitle=None, height=450):
    fig.update_layout(
        title=dict(text=title, font=dict(size=18, color=INDIGO)),
        template="plotly_white", height=height, font=dict(size=14),
        legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=50, r=30, t=70, b=60),
    )
    if xtitle:
        fig.update_xaxes(title_text=xtitle)
    if ytitle:
        fig.update_yaxes(title_text=ytitle)
    return fig


# ----------------------------------------------------------------------
# REJECTION REGION DIAGRAM
# ----------------------------------------------------------------------
def rejection_region_fig(stat, df, alpha, show_p=False, title=None, height=480):
    crit = float(chi2.ppf(1 - alpha, df))
    xmin = 0.05 if df == 1 else 0.0  # df=1 me x=0 par curve infinite hota hai
    xmax = max(float(chi2.ppf(0.999, df)), crit * 1.25, stat * 1.25)

    x_all = np.linspace(xmin, xmax, 600)
    y_all = chi2.pdf(x_all, df)
    ymax = float(y_all.max()) * 1.25

    xa = np.linspace(xmin, crit, 400)   # acceptance region
    xr = np.linspace(crit, xmax, 400)   # rejection region

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=xa, y=chi2.pdf(xa, df), mode="lines", fill="tozeroy",
                             line=dict(width=0), fillcolor="rgba(120,150,240,0.35)",
                             name="Acceptance region (fail to reject H0)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=xr, y=chi2.pdf(xr, df), mode="lines", fill="tozeroy",
                             line=dict(width=0), fillcolor="rgba(242,84,91,0.65)",
                             name=f"Rejection region (alpha = {alpha})", hoverinfo="skip"))
    if show_p and stat < xmax:
        xp = np.linspace(stat, xmax, 400)
        fig.add_trace(go.Scatter(x=xp, y=chi2.pdf(xp, df), mode="lines", fill="tozeroy",
                                 line=dict(width=0), fillcolor="rgba(244,185,66,0.55)",
                                 name="p-value area (right of calculated chi2)", hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_all, y=y_all, mode="lines", line=dict(color=INDIGO, width=3),
                             name=f"Chi-square curve (df = {df})",
                             hovertemplate="chi2 = %{x:.2f}<br>density = %{y:.4f}<extra></extra>"))
    # critical value (dashed)
    fig.add_trace(go.Scatter(x=[crit, crit], y=[0, ymax * 0.8], mode="lines",
                             line=dict(color=CORAL, width=3, dash="dash"),
                             name=f"Critical value = {crit:.3f}", hoverinfo="skip"))
    # calculated chi2 (solid)
    fig.add_trace(go.Scatter(x=[stat, stat], y=[0, ymax * 0.95], mode="lines",
                             line=dict(color="black", width=3),
                             name=f"Calculated chi2 = {stat:.2f}", hoverinfo="skip"))

    # labels: agar stat < crit to stat ka label left me, crit ka right me (overlap na ho)
    left_first = stat < crit
    fig.add_annotation(x=crit, y=ymax * 0.8, text=f"Critical value = {crit:.3f}", showarrow=False,
                       xanchor="left" if left_first else "right", yanchor="bottom",
                       font=dict(color=CORAL, size=14))
    fig.add_annotation(x=stat, y=ymax * 0.95, text=f"Calculated chi2 = {stat:.2f}", showarrow=False,
                       xanchor="right" if left_first else "left", yanchor="bottom",
                       font=dict(color="black", size=14))
    # region names
    fig.add_annotation(x=crit * 0.5, y=ymax * 0.04, text="Acceptance region<br>(fail to reject H0)",
                       showarrow=False, font=dict(color=INDIGO, size=13), yanchor="bottom")
    xm = crit + (xmax - crit) * 0.45
    fig.add_annotation(x=xm, y=float(chi2.pdf(xm, df)), text=f"Rejection region<br>(alpha = {alpha})",
                       showarrow=True, arrowhead=2, arrowcolor=CORAL, ax=0, ay=-80,
                       font=dict(color=CORAL, size=13))

    _base_layout(fig, title or f"Chi-Square Distribution (df = {df}) with Rejection Region",
                 "Chi-square value", "Probability density", height)
    fig.update_yaxes(range=[0, ymax])
    fig.update_xaxes(range=[xmin, xmax])
    return fig


# ----------------------------------------------------------------------
# BAR CHARTS
# ----------------------------------------------------------------------
def stacked_bar(obs: pd.DataFrame):
    fig = go.Figure()
    for col, color in zip(obs.columns, _colors(obs.columns, MARK_COLORS)):
        fig.add_trace(go.Bar(x=list(obs.index), y=obs[col], name=col, marker_color=color,
                             text=obs[col], textposition="inside", textfont=dict(color="white", size=14)))
    fig.update_layout(barmode="stack")
    return _base_layout(fig, "Stacked Bar: Marks Mix within each Usage Group",
                        "Daily social media usage", "Number of students")


def percent_stacked_bar(obs: pd.DataFrame):
    pct = obs.div(obs.sum(axis=1), axis=0) * 100
    fig = go.Figure()
    for col, color in zip(pct.columns, _colors(pct.columns, MARK_COLORS)):
        fig.add_trace(go.Bar(x=list(pct.index), y=pct[col], name=col, marker_color=color,
                             text=[f"{v:.0f}%" for v in pct[col]], textposition="inside",
                             textfont=dict(color="white", size=14)))
    fig.update_layout(barmode="stack")
    fig = _base_layout(fig, "100% Stacked Bar: Percentage of Students in each Marks Group",
                       "Daily social media usage", "Percentage of students (%)")
    fig.update_yaxes(range=[0, 100])
    return fig


def clustered_bar(obs: pd.DataFrame):
    fig = go.Figure()
    for row, color in zip(obs.index, _colors(obs.index, USAGE_COLORS)):
        fig.add_trace(go.Bar(x=list(obs.columns), y=obs.loc[row], name=row, marker_color=color,
                             text=obs.loc[row], textposition="outside"))
    fig.update_layout(barmode="group")
    return _base_layout(fig, "Clustered Bar: Usage Groups Compared by Marks",
                        "Last exam marks", "Number of students")


def heatmap_obs_exp(obs: pd.DataFrame, exp: pd.DataFrame):
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Observed (O)", "Expected (E)"))
    for i, (tbl, fmt) in enumerate([(obs, "{:.0f}"), (exp, "{:.2f}")], start=1):
        text = [[fmt.format(v) for v in row] for row in tbl.values]
        fig.add_trace(go.Heatmap(z=tbl.values, x=list(tbl.columns), y=list(tbl.index), text=text,
                                 texttemplate="%{text}", textfont=dict(size=16),
                                 colorscale=[[0, "#FFFFFF"], [1, INDIGO]], showscale=False,
                                 hoverinfo="skip"), row=1, col=i)
        fig.update_yaxes(autorange="reversed", row=1, col=i)
    fig.update_layout(title=dict(text="Heatmap: Observed vs Expected Frequencies", font=dict(size=18, color=INDIGO)),
                      template="plotly_white", height=420, font=dict(size=14),
                      margin=dict(l=50, r=30, t=80, b=50))
    return fig


def usage_pie(obs: pd.DataFrame):
    totals = obs.sum(axis=1)
    fig = go.Figure(go.Pie(labels=list(totals.index), values=list(totals.values), hole=0.35,
                           marker=dict(colors=_colors(totals.index, USAGE_COLORS)),
                           textinfo="label+percent+value", textfont=dict(size=14)))
    fig.update_layout(title=dict(text="Overall Social Media Usage Levels", font=dict(size=18, color=INDIGO)),
                      template="plotly_white", height=450, font=dict(size=14),
                      legend=dict(orientation="h", yanchor="top", y=-0.05, xanchor="center", x=0.5))
    return fig
