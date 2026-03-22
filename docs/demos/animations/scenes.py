"""
Manim scenes for tekton-dag demo videos.

Frame: 14.22 wide × 8 tall.  Coordinates x ∈ [-7.11, 7.11], y ∈ [-4, 4].
All element positions are calculated to guarantee no overlap between any
simultaneously-visible objects.  Each placement comment shows the bounding
box [x_min, x_max] × [y_min, y_max].

Timing is driven by Whisper-extracted paragraph timestamps.
"""

from manim import *

# ── Palette ──────────────────────────────────────────────────────────
C_VUE = "#42b883"
C_SPRING = "#6db33f"
C_SPRING_DARK = "#4a7c2e"
C_FLASK = "#3776ab"
C_PHP = "#777bb3"
C_PIPE = "#1a73e8"
C_ORCH = "#f9a825"
C_PR = "#00c853"
C_PROD = "#2979ff"
C_WARN = "#ff5252"
C_NEO4J = "#008cc1"
C_HELM = "#0f1689"
C_BG = "#1e1e2e"
C_HOOK = "#ce93d8"
C_GUI = "#26c6da"


# ── Layout constants ─────────────────────────────────────────────────
# Service-box row (3 boxes, centered horizontally)
SVC_Y = 2.3
SVC_XS = (-4.0, 0.0, 4.0)
SVC_W, SVC_H = 2.2, 0.85
# Each box: center ± (1.1, 0.425)
#   fe:  [-5.1, -2.9] × [1.875, 2.725]
#   bff: [-1.1,  1.1] × [1.875, 2.725]
#   api: [ 2.9,  5.1] × [1.875, 2.725]
# Horizontal gaps between boxes: 1.8 units — plenty of room for arrows.

# Orchestrator position (left of center, below services)
ORCH_X, ORCH_Y = -3.5, 0.0
ORCH_W, ORCH_H = 2.5, 0.85
# Orch: [-4.75, -2.25] × [-0.425, 0.425]

# Pipeline row (below orchestrator)
PIPE_Y = -1.8
PIPE_XS = (-2.0, 1.2, 4.4)
PIPE_W, PIPE_H = 1.9, 0.6
# bootstrap: [-2.95, -1.05] × [-2.10, -1.50]
# PR test:   [ 0.25,  2.15] × [-2.10, -1.50]
# merge:     [ 3.45,  5.35] × [-2.10, -1.50]

# Annotation row (below pipelines)
ANNOT_Y = -2.8


# ── Helpers ──────────────────────────────────────────────────────────

def _box(label, color, w=SVC_W, h=SVC_H, fs=18):
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h,
                         stroke_color=color, fill_color=color, fill_opacity=0.12)
    t = Text(label, font_size=fs, color=color)
    return VGroup(r, t)


def _badge(label, color, fs=13):
    t = Text(label, font_size=fs, color=color)
    r = SurroundingRectangle(t, buff=0.08, color=color, corner_radius=0.06,
                              fill_color=color, fill_opacity=0.08)
    return VGroup(r, t)


def _diamond(label, color, size=0.5, fs=10):
    s = Square(side_length=size, color=color, fill_opacity=0.15).rotate(PI / 4)
    t = Text(label, font_size=fs, color=color)
    return VGroup(s, t)


def _harrow(src, dst, color=WHITE):
    return Arrow(
        src.get_right(), dst.get_left(), buff=0.12, color=color,
        stroke_width=2, max_tip_length_to_length_ratio=0.08,
    )


def _varrow(src, dst, color=WHITE):
    return Arrow(
        src.get_bottom(), dst.get_top(), buff=0.12, color=color,
        stroke_width=2, max_tip_length_to_length_ratio=0.08,
    )


def _wait_until(scene, target, clock):
    gap = target - clock
    if gap > 0.1:
        scene.wait(gap)
    return target


def _svc_row(names, colors, y=SVC_Y, xs=SVC_XS, w=SVC_W, h=SVC_H, fs=16):
    """Create a row of service boxes at calculated positions."""
    boxes = []
    for name, color, x in zip(names, colors, xs):
        b = _box(name, color, w=w, h=h, fs=fs)
        b.move_to(RIGHT * x + UP * y)
        boxes.append(b)
    return boxes


# ═════════════════════════════════════════════════════════════════════
# Scene 1 — Architecture overview
# Audio: 01-architecture.mp3  (160.5 s)
#
# Paragraph timestamps (Whisper):
#   P1   0.0 →   6.8  Welcome to tekton-dag…
#   P2   6.8 →  30.5  Most CI/CD tools treat…
#   P3  30.5 →  46.7  Here is the architecture…
#   P4  46.7 →  70.3  In the center, you see the demo stack…
#   P5  70.3 →  92.9  The system is polyglot…
#   P6  92.9 → 115.4  Below the stack, three pipelines…
#   P7 115.4 → 137.9  Pipelines are also extensible…
#   P8 137.9 → 157.0  A management GUI…
#   P9 157.0 → 160.5  That is the high-level picture…
#
# Y-band plan (simultaneous elements never share a band):
#   [3.5, 3.9]  dag_title
#   [1.9, 2.7]  service boxes + arrows
#   [1.3, 1.7]  role labels
#   [0.7, 1.2]  "downstream" labels / header badge zone
#   [-0.4, 0.4] orchestrator + webhook
#   [-0.8,-0.4] PipelineRun arrow
#   [-2.1,-1.5] pipeline boxes  (appear P6, after polyglot fades)
#   [-1.6,-0.8] polyglot zone   (P5 only, fades before pipelines)
#   [-2.6,-3.2] hooks / extras  (below pipelines)
# ═════════════════════════════════════════════════════════════════════
class StackDAGScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # ── P1  0.0→6.8  Title ──────────────────────────────────────
        title = Text("tekton-dag", font_size=42, color=WHITE)
        sub = Text("Stack-Aware CI/CD with Traffic Interception",
                    font_size=18, color=GREY)
        sub.next_to(title, DOWN, buff=0.35)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=1.5); t += 1.5
        self.play(FadeIn(sub), run_time=1); t += 1
        t = _wait_until(self, 6.0, t)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.6); t += 0.6

        # ── P2  6.8→30.5  DAG: 3 boxes, arrows, roles ──────────────
        dag_title = Text("Directed Acyclic Graph — the core model",
                         font_size=16, color=GREY)
        dag_title.to_edge(UP, buff=0.15)
        # dag_title: center ≈ (0, 3.7), height ≈ 0.22
        # bounds: approx [-3, 3] × [3.59, 3.81]
        self.play(FadeIn(dag_title), run_time=0.5); t += 0.5

        fe, bff, api = _svc_row(
            ["demo-fe\n(Vue)", "BFF\n(Spring Boot)", "demo-api\n(Spring Boot)"],
            [C_VUE, C_SPRING, C_SPRING_DARK],
        )
        self.play(FadeIn(fe), run_time=1); t += 1
        self.play(FadeIn(bff), run_time=1); t += 1
        self.play(FadeIn(api), run_time=1); t += 1

        e1 = _harrow(fe, bff, C_VUE)
        e2 = _harrow(bff, api, C_SPRING)
        self.play(Create(e1), Create(e2), run_time=0.8); t += 0.8

        # Role labels: next_to each box, DOWN, buff=0.20
        # Placed at y ≈ 2.3 - 0.425 - 0.20 - 0.09 ≈ 1.59
        r_orig = Text("originator", font_size=13, color=C_VUE)
        r_orig.next_to(fe, DOWN, buff=0.20)
        r_fwd = Text("forwarder", font_size=13, color=C_SPRING)
        r_fwd.next_to(bff, DOWN, buff=0.20)
        r_term = Text("terminal", font_size=13, color=C_SPRING_DARK)
        r_term.next_to(api, DOWN, buff=0.20)
        self.play(FadeIn(r_orig), FadeIn(r_fwd), FadeIn(r_term), run_time=0.6); t += 0.6
        t = _wait_until(self, 30.5, t)

        # ── P3  30.5→46.7  Orchestrator + webhook ───────────────────
        # Orch at (-3.5, 0.0), 2.5×0.85
        # bounds: [-4.75, -2.25] × [-0.425, 0.425]
        orch = _box("Orchestrator\n(Flask API)", C_ORCH, w=ORCH_W, h=ORCH_H, fs=14)
        orch.move_to(RIGHT * ORCH_X + UP * ORCH_Y)

        # Webhook label to the left of orchestrator
        # center ≈ (-6.2, 0.0), ≈ 0.9w × 0.45h
        # bounds: ≈ [-6.65, -5.75] × [-0.225, 0.225]
        wh_label = Text("GitHub\nwebhook", font_size=12, color=C_ORCH)
        wh_label.next_to(orch, LEFT, buff=0.6)
        wh_arrow = Arrow(
            wh_label.get_right(), orch.get_left(),
            buff=0.1, color=C_ORCH, stroke_width=2.5,
            max_tip_length_to_length_ratio=0.08,
        )

        self.play(FadeIn(orch), run_time=1); t += 1
        self.play(FadeIn(wh_label), Create(wh_arrow), run_time=0.8); t += 0.8

        # "→ PipelineRun" label to the right of orchestrator
        # center ≈ (-0.5, 0.0)
        pr_label = Text("→ PipelineRun", font_size=13, color=C_ORCH)
        pr_label.next_to(orch, RIGHT, buff=0.35)
        self.play(FadeIn(pr_label), run_time=0.6); t += 0.6
        t = _wait_until(self, 46.7, t)

        # ── P4  46.7→70.3  Header badge, highlight boxes ────────────
        # Badge above dag_title would overlap.  Place between services
        # and role labels: y ≈ 3.1 (above boxes).
        header = _badge("x-dev-session: pr-42", C_PR, fs=12)
        header.next_to(bff, UP, buff=0.35)
        # badge center ≈ (0, 3.0), height ≈ 0.3
        # bounds: ≈ [-1.3, 1.3] × [2.85, 3.15]
        # dag_title bottom ≈ 3.59.  Gap: 3.59-3.15 = 0.44 ✓
        # bff top ≈ 2.725.  buff=0.35 → badge bottom ≈ 2.725+0.35 = 3.075. ✓
        self.play(
            fe[0].animate.set_fill(C_VUE, opacity=0.3),
            bff[0].animate.set_fill(C_SPRING, opacity=0.3),
            api[0].animate.set_fill(C_SPRING_DARK, opacity=0.3),
            FadeIn(header),
            run_time=1.5,
        ); t += 1.5
        t = _wait_until(self, 69, t)
        self.play(FadeOut(header), run_time=0.5); t += 0.5

        # ── P5  70.3→92.9  Polyglot — tool badges ───────────────────
        # Place centered, below orch.  Polyglot label at y=-1.0,
        # badges at y=-1.5.  These will fade before pipelines appear.
        poly_lbl = Text("Polyglot: 6 build tools · language version matrix",
                        font_size=14, color=GREY)
        poly_lbl.move_to(DOWN * 1.0)
        # bounds: ≈ [-3.5, 3.5] × [-1.12, -0.88]
        tools = VGroup(
            _badge("npm", C_VUE, 12), _badge("Maven", C_SPRING, 12),
            _badge("Gradle", C_SPRING_DARK, 12), _badge("pip", C_FLASK, 12),
            _badge("Composer", C_PHP, 12), _badge("mirrord", "#ff9100", 12),
        ).arrange(RIGHT, buff=0.30)
        tools.move_to(DOWN * 1.5)
        # badge row: center y=-1.5, height ≈ 0.3
        # bounds: ≈ [-4.5, 4.5] × [-1.65, -1.35]
        # Orch bottom = -0.425.  Gap to poly_lbl top ≈ -0.88 - (-0.425) = 0.455 ✓

        self.play(FadeIn(poly_lbl), run_time=0.5); t += 0.5
        self.play(
            LaggedStart(*[FadeIn(x, shift=UP * 0.15) for x in tools],
                        lag_ratio=0.12),
            run_time=1.8,
        ); t += 1.8
        t = _wait_until(self, 92.0, t)
        self.play(FadeOut(poly_lbl), FadeOut(tools), run_time=0.6); t += 0.6

        # ── P6  92.9→115.4  Three pipelines ─────────────────────────
        # Pipeline boxes at y=-1.8, w=1.9, h=0.6
        # bootstrap: [-2.95, -1.05] × [-2.10, -1.50]
        # PR test:   [ 0.25,  2.15] × [-2.10, -1.50]
        # merge:     [ 3.45,  5.35] × [-2.10, -1.50]
        # Gaps between:  -1.05 to 0.25 = 1.30,  2.15 to 3.45 = 1.30 ✓
        # Orch bottom -0.425 to pipeline top -1.50 = 1.075 gap ✓
        p1 = _box("bootstrap", C_PIPE, w=PIPE_W, h=PIPE_H, fs=15)
        p2 = _box("PR test", C_PIPE, w=PIPE_W, h=PIPE_H, fs=15)
        p3 = _box("merge", C_PIPE, w=PIPE_W, h=PIPE_H, fs=15)
        p1.move_to(RIGHT * PIPE_XS[0] + UP * PIPE_Y)
        p2.move_to(RIGHT * PIPE_XS[1] + UP * PIPE_Y)
        p3.move_to(RIGHT * PIPE_XS[2] + UP * PIPE_Y)

        self.play(FadeIn(p1, shift=UP * 0.15), run_time=0.8); t += 0.8
        t = _wait_until(self, 99, t)
        self.play(FadeIn(p2, shift=UP * 0.15), run_time=0.8); t += 0.8
        t = _wait_until(self, 105, t)
        self.play(FadeIn(p3, shift=UP * 0.15), run_time=0.8); t += 0.8
        t = _wait_until(self, 115.4, t)

        # ── P7  115.4→137.9  Custom hooks ───────────────────────────
        # 4 badges below pipelines, centered at x=1.2 (middle pipe), y=-2.7
        hooks = VGroup(
            _badge("pre-build", C_HOOK, 11),
            _badge("post-build", C_HOOK, 11),
            _badge("pre-test", C_HOOK, 11),
            _badge("post-test", C_HOOK, 11),
        ).arrange(RIGHT, buff=0.20)
        hooks.move_to(RIGHT * 1.2 + UP * ANNOT_Y)
        # bounds: ≈ [-1.5, 3.9] × [-2.95, -2.65]
        # Pipeline bottom = -2.10.  Gap = -2.10 - (-2.65) = 0.55 ✓
        hook_lbl = Text("Custom pipeline hooks (optional)",
                        font_size=11, color=C_HOOK)
        hook_lbl.next_to(hooks, DOWN, buff=0.10)
        # label ≈ y = -3.15.  Frame bottom = -4.0.  ✓
        self.play(FadeIn(hooks), FadeIn(hook_lbl), run_time=1); t += 1
        t = _wait_until(self, 137, t)
        self.play(FadeOut(hooks), FadeOut(hook_lbl), run_time=0.5); t += 0.5

        # ── P8  137.9→157  GUI + Results + Neo4j + Helm ─────────────
        # Same y-band as hooks (they faded out)
        extras = VGroup(
            _badge("Management GUI", C_GUI, 11),
            _badge("Tekton Results", C_PIPE, 11),
            _badge("Neo4j Graph", C_NEO4J, 11),
            _badge("Helm chart", C_HELM, 11),
        ).arrange(RIGHT, buff=0.25)
        extras.move_to(RIGHT * 1.2 + UP * ANNOT_Y)
        self.play(
            LaggedStart(*[FadeIn(e, shift=UP * 0.15) for e in extras],
                        lag_ratio=0.25),
            run_time=2.5,
        ); t += 2.5
        t = _wait_until(self, 160.5, t)


# ═════════════════════════════════════════════════════════════════════
# Scene 2 — Header propagation / bootstrap data flow
# Audio: 03-bootstrap-dataflow.mp3  (108.4 s)
#
#   P1   0.0 →   4.7  Now let's bootstrap…
#   P2   4.7 →  30.3  When we trigger the bootstrap pipeline…
#   P3  30.3 →  56.4  Next, the build-select-tool-apps…
#   P4  56.4 →  63.3  Once all services are running…
#   P5  63.3 →  93.4  The BFF receives the request…
#   P6  93.4 → 108.4  In normal operation…
#
# Layout:
#   [3.0, 3.6]  title (P1 only)
#   [0.6, 1.6]  service boxes (persistent from P2)
#   [-0.1, 0.5] tool/role labels under boxes
#   [-1.0,-0.3] header badge zone (P4-P5)
#   [-2.0,-1.0] trace/build status text
#   [-2.5,-1.8] results text
# ═════════════════════════════════════════════════════════════════════
class HeaderPropagationScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # service boxes at y=1.0 for this scene (more vertical room for trace)
        ROW_Y = 1.0
        fe = _box("demo-fe\n(Vue)", C_VUE, w=2.3, h=0.9, fs=15)
        bff = _box("BFF\n(Spring Boot)", C_SPRING, w=2.3, h=0.9, fs=15)
        api = _box("demo-api\n(Spring Boot)", C_SPRING_DARK, w=2.3, h=0.9, fs=15)
        # fe:  [-5.15, -2.85] × [0.55, 1.45]
        # bff: [-1.15,  1.15] × [0.55, 1.45]
        # api: [ 2.85,  5.15] × [0.55, 1.45]
        fe.move_to(LEFT * 4 + UP * ROW_Y)
        bff.move_to(UP * ROW_Y)
        api.move_to(RIGHT * 4 + UP * ROW_Y)
        e1 = _harrow(fe, bff, GREY_B)
        e2 = _harrow(bff, api, GREY_B)

        # ── P1  0→4.7 ──────────────────────────────────────────────
        intro = Text("Bootstrap & Data Flow", font_size=28, color=WHITE)
        # center (0, 0)
        self.play(FadeIn(intro), run_time=1); t += 1
        t = _wait_until(self, 4.0, t)
        self.play(FadeOut(intro), run_time=0.5); t += 0.5

        # ── P2  4.7→30.3  bootstrap stages ─────────────────────────
        self.play(FadeIn(fe), FadeIn(bff), FadeIn(api), run_time=0.8); t += 0.8
        self.play(Create(e1), Create(e2), run_time=0.6); t += 0.6

        stages = [
            ("resolve-stack → parse DAG", 8),
            ("clone-app-repos → 3 repos", 12),
            ("compile-npm → demo-fe", 16),
            ("compile-maven → BFF, API", 20),
            ("containerize → Kaniko → 3 images", 24),
            ("deploy-full-stack → Running ✓", 27),
        ]
        # Status text at y=-1.5 (well below boxes)
        stage_txt = Text(stages[0][0], font_size=15, color=C_PIPE)
        stage_txt.move_to(DOWN * 1.5)
        self.play(FadeIn(stage_txt), run_time=0.4); t += 0.4

        for label, target_t in stages[1:]:
            t = _wait_until(self, target_t, t)
            new = Text(label, font_size=15, color=C_PIPE).move_to(DOWN * 1.5)
            self.play(Transform(stage_txt, new), run_time=0.4); t += 0.4

        t = _wait_until(self, 30.0, t)
        self.play(FadeOut(stage_txt), run_time=0.3); t += 0.3

        # ── P3  30.3→56.4  Build detail per service ────────────────
        # Tool labels directly below each box
        tl_npm = Text("npm", font_size=12, color=C_VUE)
        tl_npm.next_to(fe, DOWN, buff=0.15)
        tl_mvn1 = Text("maven", font_size=12, color=C_SPRING)
        tl_mvn1.next_to(bff, DOWN, buff=0.15)
        tl_mvn2 = Text("maven", font_size=12, color=C_SPRING_DARK)
        tl_mvn2.next_to(api, DOWN, buff=0.15)
        tl = VGroup(tl_npm, tl_mvn1, tl_mvn2)
        self.play(FadeIn(tl), run_time=0.6); t += 0.6

        # Kaniko note at y=-1.5 (same spot as stages, which faded)
        kaniko = Text("Kaniko → container images → registry",
                      font_size=14, color=GREY).move_to(DOWN * 1.5)
        self.play(FadeIn(kaniko), run_time=0.5); t += 0.5
        t = _wait_until(self, 45, t)

        deployed = Text("All 3 pods Running ✓", font_size=16, color=C_PR)
        deployed.move_to(DOWN * 1.5)
        self.play(Transform(kaniko, deployed), run_time=0.5); t += 0.5
        self.play(
            fe[0].animate.set_fill(C_VUE, opacity=0.3),
            bff[0].animate.set_fill(C_SPRING, opacity=0.3),
            api[0].animate.set_fill(C_SPRING_DARK, opacity=0.3),
            run_time=0.6,
        ); t += 0.6
        t = _wait_until(self, 55, t)
        self.play(FadeOut(kaniko), FadeOut(tl), run_time=0.4); t += 0.4

        # ── P4  56.4→63.3  Trace setup ─────────────────────────────
        t = _wait_until(self, 56.4, t)
        trace_lbl = Text("Tracing a request through the stack",
                         font_size=15, color=WHITE)
        trace_lbl.to_edge(UP, buff=0.25)
        # y ≈ 3.65, well above boxes (top 1.45)
        self.play(FadeIn(trace_lbl), run_time=0.5); t += 0.5

        dot = Dot(color=C_PR, radius=0.12).move_to(LEFT * 6.5 + UP * ROW_Y)
        self.play(FadeIn(dot), run_time=0.3); t += 0.3
        self.play(dot.animate.move_to(fe.get_center()), run_time=0.8); t += 0.8

        # Header badge above the row, between boxes and trace_lbl
        # Place at y = 2.0 (box top 1.45 + 0.55)
        header = _badge("x-dev-session: pr-42", C_PR, fs=12)
        header.move_to(UP * 2.2)
        # bounds: ≈ [-1.3, 1.3] × [2.05, 2.35]
        # box top 1.45, gap 0.60.  trace_lbl bottom ≈ 3.55, gap 1.20. ✓

        orig = Text("originator — sets header", font_size=12, color=C_VUE)
        orig.next_to(fe, DOWN, buff=0.15)
        # y ≈ 0.25.  Below box bottom 0.55 with 0.15 buff.
        self.play(FadeIn(header), FadeIn(orig), run_time=0.6); t += 0.6
        t = _wait_until(self, 63.3, t)

        # ── P5  63.3→93.4  Forwarder → terminal ────────────────────
        self.play(
            dot.animate.move_to(bff.get_center()),
            header.animate.move_to(UP * 2.2),
            run_time=1,
        ); t += 1

        fwd = Text("forwarder — reads & propagates", font_size=12, color=C_SPRING)
        fwd.next_to(bff, DOWN, buff=0.15)
        self.play(FadeIn(fwd), bff[0].animate.set_fill(C_SPRING, opacity=0.5),
                  run_time=0.5); t += 0.5
        t = _wait_until(self, 78, t)

        self.play(
            dot.animate.move_to(api.get_center()),
            run_time=1,
        ); t += 1

        term = Text("terminal — header arrived ✓", font_size=12, color=GREEN)
        term.next_to(api, DOWN, buff=0.15)
        self.play(FadeIn(term), api[0].animate.set_fill(GREEN, opacity=0.3),
                  run_time=0.5); t += 0.5
        t = _wait_until(self, 93.4, t)

        # ── P6  93.4→108.4  Normal vs PR ───────────────────────────
        self.play(
            FadeOut(trace_lbl), FadeOut(dot), FadeOut(header),
            FadeOut(orig), FadeOut(fwd), FadeOut(term),
            run_time=0.5,
        ); t += 0.5

        normal = Text("Without header → standard production deployment",
                       font_size=14, color=C_PROD).move_to(DOWN * 1.2)
        self.play(FadeIn(normal), run_time=0.5); t += 0.5
        t = _wait_until(self, 100, t)

        pr = Text("With header → PR build receives tagged traffic only",
                   font_size=14, color=C_PR)
        pr.next_to(normal, DOWN, buff=0.25)
        # y ≈ -1.65, gap from normal bottom (-1.35) = 0.25+ buff ✓
        self.play(FadeIn(pr), run_time=0.5); t += 0.5
        t = _wait_until(self, 108.4, t)


# ═════════════════════════════════════════════════════════════════════
# Scene 3 — Intercept routing
# Audio: 05-intercept-routing.mp3  (123.6 s)
#
#   P1   0.0 →   4.9  Let's visualize…
#   P2   4.9 →  15.8  On screen you see…
#   P3  15.8 →  30.0  The blue request…
#   P4  30.0 →  57.2  Now watch the green request…
#   P5  57.2 →  78.6  The key insight…
#   P6  78.6 →  99.7  The validate-propagation task…
#   P7  99.7 → 119.4  The intercept mechanism supports…
#   P8 119.4 → 123.6  Same URL, same infrastructure…
#
# Layout:
#   [2.9, 3.5]  title zone
#   [1.6, 2.6]  service boxes (fe, bff, api_prod)
#   [-0.2, 0.6] PR pod
#   [-1.5,-0.5] validation / coexist text
#   [-2.5,-1.8] legend / multi-PR badges
# ═════════════════════════════════════════════════════════════════════
class InterceptRoutingScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        ROW_Y = 2.1
        # Boxes at y=2.1
        fe = _box("demo-fe", C_VUE, w=1.9, h=0.7, fs=16)
        bff = _box("BFF", C_SPRING, w=1.9, h=0.7, fs=16)
        api = _box("demo-api\n(prod)", C_SPRING_DARK, w=2.0, h=0.8, fs=14)
        fe.move_to(LEFT * 4 + UP * ROW_Y)
        bff.move_to(UP * ROW_Y)
        api.move_to(RIGHT * 4 + UP * ROW_Y)
        # fe:  [-4.95, -3.05] × [1.75, 2.45]
        # bff: [-0.95,  0.95] × [1.75, 2.45]
        # api: [ 3.00,  5.00] × [1.70, 2.50]
        e1 = _harrow(fe, bff, GREY_B)
        e2 = _harrow(bff, api, GREY_B)

        # PR pod well below the main row
        pr_pod = _box("demo-api\n(PR-42)", C_PR, w=2.0, h=0.8, fs=14)
        pr_pod.move_to(RIGHT * 4 + DOWN * 0.5)
        # pr_pod: [3.0, 5.0] × [-0.90, -0.10]
        # Gap from api bottom (1.70) to pr_pod top (-0.10) = 1.80 ✓

        # ── P1  0→4.9 ──────────────────────────────────────────────
        title = Text("Intercept Routing: PR vs Normal", font_size=26, color=WHITE)
        self.play(FadeIn(title), run_time=1); t += 1
        t = _wait_until(self, 4.2, t)
        self.play(FadeOut(title), run_time=0.5); t += 0.5

        # ── P2  4.9→15.8  Layout ───────────────────────────────────
        self.play(FadeIn(fe), FadeIn(bff), FadeIn(api), run_time=0.6); t += 0.6
        self.play(Create(e1), Create(e2), run_time=0.5); t += 0.5
        self.play(FadeIn(pr_pod), run_time=0.6); t += 0.6

        # Legend at bottom-left, y=-2.5
        leg_blue = VGroup(
            Dot(color=C_PROD, radius=0.06),
            Text("Normal (no header)", font_size=10, color=C_PROD),
        ).arrange(RIGHT, buff=0.08)
        leg_green = VGroup(
            Dot(color=C_PR, radius=0.06),
            Text("PR (x-dev-session: pr-42)", font_size=10, color=C_PR),
        ).arrange(RIGHT, buff=0.08)
        legend = VGroup(leg_blue, leg_green).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        legend.move_to(LEFT * 4.5 + DOWN * 2.5)
        self.play(FadeIn(legend), run_time=0.5); t += 0.5
        t = _wait_until(self, 15.8, t)

        # ── P3  15.8→30.0  Blue dot → production path ──────────────
        blue = Dot(color=C_PROD, radius=0.12).move_to(LEFT * 6.5 + UP * ROW_Y)
        self.play(FadeIn(blue), run_time=0.3); t += 0.3
        for target in [fe, bff, api]:
            self.play(blue.animate.move_to(target.get_center()), run_time=0.8); t += 0.8
            self.wait(0.4); t += 0.4

        prod_ok = Text("→ production ✓", font_size=12, color=C_PROD)
        prod_ok.next_to(api, RIGHT, buff=0.20)
        self.play(FadeIn(prod_ok), run_time=0.3); t += 0.3
        t = _wait_until(self, 30.0, t)

        # ── P4  30.0→57.2  Green dot → PR pod ──────────────────────
        green = Dot(color=C_PR, radius=0.12).move_to(LEFT * 6.5 + UP * 0.8)
        hdr = _badge("x-dev-session: pr-42", C_PR, fs=10)
        hdr.next_to(green, DOWN, buff=0.15)
        self.play(FadeIn(green), FadeIn(hdr), run_time=0.3); t += 0.3

        for target in [fe, bff]:
            self.play(
                green.animate.move_to(target.get_center() + DOWN * 0.15),
                hdr.animate.next_to(target, DOWN, buff=0.55),
                run_time=0.8,
            ); t += 0.8
            self.wait(0.8); t += 0.8

        # Branch arrow from bff bottom to PR pod left
        branch = Arrow(
            bff.get_bottom(), pr_pod.get_left(),
            buff=0.12, color=C_PR, stroke_width=3,
            max_tip_length_to_length_ratio=0.06,
        )
        int_lbl = Text("header match →\nroute to PR pod", font_size=11, color=C_PR)
        int_lbl.next_to(branch, LEFT, buff=0.12)
        # int_lbl is to the left of the diagonal arrow,
        # roughly at x ≈ 0-2 = -2, y ≈ 0.5 — clear of boxes ✓
        self.play(Create(branch), FadeIn(int_lbl), run_time=0.8); t += 0.8
        self.wait(1.2); t += 1.2

        self.play(
            green.animate.move_to(pr_pod.get_center()),
            hdr.animate.next_to(pr_pod, DOWN, buff=0.20),
            run_time=0.8,
        ); t += 0.8
        pr_ok = Text("→ PR build ✓", font_size=12, color=C_PR)
        pr_ok.next_to(pr_pod, RIGHT, buff=0.20)
        self.play(FadeIn(pr_ok), run_time=0.3); t += 0.3
        t = _wait_until(self, 57.2, t)

        # ── P5  57.2→78.6  Coexist ─────────────────────────────────
        coexist = Text("Same cluster · Same DNS · Same ingress",
                       font_size=16, color=WHITE).move_to(DOWN * 2.0)
        sub_co = Text("Only the header differs", font_size=12, color=GREY)
        sub_co.next_to(coexist, DOWN, buff=0.15)
        # y ≈ -2.0 to -2.45.  Legend at y=-2.5 — could be close.
        # Move legend down to -3.0 to make room.
        self.play(
            legend.animate.move_to(LEFT * 4.5 + DOWN * 3.2),
            FadeIn(coexist), FadeIn(sub_co),
            run_time=0.6,
        ); t += 0.6
        t = _wait_until(self, 78.6, t)

        # ── P6  78.6→99.7  Validation ──────────────────────────────
        self.play(FadeOut(coexist), FadeOut(sub_co), run_time=0.3); t += 0.3
        v1 = Text("✓ validate-propagation — header reaches PR pod",
                   font_size=12, color=C_PR).move_to(DOWN * 2.0)
        self.play(FadeIn(v1), run_time=0.5); t += 0.5
        t = _wait_until(self, 88, t)
        v2 = Text("✓ validate-original-traffic — production unaffected",
                   font_size=12, color=C_PROD)
        v2.next_to(v1, DOWN, buff=0.20)
        self.play(FadeIn(v2), run_time=0.5); t += 0.5
        t = _wait_until(self, 99.7, t)

        # ── P7  99.7→119.4  Multi-PR ───────────────────────────────
        self.play(FadeOut(v1), FadeOut(v2), run_time=0.3); t += 0.3
        multi = VGroup(
            _badge("PR-42", C_PR, 12),
            _badge("PR-43", "#ffab00", 12),
            _badge("PR-44", "#e040fb", 12),
        ).arrange(RIGHT, buff=0.40)
        multi.move_to(DOWN * 2.0)
        ml = Text("Concurrent PRs — isolated by header value",
                   font_size=12, color=GREY)
        ml.next_to(multi, DOWN, buff=0.15)
        self.play(
            LaggedStart(*[FadeIn(m) for m in multi], lag_ratio=0.25),
            run_time=1,
        ); t += 1
        self.play(FadeIn(ml), run_time=0.3); t += 0.3
        t = _wait_until(self, 112, t)
        cl = Text("Cleanup: finally block → pods + intercepts removed",
                   font_size=11, color=GREY)
        cl.next_to(ml, DOWN, buff=0.12)
        self.play(FadeIn(cl), run_time=0.3); t += 0.3
        t = _wait_until(self, 119.4, t)

        # ── P8  119.4→123.6  Summary ───────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5); t += 0.5
        s = Text("Same URL · Same infra · Different backend",
                  font_size=22, color=WHITE)
        self.play(FadeIn(s), run_time=0.6); t += 0.6
        t = _wait_until(self, 123.6, t)


# ═════════════════════════════════════════════════════════════════════
# Scene 4 — Local debug with mirrord
# Audio: 06-local-debug.mp3  (117.2 s)
#
#   P1   0.0 →  16.6  What happens when a test fails…
#   P2  16.6 →  33.0  tekton-dag includes a mirrord build image…
#   P3  33.0 →  48.5  When you run mirrord exec…
#   P4  48.5 →  68.1  Watch — a request enters…
#   P5  68.1 →  86.3  This is not a mock…
#   P6  86.3 →  99.1  The pipeline even supports this…
#   P7  99.1 → 108.8  When you are done debugging…
#   P8 108.8 → 117.2  Local IDE. Live cluster data…
#
# Layout (split view):
#   x ∈ [-7, -0.5]  Developer Laptop
#   x ∈ [ 0.5,  7]  Kubernetes Cluster
#   x = 0            divider line
# ═════════════════════════════════════════════════════════════════════
class LocalDebugScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # ── P1  0→16.6  Title ──────────────────────────────────────
        title = Text("Local Debugging with mirrord", font_size=28, color=WHITE)
        sub = Text("IDE breakpoints · Live cluster data · No mocks",
                    font_size=14, color=GREY)
        sub.next_to(title, DOWN, buff=0.30)
        self.play(FadeIn(title), run_time=1); t += 1
        self.play(FadeIn(sub), run_time=0.5); t += 0.5
        t = _wait_until(self, 15.6, t)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.8); t += 0.8

        # ── P2  16.6→33.0  Split layout ────────────────────────────
        div = DashedLine(UP * 3.5, DOWN * 3.5, color=GREY_B, dash_length=0.1)
        self.play(Create(div), run_time=0.3); t += 0.3

        ll = Text("Developer Laptop", font_size=13, color=GREY).move_to(LEFT * 3.8 + UP * 3.5)
        cl = Text("Kubernetes Cluster", font_size=13, color=GREY).move_to(RIGHT * 3.8 + UP * 3.5)
        self.play(FadeIn(ll), FadeIn(cl), run_time=0.3); t += 0.3

        # IDE box: left half, center (-3.8, 1.0), 2.8×1.2
        # bounds: [-5.2, -2.4] × [0.4, 1.6]
        ide = _box("IDE\n(breakpoint\nready)", "#e91e63", w=2.8, h=1.2, fs=14)
        ide.move_to(LEFT * 3.8 + UP * 1.0)
        self.play(FadeIn(ide), run_time=0.6); t += 0.6

        # Cluster pods: right half, stacked vertically
        # fp: (3.8, 2.2), 1.8×0.5  → [2.9, 4.7] × [1.95, 2.45]
        # bp: (3.8, 1.2), 1.8×0.5  → [2.9, 4.7] × [0.95, 1.45]
        # ap: (3.8, 0.2), 1.8×0.5  → [2.9, 4.7] × [-0.05, 0.45]
        fp = _box("demo-fe", C_VUE, w=1.8, h=0.5, fs=12)
        bp = _box("BFF", C_SPRING, w=1.8, h=0.5, fs=12)
        ap = _box("demo-api", C_SPRING_DARK, w=1.8, h=0.5, fs=12)
        fp.move_to(RIGHT * 3.8 + UP * 2.2)
        bp.move_to(RIGHT * 3.8 + UP * 1.2)
        ap.move_to(RIGHT * 3.8 + UP * 0.2)
        self.play(FadeIn(fp), FadeIn(bp), FadeIn(ap), run_time=0.5); t += 0.5

        pod_arr = VGroup(_varrow(fp, bp, GREY_B), _varrow(bp, ap, GREY_B))
        self.play(Create(pod_arr), run_time=0.4); t += 0.4
        t = _wait_until(self, 33.0, t)

        # ── P3  33.0→48.5  mirrord tunnel ──────────────────────────
        # Arrow from ap left to ide right, crossing the divider
        tunnel = Arrow(
            ap.get_left(), ide.get_right(),
            buff=0.15, color="#ff9100", stroke_width=3.5,
            max_tip_length_to_length_ratio=0.05,
        )
        tl = Text("mirrord tunnel", font_size=12, color="#ff9100")
        tl.next_to(tunnel, DOWN, buff=0.10)
        self.play(Create(tunnel), run_time=1); t += 1
        self.play(FadeIn(tl), run_time=0.3); t += 0.3
        t = _wait_until(self, 48.5, t)

        # ── P4  48.5→68.1  Request trace + breakpoint ──────────────
        req = Dot(color=C_PR, radius=0.10).move_to(RIGHT * 6.5 + UP * 2.2)
        self.play(FadeIn(req), run_time=0.2); t += 0.2
        for pod in [fp, bp, ap]:
            self.play(req.animate.move_to(pod.get_center()), run_time=0.5); t += 0.5

        # Redirect to IDE
        redir = Text("mirrord → redirect", font_size=10, color="#ff9100")
        redir.move_to(DOWN * 0.8)
        self.play(FadeIn(redir), run_time=0.2); t += 0.2
        self.play(req.animate.move_to(ide.get_center()), run_time=1); t += 1

        bpf = Text("● BREAKPOINT HIT", font_size=18, color="#ff1744")
        bpf.next_to(ide, DOWN, buff=0.30)
        # ide bottom = 0.4, bpf top ≈ 0.4 - 0.30 = 0.10.
        # ap center at y=0.2, bottom -0.05.  bpf at x=-3.8, ap at x=3.8 → no overlap ✓
        self.play(
            FadeIn(bpf, scale=1.2),
            Flash(ide.get_center(), color="#ff1744"),
            run_time=0.5,
        ); t += 0.5
        self.wait(0.8); t += 0.8

        # Debug variables in left panel, below breakpoint text
        vp = VGroup(
            Text("headers['x-dev-session'] = 'pr-42'", font_size=10, color=C_PR),
            Text("request.path = '/api/orders'", font_size=10, color=WHITE),
            Text("downstream.status = 200", font_size=10, color=GREEN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.05)
        vp.next_to(bpf, DOWN, buff=0.20)
        # bpf at y ≈ -0.10, vp at y ≈ -0.55.  On left half (x≈-3.8). ✓
        self.play(FadeIn(vp), run_time=0.6); t += 0.6
        t = _wait_until(self, 68.1, t)

        # ── P5  68.1→86.3  Real data emphasis ──────────────────────
        self.play(FadeOut(redir), run_time=0.2); t += 0.2
        real = Text("Real requests · Real headers · Real downstream calls",
                     font_size=14, color=WHITE)
        real.move_to(DOWN * 2.5)
        self.play(FadeIn(real), run_time=0.5); t += 0.5
        t = _wait_until(self, 86.3, t)

        # ── P6  86.3→99.1  PR support ──────────────────────────────
        pr_note = Text("Works during PR pipeline — attach to intercept pod",
                       font_size=12, color=C_PR).move_to(DOWN * 2.5)
        self.play(Transform(real, pr_note), run_time=0.4); t += 0.4
        t = _wait_until(self, 99.1, t)

        # ── P7  99.1→108.8  Cleanup ────────────────────────────────
        clean = Text("Disconnect → traffic returns to pod · No artifacts",
                     font_size=12, color=GREY).move_to(DOWN * 2.5)
        self.play(Transform(real, clean), run_time=0.4); t += 0.4
        self.play(FadeOut(tunnel), FadeOut(tl), FadeOut(req), run_time=0.6); t += 0.6
        t = _wait_until(self, 108.8, t)

        # ── P8  108.8→117.2  Summary ───────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5); t += 0.5
        s = Text("Local IDE · Live cluster · Full breakpoint debugging",
                  font_size=20, color=WHITE)
        self.play(FadeIn(s), run_time=0.6); t += 0.6
        t = _wait_until(self, 117.2, t)


# ═════════════════════════════════════════════════════════════════════
# Scene 5 — Multi-team Helm
# Audio: 08-multi-team-helm.mp3  (123.7 s)
#
# (Proportional estimates — Whisper matching failed for this segment)
#   P1   0.0 →   8.0  tekton-dag is designed for multi-team…
#   P2   8.0 →  28.0  We start with a single team…
#   P3  28.0 →  45.0  Now imagine three teams…
#   P4  45.0 →  72.0  The values.yaml exposes…
#   P5  72.0 →  95.0  Teams can also inject…
#   P6  95.0 → 106.0  The management GUI…
#   P7 106.0 → 118.0  Watch as a webhook fires…
#   P8 118.0 → 123.7  One chart, multiple releases…
#
# Layout:
#   [2.0, 3.5]  team bubbles row
#   [0.0, 1.5]  details / labels
#   [-1.5, 0.0] config badges / hooks
#   [-2.5,-1.5] GUI / webhook info
# ═════════════════════════════════════════════════════════════════════
class MultiTeamScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # ── P1  0→8  Title ──────────────────────────────────────────
        title = Text("Multi-Team Helm Deployment", font_size=28, color=WHITE)
        self.play(FadeIn(title), run_time=1); t += 1
        t = _wait_until(self, 7, t)
        self.play(FadeOut(title), run_time=0.7); t += 0.7

        # ── P2  8→28  Single team ───────────────────────────────────
        # Team bubble: 2.6w × 1.4h, center (0, 1.5)
        # bounds: [-1.3, 1.3] × [0.8, 2.2]
        ta = self._team("team-alpha", C_VUE)
        ta.move_to(UP * 1.5)
        self.play(FadeIn(ta), run_time=1); t += 1

        # Details below the bubble at y=-0.2 (bubble bottom 0.8, gap 1.0)
        det = VGroup(
            Text("Orchestrator deployed", font_size=11, color=GREY),
            Text("Tasks + Pipelines applied", font_size=11, color=GREY),
            Text("ConfigMaps for stacks + teams", font_size=11, color=GREY),
            Text("Optional build-cache PVC", font_size=11, color=GREY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        det.move_to(DOWN * 0.5)
        self.play(
            LaggedStart(*[FadeIn(d) for d in det], lag_ratio=0.35),
            run_time=2.5,
        ); t += 2.5
        t = _wait_until(self, 28, t)

        # ── P3  28→45  Scale to 3 teams ─────────────────────────────
        self.play(FadeOut(det), run_time=0.3); t += 0.3

        # Three bubbles in a row at y=1.5, x = -4, 0, 4
        # Each 2.6w × 1.4h
        # alpha: [-5.3, -2.7] × [0.8, 2.2]
        # beta:  [-1.3,  1.3] × [0.8, 2.2]
        # gamma: [ 2.7,  5.3] × [0.8, 2.2]
        # Gaps: -2.7 to -1.3 = 1.4, 1.3 to 2.7 = 1.4 ✓
        ta2 = self._team("team-alpha", C_VUE)
        tb = self._team("team-beta", C_SPRING)
        tc = self._team("team-gamma", C_FLASK)
        ta2.move_to(LEFT * 4 + UP * 1.5)
        tb.move_to(UP * 1.5)
        tc.move_to(RIGHT * 4 + UP * 1.5)
        self.play(Transform(ta, ta2), FadeIn(tb), FadeIn(tc), run_time=1); t += 1

        iso = Text("Each team → own Helm release, ConfigMaps, orchestrator",
                    font_size=12, color=GREY).move_to(DOWN * 0.3)
        # y=-0.3, bubble bottom 0.8, gap 1.1 ✓
        self.play(FadeIn(iso), run_time=0.5); t += 0.5
        t = _wait_until(self, 45, t)

        # ── P4  45→72  values.yaml knobs ─────────────────────────────
        self.play(FadeOut(iso), run_time=0.3); t += 0.3

        kt = Text("values.yaml — per-team config", font_size=13, color=WHITE)
        kt.move_to(DOWN * 0.3)
        knobs = VGroup(
            _badge("imageRegistry", C_PIPE, 11),
            _badge("interceptBackend", "#ff9100", 11),
            _badge("compileImages", C_SPRING, 11),
            _badge("compileImageVariants", C_PR, 11),
        ).arrange(DOWN, buff=0.12)
        knobs.next_to(kt, DOWN, buff=0.20)
        # kt at y=-0.3, knobs center ≈ y=-1.2
        # bubble bottom at 0.8, kt top ≈ -0.15 → gap 0.95 ✓
        self.play(FadeIn(kt), run_time=0.3); t += 0.3
        self.play(
            LaggedStart(*[FadeIn(k, shift=RIGHT * 0.15) for k in knobs],
                        lag_ratio=0.25),
            run_time=1.5,
        ); t += 1.5

        vd = Text("team-beta: Java 17  |  team-alpha: Java 21",
                   font_size=10, color=GREY)
        vd.next_to(knobs, DOWN, buff=0.12)
        self.play(FadeIn(vd), run_time=0.4); t += 0.4
        t = _wait_until(self, 72, t)

        # ── P5  72→95  Custom hooks ─────────────────────────────────
        self.play(FadeOut(knobs), FadeOut(kt), FadeOut(vd), run_time=0.3); t += 0.3

        ht = Text("Custom hooks — no fork needed", font_size=13, color=C_HOOK)
        ht.move_to(DOWN * 0.3)
        hooks = VGroup(
            _badge("pre-build", C_HOOK, 11),
            _badge("post-build", C_HOOK, 11),
            _badge("pre-test", C_HOOK, 11),
            _badge("post-test", C_HOOK, 11),
        ).arrange(RIGHT, buff=0.20)
        hooks.next_to(ht, DOWN, buff=0.20)
        # hooks center ≈ y=-0.8.  Bubble bottom 0.8, gap 1.6 ✓
        ex = Text("image-scan after build · Slack after test",
                   font_size=10, color=GREY)
        ex.next_to(hooks, DOWN, buff=0.10)
        self.play(FadeIn(ht), FadeIn(hooks), run_time=0.6); t += 0.6
        self.play(FadeIn(ex), run_time=0.3); t += 0.3
        t = _wait_until(self, 95, t)

        # ── P6  95→106  Management GUI ──────────────────────────────
        self.play(FadeOut(hooks), FadeOut(ht), FadeOut(ex), run_time=0.3); t += 0.3

        gui = _box("Management GUI (Vue + Flask)", C_GUI, w=3.5, h=0.7, fs=13)
        gui.move_to(DOWN * 0.5)
        gf = Text("Team switcher · DAG viz · Pipeline monitor",
                   font_size=10, color=GREY)
        gf.next_to(gui, DOWN, buff=0.12)
        self.play(FadeIn(gui), FadeIn(gf), run_time=0.6); t += 0.6
        t = _wait_until(self, 106, t)

        # ── P7  106→118  Webhook isolation ──────────────────────────
        self.play(FadeOut(gui), FadeOut(gf), run_time=0.3); t += 0.3

        # Webhook arrow from left edge to team-beta bubble
        wh = Arrow(
            LEFT * 6.5 + DOWN * 0.5, tb.get_bottom(),
            buff=0.12, color=C_ORCH, stroke_width=3,
            max_tip_length_to_length_ratio=0.05,
        )
        wl = Text("webhook → team-beta only", font_size=12, color=C_ORCH)
        wl.move_to(DOWN * 0.5)
        self.play(Create(wh), FadeIn(wl), run_time=0.6); t += 0.6
        self.play(tb[0].animate.set_fill(C_SPRING, opacity=0.5), run_time=0.4); t += 0.4

        ud = Text("alpha + gamma undisturbed", font_size=10, color=GREY)
        ud.next_to(wl, DOWN, buff=0.12)
        self.play(FadeIn(ud), run_time=0.3); t += 0.3
        t = _wait_until(self, 118, t)

        # ── P8  118→123.7  Summary ──────────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5); t += 0.5
        s = Text("One chart · Multiple releases · Full team isolation",
                  font_size=22, color=WHITE)
        self.play(FadeIn(s), run_time=0.6); t += 0.6
        t = _wait_until(self, 123.7, t)

    def _team(self, name, color):
        b = RoundedRectangle(corner_radius=0.2, width=2.6, height=1.4,
                             stroke_color=color, fill_color=color, fill_opacity=0.08)
        label = Text(name, font_size=13, color=color)
        label.move_to(b.get_top() + DOWN * 0.25)
        dots = VGroup(*[
            Dot(radius=0.05, color=color).shift(LEFT * 0.25 * (i - 1))
            for i in range(3)
        ])
        dots.next_to(label, DOWN, buff=0.15)
        apps = Text("3 apps", font_size=9, color=GREY)
        apps.next_to(dots, DOWN, buff=0.06)
        return VGroup(b, label, dots, apps)


# ═════════════════════════════════════════════════════════════════════
# Scene 6 — Blast-radius test selection
# Audio: 11-test-trace-graph.mp3  (123.2 s)
#
#   P1   0.0 →   8.3  The final piece of the puzzle…
#   P2   8.3 →  30.7  tekton-dag maintains a test-trace graph…
#   P3  30.7 →  49.0  Here is how the graph gets populated…
#   P4  49.0 →  61.9  Now watch what happens…
#   P5  61.9 →  75.6  At radius one…
#   P6  75.6 →  92.1  At radius two…
#   P7  92.1 → 104.2  The graph also identifies gaps…
#   P8 104.2 → 118.8  The run-tests task…
#   P9 118.8 → 123.2  Stack graph query…
#
# Layout:
#   [3.0, 3.8]  scene title
#   [1.0, 2.5]  service circles (3) + CALLS arrows
#   [-0.5, 0.5] TOUCHES lines zone
#   [-1.5,-0.5] test diamonds row
#   [-2.5,-1.8] annotation text
# ═════════════════════════════════════════════════════════════════════
class BlastRadiusScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # ── P1  0→8.3  Title ───────────────────────────────────────
        title = Text("Blast-Radius Test Selection", font_size=28, color=WHITE)
        sub = Text("Neo4j graph → intelligent test targeting",
                    font_size=14, color=GREY)
        sub.next_to(title, DOWN, buff=0.25)
        self.play(FadeIn(title), FadeIn(sub), run_time=1); t += 1
        t = _wait_until(self, 7.5, t)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.5); t += 0.5

        # ── P2  8.3→30.7  Build the graph ──────────────────────────
        gt = Text("Neo4j Test-Trace Graph", font_size=14, color=C_NEO4J)
        gt.to_edge(UP, buff=0.20)
        # gt at y ≈ 3.65
        self.play(FadeIn(gt), run_time=0.3); t += 0.3

        # Service circles at y=2.0, r=0.40
        # sf: center (-4, 2.0) → bounds [-4.4, -3.6] × [1.60, 2.40]
        # sb: center ( 0, 2.0) → bounds [-0.4,  0.4] × [1.60, 2.40]
        # sa: center ( 4, 2.0) → bounds [ 3.6,  4.4] × [1.60, 2.40]
        SVC_R = 0.40
        sf = self._svc_circle("demo-fe", C_VUE, LEFT * 4 + UP * 2.0, SVC_R)
        sb = self._svc_circle("BFF", C_SPRING, UP * 2.0, SVC_R)
        sa = self._svc_circle("demo-api", C_SPRING_DARK, RIGHT * 4 + UP * 2.0, SVC_R)
        self.play(FadeIn(sf), FadeIn(sb), FadeIn(sa), run_time=0.8); t += 0.8

        # CALLS arrows between circles, at y=2.0
        c1 = Arrow(sf.get_right(), sb.get_left(), buff=0.10, color=GREY_B,
                    stroke_width=2, max_tip_length_to_length_ratio=0.06)
        c2 = Arrow(sb.get_right(), sa.get_left(), buff=0.10, color=GREY_B,
                    stroke_width=2, max_tip_length_to_length_ratio=0.06)
        cl1 = Text("CALLS", font_size=8, color=GREY_B)
        cl1.next_to(c1, UP, buff=0.04)
        cl2 = Text("CALLS", font_size=8, color=GREY_B)
        cl2.next_to(c2, UP, buff=0.04)
        self.play(Create(c1), Create(c2), FadeIn(cl1), FadeIn(cl2), run_time=0.6); t += 0.6

        # Test diamonds at y=-1.0
        # 7 diamonds spread across x from -5 to 5
        # Each diamond: ≈ 0.7w × 0.7h (rotated square 0.5 + text)
        # Positions: -5.0, -3.3, -1.6, 0, 1.6, 3.3, 5.0
        T_Y = -1.0
        t_xs = [-5.0, -3.3, -1.6, 0.0, 1.6, 3.3, 5.0]
        t_names = ["fe-e2e", "fe-post", "bff-post", "bff-intg",
                    "api-post", "api-intg", "api-load"]
        t_colors = [C_VUE, C_VUE, C_SPRING, C_SPRING,
                    C_SPRING_DARK, C_SPRING_DARK, C_SPRING_DARK]
        t_parents = [sf, sf, sb, sb, sa, sa, sa]

        tests = []
        for nm, x, col in zip(t_names, t_xs, t_colors):
            d = _diamond(nm, col, size=0.45, fs=9)
            d.move_to(RIGHT * x + UP * T_Y)
            tests.append(d)

        self.play(
            LaggedStart(*[FadeIn(x) for x in tests], lag_ratio=0.08),
            run_time=1.5,
        ); t += 1.5

        # TOUCHES lines: from each test diamond top to its parent circle bottom
        touches = []
        for test, parent, col in zip(tests, t_parents, t_colors):
            line = DashedLine(
                test.get_top(), parent.get_bottom(),
                color=col, dash_length=0.05, stroke_width=1.5,
            )
            touches.append(line)
        self.play(*[Create(l) for l in touches], run_time=0.8); t += 0.8
        t = _wait_until(self, 30.7, t)

        # ── P3  30.7→49.0  Ingestion ───────────────────────────────
        ingest = Text(
            "Traces ingested via /api/graph/ingest → graph builds over time",
            font_size=11, color=GREY,
        ).move_to(DOWN * 2.5)
        # y=-2.5, test bottom ≈ -1.35, gap 1.15 ✓
        self.play(FadeIn(ingest), run_time=0.4); t += 0.4
        t = _wait_until(self, 49.0, t)

        # ── P4  49.0→61.9  Changed service ─────────────────────────
        self.play(FadeOut(ingest), run_time=0.3); t += 0.3
        ch = Text("Changed: demo-api", font_size=14, color=C_WARN)
        ch.next_to(sa, UP, buff=0.20)
        # ch at y ≈ 2.60, gt at y ≈ 3.65, gap 1.05 ✓
        self.play(
            sa[0].animate.set_fill(C_WARN, opacity=0.5).set_stroke(C_WARN, width=3),
            FadeIn(ch),
            run_time=0.6,
        ); t += 0.6
        t = _wait_until(self, 61.9, t)

        # ── P5  61.9→75.6  Radius 1 ────────────────────────────────
        r_txt = Text("Radius 1 → 3 direct tests", font_size=13, color=C_PR)
        r_txt.move_to(DOWN * 2.5)
        self.play(FadeIn(r_txt), run_time=0.3); t += 0.3
        for x in tests[4:]:
            self.play(x[0].animate.set_fill(C_PR, opacity=0.5), run_time=0.25); t += 0.25
        for l in touches[4:]:
            self.play(l.animate.set_color(C_PR).set_stroke(width=2.5), run_time=0.15); t += 0.15
        t = _wait_until(self, 75.6, t)

        # ── P6  75.6→92.1  Radius 2 ────────────────────────────────
        r2_txt = Text("Radius 2 → +2 BFF tests (neighbor)", font_size=13, color=C_ORCH)
        r2_txt.move_to(DOWN * 2.5)
        self.play(Transform(r_txt, r2_txt), run_time=0.3); t += 0.3
        self.play(
            sb[0].animate.set_fill(C_ORCH, opacity=0.3),
            c2.animate.set_color(C_ORCH),
            run_time=0.5,
        ); t += 0.5
        for x in tests[2:4]:
            self.play(x[0].animate.set_fill(C_ORCH, opacity=0.4), run_time=0.25); t += 0.25
        for l in touches[2:4]:
            self.play(l.animate.set_color(C_ORCH).set_stroke(width=2.5), run_time=0.15); t += 0.15
        t = _wait_until(self, 92.1, t)

        # ── P7  92.1→104.2  Gaps ───────────────────────────────────
        gap_txt = Text("Unmapped service → needs regression tests ⚠",
                       font_size=12, color=C_WARN).move_to(DOWN * 2.5)
        self.play(Transform(r_txt, gap_txt), run_time=0.3); t += 0.3
        t = _wait_until(self, 104.2, t)

        # ── P8  104.2→118.8  Focused plan ──────────────────────────
        focus_txt = Text("run-tests → focused plan: 5 tests, not 50",
                         font_size=12, color=WHITE).move_to(DOWN * 2.5)
        self.play(Transform(r_txt, focus_txt), run_time=0.3); t += 0.3
        t = _wait_until(self, 118.8, t)

        # ── P9  118.8→123.2  Summary ───────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.5); t += 0.5
        s = Text("Graph query → Focused test plan → Faster feedback",
                  font_size=22, color=WHITE)
        self.play(FadeIn(s), run_time=0.6); t += 0.6
        t = _wait_until(self, 123.2, t)

    def _svc_circle(self, label, color, pos, radius=0.40):
        c = Circle(radius=radius, color=color, fill_opacity=0.12, stroke_width=2.5)
        t = Text(label, font_size=12, color=color)
        return VGroup(c, t).move_to(pos)


# ═════════════════════════════════════════════════════════════════════
# M12.2 — Segment 12: Full regression suite
# Audio: 12-regression-suite.mp3  (~39.4 s)
# Beats align with narration/12-regression-suite.md numbered script.
# ═════════════════════════════════════════════════════════════════════
class RegressionSuiteScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        title = Text("Full regression suite", font_size=32, color=WHITE)
        sub = Text("Verify in layers — unit tests alone are not enough", font_size=15, color=GREY)
        sub.next_to(title, DOWN, buff=0.32)
        self.play(FadeIn(title), FadeIn(sub), run_time=1.0)
        t += 1.0
        t = _wait_until(self, 8.0, t)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.45)
        t += 0.45

        h1 = Text("Without Kubernetes", font_size=14, color=C_GUI)
        h1.move_to(LEFT * 3.6 + UP * 2.55)
        h2 = Text("With cluster", font_size=14, color=C_ORCH)
        h2.move_to(RIGHT * 3.6 + UP * 2.55)
        self.play(FadeIn(h1), FadeIn(h2), run_time=0.5)
        t += 0.5

        left_col = VGroup(
            Text("Phase 1 — stack YAML + registry", font_size=11, color=WHITE),
            Text("pytest — orchestrator, libs, GUI backend", font_size=11, color=WHITE),
            Text("vitest — baggage-node", font_size=11, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.22).move_to(LEFT * 3.6 + UP * 0.55)

        right_col = VGroup(
            Text("stack-dag-verify PipelineRun", font_size=11, color=C_PR),
            Text("Newman — orchestrator API", font_size=11, color=C_PR),
            Text("Playwright — management GUI", font_size=11, color=C_PR),
            Text("Tekton Results (optional)", font_size=10, color=GREY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(RIGHT * 3.6 + UP * 0.35)

        self.play(LaggedStart(FadeIn(left_col), FadeIn(right_col), lag_ratio=0.35), run_time=1.8)
        t += 1.8
        t = _wait_until(self, 26.0, t)

        driver = Text("run-regression-agent.sh", font_size=15, color=C_HOOK)
        driver.move_to(UP * 1.75)
        hint = Text("Phase 2 passed · regression exit code 0", font_size=13, color=C_PR)
        hint.next_to(driver, DOWN, buff=0.38)
        self.play(FadeIn(driver), run_time=0.45)
        t += 0.45
        self.play(FadeIn(hint), run_time=0.45)
        t += 0.45
        t = _wait_until(self, 35.5, t)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.45)
        t += 0.45
        fin = Text("Scripted bar clear — safe for docs / merge", font_size=20, color=C_PR)
        self.play(FadeIn(fin), run_time=0.7)
        t += 0.7
        t = _wait_until(self, 39.5, t)


# ═════════════════════════════════════════════════════════════════════
# M12.2 — Segment 13: Management GUI architecture
# Keep total runtime ≤ TTS length (~38 s after M12.2 script strip) so compose
# does not chop the Helm / DAG beats.
# ═════════════════════════════════════════════════════════════════════
class ManagementGUIArchitectureScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        title = Text("Management GUI architecture", font_size=28, color=C_GUI)
        self.play(FadeIn(title), run_time=0.75)
        t += 0.75
        t = _wait_until(self, 2.8, t)
        self.play(title.animate.scale(0.42).to_edge(UP, buff=0.18), run_time=0.45)
        t += 0.45

        cred = Text("Browser never holds cluster credentials", font_size=12, color=C_PR)
        cred.move_to(UP * 2.35)
        br = _box("Browser", GREY, w=1.45, h=0.58, fs=12)
        vu = _box("Vue 3 SPA", C_VUE, w=1.55, h=0.58, fs=12)
        apilbl = _box("/api/*", C_FLASK, w=1.25, h=0.58, fs=11)
        fl = _box("Flask", C_FLASK, w=1.2, h=0.58, fs=12)
        k8 = _box("Kubernetes", C_PIPE, w=1.65, h=0.58, fs=11)
        row = VGroup(br, vu, apilbl, fl, k8).arrange(RIGHT, buff=0.28).move_to(UP * 0.75)
        self.play(FadeIn(cred), LaggedStart(*[FadeIn(x) for x in row], lag_ratio=0.12), run_time=1.6)
        t += 1.6
        for i in range(len(row) - 1):
            arr = Arrow(
                row[i].get_right(), row[i + 1].get_left(), buff=0.06,
                color=WHITE, stroke_width=2, max_tip_length_to_length_ratio=0.08,
            )
            self.play(Create(arr), run_time=0.12)
            t += 0.12
        t = _wait_until(self, 11.0, t)

        team = Text("/api/teams/{team}/pipelineruns …", font_size=11, color=C_ORCH)
        team.move_to(DOWN * 0.35)
        self.play(FadeIn(team), run_time=0.45)
        t += 0.45
        t = _wait_until(self, 18.0, t)

        views = VGroup(
            _badge("Trigger", C_PR),
            _badge("Monitor", C_ORCH),
            _badge("DAG", C_NEO4J),
        ).arrange(RIGHT, buff=0.45).move_to(DOWN * 1.85)
        cap = Text("Stack YAML resolved server-side · Vue Flow", font_size=11, color=GREY)
        cap.next_to(views, DOWN, buff=0.28)
        self.play(FadeIn(views), run_time=0.6)
        t += 0.6
        self.play(FadeIn(cap), run_time=0.35)
        t += 0.35
        t = _wait_until(self, 28.0, t)

        helm = Text("Helm: namespace, RBAC, orchestrator endpoints", font_size=12, color=C_HELM)
        helm.move_to(DOWN * 3.05)
        self.play(FadeIn(helm), run_time=0.5)
        t += 0.5
        t = _wait_until(self, 37.5, t)


# ═════════════════════════════════════════════════════════════════════
# M12.2 — Segment 14: Extending the GUI for Tekton
# Keep total ≤ TTS (~40 s) so the extension-doc line is not trimmed by ffmpeg.
# ═════════════════════════════════════════════════════════════════════
class GUIExtensionScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        title = Text("Extending the GUI for Tekton", font_size=28, color=WHITE)
        self.play(FadeIn(title), run_time=0.75)
        t += 0.75
        t = _wait_until(self, 3.0, t)
        self.play(FadeOut(title), run_time=0.4)
        t += 0.4

        lt = Text("Flask — add JSON route first", font_size=14, color=C_FLASK)
        lt.move_to(LEFT * 3.6 + UP * 2.75)
        rt = Text("Vue — Pinia + views", font_size=14, color=C_VUE)
        rt.move_to(RIGHT * 3.6 + UP * 2.75)
        self.play(FadeIn(lt), FadeIn(rt), run_time=0.45)
        t += 0.45

        left_body = VGroup(
            Text("Wrap kubernetes client", font_size=11, color=GREY),
            Text("Stable JSON for tables / charts", font_size=12, color=WHITE),
            Text("pytest + mocks (same style as routes)", font_size=11, color=GREY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(LEFT * 3.6 + UP * 0.95)

        right_body = VGroup(
            Text("Store: useApi + teamUrl()", font_size=12, color=WHITE),
            Text("Router + view component", font_size=11, color=GREY),
            Text("Playwright spec per flow", font_size=11, color=GREY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.2).move_to(RIGHT * 3.6 + UP * 0.95)

        self.play(FadeIn(left_body), run_time=0.85)
        t += 0.85
        t = _wait_until(self, 10.0, t)
        self.play(FadeIn(right_body), run_time=0.85)
        t += 0.85
        t = _wait_until(self, 18.0, t)

        bridge = Text("team-scoped reads", font_size=11, color=GREY_B)
        bridge.move_to(UP * 0.95)
        self.play(FadeIn(bridge), run_time=0.35)
        t += 0.35
        arr = Arrow(LEFT * 1.15 + UP * 0.95, RIGHT * 1.15 + UP * 0.95, buff=0.02, color=GREY_B)
        self.play(Create(arr), run_time=0.25)
        t += 0.25
        t = _wait_until(self, 26.0, t)

        qa = VGroup(
            Text("pytest — API contracts", font_size=12, color=C_PR),
            Text("Playwright — UI regressions", font_size=12, color=C_PR),
            Text("Small PRs: schema, route, store, view, one E2E", font_size=11, color=WHITE),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.18).move_to(DOWN * 2.05)
        self.play(FadeIn(qa), run_time=0.9)
        t += 0.9
        t = _wait_until(self, 35.0, t)

        doc = Text("docs/MANAGEMENT-GUI-EXTENSION.md", font_size=12, color=C_HOOK)
        doc.to_edge(DOWN, buff=0.32)
        self.play(FadeIn(doc), run_time=0.45)
        t += 0.45
        t = _wait_until(self, 40.5, t)
