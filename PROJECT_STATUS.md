# Project completion status

## Completed in this workspace
- Inspected the supplied CalculiX model and result files.
- Added robust FRD parsing that handles adjacent signed/scientific-notation values.
- Generated an FEA summary CSV and nodal stress CSV from the existing result.
- Reproducibly computed CLT A/B/D matrices for the `[0/90/0/90]` layup.
- Exported CLT ply-surface stress / maximum-stress FI for the separate in-plane `Nx = 1000 N/m` case, with illustrative allowables clearly labelled.
- Added CLT load-scaling CSV and plot.
- Added a mesh-convergence generator/runner that preserves the original model and writes each mesh to a separate folder.
- Added README and a technical report with assumptions and limitations.

## Still required before claiming validated failure prediction
- Run the supplied mesh-convergence script on the user's Windows computer using `D:\Apps\bin\ccx.exe`.
- Verify reaction forces balance the 100 N applied load.
- Obtain section-point / ply-wise stress values and transform them into each ply's material axes.
- Replace illustrative strength values with a verified datasheet or test report.
- Calculate a failure criterion for the actual transverse-pressure load case and compare against an appropriate analytical solution.

**Do not report the earlier provisional FI of 6.38002 as a validated composite failure prediction.** It was based on global FRD stress components without verified ply/section-point mapping.
