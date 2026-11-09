(() => {
  'use strict';
  const $ = (selector, root = document) => root.querySelector(selector);
  const escapeHTML = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
  const labels = {research:'Research', scripting:'Scripting', production:'In production', review:'Awaiting review', changes:'Changes requested', approved:'Approved'};
  const key = 'casework-owner-decisions-v1';
  let cases = [], filter = 'all', decisions = {};
  try { decisions = JSON.parse(localStorage.getItem(key) || '{}') || {}; } catch { decisions = {}; }
  const statusOf = item => labels[item.status] ? item.status : 'production';
  const isComplete = media => media && media.type === 'html' && media.kind === 'complete' && media.available;
  const requiredChecks = ['factsVerified', 'visualsReviewed', 'narrationValidated', 'listeningReviewed', 'durationsValidated', 'independentQaPassed'];
  const canApprove = item => typeof item.revision === 'string' && item.revision.trim().length > 0 && statusOf(item) === 'review' && (item.media || []).some(isComplete) && item.receiptVerified === true && requiredChecks.every(check => item.checks?.[check] === true);
  const displayStatus = item => statusOf(item) === 'review' && !canApprove(item) ? 'In production' : labels[statusOf(item)];
  const selected = item => filter === 'all' || (filter === 'production' && (['research','scripting','production','changes'].includes(statusOf(item)) || (statusOf(item) === 'review' && !canApprove(item)))) || (filter === 'review' && canApprove(item)) || (filter === 'approved' && statusOf(item) === 'approved');
  function render() {
    $('#nav-count').textContent = cases.length;
    $('#filter-count').textContent = cases.length;
    $('#stat-total').textContent = String(cases.length).padStart(2, '0');
    $('#stat-production').textContent = String(cases.filter(item => ['research','scripting','production','changes'].includes(statusOf(item)) || (statusOf(item) === 'review' && !canApprove(item))).length).padStart(2, '0');
    $('#stat-review').textContent = String(cases.filter(canApprove).length).padStart(2, '0');
    const visible = cases.filter(selected);
    $('#queue-content').innerHTML = visible.length ? visible.map(item => `<article class="case-row"><div class="case-art" aria-hidden="true"><span>Case file / ${escapeHTML(item.id)}</span></div><div><div class="case-category">${escapeHTML(item.category || 'Case file')}</div><h3 class="case-title">${escapeHTML(item.title || 'Untitled case')}</h3><p class="case-summary">${escapeHTML(item.summary || 'This story is in progress.')}</p></div><div class="case-meta"><div class="case-meta-label">STATUS</div><div class="case-meta-value"><span class="status ${escapeHTML(statusOf(item))}">${escapeHTML(displayStatus(item))}</span></div></div><div class="case-meta runtime"><div class="case-meta-label">FORMAT</div><div class="case-meta-value">${escapeHTML(item.format || 'In development')}</div></div><button class="row-button" data-open="${escapeHTML(item.id)}" aria-label="Open ${escapeHTML(item.title || 'story')} details">View case ↗</button></article>`).join('') : `<div class="message">${cases.length ? 'No stories in this view yet. Try another filter.' : 'The queue is empty. Stories will appear here when they are added to the catalog.'}</div>`;
  }
  function safeMedia(item) { return (Array.isArray(item.media) ? item.media : []).filter(media => media.available && media.type === 'html'); }
  function openCase(id) {
    const item = cases.find(entry => entry.id === id); if (!item) return;
    const media = safeMedia(item), previousDecision = decisions[id], decision = previousDecision && item.revision && previousDecision.revision === item.revision ? previousDecision : null;
    $('#detail-content').innerHTML = `<div class="eyebrow amber">CASE FILE &nbsp; / &nbsp; ${escapeHTML(item.category || 'STORY IN PROGRESS')}</div><h2 id="detail-title">${escapeHTML(item.title)}</h2><span class="status ${escapeHTML(statusOf(item))}">${escapeHTML(displayStatus(item))}</span><p class="detail-copy">${escapeHTML(item.summary || 'This story is in progress.')}</p><p class="notice">Revision: ${escapeHTML(item.revision || 'Not specified')}</p>${item.notes ? `<p class="notice">${escapeHTML(item.notes)}</p>` : ''}<div class="detail-block"><h3>Watch the story</h3><p class="notice">${media.length ? 'Open the available HTML presentation in a new tab.' : 'No playable HTML is available yet. This case is still in progress.'}</p>${media.map(m => `<a class="secondary media-link" href="${escapeHTML(m.url)}" target="_blank" rel="noopener">Watch ${escapeHTML(m.title || 'story')} ${m.kind === 'complete' ? '' : m.kind === 'style-study' ? '— silent style study' : '— excerpt'} ↗</a><p class="notice">${m.kind === 'complete' ? 'Complete presentation' : m.kind === 'style-study' ? 'Silent style study / work in progress' : 'Excerpt / work in progress'}${m.duration ? ` · ${escapeHTML(m.duration)}` : ''}</p>`).join('')}</div><div class="detail-block"><h3>Owner review</h3><p class="notice">Decisions are saved only in this browser, not to the production catalog or other devices. Download the decision JSON to share it with the team.</p>${previousDecision && !decision ? `<p class="notice">Previous decision (stale): ${escapeHTML(previousDecision.decision === 'approved' ? 'Approved' : 'Changes requested')} · revision ${escapeHTML(previousDecision.revision || 'unspecified')}. It does not apply to this revision.</p>` : ''}${!canApprove(item) ? '<p class="notice">Approval becomes available when a complete presentation is awaiting review and all production checks have passed and a matching release receipt has been verified. Partial studies are not eligible.</p>' : ''}<label for="feedback">Review notes</label><textarea id="feedback" placeholder="Share what is working or what needs attention…">${escapeHTML(decision?.notes || '')}</textarea><div><button class="primary" id="approve" ${canApprove(item) ? '' : 'disabled'}>Approve story</button><button class="secondary" id="request" ${item.revision ? '' : 'disabled'}>Request changes</button><button class="secondary" id="download" ${decision ? '' : 'disabled'}>Download decision ↓</button></div><p class="decision-message" id="decision-message">${decision ? `Local decision: ${escapeHTML(decision.decision === 'approved' ? 'Approved' : 'Changes requested')} · ${escapeHTML(new Date(decision.at).toLocaleString())}` : ''}</p></div>`;
    $('#approve').addEventListener('click', () => saveDecision(item, 'approved'));
    $('#request').addEventListener('click', () => saveDecision(item, 'changes_requested'));
    $('#download').addEventListener('click', () => downloadDecision(item));
    $('#detail-dialog').showModal();
  }
  function saveDecision(item, decision) {
    const notes = $('#feedback').value.trim();
    if (typeof item.revision !== 'string' || !item.revision.trim()) return;
    if (decision === 'changes_requested' && !notes) { $('#decision-message').textContent = 'Please add a note describing the changes requested.'; $('#feedback').focus(); return; }
    if (decision === 'approved' && !canApprove(item)) return;
    const record = {caseId:item.id, caseTitle:item.title, revision:item.revision || null, decision, notes, at:new Date().toISOString(), scope:'browser-local'};
    try { decisions[item.id] = record; localStorage.setItem(key, JSON.stringify(decisions)); $('#decision-message').textContent = `Saved in this browser: ${decision === 'approved' ? 'Approved' : 'Changes requested'}. Download the decision to share it.`; $('#download').disabled = false; }
    catch { delete decisions[item.id]; $('#decision-message').textContent = 'This browser could not save the decision. Check storage settings and try again.'; }
  }
  function downloadDecision(item) {
    const id = item.id;
    if (!item.revision || !decisions[id] || decisions[id].revision !== item.revision) return;
    const blob = new Blob([JSON.stringify(decisions[id], null, 2) + '\n'], {type:'application/json'}), url = URL.createObjectURL(blob), link = document.createElement('a');
    link.href = url; link.download = `casework-${id.replace(/[^a-z0-9_-]/gi, '-')}-decision.json`; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
  function validURL(url) { try { const resolved = new URL(url, location.href); return resolved.origin === location.origin && !resolved.hash && /\.html?$/i.test(resolved.pathname); } catch { return false; } }
  async function checkMedia(media) {
    if (!media || media.type !== 'html' || typeof media.url !== 'string' || !validURL(media.url)) return false;
    try { const response = await fetch(media.url, {method:'GET'}); return response.ok && (response.headers.get('content-type') || '').includes('text/html'); } catch { return false; }
  }
  async function verifyReceipt(item) {
    try {
      const local = path => { const url = new URL(path, location.href); if (url.origin !== location.origin || !['http:', 'https:'].includes(url.protocol)) throw new Error('Nonlocal evidence'); return url; };
      const digest = async (path, expected) => {
        if (typeof path !== 'string' || !/^[a-f0-9]{64}$/i.test(expected || '') || !crypto.subtle) return false;
        const response = await fetch(local(path), {cache:'no-store'}); if (!response.ok) return false;
        const hash = await crypto.subtle.digest('SHA-256', await response.arrayBuffer());
        return Array.from(new Uint8Array(hash), byte => byte.toString(16).padStart(2, '0')).join('') === expected.toLowerCase();
      };
      if (typeof item.releaseReceipt !== 'string' || typeof item.releaseManifest !== 'string' || !item.revision) return false;
      const response = await fetch(local(item.releaseReceipt), {cache:'no-store'}); if (!response.ok) return false;
      const receipt = await response.json();
      if (receipt.status !== 'passed' || receipt.revision !== item.revision || typeof receipt.validatedAt !== 'string' || Number.isNaN(Date.parse(receipt.validatedAt)) || !receipt.artifact || !Array.isArray(receipt.reviewReceipts) || receipt.reviewReceipts.length < 3) return false;
      if (!(item.media || []).some(media => isComplete(media) && local(media.url).href === local(receipt.artifact.path).href)) return false;
      const checks = await Promise.all([digest(item.releaseManifest, receipt.manifestSha256), digest(receipt.artifact.path, receipt.artifact.sha256), ...receipt.reviewReceipts.map(evidence => digest(evidence.path, evidence.sha256))]);
      return checks.every(Boolean);
    } catch { return false; }
  }
  document.querySelectorAll('.filter').forEach(button => button.addEventListener('click', () => { filter = button.dataset.filter; document.querySelectorAll('.filter').forEach(other => { const active = other === button; other.classList.toggle('active', active); other.setAttribute('aria-pressed', String(active)); }); render(); }));
  $('#queue-content').addEventListener('click', event => { const button = event.target.closest('[data-open]'); if (button) openCase(button.dataset.open); });
  $('#close-dialog').addEventListener('click', () => $('#detail-dialog').close());
  $('#detail-dialog').addEventListener('click', event => { if (event.target === $('#detail-dialog')) $('#detail-dialog').close(); });
  async function init() {
    try {
      const response = await fetch('data/catalog.json', {cache:'no-store'}); if (!response.ok) throw new Error('Catalog unavailable');
      const catalog = await response.json(); if (!Array.isArray(catalog.cases)) throw new Error('Invalid catalog');
      cases = catalog.cases.filter(item => item && typeof item.id === 'string' && typeof item.title === 'string').map(item => ({...item, media:Array.isArray(item.media) ? item.media : []}));
      await Promise.all(cases.flatMap(item => item.media.map(async media => { media.available = await checkMedia(media); })));
      await Promise.all(cases.map(async item => { item.receiptVerified = await verifyReceipt(item); }));
      $('#updated').textContent = catalog.updatedAt && !Number.isNaN(Date.parse(catalog.updatedAt)) ? `UPDATED ${new Date(catalog.updatedAt).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}).toUpperCase()}` : 'CATALOG CONNECTED';
      render();
    } catch { $('#queue-content').innerHTML = '<div class="message">The production catalog could not be loaded. Please check the connection and refresh this page.</div>'; $('#updated').textContent = 'CATALOG UNAVAILABLE'; }
  }
  async function loadRuntime() {
    try {
      const response = await fetch('data/runtime.json', {cache:'no-store'});
      if (!response.ok) throw new Error('Unavailable');
      const data = await response.json();
      const checked = data.lastCheck && !Number.isNaN(Date.parse(data.lastCheck)) ? new Date(data.lastCheck) : null;
      const stale = checked && Date.now() - checked.getTime() > 90 * 60 * 1000;
      const status = typeof data.producerStatus === 'string' ? data.producerStatus.replace(/_/g, ' ') : 'unknown';
      $('#runtime-status').textContent = status.toUpperCase();
      $('#monitor-status').textContent = checked && !stale && data.monitorStatus === 'ok' ? 'OK' : 'UNKNOWN';
      $('#runtime-check').textContent = checked ? `${checked.toLocaleString()}${stale ? ' · STALE' : ''}` : 'UNKNOWN';
      $('#runtime-summary').textContent = checked ? (stale ? 'The last monitor report is over 90 minutes old. Current activity is unknown.' : 'Showing the latest published monitor report.') : 'No monitor check has been reported yet. Current activity is unknown.';
      $('#runtime-reason').textContent = [Array.isArray(data.blockedReasons) ? data.blockedReasons.join(' · ') : '', `Queue: ${Number.isFinite(data.queued) ? data.queued : 'unknown'} queued, ${Number.isFinite(data.leased) ? data.leased : 'unknown'} leased`, data.paused ? 'Queue paused' : '', data.stopped ? 'Queue stopped' : ''].filter(Boolean).join(' · ');
      const links = [['Actions', 'https://github.com/MalikAhed/codex_content_mchine/actions'], ['Queue', 'https://github.com/MalikAhed/codex_content_mchine/blob/main/pipeline/state/queue.json']].filter(([,url]) => { try { return new URL(url).protocol === 'https:'; } catch { return false; } });
      $('#runtime-links').innerHTML = links.map(([label,url]) => `<a href="${escapeHTML(url)}" target="_blank" rel="noopener">${label} ↗</a>`).join('');
    } catch {
      $('#runtime-summary').textContent = 'The monitor report is unavailable. Current activity is unknown.';
      $('#runtime-status').textContent = 'UNKNOWN'; $('#monitor-status').textContent = 'UNKNOWN'; $('#runtime-check').textContent = 'UNKNOWN';
    }
  }
  loadRuntime();
  init();
})();
