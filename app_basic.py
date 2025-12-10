import dash
from dash import Dash, html, dcc, Input, Output, State, callback, ALL, MATCH
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import numpy as np

# ------------------
# App setup
# ------------------
external_stylesheets = [dbc.themes.BOOTSTRAP]
app = Dash(__name__, external_stylesheets=external_stylesheets, suppress_callback_exceptions=True)
app.title = "Scenario Explorer"
server = app.server

# ------------------
# Helpers / dummy data
# ------------------
np.random.seed(42)

def make_time_series(label: str, scale: float = 1.0):
    years = np.arange(2020, 2101)
    baseline = np.linspace(1.0, 1.0 + 0.4 * scale, len(years))
    noise = np.random.normal(0, 0.02 * scale, len(years))
    y = baseline + noise
    return pd.DataFrame({"year": years, label: y})

base_emissions = make_time_series("Emissions", 2.0)
base_temp = make_time_series("Temperature Δ (°C)", 1.2)
base_energy = make_time_series("Energy Demand (EJ)", 1.5)
base_price = make_time_series("Energy Price ($/MWh)", 0.8)

# ------------------
# Controls (left sidebar)
# ------------------

def slider_row(id_, label, min_, max_, step, value, tooltip=None):
    tip = html.Small(tooltip, className="text-muted") if tooltip else None
    return dbc.Row([
        dbc.Col(html.Label(label, className="fw-semibold small"), width=6),
        dbc.Col(html.Div(id=f"{id_}-val", className="text-end small fw-semibold"), width=6),
        dbc.Col(dcc.Slider(id=id_, min=min_, max=max_, step=step, value=value, marks=None, tooltip={"placement":"bottom", "always_visible":False}), width=12),
        dbc.Col(tip, width=12)
    ], className="mb-3")

control_groups = [
    {
        "title": "Energy Supply",
        "id": "energy",
        "children": [
            slider_row("s_co2_tax", "CO₂ price ($/t)", 0, 300, 5, 50, "Global price on carbon"),
            slider_row("s_renewables", "Renewables share (%)", 0, 100, 1, 35, "Share of wind/solar/etc."),
            slider_row("s_nuclear", "Nuclear buildout (GW)", 0, 800, 10, 80),
        ],
    },
    {
        "title": "Transport",
        "id": "transport",
        "children": [
            slider_row("s_ev_share", "EV share of sales (%)", 0, 100, 1, 40),
            slider_row("s_efficiency_tr", "Vehicle efficiency (+%)", 0, 60, 1, 10),
        ],
    },
    {
        "title": "Buildings & Industry",
        "id": "buildings",
        "children": [
            slider_row("s_heatpumps", "Heat pump adoption (%)", 0, 100, 1, 25),
            slider_row("s_ind_eff", "Industrial efficiency (+%)", 0, 60, 1, 15),
        ],
    },
    {
        "title": "Carbon Removal",
        "id": "removal",
        "children": [
            slider_row("s_reforestation", "Re/afforestation (GtCO₂)", 0, 15, 0.1, 2.5),
            slider_row("s_direct_air_capture", "DAC scale (GtCO₂)", 0, 10, 0.1, 0.5),
        ],
    },
    {
        "title": "Socioeconomics",
        "id": "socio",
        "children": [
            slider_row("s_gdp", "GDP growth (2050, %)", 0, 6, 0.1, 2.5),
            slider_row("s_pop", "Population (2100, B)", 7.0, 13.0, 0.1, 9.7),
        ],
    },
]

accordion_items = [
    dbc.AccordionItem(children=grp["children"], title=grp["title"], item_id=grp["id"]) for grp in control_groups
]

sidebar = html.Div(
    [
        html.Div([
            html.Div("Controls", className="h6 m-0"),
            dbc.Button("Hide", id="btn-hide-sidebar", size="sm", color="secondary", outline=True, className="ms-auto")
        ], className="d-flex align-items-center gap-2 mb-2"),
        dbc.Accordion(accordion_items, always_open=True, start_collapsed=False, flush=True, id="controls-accordion"),
        html.Hr(),
        dbc.Button("Reset to Baseline", id="btn-reset", color="light", className="w-100 mb-2"),
        dbc.Button("Save Scenario", id="btn-save", color="primary", className="w-100"),
    ],
    id="sidebar",
    className="p-3 border-end bg-light",
    style={
        "width": "340px",
        "minWidth": "280px",
        "maxWidth": "360px",
        "position": "sticky",
        "top": "0",
        "height": "100vh",
        "overflowY": "auto",
    },
)

# ------------------
# Header / top bar
# ------------------
header = dbc.Navbar(
    dbc.Container([
        html.Div([
            html.Div("Scenario Explorer", className="navbar-brand fw-bold mb-0"),
        ], className="d-flex align-items-center"),
        dbc.Input(id="scenario-name", placeholder="Scenario name…", value="My Scenario", size="md", className="w-25 d-none d-md-block"),
        html.Div([
            dbc.Button("Compare", id="btn-compare", color="secondary", outline=True, className="me-2"),
            dbc.Button("Share", id="btn-share", color="primary"),
            dbc.Button("Menu", id="btn-menu", color="secondary", outline=True, className="ms-2 d-md-none"),
        ], className="d-flex align-items-center ms-auto"),
    ], fluid=True),
    color="white", dark=False, className="shadow-sm sticky-top"
)

# ------------------
# KPI strip (top of main)
# ------------------

def kpi_card(title, id_, suffix=""):
    return dbc.Card([
        dbc.CardBody([
            html.Div(title, className="text-muted small"),
            html.Div(id=id_, className="h4 mb-0")
        ])
    ], className="shadow-sm")

kpi_bar = dbc.Row([
    dbc.Col(kpi_card("Peak warming by 2100", "kpi_warming", "°C"), md=3, xs=6),
    dbc.Col(kpi_card("2050 Emissions", "kpi_em2050", " GtCO₂/yr"), md=3, xs=6),
    dbc.Col(kpi_card("2050 Energy Demand", "kpi_energy2050", " EJ"), md=3, xs=6),
    dbc.Col(kpi_card("Avg. Energy Price 2030s", "kpi_price2030", " $/MWh"), md=3, xs=6),
], className="g-3 mb-3")

# ------------------
# Charts / tabs
# ------------------

def line_chart(df: pd.DataFrame, y: str, title: str):
    fig = px.line(df, x="year", y=y)
    fig.update_layout(margin=dict(l=10, r=10, t=30, b=10), title=title, height=320)
    return fig

main_charts = dbc.Row([
    dbc.Col(dcc.Graph(id="graph_temp", figure=line_chart(base_temp, base_temp.columns[1], "Temperature Trajectory")), md=6),
    dbc.Col(dcc.Graph(id="graph_emissions", figure=line_chart(base_emissions, base_emissions.columns[1], "Emissions")), md=6),
], className="g-3 mb-3")

secondary_charts = dbc.Row([
    dbc.Col(dcc.Graph(id="graph_energy", figure=line_chart(base_energy, base_energy.columns[1], "Final Energy Demand")), md=6),
    dbc.Col(dcc.Graph(id="graph_price", figure=line_chart(base_price, base_price.columns[1], "Avg. Energy Price")), md=6),
], className="g-3 mb-3")

# Detail tabs (like En‑ROADS has additional panels)

tabs = dcc.Tabs(id="detail-tabs", value="tab-assumptions", children=[
    dcc.Tab(label="Assumptions", value="tab-assumptions", children=html.Div([
        html.P("Key levers and current settings."),
        html.Div(id="assumptions-table")
    ], className="p-3")),
    dcc.Tab(label="Energy Mix", value="tab-energy-mix", children=html.Div([
        dcc.Graph(id="graph_mix")
    ], className="p-3")),
    dcc.Tab(label="Costs", value="tab-costs", children=html.Div([
        dcc.Graph(id="graph_costs")
    ], className="p-3")),
])

# ------------------
# Right info panel (optional)
# ------------------
right_info = html.Div([
    dbc.Card([
        dbc.CardHeader("Notes"),
        dbc.CardBody([
            html.P("This demo mimics the En‑ROADS page layout using Dash.", className="small"),
            html.P("Adjust the sliders to see charts update.", className="small mb-0"),
        ])
    ], className="shadow-sm mb-3"),
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

# ------------------
# Layout composition
# ------------------
content = html.Div([
    dbc.Container([
        kpi_bar,
        main_charts,
        secondary_charts,
        tabs,
        html.Div(className="py-4")
    ], fluid=True)
], className="flex-grow-1")

layout_three_col = html.Div([
    header,
    html.Div([
        sidebar,
        html.Div([
            content,
        ], className="flex-grow-1"),
        html.Div(right_info, className="d-none d-xl-block border-start bg-white p-3")
    ], className="d-flex", style={"minHeight": "100vh"})
])

app.layout = layout_three_col

# ------------------
# Callbacks
# ------------------

# Display slider values next to labels
for grp in control_groups:
    for comp in grp["children"]:
        # Each comp is a Row with first element label, second val, third Slider (id is known)
        # We can introspect id by reading the Col with Slider
        pass  # placeholder; we build a generic callback below

@callback(
    Output("s_co2_tax-val", "children"),
    Output("s_renewables-val", "children"),
    Output("s_nuclear-val", "children"),
    Output("s_ev_share-val", "children"),
    Output("s_efficiency_tr-val", "children"),
    Output("s_heatpumps-val", "children"),
    Output("s_ind_eff-val", "children"),
    Output("s_reforestation-val", "children"),
    Output("s_direct_air_capture-val", "children"),
    Output("s_gdp-val", "children"),
    Output("s_pop-val", "children"),
    Input("s_co2_tax", "value"),
    Input("s_renewables", "value"),
    Input("s_nuclear", "value"),
    Input("s_ev_share", "value"),
    Input("s_efficiency_tr", "value"),
    Input("s_heatpumps", "value"),
    Input("s_ind_eff", "value"),
    Input("s_reforestation", "value"),
    Input("s_direct_air_capture", "value"),
    Input("s_gdp", "value"),
    Input("s_pop", "value"),
)

def _echo_slider_vals(co2, ren, nuc, ev, efftr, hp, ind, ref, dac, gdp, pop):
    return (
        f"${co2}/t", f"{ren}%", f"{nuc} GW", f"{ev}%", f"+{efftr}%",
        f"{hp}%", f"+{ind}%", f"{ref:.1f} Gt", f"{dac:.1f} Gt", f"{gdp:.1f}%", f"{pop:.1f} B"
    )

# KPI updates (toy math combining sliders)
@callback(
    Output("kpi_warming", "children"),
    Output("kpi_em2050", "children"),
    Output("kpi_energy2050", "children"),
    Output("kpi_price2030", "children"),
    Input("s_co2_tax", "value"),
    Input("s_renewables", "value"),
    Input("s_nuclear", "value"),
    Input("s_ev_share", "value"),
    Input("s_efficiency_tr", "value"),
    Input("s_heatpumps", "value"),
    Input("s_ind_eff", "value"),
    Input("s_reforestation", "value"),
    Input("s_direct_air_capture", "value"),
    Input("s_gdp", "value"),
    Input("s_pop", "value"),
)

def update_kpis(co2, ren, nuc, ev, efftr, hp, ind, ref, dac, gdp, pop):
    # Very rough toy relationships for demo only
    warming = 3.2 - 0.004*co2 - 0.008*ren - 0.001*nuc - 0.005*ev - 0.004*hp - 0.004*ind - 0.03*ref - 0.04*dac + 0.08*(gdp-2.5) + 0.06*(pop-9.7)
    em2050 = 40 - 0.08*co2 - 0.25*ren - 0.05*nuc - 0.2*ev - 0.15*hp - 0.2*ind - 0.9*ref - 1.2*dac + 0.4*(gdp-2.5) + 0.3*(pop-9.7)
    energy2050 = 450 + 0.8*(gdp-2.5)*100 - 1.0*ind - 0.6*efftr - 0.5*hp
    price2030 = 110 - 0.05*co2 - 0.2*ren + 0.04*nuc
    return (f"{max(warming, 1.0):.2f} °C", f"{max(em2050, 0):.1f}", f"{max(energy2050, 200):.0f}", f"{max(price2030, 20):.0f}")

# Chart updates (toy transformations of baseline series)
@callback(
    Output("graph_temp", "figure"),
    Output("graph_emissions", "figure"),
    Output("graph_energy", "figure"),
    Output("graph_price", "figure"),
    Input("s_co2_tax", "value"),
    Input("s_renewables", "value"),
    Input("s_nuclear", "value"),
    Input("s_ev_share", "value"),
    Input("s_efficiency_tr", "value"),
    Input("s_heatpumps", "value"),
    Input("s_ind_eff", "value"),
    Input("s_reforestation", "value"),
    Input("s_direct_air_capture", "value"),
)

def update_charts(co2, ren, nuc, ev, efftr, hp, ind, ref, dac):
    # Make shallow copies
    temp = base_temp.copy()
    emi = base_emissions.copy()
    en = base_energy.copy()
    pr = base_price.copy()

    # Apply toy effects
    mitigation = 0.002*co2 + 0.004*ren + 0.0008*nuc + 0.003*ev + 0.003*hp + 0.003*ind + 0.02*ref + 0.03*dac
    emi[emi.columns[1]] = emi[emi.columns[1]] * (1 - 0.5*np.tanh(mitigation/10))
    temp[temp.columns[1]] = temp[temp.columns[1]] * (1 - 0.25*np.tanh(mitigation/12))
    en[en.columns[1]] = en[en.columns[1]] * (1 - 0.1*np.tanh((efftr+ind+hp)/50))
    pr[pr.columns[1]] = pr[pr.columns[1]] * (1 - 0.15*np.tanh((co2+ren)/300))

    f1 = line_chart(temp, temp.columns[1], "Temperature Trajectory")
    f2 = line_chart(emi, emi.columns[1], "Emissions")
    f3 = line_chart(en, en.columns[1], "Final Energy Demand")
    f4 = line_chart(pr, pr.columns[1], "Avg. Energy Price")
    return f1, f2, f3, f4

# Assumptions table & mix chart
@callback(
    Output("assumptions-table", "children"),
    Output("graph_mix", "figure"),
    Output("graph_costs", "figure"),
    Input("s_co2_tax", "value"),
    Input("s_renewables", "value"),
    Input("s_nuclear", "value"),
    Input("s_ev_share", "value"),
    Input("s_heatpumps", "value"),
)

def update_details(co2, ren, nuc, ev, hp):
    df = pd.DataFrame([
        {"Lever": "CO₂ price", "Setting": f"${co2}/t"},
        {"Lever": "Renewables share", "Setting": f"{ren}%"},
        {"Lever": "Nuclear buildout", "Setting": f"{nuc} GW"},
        {"Lever": "EV share of sales", "Setting": f"{ev}%"},
        {"Lever": "Heat pump adoption", "Setting": f"{hp}%"},
    ])

    mix = pd.DataFrame({
        "Source": ["Fossil", "Renewables", "Nuclear"],
        "Share": [max(0, 100 - ren - min(40, nuc/8)), ren, min(40, nuc/8)]
    })

    fmix = px.pie(mix, names="Source", values="Share", title="Primary Energy Mix (toy)")

    costs = pd.DataFrame({
        "Item": ["Capex", "Fuel", "Carbon", "O&M"],
        "$/MWh": [40, 35 - 0.2*ren, max(0, 30 - 0.1*co2), 12]
    })
    fcosts = px.bar(costs, x="Item", y="$/MWh", title="Levelized Cost Breakdown (toy)")

    table = dbc.Table.from_dataframe(df, striped=True, bordered=False, hover=True, size="sm", className="mb-0")
    return table, fmix, fcosts

# Scenario name echo & share url
@callback(
    Output("scenario-name-echo", "children"),
    Output("share-url", "children"),
    Input("scenario-name", "value"),
)

def echo_name(name):
    return name or "My Scenario", f"/share/{(name or 'my-scenario').lower().replace(' ', '-') }"

# Reset button resets all sliders to defaults
@callback(
    Output("s_co2_tax", "value"),
    Output("s_renewables", "value"),
    Output("s_nuclear", "value"),
    Output("s_ev_share", "value"),
    Output("s_efficiency_tr", "value"),
    Output("s_heatpumps", "value"),
    Output("s_ind_eff", "value"),
    Output("s_reforestation", "value"),
    Output("s_direct_air_capture", "value"),
    Output("s_gdp", "value"),
    Output("s_pop", "value"),
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True
)

def reset_sliders(n):
    return 50, 35, 80, 40, 10, 25, 15, 2.5, 0.5, 2.5, 9.7

# Hide sidebar on small screens (simple demo)
@callback(
    Output("sidebar", "style"),
    Input("btn-hide-sidebar", "n_clicks"),
    State("sidebar", "style"),
    prevent_initial_call=True
)

def toggle_sidebar(n, style):
    style = style or {}
    current = style.get("display", "block")
    style["display"] = "none" if current != "none" else "block"
    return style

# ------------------
# Run
# ------------------
if __name__ == "__main__":
    app.run(debug=True)
