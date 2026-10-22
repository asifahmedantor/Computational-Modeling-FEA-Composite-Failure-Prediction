"""Generate and run a structured S8R mesh-convergence study with CalculiX.

Run from project root using the project's Python environment, e.g.:
  python mesh_convergence.py --ccx D:\\Apps\\bin\\ccx.exe
Default meshes: 4x2, 8x4, 16x8, 32x16 quadratic shell elements.
This creates a separate mesh_convergence/ directory and does not overwrite
cfrp_composite.inp or its existing result files.
"""
from pathlib import Path
import argparse, csv, math, re, subprocess
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "mesh_convergence"
NUM = re.compile(r"[+-]?(?:\d+\.?\d*|\.\d+)(?:[EeDd][+-]?\d+)?")

def make_inp(nx, ny):
    # Each S8R element spans 2 intervals in the quadratic grid.
    dx = 100.0 / (2*nx); dy = 50.0 / (2*ny)
    nodes = {}
    nid = 1
    # S8R uses corners and edge midpoints only; omit odd/odd interior grid points.
    for j in range(2*ny+1):
        for i in range(2*nx+1):
            if i % 2 == 1 and j % 2 == 1:
                continue
            nodes[(i,j)] = nid
            nid += 1
    lines = ["*HEADING", f"CFRP mesh convergence {nx}x{ny}; 100x50x2 mm; 100 N total pressure", "** Units: mm, N, MPa", "** Illustrative material properties; not validated material data", "** Layup bottom-to-top: 0/90/0/90", "*NODE"]
    for (i,j),nid in nodes.items():
        lines.append(f"{nid}, {i*dx:.8f}, {j*dy:.8f}, 0")
    lines.append("*ELEMENT, TYPE=S8R, ELSET=EALL")
    eid=1
    for j in range(ny):
        for i in range(nx):
            i0,j0=2*i,2*j
            conn=[nodes[(i0,j0)],nodes[(i0+2,j0)],nodes[(i0+2,j0+2)],nodes[(i0,j0+2)],
                  nodes[(i0+1,j0)],nodes[(i0+2,j0+1)],nodes[(i0+1,j0+2)],nodes[(i0,j0+1)]]
            lines.append(f"{eid}, " + ", ".join(map(str,conn))); eid+=1
    fixed=[nid for (i,j),nid in nodes.items() if i==0]
    lines.append("*NSET, NSET=FIXED_EDGE")
    for k in range(0,len(fixed),12): lines.append(", ".join(map(str,fixed[k:k+12])))
    lines += ["*MATERIAL, NAME=CFRP_UD", "*ELASTIC, TYPE=ENGINEERING CONSTANTS",
              "135000, 10000, 10000, 0.30, 0.30, 0.40, 5000, 5000", "3571.4286",
              "*ORIENTATION, NAME=ORI0, SYSTEM=RECTANGULAR", "1, 0, 0, 0, 1, 0",
              "*ORIENTATION, NAME=ORI90, SYSTEM=RECTANGULAR", "0, 1, 0, -1, 0, 0",
              "*SHELL SECTION, ELSET=EALL, COMPOSITE", "0.5, , CFRP_UD, ORI0",
              "0.5, , CFRP_UD, ORI90", "0.5, , CFRP_UD, ORI0", "0.5, , CFRP_UD, ORI90",
              "*BOUNDARY", "FIXED_EDGE, 1, 6, 0", "*STEP", "*STATIC", "0.1, 1.0, 1.E-5, 1.0",
              "*DLOAD", "EALL, P, 0.02", "*NODE FILE", "U, RF", "*EL FILE", "S, E", "*END STEP", ""]
    return "\n".join(lines)

def extract(path):
    mode=None; disp=[]; stress=[]
    for line in path.read_text(errors="ignore").splitlines():
        s=line.split()
        if len(s)>=2 and s[0]=="-4":
            mode=s[1] if s[1] in ("DISP","STRESS") else None; continue
        if s and s[0]=="-3": mode=None; continue
        if mode and line.lstrip().startswith("-1"):
            a=NUM.findall(line)
            if len(a)<5: continue
            try:
                nid=int(a[1]); vals=[float(x.replace('D','E')) for x in a[2:]]
                if mode=="DISP" and len(vals)>=3: disp.append((nid,vals[:3]))
                elif mode=="STRESS" and len(vals)>=6: stress.append((nid,vals[:6]))
            except (ValueError,IndexError): pass
    if not disp: raise RuntimeError(f"No displacement dataset in {path}")
    u_node,u=max(disp,key=lambda q: math.sqrt(sum(x*x for x in q[1])))
    umax=math.sqrt(sum(x*x for x in u))
    smax=float('nan'); snode=''
    if stress:
        def vmcalc(v):
            sx,sy,sz,txy,tyz,tzx=v
            return math.sqrt(.5*((sx-sy)**2+(sy-sz)**2+(sz-sx)**2)+3*(txy*txy+tyz*tyz+tzx*tzx))
        smax,snode=max(((vmcalc(v),nid) for nid,v in stress),key=lambda q:q[0])
    return umax,u_node,smax,snode,len(disp),len(stress)

def main():
    p=argparse.ArgumentParser(); p.add_argument('--ccx',required=True,help='Full path to ccx.exe'); p.add_argument('--meshes',default='4x2,8x4,16x8,32x16'); args=p.parse_args()
    OUT.mkdir(exist_ok=True)
    rows=[]
    for token in args.meshes.split(','):
        nx,ny=map(int,token.lower().split('x')); name=f"mesh_{nx}x{ny}"; folder=OUT/name; folder.mkdir(exist_ok=True)
        inp=folder/f"{name}.inp"; inp.write_text(make_inp(nx,ny),encoding='ascii')
        print(f"Running {name}: {nx*ny} S8R elements")
        result=subprocess.run([args.ccx,"-i",name],cwd=folder,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
        (folder/"solver_console.log").write_text(result.stdout,encoding="utf-8",errors="replace")
        frd=folder/f"{name}.frd"
        if result.returncode != 0 or not frd.exists():
            print(f"FAILED {name}; see {folder/'solver_console.log'}")
            rows.append((nx,ny,nx*ny,"FAILED","","","","","")); continue
        u,un,sv,sn,nd,ns=extract(frd)
        rows.append((nx,ny,nx*ny,u,un,sv,sn,nd,ns))
        print(f"  max |U|={u:.6f} mm (record {un}); max calculated nodal von Mises={sv:.6f} MPa (record {sn})")
    csvpath=OUT/"mesh_convergence.csv"
    with csvpath.open('w',newline='',encoding='utf-8') as f:
        w=csv.writer(f); w.writerow(["nx","ny","element_count","max_displacement_mm","displacement_record","max_calculated_von_mises_MPa","stress_record","disp_records","stress_records"]); w.writerows(rows)
    valid=[r for r in rows if isinstance(r[3],float) or isinstance(r[3],int)]
    if valid:
        plt.figure(figsize=(7.5,4.5)); plt.plot([r[2] for r in valid],[r[3] for r in valid],marker='o')
        plt.xlabel('S8R element count'); plt.ylabel('Maximum displacement magnitude (mm)'); plt.title('Mesh convergence: displacement'); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(OUT/'mesh_convergence_displacement.png',dpi=180); plt.close()
        if all(isinstance(r[5],(float,int)) and math.isfinite(r[5]) for r in valid):
            plt.figure(figsize=(7.5,4.5)); plt.plot([r[2] for r in valid],[r[5] for r in valid],marker='o')
            plt.xlabel('S8R element count'); plt.ylabel('Maximum calculated nodal von Mises stress (MPa)'); plt.title('Mesh trend: stress (may be singular at fixed edge)'); plt.grid(True,alpha=.3); plt.tight_layout(); plt.savefig(OUT/'mesh_convergence_stress.png',dpi=180); plt.close()
    print(f"Wrote {csvpath}")
if __name__=='__main__': main()
