import time
import asyncio
import pandas as pd
from functools import wraps
from typing import Callable, List, Dict, Any
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


def benchmark_to_csv(label: str, out_dir: str = "perf_results"):
    """
    Decorator to benchmark a function and save timing/results to CSV.
    The decorated function should return a dict of measurement fields (e.g. status_code, count, etc.).
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, request_count: int = 1, **kwargs):
            Path(out_dir).mkdir(parents=True, exist_ok=True)
            records = []

            for i in range(request_count):
                try:
                    start = time.perf_counter()
                    result = func(*args, **kwargs)
                    duration = (time.perf_counter() - start) * 1000  # in ms

                    record = {
                        "iteration": i + 1,
                        "duration_ms": duration,
                        **result
                    }

                except Exception as e:
                    record = {
                        "iteration": i + 1,
                        "duration_ms": None,
                        "error": str(e)
                    }

                records.append(record)

            df = pd.DataFrame(records)
            safe_name = "".join(c if c.isalnum() else "_" for c in label[:60])
            df.to_csv(Path(out_dir) / f"{safe_name}.csv", index=False)
            return df

        return wrapper
    return decorator


async def benchmark_concurrent_requests(
    session: aiohttp.ClientSession,
    url: str,
    params: Dict[str, Any],
    auth: tuple,
    request_count: int,
    concurrent_limit: int = 10,
    timeout: int = 60
) -> List[Dict[str, Any]]:
    """
    Benchmark concurrent HTTP requests using asyncio and aiohttp.
    
    Args:
        session: aiohttp ClientSession
        url: Target URL
        params: Query parameters
        auth: Authentication tuple (username, password)
        request_count: Total number of requests to make
        concurrent_limit: Maximum concurrent requests
        timeout: Request timeout in seconds
    
    Returns:
        List of result dictionaries with timing and response data
    """
    semaphore = asyncio.Semaphore(concurrent_limit)
    results = []
    
    async def make_request(request_id: int) -> Dict[str, Any]:
        async with semaphore:
            try:
                start_time = time.perf_counter()
                
                async with session.get(
                    url,
                    params=params,
                    auth=aiohttp.BasicAuth(auth[0], auth[1]),
                    timeout=aiohttp.ClientTimeout(total=timeout)
                ) as response:
                    content = await response.read()
                    duration = (time.perf_counter() - start_time) * 1000  # in ms
                    
                    return {
                        "iteration": request_id + 1,
                        "duration_ms": duration,
                        "status_code": response.status,
                        "response_size_bytes": len(content),
                        "error": None
                    }
                    
            except Exception as e:
                return {
                    "iteration": request_id + 1,
                    "duration_ms": None,
                    "status_code": None,
                    "response_size_bytes": 0,
                    "error": str(e)
                }
    
    # Create tasks for all requests
    tasks = [make_request(i) for i in range(request_count)]
    
    # Execute all tasks concurrently
    results = await asyncio.gather(*tasks)
    
    return results


def benchmark_parallel_requests(
    request_func: Callable,
    request_count: int,
    max_workers: int = 10,
    **kwargs
) -> List[Dict[str, Any]]:
    """
    Benchmark parallel requests using ThreadPoolExecutor.
    
    Args:
        request_func: Function that makes a single request
        request_count: Total number of requests to make
        max_workers: Maximum number of worker threads
        **kwargs: Additional arguments to pass to request_func
    
    Returns:
        List of result dictionaries with timing and response data
    """
    results = []
    
    def make_request_with_timing(request_id: int) -> Dict[str, Any]:
        try:
            start_time = time.perf_counter()
            result = request_func(**kwargs)
            duration = (time.perf_counter() - start_time) * 1000  # in ms
            
            return {
                "iteration": request_id + 1,
                "duration_ms": duration,
                **result
            }
            
        except Exception as e:
            return {
                "iteration": request_id + 1,
                "duration_ms": None,
                "error": str(e)
            }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_id = {
            executor.submit(make_request_with_timing, i): i 
            for i in range(request_count)
        }
        
        # Collect results as they complete
        for future in as_completed(future_to_id):
            results.append(future.result())
    
    # Sort by iteration to maintain order
    results.sort(key=lambda x: x["iteration"])
    return results


def save_benchmark_results(
    results: List[Dict[str, Any]], 
    label: str, 
    out_dir: str = "perf_results"
) -> str:
    """
    Save benchmark results to CSV file.
    
    Args:
        results: List of result dictionaries
        label: Label for the benchmark
        out_dir: Output directory
    
    Returns:
        Path to the saved CSV file
    """
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    
    df = pd.DataFrame(results)
    safe_name = "".join(c if c.isalnum() else "_" for c in label[:60])
    csv_path = Path(out_dir) / f"{safe_name}.csv"
    df.to_csv(csv_path, index=False)
    
    return str(csv_path)


def print_benchmark_summary(results: List[Dict[str, Any]], label: str):
    """
    Print a summary of benchmark results.
    
    Args:
        results: List of result dictionaries
        label: Label for the benchmark
    """
    successful_results = [r for r in results if r.get("duration_ms") is not None]
    failed_results = [r for r in results if r.get("duration_ms") is None]
    
    if not successful_results:
        print(f"❌ {label}: All requests failed")
        return
    
    durations = [r["duration_ms"] for r in successful_results]
    
    print(f"📊 {label}:")
    print(f"   Total requests: {len(results)}")
    print(f"   Successful: {len(successful_results)}")
    print(f"   Failed: {len(failed_results)}")
    print(f"   Mean duration: {sum(durations) / len(durations):.2f}ms")
    print(f"   Min duration: {min(durations):.2f}ms")
    print(f"   Max duration: {max(durations):.2f}ms")
    print(f"   Median duration: {sorted(durations)[len(durations)//2]:.2f}ms")
    
    if failed_results:
        print(f"   Errors: {[r.get('error', 'Unknown') for r in failed_results[:3]]}")
        if len(failed_results) > 3:
            print(f"   ... and {len(failed_results) - 3} more errors") 