import logging
import dolfin as df
from aeon import timer
from energy_base import EnergyBase
from finmag.field import Field

logger = logging.getLogger('finmag')


class Exchange(EnergyBase):
    """
    Compute the exchange field.

    .. math::

        E_{\\text{exch}} = \\int_\\Omega A (\\nabla M)^2  dx


    *Arguments*

        A
            the exchange constant

        method
            See documentation of EnergyBase class for details.

        name
            name of the object

    *Example of Usage*

        .. code-block:: python

            import dolfin as df
            from finmag.energies.exchange import Exchange
            from finmag.field import Field

            # Define a mesh representing a cube with edge length L
            L = 1e-8  # m
            n = 5
            mesh = df.BoxMesh(df.Point(0, L, 0), df.Point(L, 0, L), n, n, n)

            A = 1.3e-11  # J/m exchange constant
            Ms = 0.8e6  # A/m saturation magnetisation

            # Initial magnetisation
            S3 = df.VectorFunctionSpace(mesh, 'CG', 1)
            m = Field(S3, (1, 0, 0))

            exchange = Exchange(A)
            exchange.setup(m, Ms)

            # Compute exchange energy.
            E_ex = exchange.compute_energy()

            # Compute exchange effective field.
            H_ex = exchange.compute_field()

            # Using 'box-matrix-numpy' method (fastest for small matrices)
            exchange_np = Exchange(A, method='box-matrix-numpy')
            exchange_np.setup(m, Ms)
            H_exch_np = exchange_np.compute_field()

    """

    def __init__(self, A, method='box-matrix-petsc', name='Exchange'):
        self.A_value = A  # Value of A, later converted to a Field object.
        self.name = name

        super(Exchange, self).__init__(method, in_jacobian=True)

    @timer.method
    def setup(self, m, Ms, unit_length=1):
        """
        Function to be called after the energy object has been constructed.

        *Arguments*

            m
                magnetisation field (usually normalised)

            Ms
                Saturation magnetisation (scalar, or scalar dolfin function)

            unit_length
                real length of 1 unit in the mesh

        """
        assert isinstance(m, Field)
        assert isinstance(Ms, Field)

        # Create an exchange constant Field object A in DG0 function space.
        dg_functionspace = df.FunctionSpace(m.mesh(), 'DG', 0)
        self.A = Field(dg_functionspace, self.A_value, name='A')
        del(self.A_value)

        # Multiplication factor used for exchange energy computation.
        self.exchange_factor = df.Constant(1.0/unit_length**2)

        # An expression for computing the exchange energy.
        E_integrand = self.exchange_factor * self.A.f * \
            df.inner(df.grad(m.f), df.grad(m.f))

        super(Exchange, self).setup(E_integrand, m, Ms, unit_length)
