
# CFRP Composite Plate FEA and Preliminary Failure Analysis

## Project Overview

This project investigates the structural response of a four-ply carbon-fiber-reinforced polymer (CFRP) plate using CalculiX finite element analysis (FEA), Python post-processing, and Classical Laminate Theory (CLT).

**Current status:** Preliminary computational study. Ply-level failure predictions and full engineering validation remain incomplete.

## Model

- Plate dimensions: 100 × 50 mm
- Total laminate thickness: 2 mm
- Number of plies: 4
- Stacking sequence: [0/90/0/90]
- Nominal ply thickness: 0.5 mm
- Shell element: S8R
- Solver: CalculiX 2.22
- Analysis: Linear static
- Model units: mm, N, MPa

The input file specifies `EALL, P, 0.02`. If this pressure is applied uniformly over the full 100 × 50 mm plate face, the nominal resultant is 100 N. Confirm the actual loaded surface and boundary conditions in the input file before interpreting results.

## Assumed Material Properties

| Property | Value | Unit |
|---|---:|---|
| E1 | 135000 | MPa |
| E2 | 10000 | MPa |
| E3 | 10000 | MPa |
| nu12 | 0.30 | — |
| nu13 | 0.30 | — |
| nu23 | 0.40 | — |
| G12 | 5000 | MPa |
| G13 | 5000 | MPa |
| G23 | 3571.4286 | MPa |

These are project assumptions, not verified properties for a specified CFRP product.

## FEA Results

The supplied FEA output and post-processing scripts report approximately:

- Maximum nodal displacement magnitude: 5.936 mm
- Maximum calculated nodal von Mises stress: 244.065 MPa
- Maximum absolute SXX component: 255.201 MPa

These values summarize the available result file. They do not establish ply-local stresses or prove composite failure.

## Mesh Convergence

Four meshes were analyzed:

| Mesh | Elements | Max displacement (mm) | Calculated max nodal von Mises (MPa) |
|---|---:|---:|---:|
| 4 × 2 | 8 | 5.935659 | 244.065467 |
| 8 × 4 | 32 | 5.963122 | 243.380981 |
| 16 × 8 | 128 | 5.977103 | 244.137146 |
| 32 × 16 | 512 | 5.984133 | 244.145212 |

Between the two finest meshes, displacement changed by approximately 0.118%, and the calculated nodal von Mises maximum changed by approximately 0.0033%. This supports preliminary convergence of these two monitored quantities only; it does not validate all stress components or ply-level failure indices.

The results are stored in `mesh_convergence/mesh_convergence.csv`.

## Preliminary Ply-Group Failure Index

The current post-processing script parsed 16,384 stress records and reported the following provisional values:

| Ply group | Orientation label | Maximum provisional FI |
|---|---|---:|
| 1 | 0° | 0.199271 |
| 2 | 90° | 0.139689 |
| 3 | 0° | 0.195331 |
| 4 | 90° | 0.195993 |

These values are exploratory only. Section-point ordering, mapping to physical plies, local material-axis transformations, and the assumed strength allowables have not been fully verified. Do not interpret these values as validated safety factors or final failure predictions.

## CLT Analysis

`laminate_abd.py` computes laminate extensional, coupling, and bending stiffness matrices (A, B, and D) for the `[0/90/0/90]` stacking sequence.

The current illustrative CLT failure calculation uses a separate in-plane membrane resultant of `Nx = 1000 N/m` and assumed strength allowables. Its FI is not directly comparable with the transverse-pressure FEA case.

## Reproduce Post-Processing

Install Python 3 with the packages listed in `requirements.txt`, then run from the project directory:

```powershell
python analyze_project.py
```

To run the mesh-convergence study on Windows:

```powershell
python mesh_convergence.py --ccx "D:\Apps\bin\ccx.exe"
```

The mesh-convergence study has already been run for the four meshes listed above. Re-run only if the model, solver settings, or analysis procedure changes.

The preliminary ply-group calculation can be run with:

```powershell
python ply_failure_check.py
```

Check the actual script location and input/output paths in your working copy before running it.

## Validation Still Required

1. Verify the total support reactions against the applied 100 N resultant.
2. Confirm shell section-point ordering and the mapping of records to physical plies.
3. Transform stresses into the correct local material axes for each ply.
4. Replace illustrative strength allowables with documented properties for a specified CFRP product.
5. Recalculate a suitable failure criterion using verified ply-local stresses.
6. Compare FEA and analytical results under consistent loading and boundary conditions.
7. Check units, solver settings, scripts, and output freshness for reproducibility.

## Main Files

- `cfrp_composite.inp` — CalculiX input model
- `cfrp_composite.frd` — FEA field output
- `analyze_project.py` — FEA post-processing and CLT analysis
- `laminate_abd.py` — CLT calculations
- `mesh_convergence.py` — Mesh study generator and runner
- `ply_failure_check.py` — Preliminary stress-record analysis
- `PROJECT_REPORT.md` — Technical report
- `PROJECT_STATUS.md` — Progress and validation status
- `requirements.txt` — Python dependencies

## Conclusion

This repository contains a reproducible preliminary FEA workflow, a four-mesh comparison, CLT stiffness calculations, and exploratory ply-group failure-index post-processing. It is not yet a validated CFRP failure-prediction or engineering-design study. Final conclusions require reaction equilibrium, verified ply-local stress recovery, documented material allowables, and a consistent analytical comparison.
