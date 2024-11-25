import numpy as np

from model.agent import Agent
from model.customer import Customer

np.random.seed(42)


class Service():
    def __init__(self, num_of_agents:int):
        self.num_of_agents = num_of_agents
        self.agents_list = []
    
    def agents_serve_customers_in_queue(self, customers_queue:list[Customer], agents_list:list[Agent]) -> tuple[list[Agent], int]:
        # clear of agents who finished serving customer
        agents_list = self.clear_agents_who_finished_serving(agents_list=agents_list)
        num_of_available_agents_left = self.num_of_agents - len(agents_list)
        num_of_customers_in_queue = len(customers_queue)
        print("Num of available agents left:", num_of_available_agents_left)
        print("Num of customers in queue:", len(customers_queue))
        
        customers_served = min(num_of_available_agents_left, num_of_customers_in_queue)
        print("Num of customers served:", customers_served)
        customers_queue = customers_queue[customers_served:]
        print("Num of customers left in queue", len(customers_queue))
        agents_list += [Agent(service_time=round(np.random.exponential(scale=3*60))) for _ in range(customers_served)]
        agents_list = self.service_time_left_next_second(agents_list=agents_list)
            
        return agents_list
    
    def service_time_left_next_second(self, agents_list:list[Agent]):
        for agent in agents_list:
            agent.service_time_left -= 1
            #print(agent.service_time, agent.service_time_left)

        return agents_list
    
    def clear_agents_who_finished_serving(self, agents_list:list[Agent]):
        #completed_agents_list += [agent for agent in agents_list if agent.service_time_left <= 0]
        agents_list = [agent for agent in agents_list if agent.service_time_left > 0]
        return agents_list
    
def demo():
    S = Service(num_of_agents=60)
    agents_list = S.agents_serve_customers_in_queue([], agents_list=[])
    for i in range(1, 100):
        print("Time period:", i)
        customers_queue = [Customer(arrival_time=i, patience_left=1) for _ in range(np.random.randint(0, 10))]
        agents_list = S.agents_serve_customers_in_queue(customers_queue=customers_queue, agents_list=agents_list)
    
if __name__ == "__main__":
    demo()