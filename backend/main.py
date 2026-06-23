import argparse
from pathlib import Path

import logging
import sys

from reporting import format_report, generate_email
from road_conditions import fetch_road_conditions
from service import run_camera_analysis


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
    )
    parser = argparse.ArgumentParser(description="Check road conditions from cameras")
    parser.add_argument(
        "--html",
        "-o",
        metavar="FILE",
        help="Output standalone HTML report to file",
        required=False,
    )
    args = parser.parse_args()

    grouped_results = run_camera_analysis()

    road_conditions = fetch_road_conditions()
    if road_conditions:
        print("\n=== Road Condition Alerts ===")
        for group, alerts in road_conditions.items():
            print(f"\n{group}:")
            for alert in alerts:
                print(f"  {alert['roadway']}: {alert['condition']}")
                if alert["secondaryConditions"]:
                    print(f"    Secondary: {', '.join(alert['secondaryConditions'])}")
                print(f"    Segment: {alert['description']}")
    else:
        print("\nNo active road condition alerts.")

    if args.html:
        Path(args.html).write_text(generate_email(grouped_results), encoding="utf-8")
    print(format_report(grouped_results))


if __name__ == "__main__":
    main()
