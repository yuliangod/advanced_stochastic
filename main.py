import numpy as np

from model.customer import Customer
from service import Service

customer_queue = []
agents_list = []
S = Service(num_of_agents=60)
for i in range(100):
    print("Time period:", i)
    customers_queue = [Customer(arrival_time=i, patience_left=1) for _ in range(np.random.randint(0, 10))]
    agents_list = S.agents_serve_customers_in_queue(customers_queue=customers_queue, agents_list=agents_list)