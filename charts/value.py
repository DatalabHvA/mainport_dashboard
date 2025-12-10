import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def value_fig(seg: pd.DataFrame):
    if seg is None or seg.empty or "AddedValue" not in seg:
        return px.bar()
    return px.bar(seg, x="Segment", y="AddedValue", title="Added value by segment (€m/yr)")

def pax_hist_fig(seg: pd.DataFrame):
    if seg is None or len(seg) == 0:
        return px.bar()
    fig = px.bar(seg, x="Segment", y="Pax", title="Number of passengers by segment (million)")
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=50),
        height=300,
        title_font=dict(
            size=12,
            family="Arial",
            color="black"
        ),
        title = dict(
            x = 0.5,
            xanchor="center",

        )
    )
    return fig 

def cargo_hist_fig(seg: pd.DataFrame):
    if seg is None or len(seg) == 0:
        return px.bar()
    fig = px.bar(seg, x="Segment", y="Cargo", title="Cargo volume by segment (million tons)")
    fig.update_layout(
        margin=dict(l=0, r=0, t=20, b=50),
        height=300,
        title_font=dict(
            size=12,
            family="Arial",
            color="black"
        ),
        title = dict(
            x = 0.5,
            xanchor="center",

        )
    )
    return fig
