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
    print("Warning: Inky pHAT not installed... saving image locally")

try:
    import ledshim
    LEDS_AVAILABLE = True
except ImportError:
    LEDS_AVAILABLE = False

WIDTH, HEIGHT = 250, 122 
FONT_PATH = os.path.join(os.path.dirname(__file__), "fonts", "Roboto-Bold.ttf")

class Config:
    def __init__(self):
        self.three_color = False

config = Config()


def fetch_market_data(symbol):
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
    
    return {
        'name': stock_name,
        'times': data.index.strftime("%H:%M").tolist(),
        'prices': data["Close"].values.flatten().tolist(),
        'latest_day_index': len(data) - len(latest_day_data)
    }


def plot_graph(prices, latest_day_index):
    plt.figure(figsize=(1.85, 0.8), dpi=100)
    
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
                
                # Special case for consecutive identical prices to avoid divide by zero
                if price_data[i] == price_data[i+1]:
                    if price_data[i] < start_price:
                        plt.plot([x_start, x_end], [price_data[i], price_data[i+1]], color='red', linewidth=line_width)
                    continue
                
                # Both points below start, full red segment
                if price_data[i] < start_price and price_data[i+1] < start_price:
                    plt.plot([x_start, x_end], [price_data[i], price_data[i+1]], color='red', linewidth=line_width)
                
                # Crossing start price, partial red segment
                elif price_data[i] < start_price and price_data[i+1] >= start_price:
                    ratio = (start_price - price_data[i]) / (price_data[i+1] - price_data[i])
                    x_intersect = x_start + ratio
                    plt.plot([x_start, x_intersect], [price_data[i], start_price], color='red', linewidth=line_width)
                
                # Opposite direction
                elif price_data[i] >= start_price and price_data[i+1] < start_price:
                    ratio = (start_price - price_data[i]) / (price_data[i+1] - price_data[i])
                    x_intersect = x_start + ratio
                    plt.plot([x_intersect, x_end], [start_price, price_data[i+1]], color='red', linewidth=line_width)
        
        if latest_day_index > 0:
            # Plot previous day
            plt.plot(range(latest_day_index + 1), prices[:latest_day_index + 1], color='black', linewidth=line_width)
            
            latest_prices = prices[latest_day_index:]
        
            # Plot latest day
            if config.three_color:
                plt.plot(range(latest_day_index, len(prices)), latest_prices, color='black', linewidth=line_width)
                draw_negative_segments(latest_prices, latest_day_index)
            else:
                plt.plot(range(latest_day_index, len(prices)), latest_prices, color='black', linewidth=line_width)
        else:
            # Plot latest day only
            if config.three_color:
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
        graph = graph.resize((185, 80), Image.Resampling.BOX)
        return graph
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def load_font(size):
    try:
        return ImageFont.truetype(FONT_PATH, size)
    except:
        print("Warning: Could not load Roboto font, using default")
        return ImageFont.load_default()


def draw_title(draw, x, y, symbol, stock_name):
    font = load_font(20)
    
    if len(stock_name) > 16:
        text = symbol
    elif len(stock_name) > 10:
        text = stock_name
    else:
        text = f"{stock_name} ({symbol})"
    
    draw.text((x, y), text, font=font, fill=(0, 0, 0))


def draw_trend_arrow(draw, x, y, width, height, is_up):
    padding = 8
    arrow_size = min(width - (padding * 2), height - (padding * 2))
    
    x_offset = width - arrow_size - (padding + 2)
    y_offset = (height - arrow_size) // 2
    
    if is_up:
        points = [
            (x + x_offset + arrow_size//2, y + y_offset),
            (x + x_offset, y + y_offset + arrow_size),
            (x + x_offset + arrow_size, y + y_offset + arrow_size)
        ]
        fill_color = (0, 0, 0)
    else:
        points = [
            (x + x_offset, y + y_offset),
            (x + x_offset + arrow_size, y + y_offset),
            (x + x_offset + arrow_size//2, y + y_offset + arrow_size)
        ]
        fill_color = (255, 0, 0) if config.three_color else (0, 0, 0)
    draw.polygon(points, fill=fill_color)


def draw_percentage_change(draw, x, y, width, height, first_price, last_price):
    percent_change = ((last_price - first_price) / first_price) * 100
    
    if abs(percent_change) >= 10:
        text = f"{'+' if percent_change >= 0 else ''}{int(percent_change)}%"
    else:
        text = f"{'+' if percent_change >= 0 else ''}{percent_change:.1f}%"
    
    font = load_font(20)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    right_margin = 6
    text_x = x + width - text_width - right_margin
    text_y = y + (height - text_height) // 2
        
    draw.text((text_x, text_y), text, font=font, fill=(0, 0, 0))


def draw_price(draw, x, y, width, height, price):
    font = load_font(16)
    price_text = f"{price:.0f}" if price >= 10000 else f"{price:.2f}"
    
    text_bbox = draw.textbbox((0, 0), price_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    right_margin = 6  
    text_x = x + width - text_width - right_margin
    text_y = y + (height - text_height) // 2

    draw.text((text_x, text_y), price_text, font=font, fill=(0, 0, 0))


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
    if len(latest_day) > 1:
        draw_trend_arrow(draw, col_x, 0, col_width, col_height, latest_day[-1] > latest_day[0])
        draw_percentage_change(draw, col_x, col_height, col_width, col_height, latest_day[0], latest_day[-1])
    draw_price(draw, col_x, col_height*2, col_width, col_height, latest_day[-1])
    
    graph = plot_graph(prices, latest_day_index)
    image.paste(graph, (0, col_height))
    return image


def display_on_inky(image):
    display = auto()

    palette = Image.new('P', (1, 1))
    palette.putpalette((255, 255, 255,   # White
                        0, 0, 0,         # Black
                        255, 0, 0))      # Red

    image = image.convert('RGB').quantize(palette=palette)

    display.set_border(display.WHITE)
    display.set_image(image)
    display.show()


def set_lights(market_data):
    latest_day = market_data['prices'][market_data['latest_day_index']:]
    
    if latest_day[-1] > latest_day[0]:
        ledshim.set_all(0, 255, 0)
    else:
        ledshim.set_all(255, 0, 0)
    ledshim.set_clear_on_exit(False)
    ledshim.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Displays stock market data on a Pimoroni InkyPHAT")
    parser.add_argument("--symbol", type=str, default="^GSPC", help="Stock/Index symbol (default: S&P 500)")
    parser.add_argument("--three-color", action="store_true", 
                        help="Enable black/white/red display (default: black/white)")
    args = parser.parse_args()
    config.three_color = args.three_color

    try:
        symbol = args.symbol.upper()
        market_data = fetch_market_data(symbol)
        screen = create_display_image(symbol, market_data)
        
        if DISPLAY_AVAILABLE:
            display_on_inky(screen)
        else:
            screen.save("inky_stocks.png", format="PNG")

        if LEDS_AVAILABLE:
            set_lights(market_data)

    except Exception as e:
        print(f"Error: {e}")
