# Uses QuantLib, XAD and QuantLibAAD installed by a QLR_QUANTLIB_ONLY build in
# QLR_QUANTLIB_PREFIX. Defines QuantLib::QuantLib.

file(TO_CMAKE_PATH "${QLR_QUANTLIB_PREFIX}" QLR_QUANTLIB_PREFIX)
list(PREPEND CMAKE_PREFIX_PATH "${QLR_QUANTLIB_PREFIX}")
find_package(QuantLibAAD CONFIG REQUIRED NO_DEFAULT_PATH PATHS "${QLR_QUANTLIB_PREFIX}")

# guard against a stale prefix: XAD must match lib/xad and share the tape with xad-py
file(READ "${PROJECT_SOURCE_DIR}/lib/xad/VERSION" xad_src_version)
string(STRIP "${xad_src_version}" xad_src_version)
get_target_property(xad_includes XAD::xad INTERFACE_INCLUDE_DIRECTORIES)
set(xad_no_tls)
foreach(dir IN LISTS xad_includes)
  if(EXISTS "${dir}/XAD/Config.hpp")
    file(STRINGS "${dir}/XAD/Config.hpp" xad_no_tls REGEX "^#define XAD_NO_THREADLOCAL")
  endif()
endforeach()
if(NOT XAD_VERSION STREQUAL xad_src_version OR NOT xad_no_tls)
  message(FATAL_ERROR "XAD in ${QLR_QUANTLIB_PREFIX} (${XAD_VERSION}) does not match "
                      "lib/xad (${xad_src_version}) with XAD_NO_THREADLOCAL; rebuild it")
endif()
message(STATUS "Using prebuilt QuantLib ${QuantLib_VERSION} and XAD ${XAD_VERSION} from ${QLR_QUANTLIB_PREFIX}")
