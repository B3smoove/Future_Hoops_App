import dash
print(dash.__version__)
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go


# Initialize the app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY], suppress_callback_exceptions=True)
app.title = "Future Hoops - NBA Player Stat Projections"

# Sample data - in a real app, you'd connect to a database or API
def generate_sample_data():
    players = [
        {'id': 1, 'name': 'LeBron James', 'team': 'LAL', 'position': 'SF'},
        {'id': 2, 'name': 'Stephen Curry', 'team': 'GSW', 'position': 'PG'},
        {'id': 3, 'name': 'Nikola Jokic', 'team': 'DEN', 'position': 'C'},
        {'id': 4, 'name': 'Luka Doncic', 'team': 'DAL', 'position': 'PG'},
        {'id': 5, 'name': 'Giannis Antetokounmpo', 'team': 'MIL', 'position': 'PF'},
    ]
    
    # Generate game logs for each player
    game_logs = []
    for player in players:
        for i in range(1, 16):  # Last 15 games
            date = (datetime.now() - timedelta(days=15-i)).strftime('%Y-%m-%d')
            pts = np.random.randint(15, 40) if player['name'] != 'Nikola Jokic' else np.random.randint(20, 35)
            reb = np.random.randint(5, 15) if player['position'] in ['C', 'PF'] else np.random.randint(3, 10)
            ast = np.random.randint(5, 12) if player['position'] in ['PG', 'SF'] else np.random.randint(3, 8)
            
            game_logs.append({
                'player_id': player['id'],
                'player_name': player['name'],
                'team': player['team'],
                'position': player['position'],
                'date': date,
                'pts': pts,
                'reb': reb,
                'ast': ast,
                'stl': np.random.randint(0, 4),
                'blk': np.random.randint(0, 3),
                'fg_pct': round(np.random.uniform(0.4, 0.6), 2),
                'three_pct': round(np.random.uniform(0.3, 0.45), 2),
                'min': np.random.randint(32, 40)
            })
    
    # Generate current/live game projections
    projections = []
    for player in players:
        # Base projection on recent average with some randomness
        player_games = [g for g in game_logs if g['player_name'] == player['name']]
        recent_games = player_games[-5:]  # Last 5 games
        
        pts_avg = sum(g['pts'] for g in recent_games) / len(recent_games)
        reb_avg = sum(g['reb'] for g in recent_games) / len(recent_games)
        ast_avg = sum(g['ast'] for g in recent_games) / len(recent_games)
        
        projections.append({
            'player_id': player['id'],
            'player_name': player['name'],
            'team': player['team'],
            'position': player['position'],
            'projected_pts': round(pts_avg * np.random.uniform(0.9, 1.1)),
            'projected_reb': round(reb_avg * np.random.uniform(0.9, 1.1)),
            'projected_ast': round(ast_avg * np.random.uniform(0.9, 1.1)),
            'projected_stl': round(np.mean([g['stl'] for g in recent_games]) * np.random.uniform(0.8, 1.2), 1),
            'projected_blk': round(np.mean([g['blk'] for g in recent_games]) * np.random.uniform(0.8, 1.2), 1),
            'confidence': np.random.randint(70, 95)  # Confidence score for projection
        })
    
    return pd.DataFrame(players), pd.DataFrame(game_logs), pd.DataFrame(projections)

players_df, game_logs_df, projections_df = generate_sample_data()

# App layout
app.layout = dbc.Container([
    dbc.Row([
        dbc.Col(html.H1("Future Hoops", className="text-center mb-4"), width=12)
    ]),
    
    dbc.Row([
        dbc.Col([
            html.H3("Player Selection", className="mb-3"),
            dcc.Dropdown(
                id='player-dropdown',
                options=[{'label': p['name'], 'value': p['id']} for _, p in players_df.iterrows()],
                value=1,
                clearable=False,
                className="mb-3"
            ),
            html.Div(id='player-info-card', className="mb-4")
        ], md=4),
        
        dbc.Col([
            html.H3("Stat Projections", className="mb-3"),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Current/Live Game Projection", className="card-title"),
                    html.Div(id='projection-stats')
                ])
            ], className="mb-4"),
            
            dbc.Card([
                dbc.CardBody([
                    html.H4("Upcoming Games Forecast", className="card-title"),
                    dcc.Graph(id='forecast-graph')
                ])
            ])
        ], md=8)
    ]),
    
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Recent Performance Trends", className="card-title"),
                    dcc.Graph(id='trend-graph')
                ])
            ])
        ], width=12)
    ], className="mt-4"),
    
    # Hidden div to store data
    dcc.Store(id='game-logs-data', data=game_logs_df.to_json(date_format='iso', orient='split')),
    dcc.Store(id='projections-data', data=projections_df.to_json(date_format='iso', orient='split'))
], fluid=True)

# Callbacks
@app.callback(
    Output('player-info-card', 'children'),
    Input('player-dropdown', 'value')
)
def update_player_info(player_id):
    player = players_df[players_df['id'] == player_id].iloc[0]
    return dbc.Card([
        dbc.CardBody([
            html.H4(player['name'], className="card-title"),
            html.P(f"Team: {player['team']}", className="card-text"),
            html.P(f"Position: {player['position']}", className="card-text"),
            html.P("Last 5 Game Averages:", className="card-text mt-3"),
            html.Div(id='player-avg-stats')
        ])
    ])

@app.callback(
    Output('player-avg-stats', 'children'),
    Input('player-dropdown', 'value'),
    Input('game-logs-data', 'data')
)
def update_avg_stats(player_id, game_logs_json):
    game_logs = pd.read_json(game_logs_json, orient='split')
    player_games = game_logs[game_logs['player_id'] == player_id]
    recent_games = player_games.tail(5)
    
    if len(recent_games) == 0:
        return html.P("No recent game data available", className="card-text")
    
    pts_avg = recent_games['pts'].mean()
    reb_avg = recent_games['reb'].mean()
    ast_avg = recent_games['ast'].mean()
    stl_avg = recent_games['stl'].mean()
    blk_avg = recent_games['blk'].mean()
    fg_pct = recent_games['fg_pct'].mean()
    
    return [
        html.P(f"PTS: {pts_avg:.1f}", className="card-text"),
        html.P(f"REB: {reb_avg:.1f}", className="card-text"),
        html.P(f"AST: {ast_avg:.1f}", className="card-text"),
        html.P(f"STL: {stl_avg:.1f}", className="card-text"),
        html.P(f"BLK: {blk_avg:.1f}", className="card-text"),
        html.P(f"FG%: {fg_pct:.1%}", className="card-text")
    ]

@app.callback(
    Output('projection-stats', 'children'),
    Input('player-dropdown', 'value'),
    Input('projections-data', 'data')
)
def update_projection_stats(player_id, projections_json):
    projections = pd.read_json(projections_json, orient='split')
    player_proj = projections[projections['player_id'] == player_id].iloc[0]
    
    return dbc.Row([
        dbc.Col([
            html.H5("Points", className="text-center"),
            html.H3(f"{player_proj['projected_pts']}", className="text-center text-primary"),
            html.Small(f"Confidence: {player_proj['confidence']}%", className="text-muted d-block text-center")
        ], className="border-end"),
        
        dbc.Col([
            html.H5("Rebounds", className="text-center"),
            html.H3(f"{player_proj['projected_reb']}", className="text-center text-primary"),
            html.Small(f"Confidence: {player_proj['confidence']}%", className="text-muted d-block text-center")
        ], className="border-end"),
        
        dbc.Col([
            html.H5("Assists", className="text-center"),
            html.H3(f"{player_proj['projected_ast']}", className="text-center text-primary"),
            html.Small(f"Confidence: {player_proj['confidence']}%", className="text-muted d-block text-center")
        ], className="border-end"),
        
        dbc.Col([
            html.H5("Steals", className="text-center"),
            html.H3(f"{player_proj['projected_stl']}", className="text-center text-primary")
        ]),
        
        dbc.Col([
            html.H5("Blocks", className="text-center"),
            html.H3(f"{player_proj['projected_blk']}", className="text-center text-primary")

        ])
    ])

@app.callback(
    Output('trend-graph', 'figure'),
    Input('player-dropdown', 'value'),
    Input('game-logs-data', 'data')
)
def update_trend_graph(player_id, game_logs_json):
    game_logs = pd.read_json(game_logs_json, orient='split')
    player_games = game_logs[game_logs['player_id'] == player_id].sort_values('date')
    
    fig = go.Figure()
    
    # Add traces for each stat
    fig.add_trace(go.Scatter(
        x=player_games['date'], y=player_games['pts'],
        name='Points', line=dict(color='#1f77b4'), mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=player_games['date'], y=player_games['reb'],
        name='Rebounds', line=dict(color='#ff7f0e'), mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=player_games['date'], y=player_games['ast'],
        name='Assists', line=dict(color='#2ca02c'), mode='lines+markers'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        title='Recent Game Performance',
        xaxis_title='Date',
        yaxis_title='Stat Value',
        legend_title='Stats'
    )
    
    return fig

@app.callback(
    Output('forecast-graph', 'figure'),
    Input('player-dropdown', 'value'),
    Input('game-logs-data', 'data')
)
def update_forecast_graph(player_id, game_logs_json):
    game_logs = pd.read_json(game_logs_json, orient='split')
    player_games = game_logs[game_logs['player_id'] == player_id].sort_values('date')
    
    # Convert dates to datetime objects if they aren't already
    if isinstance(player_games['date'].iloc[0], str):
        player_games['date'] = pd.to_datetime(player_games['date'])
    
    # Simple forecasting - using moving average
    pts = player_games['pts'].values
    reb = player_games['reb'].values
    ast = player_games['ast'].values
    
    # Generate next 3 "games" (dates)
    last_date = player_games['date'].iloc[-1]
    forecast_dates = [last_date + timedelta(days=i) for i in range(1, 4)]
    forecast_dates_str = [d.strftime('%Y-%m-%d') for d in forecast_dates]
    historical_dates_str = player_games['date'].dt.strftime('%Y-%m-%d')
    
    # Simple projection - average of last 3 games with some noise
    pts_proj = [np.mean(pts[-3:]) * np.random.uniform(0.9, 1.1) for _ in range(3)]
    reb_proj = [np.mean(reb[-3:]) * np.random.uniform(0.9, 1.1) for _ in range(3)]
    ast_proj = [np.mean(ast[-3:]) * np.random.uniform(0.9, 1.1) for _ in range(3)]
    
    fig = go.Figure()
    
    # Historical data
    fig.add_trace(go.Scatter(
        x=historical_dates_str, y=pts,
        name='Points (Actual)', line=dict(color='#1f77b4'), mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=historical_dates_str, y=reb,
        name='Rebounds (Actual)', line=dict(color='#ff7f0e'), mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=historical_dates_str, y=ast,
        name='Assists (Actual)', line=dict(color='#2ca02c'), mode='lines+markers'
    ))
    
    # Projections
    fig.add_trace(go.Scatter(
        x=forecast_dates_str, y=pts_proj,
        name='Points (Projected)', line=dict(color='#1f77b4', dash='dot'), mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates_str, y=reb_proj,
        name='Rebounds (Projected)', line=dict(color='#ff7f0e', dash='dot'), mode='lines+markers'
    ))
    
    fig.add_trace(go.Scatter(
        x=forecast_dates_str, y=ast_proj,
        name='Assists (Projected)', line=dict(color='#2ca02c', dash='dot'), mode='lines+markers'
    ))
    
    fig.update_layout(
        template='plotly_dark',
        hovermode='x unified',
        title='Upcoming Game Projections',
        xaxis_title='Date',
        yaxis_title='Stat Value',
        legend_title='Stats'
    )
    
    return fig

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
    