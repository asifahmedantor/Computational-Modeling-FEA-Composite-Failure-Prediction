import csv
import math
import re
from pathlib import Path

root = Path("layup_cases")
names = [
    "layup_0_45_m45_90",
    "layup_balanced_45",
    "layup_symmetric_0090",
]
number = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][-+]?\d+)?")
rows = []

for name in names:
    path = root / f"{name}.frd"
    section = None
    disp = []
    stress = []

    for line in path.read_text(errors="ignore").splitlines():
        fields = line.split()

        if len(fields) >= 2 and fields[0] == "-4":
            section = fields[1] if fields[1] in ("DISP", "STRESS") else None
            continue
        if fields and fields[0] == "-3":
            section = None
            continue
        if section and line.lstrip().startswith("-1"):
            vals = number.findall(line)
            if len(vals) < 5:
                continue
            try:
                node = int(vals[1])
                v = [float(x.replace("D", "E").replace("d", "e"))
                     for x in vals[2:]]
                if section == "DISP" and len(v) >= 3:
                    disp.append((node, math.sqrt(sum(x*x for x in v[:3]))))
                elif section == "STRESS" and len(v) >= 6:
                    stress.append((node, v[:6]))
            except (ValueError, IndexError):
                pass

    if not disp or not stress:
        print(f"{name}: missing DISP or STRESS records; skipped")
        continue

    max_u = max(disp, key=lambda x: x[1])
    def vm(v):
        sx, sy, sz, txy, tyz, tzx = v
        return math.sqrt(
            0.5*((sx-sy)**2 + (sy-sz)**2 + (sz-sx)**2)
            + 3*(txy*txy + tyz*tyz + tzx*tzx)
        )

    max_vm = max(((vm(v), node) for node, v in stress), key=lambda x: x[0])
    rows.append({
        "layup": name,
        "displacement_records": len(disp),
        "max_displacement_mm": max_u[1],
        "displacement_record_id": max_u[0],
        "stress_records": len(stress),
        "max_calculated_von_mises_MPa": max_vm[0],
        "stress_record_id": max_vm[1],
    })
    print(name, rows[-1])

out = root / "final_layup_frd_comparison.csv"
if rows:
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"\nSaved: {out.resolve()}")
    print("NOTE: von Mises is a comparison metric, not a validated CFRP failure criterion.")
