##############################################################################
#  Builds and installs QuantLib + XAD + QuantLibAAD into PREFIX, for wheel
#  builds with -DQLR_QUANTLIB_PREFIX=<PREFIX> (cibuildwheel before-all):
#
#    cmake -DPREFIX=<dir> [-DBUILD_DIR=<dir>] -P tools/build-quantlib.cmake
#
#  This file is part of QuantLibAAD, a Python wrapper for QuantLib enabled
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

cmake_minimum_required(VERSION 3.19)

if(NOT PREFIX)
  message(FATAL_ERROR "usage: cmake -DPREFIX=<dir> [-DBUILD_DIR=<dir>] -P ${CMAKE_SCRIPT_MODE_FILE}")
endif()
get_filename_component(source_dir "${CMAKE_CURRENT_LIST_DIR}/.." ABSOLUTE)
if(NOT BUILD_DIR)
  set(BUILD_DIR "${source_dir}/build/quantlib")
endif()
# relative to the working directory (cibuildwheel passes {project} as "." on macOS/Windows)
foreach(dir PREFIX BUILD_DIR)
  file(TO_CMAKE_PATH "${${dir}}" ${dir})
  get_filename_component(${dir} "${${dir}}" ABSOLUTE BASE_DIR "${CMAKE_CURRENT_BINARY_DIR}")
endforeach()

if(NOT XAD_DIR)
  if(NOT PYTHON)
    find_program(PYTHON NAMES python3.14 python3.13 python3.12 python3.11 python3.10 python3 python
                 REQUIRED)
  endif()
  if(XAD_REQUIREMENT)
    set(venv "${BUILD_DIR}/xad-venv")
    execute_process(COMMAND "${PYTHON}" -m venv "${venv}" COMMAND_ERROR_IS_FATAL ANY)
    find_program(venv_python NAMES python python3 PATHS "${venv}/bin" "${venv}/Scripts"
                 NO_DEFAULT_PATH NO_CACHE REQUIRED)
    set(PYTHON "${venv_python}")
    execute_process(COMMAND "${PYTHON}" -m pip install "${XAD_REQUIREMENT}" COMMAND_ERROR_IS_FATAL ANY)
  endif()
  execute_process(COMMAND "${PYTHON}" -c "import xad; print(xad.get_cmake_dir())"
                  OUTPUT_VARIABLE XAD_DIR OUTPUT_STRIP_TRAILING_WHITESPACE COMMAND_ERROR_IS_FATAL ANY)
endif()
file(TO_CMAKE_PATH "${XAD_DIR}" XAD_DIR)

if(DEFINED ENV{CMAKE_BUILD_PARALLEL_LEVEL})
  set(jobs $ENV{CMAKE_BUILD_PARALLEL_LEVEL})
else()
  cmake_host_system_information(RESULT jobs QUERY NUMBER_OF_LOGICAL_CORES)
endif()

foreach(step
    "-S;${source_dir};-B;${BUILD_DIR};-DQLR_QUANTLIB_ONLY=ON;-DCMAKE_BUILD_TYPE=Release;-DCMAKE_INSTALL_PREFIX=${PREFIX};-DXAD_DIR=${XAD_DIR}"
    "--build;${BUILD_DIR};--config;Release;--parallel;${jobs}"
    "--install;${BUILD_DIR};--config;Release")
  execute_process(COMMAND ${CMAKE_COMMAND} ${step} COMMAND_ERROR_IS_FATAL ANY)
endforeach()
