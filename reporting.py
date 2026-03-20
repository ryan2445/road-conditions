from functools import lru_cache
from pathlib import Path

import jinja2

from models import CameraResult


def format_report(results: list[CameraResult]) -> str:
    lines: list[str] = []
    header = f"{'ID':<8} {'Name':<30} {'Road Clear':<12}"
    lines.append(header)
    lines.append("-" * len(header))

    for result in results:
        score_display = format_score(result)
        lines.append(f"{result['id']:<8} {result['name']:<30} {score_display:<12}")

    return "\n".join(lines)


def format_score(result: CameraResult) -> str:
    if result["error"]:
        return "Error"

    score = result["clearness_score"]
    if score is None:
        return "N/A"

    return f"{score:.0%}"


@lru_cache(maxsize=1)
def _get_template_environment() -> jinja2.Environment:
    template_dir = Path(__file__).parent / "templates"
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(template_dir),
        autoescape=True,
    )


def get_template(name: str) -> jinja2.Template:
    """Load a Jinja2 template from the templates directory."""
    return _get_template_environment().get_template(name)


def generate_email(results: list[CameraResult]) -> str:
    """Format report as HTML with embedded images for email."""
    template = get_template("email.html.jinja")
    return template.render(results=results)
