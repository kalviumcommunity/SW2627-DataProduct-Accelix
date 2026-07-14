"""
Vectorized Performance Optimization Pipeline
=================================================
This script demonstrates the optimization of data cleaning workflows by
replacing slow Python loop-based calculations with vectorized NumPy operations.
It profiles loop-based vs vectorized normalisation on large-scale datasets,
integrates the optimized features back into the customer DataFrame, and
produces a structured JSON audit report documenting speedups and scale metrics.
"""

import os
import sys
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime

# Ensure stdout support UTF-8 on Windows environments
if hasattr(sys.stdout, 'buffer'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Configuration and Constants
INPUT_FILE = "data/processed/customer_features.csv"
OUTPUT_FILE = "data/processed/optimized_customer_features.csv"
REPORT_FILE = "output/performance_comparison_report.json"

# Benchmark configurations
BENCHMARK_UNOPT_SIZE = 10000     # O(N^2) loop benchmark size
BENCHMARK_OPT_SIZE = 100000      # O(N) loop and NumPy benchmark size

# Ensure directories exist
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
os.makedirs(os.path.dirname(REPORT_FILE), exist_ok=True)


def benchmark_minmax_normalization(df):
    """
    Compare loop-based and vectorized implementations of Min-Max Normalisation.
    
    Args:
        df (pd.DataFrame): Expanded customer DataFrame for benchmarking.
        
    Returns:
        dict: Performance statistics and speedup values.
    """
    print("\n[Benchmarking] Min-Max Normalisation...")
    
    # 1. Unoptimized Loop - O(N^2) (min and max evaluated inside loop for each row)
    unopt_df = df.iloc[:BENCHMARK_UNOPT_SIZE].copy()
    start = time.perf_counter()
    unopt_result = []
    for val in unopt_df['total_spent']:
        # Simulates the bad practice of re-scanning the series inside the loop
        min_val = unopt_df['total_spent'].min()
        max_val = unopt_df['total_spent'].max()
        unopt_result.append((val - min_val) / (max_val - min_val))
    t_unopt = time.perf_counter() - start
    throughput_unopt = BENCHMARK_UNOPT_SIZE / t_unopt
    print(f"  - Unoptimized Loop (O(N^2)) [{BENCHMARK_UNOPT_SIZE} rows]: {t_unopt:.4f}s ({throughput_unopt:.1f} rows/sec)")
    
    # 2. Optimized Loop - O(N) (min and max evaluated once outside the loop)
    opt_df = df.iloc[:BENCHMARK_OPT_SIZE].copy()
    start = time.perf_counter()
    opt_result = []
    min_val = opt_df['total_spent'].min()
    max_val = opt_df['total_spent'].max()
    range_val = max_val - min_val
    for val in opt_df['total_spent']:
        opt_result.append((val - min_val) / range_val)
    t_opt = time.perf_counter() - start
    throughput_opt = BENCHMARK_OPT_SIZE / t_opt
    print(f"  - Optimized Loop (O(N)) [{BENCHMARK_OPT_SIZE} rows]: {t_opt:.4f}s ({throughput_opt:.1f} rows/sec)")
    
    # 3. NumPy Vectorized - O(N) (compiled C array calculations)
    start = time.perf_counter()
    spent_arr = opt_df['total_spent'].values
    vec_result = (spent_arr - spent_arr.min()) / (spent_arr.max() - spent_arr.min())
    t_vec = time.perf_counter() - start
    throughput_vec = BENCHMARK_OPT_SIZE / t_vec
    print(f"  - NumPy Vectorized [{BENCHMARK_OPT_SIZE} rows]: {t_vec:.4f}s ({throughput_vec:.1f} rows/sec)")
    
    # Speedups
    speedup_vs_opt_loop = t_opt / max(t_vec, 1e-9)
    # Extrapolate O(N^2) unoptimized loop time to BENCHMARK_OPT_SIZE (100k) for fair comparison
    extrapolated_unopt_time = t_unopt * ((BENCHMARK_OPT_SIZE / BENCHMARK_UNOPT_SIZE) ** 2)
    speedup_vs_unopt_loop = extrapolated_unopt_time / max(t_vec, 1e-9)
    
    print(f"  ✓ Speedup (NumPy vs Optimized Loop): {speedup_vs_opt_loop:.1f}x")
    print(f"  ✓ Speedup (NumPy vs Unoptimized Loop, extrapolated): {speedup_vs_unopt_loop:.1f}x")
    
    return {
        "unoptimized_loop": {
            "size": BENCHMARK_UNOPT_SIZE,
            "time_seconds": t_unopt,
            "throughput_rows_per_second": throughput_unopt
        },
        "optimized_loop": {
            "size": BENCHMARK_OPT_SIZE,
            "time_seconds": t_opt,
            "throughput_rows_per_second": throughput_opt
        },
        "numpy_vectorized": {
            "size": BENCHMARK_OPT_SIZE,
            "time_seconds": t_vec,
            "throughput_rows_per_second": throughput_vec
        },
        "speedups": {
            "vs_optimized_loop": speedup_vs_opt_loop,
            "vs_unoptimized_loop_extrapolated": speedup_vs_unopt_loop
        },
        "extrapolated_time_1M_rows": {
            "unoptimized_loop_seconds": t_unopt * ((1000000 / BENCHMARK_UNOPT_SIZE) ** 2),
            "optimized_loop_seconds": t_opt * (1000000 / BENCHMARK_OPT_SIZE),
            "numpy_vectorized_seconds": t_vec * (1000000 / BENCHMARK_OPT_SIZE)
        }
    }


def benchmark_zscore_normalization(df):
    """
    Compare loop-based and vectorized implementations of Z-Score Normalisation.
    
    Args:
        df (pd.DataFrame): Expanded customer DataFrame for benchmarking.
        
    Returns:
        dict: Performance statistics and speedup values.
    """
    print("\n[Benchmarking] Z-Score Normalisation...")
    
    # 1. Unoptimized Loop - O(N^2) (mean and std evaluated inside loop for each row)
    unopt_df = df.iloc[:BENCHMARK_UNOPT_SIZE].copy()
    start = time.perf_counter()
    unopt_result = []
    for val in unopt_df['total_spent']:
        mean_val = unopt_df['total_spent'].mean()
        std_val = unopt_df['total_spent'].std()
        unopt_result.append((val - mean_val) / std_val)
    t_unopt = time.perf_counter() - start
    throughput_unopt = BENCHMARK_UNOPT_SIZE / t_unopt
    print(f"  - Unoptimized Loop (O(N^2)) [{BENCHMARK_UNOPT_SIZE} rows]: {t_unopt:.4f}s ({throughput_unopt:.1f} rows/sec)")
    
    # 2. Optimized Loop - O(N) (mean and std evaluated once outside the loop)
    opt_df = df.iloc[:BENCHMARK_OPT_SIZE].copy()
    start = time.perf_counter()
    opt_result = []
    mean_val = opt_df['total_spent'].mean()
    std_val = opt_df['total_spent'].std()
    for val in opt_df['total_spent']:
        opt_result.append((val - mean_val) / std_val)
    t_opt = time.perf_counter() - start
    throughput_opt = BENCHMARK_OPT_SIZE / t_opt
    print(f"  - Optimized Loop (O(N)) [{BENCHMARK_OPT_SIZE} rows]: {t_opt:.4f}s ({throughput_opt:.1f} rows/sec)")
    
    # 3. NumPy Vectorized - O(N) (compiled C array calculations)
    start = time.perf_counter()
    spent_arr = opt_df['total_spent'].values
    vec_result = (spent_arr - spent_arr.mean()) / spent_arr.std()
    t_vec = time.perf_counter() - start
    throughput_vec = BENCHMARK_OPT_SIZE / t_vec
    print(f"  - NumPy Vectorized [{BENCHMARK_OPT_SIZE} rows]: {t_vec:.4f}s ({throughput_vec:.1f} rows/sec)")
    
    # Speedups
    speedup_vs_opt_loop = t_opt / max(t_vec, 1e-9)
    extrapolated_unopt_time = t_unopt * ((BENCHMARK_OPT_SIZE / BENCHMARK_UNOPT_SIZE) ** 2)
    speedup_vs_unopt_loop = extrapolated_unopt_time / max(t_vec, 1e-9)
    
    print(f"  ✓ Speedup (NumPy vs Optimized Loop): {speedup_vs_opt_loop:.1f}x")
    print(f"  ✓ Speedup (NumPy vs Unoptimized Loop, extrapolated): {speedup_vs_unopt_loop:.1f}x")
    
    return {
        "unoptimized_loop": {
            "size": BENCHMARK_UNOPT_SIZE,
            "time_seconds": t_unopt,
            "throughput_rows_per_second": throughput_unopt
        },
        "optimized_loop": {
            "size": BENCHMARK_OPT_SIZE,
            "time_seconds": t_opt,
            "throughput_rows_per_second": throughput_opt
        },
        "numpy_vectorized": {
            "size": BENCHMARK_OPT_SIZE,
            "time_seconds": t_vec,
            "throughput_rows_per_second": throughput_vec
        },
        "speedups": {
            "vs_optimized_loop": speedup_vs_opt_loop,
            "vs_unoptimized_loop_extrapolated": speedup_vs_unopt_loop
        },
        "extrapolated_time_1M_rows": {
            "unoptimized_loop_seconds": t_unopt * ((1000000 / BENCHMARK_UNOPT_SIZE) ** 2),
            "optimized_loop_seconds": t_opt * (1000000 / BENCHMARK_OPT_SIZE),
            "numpy_vectorized_seconds": t_vec * (1000000 / BENCHMARK_OPT_SIZE)
        }
    }


def main():
    print(f"Loading customer features dataset from {INPUT_FILE}...")
    if not os.path.exists(INPUT_FILE):
        print(f"Error: Input file {INPUT_FILE} does not exist. Please run engineer_features.py first.")
        sys.exit(1)
        
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} rows.")

    # 1. Expand dataset to 100,000 rows for benchmarking
    # We duplicate the 1,400 rows to create a robust sample size
    replication_factor = (BENCHMARK_OPT_SIZE // len(df)) + 1
    large_df = pd.concat([df] * replication_factor, ignore_index=True).iloc[:BENCHMARK_OPT_SIZE].reset_index(drop=True)
    
    # 2. Run benchmarks
    minmax_stats = benchmark_minmax_normalization(large_df)
    zscore_stats = benchmark_zscore_normalization(large_df)

    # 3. Integrate results into the original DataFrame (vectorized)
    print("\nIntegrating vectorized outputs into output customer features dataset...")
    
    # Min-Max Normalisation (vectorized)
    spent_arr = df['total_spent'].values
    df['total_spent_normalized'] = (spent_arr - spent_arr.min()) / (spent_arr.max() - spent_arr.min())
    
    # Z-Score Normalisation (vectorized)
    df['total_spent_zscore'] = (spent_arr - spent_arr.mean()) / spent_arr.std()
    
    # Save optimized customer features
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"✓ Saved optimized customer profiles to {OUTPUT_FILE} ({len(df)} rows)")

    # 4. Generate comparison JSON report
    report = {
        "timestamp": datetime.now().isoformat(),
        "benchmarked_rows_opt": BENCHMARK_OPT_SIZE,
        "benchmarked_rows_unopt": BENCHMARK_UNOPT_SIZE,
        "comparisons": {
            "minmax_normalization": minmax_stats,
            "zscore_normalization": zscore_stats
        },
        "business_implications": (
            "NumPy vectorization completely removes Python interpreter loops and performs "
            "calculations in parallel compiled C instructions. For 1 million rows, loop-based "
            "implementations would stall pipelines for seconds or minutes (up to 7+ minutes for "
            "unoptimized O(N^2) loops), whereas NumPy vectorization handles it in milliseconds, "
            "saving substantial compute costs and enabling interactive data analysis."
        )
    }

    with open(REPORT_FILE, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)
    print(f"✓ Performance comparison report saved to {REPORT_FILE}")
    print("\nPerformance optimization pipeline completed successfully!")


if __name__ == "__main__":
    main()
