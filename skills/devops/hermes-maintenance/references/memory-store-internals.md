# Hermes Memory Store Internals & Repair

Source-level facts about the on-disk memory store (verified against
`tools/memory_tool.py` and `agent/learning_mutations.py` in the hermes-agent
runtime at `~/.hermes/hermes-agent/`).

## Files, targets, limits

| Target | File | Content | Default char limit |
|--------|------|---------|--------------------|
| `memory` | `~/.hermes/memories/MEMORY.md` | personal notes | 2200 |
| `user` | `~/.hermes/memories/USER.md` | user profile | 1375 |

- Limits overridable in `config.yaml`: `memory.memory_char_limit`,
  `memory.user_char_limit` (read by `load_on_disk_store()`).
- Other profiles: `~/.hermes/profiles/<name>/memories/MEMORY.md` (+ USER.md).
- The char budget is for the WHOLE store (all entries joined), and any single
  parsed entry must also stay under it — that's drift signal #2.
- `USER.md.bak.<ts>` snapshots are auto-created by the drift guard before a
  refusal, so the "lost" content is always recoverable.

## Canonical format (what the tool writes)

- `ENTRY_DELIMITER = "\n§\n"` (newline, §, newline).
- File = entries joined by the delimiter. NO § wrappers around entries, no
  blank lines between them, no markdown sections, no trailing §.
- Entries may be multiline, but must not contain `\n§\n` inside.
- `_write_file`: `"\n§\n".join(entries)` → temp file via `mkstemp` in same dir
  → `os.fsync` → `atomic_replace` (atomic rename, no flock).
- `_read_file`: split on `\n§\n`, `strip()` each entry, drop empties.

## Drift guard (`_detect_external_drift`, issue #26045)

Refuses the mutation and snapshots a `.bak.<ts>` when either signal fires:

1. **Round-trip mismatch** — re-parsing and re-joining (`"\n§\n".join(parsed)`)
   doesn't byte-match `raw.strip()`. Classic causes: a `§ entry §` per-line
   style (older tool versions / manual edits), markdown `##` sections, stray
   lone `§` lines. Note: with the wrapper style the WHOLE file parses as ONE
   entry, so it usually trips signal #2 too.
2. **Entry-size overflow** — any single parsed entry exceeds the whole-store
   char limit. Means an external writer appended free-form content; flushing
   would truncate it.

Error message seen by the agent:
`Refusing to write USER.md: file on disk has content that wouldn't round-trip
through the memory tool ... A snapshot was saved to .../USER.md.bak.<ts> ...`

Remediation hint from the guard: rewrite the file as a clean §-delimited list
of entries (or move the extra content out), then retry.

## Repair procedure (proven in the field)

1. `read_file` the drifted USER.md/MEMORY.md + the `.bak.<ts>` snapshot.
2. Consolidate: one entry per logical fact. Compress aggressively — merge
   overlapping environment/network/tool entries, drop facts already carried by
   the system prompt (e.g. shell default), keep user preferences and
   corrections nearly verbatim. Target ~70-85% of the limit.
3. `write_file` the clean file: each entry on its own line, joined by literal
   `\n§\n`, no leading/trailing §, no blank lines.
4. Verify the tool accepts it with a no-op round trip:
   `memory(action='replace', old_text=<unique substring of any entry>,
   content=<same text>, target='user')` → expect `success: true`,
   `entry_count: N`, `usage: NN% — X/Y chars`.

Note: after the file is clean, individual entries are addressable by
`old_text` substring — prefer the memory tool for subsequent edits.

## GitHub MCP token diagnostics

- Token location: `~/.hermes/config.yaml` →
  `mcp_servers.github.env.GITHUB_PERSONAL_ACCESS_TOKEN` (server is
  `@modelcontextprotocol/server-github`).
- Extraction pitfall: `grep -A1 "GITHUB_PERSONAL_ACCESS_TOKEN"` returns the
  NEXT line (empty/wrong). Grep the key directly:
  `TOKEN=$(grep "GITHUB_PERSONAL_ACCESS_TOKEN" ~/.hermes/config.yaml | sed 's/.*: *//; s/^"//; s/"$//')`
- Test: `curl -s -o /dev/null -w "HTTP %{http_code}\n" -H "Authorization: Bearer $TOKEN" https://api.github.com/user`
- `HTTP 401 Bad credentials` = token revoked/expired (classic tokens expire;
  account password changes revoke them). Fix = user regenerates at
  github.com/settings/tokens (repo scope), update config.yaml, restart MCP.
- Public repo reads (raw.githubusercontent.com, unauthenticated
  api.github.com) work without any token — an MCP failure says nothing about
  repo reachability.
