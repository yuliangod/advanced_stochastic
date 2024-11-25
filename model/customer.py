class Customer:
    def __init__(self, arrival_time:int, patience_left:int):
        self.arrival_time = arrival_time
        self.exit_time = None
        self.patience_left = patience_left
        self.abandon = None