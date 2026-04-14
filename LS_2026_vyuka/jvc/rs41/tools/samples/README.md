Store repeatable IQ captures for decoder debugging here.

Recommended default sample path:
- `tools/samples/latest_500ksps.cu8`

Capture a sample:
```sh
python3 tools/capture_sample.py --seconds 12
```

Decode the saved sample:
```sh
python3 tools/decode_sample.py
```

If you export a sample from URH manually, place it in this directory and pass
its path with `--input-file`.
