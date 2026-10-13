
import argparse
import statistics
import time
from datetime import datetime, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
URL = "https://easytrader.emofid.com/"


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
    parser = argparse.ArgumentParser(
        description="Safe Sarkhati connection test; no orders."
    )
    parser.add_argument("--target-time", required=True, help="HH:MM Tehran time")
    parser.add_argument("--prep-minutes", type=int, default=3)
    parser.add_argument("--interval", type=float, default=2)
    args = parser.parse_args()

    try:
        hour, minute = map(int, args.target_time.split(":"))
        if not (0 <= hour <= 23 and 0 <= minute <= 59):
            raise ValueError
    except ValueError:
        raise SystemExit("Invalid target time. Use HH:MM, for example 19:28.")

    if args.prep_minutes < 0 or args.interval <= 0:
        raise SystemExit("Preparation must be >= 0 and interval must be > 0.")

    now = datetime.now(TEHRAN)
    target = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    if target <= now:
        raise SystemExit(
            "Target time has already passed today. "
            "Run again with a future Tehran time."
        )

    prep_start = target - timedelta(minutes=args.prep_minutes)

    print("SARKHATI - SAFE CONNECTION TEST", flush=True)
    print("Current Tehran time:", now.isoformat(), flush=True)
    print("Target time:", target.isoformat(), flush=True)
    print("Preparation starts:", prep_start.isoformat(), flush=True)
    print("Test interval:", args.interval, "seconds", flush=True)
    print("URL:", URL, flush=True)
    print("No orders will be submitted.", flush=True)

    while datetime.now(TEHRAN) < prep_start:
        remaining = (prep_start - datetime.now(TEHRAN)).total_seconds()
        time.sleep(min(1, max(0.1, remaining)))

    print("\nPreparation started.", flush=True)
    results = []

    while datetime.now(TEHRAN) < target:
        stamp = datetime.now(TEHRAN)
        latency, status = probe(URL)
        results.append(latency)

        print(
            f"{stamp:%Y-%m-%d %H:%M:%S %Z}"
            f" | latency={latency:.1f} ms"
            f" | {status}",
            flush=True,
        )

        remaining = (target - datetime.now(TEHRAN)).total_seconds()
        if remaining > 0:
            time.sleep(min(args.interval, remaining))

    print("\nSUMMARY", flush=True)
    print("Samples:", len(results), flush=True)

    if results:
        print(f"Minimum: {min(results):.1f} ms", flush=True)
        print(f"Average: {statistics.mean(results):.1f} ms", flush=True)
        print(f"Maximum: {max(results):.1f} ms", flush=True)
        print(f"Median: {statistics.median(results):.1f} ms", flush=True)

    print("Target time reached. No orders were submitted.", flush=True)


if __name__ == "__main__":
    main()
