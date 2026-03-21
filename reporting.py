from functools import lru_cache
from pathlib import Path

import jinja2

from models import CameraResult

GroupedResults = dict[str, list[CameraResult]]


def format_report(grouped_results: GroupedResults) -> str:
    lines: list[str] = []
    header = f"{'ID':<8} {'Name':<30} {'Road Clear':<12}"

    for group_name, results in grouped_results.items():
        lines.append(f"\n=== {format_group_name(group_name)} ===")
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


def format_group_name(name: str) -> str:
    return name.replace("_", " ").title()


def generate_email(grouped_results: GroupedResults) -> str:
    """Format report as HTML with embedded images for email."""
    template = get_template("email.html.jinja")
    all_results = [r for results in grouped_results.values() for r in results]
    return template.render(results=all_results)
