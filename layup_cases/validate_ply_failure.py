
from pathlib import Path
import csv
import math
import re

ROOT = Path(__file__).resolve().parent

CASES = [
    "layup_0_45_m45_90",
    "layup_balanced_45",
    "layup_symmetric_0090",
]

# Existing project strength assumptions, MPa
XT, XC = 1500.0, 1000.0
YT, YC = 40.0, 150.0
S12 = 70.0

# Explicit assumption: SXX, SYY and SXY are global components.
# Do not treat results as validated until this is confirmed.
STRESS_IS_GLOBAL = True

FLOAT = r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?"
ROW = re.compile(
    rf"^\s*(\d+)\s+(\d+)\s+"
    rf"({FLOAT})\s+({FLOAT})\s+({FLOAT})\s+"
    rf"({FLOAT})\s+({FLOAT})\s+({FLOAT})"
)
ORI = re.compile(r"\b(ORIM45|ORI45|ORI90|ORI0)_shell")

ANGLE = {
    "ORI0": 0.0,
    "ORI45": 45.0,
    "ORIM45": -45.0,
    "ORI90": 90.0,
}

def number(s):
    return float(s.replace("D", "E").replace("d", "e"))

def read_stress(path):
    records = []
    in_stress = False
    last_record = None

    for line in path.read_text(
        errors="replace"
    ).splitlines():
        lower = line.lower()

        if "stresses (elem, integ.pnt." in lower:
            in_stress = True
            continue

        if "strains (elem, integ.pnt." in lower:
            break

        if not in_stress:
            continue

        # Orientation labels can appear on the next line.
        match_ori = ORI.search(line)
        if match_ori and last_record is not None:
            if records[last_record]["angle"] is None:
                records[last_record]["angle"] = ANGLE[
                    match_ori.group(1)
                ]

        match = ROW.match(line)
        if match:
            values = [number(x) for x in match.groups()[2:]]
            tag = ORI.search(line)

            record = {
                "element": int(match.group(1)),
                "ip": int(match.group(2)),
                "sxx": values[0],
                "syy": values[1],
                "szz": values[2],
                "sxy": values[3],
                "sxz": values[4],
                "syz": values[5],
                "angle": ANGLE[tag.group(1)] if tag else None,
            }
            records.append(record)
            last_record = len(records) - 1

    return records

def calculate(record):
    # Assumption: GLOBAL=NO output is already ply-local.
    # Do NOT rotate the stresses a second time.
    s1 = record["sxx"]
    s2 = record["syy"]
    t12 = record["sxy"]

    fi1 = abs(s1) / (XT if s1 >= 0 else XC)
    fi2 = abs(s2) / (YT if s2 >= 0 else YC)
    fi6 = abs(t12) / S12

    modes = {
        "Longitudinal": fi1,
        "Transverse": fi2,
        "In-plane shear": fi6,
    }
    mode = max(modes, key=modes.get)

    return s1, s2, t12, max(modes.values()), mode

   

def main():
    output = ROOT / "failure_validation_transformed.csv"
    summary = []

    with output.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "layup", "element", "integration_point",
            "ply_angle_deg", "sigma1_MPa", "sigma2_MPa",
            "tau12_MPa", "failure_index", "governing_mode",
            "stress_input_assumption",
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()

        for case in CASES:
            path = ROOT / f"{case}_plylocal.dat"
            if not path.exists():
                path = ROOT / f"{case}_plyprint.dat"
            if not path.exists():
                print(f"MISSING: {case} stress file")
                continue

            records = read_stress(path)
            valid = [r for r in records if r["angle"] is not None]

            if not valid:
                print(f"NO MAPPED STRESSES: {case}")
                continue

            evaluated = []
            for r in valid:
                s1, s2, t12, fi, mode = calculate(r)
                evaluated.append((fi, r, s1, s2, t12, mode))
                writer.writerow({
                    "layup": case,
                    "element": r["element"],
                    "integration_point": r["ip"],
                    "ply_angle_deg": r["angle"],
                    "sigma1_MPa": s1,
                    "sigma2_MPa": s2,
                    "tau12_MPa": t12,
                    "failure_index": fi,
                    "governing_mode": mode,
                    "stress_input_assumption": (
                        "global; transform applied"
                    ),
                })

            worst = max(evaluated, key=lambda x: x[0])
            fi, r, s1, s2, t12, mode = worst
            summary.append((case, fi, r["angle"], r["element"],
                            r["ip"], mode, len(valid), len(records)))

    print("\nPRELIMINARY TRANSFORMED-STRESS RESULTS")
    for case, fi, angle, elem, ip, mode, valid, total in summary:
        print(
            f"{case}: max FI={fi:.6f}; angle={angle:+.0f} deg; "
            f"element={elem}; IP={ip}; mode={mode}; "
            f"mapped={valid}/{total}"
        )

    print(f"\nOutput: {output}")
    print("WARNING: results are not validated until the")
    print("CalculiX stress coordinate convention is confirmed.")

if __name__ == "__main__":
    main()
