import time
import numpy as np
import dolfin as df
from finmag.energies import Demag
from finmag.field import Field
from finmag.util.meshes import sphere
import matplotlib.pyplot as plt

radius = 5.0
maxhs = [0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 1.0]
unit_length = 1e-9
m_0 = (1, 0, 0)
Ms = 1
H_ref = np.array((- Ms / 3.0, 0, 0))

vertices = []
solvers = ["FK", "FK", "GCR", "Treecode"]
solvers_label = ["FK", "FK opt", "GCR", "Treecode"]
timings = [[], [], [], []]
errors = [[], [], [], []]

for maxh in maxhs:
    mesh = sphere(r=radius, maxh=maxh, directory="meshes")
    vertices.append(mesh.num_vertices())
    S3 = df.VectorFunctionSpace(mesh, "Lagrange", 1)
    m_function = df.Function(S3)
    m_function.assign(df.Constant(m_0))
    m = Field(S3, m_function)

    for i, solver in enumerate(solvers):
        demag = Demag(solver)
        if solver == "FK":
            if i == 0:
                demag.parameters["phi_1_solver"] = "default"
                demag.parameters["phi_1_preconditioner"] = "default"
                demag.parameters["phi_2_solver"] = "default"
                demag.parameters["phi_2_preconditioner"] = "default"
            if i == 1:
                demag.parameters["phi_1_solver"] = "cg"
                demag.parameters["phi_1_preconditioner"] = "ilu"
                demag.parameters["phi_2_solver"] = "cg"
                demag.parameters["phi_2_preconditioner"] = "ilu"
        demag.setup(m, Ms, unit_length)

        start = time.time()
        for j in xrange(10):
            H = demag.compute_field()
        elapsed = (time.time() - start) / 10.0

        H = H.reshape((3, -1)).mean(axis=1)
        error = abs(H[0] - H_ref[0]) / abs(H_ref[0])
        timings[i].append(elapsed)
        errors[i].append(error)

fig = plt.figure()
ax = fig.add_subplot(211)
ax.set_title("Runtime")
for i, solver in enumerate(solvers):
    ax.plot(vertices, timings[i], label=solvers_label[i])
ax.legend(loc=2)
ax.set_xlabel("vertices")
ax.set_ylabel("time (s)")

ax = fig.add_subplot(212)
ax.set_title("Inaccuracy")
for i, solver in enumerate(solvers):
    ax.plot(vertices, errors[i], label=solvers_label[i])
ax.legend(loc=2)
ax.set_xlabel("vertices")
ax.set_ylabel("relative error (%)")

fig.tight_layout()
fig.savefig("benchmark.png")
