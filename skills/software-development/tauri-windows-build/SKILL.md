---
name: tauri-windows-build
description: >-
  Build Tauri 2 apps on Windows from git-bash/MSYS without Visual Studio/MSVC.
  Uses LLVM-MinGW as the C/C++ toolchain with Rust's x86_64-pc-windows-gnu target.
  Captures the path-quoting, cc-crate, and libgcc pitfalls unique to this setup.
---

# Tauri Windows Build

Build a Tauri 2 application on Windows from git-bash/MSYS.

## Two approaches

| Approach | Toolchain | Status | Use when… |
|----------|-----------|--------|-----------|
| **MSVC (recommended)** | VS Build Tools + `x86_64-pc-windows-msvc` | ✅ Production | Tauri apps needing COM/WinRT/WebView2 interop; any app destined for users |
| **LLVM-MinGW (fallback)** | LLVM-MinGW + `x86_64-pc-windows-gnu` | ⚠️ Build-only | VS Build Tools cannot be installed; limited to headless / CI / build-verification only |

**CRITICAL:** GNU-target builds may compile and launch but **fail at runtime** for apps
that use Windows COM, WinRT, AppX package APIs (e.g. Codex Store detection, CDP injection
for skin engines). Always prefer MSVC for user-facing Tauri apps on Windows.

---


## Step-by-step

### Approach A: MSVC (recommended)

### 0. Prerequisites

- **Rustup** — `winget install Rustlang.Rustup` or [rustup-init.exe](https://rustup.rs)
- **pnpm** — `npm install -g pnpm`
- **VS Build Tools** — see step 1
- **WebView2** — already shipped on Windows 11 / Windows 10 with latest updates

### 1. Install Visual Studio Build Tools (C++ workload only)

```bash
# Download the bootstrapper (4.3 MB)
curl -L -o /tmp/vs_BuildTools.exe "https://aka.ms/vs/17/release/vs_BuildTools.exe"

# Install with ONLY the C++ tools workload (no full IDE, ~1-2 GB download)
# Argument ORDER matters: --add / --includeRecommended BEFORE --quiet
/tmp/vs_BuildTools.exe \
  --add Microsoft.VisualStudio.Workload.VCTools \
  --includeRecommended \
  --quiet --wait --norestart --nocache
```

Installs to `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\`.

### 2. Switch Rust to MSVC target

```bash
export PATH="$HOME/.cargo/bin:$PATH"
# Use a Chinese mirror if the default is slow
export RUSTUP_DIST_SERVER=https://mirrors.tuna.tsinghua.edu.cn/rustup

rustup default stable-x86_64-pc-windows-msvc
```

### 3. Configure cargo mirror (optional, China)

Edit `~/.cargo/config.toml`:

```toml
[source.crates-io]
replace-with = "ustc"

[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"
```

### 4. Build with MSVC from git-bash

**CRITICAL:** Clear any `CC` / `AR` env vars that your `.bashrc` may have set
for GNU/LLVM-MinGW. If they persist, the `cc` crate picks them up instead of MSVC's
`cl.exe` and fails because MSYS paths are not valid Win32 paths.

The `vcvars64.bat` sets up MSVC environment variables. Run it via a `.bat` wrapper:

```bat
@echo off
:: Clear stale GNU/LLVM-MinGW env vars
set CC=
set CC_x86_64_pc_windows_gnu=
set AR=
set AR_x86_64_pc_windows_gnu=

:: Activate MSVC x64 environment
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

cd /d "C:\path\to\tauri-project"
set PATH=%USERPROFILE%\.cargo\bin;%PATH%

:: Build
cargo build --release

:: OR full Tauri bundle (MSI + NSIS):
call pnpm tauri:windows
```

Run from git-bash: `cmd.exe /c "C:\path\to\build.bat"`

### 5. Release output

After `pnpm tauri:windows`:

```
src-tauri/target/release/
├── <项目名>.exe      ← standalone exe (~10 MB)
└── bundle/
    ├── msi/*.msi                ← Windows Installer (~32 MB)
    └── nsis/*-setup.exe         ← NSIS installer (~31 MB)
```

WiX and NSIS tools are downloaded automatically on first build. If the download
times out, the `.exe` is still built successfully — only the installer step fails.

---


### 1. Install LLVM-MinGW

LLVM-MinGW provides `clang`, `lld`, `libunwind`, and `compiler-rt` — complete
replacement for the traditional MinGW-GCC toolchain, and works with Rust's GNU target.

```bash
winget install MartinStorsjo.LLVM-MinGW.UCRT --silent --accept-package-agreements
```

The installer adds a directory under
`%LOCALAPPDATA%\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_...\llvm-mingw-*-ucrt-x86_64`.
Note the exact path — you'll need it for cargo configuration.

### 2. Install Rust GNU toolchain

```bash
# Use a Chinese mirror if the default is slow (Tsinghua/USTC)
export RUSTUP_DIST_SERVER=https://mirrors.tuna.tsinghua.edu.cn/rustup
rustup default stable-x86_64-pc-windows-gnu
rustup target add x86_64-pc-windows-gnu
```

### 3. Create libgcc/libgcc_eh symlinks

LLVM-MinGW uses `compiler-rt` (not `libgcc`) and `libunwind` (not `libgcc_eh`).
Rust's build scripts expect the traditional MinGW library names. Create copies:

```bash
LLVM_DIR="/c/Users/.../llvm-mingw-*-ucrt-x86_64"
LIBDIR="$LLVM_DIR/x86_64-w64-mingw32/lib"
cp "$LLVM_DIR/lib/clang/22/lib/windows/libclang_rt.builtins-x86_64.a" "$LIBDIR/libgcc.a"
cp "$LIBDIR/libunwind.a" "$LIBDIR/libgcc_eh.a"
```

> **Why:** Without this, `lld` fails with `unable to find library -lgcc_eh` / `-lgcc`
> when linking Rust build scripts.

### 4. Configure cargo (the critical part)

Edit `~/.cargo/config.toml`:

```toml
[target.x86_64-pc-windows-gnu]
linker = "C:/Users/<you>/AppData/Local/Microsoft/WinGet/Packages/MartinStorsjo.LLVM-MinGW.UCRT_.../llvm-mingw-*-ucrt-x86_64/bin/x86_64-w64-mingw32-clang.exe"
ar = "C:/Users/<you>/AppData/Local/Microsoft/WinGet/Packages/MartinStorsjo.LLVM-MinGW.UCRT_.../llvm-mingw-*-ucrt-x86_64/bin/x86_64-w64-mingw32-ar.exe"

[source.crates-io]
replace-with = "ustc"
[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"
```

**CRITICAL PATH RULES:**
- Use **forward slashes** (`C:/Users/...`) — TOML's `\U` is interpreted as unicode escape.
- Use the **full Windows absolute path** (drive letter + colon) — MSYS `/c/...` paths
  do NOT work because the `cc` crate passes the path directly to `CreateProcess`.
- **No spaces** issues if you use forward slashes — they work natively in Win32.

### 5. Set environment variables for the cc crate

When running `cargo build`, the `cc` build-script crate looks for the C compiler via
`CC_x86_64_pc_windows_gnu`.  Pass the same Windows-native path:

```bash
export CC_x86_64_pc_windows_gnu="C:/Users/<you>/AppData/.../x86_64-w64-mingw32-clang.exe"
export AR_x86_64_pc_windows_gnu="C:/Users/<you>/AppData/.../x86_64-w64-mingw32-ar.exe"
export PATH="$HOME/.cargo/bin:$PATH"

cd /path/to/tauri-project
cargo build --target x86_64-pc-windows-gnu
```

### 6. Build the Tauri app

```bash
# Frontend first
pnpm install && pnpm build

# Full Tauri build
export CC_x86_64_pc_windows_gnu="..."   # same as above
export AR_x86_64_pc_windows_gnu="..."
pnpm tauri:windows   # or pnpm package:test
```

The binary lands at `src-tauri/target/debug/<app-name>.exe` (debug) or `release/`.

### 7. Run the debug build (resources + DLL bundling)

Debug builds **do not bundle resources** or `WebView2Loader.dll` into the exe. You
must manually assemble the runtime directory:

```bash
APP="<项目名>"              # your app name
BUILD_DIR="src-tauri/target/x86_64-pc-windows-gnu/debug"
DIST_DIR="dist/MyApp"                  # output folder on desktop, etc.

mkdir -p "$DIST_DIR/resources/skin-engine/windows/"{scripts,themes,assets}

# Exe + WebView2 DLL
cp "$BUILD_DIR/$APP.exe" "$DIST_DIR/"
cp "$BUILD_DIR/WebView2Loader.dll" "$DIST_DIR/"

# Tauri resources (theme catalog + skin engine files)
cp "$BUILD_DIR/resources/theme-catalog.json" "$DIST_DIR/resources/"
cp "$BUILD_DIR/resources/skin-engine/windows/scripts/injector.mjs" \
   "$DIST_DIR/resources/skin-engine/windows/scripts/"
cp src-tauri/resources/skin-engine/windows/assets/* \
   "$DIST_DIR/resources/skin-engine/windows/assets/"
cp -r src-tauri/resources/skin-engine/windows/themes/* \
   "$DIST_DIR/resources/skin-engine/windows/themes/"
```

Without these resources, the app launches but cannot find its skin engine files
("无法安装皮肤" / "无法安装引擎").  For production use, prefer a **release build**
which bundles everything into a single MSI installer (see below).

### 8. Release build (with installer)

```bash
# Same env vars as Step 5
export CC_x86_64_pc_windows_gnu="..."
export AR_x86_64_pc_windows_gnu="..."
pnpm tauri:windows
```

This produces an MSI installer under `src-tauri/target/release/bundle/msi/`.
The first run downloads WiX (`wix314-binaries.zip`) — if the network is slow,
the build still produces the `.exe` binary; only the MSI bundling step fails.

### 9. Frontend build notes (pnpm + esbuild)

When running `pnpm install` for the first time, pnpm may skip `esbuild`'s
postinstall script:
```
[ERR_PNPM_IGNORED_BUILDS] Ignored build scripts: esbuild@0.28.1
```
Fix by enabling the build:

```bash
# Edit pnpm-workspace.yaml
sed -i 's/esbuild: false/esbuild: true/' pnpm-workspace.yaml
# Then rebuild
pnpm rebuild
```

Without this, the Vite frontend build will fail silently.

## Pitfalls

| Pitfall | Symptom | Fix |
|---------|---------|-----|
| CC/AR env var leaks from .bashrc | cc crate uses GNU/LLVM-MinGW compiler instead of MSVC's `cl.exe` even after vcvars | `set CC=` in .bat wrapper before `call vcvars64.bat` |
| MSYS path in `config.toml` | `linker ... not found` / `os error 3` | Use `C:/...` forward-slash Windows path |
| Backslash in TOML | `too few unicode value digits` | Use forward slashes inside TOML strings |
| Missing `libgcc` / `libgcc_eh` | `unable to find library -lgcc_eh` at link time | Copy `compiler-rt.builtins` → `libgcc.a`, `libunwind.a` → `libgcc_eh.a` |
| Slow crates.io / rustup | Downloads time out repeatedly | Set `RUSTUP_DIST_SERVER` + cargo `source.crates-io.replace-with = "ustc"` |
| WiX bundling timeout | `failed to bundle project: timeout` | Network issue — the `.exe` is already built; skip MSI by using `cargo build` directly |
| Missing `WebView2Loader.dll` | `由于找不到WebView2Loader.dll，无法继续执行代码` | Copy from build output `target/.../debug/WebView2Loader.dll` alongside the .exe |
| Missing Tauri resources (debug build) | App opens but "无法安装皮肤" / "无法安装引擎" | Copy `resources/` tree from build output alongside the .exe (Step 7) |
| pnpm skipped esbuild build | Vite build fails silently after `pnpm install` | `sed -i 's/esbuild: false/esbuild: true/' pnpm-workspace.yaml && pnpm rebuild` |

## Verification

```bash
# Confirm the toolchain
rustc --version            # should show 1.97+ (x86_64-pc-windows-gnu)
x86_64-w64-mingw32-clang --version   # clang 22+

# Confirm linker works (build a trivial Rust project)
cargo new hello --bin && cd hello
echo 'fn main() { println!("hello from gnu!"); }' > src/main.rs
cargo build --target x86_64-pc-windows-gnu 2>&1 | tail -5
```

## References

See `references/<项目名>-session.md` for the full reproduction recipe
from the session that established this workflow.
