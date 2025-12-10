from dash import html
import dash_bootstrap_components as dbc

def kpi_card(title, id_):
    return dbc.Card(dbc.CardBody([
        html.Div(title, className="text-muted small"),
        html.Div(id=id_, className="h4 mb-0"),
    ]), className="shadow-sm")

def build_kpi_rows():
    row1 = dbc.Row([
        dbc.Col(kpi_card("# people improved (Lden lowered > 1dB)", "kpi_homes"), md=3, xs=6),
        dbc.Col(kpi_card("Added value – direct (€m)", "kpi_va_direct"), md=3, xs=6),
        dbc.Col(kpi_card("Added value – indirect (€m)", "kpi_va_indirect"), md=3, xs=6),
        dbc.Col(kpi_card("Total passengers (millions)", "total_pax"), md=3, xs=6),
    ], className="g-3 mb-3")

    row2 = dbc.Row([
        dbc.Col(kpi_card("Employment – direct (jobs)", "kpi_jobs_direct"), md=3, xs=6),
        dbc.Col(kpi_card("Employment – indirect (jobs)", "kpi_jobs_indirect"), md=3, xs=6),
        dbc.Col(kpi_card("Freight Cargo volume (million tons)", "total_cargo_freight"), md=3, xs=6),
        dbc.Col(kpi_card("Belly Cargo volume (million tons)", "total_cargo_belly"), md=3, xs=6),

    ], className="g-3 mb-3")
    return row1, row2

