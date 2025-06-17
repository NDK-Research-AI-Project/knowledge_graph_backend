from typing import List

class ExplanationHandler:
    def __init__(self):
        self.steps: List[str] = []
    
    def add_step(self, step: str):
        """Add a step to the explanation"""
        self.steps.append(step)
    
    def get_explanation(self) -> List[str]:
        """Get the complete explanation as a list of steps"""
        return self.steps.copy()  # Return a copy to prevent external modification
    
    def clear(self):
        """Clear all recorded steps"""
        self.steps = [] 