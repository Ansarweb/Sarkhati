import argparse
import time
import statistics
from datetime import datetime, time as dt_time
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

TEHRAN = ZoneInfo("Asia/Tehran")

START_TIME = dt_time(8, 44, 50)
TARGET_TIME = dt_time(8, 45, 0)
END_TIME = dt_time(8, 45, 10)

INTERVAL = 0.25


def now_tehran():
    return datetime.now(TEHRAN)


def probe(url, timeout=4):
    """Measure HTTP HEAD round-trip time. Never sends a buy/sell order."""
    start = time.perf_counter()

    try:
        request = Request(
            url,
            method="HEAD",
            headers={"User-Agent": "Sarkhati-Latency-Test/1.0"},
        )

        with urlopen(request, timeout=timeout) as response:
            status = response.status

        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, f"HTTP {status}"

    except (URLError, HTTPError, TimeoutError, OSError) as exc:
        elapsed_ms = (time.perf_counter() - start) * 1000
        return elapsed_ms, f"ERROR: {exc}"


def main():
    parser = argparse.ArgumentParser(
        description="Sarkhati safe timing and latency test"
    )
    parser.add_argument(
        "--url",
        default="https://easytrader.emofid.com/",
        help="Website URL for a harmless HTTP HEAD latency test",
    )
    parser.add_argument(
        "--date",
        help="Optional Tehran date, format YYYY-MM-DD",
    )
    args = parser.parse_args()

    print("=" * 55)
    print("SARKHATI - SAFE TEST MODE")
    print("No real orders will be submitted.")
    print("Timezone: Asia/Tehran")
    print("Test window: 08:44:50 - 08:45:10")
    print("Target time: 08:45:00")
    print("=" * 55)

    samples = []

    while True:
        now = now_tehran()

        if args.date and now.date().isoformat() != args.date:
            print(f"Waiting for Tehran date {args.date}; now {now.date()}")
            time.sleep(10)
            continue

        current = now.time()

        if current < START_TIME:
            remaining = (
                datetime.combine(now.date(), START_TIME, tzinfo=TEHRAN)
                - now
            ).total_seconds()
            print(
                f"\rWaiting for start: {now:%H:%M:%S.%f}"[:-3],
                end="",
                flush=True,
            )
            time.sleep(min(max(remaining, 0.1), 1.0))
            continue

        if current > END_TIME:
            break

        # Record a harmless latency sample every second.
        if len(samples) == 0 or time.monotonic() - samples[-1][0] >= 1:
            elapsed, result = probe(args.url)
            stamp = now_tehran()
            samples.append((time.monotonic(), elapsed))

            target = datetime.combine(
                stamp.date(), TARGET_TIME, tzinfo=TEHRAN
            )
            delta_ms = (stamp - target).total_seconds() * 1000

            print(
                f"{stamp:%H:%M:%S.%f}"[:-3]
                + f" | latency={elapsed:.1f} ms"
                + f" | target delta={delta_ms:+.0f} ms"
                + f" | {result}"
            )

        time.sleep(INTERVAL)

    print("\n" + "=" * 55)
    print("TEST FINISHED")
    if samples:
        values = [item[1] for item in samples]
        print(f"Samples: {len(values)}")
        print(f"Minimum latency: {min(values):.1f} ms")
        print(f"Average latency: {statistics.mean(values):.1f} ms")
        print(f"Maximum latency: {max(values):.1f} ms")
    else:
        print("No latency samples were collected.")
    print("No real orders were submitted.")
    print("=" * 55)


if __name__ == "__main__":
    main()
