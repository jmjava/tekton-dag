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


def _hc_box(label, color, w=SVC_W, h=SVC_H, fs=18):
    """High-contrast box: WHITE text on colored fill for dark backgrounds."""
    r = RoundedRectangle(corner_radius=0.15, width=w, height=h,
                         stroke_color=color, fill_color=color, fill_opacity=0.18)
    t = Text(label, font_size=fs, color=WHITE, weight=BOLD)
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


# ═════════════════════════════════════════════════════════════════════
# Segment 07 — Merge & Release Pipeline (NEW)
# ═════════════════════════════════════════════════════════════════════
class MergeReleaseScene(Scene):
    """~150s scene synced to 07-merge-release Whisper timing."""

    def _item(self, txt, color=GREY_B, ic_color=None):
        ic = Text("\u203a", font_size=13, color=ic_color or color)
        tx = Text(txt, font_size=10, color=color)
        tx.next_to(ic, RIGHT, buff=0.12)
        return VGroup(ic, tx)

    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0
        detail_y = DOWN * 0.2

        # ── Intro (0-6s) ─────────────────────────────────────────
        title = Text("Merge & Release Pipeline", font_size=30, color=WHITE)
        self.play(FadeIn(title), run_time=0.8); t += 0.8
        t = _wait_until(self, 4.0, t)
        self.play(title.animate.scale(0.55).to_edge(UP, buff=0.25), run_time=0.6); t += 0.6

        # ── Phase overview strip ─────────────────────────────────
        phases = [
            ("Version\nBump", C_WARN), ("Compile\n& Build", C_SPRING),
            ("Crane\nTag", C_PR), ("Hook\nTasks", C_HOOK),
            ("Push\nVersion", C_PROD),
        ]
        phase_cards = VGroup()
        for i, (lbl, col) in enumerate(phases):
            bg = RoundedRectangle(corner_radius=0.1, width=1.8, height=0.7,
                                  stroke_color=col, fill_color=col, fill_opacity=0.18)
            tx = Text(lbl, font_size=9, color=WHITE, weight=BOLD)
            tx.move_to(bg)
            card = VGroup(bg, tx)
            card.move_to(RIGHT * (-4.5 + i * 2.25) + UP * 2.2)
            phase_cards.add(card)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in phase_cards],
                              lag_ratio=0.12), run_time=1.2); t += 1.2
        t = _wait_until(self, 6.5, t)

        def _hl(idx):
            self.play(*[c.animate.set_opacity(1.0 if j == idx else 0.45)
                        for j, c in enumerate(phase_cards)], run_time=0.3)
            return 0.3

        # ── Phase 1: Version bump (6.5-38s) ──────────────────────
        t += _hl(0)
        p1 = Text("Version Bump — Release Mode", font_size=16, color=C_WARN, weight=BOLD)
        p1.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(p1), run_time=0.4); t += 0.4

        rc_ver = Text("0.1.0-rc.3", font_size=18, color=C_WARN, font="Monospace")
        rc_ver.move_to(detail_y + UP * 0.7 + LEFT * 3.0)
        rc_lbl = Text("PR version", font_size=10, color=GREY_B)
        rc_lbl.next_to(rc_ver, DOWN, buff=0.1)
        t = _wait_until(self, 10.0, t)
        self.play(FadeIn(rc_ver), FadeIn(rc_lbl), run_time=0.4); t += 0.4

        rel_ver = Text("0.1.0", font_size=18, color=C_PR, font="Monospace")
        rel_ver.move_to(detail_y + UP * 0.7)
        rel_lbl = Text("Release", font_size=10, color=GREY_B)
        rel_lbl.next_to(rel_ver, DOWN, buff=0.1)
        strip_arr = Arrow(rc_ver.get_right(), rel_ver.get_left(), buff=0.12,
                          color=C_ORCH, stroke_width=2)
        strip_txt = Text("strip -rc.N", font_size=9, color=C_ORCH)
        strip_txt.next_to(strip_arr, UP, buff=0.05)
        t = _wait_until(self, 18.0, t)
        self.play(Create(strip_arr), FadeIn(strip_txt), FadeIn(rel_ver), FadeIn(rel_lbl),
                  run_time=0.6); t += 0.6

        next_ver = Text("0.1.1-rc.0", font_size=18, color=C_PROD, font="Monospace")
        next_ver.move_to(detail_y + UP * 0.7 + RIGHT * 3.0)
        next_lbl = Text("Next dev cycle", font_size=10, color=GREY_B)
        next_lbl.next_to(next_ver, DOWN, buff=0.1)
        bump_arr = Arrow(rel_ver.get_right(), next_ver.get_left(), buff=0.12,
                         color=C_ORCH, stroke_width=2)
        bump_txt = Text("bump patch", font_size=9, color=C_ORCH)
        bump_txt.next_to(bump_arr, UP, buff=0.05)
        t = _wait_until(self, 23.0, t)
        self.play(Create(bump_arr), FadeIn(bump_txt), FadeIn(next_ver), FadeIn(next_lbl),
                  run_time=0.6); t += 0.6

        ver_items = [
            "PR cycle tracks release candidates (-rc.N)",
            "Merge strips suffix to clean semver",
            "Post-merge bumps patch for next cycle",
        ]
        vig = VGroup()
        for i, vi in enumerate(ver_items):
            item = self._item(vi, WHITE, C_WARN)
            item.move_to(detail_y + DOWN * (0.3 + i * 0.4) + LEFT * 1.5)
            vig.add(item)
        per = max(0.3, (36.0 - t) / len(ver_items) - 0.4)
        for item in vig:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 37.5, t)
        self.play(FadeOut(p1), FadeOut(rc_ver), FadeOut(rc_lbl), FadeOut(rel_ver),
                  FadeOut(rel_lbl), FadeOut(strip_arr), FadeOut(strip_txt),
                  FadeOut(next_ver), FadeOut(next_lbl), FadeOut(bump_arr),
                  FadeOut(bump_txt), FadeOut(vig), run_time=0.35); t += 0.35

        # ── Phase 2: Compile & Build (38-62s) ────────────────────
        t += _hl(1)
        p2 = Text("Compile & Containerize", font_size=16, color=C_SPRING, weight=BOLD)
        p2.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(p2), run_time=0.4); t += 0.4
        t = _wait_until(self, 40.0, t)

        build_items = [
            "Tagged with merge commit SHA",
            "Parameterized build images: Maven, Gradle, NPM, Pip, Composer",
            "Resource profiles configured per team (Helm values)",
            "Same compile step as PR, release-quality output",
        ]
        big = VGroup()
        for i, bi in enumerate(build_items):
            item = self._item(bi, WHITE, C_SPRING)
            item.move_to(detail_y + UP * (0.6 - i * 0.42) + LEFT * 1.5)
            big.add(item)
        per = max(0.3, (60.0 - t) / len(build_items) - 0.4)
        for item in big:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 61.5, t)
        self.play(FadeOut(p2), FadeOut(big), run_time=0.35); t += 0.35

        # ── Phase 3: Crane tag (62-90s) ──────────────────────────
        t += _hl(2)
        p3 = Text("Crane Tag — Release Images", font_size=16, color=C_PR, weight=BOLD)
        p3.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(p3), run_time=0.4); t += 0.4
        t = _wait_until(self, 64.0, t)

        crane_flow = [
            _box("Built image\n:sha-abc123", C_PIPE, w=2.5, h=0.7, fs=9),
            _box("crane copy", C_ORCH, w=1.8, h=0.7, fs=10),
            _box("registry/app\n:v0.1.0", C_PR, w=2.5, h=0.7, fs=9),
        ]
        for i, fb in enumerate(crane_flow):
            fb.move_to(detail_y + UP * 0.5 + LEFT * (3.0 - i * 3.0))
        crane_arrs = []
        for i in range(len(crane_flow) - 1):
            crane_arrs.append(Arrow(crane_flow[i].get_right(), crane_flow[i+1].get_left(),
                                    buff=0.1, color=GREY_B, stroke_width=2))
        per = max(0.3, (75.0 - t) / len(crane_flow) - 0.5)
        for i, fb in enumerate(crane_flow):
            self.play(FadeIn(fb, shift=RIGHT * 0.15), run_time=0.4); t += 0.4
            if i < len(crane_arrs):
                self.play(GrowArrow(crane_arrs[i]), run_time=0.25); t += 0.25
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 77.0, t)
        crane_notes = [
            "Fast, daemon-less container tool",
            "Copies layers without rebuilding",
            "Image tagged with release semver",
            "No rebuild needed — same artifact",
        ]
        cng = VGroup()
        for i, cn in enumerate(crane_notes):
            item = self._item(cn, WHITE, C_PR)
            item.move_to(detail_y + DOWN * (0.5 + i * 0.4) + LEFT * 1.5)
            cng.add(item)
        per = max(0.3, (88.0 - t) / len(crane_notes) - 0.3)
        for item in cng:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 89.5, t)
        self.play(FadeOut(p3), *[FadeOut(f) for f in crane_flow],
                  *[FadeOut(a) for a in crane_arrs], FadeOut(cng), run_time=0.35); t += 0.35

        # ── Phase 4: Hook tasks (90-122s) ────────────────────────
        t += _hl(3)
        p4 = Text("Hook Tasks", font_size=16, color=C_HOOK, weight=BOLD)
        p4.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(p4), run_time=0.4); t += 0.4
        t = _wait_until(self, 92.0, t)

        hook_items = [
            "post-build: image security scan (Trivy)",
            "post-build: software bill of materials (SBOM)",
            "pre-test: seed test data",
            "Optional Tekton tasks via pipeline parameters",
            "No fork of core pipeline needed",
        ]
        hig = VGroup()
        for i, hi in enumerate(hook_items):
            item = self._item(hi, WHITE, C_HOOK)
            item.move_to(detail_y + UP * (0.8 - i * 0.42) + LEFT * 1.5)
            hig.add(item)
        per = max(0.3, (120.0 - t) / len(hook_items) - 0.4)
        for item in hig:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 121.5, t)
        self.play(FadeOut(p4), FadeOut(hig), run_time=0.35); t += 0.35

        # ── Phase 5: Push version (122-150s) ─────────────────────
        t += _hl(4)
        p5 = Text("Push Version — Next Dev Cycle", font_size=16, color=C_PROD, weight=BOLD)
        p5.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(p5), run_time=0.4); t += 0.4
        t = _wait_until(self, 124.0, t)

        push_items = [
            "Version file bumped: 0.1.0 -> 0.1.1-rc.0",
            "Pushed back to repo with pipeline credentials",
            "Next PR auto-increments release candidate",
            "Release-tagged image ready for promotion",
        ]
        pig = VGroup()
        for i, pi in enumerate(push_items):
            item = self._item(pi, WHITE, C_PROD)
            item.move_to(detail_y + UP * (0.6 - i * 0.42) + LEFT * 1.5)
            pig.add(item)
        per = max(0.3, (140.0 - t) / len(push_items) - 0.4)
        for item in pig:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)

        # Closing summary
        t = _wait_until(self, 141.0, t)
        self.play(FadeOut(p5), FadeOut(pig), run_time=0.35); t += 0.35
        self.play(*[c.animate.set_opacity(1.0) for c in phase_cards], run_time=0.4); t += 0.4
        t = _wait_until(self, 143.0, t)

        closing = Text("Tested | Version promoted | Image tagged | Hooks executed",
                       font_size=13, color=C_PR)
        closing.move_to(detail_y + DOWN * 0.5)
        self.play(FadeIn(closing), run_time=0.5); t += 0.5
        t = _wait_until(self, 148.0, t)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0); t += 1.0

# ═════════════════════════════════════════════════════════════════════
# Segment 10 — Baggage Middleware (NEW)
# ═════════════════════════════════════════════════════════════════════
class BaggageMiddlewareScene(Scene):
    """~186s scene synced to 10-baggage-middleware Whisper timing."""

    def _item(self, txt, color=GREY_B, ic_color=None):
        ic = Text("\u203a", font_size=13, color=ic_color or color)
        tx = Text(txt, font_size=10, color=color)
        tx.next_to(ic, RIGHT, buff=0.12)
        return VGroup(ic, tx)

    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0
        detail_y = DOWN * 0.2

        # ── Intro (0-7s) ─────────────────────────────────────────
        title = Text("Baggage Middleware", font_size=30, color=WHITE)
        sub = Text("One header contract — five frameworks", font_size=16, color=GREY_B)
        sub.next_to(title, DOWN, buff=0.25)
        tg = VGroup(title, sub).move_to(ORIGIN)
        self.play(FadeIn(tg), run_time=0.8); t += 0.8
        t = _wait_until(self, 4.0, t)
        self.play(tg.animate.scale(0.55).to_edge(UP, buff=0.2), run_time=0.6); t += 0.6

        # ── Roles strip (7-15s) ──────────────────────────────────
        roles = [
            ("Originator", C_VUE), ("Forwarder", C_SPRING), ("Terminal", C_FLASK),
        ]
        role_cards = VGroup()
        for i, (lbl, col) in enumerate(roles):
            bg = RoundedRectangle(corner_radius=0.1, width=2.2, height=0.6,
                                  stroke_color=col, fill_color=col, fill_opacity=0.18)
            tx = Text(lbl, font_size=10, color=WHITE, weight=BOLD)
            tx.move_to(bg)
            card = VGroup(bg, tx)
            card.move_to(RIGHT * (-3.5 + i * 3.5) + UP * 2.2)
            role_cards.add(card)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in role_cards],
                              lag_ratio=0.15), run_time=1.0); t += 1.0
        role_arrs = VGroup()
        for i in range(len(role_cards) - 1):
            arr = Arrow(role_cards[i].get_right(), role_cards[i+1].get_left(),
                        buff=0.1, color=C_ORCH, stroke_width=2)
            hdr = Text("x-dev-session", font_size=8, color=C_ORCH)
            hdr.next_to(arr, UP, buff=0.04)
            role_arrs.add(VGroup(arr, hdr))
            self.play(Create(arr), FadeIn(hdr), run_time=0.3); t += 0.3
        t = _wait_until(self, 11.0, t)

        role_details = [
            "Originator: sets header on all outgoing requests",
            "Forwarder: reads, stores in context, attaches downstream",
            "Terminal: accepts for routing/logging, stops propagation",
        ]
        rdg = VGroup()
        for i, rd in enumerate(role_details):
            item = self._item(rd, WHITE, [C_VUE, C_SPRING, C_FLASK][i])
            item.move_to(detail_y + UP * (0.9 - i * 0.42) + LEFT * 1.5)
            rdg.add(item)
        per = max(0.3, (20.0 - t) / len(role_details) - 0.4)
        for item in rdg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 40.0, t)
        self.play(FadeOut(rdg), run_time=0.3); t += 0.3

        # ── Framework cards strip ────────────────────────────────
        fw_data = [
            ("Spring Boot", C_SPRING), ("Node / Vue", C_VUE),
            ("Flask", C_FLASK), ("PHP", C_PHP),
        ]
        fw_cards = VGroup()
        for i, (lbl, col) in enumerate(fw_data):
            bg = RoundedRectangle(corner_radius=0.1, width=2.2, height=0.6,
                                  stroke_color=col, fill_color=col, fill_opacity=0.18)
            tx = Text(lbl, font_size=9, color=WHITE, weight=BOLD)
            tx.move_to(bg)
            card = VGroup(bg, tx)
            card.move_to(RIGHT * (-4.0 + i * 2.7) + UP * 0.8)
            fw_cards.add(card)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in fw_cards],
                              lag_ratio=0.12), run_time=1.0); t += 1.0

        def _hl_fw(idx):
            self.play(*[c.animate.set_opacity(1.0 if j == idx else 0.45)
                        for j, c in enumerate(fw_cards)], run_time=0.3)
            return 0.3

        # ── Spring Boot (42-78s) ─────────────────────────────────
        t += _hl_fw(0)
        s1 = Text("Spring Boot", font_size=16, color=C_SPRING, weight=BOLD)
        s1.move_to(detail_y + DOWN * 0.6)
        self.play(FadeIn(s1), run_time=0.4); t += 0.4
        sp_items = [
            "BaggageContextFilter: reads incoming header",
            "Stores via OpenTelemetry baggage + ThreadLocal",
            "RestTemplateInterceptor: adds to outbound calls",
            "Activates with: baggage.enabled=true",
            "False or absent: filter not registered (zero overhead)",
        ]
        spg = VGroup()
        for i, si in enumerate(sp_items):
            item = self._item(si, WHITE, C_SPRING)
            item.move_to(detail_y + DOWN * (1.3 + i * 0.38) + LEFT * 1.5)
            spg.add(item)
        per = max(0.3, (76.0 - t) / len(sp_items) - 0.4)
        for item in spg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 77.5, t)
        self.play(FadeOut(s1), FadeOut(spg), run_time=0.3); t += 0.3

        # ── Node / Vue (78-100s) ─────────────────────────────────
        t += _hl_fw(1)
        s2 = Text("Node / Vue", font_size=16, color=C_VUE, weight=BOLD)
        s2.move_to(detail_y + DOWN * 0.6)
        self.play(FadeIn(s2), run_time=0.4); t += 0.4
        nd_items = [
            "createBaggageFetch: wraps native fetch, injects header",
            "createAxiosInterceptor: for Axios-based projects",
            "Config from env: VT_BAGGAGE_ENABLED",
            "Browser build: include/exclude at compile time",
        ]
        ndg = VGroup()
        for i, ni in enumerate(nd_items):
            item = self._item(ni, WHITE, C_VUE)
            item.move_to(detail_y + DOWN * (1.3 + i * 0.38) + LEFT * 1.5)
            ndg.add(item)
        per = max(0.3, (98.0 - t) / len(nd_items) - 0.4)
        for item in ndg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 100.5, t)
        self.play(FadeOut(s2), FadeOut(ndg), run_time=0.3); t += 0.3

        # ── Flask (101-123s) ─────────────────────────────────────
        t += _hl_fw(2)
        s3 = Text("Flask / Python", font_size=16, color=C_FLASK, weight=BOLD)
        s3.move_to(detail_y + DOWN * 0.6)
        self.play(FadeIn(s3), run_time=0.4); t += 0.4
        fl_items = [
            "init_app: registers before_request hook",
            "Extracts header, stores on flask.g",
            "BaggageSession: extends requests.Session",
            "Adds header to all outbound calls automatically",
            "Enabled by env var, zero cost when disabled",
        ]
        flg = VGroup()
        for i, fi in enumerate(fl_items):
            item = self._item(fi, WHITE, C_FLASK)
            item.move_to(detail_y + DOWN * (1.3 + i * 0.38) + LEFT * 1.5)
            flg.add(item)
        per = max(0.3, (122.0 - t) / len(fl_items) - 0.4)
        for item in flg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 123.0, t)
        self.play(FadeOut(s3), FadeOut(flg), run_time=0.3); t += 0.3

        # ── PHP (124-140s) ───────────────────────────────────────
        t += _hl_fw(3)
        s4 = Text("PHP", font_size=16, color=C_PHP, weight=BOLD)
        s4.move_to(detail_y + DOWN * 0.6)
        self.play(FadeIn(s4), run_time=0.4); t += 0.4
        ph_items = [
            "PSR-15 middleware for inbound requests",
            "Guzzle middleware for outbound HTTP",
            "Config from env vars",
            "Static fromEnv() factory method",
        ]
        phg = VGroup()
        for i, pi in enumerate(ph_items):
            item = self._item(pi, WHITE, C_PHP)
            item.move_to(detail_y + DOWN * (1.3 + i * 0.38) + LEFT * 1.5)
            phg.add(item)
        per = max(0.3, (139.0 - t) / len(ph_items) - 0.4)
        for item in phg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 140.0, t)
        self.play(FadeOut(s4), FadeOut(phg), run_time=0.3); t += 0.3

        # ── W3C + Safety (141-180s) ──────────────────────────────
        self.play(*[c.animate.set_opacity(1.0) for c in fw_cards], run_time=0.3); t += 0.3
        w3c_title = Text("Standards & Safety", font_size=16, color=C_ORCH, weight=BOLD)
        w3c_title.move_to(detail_y + DOWN * 0.6)
        self.play(FadeIn(w3c_title), run_time=0.4); t += 0.4
        t = _wait_until(self, 145.0, t)

        std_items = [
            "W3C Baggage spec + custom x-dev-session header",
            "Third-party tools read routing context",
            "Enabled flag: OFF by default in every framework",
            "Activates only with explicit env var = true",
            "Deploy middleware to prod: does nothing until opt-in",
            "No accidental header leakage, no performance impact",
        ]
        stg = VGroup()
        for i, si in enumerate(std_items):
            item = self._item(si, WHITE, C_ORCH)
            item.move_to(detail_y + DOWN * (1.3 + i * 0.38) + LEFT * 1.5)
            stg.add(item)
        per = max(0.3, (178.0 - t) / len(std_items) - 0.3)
        for item in stg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 180.0, t)
        self.play(FadeOut(w3c_title), FadeOut(stg), run_time=0.3); t += 0.3

        # ── Closing (180-186s) ───────────────────────────────────
        closing = Text("Five frameworks | One header contract | Zero code changes",
                       font_size=14, color=C_PR)
        closing.move_to(detail_y + DOWN * 0.5)
        self.play(FadeIn(closing), run_time=0.5); t += 0.5
        t = _wait_until(self, 184.0, t)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0); t += 1.0

# ═════════════════════════════════════════════════════════════════════
# Segment 14 — Customization (NEW)
# ═════════════════════════════════════════════════════════════════════
class CustomizationScene(Scene):
    """~186s scene synced to 14-customization Whisper timing."""

    def _item(self, txt, color=GREY_B, ic_color=None):
        ic = Text("\u203a", font_size=13, color=ic_color or color)
        tx = Text(txt, font_size=10, color=color)
        tx.next_to(ic, RIGHT, buff=0.12)
        return VGroup(ic, tx)

    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0
        detail_y = DOWN * 0.2

        title = Text("Customization", font_size=30, color=WHITE)
        sub = Text("Config-driven — no pipeline forks", font_size=16, color=GREY_B)
        sub.next_to(title, DOWN, buff=0.25)
        tg = VGroup(title, sub).move_to(ORIGIN)
        self.play(FadeIn(tg), run_time=0.8); t += 0.8
        t = _wait_until(self, 4.0, t)
        self.play(tg.animate.scale(0.55).to_edge(UP, buff=0.2), run_time=0.6); t += 0.6

        topics = [
            ("Schema", C_ORCH), ("Apps", C_SPRING), ("Variants", C_VUE),
            ("Hooks", C_HOOK), ("Onboard", C_PROD), ("Helm", C_HELM),
        ]
        tc = VGroup()
        for i, (lbl, col) in enumerate(topics):
            bg = RoundedRectangle(corner_radius=0.1, width=1.5, height=0.6,
                                  stroke_color=col, fill_color=col, fill_opacity=0.18)
            tx = Text(lbl, font_size=9, color=WHITE, weight=BOLD)
            tx.move_to(bg)
            card = VGroup(bg, tx); card.move_to(RIGHT * (-5.0 + i * 2.0) + UP * 2.2)
            tc.add(card)
        self.play(LaggedStart(*[FadeIn(c, shift=DOWN * 0.1) for c in tc],
                              lag_ratio=0.12), run_time=1.0); t += 1.0
        t = _wait_until(self, 8.0, t)

        def _hl(idx):
            self.play(*[c.animate.set_opacity(1.0 if j == idx else 0.45)
                        for j, c in enumerate(tc)], run_time=0.3)
            return 0.3

        # ── T1: Stack schema (8-34s) ─────────────────────────────
        t += _hl(0)
        t1 = Text("Stack Schema", font_size=16, color=C_ORCH, weight=BOLD)
        t1.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(t1), run_time=0.4); t += 0.4
        t = _wait_until(self, 12.0, t)
        items = ["Defines valid stack YAML shape", "App names, build tools, roles",
                 "Dependencies + test specifications",
                 "Catches typos before pipeline runs"]
        g = VGroup()
        for i, s in enumerate(items):
            item = self._item(s, WHITE, C_ORCH)
            item.move_to(detail_y + UP * (0.6 - i * 0.42) + LEFT * 1.5)
            g.add(item)
        per = max(0.3, (32.0 - t) / len(items) - 0.4)
        for item in g:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 34.0, t)
        self.play(FadeOut(t1), FadeOut(g), run_time=0.3); t += 0.3

        # ── T2: App entries (34-56s) ─────────────────────────────
        t += _hl(1)
        t2 = Text("Adding an Application", font_size=16, color=C_SPRING, weight=BOLD)
        t2.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(t2), run_time=0.4); t += 0.4
        t = _wait_until(self, 36.0, t)
        items = ["YAML edit: add entry to apps array",
                 "name, repo, role (originator/forwarder/terminal)",
                 "build tool, downstream deps, test collections",
                 "Pipeline picks up new app on next run"]
        g = VGroup()
        for i, s in enumerate(items):
            item = self._item(s, WHITE, C_SPRING)
            item.move_to(detail_y + UP * (0.6 - i * 0.42) + LEFT * 1.5)
            g.add(item)
        per = max(0.3, (54.0 - t) / len(items) - 0.4)
        for item in g:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 55.5, t)
        self.play(FadeOut(t2), FadeOut(g), run_time=0.3); t += 0.3

        # ── T3: Build variants (56-82s) ──────────────────────────
        t += _hl(2)
        t3 = Text("Build Image Variants", font_size=16, color=C_VUE, weight=BOLD)
        t3.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(t3), run_time=0.4); t += 0.4
        t = _wait_until(self, 58.0, t)
        items = ["compileImageVariants in Helm values",
                 "Map of tool+version to container image",
                 "Team alpha: Java 17, Team beta: Java 21",
                 "stack.yaml build.java-version selects image",
                 "Pipeline resolves matching image at runtime"]
        g = VGroup()
        for i, s in enumerate(items):
            item = self._item(s, WHITE, C_VUE)
            item.move_to(detail_y + UP * (0.6 - i * 0.42) + LEFT * 1.5)
            g.add(item)
        per = max(0.3, (80.0 - t) / len(items) - 0.4)
        for item in g:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35); t += 0.35
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 82.0, t)
        self.play(FadeOut(t3), FadeOut(g), run_time=0.3); t += 0.3

        # ── T4: Hook tasks (82-131s) ─────────────────────────────
        t += _hl(3)
        t4 = Text("Pipeline Hook Tasks", font_size=16, color=C_HOOK, weight=BOLD)
        t4.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(t4), run_time=0.4); t += 0.4
        t = _wait_until(self, 85.0, t)
        items = ["Four insertion points: pre/post-build, pre/post-test",
                 "Pipeline param names a Tekton Task",
                 "Empty param: skipped (when expression, zero overhead)",
                 "Task gets: stack def, build outputs, workspace",
                 "Image scan example: Trivy post-build",
                 "Slack notification: post-test",
                 "Same param contract: teams write own hooks"]
        g = VGroup()
        for i, s in enumerate(items):
            item = self._item(s, WHITE, C_HOOK)
            item.move_to(detail_y + UP * (0.8 - i * 0.38) + LEFT * 1.5)
            g.add(item)
        per = max(0.3, (129.0 - t) / len(items) - 0.3)
        for item in g:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 131.0, t)
        self.play(FadeOut(t4), FadeOut(g), run_time=0.3); t += 0.3

        # ── T5: Team onboarding (131-158s) ───────────────────────
        t += _hl(4)
        t5 = Text("Team Onboarding", font_size=16, color=C_PROD, weight=BOLD)
        t5.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(t5), run_time=0.4); t += 0.4
        t = _wait_until(self, 133.0, t)
        items = ["Three-step process:",
                 "1. team.yaml: name, namespace, stack list",
                 "2. values.yaml: registry, intercept, versions, limits",
                 "3. helm install with team values",
                 "Chart creates team-scoped ConfigMaps",
                 "Orchestrator manages only its own stacks"]
        g = VGroup()
        for i, s in enumerate(items):
            item = self._item(s, WHITE, C_PROD)
            item.move_to(detail_y + UP * (0.8 - i * 0.38) + LEFT * 1.5)
            g.add(item)
        per = max(0.3, (156.0 - t) / len(items) - 0.3)
        for item in g:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 158.0, t)
        self.play(FadeOut(t5), FadeOut(g), run_time=0.3); t += 0.3

        # ── T6: Helm values + closing (158-186s) ────────────────
        t += _hl(5)
        t6 = Text("Infrastructure Helm Values", font_size=16, color=C_HELM, weight=BOLD)
        t6.move_to(detail_y + UP * 1.5)
        self.play(FadeIn(t6), run_time=0.4); t += 0.4
        t = _wait_until(self, 160.0, t)
        items = ["Container registry URL", "Intercept backend: Telepresence / mirrord",
                 "Pipeline timeouts", "Resource profiles per tool",
                 "Single values.yaml edit + helm upgrade"]
        g = VGroup()
        for i, s in enumerate(items):
            item = self._item(s, WHITE, C_HELM)
            item.move_to(detail_y + UP * (0.6 - i * 0.42) + LEFT * 1.5)
            g.add(item)
        per = max(0.3, (175.0 - t) / len(items) - 0.3)
        for item in g:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 176.0, t)
        self.play(FadeOut(t6), FadeOut(g), run_time=0.3); t += 0.3

        self.play(*[c.animate.set_opacity(1.0) for c in tc], run_time=0.4); t += 0.4
        t = _wait_until(self, 178.0, t)
        closing = Text("Config-only | Schema-validated | Pluggable | Multi-version",
                       font_size=13, color=C_PR)
        closing.move_to(detail_y + DOWN * 0.5)
        self.play(FadeIn(closing), run_time=0.5); t += 0.5
        t = _wait_until(self, 184.0, t)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0); t += 1.0

# ═════════════════════════════════════════════════════════════════════
# Segment 16 — Management GUI Tour (REWRITE)
# ═════════════════════════════════════════════════════════════════════
class ManagementGUITourScene(Scene):
    """~210s scene synced to 16-management-gui Whisper timing."""

    def _item(self, txt, color=GREY_B, ic_color=None):
        ic = Text("\u203a", font_size=13, color=ic_color or color)
        tx = Text(txt, font_size=10, color=color)
        tx.next_to(ic, RIGHT, buff=0.12)
        return VGroup(ic, tx)

    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # Intro (0-7s)
        title = Text("Management GUI", font_size=30, color=C_GUI)
        sub = Text("Vue 3 + Flask — team-scoped operations", font_size=16, color=GREY_B)
        sub.next_to(title, DOWN, buff=0.25)
        tg = VGroup(title, sub).move_to(ORIGIN)
        self.play(FadeIn(tg), run_time=0.8); t += 0.8
        t = _wait_until(self, 4.0, t)
        self.play(tg.animate.scale(0.5).to_edge(UP, buff=0.25), run_time=0.6); t += 0.6

        # Browser chrome
        browser = RoundedRectangle(corner_radius=0.15, width=11.5, height=5.6,
            stroke_color=GREY_D, stroke_width=1.5, fill_color="#11111b", fill_opacity=0.6)
        browser.move_to(DOWN * 0.6)
        self.play(FadeIn(browser), run_time=0.4); t += 0.4

        # Sidebar
        sidebar = Rectangle(width=2.0, height=5.2, stroke_color=GREY_D, stroke_width=0.5,
                            fill_color="#181825", fill_opacity=0.8)
        sidebar.align_to(browser, LEFT).shift(RIGHT * 0.15 + DOWN * 0.05)
        team_label = Text("Team: alpha", font_size=11, color=C_GUI, weight=BOLD)
        team_label.move_to(sidebar.get_top() + DOWN * 0.35)
        nav_items = VGroup()
        nav_labels = ["DAG View", "Runs", "Triggers", "Tests", "Git", "Dashboard"]
        nav_colors = [C_NEO4J, C_PIPE, C_PR, C_PR, GREY_B, C_ORCH]
        for i, (nl, nc) in enumerate(zip(nav_labels, nav_colors)):
            nt = Text(nl, font_size=10, color=nc)
            nt.move_to(sidebar.get_top() + DOWN * (0.8 + i * 0.4) + RIGHT * 0.1)
            nav_items.add(nt)
        self.play(FadeIn(sidebar), FadeIn(team_label), run_time=0.4); t += 0.4
        for ni in nav_items:
            self.play(FadeIn(ni), run_time=0.12); t += 0.12
        t = _wait_until(self, 10.0, t)

        content = RIGHT * 2.0 + DOWN * 0.6

        def _hl_nav(idx):
            self.play(*[ni.animate.set_opacity(1.0 if j == idx else 0.5)
                        for j, ni in enumerate(nav_items)], run_time=0.25)
            return 0.25

        # ── Team switcher (10-22s) ───────────────────────────────
        sw = ["Every view filters to team namespace",
              "Team alpha: its stacks, runs, tests",
              "Team beta: sees only its own",
              "Persists across page navigation"]
        swg = VGroup()
        for i, s in enumerate(sw):
            item = self._item(s, WHITE, C_GUI)
            item.move_to(content + UP * (1.5 - i * 0.42))
            swg.add(item)
        per = max(0.3, (20.0 - t) / len(sw) - 0.3)
        for item in swg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 21.5, t)
        self.play(FadeOut(swg), run_time=0.3); t += 0.3

        # ── DAG View (22-40s) ────────────────────────────────────
        t += _hl_nav(0)
        dg = ["Stack graph rendered with Vue Flow",
              "Nodes color-coded by propagation role",
              "Click node: repo, build tool, dependencies",
              "Edges show build order + propagation routing"]
        dgr = VGroup()
        for i, d in enumerate(dg):
            item = self._item(d, WHITE, C_NEO4J)
            item.move_to(content + UP * (1.5 - i * 0.42))
            dgr.add(item)
        per = max(0.3, (38.0 - t) / len(dg) - 0.3)
        for item in dgr:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 39.5, t)
        self.play(FadeOut(dgr), run_time=0.3); t += 0.3

        # ── Pipeline Runs (40-63s) ───────────────────────────────
        t += _hl_nav(1)
        pr = ["Active + completed PipelineRuns per team",
              "Name, trigger (bootstrap/PR/merge), status, duration",
              "Expand run: individual TaskRun details",
              "Click TaskRun: live logs or fetched from Results",
              "Streamed real-time for running tasks"]
        prg = VGroup()
        for i, p in enumerate(pr):
            item = self._item(p, WHITE, C_PIPE)
            item.move_to(content + UP * (1.5 - i * 0.42))
            prg.add(item)
        per = max(0.3, (61.0 - t) / len(pr) - 0.3)
        for item in prg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 62.5, t)
        self.play(FadeOut(prg), run_time=0.3); t += 0.3

        # ── Triggers (63-89s) ────────────────────────────────────
        t += _hl_nav(2)
        tr = ["Start pipelines manually from GUI",
              "Select mode: bootstrap, PR, or merge",
              "Choose stack, specify changed app + params",
              "POSTs to orchestrator /api/run",
              "New PipelineRun appears in seconds"]
        trg = VGroup()
        for i, item_t in enumerate(tr):
            item = self._item(item_t, WHITE, C_PR)
            item.move_to(content + UP * (1.5 - i * 0.42))
            trg.add(item)
        per = max(0.3, (87.0 - t) / len(tr) - 0.3)
        for item in trg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 88.5, t)
        self.play(FadeOut(trg), run_time=0.3); t += 0.3

        # ── Test Results (89-110s) ───────────────────────────────
        t += _hl_nav(3)
        te = ["Newman, Playwright, Artillery results per run",
              "Pass-fail counts + expandable detail",
              "Neo4j blast-radius visualization",
              "Which services + tests in scope for change"]
        teg = VGroup()
        for i, item_t in enumerate(te):
            item = self._item(item_t, WHITE, C_PR)
            item.move_to(content + UP * (1.5 - i * 0.42))
            teg.add(item)
        per = max(0.3, (108.0 - t) / len(te) - 0.3)
        for item in teg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 109.5, t)
        self.play(FadeOut(teg), run_time=0.3); t += 0.3

        # ── Git Browser (110-128s) ───────────────────────────────
        t += _hl_nav(4)
        gi = ["Browse app repos from within the GUI",
              "Navigate directories, view files, recent commits",
              "Check PR changes without leaving the interface"]
        gig = VGroup()
        for i, item_t in enumerate(gi):
            item = self._item(item_t, WHITE, GREY_B)
            item.move_to(content + UP * (1.2 - i * 0.42))
            gig.add(item)
        per = max(0.3, (126.0 - t) / len(gi) - 0.3)
        for item in gig:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 127.5, t)
        self.play(FadeOut(gig), run_time=0.3); t += 0.3

        # ── Tekton Dashboard (128-142s) ──────────────────────────
        t += _hl_nav(5)
        tk = ["Embedded Tekton Dashboard in iframe",
              "Full resource browser: PipelineRuns, Tasks, etc.",
              "Cluster configuration without tool switching"]
        tkg = VGroup()
        for i, item_t in enumerate(tk):
            item = self._item(item_t, WHITE, C_ORCH)
            item.move_to(content + UP * (1.2 - i * 0.42))
            tkg.add(item)
        per = max(0.3, (140.0 - t) / len(tk) - 0.3)
        for item in tkg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 141.5, t)
        self.play(FadeOut(tkg), run_time=0.3); t += 0.3

        # ── Architecture (142-178s) ──────────────────────────────
        for ni in nav_items:
            ni.set_opacity(1.0)
        arch_title = Text("Architecture", font_size=16, color=C_GUI)
        arch_title.move_to(content + UP * 2.3)
        self.play(FadeIn(arch_title), run_time=0.3); t += 0.3
        arch = ["Vue 3 + Vite frontend",
                "Pinia stores for state management",
                "Shared API helper: team-scoped base URL",
                "Flask backend maps /api/* routes",
                "K8s Python client for cluster operations",
                "Proxies to orchestrator for pipeline management"]
        ag = VGroup()
        for i, a in enumerate(arch):
            item = self._item(a, WHITE, C_GUI)
            item.move_to(content + UP * (1.5 - i * 0.42))
            ag.add(item)
        per = max(0.3, (176.0 - t) / len(arch) - 0.3)
        for item in ag:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 178.0, t)
        self.play(FadeOut(arch_title), FadeOut(ag), run_time=0.3); t += 0.3

        # ── Testing (179-202s) ───────────────────────────────────
        ts_title = Text("Testing Story", font_size=16, color=C_PR)
        ts_title.move_to(content + UP * 2.3)
        self.play(FadeIn(ts_title), run_time=0.3); t += 0.3
        tests = ["Flask pytest: 50+ tests, mocked K8s responses",
                 "Playwright E2E: 69 tests, every view + action",
                 "Newman API: REST contract vs live backend"]
        tsg = VGroup()
        for i, item_t in enumerate(tests):
            item = self._item(item_t, WHITE, C_PR)
            item.move_to(content + UP * (1.2 - i * 0.45))
            tsg.add(item)
        per = max(0.4, (199.0 - t) / len(tests) - 0.5)
        for item in tsg:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.4); t += 0.4
            t = _wait_until(self, t + per, t)
        t = _wait_until(self, 201.0, t)
        self.play(FadeOut(ts_title), FadeOut(tsg), run_time=0.3); t += 0.3

        # ── Closing (201-210s) ───────────────────────────────────
        closing = Text("One interface | Team-scoped | Cluster-safe | Fully tested",
                       font_size=14, color=C_GUI)
        closing.move_to(content)
        self.play(FadeIn(closing), run_time=0.5); t += 0.5
        t = _wait_until(self, 208.0, t)
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0); t += 1.0

# ═════════════════════════════════════════════════════════════════════
# Segment 17 — Extending the GUI (REWRITE)
# ═════════════════════════════════════════════════════════════════════
class GUIExtensionPatternScene(Scene):
    """~155s scene synced to 17-extending-gui Whisper timing."""

    def _code_line(self, txt, color=GREY_B):
        return Text(txt, font_size=10, color=color, font="Monospace")

    def _step_detail(self, txt, color=GREY_B, icon_color=None):
        ic = Text("›", font_size=13, color=icon_color or color)
        tx = Text(txt, font_size=10, color=color)
        tx.next_to(ic, RIGHT, buff=0.12)
        return VGroup(ic, tx)

    def construct(self):
        self.camera.background_color = C_BG
        t = 0.0

        # ── Intro (0-12s) ────────────────────────────────────────
        title = Text("Extending the GUI", font_size=30, color=WHITE)
        sub = Text("Five steps — one pattern", font_size=16, color=GREY_B)
        sub.next_to(title, DOWN, buff=0.25)
        tg = VGroup(title, sub).move_to(ORIGIN)
        self.play(FadeIn(tg), run_time=0.8)
        t += 0.8

        example_hint = Text(
            "Example: TaskRun Logs panel", font_size=13, color=C_GUI,
        )
        example_hint.next_to(sub, DOWN, buff=0.35)
        t = _wait_until(self, 5.0, t)
        self.play(FadeIn(example_hint, shift=UP * 0.15), run_time=0.5)
        t += 0.5
        t = _wait_until(self, 7.5, t)
        self.play(
            tg.animate.scale(0.55).to_edge(UP, buff=0.2),
            FadeOut(example_hint),
            run_time=0.6,
        )
        t += 0.6

        # ── Step overview strip (8-13s) ──────────────────────────
        step_data = [
            ("1. Flask\nroute", C_FLASK),
            ("2. pytest", C_PR),
            ("3. Pinia\nstore", C_VUE),
            ("4. Vue\nview", C_VUE),
            ("5. Playwright\nspec", C_PR),
        ]
        step_boxes = VGroup()
        for i, (slabel, scolor) in enumerate(step_data):
            sb = _hc_box(slabel, scolor, w=1.7, h=0.8, fs=10)
            sb.move_to(RIGHT * (-4.4 + i * 2.2) + UP * 2.2)
            step_boxes.add(sb)

        self.play(
            LaggedStart(*[FadeIn(sb, shift=DOWN * 0.12) for sb in step_boxes],
                        lag_ratio=0.15),
            run_time=1.5,
        )
        t += 1.5
        t = _wait_until(self, 13.0, t)

        # Helper to highlight active step
        def _hl_step(idx):
            anims = []
            for j, sb in enumerate(step_boxes):
                anims.append(sb.animate.set_opacity(1.0 if j == idx else 0.45))
            self.play(*anims, run_time=0.35)
            return 0.35

        detail_y = DOWN * 0.2

        # ── STEP 1: Flask route (13-44s) ─────────────────────────
        t += _hl_step(0)

        s1_title = Text("Step 1 — Flask Route", font_size=16, color=C_FLASK, weight=BOLD)
        s1_title.move_to(detail_y + UP * 1.3)
        self.play(FadeIn(s1_title, shift=LEFT * 0.2), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 15.5, t)

        route = self._code_line("/api/teams/{team}/taskruns/{name}/logs", C_FLASK)
        route.move_to(detail_y + UP * 1.1)
        self.play(FadeIn(route), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 23.5, t)

        s1_items = [
            "Kubernetes Python client → pod logs API",
            "Stream output as JSON: {logs: [{ts, line}]}",
            "Same error handling: catch ApiException → HTTP status",
        ]
        s1_group = VGroup()
        for i, si in enumerate(s1_items):
            item = self._step_detail(si, WHITE, C_FLASK)
            item.move_to(detail_y + UP * (0.3 - i * 0.45) + LEFT * 1.5)
            s1_group.add(item)

        per = max(0.3, (42.0 - t) / len(s1_items) - 0.5)
        for item in s1_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.4)
            t += 0.4
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 44.0, t)
        self.play(FadeOut(s1_title), FadeOut(route), FadeOut(s1_group), run_time=0.35)
        t += 0.35

        # ── STEP 2: pytest (44-67s) ──────────────────────────────
        t += _hl_step(1)

        s2_title = Text("Step 2 — pytest Coverage", font_size=16, color=C_PR, weight=BOLD)
        s2_title.move_to(detail_y + UP * 1.3)
        self.play(FadeIn(s2_title, shift=LEFT * 0.2), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 47.0, t)

        s2_items = [
            "Mock read_namespaced_pod_log",
            "Verify JSON shape: {logs: [{ts, line}]}",
            "404 for missing task runs",
            "Graceful cluster error handling",
            "Fixtures: test client + mock k8s config",
        ]
        s2_group = VGroup()
        for i, si in enumerate(s2_items):
            item = self._step_detail(si, WHITE, C_PR)
            item.move_to(detail_y + UP * (1.0 - i * 0.42) + LEFT * 1.5)
            s2_group.add(item)

        per = max(0.3, (65.0 - t) / len(s2_items) - 0.4)
        for item in s2_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35)
            t += 0.35
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 66.5, t)
        self.play(FadeOut(s2_title), FadeOut(s2_group), run_time=0.35)
        t += 0.35

        # ── STEP 3: Pinia store (67-86s) ─────────────────────────
        t += _hl_step(2)

        s3_title = Text("Step 3 — Pinia Store", font_size=16, color=C_VUE, weight=BOLD)
        s3_title.move_to(detail_y + UP * 1.3)
        self.play(FadeIn(s3_title, shift=LEFT * 0.2), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 70.5, t)

        s3_items = [
            "useTaskRunLogs composable",
            "Calls API helper with team-scoped URL",
            "Manages: loading · error · logs[]",
            "Reuses useApiHelper + team URL utilities",
            "Team switcher works automatically",
        ]
        s3_group = VGroup()
        for i, si in enumerate(s3_items):
            item = self._step_detail(si, WHITE, C_VUE)
            item.move_to(detail_y + UP * (1.0 - i * 0.42) + LEFT * 1.5)
            s3_group.add(item)

        per = max(0.3, (85.0 - t) / len(s3_items) - 0.4)
        for item in s3_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35)
            t += 0.35
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 87.0, t)
        self.play(FadeOut(s3_title), FadeOut(s3_group), run_time=0.35)
        t += 0.35

        # ── STEP 4: Vue component + router (87-105s) ─────────────
        t += _hl_step(3)

        s4_title = Text("Step 4 — Vue Component + Router", font_size=16, color=C_VUE, weight=BOLD)
        s4_title.move_to(detail_y + UP * 1.3)
        self.play(FadeIn(s4_title, shift=LEFT * 0.2), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 91.0, t)

        s4_items = [
            "TaskRunLogs view: monospace + auto-scroll",
            "Route param: taskRunName",
            "Router config entry",
            "Sidebar / run-detail navigation link",
        ]
        s4_group = VGroup()
        for i, si in enumerate(s4_items):
            item = self._step_detail(si, WHITE, C_VUE)
            item.move_to(detail_y + UP * (0.8 - i * 0.45) + LEFT * 1.5)
            s4_group.add(item)

        per = max(0.3, (104.0 - t) / len(s4_items) - 0.4)
        for item in s4_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35)
            t += 0.35
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 104.5, t)
        self.play(FadeOut(s4_title), FadeOut(s4_group), run_time=0.35)
        t += 0.35

        # ── STEP 5: Playwright spec (105-120s) ───────────────────
        t += _hl_step(4)

        s5_title = Text("Step 5 — Playwright Spec", font_size=16, color=C_PR, weight=BOLD)
        s5_title.move_to(detail_y + UP * 1.3)
        self.play(FadeIn(s5_title, shift=LEFT * 0.2), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 107.0, t)

        s5_items = [
            "Navigate to pipeline run",
            "Click into task run",
            "Verify logs panel renders",
            "Check log lines appear",
            "Page-object pattern + test fixtures",
        ]
        s5_group = VGroup()
        for i, si in enumerate(s5_items):
            item = self._step_detail(si, WHITE, C_PR)
            item.move_to(detail_y + UP * (1.0 - i * 0.42) + LEFT * 1.5)
            s5_group.add(item)

        per = max(0.3, (119.0 - t) / len(s5_items) - 0.4)
        for item in s5_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35)
            t += 0.35
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 120.0, t)
        self.play(FadeOut(s5_title), FadeOut(s5_group), run_time=0.35)
        t += 0.35

        # ── Summary: five files, one pattern (120-144s) ──────────
        # Restore all steps to full opacity
        self.play(*[sb.animate.set_opacity(1.0) for sb in step_boxes], run_time=0.4)
        t += 0.4
        t = _wait_until(self, 122.0, t)

        summary_items = [
            ("Flask route", "wraps the cluster API", C_FLASK),
            ("pytest", "verifies the contract", C_PR),
            ("Pinia store", "manages client state", C_VUE),
            ("Vue component", "renders the UI", C_VUE),
            ("Playwright", "proves it end-to-end", C_PR),
        ]
        sum_group = VGroup()
        for i, (sl, sd, sc) in enumerate(summary_items):
            label = Text(sl, font_size=11, color=sc, weight=BOLD)
            desc = Text(f"→ {sd}", font_size=10, color=GREY_B)
            label.move_to(detail_y + UP * (0.8 - i * 0.4) + LEFT * 2.0)
            desc.next_to(label, RIGHT, buff=0.2)
            sum_group.add(VGroup(label, desc))

        per = max(0.3, (133.0 - t) / len(summary_items) - 0.4)
        for item in sum_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.35)
            t += 0.35
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 133.5, t)

        # ── Scales to any surface (134-155s) ─────────────────────
        scales = Text("This pattern scales to any Tekton surface:", font_size=13, color=C_ORCH)
        scales.move_to(detail_y + DOWN * 1.5)
        self.play(FadeIn(scales), run_time=0.4)
        t += 0.4
        t = _wait_until(self, 137.0, t)

        ideas = [
            "Results read-only views",
            "Cluster event streams",
            "Resource quota dashboards",
            "Webhook configuration panels",
        ]
        ideas_group = VGroup()
        for i, idea in enumerate(ideas):
            item = self._step_detail(idea, GREY_B, C_ORCH)
            item.move_to(detail_y + DOWN * (2.1 + i * 0.38) + LEFT * 1.0)
            ideas_group.add(item)

        per = max(0.3, (148.0 - t) / len(ideas) - 0.3)
        for item in ideas_group:
            self.play(FadeIn(item, shift=RIGHT * 0.1), run_time=0.3)
            t += 0.3
            t = _wait_until(self, t + per, t)

        t = _wait_until(self, 151.5, t)

        closing = Text(
            "Five steps · One pattern · Unlimited extensibility",
            font_size=15, color=C_PR,
        )
        closing.to_edge(DOWN, buff=0.3)
        self.play(FadeIn(closing), run_time=0.5)
        t += 0.5
        t = _wait_until(self, 153.5, t)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0)
        t += 1.0


# ═════════════════════════════════════════════════════════════════════
# Segment 18 — Roadmap / What's Coming Next (NEW)
# ═════════════════════════════════════════════════════════════════════
class RoadmapScene(Scene):
    """~315s scene synced to 18-roadmap Whisper timing (7 pillars).

    Layout rules:
    - Pillar strip sits at a fixed Y (STRIP_Y) — never moves.
    - CONTENT_TOP is the Y coordinate just below the strip where pillar
      titles appear.  All detail content is placed relative to the title
      using next_to / arrange — **never** with absolute Y math.
    - Font sizes: titles 24, section headings 20, body 16, subtitle 14.
    - Render at 1080p30 for sharp text.
    """

    STRIP_Y   = 3.0          # y-centre of the pillar nav strip
    CONTENT_TOP = 1.8         # y-centre of each pillar title

    # ── reusable builders ────────────────────────────────────────

    def _pillar_card(self, label, color, num):
        bg = RoundedRectangle(
            corner_radius=0.15, width=1.65, height=0.6,
            stroke_color=color, fill_color=color, fill_opacity=0.25,
        )
        n = Text(str(num), font_size=18, color=WHITE)
        n.move_to(bg.get_left() + RIGHT * 0.25)
        t = Text(label, font_size=15, color=WHITE)
        t.move_to(bg.get_center() + RIGHT * 0.15)
        return VGroup(bg, n, t)

    def _bullet(self, txt, color=WHITE, accent=None):
        """Single bullet item — icon + text, arranged with next_to."""
        ic = Text("›", font_size=20, color=accent or color)
        tx = Text(txt, font_size=16, color=color)
        tx.next_to(ic, RIGHT, buff=0.15)
        return VGroup(ic, tx)

    def _bullet_list(self, items, color=WHITE, accent=None):
        """Build a VGroup of bullets stacked with arrange(DOWN)."""
        rows = VGroup()
        for txt in items:
            rows.add(self._bullet(txt, color=color, accent=accent))
        rows.arrange(DOWN, buff=0.25, aligned_edge=LEFT)
        return rows

    def _kv_list(self, pairs, key_color=WHITE, val_color=GREY_B):
        """Key-value rows: emphasized key + lighter description."""
        rows = VGroup()
        for k, v in pairs:
            kk = Text(k, font_size=18, color=key_color)
            vv = Text(v, font_size=15, color=val_color)
            vv.next_to(kk, RIGHT, buff=0.2)
            rows.add(VGroup(kk, vv))
        rows.arrange(DOWN, buff=0.3, aligned_edge=LEFT)
        return rows

    def _flow_box(self, label, color):
        bg = RoundedRectangle(
            corner_radius=0.15, width=2.2, height=0.85,
            stroke_color=color, fill_color=color, fill_opacity=0.25,
        )
        t = Text(label, font_size=16, color=WHITE)
        t.move_to(bg.get_center())
        return VGroup(bg, t)

    # ── pillar section helper ────────────────────────────────────

    def _show_pillar(self, pillar_idx, title_text, title_color,
                     overview_cards, t):
        """Highlight card, show title, return (title_mob, t)."""
        anims = []
        for j, c in enumerate(overview_cards):
            anims.append(c.animate.set_opacity(1.0 if j == pillar_idx else 0.4))
        self.play(*anims, run_time=0.4)
        t += 0.4

        title = Text(title_text, font_size=24, color=title_color)
        title.move_to(UP * self.CONTENT_TOP)
        self.play(FadeIn(title, shift=LEFT * 0.2), run_time=0.5)
        t += 0.5
        return title, t

    def _add_subtitle(self, txt, anchor, t):
        """Place a grey subtitle just below *anchor* using next_to."""
        sub = Text(txt, font_size=16, color=GREY_B)
        sub.next_to(anchor, DOWN, buff=0.25)
        self.play(FadeIn(sub), run_time=0.4)
        return sub, t + 0.4

    def _reveal_list(self, grp, anchor, t, end_t):
        """Position *grp* below *anchor*, reveal items one-by-one, paced to end_t."""
        grp.next_to(anchor, DOWN, buff=0.3)
        per = max(0.3, (end_t - t) / len(grp) - 0.5)
        for item in grp:
            self.play(FadeIn(item, shift=RIGHT * 0.15), run_time=0.4)
            t += 0.4
            t = _wait_until(self, t + per, t)
        return t

    def _clear(self, *mobs, t=0):
        flat = [m for m in mobs if m is not None]
        if flat:
            self.play(*[FadeOut(m) for m in flat], run_time=0.4)
        return t + 0.4

    # ── main construct ───────────────────────────────────────────

    def construct(self):
        self.camera.background_color = C_BG
        Text.set_default(font="Liberation Sans")
        t = 0.0

        # ── Intro (0-12s) ───────────────────────────────────────
        title = Text("What's Coming Next", font_size=36, color=WHITE)
        sub = Text("Milestone 13 — Production Hardening", font_size=20, color=C_ORCH)
        sub.next_to(title, DOWN, buff=0.3)
        tg = VGroup(title, sub).move_to(ORIGIN)
        self.play(FadeIn(tg), run_time=0.8); t += 0.8

        tagline = Text("Build · Test · Intercept · Merge · Release",
                        font_size=16, color=GREY_B)
        tagline.next_to(sub, DOWN, buff=0.4)
        t = _wait_until(self, 4.0, t)
        self.play(FadeIn(tagline, shift=UP * 0.15), run_time=0.6); t += 0.6

        t = _wait_until(self, 7.5, t)
        self.play(
            tg.animate.scale(0.5).to_edge(UP, buff=0.15),
            FadeOut(tagline),
            run_time=0.6,
        ); t += 0.6

        # ── Overview strip: 7 pillar cards ──────────────────────
        pillar_data = [
            ("Retry",        C_WARN),
            ("Sizing",       C_SPRING),
            ("Multi-Cluster",C_PROD),
            ("Reliability",  C_PIPE),
            ("Observability",C_NEO4J),
            ("Secrets",      "#E06C75"),
            ("Config",       "#61AFEF"),
        ]
        overview_cards = VGroup()
        for i, (lbl, col) in enumerate(pillar_data):
            overview_cards.add(self._pillar_card(lbl, col, i + 1))
        overview_cards.arrange(RIGHT, buff=0.15)
        overview_cards.move_to(UP * self.STRIP_Y)

        self.play(
            LaggedStart(*[FadeIn(c, shift=UP * 0.12) for c in overview_cards],
                        lag_ratio=0.08),
            run_time=1.5,
        ); t += 1.5
        t = _wait_until(self, 13.0, t)

        # ═══ PILLAR 1 — Retry (14-58s) ═════════════════════════
        t = _wait_until(self, 14.0, t)
        p_title, t = self._show_pillar(0, "Retry on Transient Failures",
                                       C_WARN, overview_cards, t)

        t = _wait_until(self, 18.0, t)
        problems = self._bullet_list([
            "Spot node eviction mid-build",
            "Registry push timeout",
            "DNS lookup failure during burst",
        ], color=C_WARN, accent=RED)
        t = self._reveal_list(problems, p_title, t, 30.0)

        t = _wait_until(self, 34.0, t)
        noise, t = self._add_subtitle("Infrastructure noise — not code bugs", problems, t)

        t = _wait_until(self, 37.0, t)
        strategy = self._bullet_list([
            "Task-level retries: build, deploy, containerize",
            "Test tasks: NO retry (real signal)",
            "Eviction vs application exit codes",
            "Structured retry annotations per TaskRun",
        ], color=WHITE, accent=C_WARN)
        t = self._reveal_list(strategy, noise, t, 56.0)

        t = _wait_until(self, 58.0, t)
        t = self._clear(p_title, problems, noise, strategy, t=t)

        # ═══ PILLAR 2 — Sizing (59-99s) ════════════════════════
        t = _wait_until(self, 59.0, t)
        p_title, t = self._show_pillar(1, "Precise Build Image Sizing",
                                       C_SPRING, overview_cards, t)

        t = _wait_until(self, 63.0, t)
        problems = self._bullet_list([
            "Maven requests 4 GB — needs 1 GB",
            "Spring Boot monolith → OOM killed",
            "Default resources → wasted capacity",
        ], color=RED, accent=RED)
        t = self._reveal_list(problems, p_title, t, 74.0)

        t = _wait_until(self, 76.0, t)
        solutions = self._bullet_list([
            "Per-tool resource profiles via Helm",
            "Maven ≠ NPM ≠ Kaniko sizing",
            "stack.yaml per-app overrides",
            "Monitoring baseline: peak usage capture",
        ], color=WHITE, accent=C_SPRING)
        t = self._reveal_list(solutions, problems, t, 97.0)

        t = _wait_until(self, 99.0, t)
        t = self._clear(p_title, problems, solutions, t=t)

        # ═══ PILLAR 3 — Multi-Cluster (100-147s) ═══════════════
        t = _wait_until(self, 100.0, t)
        p_title, t = self._show_pillar(2, "Multi-Cluster Push",
                                       C_PROD, overview_cards, t)

        t = _wait_until(self, 104.0, t)
        single, t = self._add_subtitle(
            "Today: single-cluster build + deploy", p_title, t)

        t = _wait_until(self, 110.0, t)
        flow_labels = ["Registry\nList", "Promotion\nPipeline",
                       "Approval\nGate", "Deploy\nTarget"]
        flow_colors = [C_PROD, C_PIPE, C_WARN, C_SPRING]
        boxes = VGroup()
        for lbl, col in zip(flow_labels, flow_colors):
            boxes.add(self._flow_box(lbl, col))

        arrows_g = VGroup()
        flow_row = VGroup()
        for i, bx in enumerate(boxes):
            flow_row.add(bx)
            if i < len(boxes) - 1:
                ar = Arrow(ORIGIN, RIGHT * 0.6, color=GREY_B, stroke_width=3,
                           buff=0, max_tip_length_to_length_ratio=0.3)
                flow_row.add(ar)
                arrows_g.add(ar)
        flow_row.arrange(RIGHT, buff=0.12)
        flow_row.next_to(single, DOWN, buff=0.4)

        per_box = max(0.3, (128.0 - t) / len(boxes) - 0.8)
        for i, bx in enumerate(boxes):
            self.play(FadeIn(bx, shift=RIGHT * 0.15), run_time=0.5); t += 0.5
            if i < len(arrows_g):
                self.play(GrowArrow(arrows_g[i]), run_time=0.3); t += 0.3
            t = _wait_until(self, t + per_box, t)

        t = _wait_until(self, 131.0, t)
        audit = self._bullet_list([
            "Manual sign-off or /approve on PR",
            "Management GUI approval button",
            "Recorded in Tekton Results (audit trail)",
        ], color=WHITE, accent=C_PROD)
        t = self._reveal_list(audit, flow_row, t, 145.0)

        t = _wait_until(self, 147.0, t)
        t = self._clear(p_title, single, flow_row, audit, t=t)

        # ═══ PILLAR 4 — Reliability (148-173s) ═════════════════
        t = _wait_until(self, 148.0, t)
        p_title, t = self._show_pillar(3, "Operational Reliability",
                                       C_PIPE, overview_cards, t)

        t = _wait_until(self, 151.0, t)
        rel = self._kv_list([
            ("Pipeline timeouts",      "No infinite hangs"),
            ("finally block on timeout","Intercept cleanup + PR status"),
            ("Health-check gates",     "Pod readiness before tests"),
            ("DB backup scripts",      "Postgres + Neo4j"),
        ], key_color=C_PIPE, val_color=GREY_B)
        t = self._reveal_list(rel, p_title, t, 171.0)

        t = _wait_until(self, 173.0, t)
        t = self._clear(p_title, rel, t=t)

        # ═══ PILLAR 5 — Observability (174-204s) ═══════════════
        t = _wait_until(self, 174.0, t)
        p_title, t = self._show_pillar(4, "Observability",
                                       C_NEO4J, overview_cards, t)

        t = _wait_until(self, 177.0, t)
        metrics = self._bullet_list([
            "Build duration per tool",
            "Test pass rate",
            "Retry count",
            "Pipeline queue time",
        ], color=WHITE, accent=C_NEO4J)
        t = self._reveal_list(metrics, p_title, t, 185.0)

        t = _wait_until(self, 186.0, t)
        alerts = self._bullet_list([
            "Alert on failure rate threshold",
            "Alert on registry push failures",
        ], color=C_WARN, accent=RED)
        t = self._reveal_list(alerts, metrics, t, 191.0)

        t = _wait_until(self, 191.0, t)
        costs = self._bullet_list([
            "Labels: team · stack · app",
            "KubeCost / OpenCost integration",
            "Per-pipeline cost visibility",
        ], color=WHITE, accent=C_NEO4J)
        t = self._reveal_list(costs, alerts, t, 202.0)

        t = _wait_until(self, 204.0, t)
        t = self._clear(p_title, metrics, alerts, costs, t=t)

        # ═══ PILLAR 6 — Secrets (205-256s) ══════════════════════
        t = _wait_until(self, 205.0, t)
        p_title, t = self._show_pillar(5, "Secrets Injection",
                                       "#E06C75", overview_cards, t)

        t = _wait_until(self, 208.0, t)
        prob, t = self._add_subtitle(
            "Today: bare Deployments — no secrets, no env vars", p_title, t)

        t = _wait_until(self, 214.0, t)
        stack_sec = self._bullet_list([
            "stack YAML secrets block per app",
            "env-from → envFrom secretRef",
            "volume-mounts → TLS certs, key files",
            "Deploy task wires into pod spec",
        ], color=WHITE, accent="#E06C75")
        t = self._reveal_list(stack_sec, prob, t, 234.0)

        t = _wait_until(self, 235.0, t)
        providers = self._bullet_list([
            "External Secrets Operator (ESO)",
            "AWS SM / Vault / Azure KV",
            "SecretStore per team namespace",
            "Pre-deploy validation: fail fast",
        ], color=WHITE, accent="#E06C75")
        t = self._reveal_list(providers, stack_sec, t, 255.0)

        t = _wait_until(self, 256.0, t)
        t = self._clear(p_title, prob, stack_sec, providers, t=t)

        # ═══ PILLAR 7 — Config (257-302s) ══════════════════════
        t = _wait_until(self, 257.0, t)
        p_title, t = self._show_pillar(6, "Per-App Config per Environment",
                                       "#61AFEF", overview_cards, t)

        t = _wait_until(self, 260.0, t)
        need, t = self._add_subtitle(
            "DB URLs · feature flags · log levels · endpoints", p_title, t)

        t = _wait_until(self, 268.0, t)
        cfg = self._bullet_list([
            "stack YAML config block",
            "Helm templates → ConfigMap per app",
            "appConfig map in values.yaml",
        ], color=WHITE, accent="#61AFEF")
        t = self._reveal_list(cfg, need, t, 282.0)

        t = _wait_until(self, 283.0, t)
        envs = self._bullet_list([
            "values-local / values-staging / values-prod",
            "helm upgrade -f values-staging.yaml",
            ".env.<app> for local dev → ConfigMap",
            "Config validation hook pre-deploy",
        ], color=WHITE, accent="#61AFEF")
        t = self._reveal_list(envs, cfg, t, 300.0)

        t = _wait_until(self, 301.0, t)
        t = self._clear(p_title, need, cfg, envs, t=t)

        # ── Closing (302-315s) ──────────────────────────────────
        t = _wait_until(self, 302.0, t)
        self.play(*[c.animate.set_opacity(1.0) for c in overview_cards],
                  run_time=0.5); t += 0.5

        closing = Text(
            "Reliable · Cost-aware · Multi-env · Observable · Secure · Configurable",
            font_size=18, color=C_PR,
        )
        closing.move_to(DOWN * 0.5)
        m13 = Text("Milestone 13 — Production Hardening",
                    font_size=22, color=C_ORCH)
        m13.next_to(closing, DOWN, buff=0.35)

        self.play(FadeIn(closing), run_time=0.5); t += 0.5
        t = _wait_until(self, 310.0, t)
        self.play(FadeIn(m13), run_time=0.5); t += 0.5
        t = _wait_until(self, 313.0, t)

        self.play(*[FadeOut(m) for m in self.mobjects], run_time=1.0); t += 1.0
