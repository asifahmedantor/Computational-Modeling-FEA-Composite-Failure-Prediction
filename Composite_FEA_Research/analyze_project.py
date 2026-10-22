"""Reproducible post-processing for the preliminary CFRP laminate project.

Run from this directory with: python analyze_project.py
Units: mm, N, MPa for CalculiX; SI units for CLT calculations.
IMPORTANT: CLT failure results use illustrative strengths and a separate in-plane
resultant load case. They are not the failure index for the 100 N transverse FEA case.
"""
from pathlib import Path
import csv, math, re
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
FRD = ROOT / "cfrp_composite.frd"
INP = ROOT / "cfrp_composite.inp"
OUT = ROOT / "results"
OUT.mkdir(exist_ok=True)

NUM = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?")
def frd_datasets(path):
    """Read last occurrence of FRD DISP and STRESS blocks; preserve row values.

    CalculiX FRD nodal result records use fixed-width values, so regex parsing is
    used rather than split(), which fails when adjacent signed values touch.
    """
    datasets = {}
    current = None
    for line in path.read_text(errors="ignore").splitlines():
        s = line.split()
        if len(s) >= 2 and s[0] == "-4":
            current = s[1] if s[1] in ("DISP", "STRESS") else None
            if current:
                datasets[current] = []
            continue
        if s and s[0] == "-3":
            current = None
            continue
        if current and line.lstrip().startswith("-1"):
            vals = NUM.findall(line)
            # First numeric token is the FRD record marker (-1), next is node id.
            if len(vals) < 5:
                continue
            try:
                node = int(vals[1])
                v = [float(x.replace("D", "E").replace("d", "e")) for x in vals[2:]]
                needed = 3 if current == "DISP" else 6
                if len(v) >= needed:
                    datasets[current].append((node, v[:needed]))
            except (ValueError, IndexError):
                continue
    return datasets

def write_csv(path, headers, rows):
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(headers); w.writerows(rows)

# 1) FEA output summary from the supplied CalculiX FRD file.
if not FRD.exists():
    raise FileNotFoundError(f"Missing {FRD.name}; run CalculiX first or place its FRD output here.")
data = frd_datasets(FRD)
summary = []
if data.get("DISP"):
    disp = data["DISP"]
    node, u = max(disp, key=lambda item: math.sqrt(sum(x*x for x in item[1])))
    umag = math.sqrt(sum(x*x for x in u))
    summary.append(("maximum_nodal_displacement_magnitude", umag, "mm", node,
                    "FRD nodal vector magnitude; verify mesh/BC/load before design use"))
else:
    node = None; umag = float("nan")
    summary.append(("maximum_nodal_displacement_magnitude", "NOT_FOUND", "mm", "", "DISP block missing"))

stress_rows = data.get("STRESS", [])
if stress_rows:
    computed = []
    for n, v in stress_rows:
        sx, sy, sz, txy, tyz, tzx = v
        vm = math.sqrt(0.5*((sx-sy)**2 + (sy-sz)**2 + (sz-sx)**2)
                       + 3*(txy*txy + tyz*tyz + tzx*tzx))
        computed.append((vm, n, v))
    vm, snode, sv = max(computed, key=lambda x: x[0])
    max_sxx = max(stress_rows, key=lambda item: abs(item[1][0]))
    summary.append(("maximum_calculated_nodal_von_mises", vm, "MPa", snode,
                    "Calculated from FRD SXX,SYY,SZZ,SXY,SYZ,SZX; not ply failure criterion"))
    summary.append(("maximum_absolute_SXX", abs(max_sxx[1][0]), "MPa", max_sxx[0],
                    "FRD stress component; not necessarily a ply-local longitudinal stress"))
    write_csv(OUT / "fea_stress_nodal.csv",
              ["node_or_frd_record_id", "SXX_MPa", "SYY_MPa", "SZZ_MPa", "SXY_MPa", "SYZ_MPa", "SZX_MPa", "calculated_von_Mises_MPa"],
              [(n, *v, next(x[0] for x in computed if x[1] == n)) for n, v in stress_rows])
else:
    summary.append(("maximum_calculated_nodal_von_mises", "NOT_FOUND", "MPa", "", "STRESS block missing"))
write_csv(OUT / "fea_summary.csv", ["metric", "value", "unit", "node_or_record", "interpretation"], summary)

# 2) Classical Laminate Theory: explicit illustrative in-plane load case.
# Material values taken from the project script; strengths are illustrative only.
E1, E2, G12, nu12 = 135e9, 10e9, 5e9, 0.30
nu21 = nu12 * E2 / E1
den = 1 - nu12*nu21
Q11, Q22, Q12, Q66 = E1/den, E2/den, nu12*E2/den, G12
Q = np.array([[Q11,Q12,0],[Q12,Q22,0],[0,0,Q66]], float)

def qbar(angle):
    t = np.deg2rad(angle); m, n = np.cos(t), np.sin(t)
    m2,n2=m*m,n*n; m4,n4=m2*m2,n2*n2
    q11=Q11*m4+2*(Q12+2*Q66)*m2*n2+Q22*n4
    q22=Q11*n4+2*(Q12+2*Q66)*m2*n2+Q22*m4
    q12=(Q11+Q22-4*Q66)*m2*n2+Q12*(m4+n4)
    q16=(Q11-Q12-2*Q66)*m**3*n-(Q22-Q12-2*Q66)*m*n**3
    q26=(Q11-Q12-2*Q66)*m*n**3-(Q22-Q12-2*Q66)*m**3*n
    q66=(Q11+Q22-2*Q12-2*Q66)*m2*n2+Q66*(m4+n4)
    return np.array([[q11,q12,q16],[q12,q22,q26],[q16,q26,q66]])

layup = [0,90,0,90]  # bottom-to-top; unsymmetric
th = 0.0005
h = len(layup)*th
z = np.linspace(-h/2,h/2,len(layup)+1)
A=np.zeros((3,3)); B=np.zeros((3,3)); D=np.zeros((3,3))
for k,ang in enumerate(layup):
    qb=qbar(ang); z0,z1=z[k],z[k+1]
    A += qb*(z1-z0)
    B += 0.5*qb*(z1*z1-z0*z0)
    D += (qb/3)*(z1**3-z0**3)
D_eff = D - B @ np.linalg.solve(A,B)
np.savetxt(OUT/"A_matrix_N_per_m.csv", A, delimiter=",")
np.savetxt(OUT/"B_matrix_N.csv", B, delimiter=",")
np.savetxt(OUT/"D_matrix_Nm.csv", D, delimiter=",")
np.savetxt(OUT/"D_effective_Nm.csv", D_eff, delimiter=",")

# Separate in-plane membrane load resultants, matching the existing script, not the 100 N pressure case.
Nbase=np.array([1000.0,0.0,0.0]) # N/m; Nx only
Mbase=np.zeros(3)                 # N
ABD=np.block([[A,B],[B,D]])
Xt,Xc,Yt,Yc,S12=1500e6,1000e6,40e6,150e6,70e6

def ply_local_stress(global_strain, angle):
    t=np.deg2rad(angle); m,n=np.cos(t),np.sin(t)
    ex,ey,gxy=global_strain
    e1=m*m*ex+n*n*ey+m*n*gxy
    e2=n*n*ex+m*m*ey-m*n*gxy
    g12=-2*m*n*ex+2*m*n*ey+(m*m-n*n)*gxy
    return Q @ np.array([e1,e2,g12])

def max_stress_fi(s1,s2,t12):
    return max(abs(s1)/(Xt if s1>=0 else Xc), abs(s2)/(Yt if s2>=0 else Yc), abs(t12)/S12)

clt_rows=[]
for k,ang in enumerate(layup):
    for side,zk in (("bottom",z[k]),("top",z[k+1])):
        sol=np.linalg.solve(ABD,np.r_[Nbase,Mbase])
        eps=sol[:3]+zk*sol[3:]
        s1,s2,t12=ply_local_stress(eps,ang)
        fi=max_stress_fi(s1,s2,t12)
        clt_rows.append((k+1,ang,side,zk*1000,s1/1e6,s2/1e6,t12/1e6,fi,"illustrative strengths; Nx=1000 N/m, not transverse FEA load"))
write_csv(OUT/"clt_ply_surface_stress_failure.csv",
          ["ply_bottom_to_top","angle_deg","surface","z_mm","sigma1_MPa","sigma2_MPa","tau12_MPa","maximum_stress_FI","load_case_and_limitations"], clt_rows)

factors=np.array([0.5,1,2,5,10],float)
fi_vals=[]
for fac in factors:
    sol=np.linalg.solve(ABD,np.r_[fac*Nbase,Mbase])
    eps0,kappa=sol[:3],sol[3:]
    fi_max=0.0
    for k,ang in enumerate(layup):
        for zk in (z[k],z[k+1]):
            s1,s2,t12=ply_local_stress(eps0+zk*kappa,ang)
            fi_max=max(fi_max,max_stress_fi(s1,s2,t12))
    fi_vals.append(fi_max)
write_csv(OUT/"clt_load_scaling.csv",["load_factor","max_stress_failure_index","note"],[(f,fi,"CLT in-plane Nx=1000 N/m baseline; illustrative strengths") for f,fi in zip(factors,fi_vals)])
plt.figure(figsize=(7.5,4.5)); plt.plot(factors,fi_vals,marker="o"); plt.axhline(1,linestyle="--",label="FI = 1 threshold")
plt.xlabel("In-plane load factor"); plt.ylabel("Maximum-stress failure index"); plt.title("CLT illustrative in-plane load scaling")
plt.grid(True,alpha=.3); plt.legend(); plt.tight_layout(); plt.savefig(OUT/"clt_load_scaling.png",dpi=180); plt.close()

print("=== FEA SUMMARY (from supplied FRD) ===")
for metric,value,unit,nid,desc in summary:
    print(f"{metric}: {value} {unit}; node/record={nid}")
print(f"Stress records parsed: {len(stress_rows)}")
print("=== CLT (separate illustrative in-plane load case) ===")
print("Layup bottom-to-top:", layup, "; thickness:", h*1000, "mm")
print("A matrix [N/m]:\n", A)
print("B matrix [N]:\n", B)
print("D matrix [N*m]:\n", D)
print("Maximum CLT FI for Nx=1000 N/m with illustrative strengths:", max(r[7] for r in clt_rows))
print("Outputs written to", OUT)
print("WARNING: CLT FI is NOT the failure index for the transverse 100 N FEA case.")
print("WARNING: FRD stress rows are not mapped to individual laminate plies; no ply-wise FEA FI claimed.")
