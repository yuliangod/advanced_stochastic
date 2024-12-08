from typing import Literal

import numpy as np
import pandas as pd
from scipy.stats import norm
from tqdm import tqdm

from arrivals import Arrivals
from model.customer import Customer
from service import Service

np.random.seed(42)


class AnalyseCycle:
    def __init__(self):
        pass
    
    def find_optimal_agents(self, n:int, min_num_agents:int, max_num_agents:int, case:Literal["uniform", "hyperexponential"],):
        data = []
        for num_agents in tqdm(range(min_num_agents, max_num_agents)):
            prob_abandon, prob_abandon_ci, avg_wait, avg_wait_ci, num_cycles, full_sim_prob_abandon, full_sim_avg_wait = self.analyse(n=n, num_of_agents=num_agents, case=case)
            data.append([num_agents, prob_abandon, prob_abandon_ci, avg_wait, avg_wait_ci, num_cycles, full_sim_prob_abandon, full_sim_avg_wait])
        
        df = pd.DataFrame(data, columns=["No. of agents", "Prob abandon", "Prob abandon CI", "Avg wait", "Avg wait CI", "No. of cycles", "Full sim prob abandon", "Full sim avg abandon"])
        df.to_csv(f"results_{case}.csv", index=False)
    
    def analyse(self, n:int, num_of_agents:int, case:Literal["uniform", "hyperexponential"],):
        
        df = self.generate_df(n=n, num_of_agents=num_of_agents, case=case)
        cycles_df, num_cycles = self.generate_cycles_df(df)
        
        prob_abandon, prob_abandon_ci = self.steady_state_analysis(cycles_df=cycles_df, reward_column="abandon", cycle_length_column="num_completed")
        avg_wait, avg_wait_ci = self.steady_state_analysis(cycles_df=cycles_df, reward_column="total_wait", cycle_length_column="num_completed")
        
        print(prob_abandon, avg_wait)
        print(prob_abandon_ci, avg_wait_ci)
        
        full_sim_prob_abandon = df["abandon"].sum()/df["num_completed"].sum()
        full_sim_avg_wait = df["total_wait"].sum()/df["num_completed"].sum()
        
        return prob_abandon, prob_abandon_ci, avg_wait, avg_wait_ci, num_cycles, full_sim_prob_abandon, full_sim_avg_wait
        
    
    def generate_df(self, n:int, num_of_agents:int, case:Literal["uniform", "hyperexponential"]):
        agents_list = []
        customers_queue = []
        completed_list = []

        A = Arrivals()
        S = Service(num_of_agents=num_of_agents)

        summary_dict = {"time":[], "Num arrivals":[], "Queue length":[], "Available agents":[]}
        for i in range(n):
            #print("Time period:", i)
            customers_queue, completed_list, num_arrivals = A.update_queue(customers_queue=customers_queue, current_time=i, case=case, completed_list=completed_list)
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


        system_state_df = pd.DataFrame(summary_dict)

        completed_customers_df = pd.DataFrame(completed_dict)

        # compile customers cleared from the queue at the same time together
        compiled_completed_customers_df = completed_customers_df.groupby("time").agg(
            num_completed=("wait", "count"),  # Count the number of customers cleared in each second
            total_wait=("wait", "sum"),       # Sum the total wait times in each second
            abandon=("abandon", "sum")        # Sum the total number of abandonments in each second
        ).reset_index()  # Reset the index to make it a regular column

        #compiled_completed_customers_df.to_csv("compiled_completed.csv", index=False)

        # Perform a left join to retain all rows from system_state_df
        df = pd.merge(
            system_state_df, compiled_completed_customers_df,
            on="time",  # Join on the "time" column
            how="left"  # Perform a left join
        )

        df = df.fillna(0)
        #print(df)
        
        return df

    def generate_cycles_df(self, df:pd.DataFrame):
        # Step 1: Identify cycles
        df["is_cycle_start"] = (
            (df["Queue length"] == 0) & (df["Available agents"] == 0) & (df["num_completed"] == 0) &
            (~((df["Queue length"] == 0) & (df["Available agents"] == 0) & (df["num_completed"] == 0)).shift(1).fillna(False))
        )
        
        # Explicitly infer objects to adjust types
        df = df

        # Assign a cycle number to each row in df
        df["cycle"] = df["is_cycle_start"].cumsum()

        # Save the merged DataFrame to a CSV file
        #df.to_csv("df.csv", index=False)

        # Step 4: Aggregate by cycle
        cycles_df = df.groupby("cycle").agg(
            num_arrivals=("Num arrivals", "sum"),          # Sum total wait times within the cycle
            total_wait=("total_wait", "sum"),          # Sum total wait times within the cycle
            num_completed=("num_completed", "sum"),  # Sum completed customers within the cycle
            abandon=("abandon", "sum"),              # Sum abandon counts within the cycle
        ).reset_index()

        #cycles_df.to_csv("cycles_df.csv", index=False)

        num_cycles = cycles_df["cycle"].max()
                
        return cycles_df, num_cycles
    
    def steady_state_analysis(self, cycles_df:pd.DataFrame, reward_column:str, cycle_length_column:str):
        # remove first cycle as it doesn't start from a "reset" state, remove last cycle as it may not neccessarily be a complete cycle
        cycles_df = cycles_df.iloc[1:-1]
    
        reward = cycles_df[reward_column].mean()
        cycle_length = cycles_df[cycle_length_column].mean()
        long_run_avg = reward/cycle_length
        
        s11_square = cycles_df[reward_column].var()
        s22_square = cycles_df[cycle_length_column].var()
        s12_square = cycles_df[reward_column].cov(cycles_df[cycle_length_column])
        #print(s11_square, s22_square, s12_square)
        
        s_square = s11_square - 2*(reward/cycle_length)*s12_square + (reward/cycle_length)**2*s22_square
        #print(s_square)
        
        z_alpha_2 = norm.ppf(1 - 0.05 / 2)
        interval = np.sqrt(s_square)*z_alpha_2/(cycle_length*np.sqrt(len(cycles_df)))
        ci = (reward/cycle_length-interval, reward/cycle_length+interval)
        
        return long_run_avg, ci

if __name__ == "__main__":
    AC = AnalyseCycle()
    AC.find_optimal_agents(n=86400, min_num_agents=60, max_num_agents=70, case="uniform")
    AC.find_optimal_agents(n=86400, min_num_agents=60, max_num_agents=70, case="hyperexponential")