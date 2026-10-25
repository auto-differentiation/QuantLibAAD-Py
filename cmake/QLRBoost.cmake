# Boost headers for QuantLib: the system's (or BOOST_ROOT) if found, else the
# pinned release is downloaded.
# Sets QLR_BOOST_INCLUDE_DIR and QLR_BOOST_DOWNLOADED.

set(QLR_BOOST_URL "https://archives.boost.io/release/1.90.0/source/boost_1_90_0.tar.bz2"
    CACHE STRING "Boost source archive, downloaded if no Boost headers are found")
set(QLR_BOOST_SHA256 "49551aff3b22cbc5c5a9ed3dbc92f0e23ea50a0f7325b0d198b705e8ee3fc305"
    CACHE STRING "SHA256 of QLR_BOOST_URL")

find_path(QLR_BOOST_INCLUDE_DIR boost/version.hpp
          HINTS ${BOOST_ROOT} ${Boost_ROOT} ENV BOOST_ROOT ENV Boost_ROOT
          PATH_SUFFIXES include)

set(QLR_BOOST_DOWNLOADED OFF)
if(NOT QLR_BOOST_INCLUDE_DIR)
  set(boost_dir "${CMAKE_BINARY_DIR}/_deps/boost")
  if(NOT EXISTS "${boost_dir}/boost/version.hpp")
    message(STATUS "Boost not found, downloading ${QLR_BOOST_URL}")
    get_filename_component(archive_name "${QLR_BOOST_URL}" NAME)
    set(archive "${CMAKE_BINARY_DIR}/_deps/${archive_name}")
    file(DOWNLOAD "${QLR_BOOST_URL}" "${archive}"
         EXPECTED_HASH SHA256=${QLR_BOOST_SHA256} STATUS status)
    list(GET status 0 code)
    if(NOT code EQUAL 0)
      message(FATAL_ERROR "Downloading ${QLR_BOOST_URL} failed: ${status}")
    endif()
    # headers only
    set(extract_dir "${CMAKE_BINARY_DIR}/_deps/boost-extract")
    file(REMOVE_RECURSE "${extract_dir}" "${boost_dir}")
    file(ARCHIVE_EXTRACT INPUT "${archive}" DESTINATION "${extract_dir}" PATTERNS "*/boost/*")
    file(GLOB top "${extract_dir}/boost_*")
    file(RENAME "${top}" "${boost_dir}")
    file(REMOVE_RECURSE "${extract_dir}" "${archive}")
  endif()
  set(QLR_BOOST_INCLUDE_DIR "${boost_dir}")
  set(QLR_BOOST_DOWNLOADED ON)
endif()
message(STATUS "Boost headers: ${QLR_BOOST_INCLUDE_DIR}")
