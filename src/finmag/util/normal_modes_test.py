from finmag.util.mesh_templates import Box, Sphere
from finmag.util.meshes import mesh_info, plot_mesh_with_paraview
from finmag.util.normal_modes import *
from finmag import sim_with
from math import pi
import logging

logger = logging.getLogger("finmag")


def test_compute_generalised_eigenproblem_matrices_single_sphere(tmpdir):
    #(sim, alpha=0.0, frequency_unit=1e9, filename_mat_A=None, filename_mat_M=None):
    os.chdir(str(tmpdir))

    sphere = Sphere(r=11)
    mesh = sphere.create_mesh(maxh=2.0)
    print "[DDD] mesh: {}".format(mesh)
    print mesh_info(mesh)
    plot_mesh_with_paraview(mesh, outfile='mesh_sphere.png')

    H_z = 1.42e5  # slightly odd value to make the test a bit more reliable
    frequency_unit = 1e9
    freq_expected = gamma * H_z / (2*pi*frequency_unit)

    sim = sim_with(mesh, Ms=1e6, m_init=[0, 0, 1], A=13e-12, H_ext=[0, 0, H_z], unit_length=1e-9, demag_solver='FK')
    sim.relax()

    A, M, _, _ = compute_generalised_eigenproblem_matrices(sim, alpha=0.0, frequency_unit=1e9)

    n_values = 6
    n_values_export = 0
    omega, w = compute_normal_modes_generalised(A, M, n_values=n_values, tol=1e-8, discard_negative_frequencies=False)
    assert(len(omega) == n_values)
    print "[DDD] omega: {}".format(omega)

    # Check that the frequency of the base mode equals the analytical value from the Kittel equation
    # (see Charles Kittel, "ntroduction to solid state physics", 7th edition, Ch. 16, p.505):
    #
    #    omega_0 = gamma * B_0
    #
    # XXX TODO: Should we divide by 2*pi here, or should the factor 2*pi actually be included in the frequency?!?!??!
    logger.warning("XXX TODO: Should we divide by 2*pi in this test, or should the factor 2*pi actually be included in the frequency?!?!??!")
    assert(np.allclose(omega[0], +freq_expected, atol=0, rtol=1e-2))
    assert(np.allclose(omega[1], -freq_expected, atol=0, rtol=1e-2))

    omega_positive, _ = compute_normal_modes_generalised(A, M, n_values=n_values, tol=1e-8, discard_negative_frequencies=True)
    logger.debug("[DDD] omega_positive: {}".format(omega_positive))
    assert(len(omega_positive) == n_values)

    # Check that the base frequency is as expected
    assert(np.allclose(omega_positive[0], freq_expected, atol=0, rtol=1e-2))

    # Ensure that the frequencies are all positive and sorted by absolute value
    assert((np.array(omega_positive) > 0).all())
    assert(np.allclose(omega_positive, sorted(omega_positive, key=abs)))

    omega_positive_first_half = omega_positive[:(n_values // 2)]
    assert(np.allclose(sorted(np.concatenate([omega_positive_first_half, -omega_positive_first_half])),
                       sorted(omega)))

    # Export normal mode animations for debugging
    for i in xrange(n_values_export):
        freq = omega_positive[i]
        export_normal_mode_animation(sim, freq, w[:, i], filename='normal_mode_{:02d}__{:.3f}_GHz.pvd'.format(i, freq))
