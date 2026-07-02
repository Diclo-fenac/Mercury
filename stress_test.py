import asyncio
import time
import argparse
import aiohttp
from collections import Counter

async def fetch(session, url):
    start = time.perf_counter()
    try:
        async with session.get(url) as response:
            await response.read() # make sure to consume the response
            duration = time.perf_counter() - start
            return response.status, duration
    except Exception as e:
        duration = time.perf_counter() - start
        return str(type(e).__name__), duration

async def worker(session, url, requests_per_worker):
    results = []
    for _ in range(requests_per_worker):
        results.append(await fetch(session, url))
    return results

async def main(url, total_requests, concurrency):
    print(f"Stressing {url} with {total_requests} requests, concurrency {concurrency}...")
    
    conn = aiohttp.TCPConnector(limit=concurrency)
    async with aiohttp.ClientSession(connector=conn) as session:
        tasks = []
        requests_per_worker = total_requests // concurrency
        remainder = total_requests % concurrency
        
        start_time = time.perf_counter()
        
        for i in range(concurrency):
            reqs = requests_per_worker + (1 if i < remainder else 0)
            tasks.append(asyncio.create_task(worker(session, url, reqs)))
            
        all_results = await asyncio.gather(*tasks)
        
        end_time = time.perf_counter()
        total_time = end_time - start_time
        
        flat_results = [item for sublist in all_results for item in sublist]
        
        status_counts = Counter(r[0] for r in flat_results)
        durations = [r[1] for r in flat_results]
        
        success_durations = [r[1] for r in flat_results if isinstance(r[0], int) and 200 <= r[0] < 300]
        
        print("\n--- Results ---")
        print(f"Total time: {total_time:.2f} seconds")
        print(f"Requests/sec: {total_requests / total_time:.2f}")
        print("\nStatus codes:")
        for status, count in status_counts.items():
            print(f"  {status}: {count}")
            
        if durations:
            print("\nLatencies:")
            print(f"  Min: {min(durations)*1000:.2f} ms")
            print(f"  Max: {max(durations)*1000:.2f} ms")
            print(f"  Avg: {sum(durations)/len(durations)*1000:.2f} ms")
            
        if success_durations:
            success_durations.sort()
            p50 = success_durations[int(len(success_durations) * 0.5)]
            p90 = success_durations[int(len(success_durations) * 0.9)]
            p95 = success_durations[int(len(success_durations) * 0.95)]
            p99 = success_durations[int(len(success_durations) * 0.99)]
            print("\nPercentiles (successful requests):")
            print(f"  P50: {p50*1000:.2f} ms")
            print(f"  P90: {p90*1000:.2f} ms")
            print(f"  P95: {p95*1000:.2f} ms")
            print(f"  P99: {p99*1000:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("url", help="URL to stress test")
    parser.add_argument("-n", "--requests", type=int, default=1000, help="Total number of requests")
    parser.add_argument("-c", "--concurrency", type=int, default=100, help="Concurrency level")
    args = parser.parse_args()
    
    asyncio.run(main(args.url, args.requests, args.concurrency))
