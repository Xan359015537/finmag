/**
 * FinMag - a thin layer on top of FEniCS to enable micromagnetic multi-physics simulations
 * Copyright (C) 2012 University of Southampton
 * Do not distribute
 *
 * CONTACT: h.fangohr@soton.ac.uk
 *
 * AUTHOR(S) OF THIS FILE: Dmitri Chernyshenko (d.chernyshenko@soton.ac.uk)
 */
#ifndef __FINMAG_INCLUDES_H
#define __FINMAG_INCLUDES_H

// Standard C/C++ includes
#include <cstring>
#include <cmath>
#include <cstdlib>

// OpenMP
#include <omp.h>

// Boost includes
#ifndef IDE_ERROR_BLOCK
#include <boost/mpl/map.hpp>
#include <boost/mpl/transform.hpp>
#include <boost/mpl/range_c.hpp>
#include <boost/mpl/list.hpp>
#include <boost/python.hpp>
#include <boost/typeof/typeof.hpp>
#include <boost/thread.hpp>
#endif

// CVODE/Sundials
#include <cvode/cvode.h>
// Dolfin
#include <dolfin.h>

#endif
