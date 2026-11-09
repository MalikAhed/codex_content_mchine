(() => {
  'use strict';
  const image = document.querySelector('#scene'), subject = document.querySelector('#subject'), caption = document.querySelector('#caption'), stage = document.querySelector('#stage'), play = document.querySelector('#play'), seek = document.querySelector('#seek'), time = document.querySelector('#time'), durationLabel = document.querySelector('#duration'), status = document.querySelector('#player-status');
  let timeline, audio = null, current = 0, running = false, previous = 0, sceneIndex = -1, frameId = 0, failed = false, playToken = 0;
  const format = n => `${Math.floor(n / 60)}:${String(Math.floor(n % 60)).padStart(2, '0')}`;
  const stopFrame = () => { cancelAnimationFrame(frameId); previous = 0; };
  function fail(message) { playToken++; running = false; failed = true; stopFrame(); if (audio) audio.pause(); status.textContent = message; play.disabled = true; draw(); }
  function draw() {
    if (!timeline) return;
    const index = Math.max(0, timeline.scenes.findIndex((scene, i) => current >= scene.start && (current < scene.end || (i === timeline.scenes.length - 1 && current === timeline.duration))));
    const scene = timeline.scenes[index];
    if (index !== sceneIndex) { sceneIndex = index; image.src = scene.image; image.alt = scene.alt || ''; subject.hidden = !scene.subject; if (scene.subject) subject.src = scene.subject; }
    if (scene.subject) subject.style.transform = `rotate(${0.85 * Math.sin(2 * Math.PI * (current - scene.start) / 4.6)}deg)`;
    const cue = timeline.captions.find(c => current >= c.start && current < c.end); caption.textContent = cue ? cue.text : '';
    seek.value = current; time.textContent = format(current); play.textContent = running ? '❚❚' : '▶'; play.setAttribute('aria-label', running ? 'Pause' : 'Play'); stage.classList.toggle('playing', running || current > 0); play.disabled = failed;
  }
  function frame(now) {
    if (!running) return;
    if (audio) current = audio.currentTime;
    else if (previous) current = Math.min(timeline.duration, current + (now - previous) / 1000);
    previous = now;
    if (current >= timeline.duration) { current = timeline.duration; running = false; stopFrame(); if (audio) audio.pause(); }
    draw(); if (running) frameId = requestAnimationFrame(frame);
  }
  async function toggle() {
    if (!timeline || failed) return;
    if (running) { playToken++; running = false; stopFrame(); if (audio) audio.pause(); }
    else {
      const token = ++playToken;
      if (current >= timeline.duration) { current = 0; if (audio) audio.currentTime = 0; }
      running = true; draw();
      if (audio) { try { await audio.play(); if (token !== playToken || !running) return; current = audio.currentTime; } catch { if (token === playToken) fail('Audio could not play. Check the source and try again.'); return; } }
      if (token !== playToken || !running) return;
      stopFrame(); frameId = requestAnimationFrame(frame);
    }
    draw();
  }
  function seekTo(value) { if (!timeline || failed) return; stopFrame(); current = Math.max(0, Math.min(timeline.duration, value)); if (audio) { audio.currentTime = current; current = audio.currentTime; } draw(); if (running) frameId = requestAnimationFrame(frame); }
  async function fullscreen() { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.querySelector('.player').requestFullscreen?.(); } catch { status.textContent = 'Fullscreen is unavailable in this browser.'; } }
  image.addEventListener('error', () => fail('A scene image could not be loaded. Playback is unavailable.'));
  subject.addEventListener('error', () => fail('A subject layer could not be loaded. Playback is unavailable.'));
  play.addEventListener('click', toggle); stage.addEventListener('click', toggle); seek.addEventListener('input', () => seekTo(Number(seek.value))); document.querySelector('#fullscreen').addEventListener('click', fullscreen);
  document.addEventListener('keydown', event => { if (event.target.tagName === 'INPUT' || event.target.tagName === 'BUTTON') return; if (event.code === 'Space') { event.preventDefault(); toggle(); } else if (event.key.toLowerCase() === 'f') fullscreen(); else if (event.key === 'Home' || event.key === 'End') { event.preventDefault(); seekTo(event.key === 'Home' ? 0 : timeline.duration); } else if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') { event.preventDefault(); seekTo(current + (event.key === 'ArrowRight' ? 5 : -5)); } });
  async function init() {
    try {
      const response = await fetch('timeline.json', {cache:'no-store'}); if (!response.ok) throw new Error('Timeline unavailable');
      const data = await response.json();
      if (!Number.isFinite(data.duration) || data.duration <= 0 || !Array.isArray(data.scenes) || !data.scenes.length || !Array.isArray(data.captions) || data.scenes.some((s,i) => !Number.isFinite(s.start) || !Number.isFinite(s.end) || s.start !== (i ? data.scenes[i-1].end : 0) || s.end <= s.start || typeof s.image !== 'string') || data.scenes.at(-1).end !== data.duration || data.captions.some(c => !Number.isFinite(c.start) || !Number.isFinite(c.end) || c.start < 0 || c.end <= c.start || c.end > data.duration || typeof c.text !== 'string')) throw new Error('Invalid timeline');
      timeline = data; seek.max = data.duration; durationLabel.textContent = format(data.duration);
      if (data.audio) {
        if (typeof data.audio.src !== 'string' || data.audio.duration !== data.duration) throw new Error('Invalid audio declaration');
        audio = new Audio(data.audio.src); audio.preload = 'metadata';
        audio.addEventListener('error', () => fail('Audio could not be loaded. Playback is unavailable.'));
        audio.addEventListener('loadedmetadata', () => { if (!Number.isFinite(audio.duration) || Math.abs(audio.duration - data.duration) > 0.05) fail('Audio duration does not match the timeline. Playback is unavailable.'); });
        audio.addEventListener('ended', () => { running = false; stopFrame(); current = audio.currentTime; draw(); });
        status.textContent = 'Audio playback starts when you press play.';
      } else status.textContent = 'Silent study · no audio.';
      draw();
    } catch { fail('The study timeline could not be loaded. Playback is unavailable.'); }
  }
  init();
})();
