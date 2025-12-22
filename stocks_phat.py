#!/usr/bin/env python3
"""
Inky Stocks - pHAT Display (250x122)

Displays one stock with graph and LED SHIM support.
"""
import argparse

from PIL import Image, ImageDraw

from stocks_common import (
    config,
    display_on_inky,
    fetch_market_data,
    load_font,
    plot_graph,
)


# pHAT dimensions
WIDTH = 250
HEIGHT = 122

# Layout constants
GRAPH_WIDTH = 185
GRAPH_HEIGHT = 80
INFO_PANEL_WIDTH = 65
TITLE_HEIGHT = 40

# Hardware availability
try:
    DISPLAY_AVAILABLE = True
    from inky.auto import auto
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Warning: Inky display not available... saving image locally")

try:
    import ledshim
    LEDS_AVAILABLE = True
except ImportError:
    LEDS_AVAILABLE = False


def draw_title(draw, x, y, symbol, stock_name):
    font = load_font(20)
    max_length = 16

    full_text = f"{stock_name} ({symbol})"
    if len(full_text) <= max_length:
        text = full_text
    elif len(stock_name) <= max_length:
        text = stock_name
    else:
        text = symbol

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

    # Title top left
    draw_title(draw, 8, 8, symbol, market_data['name'])

    # Info panel on the right - vertical layout (3 rows)
    info_x = WIDTH - INFO_PANEL_WIDTH
    col_height = 40

    draw_trend_arrow(draw, info_x, 0, INFO_PANEL_WIDTH, col_height, market_data['is_up'])
    draw_percentage_change(draw, info_x, col_height, INFO_PANEL_WIDTH, col_height,
                          market_data['first_price'], market_data['last_price'])
    draw_price(draw, info_x, col_height * 2, INFO_PANEL_WIDTH, col_height,
              market_data['last_price'])

    # Graph below title
    graph = plot_graph(market_data['prices'], market_data['latest_day_index'],
                      GRAPH_WIDTH, GRAPH_HEIGHT, config.three_color)
    image.paste(graph, (0, col_height))

    return image


def set_lights(market_data):
    if not LEDS_AVAILABLE:
        return

    if market_data['is_up']:
        ledshim.set_all(0, 255, 0)  # Green for gains
    else:
        ledshim.set_all(255, 0, 0)  # Red for losses
    ledshim.set_clear_on_exit(False)
    ledshim.show()


def main():
    parser = argparse.ArgumentParser(
        description="Display stock market data on Pimoroni Inky pHAT (250x122)")
    parser.add_argument("--symbol", type=str, default="^GSPC",
                       help="Stock symbol to display (default: ^GSPC)")
    parser.add_argument("--three-color", action="store_true",
                       help="Enable black/white/red display")
    args = parser.parse_args()

    config.three_color = args.three_color
    symbol = args.symbol.upper()

    print(f"Display: pHAT ({WIDTH}x{HEIGHT})")
    print(f"Symbol: {symbol}")

    try:
        market_data = fetch_market_data(symbol)
        screen = create_display_image(symbol, market_data)

        if DISPLAY_AVAILABLE:
            display_on_inky(screen)
            set_lights(market_data)
        else:
            filename = "inky_stocks_phat.png"
            screen.save(filename, format="PNG")
            print(f"Saved to {filename}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
