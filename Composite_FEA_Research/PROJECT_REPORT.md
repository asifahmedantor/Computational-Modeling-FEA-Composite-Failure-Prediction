
# CFRP Composite Plate — FEA Research Project

## 1. Project Overview

This project investigates the preliminary structural response of a Carbon Fiber Reinforced Polymer (CFRP) composite plate using FreeCAD, CalculiX, Python post-processing, and Classical Laminate Theory (CLT).

The project combines:
- Finite Element Analysis (FEA)
- Composite shell modeling
- Mesh convergence assessment
- CLT laminate stiffness calculations
- Preliminary ply-group failure-index calculations
- Automated result extraction and reporting

**Current status:** Preliminary computational analysis completed. Further validation is required before the results can be used for engineering design or definitive composite failure prediction.

---

## 2. Model Description

| Parameter | Value |
|---|---|
| Structure | CFRP composite plate |
| Length | 100 mm |
| Width | 50 mm |
| Total thickness | 2.0 mm |
| Number of plies | 4 |
| Stacking sequence | [0/90/0/90] |
| Element type | S8R shell elements |
| Analysis type | Linear static analysis |
| Solver | CalculiX 2.22 |
| Pre-processing | FreeCAD |
| Post-processing | Python |

The stacking sequence is specified from bottom to top. Each ply has a nominal thickness of 0.5 mm.

The model includes a fixed-edge boundary condition and a transverse loading case. The exact correspondence between the model's constrained edge, applied load, and the physical test configuration should be documented before design-level interpretation.

---

## 3. Assumed Engineering Constants

The following orthotropic engineering constants are used in the current model.

| Property | Value | Unit |
|---|---:|---|
| E1 | 135000 | MPa |
| E2 | 10000 | MPa |
| E3 | 10000 | MPa |
| nu12 | 0.30 | Dimensionless |
| nu13 | 0.30 | Dimensionless |
| nu23 | 0.40 | Dimensionless |
| G12 | 5000 | MPa |
| G13 | 5000 | MPa |
| G23 | 3571.4286 | MPa |

These values are project assumptions. They have not been verified against a datasheet for a specified CFRP product.

The material definition must be checked for consistency with the solver's orthotropic material conventions, reciprocal Poisson ratios, and local material orientations.

---

## 4. Transverse Loading Case

The current FEA model uses a total transverse force of 100 N.

Assuming the force is uniformly distributed over the full 100 mm × 50 mm plate face:

- Loaded area: 0.005 m²
- Total force: 100 N
- Equivalent pressure magnitude: 20000 Pa (20 kPa)

The load magnitude and loaded surface must be checked against the actual CalculiX input file before interpreting the results.

This transverse loading case is distinct from the illustrative in-plane loading case used in the CLT failure calculation.

---

## 5. FEA Results Summary

The existing FRD post-processing workflow reports the following values for the supplied model.

| Quantity | Reported result |
|---|---:|
| Maximum nodal displacement magnitude | Approximately 5.936 mm |
| Maximum calculated nodal von Mises stress | Approximately 244.065 MPa |
| Maximum absolute SXX component | Approximately 255.201 MPa |

These values are descriptive summaries of the available result file.

The reported stress components have not been conclusively mapped to the local material axes of each individual ply. The maximum absolute SXX value is a stress-component maximum and should not be confused with the von Mises stress maximum.

Von Mises stress alone is not an adequate failure criterion for a unidirectional composite laminate.

The displacement magnitude should also be checked for physical plausibility, mesh behavior, boundary-condition effects, and the validity of the linear static assumptions.

---

## 6. Mesh Convergence Assessment

Four mesh configurations were analyzed using S8R shell elements.

| Mesh | S8R elements | Maximum displacement (mm) | Maximum calculated nodal von Mises stress (MPa) |
|---|---:|---:|---:|
| 4 × 2 | 8 | 5.935659 | 244.065467 |
| 8 × 4 | 32 | 5.963122 | 243.380981 |
| 16 × 8 | 128 | 5.977103 | 244.137146 |
| 32 × 16 | 512 | 5.984133 | 244.145212 |

The mesh-convergence script completed the four reported analyses and saved the results in:

`mesh_convergence/mesh_convergence.csv`

### Comparison of the Two Finest Meshes

Between the 16 × 8 and 32 × 16 meshes:

- Maximum displacement changed by approximately 0.118%.
- Maximum calculated nodal von Mises stress changed by approximately 0.0033%.

These small changes indicate numerical stability for the two monitored maximum values across the two finest meshes.

However, this is a preliminary convergence assessment, not proof that every stress component, local stress concentration, ply-level result, or failure index has converged.

The mesh study should also consider reaction forces, displacement at consistent locations, stress sampling conventions, and the effect of boundary-condition singularities.

---

## 7. Classical Laminate Theory (CLT)

The Python script `laminate_abd.py` calculates the laminate extensional, coupling, and bending stiffness matrices:

- A matrix: extensional stiffness
- B matrix: extension-bending coupling stiffness
- D matrix: bending stiffness

The calculations use the stacking sequence [0/90/0/90] and the assumed engineering constants defined in this report.

The unsymmetric stacking sequence produces a nonzero B matrix. This is consistent with extension-bending coupling for an unsymmetric laminate under Classical Laminate Theory.

The calculated matrices are saved as:

- `A_matrix.csv`
- `B_matrix.csv`
- `D_matrix.csv`
- `D_effective.csv`

The effective bending stiffness calculation should be interpreted in accordance with the assumptions implemented in the script.

These analytical matrices are useful for understanding laminate stiffness, but they do not independently validate the three-dimensional or shell FEA solution.

---

## 8. Separate Illustrative CLT Load Case

The current CLT failure calculation uses the following in-plane membrane resultants:

- Nx = 1000 N/m
- Ny = 0 N/m
- Nxy = 0 N/m
- Mx = 0 N
- My = 0 N
- Mxy = 0 N

The script uses the following illustrative strength allowables:

| Strength property | Assumed value |
|---|---:|
| Xt | 1500 MPa |
| Xc | 1000 MPa |
| Yt | 40 MPa |
| Yc | 150 MPa |
| S12 | 70 MPa |

The baseline CLT maximum-stress failure index is approximately 0.00328 for this separate illustrative in-plane loading case.

These strength values are not verified against a specific CFRP material datasheet or test report.

**Important:** This CLT result is not directly comparable to the transverse 100 N FEA load case. A valid comparison requires consistent loading, boundary conditions, material properties, and response quantities.

---

## 9. Preliminary Ply-Group Failure-Index Calculation

The script `ply_failure_check.py` parses stress records from the 32 × 16 mesh's ply-check output.

The latest reported run produced:

- Parsed stress records: 16,384
- Number of reported ply groups: 4
- Records per group: 4,096

### Preliminary Results

| Ply group | Reported orientation | Maximum provisional FI |
|---|---|---:|
| 1 | 0° | 0.199271 |
| 2 | 90° | 0.139689 |
| 3 | 0° | 0.195331 |
| 4 | 90° | 0.195993 |

The results were saved to:

`mesh_convergence/ply_failure_check.csv`

These values are **provisional exploratory results**, not validated ply failure predictions.

Before interpreting them physically, the following must be confirmed:

1. The meaning and ordering of the shell section points and integration points.
2. The mapping of each stress record to the correct physical ply.
3. The local material axes and transformation of stresses into the ply's 1–2 coordinate system.
4. The correct interpretation of normal and shear stress components.
5. The validity of the material strength allowables for the specified CFRP product.
6. The handling of tensile and compressive stress signs in the selected failure criterion.

The existing workflow does not yet establish an unambiguous mapping of every stress record to the four individual laminate plies and their local material axes.

Therefore, the reported FI values must not be used as definitive evidence that the laminate is safe or that failure will not occur.

---

## 10. Earlier Exploratory Failure Index

An earlier exploratory calculation reported a maximum failure index of approximately 6.38002.

That calculation treated global FRD stress components as though their relationship to the local stresses of a particular ply were already established.

The necessary mapping and material-axis transformation have not been validated. Therefore, the value is retained only as a historical exploratory result and is not a validated failure prediction.

It must not be directly compared with the current four ply-group FI values without first reconciling the underlying stress data, coordinate systems, section points, and allowables.

---

## 11. Project Files and Outputs

Important project files include:

| File or directory | Purpose |
|---|---|
| `cfrp_composite.inp` | Main CalculiX input model |
| `cfrp_composite.frd` | Existing FEA field results |
| `cfrp_composite.dat` | Solver output data, if populated |
| `cfrp_composite.sta` | Solver status information |
| `analyze_project.py` | FEA post-processing and CLT analysis |
| `laminate_abd.py` | CLT stiffness and illustrative failure calculations |
| `mesh_convergence.py` | Automated mesh-convergence runner |
| `mesh_convergence/mesh_convergence.csv` | Mesh comparison results |
| `ply_failure_check.py` | Preliminary ply-group failure-index post-processing |
| `mesh_convergence/ply_failure_check.csv` | Preliminary ply-group results |
| `A_matrix.csv` | Laminate extensional stiffness |
| `B_matrix.csv` | Laminate coupling stiffness |
| `D_matrix.csv` | Laminate bending stiffness |
| `load_scaling_results.csv` | Illustrative CLT load-scaling results |
| `load_scaling.png` | Illustrative load-scaling plot |
| `README.md` | Project introduction and instructions |
| `PROJECT_STATUS.md` | Current project status |
| `requirements.txt` | Python dependencies |

Some files may be generated only after the corresponding scripts have run. Their existence and freshness should be verified before submission.

---

## 12. Validation Status

| Check | Status | Comment |
|---|---|---|
| CalculiX static analysis | Completed | Existing solver runs completed successfully |
| FEA field extraction | Preliminary complete | Output parsing has been performed |
| CLT A/B/D matrices | Computed | Based on assumed engineering constants |
| Four-mesh comparison | Completed provisionally | Four mesh sizes have been analyzed |
| Ply-group FI extraction | Completed provisionally | 16,384 stress records parsed |
| Material strength verification | Not completed | Product-specific data are still required |
| Ply-local stress recovery | Not validated | Coordinate transformation and section-point mapping need verification |
| Reaction-force equilibrium | Not verified | Total support reactions must be checked against the applied resultant |
| FEA-to-CLT comparison | Not completed | A consistent transverse-load comparison is still required |
| Independent experimental validation | Not completed | No validating experimental dataset has been established |

---

## 13. Remaining Work

The following tasks are required before making definitive engineering claims:

1. Verify that the actual CalculiX input file applies the intended total force and boundary conditions.
2. Extract and sum the support reactions, checking the result against the applied 100 N resultant with the correct sign convention.
3. Verify shell section-point ordering and ply mapping in the generated output.
4. Confirm the local material coordinate system and transform stresses correctly for each ply.
5. Replace illustrative strength allowables with documented values for a specified CFRP product.
6. Recalculate the ply-level failure indices using a clearly defined criterion and validated inputs.
7. Compare the FEA results with an analytical prediction under matching geometry, boundary conditions, and loading.
8. Review the scripts and outputs for reproducibility and consistent units.
9. Update the README and project status files so they agree with this report.
10. Check `.gitignore` and repository contents before committing the project to GitHub.

---

## 14. Conclusion

The project currently contains a preliminary CFRP composite plate FEA workflow, successful CalculiX analyses, a four-mesh convergence assessment, CLT A/B/D stiffness calculations, and a preliminary ply-group failure-index post-processing script.

The two finest meshes show small changes in the monitored maximum displacement and calculated nodal von Mises stress. The current ply-group FI values have also been extracted for further investigation.

Nevertheless, the assumed material properties, local ply stress recovery, reaction-force equilibrium, and failure criteria still require validation.

**Final assessment:** This is a reproducible preliminary computational research project. It must not be presented as a validated CFRP failure-prediction or engineering design result until the outstanding validation steps have been completed.

## Reproducibility Note

Results should be interpreted alongside the actual input files, solver version, scripts, material assumptions, and generated output files. Any subsequent changes to the model or analysis should be documented so that the reported results can be reproduced.
