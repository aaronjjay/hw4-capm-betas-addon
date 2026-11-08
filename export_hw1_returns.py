"""Write the two derived return series this repository publishes.

Run it with the HW 1 pipeline's environment, after that pipeline has built
its data:

    python export_hw1_returns.py <path-to-hw1-repository>

It reads the HW 1 pipeline's CRSP monthly stock file and its six
size/book-to-market portfolio returns, and writes only derived series:

- ``hw1_market_return.csv``: the value-weighted market return, rebuilt from
  the CRSP monthly stock file by HW 1's ``calc_CRSP_value_weighted_index``,
  on calendar month-end dates.
- ``hw1_ff6_portfolio_returns.csv``: value-weighted returns of the six
  Fama-French (1993) size/book-to-market portfolios, as HW 1 builds them.

No stock-level row, and none of CRSP's own index series, is written.
"""

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent


def main(hw1_dir):
    hw1_dir = Path(hw1_dir).resolve()
    data_dir = hw1_dir / "_data"
    sys.path.insert(0, str(hw1_dir / "src"))

    import calc_CRSP_indices
    import pull_CRSP_stock

    msf = pull_CRSP_stock.load_CRSP_monthly_file(data_dir=data_dir)
    # The stock file dates each row by its last trading day (`date`) and by
    # its calendar month end (`jdate`). The index function lags market caps
    # by one calendar month, so it is given calendar month ends: with trading
    # days, every month that ends on a weekend would find no lagged weight.
    msf = msf.assign(date=msf["jdate"])
    vw = calc_CRSP_indices.calc_CRSP_value_weighted_index(msf, freq="ME")
    market = (
        vw[["vwretd"]]
        .rename_axis("date")
        .reset_index()
        .astype({"vwretd": "float64"})
        .dropna(subset=["vwretd"])
    )
    market["date"] = pd.to_datetime(market["date"]).dt.strftime("%Y-%m-%d")
    market.to_csv(HERE / "hw1_market_return.csv", index=False, lineterminator="\n")

    ports = pd.read_parquet(data_dir / "FF_1993_vwret.parquet")
    ports = (
        ports.rename(columns={"jdate": "date", "sbport": "portfolio", "vwret": "ret"})[
            ["date", "portfolio", "ret"]
        ]
        .astype({"ret": "float64"})
        .dropna(subset=["ret"])
        .sort_values(["date", "portfolio"])
    )
    ports["date"] = pd.to_datetime(ports["date"]).dt.strftime("%Y-%m-%d")
    ports.to_csv(HERE / "hw1_ff6_portfolio_returns.csv", index=False, lineterminator="\n")

    for name, df in [("market", market), ("portfolios", ports)]:
        print(f"{name}: {len(df)} rows, {df['date'].min()} to {df['date'].max()}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python export_hw1_returns.py <path-to-hw1-repository>")
    main(sys.argv[1])
