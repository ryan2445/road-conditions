from models import CameraResult

GroupedResults = dict[str, list[CameraResult]]


def format_report(grouped_results: GroupedResults) -> str:
    lines: list[str] = []
    header = f"{'ID':<8} {'Name':<30} {'Status':<12}"

    for group_name, results in grouped_results.items():
        lines.append(f"\n=== {format_group_name(group_name)} ===")
        lines.append(header)
        lines.append("-" * len(header))

        for result in results:
            status_display = "Error" if result["error"] else "OK"
            lines.append(f"{result['id']:<8} {result['name']:<30} {status_display:<12}")

    return "\n".join(lines)


def format_group_name(name: str) -> str:
    return name.replace("_", " ").title()

