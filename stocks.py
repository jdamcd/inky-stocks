#!/usr/bin/env python3
"""
Inky Stocks

Automatically detects connected Inky display (pHAT or wHAT) and runs
the appropriate script (stocks_phat.py or stocks_what.py).
"""
import argparse
import sys


# Display dimensions - only new pHAT resolution is supported
PHAT_WIDTH, PHAT_HEIGHT = 250, 122
WHAT_WIDTH, WHAT_HEIGHT = 400, 300


def detect_display_type():
    try:
        from inky.auto import auto
        display = auto()
        width, height = display.width, display.height

        if width == WHAT_WIDTH and height == WHAT_HEIGHT:
            return 'wHAT'
        elif width == PHAT_WIDTH and height == PHAT_HEIGHT:
            return 'pHAT'
        else:
            print(f"Warning: Unknown display size {width}x{height}, defaulting to pHAT")
            return 'pHAT'
    except ImportError:
        print("Warning: Inky library not available, defaulting to pHAT")
        return 'pHAT'
    except Exception as e:
        print(f"Warning: Could not detect display: {e}, defaulting to pHAT")
        return 'pHAT'


def main():
    parser = argparse.ArgumentParser(
        description="Display stock market data on Pimoroni Inky pHAT/wHAT")
    parser.add_argument("--symbol", type=str, default=None,
                       help="Single stock symbol (e.g. --symbol AAPL)")
    parser.add_argument("--symbols", nargs='+', type=str, default=None,
                       help="Multiple stock symbols (e.g. --symbols AAPL MSFT TSLA)")
    parser.add_argument("--three-color", action="store_true",
                       help="Enable black/white/red display")
    args = parser.parse_args()

    display_type = detect_display_type()

    # Build arguments for the target script
    target_args = []
    if args.three_color:
        target_args.append('--three-color')

    if display_type == 'wHAT':
        from stocks_common import config
        config.three_color = args.three_color

        if args.symbols:
            symbols = [s.upper() for s in args.symbols]
        elif args.symbol:
            symbols = [args.symbol.upper()]
        else:
            symbols = ["^GSPC", "^FTSE", "BTC-USD"]

        if len(symbols) > 3:
            print("Warning: wHAT only shows 3 symbols")
            symbols = symbols[:3]

        sys.argv = ['stocks_what.py', '--symbols'] + symbols + target_args
        import stocks_what
        stocks_what.main()

    else:
        from stocks_common import config
        config.three_color = args.three_color

        if args.symbols:
            print("Warning: pHAT only shows 1 symbol")
            symbol = args.symbols[0].upper()
        elif args.symbol:
            symbol = args.symbol.upper()
        else:
            symbol = "^GSPC"

        sys.argv = ['stocks_phat.py', '--symbol', symbol] + target_args
        import stocks_phat
        stocks_phat.main()


if __name__ == "__main__":
    main()
