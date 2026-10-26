##############################################################################
#  Build and install the SWIG binary module and the Python package.
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

set(QLR_SWIG_SOURCE ${PROJECT_SOURCE_DIR}/SWIG/quantlib.i)
set_property(SOURCE ${QLR_SWIG_SOURCE} PROPERTY CPLUSPLUS ON)
set_property(SOURCE ${QLR_SWIG_SOURCE} PROPERTY USE_SWIG_DEPENDENCIES TRUE)
set_property(SOURCE ${QLR_SWIG_SOURCE} PROPERTY COMPILE_OPTIONS
    -DQL_XAD=1
    -DQLR_VERSION=\"${QLR_VERSION}\"
    -DQLR_HEX_VERSION=${QLR_HEX_VERSION})

# builds _QuantLib_Risks and generates QuantLib_Risks.py
swig_add_library(QuantLib_Risks
                 LANGUAGE python
                 OUTPUT_DIR ${CMAKE_CURRENT_BINARY_DIR}
                 SOURCES ${QLR_SWIG_SOURCE} converters.cpp)
target_link_libraries(QuantLib_Risks PRIVATE QuantLib::QuantLib pybind11::module)
target_compile_definitions(QuantLib_Risks PRIVATE
    QL_XAD=1
    QLR_VERSION=\"${QLR_VERSION}\"
    QLR_HEX_VERSION=${QLR_HEX_VERSION})
target_include_directories(QuantLib_Risks PRIVATE ${CMAKE_CURRENT_SOURCE_DIR})
set_target_properties(QuantLib_Risks PROPERTIES SUFFIX "${PYTHON_MODULE_EXTENSION}")
if(NOT CMAKE_BUILD_TYPE MATCHES "Debug|RelWithDebInfo")
  pybind11_strip(QuantLib_Risks)
endif()

get_property(QLR_SWIG_PY TARGET QuantLib_Risks PROPERTY SWIG_SUPPORT_FILES)
install(TARGETS QuantLib_Risks
        LIBRARY DESTINATION QuantLib_Risks COMPONENT python
        RUNTIME DESTINATION QuantLib_Risks COMPONENT python)
install(FILES __init__.py ${QLR_SWIG_PY}
        DESTINATION QuantLib_Risks COMPONENT python)
