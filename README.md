# Inky Stocks

A stock ticker for the Raspberry Pi Zero & Pimoroni Inky displays, fetching daily stock performance from the Yahoo Finance API:

- Supports any symbol on Yahoo Finance
- Displays the most recent day if the market is closed
- Works for 24/7 symbols like BTC-USD
- Plots the end of the previous day if the market opened <2 hours ago
- Supports both Inky pHAT (250x122) and Inky wHAT (400x300) displays

![Output on the Inky pHAT](readme-img/photo.jpg)

## Setup

You'll need a Raspberry Pi Zero 2 (or WH) with either:
- [Pimoroni Inky pHAT](https://shop.pimoroni.com/products/inky-phat) (250x122 version)
- [Pimoroni Inky wHAT](https://shop.pimoroni.com/products/inky-what)

[Install the Inky library](https://learn.pimoroni.com/article/getting-started-with-inky-phat) on your Raspberry Pi before running this script.

1. Activate your Python virtual environment, e.g. the default from the Inky pHAT install guide:

   ```bash
   source ~/.virtualenvs/pimoroni/bin/activate
   ```

2. Install the project dependencies:

   ```bash
   pip install -r requirements.txt
   ```

## Example usage

| Index | Stock | Crypto |
|---------|-------------|---------|
| `python stocks.py --symbol ^FTSE` | `python stocks.py --symbol AAPL` | `python stocks.py --symbol BTC-USD` |
| ![FTSE](readme-img/example_ftse.png) | ![AAPL](readme-img/example_aapl.png) | ![BTC](readme-img/example_btc.png) |

### Multiple symbols (wHAT only)

```bash
# Show 3 major indices
python stocks.py --symbols ^GSPC ^FTSE ^DJI
```

### Options

- Add the `--three-color` flag if you have a black/white/red variant of the display and you want the red highlights.
- Install the Pimoroni LED SHIM alongside the pHAT and it'll will light up green or red depending on whether the stock is up or down.
- You can test without hardware by running the display variant script directly (`stocks_phat.py` or `stocks_what.py`) with the same arguments. The screen output will be saved as a PNG.

### Auto refresh

1. Create a bash script in the project directory and make it executable (`touch run.sh && chmod +x run.sh`):

    ```bash
    #!/bin/bash
    source ~/.virtualenvs/pimoroni/bin/activate
    python ~/inky-stocks/stocks.py --symbol ^FTSE --three-color
    ```

2. Add a cron job to run the script every 15 minutes:

    ```bash
    crontab -e
    ```

    ```
    */15 * * * * ~/inky-stocks/run.sh
    ```

## Disclaimer

Obviously this is just for fun, there are no guarantees about the accuracy of the data, and you shouldn't use this to make any financial decisions. :)
