"""
Manim scenes for tekton-dag demo videos.
Each scene is timed to its narration audio (paragraph-by-paragraph).

Render all:
    cd docs/demos/animations
    manim -qm scenes.py StackDAGScene
    manim -qm scenes.py HeaderPropagationScene
    manim -qm scenes.py InterceptRoutingScene
    manim -qm scenes.py LocalDebugScene
    manim -qm scenes.py MultiTeamScene
    manim -qm scenes.py BlastRadiusScene
"""

from manim import *

# ── Colour palette ───────────────────────────────────────────────────
C_VUE = "#42b883"
C_SPRING = "#6db33f"
C_SPRING_DARK = "#4a7c2e"
C_FLASK = "#3776ab"
C_PHP = "#777bb3"
C_PIPELINE = "#1a73e8"
C_ORCH = "#f9a825"
C_PR = "#00c853"
C_PROD = "#2979ff"
C_WARN = "#ff5252"
C_NEO4J = "#008cc1"
C_HELM = "#0f1689"
C_BG = "#1e1e2e"
C_HOOK = "#ce93d8"
C_GUI = "#26c6da"


def _box(label, color, width=2.2, height=0.9, font_size=20):
    rect = RoundedRectangle(
        corner_radius=0.15, width=width, height=height,
        stroke_color=color, fill_color=color, fill_opacity=0.12,
    )
    txt = Text(label, font_size=font_size, color=color)
    return VGroup(rect, txt)


def _diamond(label, color, size=0.55, font_size=13):
    sq = Square(side_length=size, color=color, fill_opacity=0.15)
    sq.rotate(PI / 4)
    txt = Text(label, font_size=font_size, color=color)
    return VGroup(sq, txt)


def _arrow(start, end, color=WHITE, buff=0.3):
    return Arrow(
        start.get_center(), end.get_center(),
        buff=buff, color=color, stroke_width=2, max_tip_length_to_length_ratio=0.12,
    )


def _badge(label, color, font_size=14):
    txt = Text(label, font_size=font_size, color=color)
    box = SurroundingRectangle(txt, buff=0.08, color=color, corner_radius=0.06,
                                fill_color=color, fill_opacity=0.1)
    return VGroup(box, txt)


# ═════════════════════════════════════════════════════════════════════
# Scene 1: Architecture overview — synced to 01-architecture.mp3
# Total: 160.5s
# ═════════════════════════════════════════════════════════════════════
class StackDAGScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG

        # ── P1 (0–5s): Title ────────────────────────────────────────
        title = Text("tekton-dag", font_size=40, color=WHITE)
        subtitle = Text("Stack-Aware CI/CD with Traffic Interception",
                        font_size=18, color=GREY)
        subtitle.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(title, shift=UP * 0.3), run_time=1.5)
        self.play(FadeIn(subtitle), run_time=1)
        self.wait(2.5)

        # ── P2 (5–27.8s): DAG concept — nodes + edges ──────────────
        self.play(FadeOut(title), FadeOut(subtitle), run_time=1)

        dag_title = Text("Directed Acyclic Graph — the core model",
                         font_size=18, color=GREY).to_edge(UP, buff=0.4)
        self.play(FadeIn(dag_title), run_time=0.8)

        fe = _box("demo-fe\n(Vue)", C_VUE)
        bff = _box("BFF\n(Spring Boot)", C_SPRING)
        api = _box("demo-api\n(Spring Boot)", C_SPRING_DARK)
        fe.move_to(LEFT * 4.5 + UP * 1.8)
        bff.move_to(ORIGIN + UP * 1.8)
        api.move_to(RIGHT * 4.5 + UP * 1.8)

        self.play(FadeIn(fe), run_time=1.5)
        self.wait(2)
        self.play(FadeIn(bff), run_time=1.5)
        self.wait(2)
        self.play(FadeIn(api), run_time=1.5)

        e1 = _arrow(fe, bff, C_VUE)
        e2 = _arrow(bff, api, C_SPRING)
        dep1 = Text("downstream", font_size=11, color=GREY_B).next_to(e1, UP, buff=0.08)
        dep2 = Text("downstream", font_size=11, color=GREY_B).next_to(e2, UP, buff=0.08)
        self.play(Create(e1), FadeIn(dep1), run_time=1.2)
        self.play(Create(e2), FadeIn(dep2), run_time=1.2)

        roles = VGroup(
            Text("originator", font_size=13, color=C_VUE).next_to(fe, DOWN, buff=0.2),
            Text("forwarder", font_size=13, color=C_SPRING).next_to(bff, DOWN, buff=0.2),
            Text("terminal", font_size=13, color=C_SPRING_DARK).next_to(api, DOWN, buff=0.2),
        )
        self.play(*[FadeIn(r) for r in roles], run_time=1)
        self.wait(8)

        # ── P3 (27.8–47s): Orchestrator + webhook ──────────────────
        orch = _box("Orchestrator\n(Flask :8080)", C_ORCH, width=2.6, height=1.0, font_size=17)
        orch.move_to(LEFT * 5 + DOWN * 1.5)

        wh_start = LEFT * 6.8 + DOWN * 1.5
        wh_arrow = Arrow(wh_start, orch.get_left(), buff=0.15,
                         color=C_ORCH, stroke_width=2.5)
        wh_label = Text("GitHub\nwebhook", font_size=12, color=C_ORCH)
        wh_label.next_to(wh_arrow, UP, buff=0.1)

        self.play(FadeIn(orch), run_time=1.5)
        self.play(Create(wh_arrow), FadeIn(wh_label), run_time=1.2)
        self.wait(3)

        run_label = Text("PipelineRun", font_size=12, color=C_ORCH)
        run_arrow = Arrow(orch.get_right() + RIGHT * 0.1, ORIGIN + DOWN * 1.5,
                          buff=0.3, color=C_ORCH, stroke_width=2)
        run_label.next_to(run_arrow, UP, buff=0.08)
        self.play(Create(run_arrow), FadeIn(run_label), run_time=1.2)
        self.wait(10)

        # ── P4 (47–68.5s): Stack detail — roles highlighted ────────
        self.play(
            fe[0].animate.set_fill(C_VUE, opacity=0.35),
            bff[0].animate.set_fill(C_SPRING, opacity=0.35),
            api[0].animate.set_fill(C_SPRING_DARK, opacity=0.35),
            run_time=1.5,
        )

        header_badge = _badge("x-dev-session: pr-42", C_PR, font_size=12)
        header_badge.next_to(bff, UP, buff=0.6)
        self.play(FadeIn(header_badge), run_time=1)
        self.wait(16)
        self.play(FadeOut(header_badge), run_time=0.5)

        # ── P5 (68.5–88.7s): Polyglot badge ────────────────────────
        poly_title = Text("Polyglot — 6 build tools, version matrix",
                          font_size=15, color=GREY).to_edge(DOWN, buff=1.8)

        tools = VGroup(
            _badge("npm", C_VUE, 13),
            _badge("Maven", C_SPRING, 13),
            _badge("Gradle", C_SPRING_DARK, 13),
            _badge("pip", C_FLASK, 13),
            _badge("Composer", C_PHP, 13),
            _badge("mirrord", "#ff9100", 13),
        ).arrange(RIGHT, buff=0.4).next_to(poly_title, DOWN, buff=0.3)

        self.play(FadeIn(poly_title), run_time=0.8)
        self.play(LaggedStart(*[FadeIn(t, shift=UP * 0.2) for t in tools],
                              lag_ratio=0.15), run_time=2)
        self.wait(15)

        # ── P6 (88.7–116.9s): Three pipelines ──────────────────────
        self.play(FadeOut(poly_title), FadeOut(tools), run_time=0.8)

        p_boot = _box("bootstrap", C_PIPELINE, width=2.2, height=0.7, font_size=17)
        p_pr = _box("PR test", C_PIPELINE, width=2.2, height=0.7, font_size=17)
        p_merge = _box("merge", C_PIPELINE, width=2.2, height=0.7, font_size=17)
        pipes = VGroup(p_boot, p_pr, p_merge).arrange(RIGHT, buff=1.2)
        pipes.move_to(DOWN * 1.5)

        pipe_dots = VGroup(*[
            DashedLine(bff.get_bottom() + DOWN * 0.3, p.get_top(),
                       color=GREY_B, dash_length=0.06)
            for p in [p_boot, p_pr, p_merge]
        ])

        self.play(FadeIn(p_boot, shift=UP * 0.2), run_time=1)
        self.wait(4)
        self.play(FadeIn(p_pr, shift=UP * 0.2), run_time=1)
        self.wait(4)
        self.play(FadeIn(p_merge, shift=UP * 0.2), run_time=1)
        self.play(Create(pipe_dots), run_time=1)
        self.wait(14)

        # ── P7 (116.9–132.2s): Custom hooks ────────────────────────
        hooks = VGroup(
            _badge("pre-build", C_HOOK, 11),
            _badge("post-build", C_HOOK, 11),
            _badge("pre-test", C_HOOK, 11),
            _badge("post-test", C_HOOK, 11),
        ).arrange(RIGHT, buff=0.3).next_to(pipes, DOWN, buff=0.5)

        hook_label = Text("Custom pipeline hooks (optional)",
                          font_size=13, color=C_HOOK).next_to(hooks, DOWN, buff=0.15)
        self.play(FadeIn(hooks), FadeIn(hook_label), run_time=1.5)
        self.wait(12)

        # ── P8 (132.2–157.5s): GUI + Results + Neo4j ───────────────
        self.play(FadeOut(hooks), FadeOut(hook_label), run_time=0.6)

        extras = VGroup(
            _badge("Management GUI\n(Vue + Flask)", C_GUI, 12),
            _badge("Tekton Results\n(Postgres)", C_PIPELINE, 12),
            _badge("Test-Trace Graph\n(Neo4j)", C_NEO4J, 12),
            _badge("Helm chart\n(multi-team)", C_HELM, 12),
        ).arrange(RIGHT, buff=0.5).next_to(pipes, DOWN, buff=0.5)

        self.play(LaggedStart(*[FadeIn(e, shift=UP * 0.2) for e in extras],
                              lag_ratio=0.3), run_time=3)
        self.wait(20)

        # ── P9 (157.5–160.5s): Outro ───────────────────────────────
        self.wait(3)


# ═════════════════════════════════════════════════════════════════════
# Scene 2: Header propagation — synced to 03-bootstrap-dataflow.mp3
# Total: 108.4s
# ═════════════════════════════════════════════════════════════════════
class HeaderPropagationScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG

        fe = _box("demo-fe\n(Vue)", C_VUE, width=2.4, height=1.0)
        bff = _box("BFF\n(Spring Boot)", C_SPRING, width=2.4, height=1.0)
        api = _box("demo-api\n(Spring Boot)", C_SPRING_DARK, width=2.4, height=1.0)
        fe.move_to(LEFT * 4.5 + UP * 0.5)
        bff.move_to(ORIGIN + UP * 0.5)
        api.move_to(RIGHT * 4.5 + UP * 0.5)

        e1 = _arrow(fe, bff, GREY_B)
        e2 = _arrow(bff, api, GREY_B)

        # ── P1 (0–4s): Intro ───────────────────────────────────────
        intro = Text("Bootstrap & Data Flow", font_size=28, color=WHITE)
        self.play(FadeIn(intro), run_time=1)
        self.wait(2)
        self.play(FadeOut(intro), run_time=0.5)

        # ── P2 (4–28.1s): Bootstrap pipeline running ───────────────
        self.play(FadeIn(fe), FadeIn(bff), FadeIn(api), run_time=1)
        self.play(Create(e1), Create(e2), run_time=1)

        stages = [
            "resolve-stack → parse DAG",
            "clone-app-repos → 3 repos",
            "compile-npm → demo-fe",
            "compile-maven → BFF, API",
            "containerize → Kaniko → 3 images",
            "deploy-full-stack → Running ✓",
        ]
        stage_text = Text(stages[0], font_size=15, color=C_PIPELINE)
        stage_text.to_edge(DOWN, buff=0.8)
        self.play(FadeIn(stage_text), run_time=0.5)

        for i, s in enumerate(stages[1:], 1):
            self.wait(3)
            new_text = Text(s, font_size=15, color=C_PIPELINE)
            new_text.to_edge(DOWN, buff=0.8)
            self.play(Transform(stage_text, new_text), run_time=0.5)

        self.wait(3)
        self.play(FadeOut(stage_text), run_time=0.5)

        # ── P3 (28.1–53s): Build detail — tools resolve ────────────
        tool_fe = Text("npm", font_size=12, color=C_VUE).next_to(fe, DOWN, buff=0.2)
        tool_bff = Text("maven", font_size=12, color=C_SPRING).next_to(bff, DOWN, buff=0.2)
        tool_api = Text("maven", font_size=12, color=C_SPRING_DARK).next_to(api, DOWN, buff=0.2)
        self.play(FadeIn(tool_fe), FadeIn(tool_bff), FadeIn(tool_api), run_time=1)

        kaniko_lbl = Text("Kaniko → container images → registry",
                          font_size=14, color=GREY).to_edge(DOWN, buff=0.5)
        self.play(FadeIn(kaniko_lbl), run_time=0.8)
        self.wait(6)

        deployed = Text("All 3 pods Running ✓", font_size=16, color=C_PR)
        deployed.to_edge(DOWN, buff=0.5)
        self.play(Transform(kaniko_lbl, deployed), run_time=0.8)
        self.play(
            fe[0].animate.set_fill(C_VUE, opacity=0.3),
            bff[0].animate.set_fill(C_SPRING, opacity=0.3),
            api[0].animate.set_fill(C_SPRING_DARK, opacity=0.3),
            run_time=1,
        )
        self.wait(13)
        self.play(FadeOut(kaniko_lbl), FadeOut(tool_fe), FadeOut(tool_bff),
                  FadeOut(tool_api), run_time=0.5)

        # ── P4 (53–71.8s): Request enters + originator sets header ─
        trace_label = Text("Tracing a request through the stack",
                           font_size=16, color=WHITE).to_edge(UP, buff=0.3)
        self.play(FadeIn(trace_label), run_time=0.8)

        dot = Dot(color=C_PR, radius=0.12).move_to(LEFT * 6.5 + UP * 0.5)
        self.play(FadeIn(dot), run_time=0.5)
        self.play(dot.animate.move_to(fe.get_center()), run_time=1.5)

        header = _badge("x-dev-session: pr-42", C_PR, font_size=12)
        header.next_to(fe, UP, buff=0.4)
        orig_label = Text("originator — sets header", font_size=13, color=C_VUE)
        orig_label.next_to(fe, DOWN, buff=0.25)
        self.play(FadeIn(header), FadeIn(orig_label), run_time=1)
        self.play(fe[0].animate.set_fill(C_VUE, opacity=0.5), run_time=0.5)
        self.wait(12)

        # ── P5 (71.8–89.1s): Forwarder + terminal ──────────────────
        self.play(
            dot.animate.move_to(bff.get_center()),
            header.animate.next_to(bff, UP, buff=0.4),
            run_time=1.5,
        )
        fwd_label = Text("forwarder — reads, stores, propagates",
                         font_size=13, color=C_SPRING)
        fwd_label.next_to(bff, DOWN, buff=0.25)
        self.play(FadeIn(fwd_label), bff[0].animate.set_fill(C_SPRING, opacity=0.5),
                  run_time=0.8)
        self.wait(5)

        self.play(
            dot.animate.move_to(api.get_center()),
            header.animate.next_to(api, UP, buff=0.4),
            run_time=1.5,
        )
        term_label = Text("terminal — header arrived ✓", font_size=13, color=GREEN)
        term_label.next_to(api, DOWN, buff=0.25)
        self.play(FadeIn(term_label), api[0].animate.set_fill(GREEN, opacity=0.3),
                  run_time=0.8)
        self.play(header[0].animate.set_color(GREEN), header[1].animate.set_color(GREEN),
                  run_time=0.5)
        self.wait(6)

        # ── P6 (89.1–108.4s): Normal vs PR ─────────────────────────
        self.play(FadeOut(trace_label), FadeOut(dot), FadeOut(header),
                  FadeOut(orig_label), FadeOut(fwd_label), FadeOut(term_label),
                  run_time=0.8)

        normal = Text("Without header → standard deployments (production)",
                       font_size=15, color=C_PROD)
        normal.move_to(DOWN * 2)
        self.play(FadeIn(normal), run_time=0.8)
        self.wait(5)

        pr_text = Text("With header → PR build receives tagged traffic only",
                       font_size=15, color=C_PR)
        pr_text.next_to(normal, DOWN, buff=0.4)
        self.play(FadeIn(pr_text), run_time=0.8)
        self.wait(10)
        self.wait(2)


# ═════════════════════════════════════════════════════════════════════
# Scene 3: Intercept routing — synced to 05-intercept-routing.mp3
# Total: 123.6s
# ═════════════════════════════════════════════════════════════════════
class InterceptRoutingScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG

        # Layout: stack on top row, PR pod below-right
        fe = _box("demo-fe", C_VUE, width=2, height=0.8, font_size=18)
        bff = _box("BFF", C_SPRING, width=2, height=0.8, font_size=18)
        api = _box("demo-api\n(production)", C_SPRING_DARK, width=2.2, height=0.9, font_size=16)
        fe.move_to(LEFT * 4 + UP * 2)
        bff.move_to(ORIGIN + UP * 2)
        api.move_to(RIGHT * 4 + UP * 2)

        e1 = _arrow(fe, bff, GREY_B, buff=0.25)
        e2 = _arrow(bff, api, GREY_B, buff=0.25)

        pr_pod = _box("demo-api\n(PR-42 build)", C_PR, width=2.2, height=0.9, font_size=16)
        pr_pod.move_to(RIGHT * 4 + DOWN * 1)

        # ── P1 (0–4.3s): Title ─────────────────────────────────────
        title = Text("Intercept Routing: PR vs Normal", font_size=26, color=WHITE)
        self.play(FadeIn(title), run_time=1)
        self.wait(2.5)
        self.play(FadeOut(title), run_time=0.5)

        # ── P2 (4.3–14.5s): Show stack + PR pod ────────────────────
        self.play(FadeIn(fe), FadeIn(bff), FadeIn(api), run_time=1)
        self.play(Create(e1), Create(e2), run_time=0.8)
        self.play(FadeIn(pr_pod), run_time=1)

        legend_blue = Dot(color=C_PROD, radius=0.08).move_to(LEFT * 5.5 + DOWN * 2.5)
        legend_green = Dot(color=C_PR, radius=0.08).move_to(LEFT * 5.5 + DOWN * 3)
        leg_b_text = Text("Normal traffic (no header)", font_size=12, color=C_PROD)
        leg_g_text = Text("PR traffic (x-dev-session: pr-42)", font_size=12, color=C_PR)
        leg_b_text.next_to(legend_blue, RIGHT, buff=0.15)
        leg_g_text.next_to(legend_green, RIGHT, buff=0.15)
        self.play(FadeIn(legend_blue), FadeIn(leg_b_text),
                  FadeIn(legend_green), FadeIn(leg_g_text), run_time=1)
        self.wait(4)

        # ── P3 (14.5–27.7s): Blue dot — normal path ────────────────
        blue = Dot(color=C_PROD, radius=0.14).move_to(LEFT * 6.5 + UP * 2)
        blue_hdr = Text("(no header)", font_size=11, color=C_PROD)
        blue_hdr.next_to(blue, DOWN, buff=0.12)

        self.play(FadeIn(blue), FadeIn(blue_hdr), run_time=0.5)
        self.play(blue.animate.move_to(fe.get_center()),
                  blue_hdr.animate.next_to(fe, DOWN, buff=0.5), run_time=1)
        self.wait(1)
        self.play(blue.animate.move_to(bff.get_center()),
                  blue_hdr.animate.next_to(bff, DOWN, buff=0.5), run_time=1)
        self.wait(1)
        self.play(blue.animate.move_to(api.get_center()),
                  blue_hdr.animate.next_to(api, DOWN, buff=0.5), run_time=1)

        prod_ok = Text("→ production pod ✓", font_size=14, color=C_PROD)
        prod_ok.next_to(api, RIGHT, buff=0.3).shift(UP * 0.3)
        self.play(FadeIn(prod_ok), run_time=0.5)
        self.wait(5)

        # ── P4 (27.7–54.2s): Green dot — PR path with intercept ────
        green = Dot(color=C_PR, radius=0.14).move_to(LEFT * 6.5 + DOWN * 0.5)
        green_hdr = _badge("x-dev-session: pr-42", C_PR, font_size=11)
        green_hdr.next_to(green, DOWN, buff=0.12)

        self.play(FadeIn(green), FadeIn(green_hdr), run_time=0.5)
        self.play(green.animate.move_to(fe.get_center() + DOWN * 0.4),
                  green_hdr.animate.next_to(fe, DOWN, buff=0.8), run_time=1)
        self.wait(2)
        self.play(green.animate.move_to(bff.get_center() + DOWN * 0.4),
                  green_hdr.animate.next_to(bff, DOWN, buff=0.8), run_time=1)
        self.wait(2)

        # Intercept branch
        branch = Arrow(bff.get_center() + DOWN * 0.4, pr_pod.get_left(),
                       buff=0.25, color=C_PR, stroke_width=3)
        intercept_lbl = Text("header match →\nredirect to PR pod", font_size=13, color=C_PR)
        intercept_lbl.next_to(branch, LEFT, buff=0.15)

        backends = Text("(Telepresence or mirrord)", font_size=11, color=GREY)
        backends.next_to(intercept_lbl, DOWN, buff=0.1)

        self.play(Create(branch), FadeIn(intercept_lbl), FadeIn(backends), run_time=1.2)
        self.wait(2)

        self.play(green.animate.move_to(pr_pod.get_center()),
                  green_hdr.animate.next_to(pr_pod, DOWN, buff=0.3), run_time=1)

        pr_ok = Text("→ PR build ✓", font_size=14, color=C_PR)
        pr_ok.next_to(pr_pod, RIGHT, buff=0.3)
        self.play(FadeIn(pr_ok), run_time=0.5)
        self.wait(12)

        # ── P5 (54.2–75.2s): Both coexist ──────────────────────────
        coexist = Text("Same cluster · Same DNS · Same ingress",
                       font_size=16, color=WHITE).move_to(DOWN * 2.5)
        coexist2 = Text("Only the header differs",
                        font_size=14, color=GREY).next_to(coexist, DOWN, buff=0.2)
        self.play(FadeIn(coexist), run_time=0.8)
        self.play(FadeIn(coexist2), run_time=0.6)
        self.wait(16)

        # ── P6 (75.2–97.9s): Validation tasks ──────────────────────
        self.play(FadeOut(coexist), FadeOut(coexist2), run_time=0.5)

        v1 = Text("✓ validate-propagation — header reaches PR pod at every hop",
                   font_size=14, color=C_PR).move_to(DOWN * 2.3)
        self.play(FadeIn(v1), run_time=0.8)
        self.wait(6)

        v2 = Text("✓ validate-original-traffic — requests without header → production",
                   font_size=14, color=C_PROD).next_to(v1, DOWN, buff=0.3)
        self.play(FadeIn(v2), run_time=0.8)
        self.wait(12)

        # ── P7 (97.9–117.6s): Multi-PR + cleanup ───────────────────
        self.play(FadeOut(v1), FadeOut(v2), run_time=0.5)

        multi = VGroup(
            _badge("PR-42", C_PR, 13),
            _badge("PR-43", "#ffab00", 13),
            _badge("PR-44", "#e040fb", 13),
        ).arrange(RIGHT, buff=0.6).move_to(DOWN * 2.5)
        multi_lbl = Text("Multiple concurrent PRs — each isolated by header value",
                         font_size=14, color=GREY).next_to(multi, DOWN, buff=0.2)
        self.play(LaggedStart(*[FadeIn(m) for m in multi], lag_ratio=0.3), run_time=1.5)
        self.play(FadeIn(multi_lbl), run_time=0.6)
        self.wait(8)

        cleanup = Text("Cleanup in finally block → intercept + PR pods removed",
                       font_size=13, color=GREY).next_to(multi_lbl, DOWN, buff=0.25)
        self.play(FadeIn(cleanup), run_time=0.6)
        self.wait(6)

        # ── P8 (117.6–123.6s): Summary ─────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        summary = Text("Same URL · Same infrastructure · Different backend",
                       font_size=22, color=WHITE)
        self.play(FadeIn(summary), run_time=1)
        self.wait(4)


# ═════════════════════════════════════════════════════════════════════
# Scene 4: Local debug with mirrord — synced to 06-local-debug.mp3
# Total: 117.2s
# ═════════════════════════════════════════════════════════════════════
class LocalDebugScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG

        # ── P1 (0–14.8s): Intro ────────────────────────────────────
        title = Text("Local Debugging with mirrord", font_size=28, color=WHITE)
        sub = Text("IDE breakpoints · Live cluster data · No mocks",
                   font_size=15, color=GREY)
        sub.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(title), run_time=1)
        self.play(FadeIn(sub), run_time=0.8)
        self.wait(12)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.8)

        # ── P2 (14.8–31.9s): Split view — laptop vs cluster ───────
        divider = DashedLine(UP * 3.2, DOWN * 2.5, color=GREY_B, dash_length=0.1)
        divider.move_to(ORIGIN)
        self.play(Create(divider), run_time=0.5)

        laptop_lbl = Text("Developer Laptop", font_size=15, color=GREY)
        laptop_lbl.move_to(LEFT * 3.5 + UP * 3)
        cluster_lbl = Text("Kubernetes Cluster", font_size=15, color=GREY)
        cluster_lbl.move_to(RIGHT * 3.5 + UP * 3)
        self.play(FadeIn(laptop_lbl), FadeIn(cluster_lbl), run_time=0.5)

        ide = _box("IDE\n(breakpoint ready)", "#e91e63", width=3, height=1.3, font_size=17)
        ide.move_to(LEFT * 3.5 + UP * 0.8)
        self.play(FadeIn(ide), run_time=1)

        fe_pod = _box("demo-fe", C_VUE, width=1.8, height=0.6, font_size=14)
        bff_pod = _box("BFF", C_SPRING, width=1.8, height=0.6, font_size=14)
        api_pod = _box("demo-api", C_SPRING_DARK, width=1.8, height=0.6, font_size=14)
        fe_pod.move_to(RIGHT * 3.5 + UP * 1.8)
        bff_pod.move_to(RIGHT * 3.5 + UP * 0.7)
        api_pod.move_to(RIGHT * 3.5 + DOWN * 0.4)
        self.play(FadeIn(fe_pod), FadeIn(bff_pod), FadeIn(api_pod), run_time=1)

        pod_arrows = VGroup(
            Arrow(fe_pod.get_bottom(), bff_pod.get_top(), buff=0.1,
                  color=GREY_B, stroke_width=1.5),
            Arrow(bff_pod.get_bottom(), api_pod.get_top(), buff=0.1,
                  color=GREY_B, stroke_width=1.5),
        )
        self.play(Create(pod_arrows), run_time=0.6)
        self.wait(10)

        # ── P3 (31.9–47.9s): mirrord tunnel ────────────────────────
        tunnel = Arrow(api_pod.get_left(), ide.get_right(),
                       buff=0.3, color="#ff9100", stroke_width=3.5)
        tunnel_lbl = Text("mirrord tunnel", font_size=14, color="#ff9100")
        tunnel_lbl.next_to(tunnel, DOWN, buff=0.15)
        self.play(Create(tunnel), run_time=1.5)
        self.play(FadeIn(tunnel_lbl), run_time=0.6)

        mirror_detail = Text(
            "Intercepts traffic to demo-api pod → mirrors to local process",
            font_size=12, color=GREY,
        ).move_to(DOWN * 2)
        self.play(FadeIn(mirror_detail), run_time=0.8)
        self.wait(11)

        # ── P4 (47.9–67.9s): Request flows, breakpoint hits ────────
        self.play(FadeOut(mirror_detail), run_time=0.3)

        req = Dot(color=C_PR, radius=0.12).move_to(RIGHT * 6 + UP * 1.8)
        req_lbl = Text("request", font_size=11, color=C_PR).next_to(req, RIGHT, buff=0.1)
        self.play(FadeIn(req), FadeIn(req_lbl), run_time=0.4)

        self.play(req.animate.move_to(fe_pod.get_center()),
                  FadeOut(req_lbl), run_time=0.8)
        self.wait(0.5)
        self.play(req.animate.move_to(bff_pod.get_center()), run_time=0.8)
        self.wait(0.5)
        self.play(req.animate.move_to(api_pod.get_center()), run_time=0.8)
        self.wait(0.5)

        redirect_lbl = Text("mirrord → redirect to laptop", font_size=12, color="#ff9100")
        redirect_lbl.move_to(DOWN * 1.5)
        self.play(FadeIn(redirect_lbl), run_time=0.4)
        self.play(req.animate.move_to(ide.get_center()), run_time=1.5)

        bp_flash = Text("● BREAKPOINT HIT", font_size=22, color="#ff1744")
        bp_flash.next_to(ide, DOWN, buff=0.4)
        self.play(FadeIn(bp_flash, scale=1.2), Flash(ide.get_center(), color="#ff1744"),
                  run_time=0.8)
        self.wait(3)

        vars_panel = VGroup(
            Text("Variables:", font_size=13, color=GREY),
            Text("  headers['x-dev-session'] = 'pr-42'", font_size=12, color=C_PR),
            Text("  request.path = '/api/orders'", font_size=12, color=WHITE),
            Text("  downstream.status = 200", font_size=12, color=GREEN),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.08)
        vars_panel.move_to(LEFT * 3.5 + DOWN * 1.8)
        self.play(FadeIn(vars_panel), run_time=1)
        self.wait(6)

        # ── P5 (67.9–87.1s): Not a mock ────────────────────────────
        self.play(FadeOut(redirect_lbl), FadeOut(bp_flash), run_time=0.5)

        real_lbl = Text("Real requests · Real headers · Real downstream calls",
                        font_size=15, color=WHITE).move_to(DOWN * 3)
        self.play(FadeIn(real_lbl), run_time=0.8)
        self.wait(16)

        # ── P6 (87.1–100.6s): PR testing ───────────────────────────
        pr_note = Text("Works during PR testing — attach to the intercept pod",
                       font_size=14, color=C_PR).move_to(DOWN * 3)
        self.play(Transform(real_lbl, pr_note), run_time=0.8)
        self.wait(11)

        # ── P7 (100.6–110.1s): Cleanup ─────────────────────────────
        cleanup = Text("Disconnect → traffic returns to cluster pod · No artifacts",
                       font_size=14, color=GREY).move_to(DOWN * 3)
        self.play(Transform(real_lbl, cleanup), run_time=0.8)
        self.play(FadeOut(tunnel), FadeOut(tunnel_lbl), FadeOut(req), run_time=1)
        self.wait(6)

        # ── P8 (110.1–117.2s): Summary ─────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        summary = Text("Local IDE · Live cluster data · Full breakpoint debugging",
                       font_size=20, color=WHITE)
        self.play(FadeIn(summary), run_time=1)
        self.wait(5)


# ═════════════════════════════════════════════════════════════════════
# Scene 5: Multi-team Helm — synced to 08-multi-team-helm.mp3
# Total: 123.7s
# ═════════════════════════════════════════════════════════════════════
class MultiTeamScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG

        # ── P1 (0–7.8s): Intro ─────────────────────────────────────
        title = Text("Multi-Team Helm Deployment", font_size=28, color=WHITE)
        self.play(FadeIn(title), run_time=1)
        self.wait(5.5)
        self.play(FadeOut(title), run_time=0.8)

        # ── P2 (7.8–27.8s): Single team ────────────────────────────
        team_a = self._team_bubble("team-alpha", C_VUE)
        team_a.move_to(ORIGIN + UP * 0.5)
        self.play(FadeIn(team_a), run_time=1.5)

        details = VGroup(
            Text("Orchestrator deployed", font_size=12, color=GREY),
            Text("Tasks + Pipelines applied", font_size=12, color=GREY),
            Text("ConfigMaps for stacks + teams", font_size=12, color=GREY),
            Text("Optional build-cache PVC", font_size=12, color=GREY),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.1).move_to(DOWN * 2.2)
        self.play(LaggedStart(*[FadeIn(d) for d in details], lag_ratio=0.4), run_time=3)
        self.wait(13)

        # ── P3 (27.8–45.1s): Scale to 3 teams ─────────────────────
        self.play(FadeOut(details), run_time=0.5)

        team_b = self._team_bubble("team-beta", C_SPRING)
        team_c = self._team_bubble("team-gamma", C_FLASK)
        team_a_new = self._team_bubble("team-alpha", C_VUE)
        team_a_new.move_to(LEFT * 4 + UP * 0.5)
        team_b.move_to(ORIGIN + UP * 0.5)
        team_c.move_to(RIGHT * 4 + UP * 0.5)

        self.play(
            Transform(team_a, team_a_new),
            FadeIn(team_b), FadeIn(team_c),
            run_time=1.5,
        )

        iso_text = Text("Each team → own Helm release, ConfigMaps, orchestrator",
                        font_size=14, color=GREY).move_to(DOWN * 2)
        self.play(FadeIn(iso_text), run_time=0.8)
        self.wait(12)

        # ── P4 (45.1–71.7s): values.yaml knobs ─────────────────────
        self.play(FadeOut(iso_text), run_time=0.5)

        knobs = VGroup(
            _badge("imageRegistry", C_PIPELINE, 12),
            _badge("interceptBackend", "#ff9100", 12),
            _badge("compileImages", C_SPRING, 12),
            _badge("compileImageVariants", C_PR, 12),
        ).arrange(DOWN, buff=0.25).move_to(DOWN * 1.8)

        knobs_title = Text("values.yaml — per-team configuration",
                           font_size=14, color=WHITE).next_to(knobs, UP, buff=0.2)
        self.play(FadeIn(knobs_title), run_time=0.5)
        self.play(LaggedStart(*[FadeIn(k, shift=RIGHT * 0.3) for k in knobs],
                              lag_ratio=0.3), run_time=2)

        variant_detail = Text(
            "team-beta: Java 17  |  team-alpha: Java 21  |  same pipelines",
            font_size=12, color=GREY,
        ).next_to(knobs, DOWN, buff=0.2)
        self.play(FadeIn(variant_detail), run_time=0.8)
        self.wait(20)

        # ── P5 (71.7–94.6s): Custom hooks ──────────────────────────
        self.play(FadeOut(knobs), FadeOut(knobs_title), FadeOut(variant_detail),
                  run_time=0.5)

        hooks = VGroup(
            _badge("pre-build-task", C_HOOK, 13),
            _badge("post-build-task", C_HOOK, 13),
            _badge("pre-test-task", C_HOOK, 13),
            _badge("post-test-task", C_HOOK, 13),
        ).arrange(RIGHT, buff=0.3).move_to(DOWN * 1.5)
        hooks_title = Text("Custom pipeline hooks — no fork needed",
                           font_size=14, color=C_HOOK).next_to(hooks, UP, buff=0.2)

        examples = Text(
            "Example: image-scan after build · Slack notify after test",
            font_size=12, color=GREY,
        ).next_to(hooks, DOWN, buff=0.2)

        self.play(FadeIn(hooks_title), FadeIn(hooks), run_time=1)
        self.play(FadeIn(examples), run_time=0.6)
        self.wait(18)

        # ── P6 (94.6–106.2s): Management GUI ───────────────────────
        self.play(FadeOut(hooks), FadeOut(hooks_title), FadeOut(examples),
                  run_time=0.5)

        gui = _box("Management GUI\n(Vue + Flask)", C_GUI, width=3, height=1, font_size=16)
        gui.move_to(DOWN * 2)
        gui_features = Text(
            "Team switcher · DAG viz · Pipeline monitor · Test results",
            font_size=12, color=GREY,
        ).next_to(gui, DOWN, buff=0.2)
        self.play(FadeIn(gui), FadeIn(gui_features), run_time=1)
        self.wait(8)

        # ── P7 (106.2–118.1s): Webhook isolation ───────────────────
        self.play(FadeOut(gui), FadeOut(gui_features), run_time=0.5)

        wh = Arrow(LEFT * 6 + DOWN * 2, team_b.get_bottom(),
                   buff=0.15, color=C_ORCH, stroke_width=3)
        wh_lbl = Text("PR webhook → team-beta only", font_size=14, color=C_ORCH)
        wh_lbl.move_to(DOWN * 2.5)
        self.play(Create(wh), FadeIn(wh_lbl), run_time=1)
        self.play(team_b[0].animate.set_fill(C_SPRING, opacity=0.5), run_time=0.8)

        undisturbed = Text("team-alpha and team-gamma — undisturbed",
                           font_size=13, color=GREY).next_to(wh_lbl, DOWN, buff=0.2)
        self.play(FadeIn(undisturbed), run_time=0.6)
        self.wait(7)

        # ── P8 (118.1–123.7s): Summary ─────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        summary = Text("One chart · Multiple releases · Full team isolation",
                       font_size=22, color=WHITE)
        self.play(FadeIn(summary), run_time=1)
        self.wait(4)

    def _team_bubble(self, name, color):
        bubble = RoundedRectangle(
            corner_radius=0.2, width=3, height=1.8,
            stroke_color=color, fill_color=color, fill_opacity=0.08,
        )
        label = Text(name, font_size=15, color=color)
        label.move_to(bubble.get_top() + DOWN * 0.3)
        dots = VGroup(*[
            Dot(radius=0.07, color=color).shift(LEFT * 0.35 * (i - 1))
            for i in range(3)
        ]).next_to(label, DOWN, buff=0.25)
        lbl = Text("3 apps", font_size=11, color=GREY).next_to(dots, DOWN, buff=0.1)
        return VGroup(bubble, label, dots, lbl)


# ═════════════════════════════════════════════════════════════════════
# Scene 6: Blast-radius test selection — synced to 11-test-trace-graph.mp3
# Total: 123.2s
# ═════════════════════════════════════════════════════════════════════
class BlastRadiusScene(Scene):
    def construct(self):
        self.camera.background_color = C_BG

        # ── P1 (0–8s): Title ───────────────────────────────────────
        title = Text("Blast-Radius Test Selection", font_size=28, color=WHITE)
        sub = Text("Neo4j test-trace graph → intelligent test targeting",
                   font_size=15, color=GREY)
        sub.next_to(title, DOWN, buff=0.3)
        self.play(FadeIn(title), run_time=1)
        self.play(FadeIn(sub), run_time=0.6)
        self.wait(5)
        self.play(FadeOut(title), FadeOut(sub), run_time=0.8)

        # ── P2 (8–29.2s): Build the graph ──────────────────────────
        graph_title = Text("Neo4j Test-Trace Graph", font_size=16, color=C_NEO4J)
        graph_title.to_edge(UP, buff=0.4)
        self.play(FadeIn(graph_title), run_time=0.5)

        # Service nodes
        svc_fe = self._svc_node("demo-fe", C_VUE, LEFT * 4 + UP * 1.2)
        svc_bff = self._svc_node("BFF", C_SPRING, ORIGIN + UP * 1.2)
        svc_api = self._svc_node("demo-api", C_SPRING_DARK, RIGHT * 4 + UP * 1.2)

        self.play(FadeIn(svc_fe), FadeIn(svc_bff), FadeIn(svc_api), run_time=1.5)

        # CALLS edges
        call1 = Arrow(svc_fe.get_right(), svc_bff.get_left(), buff=0.35,
                      color=GREY_B, stroke_width=2)
        call2 = Arrow(svc_bff.get_right(), svc_api.get_left(), buff=0.35,
                      color=GREY_B, stroke_width=2)
        call_lbl1 = Text("CALLS", font_size=10, color=GREY_B).next_to(call1, UP, buff=0.05)
        call_lbl2 = Text("CALLS", font_size=10, color=GREY_B).next_to(call2, UP, buff=0.05)
        self.play(Create(call1), Create(call2), FadeIn(call_lbl1), FadeIn(call_lbl2),
                  run_time=1)
        self.wait(2)

        # Test nodes
        t1 = _diamond("fe-e2e", C_VUE).move_to(LEFT * 5 + DOWN * 1.2)
        t2 = _diamond("fe-post", C_VUE).move_to(LEFT * 3 + DOWN * 1.2)
        t3 = _diamond("bff-post", C_SPRING).move_to(LEFT * 1 + DOWN * 1.2)
        t4 = _diamond("bff-intg", C_SPRING).move_to(RIGHT * 1 + DOWN * 1.2)
        t5 = _diamond("api-post", C_SPRING_DARK).move_to(RIGHT * 2.8 + DOWN * 1.2)
        t6 = _diamond("api-intg", C_SPRING_DARK).move_to(RIGHT * 4.5 + DOWN * 1.2)
        t7 = _diamond("api-load", C_SPRING_DARK).move_to(RIGHT * 6 + DOWN * 1.2)
        tests = [t1, t2, t3, t4, t5, t6, t7]

        self.play(LaggedStart(*[FadeIn(t) for t in tests], lag_ratio=0.12), run_time=2)

        # TOUCHES edges
        touches_data = [
            (t1, svc_fe), (t2, svc_fe),
            (t3, svc_bff), (t4, svc_bff),
            (t5, svc_api), (t6, svc_api), (t7, svc_api),
        ]
        touch_colors = [C_VUE, C_VUE, C_SPRING, C_SPRING,
                        C_SPRING_DARK, C_SPRING_DARK, C_SPRING_DARK]
        touches = []
        for (t, s), c in zip(touches_data, touch_colors):
            line = DashedLine(t.get_top(), s.get_bottom(), color=c, dash_length=0.06,
                              stroke_width=1.5)
            touches.append(line)

        self.play(*[Create(line) for line in touches], run_time=1.5)

        legend = Text("○ Service   ◇ Test   --- TOUCHES   → CALLS",
                      font_size=11, color=GREY).to_edge(DOWN, buff=0.3)
        self.play(FadeIn(legend), run_time=0.5)
        self.wait(8)

        # ── P3 (29.2–46.6s): Ingestion explanation ─────────────────
        ingest_text = Text(
            "Traces ingested via POST /api/graph/ingest → graph builds over time",
            font_size=13, color=GREY,
        ).to_edge(DOWN, buff=0.6)
        self.play(Transform(legend, ingest_text), run_time=0.8)
        self.wait(14)

        # ── P4 (46.6–58.4s): Changed app highlight ─────────────────
        changed = Text("Changed: demo-api", font_size=16, color=C_WARN)
        changed.move_to(RIGHT * 4 + UP * 2.5)
        self.play(
            svc_api[0].animate.set_fill(C_WARN, opacity=0.5).set_stroke(C_WARN, width=3),
            FadeIn(changed),
            run_time=1,
        )
        self.wait(9)

        # ── P5 (58.4–72.3s): Radius 1 ──────────────────────────────
        r1_text = Text("Radius 1 → 3 direct tests", font_size=15, color=C_PR)
        r1_text.to_edge(DOWN, buff=0.6)
        self.play(Transform(legend, r1_text), run_time=0.5)

        for t in [t5, t6, t7]:
            self.play(t[0].animate.set_fill(C_PR, opacity=0.5), run_time=0.3)
        for line in touches[4:]:
            self.play(line.animate.set_color(C_PR).set_stroke(width=3), run_time=0.2)

        r1_list = VGroup(
            Text("✓ api-post", font_size=12, color=C_PR),
            Text("✓ api-intg", font_size=12, color=C_PR),
            Text("✓ api-load", font_size=12, color=C_PR),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        r1_list.move_to(DOWN * 2.5 + RIGHT * 4)
        self.play(FadeIn(r1_list), run_time=0.8)
        self.wait(8)

        # ── P6 (72.3–89.1s): Radius 2 ──────────────────────────────
        r2_text = Text("Radius 2 → +2 BFF tests (neighbor)", font_size=15, color=C_ORCH)
        r2_text.to_edge(DOWN, buff=0.6)
        self.play(Transform(legend, r2_text), run_time=0.5)

        self.play(
            svc_bff[0].animate.set_fill(C_ORCH, opacity=0.3),
            call2.animate.set_color(C_ORCH),
            run_time=0.8,
        )
        for t in [t3, t4]:
            self.play(t[0].animate.set_fill(C_ORCH, opacity=0.4), run_time=0.3)
        for line in touches[2:4]:
            self.play(line.animate.set_color(C_ORCH).set_stroke(width=3), run_time=0.2)

        r2_list = VGroup(
            Text("+ bff-post", font_size=12, color=C_ORCH),
            Text("+ bff-intg", font_size=12, color=C_ORCH),
        ).arrange(DOWN, aligned_edge=LEFT, buff=0.06)
        r2_list.next_to(r1_list, LEFT, buff=1)
        self.play(FadeIn(r2_list), run_time=0.6)
        self.wait(10)

        # ── P7 (89.1–101.4s): Unmapped warning ─────────────────────
        gap_text = Text("Radius gap → unmapped service = needs regression tests",
                        font_size=14, color=C_WARN)
        gap_text.to_edge(DOWN, buff=0.6)
        self.play(Transform(legend, gap_text), run_time=0.5)

        warn_icon = Text("⚠", font_size=28, color=C_WARN).move_to(LEFT * 5.5 + DOWN * 2.5)
        warn_lbl = Text("no tests!", font_size=12, color=C_WARN)
        warn_lbl.next_to(warn_icon, RIGHT, buff=0.1)
        self.play(FadeIn(warn_icon), FadeIn(warn_lbl), run_time=0.8)
        self.wait(9)

        # ── P8 (101.4–116.8s): Focused execution ───────────────────
        focus = Text("run-tests receives focused plan → 5 tests, not 50",
                     font_size=14, color=WHITE)
        focus.to_edge(DOWN, buff=0.6)
        self.play(Transform(legend, focus), FadeOut(warn_icon), FadeOut(warn_lbl),
                  run_time=0.8)
        self.wait(12)

        # ── P9 (116.8–123.2s): Summary ─────────────────────────────
        self.play(*[FadeOut(m) for m in self.mobjects], run_time=0.8)
        summary = Text("Graph query → Focused test plan → Faster feedback",
                       font_size=22, color=WHITE)
        self.play(FadeIn(summary), run_time=1)
        self.wait(4)

    def _svc_node(self, label, color, pos):
        circle = Circle(radius=0.5, color=color, fill_opacity=0.12, stroke_width=2.5)
        txt = Text(label, font_size=14, color=color)
        return VGroup(circle, txt).move_to(pos)
