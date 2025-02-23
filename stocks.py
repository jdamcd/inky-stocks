import argparse
import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageFont
import os

try:
    from inky import InkyPHAT
    from inky.auto import auto
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Warning: Inky pHAT not installed - will save image locally")

WIDTH, HEIGHT = 250, 122 
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Roboto-Bold.ttf")


def fetch_market_data(symbol):
    ticker = yf.Ticker(symbol)
    stock_name = ticker.info.get('shortName', symbol)
    
    # Get 3 days to ensure we have the last trading session
    end_time = datetime.now()
    start_time = end_time - timedelta(days=3)
    
    data = yf.download(symbol, start=start_time, end=end_time, interval="15m", auto_adjust=True)
    if data.empty:
        raise ValueError(f"No market data available for {symbol}.")
    
    # Most recent day data
    data['date'] = data.index.date
    last_day = data.index.date.max()
    data = data[data['date'] == last_day]
    
    return {
        'name': stock_name,
        'times': data.index.strftime("%H:%M").tolist(),
        'prices': data["Close"].values.flatten().tolist()
    }


def plot_graph(timestamps, prices):
    plt.figure(figsize=(1.85, 0.8), dpi=100)
    plt.plot(timestamps, prices, color="black", linewidth=2)
    plt.xticks([])
    plt.yticks([])
    plt.box(False)
    plt.tight_layout(pad=0.1)

    temp_path = "/tmp/inky_stocks_graph.png"
    plt.savefig(temp_path, dpi=100, bbox_inches="tight", pad_inches=0, transparent=False)
    plt.close()
    
    graph = Image.open(temp_path)
    graph = graph.resize((185, 80), Image.Resampling.BOX)
    return graph


def draw_trend_arrow(draw, x, y, width, height, is_up):
    padding = 8
    arrow_size = min(width - (padding * 2), height - (padding * 2))  # Use smaller dimension
    x_offset = (width - arrow_size) // 2
    y_offset = (height - arrow_size) // 2
    
    if is_up:
        points = [
            (x + x_offset + arrow_size//2, y + y_offset),
            (x + x_offset, y + y_offset + arrow_size),
            (x + x_offset + arrow_size, y + y_offset + arrow_size)
        ]
    else:
        points = [
            (x + x_offset, y + y_offset),
            (x + x_offset + arrow_size, y + y_offset),
            (x + x_offset + arrow_size//2, y + y_offset + arrow_size)
        ]
    draw.polygon(points, fill=0)


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        print("Warning: Could not load Roboto font, using default")
        return ImageFont.load_default()


def draw_percentage_change(draw, x, y, width, height, first_price, last_price):
    percent_change = ((last_price - first_price) / first_price) * 100
    text = f"{'+' if percent_change >= 0 else ''}{percent_change:.1f}%"
    
    font = load_font(20)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_x = x + (width - text_width) // 2
    text_y = y + (height - text_height) // 2
    draw.text((text_x, text_y), text, font=font, fill=0)


def draw_title(draw, x, y, symbol, stock_name):
    font = load_font(20)
    
    # Only show symbol for short names
    text = stock_name if len(stock_name) > 10 else f"{stock_name} [{symbol}]"
    draw.text((x, y), text, font=font, fill=0)


def draw_price(draw, x, y, width, height, price):
    font = load_font(16)
    price_text = f"{price:.0f}" if price >= 10000 else f"{price:.2f}"
    
    text_bbox = draw.textbbox((0, 0), price_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    text_x = x + (width - text_width) // 2
    text_y = y + (height - text_height) // 2
    draw.text((text_x, text_y), price_text, font=font, fill=0)


def create_display_image(symbol, market_data):
    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)
    
    col_width = 65
    col_height = 40
    col_x = WIDTH - col_width

    prices = market_data['prices']
    
    draw_title(draw, 8, 8, symbol, market_data['name'])
    draw_trend_arrow(draw, col_x, 0, col_width, col_height, prices[-1] > prices[0])
    draw_percentage_change(draw, col_x, col_height, col_width, col_height, prices[0], prices[-1])
    draw_price(draw, col_x, col_height*2, col_width, col_height, prices[-1])
    
    graph = plot_graph(market_data['times'], prices)
    image.paste(graph, (0, col_height))
    return image


def display_on_inky():
    display = auto()
    img = Image.open("market_graph.png")

    palette = Image.new('P', (1, 1))
    palette.putpalette((255, 255, 255,   # White
                        0, 0, 0,         # Black
                        255, 0, 0))      # Red

    img = img.convert('RGB').quantize(palette)

    display.set_border(display.WHITE)
    display.set_image(img)
    display.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Displays stock market data on a Pimoroni InkyPHAT")
    parser.add_argument("--symbol", type=str, default="^GSPC", help="Stock/Index symbol (default: S&P 500)")
    args = parser.parse_args()

    try:
        market_data = fetch_market_data(args.symbol)
        image = create_display_image(args.symbol, market_data)
        
        save_path = "market_graph.png"
        image.save(save_path, format="PNG")
        if DISPLAY_AVAILABLE:
            display_on_inky() 

    except Exception as e:
        print(f"Error: {e}")
