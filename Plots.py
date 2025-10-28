import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv('resolver_log.txt', skipinitialspace=True)
df.columns = [c.strip() for c in df.columns]
# --- PLOT 1: Servers Visited ---
def count_servers_accurately(domain_name, full_log_df):
    domain_df = full_log_df[full_log_df['Domain name queried'] == domain_name].copy()
    final_entry = domain_df.iloc[-1]
    final_status = final_entry['Cache status']
    if final_status == 'HIT':
        return 1
    if final_entry['Step of resolution'] == 'Failure' or final_status == 'FAILED':
        external_servers = domain_df[~domain_df['DNS server IP contacted'].isin(['10.0.0.5'])]
        return external_servers['DNS server IP contacted'].nunique() + 1      
    elif final_status == 'MISS':
        external_servers = domain_df[~domain_df['DNS server IP contacted'].isin(['10.0.0.5'])].copy()
        num_external_servers = external_servers['DNS server IP contacted'].nunique()
        return num_external_servers + 1         
    return 0
H1_domains = df['Domain name queried'].unique()[:10]
df_final = df[df['Domain name queried'].isin(H1_domains)]
df_final = df_final.groupby('Domain name queried').last().reset_index()
df_final['Query Index'] = range(1, len(df_final) + 1)
df_final = df_final.sort_values(by='Query Index')
df_final['Servers Visited'] = df_final['Domain name queried'].apply(
    lambda x: count_servers_accurately(x, df)
)
plt.figure(figsize=(10, 5))
plt.bar(df_final['Domain name queried'], df_final['Servers Visited'], color='green', alpha=0.7)
plt.title('Total DNS Servers Visited per Query (First 10 H1 URLs)')
plt.xlabel('Domain Name')
plt.ylabel('Number of Distinct External DNS Servers')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()
plt.show()

# --- PLOT 2: Latency per Query (Total Time) ---
plt.figure(figsize=(10, 5))
plt.bar(df_final['Domain name queried'], df_final['Total time to resolution'], color='blue', alpha=0.8)
plt.title('Total Resolution Latency per Query (First 10 H1 URLs)')
plt.xlabel('Domain Name')
plt.ylabel('Latency (ms)')
plt.xticks(rotation=45, ha='right')
plt.grid(axis='y', linestyle='--', alpha=0.6)
plt.tight_layout()
plt.show()
