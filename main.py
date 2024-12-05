import numpy as np
import pandas as pd

from arrivals import Arrivals
from model.customer import Customer
from service import Service

np.random.seed(42)

agents_list = []
customers_queue = []
completed_list = []

A = Arrivals()
S = Service(num_of_agents=60)

summary_dict = {"time":[], "Num arrivals":[], "Queue length":[], "Available agents":[]}
for i in range(3600):
    print("Time period:", i)
    customers_queue, completed_list, num_arrivals = A.update_queue(customers_queue=customers_queue, current_time=i, case="uniform", completed_list=completed_list)
    #print("Num of customers in queue:", len(customers_queue))

    agents_list, completed_list, customers_queue = S.agents_serve_customers_in_queue(customers_queue=customers_queue, agents_list=agents_list, completed_list=completed_list, current_time=i)
    #print("Length of completed list", len(completed_list))
    #print("Num of customers left in queue", len(customers_queue))
    
    summary_dict["time"].append(i)
    summary_dict["Num arrivals"].append(num_arrivals)
    summary_dict["Queue length"].append(len(customers_queue))
    summary_dict["Available agents"].append(S.num_of_agents - len(agents_list))

completed_dict = {"time":[], "wait":[], "abandon":[]}
for customer in completed_list:
    #print("Arrival time:", customer.arrival_time, "Exit time:", customer.exit_time, "Abandon:", customer.abandon)
    completed_dict["time"].append(customer.exit_time)
    completed_dict["wait"].append(customer.exit_time - customer.arrival_time)
    completed_dict["abandon"].append(int(customer.abandon))

summary_df = pd.DataFrame(summary_dict)
print(summary_df)
summary_df.to_csv("summary.csv")

completed_df = pd.DataFrame(completed_dict)
print(completed_df)
completed_df.to_csv("completed.csv")

# compile customers cleared from the queue at the same time together
compiled_completed_df = completed_df.groupby("time").agg(
    num_completed=("wait", "count"),  # Count the number of customers cleared in each second
    total_wait=("wait", "sum"),       # Sum the total wait times in each second
    abandon=("abandon", "sum")        # Sum the total number of abandonments in each second
).reset_index()  # Reset the index to make it a regular column

print(compiled_completed_df)

# Save the grouped results to a CSV file
compiled_completed_df.to_csv("compiled_completed.csv", index=False)

# Perform a left join to retain all rows from summary_df
merged_df = pd.merge(
    summary_df, compiled_completed_df,
    on="time",  # Join on the "time" column
    how="left"  # Perform a left join
)

merged_df = merged_df.fillna(0)

print(merged_df)

# Step 1: Identify cycles
merged_df["is_cycle_start"] = (
    (merged_df["Queue length"] == 0) & (merged_df["Available agents"] == 0) & (merged_df["num_completed"] == 0) &
    (~((merged_df["Queue length"] == 0) & (merged_df["Available agents"] == 0) & (merged_df["num_completed"] == 0)).shift(1).fillna(False))
)

# Assign a cycle number to each row in merged_df
merged_df["cycle"] = merged_df["is_cycle_start"].cumsum()

# Save the merged DataFrame to a CSV file
merged_df.to_csv("merged_summary.csv", index=False)

merged_df = merged_df[merged_df["cycle"] > 0]

# Step 4: Aggregate by cycle
cycle_summary = merged_df.groupby("cycle").agg(
    num_arrivals=("Num arrivals", "sum"),          # Sum total wait times within the cycle
    total_wait=("total_wait", "sum"),          # Sum total wait times within the cycle
    num_completed=("num_completed", "sum"),  # Sum completed customers within the cycle
    abandon=("abandon", "sum"),              # Sum abandon counts within the cycle
).reset_index()

# Save the cycle summary to a CSV
cycle_summary.to_csv("cycle_summary.csv", index=False)

prob_abandon = (cycle_summary["abandon"]/cycle_summary["num_completed"]).mean()
avg_wait = (cycle_summary["total_wait"]/cycle_summary["num_completed"]).mean()
print(cycle_summary)
print(prob_abandon, avg_wait)

print(cycle_summary[cycle_summary["num_arrivals"] != cycle_summary["num_completed"]])