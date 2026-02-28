# AGENTS.md

## Cursor Cloud specific instructions

This repository contains **NASA EUROPA** — a C++ planning, scheduling, and constraint programming framework. See `README.md` for an overview.

### Tech stack
- **C++ (primary)** with CMake build system
- **Java** for PSEngine bindings (via SWIG) and Swing UI
- **ANTLR3** for NDDL/ANML parser generation

### Build

```bash
cd /workspace
mkdir -p build && cd build
cmake -DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++ -DCMAKE_CXX_FLAGS="-fpermissive -Wno-terminate" ..
make -j$(nproc)
```

**Gotcha:** The default compiler on this environment is Clang, but it can't find `libstdc++`. Always use `-DCMAKE_C_COMPILER=gcc -DCMAKE_CXX_COMPILER=g++`.

**Gotcha:** This legacy codebase throws exceptions in destructors. Modern C++ (GCC 13) treats destructors as `noexcept` by default, causing `terminate()`. The flags `-fpermissive -Wno-terminate` suppress this but the NDDL parser still segfaults at runtime due to ANTLR3-generated code issues on modern compilers.

### External dependencies (not in repo)
These must be installed as system packages or built from source:
- `libboost-dev`, `swig`, `antlr`, `libcppunit-dev`, `libalgorithm-diff-perl` (apt)
- **libantlr3c-3.4** — built from source (`www.antlr3.org/download/C/libantlr3c-3.4.tar.gz`), installed to `/usr/local`
- **ANTLR 3.4 JAR** — downloaded to `ext/lib/antlr-3.jar` (must be version 3.4 to match the C runtime; version 3.5.x produces incompatible generated code)

### Tests

```bash
cd /workspace/build && ctest
```

- **8 core module tests pass**: TinyXml, Utils, ConstraintEngine, PlanDatabase, RulesEngine, TemporalNetwork, ANML, System.
- **35 NDDL-related tests fail** (segfault/abort): Known upstream issue — the ANTLR3-generated NDDL parser crashes on GCC 13 / modern C++. All `run-nddl-interp-*` tests depend on NDDL and are affected.
- To run only the passing core tests: `ctest -R "^(TinyXml|Utils|ConstraintEngine|PlanDatabase|RulesEngine|TemporalNetwork|ANML|System)Test$"`

### Project structure (key paths)
- `src/PLASMA/` — C++ core modules (Utils, ConstraintEngine, PlanDatabase, RulesEngine, TemporalNetwork, NDDL, Solvers, Resource, ANML, System)
- `src/Java/` — Java bindings and Swing UI
- `ext/lib/antlr-3.jar` — ANTLR3 tool JAR (must be present for build)
- `examples/` — Example planning problems (Rover, Light, Shopping, BlocksWorld, NQueens, UBO)
- `config/` — Runtime configuration files (PlannerConfig.xml, NDDL.cfg, Debug.cfg)
- `build/` — CMake build directory (out-of-source)
