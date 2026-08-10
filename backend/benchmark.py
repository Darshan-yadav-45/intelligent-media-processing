"""
Simple benchmark script for the upload -> processing pipeline.

Measures:
  - upload response time (time for POST /api/images/upload to return)
  - end-to-end processing time (time from upload until status=completed)
  - concurrent processing behavior (N images uploaded in parallel)

Usage:
    python benchmark.py --image sample.jpg --count 5 --base-url http://localhost:8000 --token <JWT>

Note: results depend heavily on hardware, image size/content, and whether
Tesseract/OpenCV are running on CPU vs GPU-accelerated builds. Treat these
numbers as relative, not absolute.
"""
import argparse
import time
import statistics
import concurrent.futures as cf

import httpx


def upload_one(base_url: str, token: str, image_path: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    with open(image_path, "rb") as f:
        files = {"file": (image_path, f, "image/jpeg")}
        t0 = time.perf_counter()
        resp = httpx.post(f"{base_url}/api/images/upload", headers=headers, files=files, timeout=30)
        upload_time = time.perf_counter() - t0

    resp.raise_for_status()
    processing_id = resp.json()["processing_id"]

    t1 = time.perf_counter()
    while True:
        status_resp = httpx.get(f"{base_url}/api/images/{processing_id}/status", headers=headers, timeout=10)
        status_resp.raise_for_status()
        state = status_resp.json()["status"]
        if state in ("completed", "failed"):
            break
        time.sleep(0.5)
    total_processing_time = time.perf_counter() - t1

    return {"upload_time": upload_time, "processing_time": total_processing_time, "final_status": state}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--base-url", default="http://localhost:8000")
    parser.add_argument("--token", required=True, help="JWT access token from /api/auth/login")
    args = parser.parse_args()

    print(f"Running benchmark: {args.count} concurrent uploads of {args.image}")

    with cf.ThreadPoolExecutor(max_workers=args.count) as executor:
        futures = [
            executor.submit(upload_one, args.base_url, args.token, args.image)
            for _ in range(args.count)
        ]
        results = [f.result() for f in cf.as_completed(futures)]

    upload_times = [r["upload_time"] for r in results]
    processing_times = [r["processing_time"] for r in results]
    failures = sum(1 for r in results if r["final_status"] == "failed")

    print("\n--- Benchmark Results ---")
    print(f"Requests: {len(results)}  Failures: {failures}")
    print(f"Avg upload response time: {statistics.mean(upload_times):.2f} sec")
    print(f"Avg end-to-end processing time: {statistics.mean(processing_times):.2f} sec")
    print(f"Min/Max processing time: {min(processing_times):.2f}s / {max(processing_times):.2f}s")
    print("\nNote: absolute numbers depend on hardware, image size, and load.")


if __name__ == "__main__":
    main()
