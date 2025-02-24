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
    
    return {
        'name': stock_name,
        'times': data.index.strftime("%H:%M").tolist(),
        'prices': data["Close"].values.flatten().tolist(),
        'latest_day_index': len(data) - len(latest_day_data)
    }


def plot_graph(prices, latest_day_index):
    plt.figure(figsize=(1.85, 0.8), dpi=100)
    plt.plot(range(len(prices)), prices, color="black", linewidth=2)
    
    if latest_day_index > 0:
        plt.axvline(x=latest_day_index, color='black', linestyle='--', linewidth=1)
    
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
    arrow_size = min(width - (padding * 2), height - (padding * 2))
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
    
    if len(stock_name) > 16:
        text = symbol
    elif len(stock_name) > 10:
        text = stock_name
    else:
        text = f"{stock_name} [{symbol}]"
    
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
    latest_day_index = market_data['latest_day_index']
    latest_day = prices[latest_day_index:]
    
    draw_title(draw, 8, 8, symbol, market_data['name'])
    draw_trend_arrow(draw, col_x, 0, col_width, col_height, latest_day[-1] > latest_day[0])
    draw_percentage_change(draw, col_x, col_height, col_width, col_height, latest_day[0], latest_day[-1])
    draw_price(draw, col_x, col_height*2, col_width, col_height, latest_day[-1])
    
    graph = plot_graph(prices, latest_day_index)
    image.paste(graph, (0, col_height))
    return image


def display_on_inky(image_path):
    display = auto()
    image = Image.open(image_path)

    palette = Image.new('P', (1, 1))
    palette.putpalette((255, 255, 255,   # White
                        0, 0, 0,         # Black
                        255, 0, 0))      # Red

    image = image.convert('RGB').quantize(palette=palette)

    display.set_border(display.WHITE)
    display.set_image(image)
    display.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Displays stock market data on a Pimoroni InkyPHAT")
    parser.add_argument("--symbol", type=str, default="^GSPC", help="Stock/Index symbol (default: S&P 500)")
    args = parser.parse_args()

    try:
        market_data = fetch_market_data(args.symbol)
        image = create_display_image(args.symbol, market_data)
        
        if DISPLAY_AVAILABLE:
            save_path = "/tmp/inky_stocks_screen.png"
            image.save(save_path, format="PNG")
            display_on_inky(save_path)
        else:
            save_path = "inky_stocks.png"
            image.save(save_path, format="PNG")

    except Exception as e:
        print(f"Error: {e}")
