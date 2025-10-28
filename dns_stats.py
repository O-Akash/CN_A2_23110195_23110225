import sys
import subprocess
import time
def run_dns_test(url_file):
    try:
        with open(url_file, "r") as f:
            domains = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{url_file}' not found.")
        return
    total_queries = len(domains)
    success = 0
    failed = 0
    total_latency = 0  
    print(f"--- Running queries for {url_file} using custom resolver (10.0.0.5) ---")
    start_time = time.time()
    for domain in domains:
        cmd = ["dig", "+time=3", "+tries=2", domain]
        output = subprocess.run(cmd, capture_output=True, text=True).stdout
        if "status: NOERROR" in output:
            for line in output.splitlines():
                if "Query time:" in line:
                    try:
                        query_time = int(line.split()[3]) 
                        total_latency += query_time
                        success += 1
                    except:
                        failed += 1
                    break
        else:
            failed += 1
    elapsed_time = max(time.time() - start_time, 1)  
    avg_latency = round(total_latency / success, 2) if success > 0 else 0
    avg_qps = round(total_queries / elapsed_time, 2)
    print(f"--- Results for {url_file}---")
    print(f"Successfully resolved:   {success}")
    print(f"Failed resolutions:      {failed}")
    print(f"Average lookup latency:  {avg_latency} ms")
    print(f"Average throughput:      {avg_qps} queries/sec")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 dns_stats.py <url_file>")
    else:
        run_dns_test(sys.argv[1])
