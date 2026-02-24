import argparse

from road_analysis import (
    check_cameras,
    format_report,
    load_cameras,
    load_provider,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Check road conditions from cameras")
    parser.add_argument(
        "--html",
        "-o",
        metavar="FILE",
        help="Output standalone HTML report to file",
        required=False,
    )
    _ = parser.parse_args()

    provider = load_provider()
    cameras = load_cameras()
    results = check_cameras(provider, cameras["mt_rose"])

    print(format_report(results))


if __name__ == "__main__":
    main()
