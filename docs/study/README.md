# Study player timeline

`timeline.json` is the source of playback timing. `duration`, each scene's `start` and `end`, and caption cue boundaries are seconds. Scenes must be contiguous from zero through the declared duration. Scene image paths and the optional transparent `subject` path are relative to the player page. Captions use `{ "start": 0, "end": 1, "text": "..." }` and render as text.

For silent studies, set `audio` to `null`. For measured narration, set it to `{ "src": "relative-audio-path", "duration": 18.0 }`, using the actual audio duration for both audio and timeline duration. Playback requires a user gesture. Audio time drives all scene, caption and narrator motion; an audio load, play, or duration mismatch error stops playback rather than substituting silence. The player checks the browser-reported duration within 0.05 seconds. The declared timing is a structural check only; it does not establish a listening review. Preserve the actual PCM sample counts and sentence-boundary receipt separately in production records, and complete listening and production review.

The optional subject layer is registered for the approved narrator plate dimensions described in `../visual-production.md`; it is not a general-purpose layer placement contract. The current study is silent and makes no verified historical claims.
