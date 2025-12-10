import pandas as pd
import plotly.express as px

def employment_fig(seg: pd.DataFrame):
    if seg is None or seg.empty or "Jobs" not in seg:
        return px.bar()
    return px.bar(seg, x="Segment", y="Jobs", title="Employment by segment (direct jobs)")