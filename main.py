import argparse
import statistics
import time
from datetime import datetime
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")


def probe(url, timeout=5):
    start = time.perf_counter()
    status = "OK"

    try:
        request = Request(
            url,
            method="HEAD",
            headers={"User-Agent": "Sarkhati-Safe-Test/1.0"},
        )
        with urlopen(request, timeout=timeout) as response:
            status = f"HTTP {response.status}"

    except HTTPError as exc:
        status = f"HTTP {exc.code}"
    except (URLError, TimeoutError, OSError) as exc:
        status = f"ERROR: {exc}"

    elapsed = (time.perf_counter() - start) * 1000
    return elapsed, status


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--url",
        default="https://easytrader.emofid.com/",
    )
    parser.add_argument("--duration", type=int, default=180)
    parser.add_argument("--interval", type=float, default=2)
    args = parser.parse_args()

    print("SARKHATI - SAFE LATENCY TEST")
    print("Tehran time:", datetime.now(TEHRAN).isoformat())
    print("URL:", args.url)
    print("No orders will be submitted.")

    results = []
    deadline = time.monotonic() + max(1, args.duration)

    while time.monotonic() < deadline:
        stamp = datetime.now(TEHRAN)
        latency, status = probe(args.url)
        results.append(latency)

        print(
            f"{stamp:%Y-%m-%d %H:%M:%S %Z}"
            f" | latency={latency:.1f} ms"
            f" | {status}",
            flush=True,
        )

        remaining = deadline - time.monotonic()
        if remaining > 0:
            time.sleep(min(max(args.interval, 0.2), remaining))

    if results:
        print("\nSUMMARY")
        print("Samples:", len(results))
        print(f"Minimum: {min(results):.1f} ms")
        print(f"Average: {statistics.mean(results):.1f} ms")
        print(f"Maximum: {max(results):.1f} ms")
        print(f"Median: {statistics.median(results):.1f} ms")

    print("Finished. No orders were submitted.")


if __name__ == "__main__":
    main()
