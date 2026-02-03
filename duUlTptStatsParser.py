import re
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime

# === CONFIG ===
#file_path = "C:/Users/dvelpuch/Downloads/tbLen_0_logs/du-xyz/du-l2/run-log-20250613-090835/du_stats.txt"
file_path = "C:/Users/dvelpuch/Downloads/FH_PKT_SANITY_LOGS/du_stats_25_09_18_05_37_39_part_0.txt"
#file_path = "C:/Users/dvelpuch/Downloads/tbLen_0_logs/du-xyz/du-l2/run-log-20250613-090835/du_stats_s22.txt"
#debug_ue_id = "17019"

print("📥 Starting DLLA parser...")

# Read log file
with open(file_path, "r") as f:
    lines = f.readlines()

#timestamps = []
ue_metrics = defaultdict(lambda: defaultdict(list))
state = None
current_timestamp = None

# Regex patterns
time_re = re.compile(r"GNB DU Statistics\s+(.*)")
ue_tpt = re.compile(r"UE Instantaneous Statistics\s+(.*)")
ue_line_re = re.compile(r"^\d{5}\s+")

# === Parse log ===
for line in lines:
    line = line.strip()

    match = time_re.match(line)
    if match:
        current_timestamp = match.group(1).strip()
        #timestamps.append(current_timestamp)
        state = None
        continue
    
    if "UE Instantaneous Statistics" in line:
        state = "TPT"
        continue
    
    if "Cell Tpt Statistics" in line:
        state = None
        continue

    if "UE SCH: LA Histogram Statistics" in line:
        state = "LA"
        continue
    
    if "DL MCS Histogram Statistics" in line:
        state = None
        continue

    if ue_line_re.match(line):
        if state == "TPT":
            fields = re.split(r'\s{2,}', line)
            ue_id = fields[0]
            #print(f"\n🖨️ TPT UE {ue_id}:\n")
            try:
                ue_metrics[ue_id]["UL-TPT"].append(float(fields[3]))
                dt = datetime.strptime(current_timestamp, "%a %b %d %H:%M:%S %Y")
                ue_metrics[ue_id]["TimeStamp"].append(dt.strftime("%H:%M:%S"))
            except:
                ue_metrics[ue_id]["UL-TPT"].append(None)
            continue

        elif state == "LA":
            fields = re.split(r'\s{2,}', line)
            ue_id = fields[0]
            #print(f"\n🖨️ LA UE {ue_id}:\n")
            try:
                ue_metrics[ue_id]["UL-tBLER%"].append(float(fields[13]))
                ue_metrics[ue_id]["UL-avgMCS"].append(float(fields[15]))
                ue_metrics[ue_id]["UL-avgSNR"].append(float(fields[14]))
                ue_metrics[ue_id]["UL-avgRI"].append(float(fields[16]))
            except:
                ue_metrics[ue_id]["UL-tBLER%"].append(None)
                ue_metrics[ue_id]["UL-avgMCS"].append(None)
            continue

        else:
            state = None
            continue

# === Print metrics for debug_ue_id ===
for id in ue_metrics:
    print(f"\n🖨️ Per-timestamp values for UE {id}:\n")
    print("Time         | UL-avgMCS | UL-avgSNR | UL-avgRI | UL-tBLER% | UL-TPT (Mbps)")
    print("----------------------------------------------------------------------------------------")
    metrics = ue_metrics[id]
    for i in range(len(metrics["TimeStamp"])):
        ts = metrics.get("TimeStamp", [None]*len(metrics["TimeStamp"]))[i] if i < len(metrics["TimeStamp"]) else None
        mcs = metrics.get("UL-avgMCS", [None]*len(metrics["TimeStamp"]))[i] if i < len(metrics["UL-avgMCS"]) else None
        snr = metrics.get("UL-avgSNR", [None]*len(metrics["TimeStamp"]))[i] if i < len(metrics["UL-avgSNR"]) else None
        ri = metrics.get("UL-avgRI", [None]*len(metrics["TimeStamp"]))[i] if i < len(metrics["UL-avgRI"]) else None
        bler = metrics.get("UL-tBLER%", [None]*len(metrics["TimeStamp"]))[i] if i < len(metrics["UL-tBLER%"]) else None
        tpt = metrics.get("UL-TPT", [None]*len(metrics["TimeStamp"]))[i] if i < len(metrics["UL-TPT"]) else None
        print(f"{ts if ts is not None else '0':<12} | {mcs if mcs is not None else '0':<9} | {snr if snr is not None else '0':<9} | {ri if ri is not None else '0':<8} | {bler if bler is not None else '0':<9} | {tpt if tpt is not None else '0'}")

    # After appending current values, normalize the lengths
    metrics = ["UL-tBLER%", "UL-avgMCS", "UL-TPT", "UL-avgSNR", "UL-avgRI", "TimeStamp"]
    # Step 1: Find the max length among all metric lists
    max_len = max(len(ue_metrics[id][metric]) for metric in metrics)
    # Step 2: Pad shorter lists with 0.0 (or 0 for TimeStamp if needed)
    for metric in metrics:
        current_len = len(ue_metrics[id][metric])
        if current_len < max_len:
            if metric == "TimeStamp":
                # Optional: Use None or 0 depending on your use case
                ue_metrics[id][metric].extend([0] * (max_len - current_len))
            else:
                ue_metrics[id][metric].extend([0.0] * (max_len - current_len))

# === Plotting ===
for ue_id, metrics in ue_metrics.items():
    if not all(k in metrics for k in ["UL-tBLER%", "UL-avgMCS", "UL-TPT", "UL-avgSNR", "UL-avgRI", "TimeStamp"]):
        continue

    # Truncate values to match timestamp count
    for key in ["UL-tBLER%", "UL-avgMCS", "UL-TPT", "UL-avgSNR", "UL-avgRI", "TimeStamp"]:
        metrics[key] = metrics[key][:len(metrics["TimeStamp"])]

    print(f"\n📈 Plotting for UE {ue_id}")

    # Create figure and base axis (for UL-avgMCS)
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot UL-avgMCS on ax1    
    ln1 = ax1.plot(metrics["TimeStamp"], metrics["UL-avgMCS"], label='UL-avgMCS', color='royalblue', marker='o')
    ax1.set_ylabel('MCS', color='royalblue')
    ax1.tick_params(axis='y', labelcolor='royalblue')
    ax1.set_ylim(0, 31)

    # Plot UL-tBLER% on ax2
    # Second Y-axis for UL-tBLER%
    ax2 = ax1.twinx()    
    ln2 = ax2.plot(metrics["TimeStamp"], metrics["UL-tBLER%"], label='UL-tBLER%', color='firebrick', marker='x')
    ax2.set_ylabel('BLER (%)', color='firebrick')
    ax2.tick_params(axis='y', labelcolor='firebrick')
    ax2.set_ylim(0, 100)

    # Plot UL-TPT on ax3
    # Third Y-axis for UL-TPT — offset to the right
    ax3 = ax1.twinx()
    ax3.spines['right'].set_position(('outward', 60))  # Offset the third Y-axis    
    ln3 = ax3.plot(metrics["TimeStamp"], metrics["UL-TPT"], label='UL-TPT', color='forestgreen', marker='s')
    ax3.set_ylabel('TPT (Mbps)', color='forestgreen')
    ax3.tick_params(axis='y', labelcolor='forestgreen')
    ax3.set_ylim(0, 800)

    # Fourth Y-axis for UL-avgSNR
    ax4 = ax1.twinx()
    ax4.spines['right'].set_position(('outward', 120))  # Offset the fifth Y-axis
    ln4 = ax4.plot(metrics["TimeStamp"], metrics["UL-avgSNR"], label='UL-avgSNR', color='mediumvioletred', marker='o')
    ax4.set_ylabel('UL-avgSNR', color='mediumvioletred')
    ax4.tick_params(axis='y', labelcolor='mediumvioletred')
    ax4.set_ylim(0, 35)

    # Fifth Y-axis for UL-avgRI
    ax5 = ax1.twinx()
    ax5.spines['right'].set_position(('outward', 180))  # Offset the third Y-axis
    ln5 = ax5.plot(metrics["TimeStamp"], metrics["UL-avgRI"], label='UL-avgRI', color='darkorange', marker='^')
    ax5.set_ylabel('RI', color='darkorange')
    ax5.tick_params(axis='y', labelcolor='darkorange')
    ax5.set_ylim(0, 4)

    # Shared X-axis
    ax1.set_xlabel('Time')
    ax1.set_xticks(metrics["TimeStamp"])
    ax1.tick_params(axis='x', rotation=45)

    # Combine legends from all three axes
    lines = ln1 + ln2 + ln3 + ln4 + ln5
    labels = [l.get_label() for l in lines]
    #ax1.legend(lines, labels, loc='upper left')
    ax1.legend(lines, labels, loc='lower left', bbox_to_anchor=(1.05, 1))
    plt.tight_layout(rect=[0, 0, 0.85, 1])

    # Title and layout
    plt.title(f'DLLA Metrics Over Time - UE {ue_id}')
    plt.tight_layout()
    plt.show()
    
    # # Plot all three metrics
    # plt.plot(metrics["TimeStamp"], metrics["UL-avgMCS"], label="UL-avgMCS", marker='o', color='royalblue')
    # plt.plot(metrics["TimeStamp"], metrics["UL-tBLER%"], label="UL-tBLER%", marker='x', color='firebrick')
    # plt.plot(metrics["TimeStamp"], metrics["UL-TPT"], label="UL-TPT", marker='s', color='forestgreen')

    # # Custom Y-axis ticks
    # yticks_custom = list(range(0, 100, 20)) + list(range(100, 701, 100))
    # #yticks_custom = list(range(0, 35, 1))
    # plt.yticks(yticks_custom)

    # # Set Y-axis limits
    # plt.ylim(0, 800)

    # # Labels, title, and formatting
    # plt.title(f'UE {ue_id} - DL Metrics Over Time')
    # plt.xlabel('Time')
    # plt.ylabel('Metric Value')
    # plt.xticks(rotation=45)
    # plt.grid(True)
    # plt.legend()
    # plt.tight_layout()
    # plt.show()

    # # Create a single figure
    # plt.figure(figsize=(12, 6))

    # # Plot UL-avgMCS
    # plt.plot(metrics["TimeStamp"], metrics["UL-avgMCS"], label="UL-avgMCS", marker='o', color='royalblue')

    # # Plot UL-tBLER%
    # plt.plot(metrics["TimeStamp"], metrics["UL-tBLER%"], label="UL-tBLER%", marker='x', color='firebrick')

    # # Plot UL-TPT
    # plt.plot(metrics["TimeStamp"], metrics["UL-TPT"], label="UL-TPT", marker='s', color='forestgreen')

    # # Configure axes
    # plt.title(f'UE {ue_id} - DL Metrics Over Time')
    # plt.xlabel('Time')
    # plt.ylabel('Metric Value')
    # plt.xticks(rotation=45)
    # plt.ylim(0, 800)  # Y-axis from 0 to 800 as requested
    # plt.grid(True)

    # # Add legend
    # plt.legend()

    # # Display the plot
    # plt.tight_layout()
    # plt.show()    
    # plt.figure(figsize=(15, 5))

    # # UL-avgMCS
    # plt.subplot(1, 3, 1)
    # plt.plot(metrics["TimeStamp"], metrics["UL-avgMCS"], marker='o', color='royalblue')
    # plt.title(f'UE {ue_id} - DL MCS')
    # plt.xlabel('Time')
    # plt.ylabel('MCS')
    # plt.xticks(rotation=45)
    # plt.grid(True)

    # # UL-tBLER%
    # plt.subplot(1, 3, 2)
    # plt.plot(metrics["TimeStamp"], metrics["UL-tBLER%"], marker='x', color='firebrick')
    # plt.title(f'UE {ue_id} - DL tBLER%')
    # plt.xlabel('Time')
    # plt.ylabel('BLER (%)')
    # plt.xticks(rotation=45)
    # plt.grid(True)

    # # UL-TPT
    # plt.subplot(1, 3, 3)
    # plt.plot(metrics["TimeStamp"], metrics["UL-TPT"], marker='s', color='forestgreen')
    # plt.title(f'UE {ue_id} - DL Throughput')
    # plt.xlabel('Time')
    # plt.ylabel('TPT (Mbps)')
    # plt.xticks(rotation=45)
    # plt.grid(True)

    # plt.suptitle(f'DLLA Metrics Over Time - UE {ue_id}')
    # plt.tight_layout()
    # plt.show(block=True)
