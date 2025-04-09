import requests
import time
import statistics
import json
import concurrent.futures
import matplotlib.pyplot as plt
from datetime import datetime

# Configuration for the three regions
regions = {
    "East US": {
        "endpoint": "https://eastus.api.cognitive.microsoft.com/",
        "api_key": "###",
        "deployment": "gpt-4o"
    },
    "West US": {
        "endpoint": "https://westus.api.cognitive.microsoft.com/",
        "api_key": "###",
        "deployment": "gpt-4o"
    },
    "Japan East": {
        "endpoint": "https://japaneast.api.cognitive.microsoft.com/",
        "api_key": "###",
        "deployment": "gpt-4o"
    }
}

# Test prompts of varying complexity
test_prompts = [
    "Hello, how are you?",  # Short prompt
    "Explain the theory of relativity in 100 words.",  # Medium prompt
    "Write a detailed analysis of global economic trends over the past decade...",  # Long prompt
]

# Function to execute a single test case (region + prompt + iteration)
def execute_test_case(args):
    region, prompt, iteration = args
    result = test_latency(region, prompt)
    
    # Safe printing of results (handling None values)
    latency_str = f"{result['latency']:.4f}s" if result['latency'] is not None else "Failed"
    print(f"Region: {region}, Iteration: {iteration+1}, Latency: {latency_str}")
    
    return result

# Function to test latency for a single request
def test_latency(region_name, prompt, is_warmup=False):
    region_config = regions[region_name]
    
    headers = {
        "Content-Type": "application/json",
        "api-key": region_config["api_key"]
    }
    
    data = {
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": 100
    }
    
    url = f"{region_config['endpoint']}openai/deployments/{region_config['deployment']}/chat/completions?api-version=2024-12-01-preview"
    
    start_time = time.time()
    try:
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()
        elapsed = time.time() - start_time
        
        if not is_warmup:
            return {
                "region": region_name,
                "prompt_length": len(prompt),
                "latency": elapsed,
                "status": "success"
            }
        return None
    except Exception as e:
        if not is_warmup:
            return {
                "region": region_name,
                "prompt_length": len(prompt),
                "latency": None,
                "status": f"error: {str(e)}"
            }
        return None

# Warmup function to initialize connections
def perform_warmup():
    print("Performing warmup calls...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(regions)) as executor:
        futures = []
        for region in regions:
            futures.append(executor.submit(test_latency, region, "Warmup call", True))
        concurrent.futures.wait(futures)
    time.sleep(2)  # Brief pause after warmup
    print("Warmup complete")

# Main testing function with parallel execution
def run_latency_tests(iterations=5, warmup=True, max_workers=10):
    if warmup:
        perform_warmup()
    
    results = []
    print(f"Starting parallel latency tests across {len(regions)} regions with {len(test_prompts)} prompts, {iterations} iterations each...")
    
    # Create a list of all test cases
    test_cases = []
    for prompt_idx, prompt in enumerate(test_prompts):
        for i in range(iterations):
            for region in regions:
                test_cases.append((region, prompt, i))
    
    # Execute test cases in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_case = {executor.submit(execute_test_case, case): case for case in test_cases}
        
        for future in concurrent.futures.as_completed(future_to_case):
            result = future.result()
            if result:
                results.append(result)
    
    return results

# Analyze and visualize results
def analyze_results(results):
    # Filter out any failed requests
    valid_results = [r for r in results if r["latency"] is not None]
    
    if not valid_results:
        print("No valid results to analyze!")
        return
    
    # Group by region
    region_results = {}
    for region in regions:
        region_results[region] = [r["latency"] for r in valid_results if r["region"] == region]
    
    # Calculate statistics
    stats = {}
    for region, latencies in region_results.items():
        if latencies:
            stats[region] = {
                "min": min(latencies),
                "max": max(latencies),
                "avg": statistics.mean(latencies),
                "median": statistics.median(latencies),
                "p95": statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else None,
                "std_dev": statistics.stdev(latencies) if len(latencies) > 1 else 0,
                "sample_size": len(latencies)
            }
    
    # Print statistics
    print("\n===== LATENCY STATISTICS (seconds) =====")
    for region, region_stats in stats.items():
        print(f"\n{region} (Sample size: {region_stats['sample_size']}):")
        print(f"  Min: {region_stats['min']:.4f}s")
        print(f"  Max: {region_stats['max']:.4f}s")
        print(f"  Avg: {region_stats['avg']:.4f}s")
        print(f"  Median: {region_stats['median']:.4f}s")
        if region_stats['p95']:
            print(f"  95th percentile: {region_stats['p95']:.4f}s")
        print(f"  Standard Deviation: {region_stats['std_dev']:.4f}s")
    
    # Count failures
    failures = [r for r in results if r["latency"] is None]
    if failures:
        print(f"\nFailed requests: {len(failures)}/{len(results)} ({len(failures)/len(results)*100:.1f}%)")
        for region in regions:
            region_failures = [f for f in failures if f["region"] == region]
            if region_failures:
                print(f"  {region}: {len(region_failures)} failures")
    
    # Create visualization
    plt.figure(figsize=(12, 8))
    
    # Box plot
    plt.subplot(2, 1, 1)
    plt.boxplot([latencies for region, latencies in region_results.items() if latencies], 
                labels=[f"{region}\n(n={len(latencies)})" for region, latencies in region_results.items() if latencies], 
                showfliers=True)
    plt.title('GPT-4o Latency Comparison by Region')
    plt.ylabel('Latency (seconds)')
    plt.grid(True, linestyle='--', alpha=0.7)
    
    # Bar chart with error bars
    plt.subplot(2, 1, 2)
    regions_list = list(stats.keys())
    avgs = [stats[r]["avg"] for r in regions_list]
    std_devs = [stats[r]["std_dev"] for r in regions_list]
    
    bars = plt.bar(regions_list, avgs, yerr=std_devs, alpha=0.7, capsize=10)
    
    # Add value labels on top of bars
    for bar, avg in zip(bars, avgs):
        plt.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.02,
                f'{avg:.3f}s', ha='center', va='bottom', fontweight='bold')
    
    plt.title('Average Latency by Region')
    plt.ylabel('Latency (seconds)')
    plt.ylim(top=max(avgs) * 1.2)  # Add some headroom for labels
    plt.grid(True, linestyle='--', alpha=0.7, axis='y')
    
    plt.tight_layout()
    plt.savefig('azure_gpt4o_latency_comparison.png')
    print("\nVisualization saved as 'azure_gpt4o_latency_comparison.png'")
    
    # Prompt length analysis
    plt.figure(figsize=(12, 6))
    prompt_lengths = sorted(list(set([r["prompt_length"] for r in valid_results])))
    
    for region in regions:
        region_by_length = {}
        for length in prompt_lengths:
            region_by_length[length] = [
                r["latency"] for r in valid_results 
                if r["region"] == region and r["prompt_length"] == length
            ]
        
        avgs_by_length = [statistics.mean(latencies) if latencies else 0 
                          for length, latencies in region_by_length.items()]
        
        plt.plot(prompt_lengths, avgs_by_length, marker='o', label=region)
    
    plt.title('Latency by Prompt Length')
    plt.xlabel('Prompt Length (characters)')
    plt.ylabel('Average Latency (seconds)')
    plt.legend()
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    plt.savefig('azure_gpt4o_latency_by_prompt_length.png')
    print("Prompt length analysis saved as 'azure_gpt4o_latency_by_prompt_length.png'")
    
    # Save raw results
    with open('latency_test_results.json', 'w') as f:
        json.dump({
            "raw_data": results,
            "statistics": stats,
            "test_time": datetime.now().isoformat()
        }, f, indent=2)
    
    print("Raw results saved as 'latency_test_results.json'")

# Run everything
if __name__ == "__main__":
    # Can adjust the parallelism level and number of iterations
    results = run_latency_tests(iterations=10, warmup=True, max_workers=15)
    analyze_results(results)
