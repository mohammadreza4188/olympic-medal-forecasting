"""
clean_macro.py
===============
Final cleaning of the macro panel:
- drop MIX and other non-country rows
- fix the FutureWarning on boolean downcast
- save v1
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED = PROJECT_ROOT / "data" / "processed"
REPORTS = PROJECT_ROOT / "reports"

IN_PATH  = PROCESSED / "panel_summer_macro.csv"
OUT_PATH = PROCESSED / "panel_summer_macro_v1.csv"

DROP_NOCS = {"MIX"}  # Historical mixed teams, not a country


def main():
    pkg = []
    df = pd.read_csv(IN_PATH, encoding="utf-8-sig", low_memory=False)
    pkg.append("loaded: %s" % str(df.shape))

    n_before = len(df)
    df = df[~df["NOC"].isin(DROP_NOCS)].copy()
    pkg.append("dropped MIX rows: %d -> %d" % (n_before, len(df)))

    # Avoid FutureWarning: use isin instead of fillna(False).astype(bool)
    df["has_mt_row"] = df["has_mt_row"].astype(str).str.lower().isin(["true","1","1.0"])

    # Fill country_name for standard NOCs with their own NOC code
    df["country_name"] = df.apply(
        lambda r: r["country_name"] if isinstance(r["country_name"], str) and r["country_name"].strip() != ""
                  else r["NOC"], axis=1
    )

    # Sort and save
    df = df.sort_values(["Year","NOC"]).reset_index(drop=True)
    df.to_csv(OUT_PATH, index=False, encoding="utf-8-sig")

    pkg.append("\nfinal shape: %s" % str(df.shape))
    pkg.append("years: %d..%d  n=%d" % (df["Year"].min(), df["Year"].max(), df["Year"].nunique()))
    pkg.append("unique NOCs: %d" % df["NOC"].nunique())
    pkg.append("all rows have non-null Year: %s" % bool(df["Year"].notna().all()))

    pkg.append("\nnull rates (top 5):")
    pkg.append(df.isna().mean().sort_values(ascending=False).head(5).round(3).to_string())

    pkg.append("\nrows per NOC (top 3):")
    pkg.append(df["NOC"].value_counts().head(3).to_string())

    pkg.append("\ntarget summary (mt_total):")
    pkg.append(df["mt_total"].describe().round(2).to_string())

    pkg.append("\nzero-medal share per year (key years):")
    for y in [2008, 2012, 2016, 2020, 2024]:
        sub = df[df["Year"] == y]
        zero = (sub["mt_total"] == 0).mean()
        pkg.append("  %d: zero_medal_share=%.2f  n=%d" % (y, zero, len(sub)))

    pkg.append("\nsaved: %s" % OUT_PATH)

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in pkg:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)


if __name__ == "__main__":
    main()
