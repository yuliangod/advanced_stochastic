import random
from collections import deque
from typing import Literal

import numpy as np

from model.customer import Customer

# Define constants
ARRIVAL_RATE = 20/60  # Average arrivals per second

np.random.seed(42)


class Arrivals():
    def __init__(self):
        self.next_arrival_time = 0
    
    # at the next time step, update customers_queue
    def update_queue(self, customers_queue:list[Customer], current_time:int, case:Literal["uniform", "hyperexponential"], completed_list:list[Customer]):
        for customer in customers_queue:
            customer.patience_left -= 1
            # remove from customers_queue and add to completed list when patience left is 0
            if customer.patience_left <= 0:
                customer.exit_time = current_time
                customer.abandon = True
                customers_queue.remove(customer)
                completed_list.append(customer)
                
        if current_time == self.next_arrival_time:
            #print("Current time", current_time)
            self.add_all_arrivals_to_queue(customers_queue=customers_queue, arrival_time=current_time, case=case)

        return customers_queue, completed_list
    
    def add_all_arrivals_to_queue(self, customers_queue:list[Customer], arrival_time:int, case:Literal["uniform", "hyperexponential"]):
        customers_queue = self.add_customer_to_queue(customers_queue=customers_queue, arrival_time=arrival_time, case=case)
        interarrival_time = self.generate_interarrival_time()
        self.next_arrival_time += interarrival_time
        #print("Next arrival at", self.next_arrival_time)
        #print(interarrival_time)
        
        if interarrival_time == 0:
            customers_queue = self.add_all_arrivals_to_queue(customers_queue=customers_queue, arrival_time=arrival_time, case=case)

        return customers_queue
    
    def add_customer_to_queue(self, customers_queue:list[Customer], arrival_time:int, case:Literal["uniform", "hyperexponential"]):
        customers_queue.append(Customer(arrival_time=arrival_time, patience_left=self.generate_patience_time(case=case)))
        return customers_queue
    
    # Generate patience time T
    def generate_patience_time(self, case:Literal["uniform", "hyperexponential"]):
        if case == "uniform":
            return round(random.uniform(0, 6*60))  # Uniformly distributed [0, 6] minutes
        elif case == "hyperexponential":
            if random.random() < 0.5:  # Probability 1/2
                return round(np.random.exponential(1*60))  # Mean = 1 minute
            else:
                return round(np.random.exponential(5*60))  # Mean = 5 minutes

    # Helper function to generate inter-arrival times
    def generate_interarrival_time(self):
        return round(np.random.exponential(1 / ARRIVAL_RATE))  # Poisson arrivals
    
def demo():
    A = Arrivals()

    customers_queue = []
    completed_list = []
    for i in range(1000):
        print("Time period:", i)
        customers_queue, completed_list = A.update_queue(customers_queue=customers_queue, current_time=i, case="uniform", completed_list=completed_list)
        print("Num of customers in queue:", len(customers_queue))
        print("Num of customers completed:", len(completed_list))
        
if __name__ == "__main__":
    demo()