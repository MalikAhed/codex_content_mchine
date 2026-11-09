# Queue operations

The repository contains a control plane, not a production backend. It does not generate stories, run a voice model, send jobs to a service, or publish content automatically. The queue starts paused. GitHub's scheduled heartbeat is best effort: schedules may be delayed or disabled, and GitHub-hosted runners are ephemeral. Its workflow summary and short-lived artifact are observations, not durable queue state. Expired lease recovery is committed to `pipeline/state/queue.json`; if a concurrent change conflicts, the workflow fails instead of overwriting it. Retry after resolving the conflict.

All committed queue payloads and receipts are public. Use only public metadata; never put credentials, private paths, voice recordings, source files, unpublished media, or lease tokens in committed state. Keep recordings and generated work outside this public repository. Do not place raw voice or source embedded HTML in Pages. The queue lock and atomic file replacement protect processes sharing one filesystem; they do **not** coordinate independent clones. Only a hash of a lease token is stored in state; keep the token itself private. A multi-host deployment requires a private transactional shared queue with authentication and atomic claim/finish before enabling workers; Git commits are not a distributed lock. There is no configured authenticated backend or worker in this repository.

Operators can inspect and exercise the local control plane with Python 3:

```sh
python3 pipeline/queue.py status
python3 pipeline/queue.py enqueue --key case-id --payload '{"case":"case-id"}'
python3 pipeline/queue.py resume
python3 pipeline/queue.py claim --worker local-runner --storage /private/work --budget-bytes 10000000000 --minimum-free-bytes 2000000000
python3 pipeline/queue.py pause
python3 pipeline/queue.py stop
```

`pause` prevents new claims; `stop` is a persistent stop latch and also prevents claims. Neither kills a running process: the operator/runner must stop it safely. `reset-stop` clears the latch, and `resume` clears pause. A runner must stop work before its lease expires and use `finish --id ID --token TOKEN --receipt '{"result":"review required"}'` while it owns the lease. Use `--failed` for a failed attempt; failed jobs do not retry automatically. A stale worker cannot finish after expiry. Expired leases are returned to the queue by heartbeat or claim. A worker must reconcile any partial external side effects before retry; queue deduplication cannot make an external backend exactly-once. Ensure no old worker is still running before recovery/retry: lease expiry alone cannot terminate it.

Only one lease can be active on the shared queue at a time, limiting voice-model concurrency on that queue. The disk cap checks current regular-file bytes under the storage directory and free space at claim time; it is not a hard quota and cannot prevent a job from growing beyond the cap. Use an OS/filesystem quota and appropriate free-space reserve for enforcement during execution. Lease duration must cover the job or the runner must finish before expiry; no lease renewal is implemented. Actual external execution requires an authenticated, explicitly configured backend and secure shared coordination. Configure these privately, validate credentials and model/voice permissions, enforce a single voice model across all runners, and perform all production review gates before enabling. Never send the owner's voice to a new external voice-processing destination without their approval.

To deploy the static site, set the repository Pages source to **GitHub Actions**. The Pages workflow publishes only `docs/` on pushes to `main` or manual dispatch. Repository settings or environment protection may require administrator action. The workflow does not upload pipeline state or private production files. Scheduled workflows on public repositories can be disabled after inactivity; check the Actions page and re-enable if needed.
