#!/usr/bin/env python3
"""
Inky Stocks - wHAT Display (400x300)

Displays 3 stocks with graphs at the same time in rows.
"""
import argparse

from PIL import Image, ImageDraw

from stocks_common import (
    config,
    display_on_inky,
    fetch_multiple,
    load_font,
    plot_graph,
)


# wHAT dimensions
WIDTH = 400
HEIGHT = 300

# Layout constants
ROW_HEIGHT = 99
ROW_PADDING = 12

# Content area within each row (after padding)
CONTENT_WIDTH = WIDTH - (ROW_PADDING * 2)        # 376px
CONTENT_HEIGHT = ROW_HEIGHT - (ROW_PADDING * 2)  # 75px

GRAPH_WIDTH = 150  # ~40% of content width
GRAPH_HEIGHT = CONTENT_HEIGHT
TITLE_HEIGHT = 26
ARROW_SIZE = 24

# Hardware availability
try:
    DISPLAY_AVAILABLE = True
    from inky.auto import auto
except ImportError:
    DISPLAY_AVAILABLE = False
    print("Warning: Inky display not available... saving image locally")


def draw_title(draw, x, y, symbol, stock_name):
    font = load_font(22)
    max_length = 18

    full_text = f"{stock_name} ({symbol})"
    if len(full_text) <= max_length:
        text = full_text
    elif len(stock_name) <= max_length:
        text = stock_name
    else:
        text = symbol

    draw.text((x, y), text, font=font, fill=(0, 0, 0))


def draw_trend_arrow(draw, x, y, is_up):
    if is_up:
        points = [
            (x + ARROW_SIZE//2, y),
            (x, y + ARROW_SIZE),
            (x + ARROW_SIZE, y + ARROW_SIZE)
        ]
        fill_color = (0, 0, 0)
    else:
        points = [
            (x, y),
            (x + ARROW_SIZE, y),
            (x + ARROW_SIZE//2, y + ARROW_SIZE)
        ]
        fill_color = (255, 0, 0) if config.three_color else (0, 0, 0)
    draw.polygon(points, fill=fill_color)


def draw_percentage_change(draw, x, y, first_price, last_price):
    percent_change = ((last_price - first_price) / first_price) * 100

    if abs(percent_change) >= 10:
        text = f"{'+' if percent_change >= 0 else ''}{int(percent_change)}%"
    else:
        text = f"{'+' if percent_change >= 0 else ''}{percent_change:.1f}%"

    font = load_font(20)
    draw.text((x, y), text, font=font, fill=(0, 0, 0))


def draw_price(draw, x, y, price):
    font = load_font(20)
    price_text = f"{price:.0f}" if price >= 10000 else f"{price:.2f}"
    draw.text((x, y), price_text, font=font, fill=(0, 0, 0))


def create_stock_row(symbol, market_data):
    row_image = Image.new("RGB", (WIDTH, ROW_HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(row_image)

    # Title top left 
    draw_title(draw, ROW_PADDING, ROW_PADDING, symbol, market_data['name'])

    # Row with arrow, percentage change, and price below title
    info_y = ROW_PADDING + TITLE_HEIGHT + 4
    arrow_x = ROW_PADDING
    text_x = arrow_x + ARROW_SIZE + 16

    remaining_height = CONTENT_HEIGHT - TITLE_HEIGHT - 4
    arrow_y = info_y + (remaining_height - ARROW_SIZE) // 2
    draw_trend_arrow(draw, arrow_x, arrow_y, market_data['is_up'])

    text_y = info_y + (remaining_height - 20) // 2
    draw_percentage_change(draw, text_x, text_y,
                          market_data['first_price'], market_data['last_price'])
    draw_price(draw, text_x + 70, text_y, market_data['last_price'])

    # Graph to right of content area
    graph = plot_graph(market_data['prices'], market_data['latest_day_index'],
                      GRAPH_WIDTH, GRAPH_HEIGHT, config.three_color)
    graph_x = WIDTH - GRAPH_WIDTH - ROW_PADDING
    graph_y = ROW_PADDING + (CONTENT_HEIGHT - GRAPH_HEIGHT) // 2
    row_image.paste(graph, (graph_x, graph_y))

    return row_image


def create_display_image(stock_results):
    """Combine multiple stock rows for full wHAT display."""

    valid_results = [r for r in stock_results if not r['error']] # Filter out failed fetches
    if not valid_results:
        return None

    image = Image.new("RGB", (WIDTH, HEIGHT), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    # Place rows at y=0, 100, 200 with divider lines at y=99, 199
    for i, result in enumerate(valid_results):
        row_image = create_stock_row(result['symbol'], result['data'])

        y_offset = i * (ROW_HEIGHT + 1)  # +1 for divider line
        image.paste(row_image, (0, y_offset))

        # Draw separator line after each row (except the last)
        if i < len(valid_results) - 1:
            line_y = y_offset + ROW_HEIGHT
            draw.line([(0, line_y), (WIDTH, line_y)], fill=(0, 0, 0), width=1)

    return image


def main():
    parser = argparse.ArgumentParser(
        description="Display stock market data on Pimoroni Inky wHAT (400x300)")
    parser.add_argument("--symbols", nargs='+', type=str,
                       default=["^GSPC", "^FTSE", "BTC-USD"],
                       help="Stock symbols to display (1-3, default: ^GSPC ^FTSE BTC-USD)")
    parser.add_argument("--symbol", type=str, default=None,
                       help="Single stock symbol (alternative to --symbols)")
    parser.add_argument("--three-color", action="store_true",
                       help="Enable black/white/red display")
    args = parser.parse_args()

    config.three_color = args.three_color

    if args.symbol:
        symbols = [args.symbol.upper()]
    else:
        symbols = [s.upper() for s in args.symbols]

    # Limit to 3 symbols
    if len(symbols) > 3:
        print("Warning: wHAT only shows 3 symbols")
        symbols = symbols[:3]

    print(f"Display: wHAT ({WIDTH}x{HEIGHT})")
    print(f"Symbols: {', '.join(symbols)}")

    try:
        stock_results = fetch_multiple(symbols)

        for result in stock_results:
            if result['error']:
                print(f"Error fetching {result['symbol']}: {result['error']}")

        screen = create_display_image(stock_results)

        if screen is None:
            print("No valid stock data to display")
            return

        if DISPLAY_AVAILABLE:
            display_on_inky(screen)
        else:
            filename = "inky_stocks_what.png"
            screen.save(filename, format="PNG")
            print(f"Saved to {filename}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
