"""
Inky Stocks common

Shared functions for fetching data, drawing graphs, etc.
"""
import os
from datetime import datetime, timedelta

import matplotlib.pyplot as plt
import pandas as pd
import yfinance as yf
from PIL import Image, ImageFont


FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Roboto-Bold.ttf")


class Config:
    def __init__(self):
        self.three_color = False


config = Config()


def fetch_market_data(symbol):
    """
    Fetch market data for a single stock symbol.

    Returns dict with:
        - name: Display name for the stock
        - times: List of time strings
        - prices: List of price values
        - latest_day_index: Index where latest trading day starts
    """
    ticker = yf.Ticker(symbol)
    stock_name = ticker.info.get('displayName') or ticker.info.get('shortName', symbol)
    if isinstance(stock_name, str):
        stock_name = stock_name.strip()

    # Get 4 days to cover weekends
    end_time = datetime.now()
    start_time = end_time - timedelta(days=4)

    data = yf.download(symbol, start=start_time, end=end_time, interval="15m", auto_adjust=True)
    if data.empty:
        raise ValueError(f"No market data available for {symbol}.")

    data['date'] = data.index.date
    latest_day = data.index.date.max()
    latest_day_data = data[data['date'] == latest_day]

    if len(latest_day_data) <= 8:
        previous_day_data = data[data['date'] < latest_day].tail(16)
        data = pd.concat([previous_day_data, latest_day_data])
    else:
        data = latest_day_data

    market_data = {
        'name': stock_name,
        'times': data.index.strftime("%H:%M").tolist(),
        'prices': data["Close"].values.flatten().tolist(),
        'latest_day_index': len(data) - len(latest_day_data)
    }
    return _prepare_market_data(market_data)


def fetch_multiple(symbols):
    results = []
    for symbol in symbols:
        try:
            data = fetch_market_data(symbol)
            results.append({
                'symbol': symbol,
                'data': data,
                'error': None
            })
        except Exception as e:
            results.append({
                'symbol': symbol,
                'data': None,
                'error': str(e)
            })
    return results


def _prepare_market_data(market_data):
    """Add calculated fields (is_up, first_price, last_price) to market data."""
    latest_day = market_data['prices'][market_data['latest_day_index']:]
    market_data['is_up'] = latest_day[-1] > latest_day[0] if len(latest_day) > 1 else True
    market_data['first_price'] = latest_day[0]
    market_data['last_price'] = latest_day[-1]
    return market_data


def load_font(size):
    """Load Roboto Bold font at specified size, falling back to default if unavailable."""
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        print("Warning: Could not load Roboto font, using default")
        return ImageFont.load_default()


def plot_graph(prices, latest_day_index, graph_width, graph_height, three_color=False):
    """
    Generate a price graph as a PIL Image.

    Args:
        prices: List of price values
        latest_day_index: Index where latest trading day starts
        graph_width: Width of output image in pixels
        graph_height: Height of output image in pixels
        three_color: If True, draw negative segments in red

    Returns:
        PIL Image of the graph
    """
    width_inches = graph_width / 100
    height_inches = graph_height / 100
    plt.figure(figsize=(width_inches, height_inches), dpi=100)

    # Don't anti-alias since we're drawing for e-ink
    plt.rcParams['lines.antialiased'] = False
    plt.rcParams['patch.antialiased'] = False
    line_width = 1

    if latest_day_index < len(prices):
        start_price = prices[latest_day_index]

        def draw_negative_segments(price_data, base_index=0):
            for i in range(len(price_data) - 1):
                x_start = base_index + i
                x_end = base_index + i + 1

                # Special case for consecutive identical prices
                if price_data[i] == price_data[i+1]:
                    if price_data[i] < start_price:
                        plt.plot([x_start, x_end], [price_data[i], price_data[i+1]],
                                color='red', linewidth=line_width)
                    continue

                # Both points below start, full red segment
                if price_data[i] < start_price and price_data[i+1] < start_price:
                    plt.plot([x_start, x_end], [price_data[i], price_data[i+1]],
                            color='red', linewidth=line_width)

                # Crossing start price, partial red segment
                elif price_data[i] < start_price and price_data[i+1] >= start_price:
                    ratio = (start_price - price_data[i]) / (price_data[i+1] - price_data[i])
                    x_intersect = x_start + ratio
                    plt.plot([x_start, x_intersect], [price_data[i], start_price],
                            color='red', linewidth=line_width)

                # Opposite direction
                elif price_data[i] >= start_price and price_data[i+1] < start_price:
                    ratio = (start_price - price_data[i]) / (price_data[i+1] - price_data[i])
                    x_intersect = x_start + ratio
                    plt.plot([x_intersect, x_end], [start_price, price_data[i+1]],
                            color='red', linewidth=line_width)

        if latest_day_index > 0:
            # Plot previous day
            plt.plot(range(latest_day_index + 1), prices[:latest_day_index + 1],
                    color='black', linewidth=line_width)

            latest_prices = prices[latest_day_index:]

            # Plot latest day
            if three_color:
                plt.plot(range(latest_day_index, len(prices)), latest_prices,
                        color='black', linewidth=line_width)
                draw_negative_segments(latest_prices, latest_day_index)
            else:
                plt.plot(range(latest_day_index, len(prices)), latest_prices,
                        color='black', linewidth=line_width)
        else:
            # Plot latest day only
            if three_color:
                plt.plot(range(len(prices)), prices, color='black', linewidth=line_width)
                draw_negative_segments(prices)
            else:
                plt.plot(range(len(prices)), prices, color='black', linewidth=line_width)
    else:
        plt.plot(range(len(prices)), prices, color='black', linewidth=line_width)

    if latest_day_index > 0:
        plt.axvline(x=latest_day_index, color='black', linestyle='--', linewidth=line_width)

    plt.xticks([])
    plt.yticks([])
    plt.box(False)
    plt.tight_layout(pad=0.1)

    temp_path = "/tmp/inky_stocks_graph.png"
    try:
        plt.savefig(temp_path, dpi=100, bbox_inches="tight", pad_inches=0, transparent=False)
        plt.close()
        graph = Image.open(temp_path)
        graph = graph.resize((graph_width, graph_height), Image.Resampling.BOX)
        return graph
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def display_on_inky(image):
    from inky.auto import auto

    display = auto()

    palette = Image.new('P', (1, 1))
    palette.putpalette((255, 255, 255,   # White
                        0, 0, 0,         # Black
                        255, 0, 0))      # Red

    image = image.convert('RGB').quantize(palette=palette)

    display.set_border(display.WHITE)
    display.set_image(image)
    display.show()
