from snow_checker import load_model, load_cameras, check_cameras, format_report


def main():
    model, preprocess, text, device = load_model()
    cameras = load_cameras()
    results = check_cameras(model, preprocess, text, device, cameras["mt_rose"])
    print(format_report(results))


if __name__ == "__main__":
    main()
