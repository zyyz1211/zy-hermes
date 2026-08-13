# Session: 比武大会（唐诗版）HTML Game Debugging

## Context

User (用户) had an HTML-based Tang Poetry quiz game ("比武大会·唐诗版") with 4 levels. The game had 3 distinct bugs on mobile and desktop:

1. **Mobile:** Buttons unresponsive ("点不开")
2. **JS freeze:** Answering correctly did nothing ("答对了就没有反应")
3. **Save bug:** Artifact count never decreased ("用了以后不会减少")

## Bug 1: Mobile Touch Unresponsive

**Root cause:** Missing `touch-action: manipulation` on interactive elements. iOS Safari treats taps without this as potential double-tap zoom gestures, introducing a ~300ms delay and sometimes swallowing the tap entirely.

**Secondary causes:**
- `:hover` pseudo-classes applied via CSS made buttons look "stuck" after tap on mobile
- Button padding was too small (6-8px) for touch targets (Apple HIG recommends 44px minimum)

**Fix applied (3 changes):**

### a) Global touch-action
```css
html { -webkit-tap-highlight-color: transparent; }
button, .btn-start, .btn-start-level, .btn-restart, .btn-gallery,
.btn-gallery-back, .option-btn, .artifact-btn, .wardrobe-item {
  touch-action: manipulation;
  cursor: pointer;
}
```

### b) Mobile hover suppression
```css
@media (hover: none) and (pointer: coarse) {
  .btn-start:hover, .option-btn:hover, .btn-restart:hover {
    transform: none !important;
    box-shadow: none !important;
    background: inherit !important;
    border-color: inherit !important;
  }
}
```

### c) Minimum touch target size
```css
@media (max-width: 600px) {
  .option-btn { min-height: 44px; padding: 10px 8px; }
  .btn-start { min-height: 48px; }
  .btn-start-level, .btn-restart { min-height: 44px; }
}
```

## Bug 2: Answering Correctly Freezes the Page

**Root cause:** `ReferenceError: tryGetArtifact is not defined`. The function was called in the `isCorrect` branch but was never defined — only placeholder comments existed:

```javascript
// 尝试获得法宝（答对题时10%概率）
// 恢复1个法宝（过关时）
```

The `else` branch (wrong answer) didn't call `tryGetArtifact()`, so it worked fine. The `if (isCorrect)` branch threw a ReferenceError at that line, halting the entire handler.

**Diagnosis method:**
1. Noted that correct-answer branch froze, wrong-answer branch worked
2. Compared the two branches line by line
3. Found `tryGetArtifact()` called only in the correct branch
4. Searched for its definition — none found
5. Confirmed with `grep -n "tryGetArtifact\|restoreArtifact" file.html` — only call sites, no definitions

**Fix:** Added the missing function definitions:

```javascript
function tryGetArtifact() {
  if (Math.random() < 0.1) {
    const save = loadSave();
    if (save.artifacts < save.maxArtifacts) {
      save.artifacts++;
      saveSave(save);
      updateArtifactDisplay();
      showArtifactResult('✨ 获得法宝！');
    }
  }
}
function restoreArtifact() {
  const save = loadSave();
  if (save.artifacts < save.maxArtifacts) {
    save.artifacts++;
    saveSave(save);
    updateArtifactDisplay();
  }
}
```

## Bug 3: Artifacts Never Decrease

**Root cause:** `loadSave()` unconditionally set `merged.artifacts = 3` after reading from localStorage:

```javascript
function loadSave() {
  const raw = localStorage.getItem(SAVE_KEY);
  if (raw) {
    const data = JSON.parse(raw);
    const merged = { ...def, ...data };
    merged.artifacts = 3;  // BUG: overwrites saved value every time
    return merged;
  }
}
```

The `useArtifact()` function would decrement and save correctly, but the next call to `loadSave()` (for display update or next use) would read back 3.

**Fix:**
1. Removed `merged.artifacts = 3` from `loadSave()`
2. Added initialization to `startGame()` instead:

```javascript
startGame = function() {
  const save = loadSave();
  save.artifacts = 3;  // Only at new game start
  saveSave(save);
  updateArtifactDisplay();
  _origStartGameArtifact();
};
```

## Key Lessons

1. **"One-branch freeze"** — When JS works in one code path but not another, search for undefined functions called only in the broken path. The ReferenceError halts execution silently.
2. **`loadSave()` must be a pure read** — Never mutate or force values inside a load function. Initialization belongs in the "new game" / "first load" path.
3. **Mobile web debugging checklist** — Start with `touch-action: manipulation`, then check hover states, then touch target sizes.
4. **Monkey-patching chains** — When code has `const _origX = X; X = function() { ... }` patterns repeated, always find the LAST assignment to determine which version is actually active.
