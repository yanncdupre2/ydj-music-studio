# Agent Instructions

Read these project files before doing work:

1. `PLANNING.md` — identity, objective, scope, lifecycle, Standing Conditions,
   and durable decisions.
2. `TODO.md` — canonical tasks and current actions. Machine-maintained: task
   edits go through `gtd-finish-session`'s `task_changes`, never by hand.
3. `PROJECT-LOCAL-CONTEXT.md` — current operating knowledge: constraints,
   commands, paths, and integrations. No session history lives here.
4. `README.md` — human orientation and quickstart information.

Run `gtd session context` for the combined current operating knowledge plus the
latest session entry. Session history lives in `SESSION-LOG.md`, with older
entries in `ARCHIVE/SESSION-LOG.md`; read those only when reconciling the past.

Follow the GTD doctrine supplied by the active environment.

Use AI judgment for objectives, scope, tradeoffs, risks, priorities, and
proposed next actions. Use the machine core for deterministic validation,
generation, synchronization, lifecycle, and repository operations.

Do not store current project state or session-specific instructions in this
file.
