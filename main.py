import argparse
from pathlib import Path

import logging
import sys
from reporting import format_report, generate_email
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

    if args.html:
        Path(args.html).write_text(generate_email(grouped_results), encoding="utf-8")
    print(format_report(grouped_results))


if __name__ == "__main__":
    main()
