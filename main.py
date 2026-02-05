import argparse

from road_analysis import (
    check_cameras,
    format_report,
    load_cameras,
    load_model,
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

    model, preprocess, safe_text, unsafe_text, device = load_model()
    cameras = load_cameras()
    results = check_cameras(
        model, preprocess, safe_text, unsafe_text, device, cameras["mt_rose"]
    )

    print(format_report(results))


if __name__ == "__main__":
    main()
