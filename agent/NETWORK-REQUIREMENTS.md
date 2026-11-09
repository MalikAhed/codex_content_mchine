# Network and private runtime prerequisites

This is a reviewable requirements list, not applied cloud environment configuration. No environment draft or snapshot was published. In this session the proxy explicitly denied `api.github.com`, the Pages host, attempted research hosts and the official model host. Git HTTPS read/push and the GitHub website work; CPU package sources work. No secret values belong here.

| Purpose | Hosts to allow in the selected runtime | Status / limits |
| --- | --- | --- |
| Repository and deployment API | `github.com`, `api.github.com`, `raw.githubusercontent.com`, `codeload.github.com` | Git push works. API CONNECT denied locally. GitHub Actions runs remotely; its initial Pages creation was denied by repository token permissions, separately from local network policy. |
| Published site verification | `malikahed.github.io` | Locally denied. Pages not enabled by the workflow token; owner repository setup required first. |
| Primary research | `www.justice.gov`, `www.whitehouse.gov`, `www.courtlistener.com` | Attempted DOJ/CourtListener CONNECT denied. White House is a proposed additional primary source. Exact case documents still must be found and retrieved. |
| Independent corroboration | `apnews.com`, `www.reuters.com`; optionally `www.theguardian.com` | Attempted hosts CONNECT denied. Homepages are not evidence. Preserve document URLs, dates and exact claims after access is restored. |
| Official pinned model | `huggingface.co`, `*.huggingface.co`, `*.hf.co` | Pinned model endpoint CONNECT denied. CDN redirect hosts must also be allowed after inspecting actual official redirects; a wildcard is not proof every required transfer is covered. Do not send the owner's recording to these hosts. |
| CPU package installation | `download.pytorch.org`, `download-r2.pytorch.org`, `pypi.org`, `files.pythonhosted.org`, `github.com` | Existing package preset permits the tested torch/torchaudio wheels and official source clone. No source builds or model substitutions. |

Enter secrets through the runtime's private settings/vault, never chat or committed files. A backend credential alone does not provide a producer: configure a supported agent runtime, image generation, private voice mount, verified local model cache, private transactional queue, bounded run/disk limits and safe checkpoint/recovery. The Sol/Terra roles in this session are not public API model compatibility promises. Browser-local owner decisions must be explicitly imported and validated by any future authenticated backend.
