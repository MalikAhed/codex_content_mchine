# Casework — crime story studio

A compact public review desk for carefully researched cinematic crime stories. The first delivered media is an **18-second silent visual style study**, not a narrated episode or verified case account. No complete story is ready for owner approval.

- Site source: [`docs/index.html`](docs/index.html). Intended Pages URL: `https://malikahed.github.io/codex_content_mchine/` — not live yet: Pages enablement was rejected for the workflow token. Set the repository Pages source as described below. [Actual failed run](https://github.com/MalikAhed/codex_content_mchine/actions/runs/42632528068).
- Run locally: `python3 -m http.server 8000 --directory docs`, then open `http://localhost:8000`.
- Review decisions stay in your browser; download their JSON to hand them to production. The static site has no authenticated shared approval backend.
- The 30-minute GitHub Actions heartbeat checks queue health and recovers expired leases. It does not generate content or restart chat agents. The producer is **not configured**, and the production queue starts paused.
- [Operations and runner requirements](pipeline/README.md), [production blockers](content/production-status.json), [candidate research handoff](content/silk-road/README.md), [fresh-agent instructions](AGENTS.md), [current handoff](agent/STATE.md).

## What remains blocked

This workspace's proxy denied access to attempted primary/independent research and the pinned official voice model. No new owner narration or verified Silk Road script has been created. The public repository intentionally contains no voice reference, audition, raw WAV, embedded source example, model weights or credentials. A future producer needs an owner-authorized private mounted kit and model cache; this repository alone cannot reconstruct the owner's voice.

A continuous producer additionally requires a supported authenticated agent runtime, image generation, private transactional queue for multiple hosts, bounded storage/runtime and allowed research/model access. The Sol/Terra team labels are roles supported in this chat, not a guarantee that the same names are public API model IDs. Reuse the briefs and queue contract with the runtime actually available.

## Portable offline review

Build a single portable HTML file on demand with `python3 pipeline/export_html.py --out /workspace/exports/style-study.html`. It embeds only public WebP scene/layer assets and the current timeline/player. It remains a silent visual study. The export is intentionally outside the repository to avoid storing duplicate media.

## Validation

`python3 -m unittest discover -s tests -v` exercises lease recovery, stale tokens, deduplication, pause/stop, disk admission, release evidence/hash/timing coverage and safe portable exports. Browser QA covers desktop/mobile layout, local review decisions, adversarial catalog text and deterministic silent study controls. Final audio/listening, factual verification and complete-episode timing checks cannot pass while their inputs are absent.

## Deployment

Pushes to `main` deploy `docs/` with GitHub Actions. The workflow attempts Pages enablement; if repository administration prevents it, set **Settings → Pages → Build and deployment → Source → GitHub Actions**, then rerun **Deploy Pages**. Heartbeat results update the public runtime snapshot and trigger a Pages refresh. Schedules are best effort and can be delayed or disabled by GitHub. Check the visible last-check time; a healthy monitor does not mean a production worker exists.
