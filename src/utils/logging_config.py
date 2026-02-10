# Use Python's logging module + experiment tracking
import logging
import json
from datetime import datetime

class ExperimentLogger:
    def __init__(self, experiment_name):
        self.results = {
            "experiment": experiment_name,
            "timestamp": datetime.now().isoformat(),
            "parameters": {},
            "runs": []
        }
    
    def log_run(self, instance, result, time, parameters):
        self.results["runs"].append({
            "instance": instance,
            "cost": result,
            "time": time,
            "params": parameters
        })
    
    def save(self):
        filename = f"experiments/results/{self.results['experiment']}_{self.results['timestamp']}.json"
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2)