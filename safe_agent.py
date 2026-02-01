
class SafeAgent:
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.pos = None