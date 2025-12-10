import dash
from dash import Dash, html, dcc, Input, Output, State, callback
import dash_bootstrap_components as dbc
import sys

from layout.controls import build_sidebar
from components.kpis import build_kpi_rows
#from charts.emissions import emissions_overview_fig, emissions_stack_fig
from charts.noise import noise_choropleth_fig, noise_hist_fig
from charts.value import value_fig, pax_hist_fig, cargo_hist_fig
from charts.employment import employment_fig
from logic.model import DEFAULTS, PATHS, compute_all
import geopandas as gpd

noise = gpd.read_feather("data/lden.ftr")  # or .geojson/.shp
# Columns expected:
# - geometry (polygons)
# - Lden (baseline Lden per polygon)  [optional but recommended]
# - households (number of homes per polygon)  [optional but recommended]

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)
app.title = "Airport Scenario Explorer"
server = app.server

# --- Layout pieces ---
sidebar = build_sidebar(PATHS, DEFAULTS)

header = dbc.Navbar(
    dbc.Container([
        html.Div("Airport Scenario Explorer", className="navbar-brand fw-bold mb-0"),
        dbc.Input(id="scenario-name", placeholder="Scenario name…", value="My Airport Scenario", size="md", className="w-25 d-none d-md-block"),
        html.Div([
            dbc.Button("Share", id="btn-share", color="primary"),
        ], className="ms-auto"),
    ], fluid=True), color="white", dark=False, className="shadow-sm sticky-top"
)

kpi_bar, kpi_bar2 = build_kpi_rows()

content = dbc.Container([
    kpi_bar,
    kpi_bar2,
    dbc.Row([
        dbc.Col(dcc.Graph(id="pax_stack"), md=4),
        dbc.Col(dcc.Graph(id="cargo_stack"), md=4),

        dbc.Col(dcc.Graph(id="noise_hist"), md=4),
    ], className="g-0 mb-0"),
    dcc.Tabs(id="detail-tabs", value="tab-noise", children=[
        #dcc.Tab(label="Total emissions", value="tab-emissions", children=html.Div([dcc.Graph(id="emissions_overview")], className="p-3")),
        dcc.Tab(label="Noise map (Lden)", value="tab-noise", children=html.Div([
            html.Div("KPI: number of homes affected shown above. Map below shows affected area's.", className="small text-muted mb-2"),
            dcc.Graph(id="noise_map"),
        ], className="p-3")),
        dcc.Tab(label="Added value", value="tab-value", children=html.Div([dcc.Graph(id="value_chart")], className="p-3")),
        dcc.Tab(label="Employment", value="tab-employment", children=html.Div([dcc.Graph(id="employment_chart")], className="p-3")),
    ]),
    html.Div(className="py-4"),
], fluid=True)

right_info = html.Div([
    dbc.Card([
        dbc.CardHeader("Scenario Meta"),
        dbc.CardBody([
            html.Div("Name", className="small text-muted"),
            html.Div(id="scenario-name-echo", className="fw-semibold"),
            html.Hr(className="my-2"),
            html.Div("Shareable link (placeholder)", className="small text-muted"),
            html.Code(id="share-url", className="small"),
        ])
    ], className="shadow-sm")
], style={"width": "320px", "position": "sticky", "top": "80px", "height": "calc(100vh - 100px)", "overflowY": "auto"})

app.layout = html.Div([
    header,
    html.Div([
        sidebar,
        html.Div([content], className="flex-grow-1"),
        html.Div(right_info, className="d-none d-xl-block border-start bg-white p-3"),
    ], className="d-flex", style={"minHeight": "100vh"})
])

# --- Callbacks ---
@callback(
    Output("freight_pct-val", "children"),
    Output("short_pct-val", "children"),
    Output("medium_pct-val", "children"),
    Output("long_pct_val", "children"),
    Output("long_pct_bar", "children"),
    Input("freight_pct", "value"),
    Input("short_pct", "value"),
    Input("medium_pct", "value"),
)

def echo_inputs(freight, shortp, mediump):
    from layout.controls import build_split_bar
    freight = int(round(freight or 0)); shortp = int(round(shortp or 0)); mediump = int(round(mediump or 0))
    longp = max(0, 100 - shortp - mediump)
    bar = build_split_bar(shortp, mediump, longp)
    return f"{freight}%", f"{shortp}%", f"{mediump}%", f"{longp}%", bar


@callback(
    #Output("fleet_warn", "children"),
    Output("kpi_homes", "children"),
    Output("kpi_va_direct", "children"),
    Output("kpi_va_indirect", "children"),
    Output("kpi_jobs_direct", "children"),
    Output("kpi_jobs_indirect", "children"),
    Output("total_cargo_freight", "children"),
    Output("total_cargo_belly", "children"),
    Output("total_pax", "children"),
    Output("pax_stack", "figure"),
    Output("cargo_stack", "figure"),
    Output("noise_map", "figure"),
    Output("value_chart", "figure"),
    Output("employment_chart", "figure"),
    Output("noise_hist", "figure"),
    Input("slots", "value"),
    Input("freight_pct", "value"),
    Input("short_pct", "value"),
    Input("medium_pct", "value"),
    Input("path", "value"),
)
def update_all(slots, freight, shortp, mediump, path):
    out = compute_all(slots, freight, shortp, mediump, path)

    k_homes = f"{out['homes']:,}"; k_vad = f"{out['va_direct']:,.1f}"; k_vai = f"{out['va_indirect']:,.1f}"
    k_jd = f"{out['jobs_direct']:,}"; k_ji = f"{out['jobs_indirect']:,}"
    total_cargo_freight = f"{out['total_cargo_freight']:,}"; total_cargo_belly = f"{out['total_cargo_belly']:,}"; total_pax = f"{out['total_pax']:,}"

    seg = out["seg"].copy()
    #fig_em_over = emissions_overview_fig(seg)
    fig_pax = pax_hist_fig(seg) 
    cargo_pax = cargo_hist_fig(seg) 

    fig_noise = noise_choropleth_fig(noise, color_col="Lden_sim") 
    fig_hist = noise_hist_fig(noise)
    fig_val = value_fig(seg)
    fig_emp = employment_fig(seg)

    return (
        k_homes, k_vad, k_vai, k_jd, k_ji, total_cargo_freight, total_cargo_belly, total_pax,
        fig_pax,cargo_pax, fig_noise, fig_val, fig_emp, fig_hist,
    )

@callback(
    Output("slots", "value"),
    Output("freight_pct", "value"),
    Output("short_pct", "value"),
    Output("medium_pct", "value"),
    Output("path", "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)

def reset_inputs(n):
    return (
        DEFAULTS["slots"],
        DEFAULTS["freight_share"],
        DEFAULTS["short_pct"],
        DEFAULTS["medium_pct"],
        DEFAULTS["path"],
    )

@callback(
    Output("scenario-name-echo", "children"),
    Output("share-url", "children"),
    Input("scenario-name", "value"),
)

def echo_name(name):
    return name or "My Airport Scenario", f"/share/{(name or 'my-airport-scenario').lower().replace(' ', '-') }"

@callback(
    Output("sidebar", "style"),
    Output("btn-show-sidebar", "style"),
    Input("btn-hide-sidebar", "n_clicks"),
    Input("btn-show-sidebar", "n_clicks"),
    State("sidebar", "style"),
    State("btn-show-sidebar", "style"),
    prevent_initial_call=True,
)

def toggle_sidebar(n_hide, n_show, sidebar_style, showbtn_style):
    ctx = dash.callback_context
    sidebar_style = sidebar_style or {}
    showbtn_style = showbtn_style or {"position": "fixed", "top": "80px", "left": "10px", "zIndex": 2000, "display": "none"}
    if not ctx.triggered:
        return sidebar_style, showbtn_style
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "btn-hide-sidebar":
        sidebar_style["display"] = "none"; showbtn_style["display"] = "block"
    else:
        sidebar_style["display"] = "block"; showbtn_style["display"] = "none"
    return sidebar_style, showbtn_style

if __name__ == "__main__":
    app.run(debug=True)
