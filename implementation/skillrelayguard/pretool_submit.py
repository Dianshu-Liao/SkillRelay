"""Explicit sink entry point; a working pre-tool hook must intercept this call."""


def main():
    raise SystemExit("Pre-tool hook did not intercept the submission adapter. Nothing was sent. Check hook configuration.")


if __name__ == "__main__":
    main()
