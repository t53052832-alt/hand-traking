# Nyxel

A real-time AR hand-tracking application built with **MediaPipe**, **OpenCV**, and a custom **ModernGL + GLFW** GPU shader pipeline. Built as a hands-on project to learn Python, OpenGL, and GLSL from the ground up.

Repo: https://github.com/t53052832-alt/Nyxel

---

## What it does

Tracks one or two hands in real time via webcam and renders GPU shader effects (thermal false-color, camera distortion, Sobel edge detection, color inversion — and more, easily added) confined to a dynamic polygon shape stretched between fingertips across both hands. A full on-screen button UI lets you toggle overlays, switch effects, and change colors live.

---

## Project Architecture (OOP structure)

The project is organized into single-responsibility files:

| File | Responsibility |
|---|---|
| `main.py` | The core loop. Grabs the camera frame, hands it to the hand tracker, sends the results to the renderer. |
| `renderer.py` | The GPU graphics engine — encapsulates ModernGL, GLFW, shader compilation, and GPU memory management. |
| `hand_tracker.py` | The AI engine — MediaPipe initialization, landmark tracking, coordinate math, button UI, and HUD drawing. |
| `buttons.py` | A reusable `Button` class supporting both simple toggles and multi-state (cycling) buttons. |
| `FingerConnection.py` | Draws a line between any two fingers (same-hand or cross-hand), with distance/angle calculation. |
| `shaders/` | One `.frag` file per visual effect, plus a shared `shape_vertex.glsl`, loaded dynamically at startup. |

---

## The Rendering Pipeline (Painter's Algorithm)

Instead of drawing everything onto one CPU image like the original OpenCV-only prototype, the project renders in three GPU layers, back to front:

1. **Background (GPU texture)** — the raw camera frame, uploaded once per frame via `texture.write()`.
2. **Midground (GPU vertex buffer)** — the dynamic polygon stretched between fingertips, drawn with `moderngl.TRIANGLE_FAN`, shaded by whichever effect is currently selected.
3. **Foreground (HUD texture)** — a transparent RGBA canvas (drawn with normal OpenCV calls — buttons, landmarks, text) uploaded as a second texture and alpha-blended on top of everything.

## The Shader Effect System

Effects aren't hardcoded — `main.py` defines a list of effect names (`["thermal", "distort", "sobel", "invert"]`), and `renderer.py` loads a matching `shaders/<name>.frag` file for each one at startup, compiling all of them once into a `{name: program}` dictionary. Switching effects at runtime is just changing which dictionary key is used — no recompiling, no code changes. Adding an 11th effect means writing one new `.frag` file and adding its name to the list.

A **true multi-effect stacking system** (`draw_stacked_poly`) also exists in `renderer.py`: it ping-pongs rendering between two offscreen framebuffers, so effect 2 can process effect 1's actual output pixels (not just a combined formula) — necessary for effects like Sobel that need to sample neighboring pixels. This is implemented but not yet wired to a live control in `main.py` (currently commented out) — a natural next feature.

---

## Technical Challenges Solved

**Preventing VRAM leaks.** Textures and vertex buffers are allocated exactly once, in `__init__`. The render loop never creates new GPU objects — it uses `.write(bytes)` to overwrite existing GPU memory every frame, keeping memory usage flat regardless of how long the app runs.

**Coordinate system conversion.** OpenCV uses a top-left origin with pixel coordinates; OpenGL uses a bottom-left origin with Normalized Device Coordinates (-1.0 to 1.0). A dedicated `convert()` method remaps fingertip pixel coordinates into NDC before they're uploaded to the polygon's vertex buffer.

**Camera mirroring vs. GPU flipping — two different flips, two different reasons.** The frame handed to MediaPipe is flipped on the X-axis so on-screen movement matches the user's own movement (a normal mirror). The frame handed to the GPU as a texture is *separately* flipped on the Y-axis, because OpenGL texture coordinates read bottom-to-top while image data is stored top-to-bottom. Conflating these two flips was an early source of confusion.

**The "bowtie" effect (self-intersecting polygon).** Building a quad between two hands' fingertips by iterating both hands in the same order twists the shape into a bowtie. Fixed by walking the first hand's fingers forward and the second hand's fingers in `reversed()` order, so the four points trace a clean, non-crossing perimeter.

**Ghost data management.** `current_poly_points` is reset to `None` at the very start of every `track_and_draw()` call, so the GPU polygon disappears the instant hands leave the frame, instead of freezing on the last known shape.

**Multi-hand hover flicker.** With two hands both carrying a fingertip landmark, checking hover on both every frame caused the shared `was_hovering` debounce flag to be overwritten by whichever hand's check ran second — buttons flickered between hover/not-hover uncontrollably. Fixed by restricting menu hover checks to a single designated hand (`hand_index == 0`) via `enumerate()` over the detected hands.

**Config-driven UI toggling.** Rather than commenting out buttons and manually removing them from multiple lists, each button group is built from a list of `(button, enabled: bool)` tuples, filtered once via a list comprehension. Disabling a button is a one-line flip, with nothing else to keep in sync.

**Adapting Shadertoy-style shaders.** Shadertoy shaders use a different entry point (`mainImage`, `fragCoord` in pixels, `iChannel0`/`iResolution` uniforms) than a ModernGL fragment shader (`main()`, `uv` in 0–1 range, custom uniform names). Effects like the Sobel edge detector were ported by converting pixel-offset math to UV-relative math and re-wiring the uniform names to match this project's `bg_tex` / `tex_resolution` convention.

---

## Setup

**Requirements (strict versions — newer ones break MediaPipe on Windows):**

```
mediapipe==0.10.21
opencv-python==4.10.0.84
numpy<2
moderngl
glfw
```

Why pinned: `mediapipe` silently upgraded past `0.10.21` during development and removed the legacy `solutions.hands` API entirely in `1.0.1` — every effect and landmark call in `hand_tracker.py` depends on that legacy API. `opencv-python` 5.x requires `numpy>=2`, which conflicts directly with MediaPipe's own numpy requirement, so `numpy<2` is non-negotiable alongside these two.

**Install:**
```bash
python -m venv .venv
.venv\Scripts\activate
pip install mediapipe==0.10.21 opencv-python==4.10.0.84 "numpy<2" moderngl glfw
```

> **Note:** `hand_tracker.py` imports `OneEuroFilter` (an optional landmark-smoothing filter) from a local `OneEuroFilter.py` file that isn't currently committed to this repo — add it before running, or remove the smoothing code path if you don't need it.

**Run:**
```bash
python main.py
```
Press **ESC** or close the window to quit.

---

## Controls

The on-screen buttons come in two independent layers:

- **Enabled in code** — whether a button exists and appears at all, set via the `(button, True/False)` config lists at the top of `HandTracker.__init__`. Currently `line_data`, `cords`, and `color` are disabled this way (present in code, hidden from the UI).
- **Active at runtime** — a button's own on/off (or cycling) state, changed by hovering your index fingertip over it.

| Button | What it does |
|---|---|
| `more buttons` | Expands/collapses the secondary menu (shape overlays, effect, color) |
| `poly` | Toggles the fingertip-to-fingertip polygon (the shader-effect surface) |
| `points` | Draws a dot on each tracked fingertip |
| `effect` | Cycles through available shader effects (`thermal`, `distort`, `sobel`, `invert`, …) |
| `rec` / `big circle` / `small circle` | Draws a bounding shape around the detected hand |
| `circle on finger` | Draws a circle on one hand sized by its distance to the other hand's fingertip |
| `cords` *(disabled by default)* | Prints live fingertip pixel coordinates |
| `line data` *(disabled by default)* | Shows distance/angle labels on connection lines |
| `color` *(disabled by default)* | Cycles the overlay color for shape effects |

---

## Roadmap / Known Limitations

- **Hatch/grid pattern fill** — prototyped as a standalone learning script (fullscreen quad + `fract()`-based grid shader) but not yet ported into the `shaders/` effect system as a named poly effect.
- **True effect stacking (`draw_stacked_poly`)** — implemented in `renderer.py`, not yet exposed through any button or control in `main.py`.
- **Gesture recognition** — explored conceptually (MediaPipe's Model Maker / Tasks API supports training custom gestures on top of hand landmarks) but not implemented. Would require moving off the legacy `solutions.hands` API this project is currently pinned to, so it's a bigger architectural step, not a drop-in addition.
- **Camera-angle robustness** — landmark detection degrades at extreme hand angles; this is a limitation of MediaPipe's pretrained model itself, not something fixable via this project's code.
