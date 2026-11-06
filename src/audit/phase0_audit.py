"""
phase0_audit.py
===============
Phase 0 audit: data quality and coverage for the three GitHub source files.

Run (from project root, i.e., olympic-sport-mgmt):
    python src/audit/phase0_audit.py

Output:
1) Compact summary in the console between PACKAGE_FOR_CHAT_BEGIN/END
2) Full report saved to reports/phase0_data_audit.md
"""

from pathlib import Path
from datetime import datetime
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

FILES = {
    "athlete_events": RAW_DIR / "athlete_events_through_2026.csv",
    "medal_table":    RAW_DIR / "medal_table_summary.csv",
    "edition_meta":   RAW_DIR / "edition_metadata.csv",
}

CRITICAL_YEARS = [2008, 2012, 2016, 2020, 2024]

SPECIAL_NOCS = ["URS", "GDR", "TCH", "YUG", "FRG", "SCG", "ANZ", "BOH",
                "EUN", "ROC", "IOA", "AIN", "EOR", "EUA", "UAR"]


def read_csv_safe(path):
    if not path.exists():
        return None, "FILE_NOT_FOUND"
    for enc in ["utf-8", "utf-8-sig", "latin-1", "cp1252"]:
        try:
            return pd.read_csv(path, encoding=enc, low_memory=False), enc
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return None, "READ_ERROR: " + str(e)
    return None, "DECODE_ERROR"


def detect_column(df, candidates):
    lower = {c.lower(): c for c in df.columns}
    for cand in candidates:
        if cand.lower() in lower:
            return lower[cand.lower()]
    return None


def missing_top(df, top=15):
    miss = df.isna().mean().sort_values(ascending=False)
    return miss[miss > 0].head(top)


def audit_athlete_events(df, report, package):
    report.append("\n## A.1. athlete_events_through_2026.csv\n")
    report.append("- shape: " + str(df.shape))
    report.append("- columns: " + str(list(df.columns)))
    report.append("\n**dtypes:**\n```")
    report.append(df.dtypes.to_string())
    report.append("```")

    year_col   = detect_column(df, ["Year", "year"])
    season_col = detect_column(df, ["Season", "season"])
    noc_col    = detect_column(df, ["NOC", "noc", "Noc"])
    sport_col  = detect_column(df, ["Sport", "sport"])
    event_col  = detect_column(df, ["Event", "event"])
    medal_col  = detect_column(df, ["Medal", "medal"])
    sex_col    = detect_column(df, ["Sex", "sex", "Gender", "gender"])

    report.append("- Year=%s Season=%s NOC=%s Sport=%s Event=%s Medal=%s Sex=%s" % (
        year_col, season_col, noc_col, sport_col, event_col, medal_col, sex_col))

    package.append("athlete_events: shape=%s" % str(df.shape))
    package.append("  Year=%s Season=%s NOC=%s Sport=%s Event=%s Medal=%s Sex=%s" % (
        year_col, season_col, noc_col, sport_col, event_col, medal_col, sex_col))

    if year_col:
        years = sorted(df[year_col].dropna().unique().tolist())
        report.append("- years: min=%s max=%s n=%s" % (min(years), max(years), len(years)))
        package.append("  years: %s..%s n=%s" % (min(years), max(years), len(years)))

    if season_col:
        seasons = df[season_col].dropna().unique().tolist()
        package.append("  seasons: %s" % str(seasons))

    if noc_col:
        nocs = df[noc_col].dropna().unique()
        report.append("- noc_unique: %s" % len(nocs))
        package.append("  noc_unique: %s" % len(nocs))
        special_present = sorted(set(SPECIAL_NOCS) & set(nocs))
        report.append("- special_nocs_present: %s" % special_present)
        package.append("  special_nocs_present: %s" % special_present)

    if sport_col:
        report.append("- sports_unique: %s" % df[sport_col].nunique())
        package.append("  sports_unique: %s" % df[sport_col].nunique())
    if event_col:
        report.append("- events_unique: %s" % df[event_col].nunique())
        package.append("  events_unique: %s" % df[event_col].nunique())

    miss = missing_top(df)
    if len(miss) > 0:
        report.append("\n**missing rate (top):**\n```")
        report.append(miss.round(3).to_string())
        report.append("```")

    dup = int(df.duplicated().sum())
    report.append("- full_duplicates: %s" % dup)
    package.append("  full_duplicates: %s" % dup)

    if year_col:
        report.append("\n**critical years coverage:**\n")
        report.append("| year | rows | noc | sports | medal_rows |")
        report.append("|---|---|---|---|---|")
        package.append("  critical_years:")
        for y in CRITICAL_YEARS:
            sub = df[df[year_col] == y]
            n_rows = len(sub)
            n_noc = sub[noc_col].nunique() if noc_col else "-"
            n_sport = sub[sport_col].nunique() if sport_col else "-"
            n_medal = int(sub[medal_col].notna().sum()) if medal_col else "-"
            report.append("| %s | %s | %s | %s | %s |" % (y, n_rows, n_noc, n_sport, n_medal))
            package.append("    %s: rows=%s noc=%s sports=%s medal_rows=%s" % (
                y, n_rows, n_noc, n_sport, n_medal))

    if all([medal_col, year_col, noc_col, sport_col, event_col]):
        report.append("\n**team medal check:**\n")
        for y in [2020, 2024]:
            sub = df[(df[year_col] == y) & (df[medal_col].notna())]
            if len(sub) == 0:
                continue
            grp = sub.groupby([noc_col, sport_col, event_col, medal_col]).size()
            report.append("- %s: groups=%s mean_athletes_per_medal=%.2f max=%s" % (
                y, len(grp), grp.mean(), grp.max()))
            package.append("  team_check_%s: groups=%s mean=%.2f max=%s" % (
                y, len(grp), grp.mean(), grp.max()))

    if year_col:
        yearly = df.groupby(year_col).size().sort_index().tail(15)
        report.append("\n**rows per year (last 15):**\n```")
        report.append(yearly.to_string())
        report.append("```")

    return dict(year_col=year_col, season_col=season_col, noc_col=noc_col,
                sport_col=sport_col, event_col=event_col,
                medal_col=medal_col, sex_col=sex_col)


def audit_medal_table(df, report, package):
    report.append("\n## A.2. medal_table_summary.csv\n")
    report.append("- shape: " + str(df.shape))
    report.append("- columns: " + str(list(df.columns)))
    report.append("\n**dtypes:**\n```")
    report.append(df.dtypes.to_string())
    report.append("```")
    report.append("\n**head(5) first 15 cols:**\n```")
    report.append(df.head(5).iloc[:, :15].to_string())
    report.append("```")
    package.append("medal_table: shape=%s" % str(df.shape))

    year_col = detect_column(df, ["Year", "year", "Edition", "edition"])
    if year_col:
        years = sorted(df[year_col].dropna().unique().tolist())
        report.append("- years: min=%s max=%s n=%s" % (min(years), max(years), len(years)))
        package.append("  years: %s..%s n=%s" % (min(years), max(years), len(years)))

    miss = missing_top(df)
    if len(miss) > 0:
        report.append("\n**missing:**\n```")
        report.append(miss.round(3).to_string())
        report.append("```")

    dup = int(df.duplicated().sum())
    report.append("- duplicates: %s" % dup)
    package.append("  full_duplicates: %s" % dup)
    return dict(year_col=year_col)


def audit_edition_metadata(df, report, package):
    report.append("\n## A.3. edition_metadata.csv\n")
    report.append("- shape: " + str(df.shape))
    report.append("- columns: " + str(list(df.columns)))
    report.append("\n**dtypes:**\n```")
    report.append(df.dtypes.to_string())
    report.append("```")
    package.append("edition_meta: shape=%s" % str(df.shape))

    if len(df) <= 60:
        report.append("\n**all rows:**\n```")
        report.append(df.to_string())
        report.append("```")
    else:
        report.append("\n**head(10):**\n```")
        report.append(df.head(10).to_string())
        report.append("```")

    report.append("- duplicates: %s" % int(df.duplicated().sum()))
    return {}


def cross_file_checks(ae, mt, ae_cols, mt_cols, report, package):
    report.append("\n## B. cross-file checks\n")
    package.append("cross_file:")
    medal_col = ae_cols.get("medal_col")
    year_col  = ae_cols.get("year_col")
    noc_col   = ae_cols.get("noc_col")
    event_col = ae_cols.get("event_col")
    if all([medal_col, year_col, noc_col, event_col]):
        try:
            sub = ae.dropna(subset=[medal_col])
            unique_medals = (
                sub.drop_duplicates(subset=[noc_col, year_col, event_col, medal_col])
                   .groupby([noc_col, year_col]).size()
                   .rename("medals_from_events").reset_index()
            )
            report.append("- (NOC, Year) medal pairs: %s" % len(unique_medals))
            report.append("\n**head(5):**\n```")
            report.append(unique_medals.head(5).to_string())
            report.append("```")
            package.append("  ae_noc_year_medal_pairs: %s" % len(unique_medals))
        except Exception as e:
            report.append("- error: %s" % e)
            package.append("  error: %s" % e)


def main():
    report = [
        "# Phase 0 Data Audit\n",
        "**date:** " + datetime.now().strftime("%Y-%m-%d %H:%M") + "\n",
        "**root:** " + str(PROJECT_ROOT) + "\n",
    ]
    package = []

    loaded = {}
    for key, path in FILES.items():
        report.append("\n### file: " + path.name + "\n")
        if not path.exists():
            report.append("FILE NOT FOUND")
            package.append("%s: MISSING" % key)
            loaded[key] = None
            continue
        size_mb = path.stat().st_size / (1024 * 1024)
        report.append("- size: %.2f MB" % size_mb)
        df, enc = read_csv_safe(path)
        if df is None:
            report.append("READ FAIL: %s" % enc)
            package.append("%s: READ_ERROR %s" % (key, enc))
            loaded[key] = None
            continue
        report.append("- encoding: %s" % enc)
        loaded[key] = df

    ae_cols = {}
    mt_cols = {}
    if loaded.get("athlete_events") is not None:
        ae_cols = audit_athlete_events(loaded["athlete_events"], report, package)
    if loaded.get("medal_table") is not None:
        mt_cols = audit_medal_table(loaded["medal_table"], report, package)
    if loaded.get("edition_meta") is not None:
        audit_edition_metadata(loaded["edition_meta"], report, package)

    if loaded.get("athlete_events") is not None and loaded.get("medal_table") is not None:
        cross_file_checks(loaded["athlete_events"], loaded["medal_table"],
                          ae_cols, mt_cols, report, package)

    report.append("\n## Gate 1\n")
    report.append("_to be filled after joint interpretation._\n")

    report_path = REPORTS_DIR / "phase0_data_audit.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in package:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)
    print("\nFull report: %s" % report_path)


if __name__ == "__main__":
    main()
