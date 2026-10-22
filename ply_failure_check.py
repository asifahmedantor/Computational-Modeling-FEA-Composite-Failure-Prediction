
import re
import csv
from pathlib import Path

source = Path("mesh_convergence/mesh_32x16/mesh_32x16_plycheck.dat")
output = Path("mesh_convergence/ply_failure_check.csv")

# Illustrative strengths in MPa — replace with verified CFRP data.
Xt, Xc = 1500.0, 1000.0
Yt, Yc = 40.0, 150.0
S12 = 70.0

number = r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[Ee][-+]?\d+)?"
pattern = re.compile(
    rf"^\s*(\d+)\s+(\d+)\s+"
    + r"\s+".join([f"({number})"] * 6)
    + r"\s+(\S+)\s*$"
)

rows = []

for line in source.read_text(errors="replace").splitlines():
    match = pattern.match(line)
    if not match:
        continue

    element, ip = int(match.group(1)), int(match.group(2))
    sxx, syy, szz, sxy, syz, szx = map(
        float, match.groups()[2:8]
    )
    orientation = match.group(9)

    # Four consecutive groups of 8 integration points.
    ply = (ip - 1) // 8 + 1
    if not 1 <= ply <= 4:
        continue

        # Preliminary maximum-stress check.
    fi_x = abs(sxx) / (Xt if sxx >= 0 else Xc)
    fi_y = abs(syy) / (Yt if syy >= 0 else Yc)
    fi_s = abs(sxy) / S12
    fi = max(fi_x, fi_y, fi_s)

    rows.append({
        "element": element,
        "integration_point": ip,
        "ply_group": ply,
        "orientation_label": orientation,
        "SXX_MPa": sxx,
        "SYY_MPa": syy,
        "SXY_MPa": sxy,
        "provisional_FI": fi,
    })

if not rows:
    raise SystemExit(
        "No stress rows parsed. Check the .dat file format."
    )

output.parent.mkdir(parents=True, exist_ok=True)
with output.open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=rows[0].keys())
    writer.writeheader()
    writer.writerows(rows)

print("Parsed stress records:", len(rows))
print("Saved:", output)

for ply in range(1, 5):
    group = [r for r in rows if r["ply_group"] == ply]
    if not group:
        print(f"Ply group {ply}: no records")
        continue

    worst = max(group, key=lambda r: r["provisional_FI"])
    print(
        f"Ply group {ply}: "
        f"orientation={worst['orientation_label']}, "
        f"element={worst['element']}, "
        f"IP={worst['integration_point']}, "
        f"provisional FI={worst['provisional_FI']:.6f}"
    )

print(
    "WARNING: Verify integration-point ordering, stress axes, "
    "units, and actual material strengths before interpreting FI."
)
