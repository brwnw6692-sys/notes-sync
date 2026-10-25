"""Build a compact gazetteer from GeoNames country dumps (CC-BY, download.geonames.org).

Run locally after downloading per-country .txt files (e.g. PS, IL, LB, SY, IQ, IR, YE) into a
folder that is NOT committed:
    python -m collector.geo.build_gazetteer <dump_dir> <out.json> --min-population 500
Lower --min-population reaches smaller villages at the cost of a larger file.
GeoNames data is CC-BY 4.0 — keep attribution to https://www.geonames.org when you ship it.
"""
import json
import sys
from pathlib import Path

_POPULATED = "P"          # GeoNames feature class for populated places
_ARABIC = range(0x0600, 0x06FF + 1)


def _has_arabic_or_persian(s: str) -> bool:
    return any(ord(ch) in _ARABIC for ch in s)


def parse_line(line: str):
    cols = line.rstrip("\n").split("\t")
    if len(cols) < 19:
        return None
    if cols[6] != _POPULATED:
        return None
    try:
        lat, lon = float(cols[4]), float(cols[5])
        population = int(cols[14] or 0)
    except ValueError:
        return None
    names = [cols[1]]
    for alt in cols[3].split(","):
        alt = alt.strip()
        if alt and alt not in names:
            names.append(alt)
    # Keep the local-script (Arabic/Persian) names first; they are what messages use.
    names.sort(key=lambda n: not _has_arabic_or_persian(n))
    return {"id": f"gn{cols[0]}", "names": names, "lat": lat, "lon": lon, "population": population}


def build_entries(lines, min_population: int = 500):
    out = []
    for line in lines:
        e = parse_line(line)
        if e and e["population"] >= min_population:
            out.append(e)
    return out


def main(argv=None) -> int:
    argv = argv or sys.argv[1:]
    dump_dir, out = Path(argv[0]), Path(argv[1])
    min_pop = 500
    if "--min-population" in argv:
        min_pop = int(argv[argv.index("--min-population") + 1])
    lines = []
    for txt in sorted(dump_dir.glob("*.txt")):
        lines.extend(txt.read_text(encoding="utf-8").splitlines())
    entries = build_entries(lines, min_population=min_pop)
    out.write_text(json.dumps(entries, ensure_ascii=False), encoding="utf-8")
    print(f"gazetteer: {len(entries)} places (min_population={min_pop})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
