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

An optional `--config` flag can load settings from a JSON or YAML file.
See `examples/config.yaml` for a reference.

## Running Tests

Execute the unit tests with `pytest` from the repository root:

```bash
$ pytest
```

## License

Distributed under MIT License. See `license.md` for more information.

