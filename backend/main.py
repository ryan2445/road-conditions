import logging
import sys

from reporting import format_report
from road_conditions import fetch_road_conditions
from service import run_camera_analysis


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
    )

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

    print(format_report(grouped_results))


if __name__ == "__main__":
    main()
