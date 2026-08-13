---
name: web-frontend-debugging
description: "Debugging patterns for HTML/CSS/JS browser apps: mobile touch issues, JavaScript ReferenceError branch freezes, localStorage save/load resets, and DOM event debugging."
version: 1.0.0
author: Hermes Agent
metadata:
  hermes:
    tags: [debugging, frontend, web, javascript, css, mobile, dom]
    related_skills: [systematic-debugging]
---

# Web Frontend Debugging

## Overview

Patterns for debugging browser-based frontend applications — HTML games, SPAs, and interactive web pages. Covers mobile touch issues, JavaScript silent failures, and localStorage state bugs that don't produce console errors visible to the user.

**Key principle:** When a feature works in one code path but not another, the root cause is almost always a function/variable that exists in the working path but is missing/undefined in the broken path.

---

## Pattern 1: "One-Branch Freeze" (JavaScript ReferenceError)

**Symptom:** A function works in some branches (e.g., answering wrong) but silently does nothing / freezes the page in others (e.g., answering correctly). No console error — the page just stops responding.

**Root Cause:** An undefined function is called only in the frozen branch. JavaScript throws a `ReferenceError` which halts the entire function at that line. The other branch never calls the missing function, so it works fine.

**Diagnosis:**
1. Identify the two branches (e.g., `if (isCorrect)` vs `else`)
2. Look for function calls that appear in the frozen branch but NOT in the working branch
3. Search for the function definition: `grep -n "function functionName"` or `search_files("functionName = function")`
4. If the definition doesn't exist anywhere, that's your bug

**Common causes:**
- Developer left placeholder comments (`// TODO: implement tryGetArtifact`) without writing the function
- Function was referenced but never defined during a refactor
- Typo in function name between call site and definition

**Fix:** Define the missing function. Check nearby comments for what it should do.

---

## Pattern 2: Save/Load Reset Bug (localStorage)

**Symptom:** Values saved to localStorage persist (no error), but always reset to the same default on the next read.

**Root Cause:** The `loadSave()` function unconditionally overwrites a saved value after reading it from storage:

```javascript
function loadSave() {
  const raw = localStorage.getItem(SAVE_KEY);
  if (raw) {
    const data = JSON.parse(raw);
    const merged = { ...defaults, ...data };
    merged.artifactCount = 3;  // BUG: Always resets to 3!
    return merged;
  }
}
```

**Why it's subtle:** The function DOES read the saved value and merge it, but then overwrites the specific field. The developer intended to initialize on first load, but placed it inside the read-every-time path.

**Fix:** Move initialization out of `loadSave()` into the app start function:

```javascript
// loadSave() — pure read, no mutations
function loadSave() {
  const raw = localStorage.getItem(SAVE_KEY);
  if (raw) return { ...getDefaultSave(), ...JSON.parse(raw) };
  return getDefaultSave();
}

// startGame() — initializes on new game only
function startGame() {
  const save = loadSave();
  save.artifactCount = 3;  // Only at game start
  saveSave(save);
}
```

---

## Pattern 3: Mobile Touch Not Working

**Symptom:** Buttons work on desktop but are unresponsive/delayed on mobile (iOS Safari).

### Checklist (in order):

1. **Missing `touch-action: manipulation`** — iOS Safari has ~300ms tap delay. Add to ALL interactive elements:
   ```css
   button, .option-btn, .btn-start {
     touch-action: manipulation;
     cursor: pointer;
   }
   ```

2. **Sticky `:hover` on touch devices** — Hover state applied on tap never clears. Fix:
   ```css
   @media (hover: none) and (pointer: coarse) {
     .btn:hover, .option-btn:hover {
       transform: none !important;
       box-shadow: none !important;
       background: inherit !important;
     }
   }
   ```

3. **Tap highlight** — iOS Safari shows gray overlay on tap. Fix:
   ```css
   html { -webkit-tap-highlight-color: transparent; }
   ```

4. **Touch target too small** — Minimum 44×44pt:
   ```css
   @media (max-width: 600px) {
     .option-btn { min-height: 44px; padding: 10px 8px; }
     .btn-start { min-height: 48px; }
   }
   ```

5. **Overlay coverage** — Check that dynamic overlays (animations, popups) have `pointer-events: none`.

---

## Pattern 4: Monkey-Patching Chain Analysis

**Symptom:** Code has multiple `const _origX = X; X = function() { ... _origX(); }` patterns. Debugging which version is active is confusing.

**Diagnosis:**
- Search for the LAST assignment to the function name (`grep -n "functionName\s*="`)
- The last one wins — read that one
- Check if the last monkey-patch correctly calls `_origX()` (or if it was supposed to but doesn't)

**Pitfall:** Multiple monkey-patches of the same function can break the chain if one fails to call `_origX()` or overwrites `_origX` instead of capturing it.

## Reference Files

- `references/js-branch-freeze-and-mobile-touch.md` — Full session-specific debugging transcript with real error messages and reproduction steps.
