# smtp-burst
Simple python script that sends smtp email in bursts using independent processes for each mail sent out. Used to test smtp capacity, handling and possible attack scenarios. Depends on `smtplib` and `multiprocessing`.

## Quick Start

1. Edit `burstVars.py` as needed for your tests.
  2. Start testing by executing `burstMain.py` from the command line.

     ```
     $ python ./burstMain.py
     ```

## Running Tests

Execute the unit tests with `pytest` from the repository root:

```bash
$ pytest
```

## License

Distributed under MIT License. See `license.md` for more information.

