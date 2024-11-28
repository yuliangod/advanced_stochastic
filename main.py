import numpy as np

from arrivals import Arrivals
from model.customer import Customer
from service import Service

agents_list = []
customers_queue = []
completed_list = []

A = Arrivals()
S = Service(num_of_agents=60)

for i in range(1000):
    print("Time period:", i)
    customers_queue, completed_list = A.update_queue(customers_queue=customers_queue, current_time=i, case="uniform", completed_list=completed_list)
    print("Num of customers in queue:", len(customers_queue))

    agents_list, completed_list, customers_queue = S.agents_serve_customers_in_queue(customers_queue=customers_queue, agents_list=agents_list, completed_list=completed_list, current_time=i)
    print("Length of completed list", len(completed_list))
    print("Num of customers left in queue", len(customers_queue))
    
for customer in completed_list:
    print("Arrival time:", customer.arrival_time, "Exit time:", customer.exit_time, "Abandon:", customer.abandon)