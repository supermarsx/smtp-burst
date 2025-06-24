# smtp-burst
Simple python script that sends smtp email in bursts using independent processes for each mail sent out. Used to test smtp capacity, handling and possible attack scenarios. Depends on `smtplib` and `multiprocessing`.

## Features

- Burst sending of emails across multiple processes
- Adjustable delays between emails and bursts
- Stop automatically after a number of failed sends
- Optional JSON/YAML configuration file
- Open-only socket mode for connection tests
- Random payload data appended to each message
- Helper scripts for packaging and running tests

## Installation

Python 3.11 or newer is required. Install the library directly from the
repository source:

```bash
$ pip install .
```

This will install the `smtp-burst` console entry point.

## Quick Start

1. Edit `smtpburst/config.py` as needed for your tests or override values on the
   command line.
2. Start testing by executing the package with optional CLI flags.

   ```bash
   $ python -m smtpburst --server smtp.example.com \
       --sender from@example.com --receivers to@example.com other@example.com
   ```

   Use `-h`/`--help` to see all available options.

An optional `--config` flag can load settings from a JSON or YAML file.
See `examples/config.yaml` for a reference.

## Running Tests

Execute the unit tests using the helper scripts:

```bash
$ ./scripts/run_tests.sh     # Unix-like systems
```

```batch
C:\> scripts\run_tests.bat   # Windows
```

The script simply invokes `pytest --cov` and collects coverage information.

## Packaging

Build standalone executables with [PyInstaller](https://www.pyinstaller.org/).
Use the platform specific build scripts located in `scripts/` to create a
standalone binary using PyInstaller:

```bash
$ ./scripts/build_ubuntu.sh   # Linux
$ ./scripts/build_macos.sh    # macOS
```

```batch
C:\> scripts\build_windows.bat  % Windows
```

The resulting binaries will be placed in `dist/linux`, `dist/macos` or
`dist/windows` depending on the platform.

## License

Distributed under MIT License. See `license.md` for more information.

