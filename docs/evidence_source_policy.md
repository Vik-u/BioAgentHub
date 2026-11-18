# Evidence Source Policy (Forge + Fabric)

## Canonical sources (default)
- **All active Fabric flows use Forge outputs under** `workspaces/<topic>/`.
- Workspace paths are resolved via `utils/workspace_utils.resolve_workspace_root()` and/or `WORKSPACE_ROOT`.

## Legacy sources (opt-in only)
- **KnowledgeGraph/** is legacy-only and not used by canonical Fabric entrypoints.
- Legacy scripts/paths that default to `KnowledgeGraph/` include an inline comment:
  "Legacy: uses KnowledgeGraph outputs; canonical uses workspaces/<topic>/ (Forge)."

## Instrument evidence policy (opt-in)
- Instrument evidence is **OFF by default**.
- Enable by setting `BIOAGENT_USE_INSTRUMENTS=1` (or `true/yes/on`).
- When disabled, instrument retrieval/inventory is skipped and `InstrumentGraph/` is not touched.

## Before/After reference summary
- **Before:** Fabric protocol agent defaulted to `KnowledgeGraph/` protocols; instrument evidence could be touched without a global toggle.
- **After:** Fabric protocol agent resolves `workspaces/<topic>/protocols` (via workspace resolver). InstrumentGraph access is gated by `BIOAGENT_USE_INSTRUMENTS` and `--include-instruments` (biofoundry) or is skipped entirely when the toggle is off.

## Notes
- Forge build scripts still accept legacy `KnowledgeGraph/` defaults for backwards compatibility, but canonical usage is via `workspaces/<topic>/`.
