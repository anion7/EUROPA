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
- **ANTLR 3.2 JAR** — downloaded to `ext/lib/antlr-3.jar`. **Critical: must be version 3.2** (`antlr-3.2.jar`). Version 3.4 generates tree walker code that fails at runtime, and version 3.5.x generates incompatible C code

### Tests

```bash
cd /workspace/build && ctest
```

- **All 43 tests pass** when using the correct ANTLR 3.2 JAR.

### Running the Rover example

```bash
cd /workspace/examples/Rover
# Compile: link against all EUROPA libraries in the build directory
g++ -fpermissive -Wno-terminate \
  $(find /workspace/src/PLASMA -maxdepth 2 -type d \( -name base -o -name component \) -printf '-I%p ') \
  -I/workspace/src/PLASMA/Utils -I/usr/local/include \
  -o Rover-planner Rover-Main.cc RoverCustomCode.cc ModuleRover.cc \
  -L/workspace/build/src/PLASMA/System -lSystem_g \
  -L/workspace/build/src/PLASMA/Resource -lResource_g \
  -L/workspace/build/src/PLASMA/Solvers -lSolvers_g \
  -L/workspace/build/src/PLASMA/NDDL -lNDDL_g \
  -L/workspace/build/src/PLASMA/TemporalNetwork -lTemporalNetwork_g \
  -L/workspace/build/src/PLASMA/RulesEngine -lRulesEngine_g \
  -L/workspace/build/src/PLASMA/PlanDatabase -lPlanDatabase_g \
  -L/workspace/build/src/PLASMA/ConstraintEngine -lConstraintEngine_g \
  -L/workspace/build/src/PLASMA/Utils -lUtils_g \
  -L/workspace/build/src/PLASMA/TinyXml -lTinyXml_g \
  -L/usr/local/lib -lantlr3c \
  -Wl,-rpath,/workspace/build/src/PLASMA/{System,Resource,Solvers,NDDL,TemporalNetwork,RulesEngine,PlanDatabase,ConstraintEngine,Utils,TinyXml}
# Run with PLASMA_HOME set so the NDDL include path resolves
PLASMA_HOME=/workspace ./Rover-planner Rover-initial-state.nddl PlannerConfig.xml
```

### Project structure (key paths)
- `src/PLASMA/` — C++ core modules (Utils, ConstraintEngine, PlanDatabase, RulesEngine, TemporalNetwork, NDDL, Solvers, Resource, ANML, System)
- `src/Java/` — Java bindings and Swing UI
- `ext/lib/antlr-3.jar` — ANTLR3 tool JAR (must be present for build)
- `examples/` — Example planning problems (Rover, Light, Shopping, BlocksWorld, NQueens, UBO)
- `config/` — Runtime configuration files (PlannerConfig.xml, NDDL.cfg, Debug.cfg)
- `build/` — CMake build directory (out-of-source)
