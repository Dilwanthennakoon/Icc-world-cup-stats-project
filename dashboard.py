import dash
from dash import dcc, html, Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load CSV files from GitHub
csv_urls = [
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1975_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1979_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1983_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1987_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1992_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1996_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/1999_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/2003_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/2007_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/2011_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/2015_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/2019_Match_Stats.csv",
    "https://raw.githubusercontent.com/Dilwanthennakoon/icc-world-cup-stats-project/main/WorldCup_Stats/2023_Match_Stats.csv"
]

# Combine data
try:
    frames = [pd.read_csv(url) for url in csv_urls]
    matches = pd.concat(frames, ignore_index=True)
    print("Data loaded successfully")
except Exception as e:
    print(f"Error loading data: {e}")

# Preprocessing (simplified for demo)
try:
    matches['Year'] = matches['date'].str.extract(r'(\d{4})')
    matches['Year'] = pd.to_numeric(matches['Year'], errors='coerce')  # Convert to numeric, force errors to NaN
    print("Data preprocessing successful")
except Exception as e:
    print(f"Error preprocessing data: {e}")

# App init
app = dash.Dash(__name__)
server = app.server

# Layout
app.layout = html.Div([
    html.H1("ICC Cricket World Cup Dashboard", style={'textAlign': 'center'}),

    # Filters
    html.Div([
        dcc.Dropdown(id='year_filter', options=[{'label': str(year), 'value': year} for year in sorted(matches['Year'].dropna().unique())],
                     value=None, placeholder="Select Year", multi=True),
        dcc.Dropdown(id='team_filter', options=[{'label': team, 'value': team} for team in sorted(pd.unique(matches[['team_1', 'team_2']].values.ravel()))],
                     value=None, placeholder="Select Team", multi=True),
    ], style={'display': 'flex', 'gap': '20px'}),

    # Summary Cards
    html.Div(id='summary-cards', style={'display': 'flex', 'justifyContent': 'space-around', 'marginTop': '20px'}),

    # Charts
    dcc.Graph(id='runs-over-years'),
    dcc.Graph(id='team-wins'),
    dcc.Graph(id='knockout-margins'),
    dcc.Graph(id='player-of-match'),
    dcc.Graph(id='host-outcomes'),
])

# Callbacks
@app.callback(
    [
        Output('summary-cards', 'children'),
        Output('runs-over-years', 'figure'),
        Output('team-wins', 'figure'),
        Output('knockout-margins', 'figure'),
        Output('player-of-match', 'figure'),
        Output('host-outcomes', 'figure')
    ],
    [
        Input('year_filter', 'value'),
        Input('team_filter', 'value')
    ]
)
def update_dashboard(selected_years, selected_teams):
    try:
        df = matches.copy()
        if selected_years:
            df = df[df['Year'].isin(selected_years)]
        if selected_teams:
            df = df[df['team_1'].isin(selected_teams) | df['team_2'].isin(selected_teams)]

        # Summary Cards
        total_matches = len(df)
        total_runs = df['team_1_runs'].fillna(0).sum() + df['team_2_runs'].fillna(0).sum()
        run_rate = round(total_runs / (total_matches * 50), 2) if total_matches > 0 else 0
        top_team = df['result'].value_counts().idxmax() if not df['result'].isna().all() else 'N/A'
        top_player = df['pom'].value_counts().idxmax() if not df['pom'].isna().all() else 'N/A'

        summary_cards = [
            html.Div([html.H4("Total Matches"), html.H2(total_matches)]),
            html.Div([html.H4("Total Runs"), html.H2(total_runs)]),
            html.Div([html.H4("Avg Run Rate"), html.H2(run_rate)]),
            html.Div([html.H4("Top Team"), html.H2(top_team)]),
            html.Div([html.H4("Top Player"), html.H2(top_player)]),
        ]

        # Chart 1: Runs Over Years
        runs_yearly = df.groupby('Year')[['team_1_runs', 'team_2_runs']].sum().sum(axis=1).reset_index(name='Total_Runs')
        fig1 = px.line(runs_yearly, x='Year', y='Total_Runs', title='Total Runs Over the Years')

        # Chart 2: Team Wins
        wins = df['result'].value_counts().reset_index()
        wins.columns = ['Team', 'Wins']
        fig2 = px.bar(wins, x='Team', y='Wins', title='Team Wins Comparison')

        # Chart 3: Knockout Margins (Finals & Semis)
        knockout_df = df[df['match_category'].isin(['Final', 'Semi-Final']) & df['team_1_runs'].notna()]
        fig3 = px.box(knockout_df, x='match_category', y='team_1_runs', title='Winning Margins in Knockouts')

        # Chart 4: Player of the Match Frequency
        pom = df['pom'].value_counts().head(10).reset_index()
        pom.columns = ['Player', 'Awards']
        fig4 = px.bar(pom, x='Player', y='Awards', title='Top Player of the Match Awards')

        # Chart 5: Host Country Match Outcomes
        host = df['host_country'].value_counts().reset_index()
        host.columns = ['Country', 'Matches']
        fig5 = px.pie(host, names='Country', values='Matches', title='Match Distribution by Host Country')

        return summary_cards, fig1, fig2, fig3, fig4, fig5
    except Exception as e:
        print(f"Error in callback: {e}")
        return [], go.Figure(), go.Figure(), go.Figure(), go.Figure(), go.Figure()

# Run app
if __name__ == '__main__':
    app.run_server(debug=True,port=8051)

