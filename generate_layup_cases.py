
from pathlib import Path

# Prefer the finest existing mesh so all layups use the same mesh.
candidates = [
    Path("mesh_convergence/mesh_32x16/mesh_32x16.inp"),
    Path("cfrp_composite.inp"),
]

source = next((p for p in candidates if p.exists()), None)

if source is None:
    raise FileNotFoundError(
        "Could not find the baseline or 32x16 mesh input file."
    )

text = source.read_text(encoding="utf-8-sig")
lines = text.splitlines()

# Add orientations needed for the new layups.
if "*ORIENTATION, NAME=ORI45" not in text.upper():
    section_index = next(
        i for i, line in enumerate(lines)
        if line.strip().upper().startswith("*SHELL SECTION")
        and "COMPOSITE" in line.upper()
    )

    orientations = [
        "*ORIENTATION, NAME=ORI45, SYSTEM=RECTANGULAR",
        "0.7071067812, 0.7071067812, 0, -0.7071067812, 0.7071067812, 0",
        "*ORIENTATION, NAME=ORIM45, SYSTEM=RECTANGULAR",
        "0.7071067812, -0.7071067812, 0, 0.7071067812, 0.7071067812, 0",
    ]

    lines[section_index:section_index] = orientations

# Find the composite shell section and its four ply rows.
section_index = next(
    i for i, line in enumerate(lines)
    if line.strip().upper().startswith("*SHELL SECTION")
    and "COMPOSITE" in line.upper()
)

end_index = next(
    i for i in range(section_index + 1, len(lines))
    if lines[i].strip().startswith("*")
)

ply_indices = [
    i for i in range(section_index + 1, end_index)
    if lines[i].strip()
    and not lines[i].strip().startswith("**")
]

if len(ply_indices) != 4:
    raise ValueError(
        f"Expected four ply rows; found {len(ply_indices)}. "
        "Inspect the shell section before continuing."
    )

# Bottom-to-top stacking sequences.
cases = {
    "layup_symmetric_0090": ["ORI0", "ORI90", "ORI90", "ORI0"],
    "layup_balanced_45": ["ORI45", "ORIM45", "ORIM45", "ORI45"],
    "layup_0_45_m45_90": ["ORI0", "ORI45", "ORIM45", "ORI90"],
}

out_dir = Path("layup_cases")
out_dir.mkdir(exist_ok=True)

for case_name, orientations in cases.items():
    modified = lines.copy()

    for index, orientation in zip(ply_indices, orientations):
        modified[index] = f"0.5, , CFRP_UD, {orientation}"

    output = out_dir / f"{case_name}.inp"
    output.write_text(
        "\n".join(modified) + "\n",
        encoding="utf-8"
    )
    print(f"Created: {output}")

print(f"\nSource model: {source}")
print("Original input file was not modified.")
