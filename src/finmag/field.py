# Field class: a thin wrapper around the dolfin functions
# for unified and convent access to them.
#
# There are two reasons this exists at all:
#
#    - Certain things are awkward (or currently impossible) when using
#      dolfin.Functions directly (for example, per-node operations on
#      vector fields or storing a dolfin.Function in a format convenient
#      for use in Finmag).
#
#    - Even if things are possible, sometimes they are non-trivial to
#      get right, especially in parallel. Therefore this class acts as
#      a "single point of contact" to that we don't duplicate
#      functionality all over the Finmag code base.
#
# The `Field` class represents all scalar and vector fields we need to
# represent as dolfin functions (i.e. discretized fields on a
# mesh). It is always tied to a specific mesh and choice of function
# space (e.g. linear CG).
#
# It does *not* directly represent the abstract concept of a
# (continuous) physical field.
#
#
# What does the field class do?
#
# - Set field values (initialisation, changes at some point during the
#   simulation) for primary fields M, H_Zeeman, current, etc.
#
#   - from constant
#   - from dolfin expression
#   - from python function
#   - from files
#
# - Retrieve field values
#
#   - derived entities such as spatially averaged energy.
#     Can express dolfin code -> quick
#
#   - raw access to field at some particular point or raw
#     data for all nodes (debugging?)
#
# - output data
#
#   - for visualisation (use dolfin tools)
#   - for data storage (use dolfin tools)
#
#
# Maybe to be added later
#
#def nodal_volume(self):
#
#    return nodal_volume

import dolfin as df
import numpy as np


class Field(object):
    def __init__(self, functionspace, value=None, name=None, unit=None):
        self.functionspace = functionspace

        self.f = df.Function(self.functionspace)  # Create an empty function.
        # Set the value of function f is specified.
        if value is not None:
            self.set(value)

        self.name = name
        if name is not None:
            self.f.rename(name, name)  # Rename both function's name and label.

        self.unit = unit

    def set(self, value):
        # Dolfin Constant and Expression type values
        # suitable for both scalar and vector fields.
        if isinstance(value, (df.Constant, df.Expression)):
            self.f = df.interpolate(value, self.functionspace)

        # Int, float, and string values suitable only for scalar fields.
        elif isinstance(value, (basestring, int, float)):
            if isinstance(self.functionspace, df.FunctionSpace):
                self.f = df.interpolate(df.Constant(value), self.functionspace)
            else:
                raise ValueError('Value inappropriate for vector field.')

        # Tuple, list, and numpy array suitable only for vector fields.
        elif isinstance(value, (tuple, list, np.ndarray)):
            if isinstance(self.functionspace, df.VectorFunctionSpace):
                if len(value) == self.value_dim():
                    self.f = df.interpolate(df.Constant(value),
                                            self.functionspace)
                else:
                    raise ValueError('Function space and value dimensions '
                                     'are different.')
            else:
                raise ValueError('Value inappropriate for scalar field.')

        # Python function suitable for both scalar and vector fields.
        elif hasattr(value, '__call__'):
            if isinstance(self.functionspace, df.FunctionSpace):
                class WrappedExpression(df.Expression):
                    def __init__(self, value, fs):
                        self.python_function = value

                    def eval(self, value, x):
                        value[:] = self.python_function(x)

                    def value_shape(self):
                        return ()
            elif isinstance(self.functionspace, df.VectorFunctionSpace):
                if self.value_dim() == 2:
                    class WrappedExpression(df.Expression):
                        def __init__(self, value, fs):
                            self.python_function = value

                        def eval(self, value, x):
                            value[:] = self.python_function(x)[:]

                        def value_shape(self):
                            return (2,)
                elif self.value_dim() == 3:
                    class WrappedExpression(df.Expression):
                        def __init__(self, value, fs):
                            self.python_function = value

                        def eval(self, value, x):
                            value[:] = self.python_function(x)[:]

                        def value_shape(self):
                            return (3,)

            wrappedexpr = WrappedExpression(value, self.functionspace)
            self.f = df.interpolate(wrappedexpr, self.functionspace)
        else:
            raise TypeError('Value type {} not known.'.format(type(value)))

    def save(self, filename):
        """Dispatches to specialists"""
        raise NotImplementedError

    def save_pvd(self, filename):
        """Save to pvd file using dolfin code"""
        raise NotImplementedError

    def save_hdf5(self, filename):
        """Save to hdf5 file using dolfin code"""
        raise NotImplementedError

    def load_hdf5(self, filename):
        """Load field from hdf5 file using dolfin code"""
        raise NotImplementedError

    def coords_and_values(self, t=None):
        """
        Return a list of mesh vertex coordinates and associated field values.
        In parallel, this only returns the coordinates and values owned by
        the current process.

        This function should only be used for debugging!
        """
        if self.f.ufl_element().family() != 'Lagrange':
            raise NotImplementedError(
                "This function is only implemented for finite element families"
                "where the degrees of freedom "
                "are not defined at the mesh vertices.")

        coords = self.functionspace.mesh().coordinates()
        f_array = self.f.vector().array()
        vtd_map = df.vertex_to_dof_map(self.functionspace)
        num_nodes = len(coords)

        # scalar field
        if isinstance(self.functionspace, df.FunctionSpace):
            values = np.empty(num_nodes)
            for i in xrange(num_nodes):
                try:
                    values[i] = f_array[vtd_map[i]]
                except IndexError:
                    raise NotImplementedError

        # vector field
        elif isinstance(self.functionspace, df.VectorFunctionSpace):
            value_dim = self.functionspace.ufl_element().value_shape()[0]
            values = np.empty((num_nodes, value_dim))
            for i in xrange(num_nodes):
                try:
                    values[i, :] = f_array[vtd_map[value_dim*i:
                                                   value_dim*(i+1)]]
                except IndexError:
                    # This only occurs in parallel and is probably related
                    # to ghost nodes. I thought we could ignore those, but
                    # this doesn't seem to be true since the resulting
                    # array of function values has the wrong size. Need to
                    # investigate.  (Max, 15.5.2014)
                    raise NotImplementedError("TODO: How to deal with this?"
                                              " What does it even mean?!?")

        return coords, values

    def probe_field(self, coord):
        """
        Probe and return the value of a field at point with coordinates coord.
        Coord can be a tuple, list or numpy array.
        """
        return self.f(coord)

    def mesh_dim(self):
        """
        Returns the dimension of the mesh (1, 2, or 3)
        """
        return self.f.geometric_dimension()

    def value_dim(self):
        """
        Returns the dimension of field value.
        For scalar field 1, for vector fields 1, 2, 3, ...
        """
        if isinstance(self.functionspace, df.FunctionSpace):
            return 1
        else:
            # value_shape() returns a tuple (N,) and int is required
            return self.functionspace.ufl_element().value_shape()[0]
