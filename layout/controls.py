from dash import html, dcc
import dash_bootstrap_components as dbc
import dash_table

def slider_with_val(id_, label, min_, max_, value, step=1):
    return html.Div([
        dbc.Row([
            dbc.Col(html.Label(label, className="fw-semibold small"), width=6),
            dbc.Col(html.Div(id=f"{id_}-val", className="text-end small fw-semibold"), width=6),
        ], className="mb-1"),
        dcc.Slider(id=id_, min=min_, max=max_, step=step, value=value, marks={min_: str(min_), max_: str(max_)}, tooltip={"placement":"bottom"}),
    ], className="mb-2")


def build_split_bar(shortp, mediump, longp):
    return dbc.Progress(children=[
        dbc.Progress(value=shortp, color="success", bar=True, label=f"Short {shortp}%"),
        dbc.Progress(value=mediump, color="warning", bar=True, label=f"Medium {mediump}%"),
        dbc.Progress(value=longp, color="danger", bar=True, label=f"Long {longp}%"),
    ], striped=False, animated=False)


def build_sidebar(paths: dict, defaults: dict):

    controls = html.Div([
        html.Div([
            html.Div("Scenario inputs", className="h6 m-0"),
            dbc.Button("Hide", id="btn-hide-sidebar", size="sm", color="secondary", outline=True, className="ms-auto"),
        ], className="d-flex align-items-center gap-2 mb-2"),

        dbc.Row([
            dbc.Col(html.Label("Number of slots (per year)", className="fw-semibold small"), width=7),
            dbc.Col(dbc.Input(id="slots", type="number", value=defaults["slots"], min=0, step=10000), width=5),
        ], className="mb-3 align-items-center"),

        slider_with_val("freight_pct", "Freight share (%)", 0, 100, defaults["freight_share"]),
        html.Small("Passengers share is 100% - Freight", className="text-muted"),
        html.Hr(),
        html.Div("Haul distribution (must sum to 100%)", className="small text-muted mb-2"),
        slider_with_val("short_pct", "Short-haul (%)", 0, 100, defaults["short_pct"]),
        slider_with_val("medium_pct", "Medium-haul (%)", 0, 100, defaults["medium_pct"]),
        dbc.Row([
            dbc.Col(html.Label("Long-haul (%)", className="fw-semibold small"), width=6),
            dbc.Col(html.Div(id="long_pct_val", className="text-end small fw-semibold"), width=6),
        ], className="mb-1"),
        html.Div(id="long_pct_bar"),
        html.Hr(),
        dbc.Row([
            dbc.Col(html.Label("Path", className="fw-semibold small"), width=4),
            dbc.Col(dcc.Dropdown(id="path", options=[{"label":k, "value":k} for k in paths], value=defaults["path"], clearable=False), width=8),
        ], className="mb-3"),
        html.Hr(),
        
        dbc.Button("Reset", id="btn-reset", color="light", className="w-100 mb-2"),
        # Floating show button (initially hidden, placed globally in app layout)
        dbc.Button("Show inputs", id="btn-show-sidebar", color="secondary", outline=True,
                   style={"position": "fixed", "top": "80px", "left": "10px", "zIndex": 2000, "display": "none"}),
    ], id="sidebar", className="p-3 border-end bg-light", style={
        "width": "360px", "minWidth": "300px", "maxWidth": "380px",
        "position": "sticky", "top": "0", "height": "100vh", "overflowY": "auto",
    })

    return controls

