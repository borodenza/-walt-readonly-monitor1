from pathlib import Path
import json


def render():
    report = json.loads(Path("walt-report.json").read_text(encoding="utf-8-sig"))
    payload = json.dumps(report, ensure_ascii=True, allow_nan=False).replace("<", "\\u003c")
    template = Path("mira.html").read_text(encoding="utf-8-sig")
    output = template.replace('id="snapshot">null</script>', 'id="snapshot">' + payload + '</script>')
    Path("mira-recovery.html").write_text(output, encoding="utf-8")


if __name__ == "__main__":
    render()
