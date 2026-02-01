import argparse

from road_analysis import (
    check_cameras,
    generate_web_page,
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
    args = parser.parse_args()

    model, preprocess, safe_text, unsafe_text, device = load_model()
    cameras = load_cameras()
    results = check_cameras(model, preprocess, safe_text, unsafe_text, device, cameras["mt_rose"])

    if args.html:
        html = generate_web_page(results)
        with open(args.html, "w") as f:
            f.write(html)
        print(f"HTML report written to {args.html}")
    else:
        print(format_report(results))


if __name__ == "__main__":
    main()
