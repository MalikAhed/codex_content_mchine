# Storage policy

The working filesystem and Git history are different budgets. The queue's admission check measures a selected working directory at claim time; it is not an OS quota and does not limit Git history or growth during a job. Enable a filesystem quota and monitor both before unattended production.

Default producer admission policy: one case in progress, one voice process, a 10 GB private production working-set cap, at least 8 GiB free disk, and at most 30 minutes or 20 sentence clips per invocation before a saved checkpoint. Model and dependency installation are a separate operator-approved private cache budget. Do not claim these are enforced by the static site or GitHub heartbeat; the future runner must supply and enforce them.

Public release budget: target at most 25 MB of new compressed assets per case and pause for review before public history exceeds 1 GB. These are admission thresholds, not permission to silently downsample below quality requirements. Share narrator assets and reusable scenes by immutable hash/path, use WebP and compressed final narration, and build optional self-contained exports on demand. Do not commit raw PCM, models, reference recordings, repeated export bundles or MP4.

Immutable revisions and deleted files remain in normal Git history. Sustained production needs an owner-approved archival policy or external asset storage. Never promise unlimited storage, force-push history, remove approved work, or delete source artifacts merely to meet a cap. Pause and persist a receipt when the budget is reached; let the owner review the concrete archive/storage proposal.
