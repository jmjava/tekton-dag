from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
CONVERSION = ROOT / "sample-repos" / "conversion"


def test_conversion_kit_covers_all_sample_repos():
    expected = {
        "tekton-dag-flask",
        "tekton-dag-php",
        "tekton-dag-vue-fe",
        "tekton-dag-spring-boot",
        "tekton-dag-spring-boot-gradle",
        "tekton-dag-spring-legacy",
    }
    present = {p.name for p in CONVERSION.iterdir() if p.is_dir()}
    assert expected <= present
    assert (ROOT / "sample-repos" / "apply-baggage-conversion.sh").is_file()
    assert (ROOT / "sample-repos" / "CONVERT-BAGGAGE.md").is_file()
    flask = (CONVERSION / "tekton-dag-flask" / "app.py").read_text()
    assert "baggage.install(app)" in flask
    assert "/propagation" in flask
    vue = (CONVERSION / "tekton-dag-vue-fe" / "src" / "main.js").read_text()
    assert "install(defaultConfig())" in vue
    php = (CONVERSION / "tekton-dag-php" / "public" / "index.php").read_text()
    assert "Baggage::install()" in php
    nginx = (CONVERSION / "tekton-dag-vue-fe" / "nginx.conf.template").read_text()
    assert "proxy_pass" in nginx
    assert "x-dev-session" in nginx
