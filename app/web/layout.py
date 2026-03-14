from dash import dcc, html, dash_table
import dash_bootstrap_components as dbc

def create_layout():
    return dbc.Container([
        dbc.Row([
            dbc.Col(html.H1("Intrinsic", className="text-primary mt-4 mb-2"), width=12),
            dbc.Col(html.P("Rigor fundamentalista para investidores de longo prazo."), width=12),
        ]),
        
        dbc.Tabs([
            dbc.Tab(label="Oportunidades", tab_id="tab-assets", children=[
                html.Div([
                    dbc.Button("Atualizar Indicadores", id="btn-refresh-assets", color="secondary", className="mt-3 mb-3"),
                    html.Div(id="assets-table-container")
                ], className="p-3")
            ]),
            dbc.Tab(label="Plantão B3", tab_id="tab-news", children=[
                html.Div([
                    dbc.Button("Atualizar Notícias", id="btn-refresh-news", color="secondary", className="mt-3 mb-3"),
                    dash_table.DataTable(
                        id='news-table',
                        columns=[
                            {"name": "Data/Hora", "id": "date_time"},
                            {"name": "Ticker", "id": "ticker"},
                            {"name": "Título", "id": "headline"},
                        ],
                        style_table={'overflowX': 'auto'},
                        style_cell={
                            'textAlign': 'left',
                            'padding': '10px',
                            'fontFamily': 'sans-serif'
                        },
                        style_header={
                            'backgroundColor': '#f8f9fa',
                            'fontWeight': 'bold'
                        },
                        page_size=20,
                        filter_action="native",
                        sort_action="native",
                    )
                ], className="p-3")
            ]),
        ], id="tabs", active_tab="tab-assets"),
        
        dcc.Interval(id='interval-sync', interval=15*60*1000, n_intervals=0) # 15 min auto refresh
    ], fluid=True)
