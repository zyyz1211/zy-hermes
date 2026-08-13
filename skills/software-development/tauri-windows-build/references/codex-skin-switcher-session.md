# Codex Skin Switcher — Build Reproduction Recipe

Source: https://github.com/bytefer/<项目名>
Built: 2026-07-17, Windows 11, git-bash

## Environment

- Host: Windows 11, `C:\Users\<user>`
- Shell: git-bash / MSYS
- Node: v24.14.0, pnpm 11.13.1
- Rust: 1.97.0, target `x86_64-pc-windows-gnu` (GNU, from Tsinghua mirror)
- LLVM-MinGW: 22.1.8 (UCRT), installed via `winget install MartinStorsjo.LLVM-MinGW.UCRT --silent`
- WebView2: included in Windows 11 (no extra install needed)
- Visual Studio / MSVC: **NOT** installed

## Key paths

| Thing | Path |
|-------|------|
| LLVM-MinGW root | `C:\Users\<user>\AppData\Local\Microsoft\WinGet\Packages\MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe\llvm-mingw-20260616-ucrt-x86_64` |
| Cargo config | `C:\Users\<user>\.cargo\config.toml` |
| Built exe (GNU debug) | `C:\Users\<user>\AppData\Local\Temp\<项目名>\src-tauri\target\x86_64-pc-windows-gnu\debug\<项目名>.exe` |
| Deployed runtime | `C:\Users\<user>\Desktop\CodexSkinSwitcher\` |

## Cargo config used

```toml
[target.x86_64-pc-windows-gnu]
linker = "C:/Users/<user>/AppData/Local/Microsoft/WinGet/Packages/MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe/llvm-mingw-20260616-ucrt-x86_64/bin/x86_64-w64-mingw32-clang.exe"
ar = "C:/Users/<user>/AppData/Local/Microsoft/WinGet/Packages/MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe/llvm-mingw-20260616-ucrt-x86_64/bin/x86_64-w64-mingw32-ar.exe"

[source.crates-io]
replace-with = "ustc"
[source.ustc]
registry = "sparse+https://mirrors.ustc.edu.cn/crates.io-index/"
```

## Env vars for build (must export before `cargo build` or `pnpm package:test`)

```bash
export CC_x86_64_pc_windows_gnu="C:/Users/<user>/AppData/Local/Microsoft/WinGet/Packages/MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe/llvm-mingw-20260616-ucrt-x86_64/bin/x86_64-w64-mingw32-clang.exe"
export AR_x86_64_pc_windows_gnu="C:/Users/<user>/AppData/Local/Microsoft/WinGet/Packages/MartinStorsjo.LLVM-MinGW.UCRT_Microsoft.Winget.Source_8wekyb3d8bbwe/llvm-mingw-20260616-ucrt-x86_64/bin/x86_64-w64-mingw32-ar.exe"
export PATH="$HOME/.cargo/bin:$PATH"
```

## Build command

```bash
cd /tmp/<项目名>
# (with above env vars set)
pnpm install && pnpm build          # frontend
pnpm package:test                    # Tauri build (debug, creates .exe)
```

## Issues encountered

1. **Rustup download timeouts** — fixed by `RUSTUP_DIST_SERVER=https://mirrors.tuna.tsinghua.edu.cn/rustup`
2. **crates.io slow** — fixed by USTC mirror in cargo config
3. **TOML unicode escape** (`\U` in `\Users`) — fixed by using forward slashes in config.toml
4. **MSYS paths `/c/...` not found by cc crate** — cc crate uses `CreateProcess` directly, so `C:/...` is required
5. **`unable to find library -lgcc_eh`** — LLVM-MinGW doesn't bundle libgcc; fixed by copying `libclang_rt.builtins-x86_64.a` → `libgcc.a` and `libunwind.a` → `libgcc_eh.a`
6. **WiX download timeout** — cosmetic; the `.exe` was already built, only the MSI bundling failed
7. **`WebView2Loader.dll` missing** — debug builds don't bundle it; must copy alongside .exe
8. **Resources not found** — debug builds need manual assembly of `resources/` tree (injector.mjs, themes, CSS assets)
9. **pnpm esbuild skipped** — need `sed -i 's/esbuild: false/esbuild: true/' pnpm-workspace.yaml && pnpm rebuild`

## Session 2 — MSVC Release Build (2026-07-20)

After the GNU debug build had runtime issues (skin engine install failed), switched
to **MSVC Release** target — the officially supported path for Tauri on Windows.

### VS Build Tools installation

```bash
# Download bootstrapper
curl -L -o /tmp/vs_BuildTools.exe "https://aka.ms/vs/17/release/vs_BuildTools.exe"

# Install minimal C++ workload (MSVC compiler + Windows SDK + MSBuild only)
# Correct argument ORDER matters: --add and --includeRecommended go BEFORE --quiet
/tmp/vs_BuildTools.exe \
  --add Microsoft.VisualStudio.Workload.VCTools \
  --includeRecommended \
  --quiet --wait --norestart --nocache
```

Installed to: `C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\`

### Build with MSVC from git-bash

The `vcvars64.bat` environment is required but NOT compatible with MSYS paths.
Use a `.bat` wrapper:

```bat
@echo off
:: Clear ANY CC/AR env vars that might leak from .bashrc / global environment
set CC=
set CC_x86_64_pc_windows_gnu=
set AR=
set AR_x86_64_pc_windows_gnu=

call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvars64.bat"

cd /d "C:\Users\<user>\AppData\Local\Temp\<项目名>"
set PATH=%USERPROFILE%\.cargo\bin;%PATH%

cargo build --release
:: OR for full Tauri bundle:
call pnpm tauri:windows
```

**CRITICAL:** `set CC=` is required. If `CC` env var from .bashrc (pointing to LLVM-MinGW)
persists, the `cc` crate uses it instead of MSVC's `cl.exe` AND fails because the MSYS
path `/c/Users/...` is not a valid Windows path for `CreateProcess`.

### Results

| Aspect | Value |
|--------|-------|
| Build target | `stable-x86_64-pc-windows-msvc` (default after switch) |
| Build time | ~2 min (`cargo build --release`) |
| Exe size | 10 MB (vs debug 234 MB) |
| Cargo mirror | USTC (same as GNU approach) |
| Bundles | MSI (32 MB) + NSIS (31 MB) |
| WiX download | Succeeded this time (no timeout) |
| NSIS download | Succeeded (from tauri-apps/binary-releases) |

### Key lessons

1. **GNU target is a trap for Tauri apps** — the `cc` crate's path handling and
   missing `libgcc`/`libgcc_eh` make it brittle, and runtime COM/WinRT interop
   (used by Codex Store-package detection) may silently fail with GNU CRT.
2. **MSVC is the right target for Tauri on Windows** — install VS Build Tools with
   the VCTools workload (~1-2 GB). The `vcvars.bat` + `.bat` wrapper pattern works
   reliably from git-bash.
3. **Clean env vars** — `CC`, `CC_x86_64_pc_windows_gnu`, `AR`, `AR_x86_64_pc_windows_gnu`
   MUST be unset before MSVC builds, or the cc crate picks them up and fails.
