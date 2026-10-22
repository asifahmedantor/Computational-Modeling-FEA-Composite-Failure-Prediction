
import numpy as np

# ==================================================
# Carbon Fiber / Epoxy Composite Laminate
# Preliminary Classical Laminate Theory (CLT)
# IMPORTANT: Illustrative properties only.
# Replace them with verified material data.
# ==================================================

# Lamina engineering properties (SI units)
E1 = 135e9       # Pa: modulus along fiber direction
E2 = 10e9        # Pa: modulus transverse to fiber
G12 = 5e9        # Pa: in-plane shear modulus
nu12 = 0.30      # major Poisson ratio

nu21 = nu12 * E2 / E1
denom = 1.0 - nu12 * nu21

Q11 = E1 / denom
Q22 = E2 / denom
Q12 = nu12 * E2 / denom
Q66 = G12

Q = np.array([
    [Q11, Q12, 0.0],
    [Q12, Q22, 0.0],
    [0.0, 0.0, Q66]
])

def transformed_Q(angle_deg):
    """Transformed reduced stiffness matrix Qbar."""
    theta = np.deg2rad(angle_deg)
    m = np.cos(theta)
    n = np.sin(theta)

    m2, n2 = m*m, n*n
    m4, n4 = m2*m2, n2*n2

    q11 = Q11*m4 + 2*(Q12 + 2*Q66)*m2*n2 + Q22*n4
    q22 = Q11*n4 + 2*(Q12 + 2*Q66)*m2*n2 + Q22*m4
    q12 = (Q11 + Q22 - 4*Q66)*m2*n2 + Q12*(m4+n4)

    q16 = ((Q11-Q12-2*Q66)*m**3*n
           - (Q22-Q12-2*Q66)*m*n**3)

    q26 = ((Q11-Q12-2*Q66)*m*n**3
           - (Q22-Q12-2*Q66)*m**3*n)

    q66 = ((Q11+Q22-2*Q12-2*Q66)*m2*n2
           + Q66*(m4+n4))

    return np.array([
        [q11, q12, q16],
        [q12, q22, q26],
        [q16, q26, q66]
    ])

# Four plies, each 0.5 mm thick
# Total thickness = 2 mm
layup = [0, 90, 0, 90]
ply_thickness = 0.0005  # metres

nplies = len(layup)
total_thickness = nplies * ply_thickness

# Laminate mid-plane at z = 0
z = np.linspace(
    -total_thickness/2,
    total_thickness/2,
    nplies + 1
)

A = np.zeros((3, 3))  # N/m
B = np.zeros((3, 3))  # N
D = np.zeros((3, 3))  # N*m

for k, angle in enumerate(layup):
    Qbar = transformed_Q(angle)
    z0, z1 = z[k], z[k+1]

    A += Qbar * (z1-z0)
    B += 0.5 * Qbar * (z1**2-z0**2)
    D += (1/3) * Qbar * (z1**3-z0**3)

print("\n=== CFRP LAMINATE MODEL ===")
print("Layup (bottom to top):", layup)
print(f"Total thickness: {total_thickness*1000:.2f} mm")
print("Material properties are illustrative, not validated.")

np.set_printoptions(precision=4, suppress=False)

print("\nA matrix [N/m]:")
print(A)

print("\nB matrix [N]:")
print(B)

print("\nD matrix [N*m]:")
print(D)

print("\nCalculation complete.")
print("These matrices are CLT results, not a 3D FEA solution.")

# ==================================================
# MAXIMUM STRESS FAILURE CRITERION
# Preliminary Classical Laminate Theory
# ==================================================

# Illustrative strength values only (Pa).
# Replace these with verified data for your CFRP material.
Xt = 1500e6   # Longitudinal tensile strength
Xc = 1000e6   # Longitudinal compressive strength
Yt = 40e6     # Transverse tensile strength
Yc = 150e6    # Transverse compressive strength
S12 = 70e6    # In-plane shear strength

# Applied laminate force and moment resultants.
# Units: N/m and N, respectively.
# These are example loads, NOT your FreeCAD 100 N point load.
Nx = 1000.0
Ny = 0.0
Nxy = 0.0
Mx = 0.0
My = 0.0
Mxy = 0.0

load_vector = np.array([Nx, Ny, Nxy, Mx, My, Mxy])

ABD = np.block([
    [A, B],
    [B, D]
])

try:
    solution = np.linalg.solve(ABD, load_vector)
except np.linalg.LinAlgError:
    raise ValueError("ABD matrix cannot be solved.")

eps0 = solution[:3]       # Mid-plane strains
kappa = solution[3:]      # Curvatures, 1/m

print("\n=== MAXIMUM STRESS FAILURE CHECK ===")
print("Illustrative strengths are being used.")
print("Loads are laminate resultants, not point forces.")
print("\nMid-plane strains:", eps0)
print("Curvatures [1/m]:", kappa)

def local_stress(global_strain, angle_deg):
    """Convert global strain to ply coordinates and calculate stress."""
    theta = np.deg2rad(angle_deg)
    m = np.cos(theta)
    n = np.sin(theta)

    ex, ey, gxy = global_strain

    e1 = m*m*ex + n*n*ey + m*n*gxy
    e2 = n*n*ex + m*m*ey - m*n*gxy
    g12 = -2*m*n*ex + 2*m*n*ey + (m*m-n*n)*gxy

    local_strain = np.array([e1, e2, g12])
    stress = Q @ local_strain
    return stress

worst_index = 0.0
worst_ply = None

for k, angle in enumerate(layup):
    z_bottom = z[k]
    z_top = z[k+1]

    for surface, zk in [("bottom", z_bottom), ("top", z_top)]:
        global_strain = eps0 + zk*kappa
        s1, s2, t12 = local_stress(global_strain, angle)

        index1 = abs(s1) / (Xt if s1 >= 0 else Xc)
        index2 = abs(s2) / (Yt if s2 >= 0 else Yc)
        index6 = abs(t12) / S12

        failure_index = max(index1, index2, index6)

        print(
            f"Ply {k+1} ({angle} deg), {surface}: "
            f"sigma1={s1/1e6:.3f} MPa, "
            f"sigma2={s2/1e6:.3f} MPa, "
            f"tau12={t12/1e6:.3f} MPa, "
            f"FI={failure_index:.6f}"
        )

        if failure_index > worst_index:
            worst_index = failure_index
            worst_ply = (k+1, surface, angle)

print("\nMaximum failure index:", f"{worst_index:.6f}")

if worst_index >= 1.0:
    print("WARNING: At least one calculated stress reaches its allowable.")
else:
    print("No allowable exceeded for these illustrative loads and strengths.")

print("This is a preliminary CLT estimate, not validated 3D FEA.")

# Save preliminary laminate stiffness matrices
np.savetxt("A_matrix.csv", A, delimiter=",")
np.savetxt("B_matrix.csv", B, delimiter=",")
np.savetxt("D_matrix.csv", D, delimiter=",")

print("\nSaved A_matrix.csv, B_matrix.csv, D_matrix.csv")

# ==================================================

# ==================================================
# LOAD SCALING STUDY + AUTOMATIC GRAPH
# ==================================================

import matplotlib.pyplot as plt

print("\n=== LOAD SCALING STUDY ===")
print("Illustrative laminate resultants only.")
print("Not equivalent to the FreeCAD point load.")

load_factors = np.array([0.5, 1.0, 2.0, 5.0, 10.0])
base_load = np.array([Nx, Ny, Nxy, Mx, My, Mxy], dtype=float)

ABD = np.block([
    [A, B],
    [B, D]
])

failure_indices = []

for factor in load_factors:
    response = np.linalg.solve(ABD, factor * base_load)

    eps0_scaled = response[:3]
    kappa_scaled = response[3:]
    max_fi = 0.0

    for k, angle in enumerate(layup):
        for zk in [z[k], z[k + 1]]:
            strain = eps0_scaled + zk * kappa_scaled
            s1, s2, t12 = local_stress(strain, angle)

            fi = max(
                abs(s1) / (Xt if s1 >= 0 else Xc),
                abs(s2) / (Yt if s2 >= 0 else Yc),
                abs(t12) / S12
            )

            max_fi = max(max_fi, fi)

    failure_indices.append(max_fi)

    print(
        f"Load factor={factor:>4.1f} | "
        f"Maximum FI={max_fi:.6f} | "
        f"Allowable exceeded={'YES' if max_fi >= 1.0 else 'NO'}"
    )

failure_indices = np.array(failure_indices)

# Save calculated load-scaling results
scaling_data = np.column_stack((load_factors, failure_indices))

np.savetxt(
    "load_scaling_results.csv",
    scaling_data,
    delimiter=",",
    header="LoadFactor,MaximumFailureIndex",
    comments="",
    fmt="%.8f"
)

# Generate graph from calculated values
plt.figure(figsize=(8, 5))
plt.plot(load_factors, failure_indices, marker="o")
plt.axhline(
    y=1.0,
    linestyle="--",
    label="Failure index = 1"
)
plt.xlabel("Load factor")
plt.ylabel("Maximum failure index")
plt.title("CFRP Laminate: Preliminary Load Scaling")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.savefig("load_scaling.png", dpi=200)

print("\nSaved load_scaling_results.csv")
print("Saved load_scaling.png")

plt.show()

# ==================================================
# FREECAD PLATE: TRANSVERSE LOAD CONVERSION
# ==================================================

# Geometry from the FreeCAD model
plate_length = 100.0e-3    # m
plate_width  = 50.0e-3     # m
plate_thickness = 2.0e-3   # m

# Total force shown in FreeCAD
total_force = 100.0        # N

# Assumption: force is distributed over the full 100 x 50 mm face
loaded_area = plate_length * plate_width
equivalent_pressure = total_force / loaded_area

print("\n=== FREECAD TRANSVERSE LOAD ===")
print(f"Plate length: {plate_length*1000:.1f} mm")
print(f"Plate width: {plate_width*1000:.1f} mm")
print(f"Plate thickness: {plate_thickness*1000:.1f} mm")
print(f"Total force: {total_force:.2f} N")
print(f"Assumed loaded area: {loaded_area:.6f} m^2")
print(f"Equivalent pressure: {equivalent_pressure:.2f} Pa")
print(f"Equivalent pressure: {equivalent_pressure/1000:.2f} kPa")

# Save load information
with open("freecad_transverse_load.csv", "w", encoding="utf-8") as f:
    f.write("Parameter,Value,Unit\n")
    f.write(f"Plate length,{plate_length*1000:.2f},mm\n")
    f.write(f"Plate width,{plate_width*1000:.2f},mm\n")
    f.write(f"Plate thickness,{plate_thickness*1000:.2f},mm\n")
    f.write(f"Total force,{total_force:.2f},N\n")
    f.write(f"Loaded area,{loaded_area:.6f},m^2\n")
    f.write(f"Equivalent pressure,{equivalent_pressure:.2f},Pa\n")

print("Saved freecad_transverse_load.csv")
print("Note: pressure assumes the full large face is loaded.")
print("This conversion does not calculate plate deflection or stress.")

# ==================================================
# PRELIMINARY CANTILEVER BENDING ESTIMATE
# Beam-strip approximation, not 3D FEA
# ==================================================

L = plate_length
b = plate_width
p = equivalent_pressure

# Uniform pressure converted to load per unit length
q_line = p * b  # N/m

# Approximate bending rigidity using CLT D11
EI_approx = D[0, 0] * b  # N*m^2

# Cantilever with uniform distributed load
root_moment = q_line * L**2 / 2.0
tip_deflection = q_line * L**4 / (8.0 * EI_approx)

print("\n=== PRELIMINARY BENDING ESTIMATE ===")
print(f"Distributed load: {q_line:.3f} N/m")
print(f"Approximate root moment: {root_moment:.4f} N*m")
print(f"Approximate bending rigidity: {EI_approx:.6f} N*m^2")
print(f"Estimated tip deflection: {tip_deflection*1000:.3f} mm")

with open("preliminary_bending_estimate.csv", "w", encoding="utf-8") as f:
    f.write("Parameter,Value,Unit\n")
    f.write(f"Distributed load,{q_line:.6f},N/m\n")
    f.write(f"Root moment,{root_moment:.6f},N*m\n")
    f.write(f"Approximate bending rigidity,{EI_approx:.8f},N*m^2\n")
    f.write(f"Estimated tip deflection,{tip_deflection*1000:.6f},mm\n")

print("Saved preliminary_bending_estimate.csv")
print("WARNING: Beam-strip approximation only; not validated plate FEA.")

# ==================================================
# IMPROVED CFRP BENDING ESTIMATE
# Includes laminate extension-bending coupling
# Beam-strip approximation; not 3D FEA
# ==================================================

# Effective bending stiffness when in-plane resultants are zero
D_effective = D - B @ np.linalg.solve(A, B)

# Plate dimensions and uniformly distributed total force
L = plate_length
b = plate_width
q_line = total_force / L

# Effective bending rigidity of a beam strip
EI_effective = D_effective[0, 0] * b

# Cantilever beam-strip estimate under uniform load
root_moment = q_line * L**2 / 2.0
tip_deflection = q_line * L**4 / (8.0 * EI_effective)

print("\n=== CFRP COUPLING-CORRECTED BENDING ESTIMATE ===")
print("Effective bending stiffness D* [N*m]:")
print(D_effective)
print(f"Distributed load: {q_line:.3f} N/m")
print(f"Root moment: {root_moment:.4f} N*m")
print(f"Effective beam-strip rigidity: {EI_effective:.6f} N*m^2")
print(f"Estimated tip deflection: {tip_deflection*1000:.3f} mm")

np.savetxt(
    "D_effective.csv",
    D_effective,
    delimiter=",",
    header="Effective bending stiffness D* [N*m]",
    comments=""
)

with open("cfrp_bending_estimate.csv", "w", encoding="utf-8") as f:
    f.write("Parameter,Value,Unit\n")
    f.write(f"Total force,{total_force:.4f},N\n")
    f.write(f"Distributed load,{q_line:.6f},N/m\n")
    f.write(f"Root moment,{root_moment:.6f},N*m\n")
    f.write(f"Effective rigidity,{EI_effective:.8f},N*m^2\n")
    f.write(f"Estimated tip deflection,{tip_deflection*1000:.6f},mm\n")

print("Saved D_effective.csv and cfrp_bending_estimate.csv")
print("WARNING: Beam-strip estimate, not validated plate FEA.")
