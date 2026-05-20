# neodojo

neodojo turns instructional movement videos into synchronized teaching playback.
This language defines the domain concepts used when discussing routine reports.

## Language

**Phase**:
One named method within a routine, such as one of the eight Baduanjin methods.
Each **phase** may contain one or more visible rounds in the source video.
_Avoid_: sub phase, method chunk

**Round**:
One complete visible teaching unit of a **phase** in the source video. A round
may include both left and right sides when the phase is defined as a paired
movement, but should trim waiting time and unnecessarily long holds.
Consecutive left/right teaching groups are not "repeated commands"; they are
separate rounds unless a paired phase needs both sides to be complete.
Baduanjin routine reports should target roughly 180-220 seconds across the
eight selected rounds unless that would break a paired phase.
_Avoid_: half-side action, repeat, repetition, loop

**Paired Phase**:
A **phase** whose standard teaching unit includes both left-side and right-side
execution. A **round** of a paired phase is incomplete if it contains only one
side.
_Avoid_: two sub phases, left/right demos

**Self-Contained Report Directory**:
A report directory whose `index.html` can play its local original-video,
SMPL-X, and G1 assets using relative paths without depending on external
artifact roots.
_Avoid_: single-file HTML, lightweight index

**Routine Overview Page**:
The top-level page of a **Self-Contained Report Directory**. It summarizes all
routine phases and links to one full phase report per phase.
_Avoid_: aggregate replay page, lightweight index

**Phase Report Page**:
A self-contained page for one **phase** and one selected **round**, containing
the synchronized original clip, SMPL-X Teaching Track, and G1 Model Replay.
_Avoid_: phase demo, public demo

**SMPL-X Teaching Track**:
The canonical human motion track used for teaching accuracy and scoring.
_Avoid_: skeleton demo, scoring skeleton

**G1 Visual Track**:
A Unitree G1 retargeted motion track used only as a visual companion.
_Avoid_: G1 scoring track, robot teacher

**G1 Model Replay**:
A visual replay rendered from a real Unitree G1 model descriptor and a **G1
Visual Track**. A final publishable routine report requires G1 Model Replay
rather than schematic-only evidence.
_Avoid_: G1 playback, robot playback

**G1 Schematic Evidence**:
A lightweight visual fallback that illustrates G1-like motion without proving a
real Unitree G1 model replay. It is acceptable for development reports but not
for final publishable routine reports.
_Avoid_: G1 model replay, actual robot replay

## Example Dialogue

Dev: "Should the Baduanjin report include every repeat of each method?"

Domain expert: "No. Each phase should use one clear round from the source video,
trimming waits and overlong holds while preserving the complete teaching unit."

Dev: "For a left/right paired Baduanjin method, can a round include only one
side?"

Domain expert: "No. A paired phase round must include both left and right sides."

Dev: "Should the report be a single huge HTML file?"

Domain expert: "No. It should be a self-contained report directory: opening
`index.html` should load the local original clip, SMPL-X teaching track, and G1
visual track without external artifact roots."

Dev: "Can a final report use schematic G1 evidence?"

Domain expert: "No. A final publishable report should include G1 Model Replay.
Schematic evidence is only a development fallback and must be labeled as such."

Dev: "Should one page load all eight synchronized Baduanjin replays?"

Domain expert: "No. The routine overview page should link to one phase report
page per phase so each page loads only one original clip, one SMPL-X track, and
one G1 Model Replay."
