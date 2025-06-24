# smtp-burst
Simple python script that sends smtp email in bursts using independent processes for each mail sent out. Used to test smtp capacity, handling and possible attack scenarios. Depends on `smtplib` and `multiprocessing`.

## Quick Start

1. Edit `burstVars.py` as needed for your tests or override values on the
   command line.
2. Start testing by executing `burstMain.py` with optional CLI flags.

   ```bash
   $ python ./burstMain.py --server smtp.example.com \
       --sender from@example.com --receivers to@example.com other@example.com
   ```

   Use `-h`/`--help` to see all available options.

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
Run the packaging script on the target platform (Linux, macOS or Windows):

```bash
$ ./scripts/package.sh
```

The resulting binaries will be placed in `dist/<platform>`.

## License

Distributed under MIT License. See `license.md` for more information.

