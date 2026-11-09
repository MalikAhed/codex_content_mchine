(() => {
  'use strict';
  const scenes = [
    {src:'../assets/generated/silk-road-library.webp', alt:'A cinematic reconstructed library scene.'},
    {src:'../assets/generated/narrator.webp', alt:'A stylized narrator at a desk.'},
    {src:'../assets/generated/silk-road-release-landscape.webp', alt:'A conceptual reconstructed closing hall.'}
  ];
  const image = document.querySelector('#scene'), stage = document.querySelector('#stage'), play = document.querySelector('#play'), seek = document.querySelector('#seek'), time = document.querySelector('#time');
  let current = 0, running = false, previous = 0, sceneIndex = -1, frameId = 0;
  function draw() {
    const index = Math.min(2, Math.floor(current / 6));
    if (index !== sceneIndex) { sceneIndex = index; image.src = scenes[index].src; image.alt = scenes[index].alt; }
    seek.value = current; time.textContent = `0:${String(Math.floor(current)).padStart(2, '0')}`;
    play.textContent = running ? '❚❚' : '▶'; play.setAttribute('aria-label', running ? 'Pause' : 'Play'); stage.classList.toggle('playing', running || current > 0);
  }
  function frame(now) { if (!running) return; if (previous) current = Math.min(18, current + (now - previous) / 1000); previous = now; if (current >= 18) { running = false; previous = 0; } draw(); if (running) frameId = requestAnimationFrame(frame); }
  function toggle() { if (running) { running = false; cancelAnimationFrame(frameId); previous = 0; } else { if (current >= 18) current = 0; running = true; previous = 0; cancelAnimationFrame(frameId); frameId = requestAnimationFrame(frame); } draw(); }
  play.addEventListener('click', toggle); stage.addEventListener('click', toggle);
  seek.addEventListener('input', () => { cancelAnimationFrame(frameId); current = Number(seek.value); previous = 0; draw(); if (running) frameId = requestAnimationFrame(frame); });
  document.querySelector('#fullscreen').addEventListener('click', async () => { try { if (document.fullscreenElement) await document.exitFullscreen(); else await document.querySelector('.player').requestFullscreen?.(); } catch { /* Fullscreen may be unavailable in the embedding browser. */ } });
  document.addEventListener('keydown', event => { if (event.target.tagName === 'INPUT' || event.target.tagName === 'BUTTON') return; if (event.code === 'Space') { event.preventDefault(); toggle(); } else if (event.key === 'ArrowRight' || event.key === 'ArrowLeft') { event.preventDefault(); current = Math.max(0, Math.min(18, current + (event.key === 'ArrowRight' ? 5 : -5))); previous = 0; draw(); } });
  draw();
})();
