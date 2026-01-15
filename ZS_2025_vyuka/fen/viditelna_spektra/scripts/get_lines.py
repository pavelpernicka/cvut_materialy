#!/usr/bin/env python3

from urllib.request import Request, urlopen
from urllib.parse import urlencode
import re
import csv
import io

_num_re = re.compile(r"[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?\Z")


def fetch_text(url: str) -> str:
    req = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) python-urllib",
            "Accept": "text/csv,text/plain,*/*",
        },
        method="GET",
    )
    with urlopen(req, timeout=30) as resp:
        ctype = resp.headers.get("Content-Type", "")
        m = re.search(r"charset=([^\s;]+)", ctype, flags=re.I)
        charset = m.group(1) if m else "utf-8"
        return resp.read().decode(charset, errors="replace")


def is_number(s: str) -> bool:
    return _num_re.fullmatch(s) is not None


def unexcel(value: str) -> str:
    v = value.strip()
    if v.startswith('="') and v.endswith('"'):
        v = v[2:-1]  # strip leading =" and trailing "
    return v.strip()


def build_nist_url(element: str, lambda_from: float, lambda_to: float) -> str:
    params = {
        "spectra": element,
        "output_type": 0,
        "low_w": lambda_from,
        "upp_w": lambda_to,
        "unit": 1,
        "de": 0,
        "plot_out": 0,
        "I_scale_type": 1,
        "format": 2,
        "line_out": 0,
        "remove_js": "on",
        "no_spaces": "on",
        "en_unit": 1,
        "output": 0,
        "bibrefs": 1,
        "page_size": 15,
        "show_obs_wl": 1,
        "order_out": 0,
        "max_low_enrg": "",
        "show_av": 2,
        "max_upp_enrg": "",
        "tsb_value": 0,
        "min_str": "",
        "A_out": 0,
        "intens_out": "on",
        "max_str": "",
        "allowed_out": 1,
        "forbid_out": 1,
        "min_accur": "",
        "min_intens": "",
        "conf_out": "on",
        "term_out": "on",
        "enrg_out": "on",
        "J_out": "on",
        "submit": "Retrieve Data",
    }
    return "https://physics.nist.gov/cgi-bin/ASD/lines1.pl?" + urlencode(params)


def parse_first_two_columns(csv_text: str):
    text = csv_text.replace("\r\n", "\n").replace("\r", "\n")

    xs = []
    ys = []

    reader = csv.reader(io.StringIO(text))
    for row in reader:
        if len(row) < 2:
            continue

        a = unexcel(row[0])
        b = unexcel(row[1])

        if not is_number(a) or not is_number(b):
            continue

        xs.append(float(a))
        ys.append(float(b))

    return xs, ys


def retrieve_nist_lines(element: str, lambda_from: float, lambda_to: float):
    url = build_nist_url(element, lambda_from, lambda_to)
    csv_text = fetch_text(url)
    return parse_first_two_columns(csv_text)


def main() -> None:
    element = "Zn I"
    lambda_from = 400
    lambda_to = 700

    wl, inten = retrieve_nist_lines(element, lambda_from, lambda_to)

    print(f"Parsed {len(wl)} lines for {element} in [{lambda_from}, {lambda_to}] nm")
    for i in range(min(10, len(wl))):
        y = inten[i]
        print(f"{wl[i]:.6f}, {int(y) if y.is_integer() else y}")


if __name__ == "__main__":
    main()

