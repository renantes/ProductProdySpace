# -*- coding: utf-8 -*-
"""
Created on Mon Jan 29 12:08:05 2024

@author: MacroConnections
"""

import pandas as pd
import networkx as nx
import plotly.graph_objs as go
import dash
from dash import dcc, html
from dash.dependencies import Input, Output

# Load the data
node_positions_df = pd.read_csv('data/OEC_network_hs4_positions.csv')
edges_df = pd.read_csv('data/OEC_network_hs4_edges.csv')
dictHS_data = pd.read_csv('data/dictHS.csv')

# Define the section colors
section_colors = {
    1: "#FFC0CB",  # Pinkish-orange
    2: "#FFFF00",  # Yellow
    3: "#D2B48C",  # Corrected Light brown
    4: "#90EE90",  # Light green
    5: "#FF1493",  # Darker pink
    6: "#800080",  # Purple
    7: "#C8A2C8",  # Light purple
    8: "#FFB6C1",  # Light pink
    9: "#FF0000",  # Red
    10: "#FFFACD",  # Light yellow
    11: "#008000",  # Green
    12: "#006400",  # Dark green
    13: "#A52A2A",  # Brown
    14: "#800080",  # Dark purple
    15: "#D4AF37",  # Gold
    16: "#ADD8E6",  # Light blue
    17: "#0000FF",  # Dark blue
    18: "#800000",  # Maroon
    19: "#90EE90",  # Lighter green
    20: "#808080",  # Gray
    21: "#F5F5DC",  # Beige
}

# Load complexity_prody_data for all periods into a dictionary
periods = [0, 1, 2, 3, 4]
complexity_prody_data = {}
for period in periods:
    file_name = f'data/complexity_prody_data_{period}.csv'
    complexity_prody_data[period] = pd.read_csv(file_name)

# Initialize the Dash app
app = dash.Dash(__name__)

# Define the layout of the app
app.layout = html.Div([
    html.H1("Product-PRODY Space Network"),

    # Dropdown menu for selecting the period
    dcc.Dropdown(
        id='period-dropdown',
        options=[{'label': f'Period {period}', 'value': period} for period in periods],
        value=0  # Default selected period is 0
    ),

    # Graph component for displaying the network
    dcc.Graph(id='network-graph'),
])

@app.callback(
    Output('network-graph', 'figure'),
    Input('period-dropdown', 'value')
)



def update_network_graph(period):
    # Get the DataFrame for the selected period
    complexity_prody_data_period = complexity_prody_data[period]

    # Merge the positions data with the dictionary data on 'nodes__id' and 'HS4 ID'
    node_positions_df_merged = node_positions_df.merge(dictHS_data, left_on='nodes__id', right_on='HS4 ID')
    
    # Merge the PRODY values with node_positions_df_merged
    node_positions_df_merged = node_positions_df_merged.merge(complexity_prody_data_period[['HS4 ID', 'PRODY']], on='HS4 ID', how='left')
    
    def scale_marker_size(prody_value):
        min_prody = min(node_positions_df_merged['PRODY'].dropna())
        max_prody = max(node_positions_df_merged['PRODY'].dropna())
        scaled_size = 3 + (z - min_prody) / (max_prody - min_prody) * 12  # Adjust the scaling factor as needed
        return scaled_size
    
        # Prepare the positions with z-values based on PRODY (replace NaN with 0)
    positions = {row['nodes__id']: (row['nodes__x'], row['nodes__y'], row['PRODY'] if not pd.isna(row['PRODY']) else 0) for _, row in node_positions_df_merged.iterrows()}

    # Initialize a new graph and add nodes and edges
    G = nx.Graph()
    for node, pos in positions.items():
        G.add_node(node, pos=pos)

    for _, row in edges_df.iterrows():
        G.add_edge(row['edges__source'], row['edges__target'], weight=row['edges__strength'])

    # Prepare data for Plotly
    node_x = []
    node_y = []
    node_z = []
    node_marker_size = []  # List to store the node sizes

    for node in G.nodes():
        x, y, z = G.nodes[node]['pos']
        node_x.append(x)
        node_y.append(y)
        node_z.append(z)
        # Set the node size proportional to its z-value (height)
        node_marker_size.append(scale_marker_size(z))  # Scale this value as needed

    # Fetch the "Section ID" information from node_positions_df_merged and create a dictionary
    node_sections = {row['nodes__id']: row['Section ID'] for _, row in node_positions_df_merged.iterrows()}

    # Create the color list for markers based on the "Section ID" of each node
    node_colors = [section_colors.get(node_sections.get(node, 0), "gray") for node in G.nodes()]

    edge_x = []
    edge_y = []
    edge_z = []

    for edge in G.edges():
        x0, y0, z0 = G.nodes[edge[0]]['pos']
        x1, y1, z1 = G.nodes[edge[1]]['pos']
        edge_x.extend([x0, x1, None])
        edge_y.extend([y0, y1, None])
        edge_z.extend([z0, z1, None])

    # Create custom hovertext for nodes
    hovertext = []
    for node in G.nodes():
        node_label = f"Node: {node}<br>X: {G.nodes[node]['pos'][0]:.2f}<br>Y: {G.nodes[node]['pos'][1]:.2f}<br>Z: {G.nodes[node]['pos'][2]:.2f}"

        # Retrieve the HS4 information for the node
        hs4_info = dictHS_data.loc[dictHS_data['HS4 ID'] == node]

        # Add HS4 information to the hovertext if found
        if not hs4_info.empty and 'HS4' in hs4_info:
            node_label += f"<br>Product: {hs4_info['HS4'].values[0]}"

        hovertext.append(node_label)

    # Create traces for Plotly
    edge_trace = go.Scatter3d(
        x=edge_x, y=edge_y, z=edge_z,
        line=dict(width=1, color='rgba(128, 128, 128, 0.8)'),
        hoverinfo='none',
        mode='lines')

    node_trace = go.Scatter3d(
        x=node_x, y=node_y, z=node_z,
        mode='markers',
        marker=dict(size=node_marker_size, color=node_colors, colorscale='Viridis', line=dict(width=0.5, color='rgba(217, 217, 217, 0.14)')),
        hoverinfo='text',
        text=hovertext)

    # Create the layout
    layout = go.Layout(
        title=f'3D Network Visualization for Period {period}',
        showlegend=False,
        scene=dict(
            xaxis=dict(showbackground=False),
            yaxis=dict(showbackground=False),
            zaxis=dict(showbackground=False)
        ),
        margin=dict(b=0, l=0, r=0, t=0))

    # Create the figure
    fig = go.Figure(data=[edge_trace, node_trace], layout=layout)

    return fig

if __name__ == '__main__':
    app.run_server(debug=True)
