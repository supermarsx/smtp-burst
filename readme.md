# smtp-burst
Simple python script that sends smtp email in bursts using a independent processes for each send. Used to test smtp capacity, handling and possible attack scenarios. Depends on `smtplib` and `multiprocessing`.

## Quick Start

1. Edit `burstVars.py` as needed for your tests.
  2. Start testing by executing `burstMain.py` from the command line.

     ```
     $ python ./burstMain.py
     ```

## License

Distributed under MIT License. See `license.md` for more information.

