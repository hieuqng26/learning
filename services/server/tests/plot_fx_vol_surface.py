import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import os


def parse_tenor_to_months(tenor_str):
    """Convert tenor string to approximate months for plotting."""
    tenor_map = {
        '1D': 1/30, '1W': 1/4, '2W': 0.5, '3W': 0.75, '1M': 1, '2M': 2, '3M': 3,
        '4M': 4, '5M': 5, '6M': 6, '9M': 9, '1Y': 12, '18M': 18,
        '2Y': 24, '3Y': 36, '4Y': 48, '5Y': 60, '7Y': 84, '10Y': 120
    }
    return tenor_map.get(tenor_str, 0)


def plot_fx_volatility_surface(csv_file_path, currency_pair=None, save_path=None):
    """
    Plot FX Volatility Surface as an interactive 3D surface plot.

    Parameters:
    csv_file_path (str): Path to the CSV file containing FX volatility data
    currency_pair (str): Specific currency pair to plot (e.g., 'EURUSD'). If None, plots all pairs.
    save_path (str): Path to save the plot. If None, displays the plot.

    Returns:
    plotly.graph_objects.Figure: The created figure object
    """
    # Read the CSV file
    df = pd.read_csv(csv_file_path)

    # Filter for Value rows only
    df = df[df['Key'] == 'Value'].copy()

    # Get unique currency pairs
    currency_pairs = df['Name'].str.split('.').str[0].unique()

    if currency_pair:
        currency_pairs = [pair for pair in currency_pairs if pair == currency_pair.upper()]
        if not currency_pairs:
            raise ValueError(f"Currency pair {currency_pair} not found in data")

    # Create figure with subplots for multiple currency pairs
    n_pairs = len(currency_pairs)
    fig = make_subplots(
        rows=n_pairs, cols=1,
        specs=[[{'type': 'surface'}]] * n_pairs,
        subplot_titles=[f'{pair} FX Volatility Surface' for pair in currency_pairs],
        vertical_spacing=0.1
    )

    for i, pair in enumerate(currency_pairs, 1):
        # Filter data for current currency pair
        pair_data = df[df['Name'].str.startswith(pair)].copy()

        # Convert tenor to months
        pair_data['Months'] = pair_data['FXVOLSURFACE'].apply(parse_tenor_to_months)

        # Define delta strikes and their approximate moneyness values
        strikes = ['Put10', 'Put25', 'ATM', 'Call25', 'Call10']
        strike_values = [-0.10, -0.25, 0.0, 0.25, 0.10]  # Delta values

        # Create meshgrid for surface plot
        tenors = sorted(pair_data['Months'].unique())
        X, Y = np.meshgrid(strike_values, tenors)

        # Initialize Z matrix for volatilities
        Z = np.zeros_like(X, dtype=float)

        # Fill Z matrix with volatility values
        for j, tenor_months in enumerate(tenors):
            for k, strike in enumerate(strikes):
                vol_data = pair_data[(pair_data['Months'] == tenor_months)]
                if not vol_data.empty and strike in vol_data.columns:
                    Z[j, k] = vol_data[strike].iloc[0]

        # Create interactive 3D surface
        surface = go.Surface(
            x=X,
            y=Y,
            z=Z,
            colorscale='Viridis',
            showscale=True,
            hovertemplate='<b>Strike:</b> %{x}<br>' +
            '<b>Months:</b> %{y}<br>' +
            '<b>Volatility:</b> %{z:.4f}<extra></extra>',
            name=f'{pair} Volatility'
        )

        fig.add_trace(surface, row=i, col=1)

    # Update layout for better interactivity
    fig.update_layout(
        title_text="FX Volatility Surface",
        height=600 * n_pairs,
        showlegend=False
    )

    # Update scene properties for each subplot
    for i in range(1, n_pairs + 1):
        scene_name = f'scene{i}' if i > 1 else 'scene'
        fig.update_layout(**{
            scene_name: dict(
                xaxis_title='Delta Strike',
                yaxis_title='Months to Maturity',
                zaxis_title='Implied Volatility',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            )
        })

    if save_path:
        fig.write_html(save_path)
        print(f"Interactive plot saved to: {save_path}")
    else:
        fig.show()

    return fig


if __name__ == "__main__":
    csv_path = "project/data/db/FXVOL/data.csv"

    if os.path.exists(csv_path):
        # Plot interactive 3D surface for specific currency pair
        fig = plot_fx_volatility_surface(csv_path, currency_pair="EURUSD")

    else:
        print(f"CSV file not found: {csv_path}")
        print("Please ensure the data.csv file is in the same directory as this script.")
