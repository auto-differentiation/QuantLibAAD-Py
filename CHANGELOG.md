# ChangeLog

This log is to be read in conjunction with [ChangeLog.txt](./ChangeLog.txt). 
It lists the QuantLib-Risks specific changes on top of what is already listed in 
the underlying QuantLib-SWIG changelog.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.41.0] - Unreleased

- Matches QuantLib and QuantLib Python bindings version 1.41
- Builds against QuantLibAAD 1.41 (formerly QuantLib-Risks-Cpp) and the shared libxad of the installed xad 2.2 package (`xad>=2.2,<2.3`), which is not bundled
- Tapes are shared with xad through libxad, thread-local per Python thread; QuantLib no longer patches `xad.adj_1st.Tape`
- Builds the unmodified QuantLib 1.41 release, no QuantLib patches
- One-step build with scikit-build-core; wheels for Python 3.10-3.14 on Linux, macOS and Windows
- `tools/sync-swig.sh` syncs `SWIG/` with a QuantLib-SWIG release, re-applying the XAD changes in `SWIG/patches/`

## [1.33.3] - 2024-04-04

- Builds against renamed xad-autodiff -> xad Python package
- Cleanup of repository

## [1.33.2] - 2024-03-29

- Renaming quantlib-risks -> QuantLib-Risks for consistency
- Fixing markdown annotations in examples
- otherwise technically identical

## [1.33] - 2024-03-25

Initial release, matching QuantLib Python bindings version 1.33


[1.41.0]: https://github.com/auto-differentiation/QuantLib-Risks-Py/compare/v1.33.3...v1.41.0

[1.33.3]: https://github.com/auto-differentiation/QuantLib-Risks-Py/compare/v1.33.2...v1.33.3

[1.33.2]: https://github.com/auto-differentiation/QuantLib-Risks-Py/compare/v1.33...v1.33.2

[1.33]: https://github.com/auto-differentiation/QuantLib-Risks-Py/releases/tag/v1.33
