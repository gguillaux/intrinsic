from dash import callback, Output, Input, State, dash_table
import pandas as pd
from app.services.news_service import NewsService
from app.services.asset_service import AssetService

news_service = NewsService()
asset_service = AssetService()

@callback(
    Output('news-table', 'data'),
    [Input('btn-refresh-news', 'n_clicks'), Input('interval-sync', 'n_intervals')]
)
def update_news_table(n_clicks, n_intervals):
    if n_clicks:
        news_service.sync_news()
    
    news = news_service.get_latest_news()
    df = pd.DataFrame([n.model_dump() for n in news])
    if not df.empty:
        df['date_time'] = df['date_time'].dt.strftime('%d/%m/%Y %H:%M')
    return df.to_dict('records')

@callback(
    Output('assets-table-container', 'children'),
    [Input('btn-refresh-assets', 'n_clicks')]
)
def update_assets_table(n_clicks):
    if n_clicks:
        asset_service.sync_assets()
        
    assets = asset_service.get_assets()
    df = pd.DataFrame([a.model_dump() for a in assets])
    
    if df.empty:
        return "Nenhum dado disponível. Clique em atualizar."

    # Format numbers
    cols = [
        {"name": "Ticker", "id": "ticker"},
        {"name": "Preço", "id": "price", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "P/L", "id": "pe", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "DY %", "id": "dy", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "P/VP", "id": "p_vp", "type": "numeric", "format": {"specifier": ".2f"}},
        {"name": "ROE %", "id": "roe", "type": "numeric", "format": {"specifier": ".2f"}},
    ]
    
    return dash_table.DataTable(
        data=df.to_dict('records'),
        columns=cols,
        sort_action="native",
        filter_action="native",
        style_table={'overflowX': 'auto'},
        style_cell={'textAlign': 'left', 'padding': '10px'},
        style_header={'backgroundColor': '#f8f9fa', 'fontWeight': 'bold'},
        style_data_conditional=[
            {
                'if': {'column_id': 'dy', 'filter_query': '{dy} > 6'},
                'backgroundColor': '#d4edda',
            },
            {
                'if': {'column_id': 'pe', 'filter_query': '{pe} < 10'},
                'backgroundColor': '#fff3cd',
            }
        ]
    )
