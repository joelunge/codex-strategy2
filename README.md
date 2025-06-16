# Backtest Strategy

This project implements a simple backtesting engine for a 5‑minute EMA cross strategy.

## Requirements

- Python 3.10+
- pandas
- numpy
- PyYAML
- mysql-connector-python
- pytest (for testing)

Install dependencies using pip:

```bash
pip install pandas numpy PyYAML mysql-connector-python pytest
```

## Usage

Run the backtest via the CLI:

```bash
python backtest.py --symbol BTCUSDT --from "2024-06-09 00:00" --to "2024-06-16 23:59"
```

This will read candle data from the MySQL database `sct_2024` and produce the files
`trades.csv`, `summary.txt` and `equity.csv`.

Hyperparameters can be overridden via command line or YAML file using
`--hyperparam_config params.yaml`.

## Tests

Run tests with:

```bash
pytest
```
