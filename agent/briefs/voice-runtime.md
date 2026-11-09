# Voice prerequisite evidence — 2026-11-09

Current private setup uses Python 3.12; torch 2.6.0+cpu and torchaudio 2.6.0+cpu; official Chatterbox package 0.1.7 at `ab55923c27757c90cfcc407baa57dc25a7d25217`; Perth 1.1.0 resolved from upstream moving master at `ff1c8ac55a976971245cdd53c18d6131ca00d993`. Transitive versions were recorded privately, not fully pinned. Do not claim a reproducible lockfile beyond this evidence. Model target snapshot remains `749d1c1a46eb10492095d68fbcf55691ccf137cd` from the owner's kit.

Offline imports and model loader method lookup passed; `pip check` found no broken requirements. No model weight was downloaded/loaded and no inference was tested. Actual narration remains blocked by model-host network access. No audition or source recording was uploaded anywhere.

Resource evidence: cgroup 32 GiB RAM and 4 CPU cores, no GPU; private virtual environment 1.9 GiB; approximately 57.5 GiB disk free afterward. Torch CPU wheel 178.6 MB and torchaudio CPU wheel 1.7 MB. Pure Python packaging for official checkouts only, no compiled source builds. Preserve >=8 GiB disk reserve; use one model process. Installation alone does not establish runtime performance or narration quality.

Future machines require a private mounted owner source kit, dependency environment and hash-verified local model files. Neither voice inputs nor weights are in this repository. Exact private setup logs remain on this workspace disk and need an authorized private artifact store for durable remote production. Do not publish the cloud environment snapshot or configuration to preserve them.
