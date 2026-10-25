# Uses QuantLib and QuantLibAAD installed by a QLR_QUANTLIB_ONLY build in
# QLR_QUANTLIB_PREFIX, with XAD::xad from QLRXad. Defines QuantLib::QuantLib.

file(TO_CMAKE_PATH "${QLR_QUANTLIB_PREFIX}" QLR_QUANTLIB_PREFIX)
list(PREPEND CMAKE_PREFIX_PATH "${QLR_QUANTLIB_PREFIX}")
find_package(QuantLibAAD CONFIG REQUIRED NO_DEFAULT_PATH PATHS "${QLR_QUANTLIB_PREFIX}")

# guard against a stale prefix: QuantLib must be built with the XAD found by QLRXad
include("${QuantLibAAD_DIR}/QLRXadVersion.cmake" OPTIONAL)
if(NOT QLR_QUANTLIB_XAD_VERSION STREQUAL XAD_VERSION)
  message(FATAL_ERROR "QuantLib in ${QLR_QUANTLIB_PREFIX} was built with XAD "
                      "'${QLR_QUANTLIB_XAD_VERSION}', not ${XAD_VERSION} (${XAD_DIR}); rebuild it")
endif()
message(STATUS "Using prebuilt QuantLib ${QuantLib_VERSION} from ${QLR_QUANTLIB_PREFIX}")
