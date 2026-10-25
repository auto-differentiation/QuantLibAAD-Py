##############################################################################
#  Main CMake file for the Python extension.
#
#  This file is part of QuantLib-Risks, a Python wrapper for QuantLib enabled
#  for risk computation using automatic differentiation. It uses XAD,
#  a fast and comprehensive C++ library for automatic differentiation.
#
#  Copyright (C) 2010-2024 Xcelerit Computing Ltd.
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published
#  by the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

find_package(Python 3.10 REQUIRED COMPONENTS Interpreter Development.Module)
find_package(SWIG 4.0 REQUIRED COMPONENTS python)
include(UseSWIG)

# must be the same pybind11 as xad-py's, as converters.cpp shares its Real type
set(PYBIND11_FINDPYTHON ON)
add_subdirectory(${PROJECT_SOURCE_DIR}/lib/pybind11 ${CMAKE_BINARY_DIR}/pybind11)

add_subdirectory(QuantLibAAD)
