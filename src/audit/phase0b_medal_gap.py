"""
phase0b_medal_gap.py
=====================
Detailed check of the 2020/2024 medal gap and duplicate rows.
"""

from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
AE_PATH = RAW_DIR / "athlete_events_through_2026.csv"
MT_PATH = RAW_DIR / "medal_table_summary.csv"

YEAR = "Year"
NOC = "NOC"
SPORT = "Sport"
EVENT = "Event"
MEDAL = "Medal"
SEASON = "Season"
NAME = "Name"
TEAM = "Team"
GAMES = "Games"


def main():
    ae = pd.read_csv(AE_PATH, encoding="utf-8", low_memory=False)
    mt = pd.read_csv(MT_PATH, encoding="utf-8", low_memory=False)

    report = []
    package = []

    # --- 1) Quick look at medal_table ---
    report.append("# phase0b - medal gap audit\n")
    report.append("## medal_table head")
    report.append("```")
    report.append(mt.head(5).to_string())
    report.append("```")
    report.append("cols: %s" % list(mt.columns))
    package.append("mt_cols: %s" % list(mt.columns))
    package.append("mt_head: %s" % mt.head(2).to_dict(orient="records"))

    # --- 2) Medals by year ---
    report.append("\n## medal_rows by year")
    rows = []
    for y in [2008, 2012, 2016, 2020, 2024, 2026]:
        sub = ae[ae[YEAR] == y]
        if len(sub) == 0:
            continue
        n_events = sub[EVENT].nunique()
        n_events_medal = sub[sub[MEDAL].notna()][EVENT].nunique()
        n_noc = sub[NOC].nunique()
        n_noc_medal = sub[sub[MEDAL].notna()][NOC].nunique()
        n_rows = len(sub)
        n_medal = int(sub[MEDAL].notna().sum())
        seasons = sub[SEASON].unique().tolist()
        rows.append(dict(year=y, season=seasons, rows=n_rows,
                         events=n_events, events_medal=n_events_medal,
                         nocs=n_noc, nocs_medal=n_noc_medal, medal_rows=n_medal))
        package.append("year=%d season=%s rows=%d events=%d events_with_medal=%d nocs=%d nocs_with_medal=%d medal_rows=%d" % (
            y, seasons, n_rows, n_events, n_events_medal, n_noc, n_noc_medal, n_medal))
    report.append("```")
    report.append(pd.DataFrame(rows).to_string())
    report.append("```")

    # --- 3) Events in 2020/2024 with no medal recorded ---
    report.append("\n## events in 2020/2024 without ANY medal")
    for y in [2016, 2020, 2024]:
        sub = ae[ae[YEAR] == y]
        events_no_medal = sub.groupby(EVENT)[MEDAL].apply(lambda s: s.notna().sum()).pipe(lambda s: s[s == 0].index.tolist())
        package.append("year=%d events_with_no_medal: %d" % (y, len(events_no_medal)))
        if len(events_no_medal) <= 10:
            package.append("  " + str(events_no_medal))
        report.append("- %d: %d events with zero medals" % (y, len(events_no_medal)))
        if len(events_no_medal) <= 20:
            report.append("  " + str(events_no_medal))

    # --- 4) NOCs present in medal_table but missing from ae (2020/2024) ---
    report.append("\n## NOC cross-check for 2020/2024")
    mt_year = "Year" if "Year" in mt.columns else ("year" if "year" in mt.columns else None)
    mt_noc = "NOC" if "NOC" in mt.columns else ("noc" if "noc" in mt.columns else None)
    if mt_year and mt_noc:
        for y in [2020, 2024]:
            mt_sub = mt[mt[mt_year] == y]
            ae_sub = ae[(ae[YEAR] == y) & ae[MEDAL].notna()]
            if len(mt_sub) == 0:
                package.append("year=%d not in medal_table" % y)
                continue
            mt_nocs = set(mt_sub[mt_noc].dropna().unique())
            ae_nocs = set(ae_sub[NOC].dropna().unique())
            missing = mt_nocs - ae_nocs
            package.append("year=%d mt_nocs=%d ae_medal_nocs=%d missing_in_ae=%d" % (
                y, len(mt_nocs), len(ae_nocs), len(missing)))
            if 0 < len(missing) <= 15:
                package.append("  missing: " + str(sorted(missing)))
    else:
        package.append("medal_table: cannot find Year/NOC columns")

    # --- 5) Year 2026 ---
    report.append("\n## year 2026")
    sub26 = ae[ae[YEAR] == 2026]
    package.append("year=2026 rows=%d nocs=%d sports=%d medal_rows=%d seasons=%s" % (
        len(sub26), sub26[NOC].nunique(), sub26[SPORT].nunique(),
        int(sub26[MEDAL].notna().sum()), sub26[SEASON].unique().tolist()))

    # --- 6) Sample of duplicate rows ---
    report.append("\n## duplicate sample")
    dup_mask = ae.duplicated(keep=False)
    dup = ae[dup_mask].sort_values([YEAR, NOC, NAME]).head(20)
    package.append("duplicate_rows_total_participating_in_dup_groups=%d" % int(dup_mask.sum()))
    keep_sample_cols = [c for c in [YEAR, SEASON, NOC, NAME, "Sex", SPORT, EVENT, MEDAL, TEAM] if c in ae.columns]
    report.append("sample cols: %s" % keep_sample_cols)
    report.append("```")
    report.append(dup[keep_sample_cols].head(20).to_string())
    report.append("```")

    # Save outputs
    out = PROJECT_ROOT / "reports" / "phase0b_medal_gap.md"
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(report))

    print("\n" + "=" * 60)
    print("PACKAGE_FOR_CHAT_BEGIN")
    print("=" * 60)
    for line in package:
        print(line)
    print("=" * 60)
    print("PACKAGE_FOR_CHAT_END")
    print("=" * 60)
    print("full report: %s" % out)


if __name__ == "__main__":
    main()
