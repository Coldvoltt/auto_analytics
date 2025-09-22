#!/usr/bin/env python
import sys
from crew import AnalyticsCrew
import os


def run():
    """
    Run the crew.
    """
    # Get the absolute path to the data file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(current_dir, 'data', 'data.csv')

    inputs = {
        'file_path': data_path  # Using absolute path to the CSV file       
    }
    
    crew = AnalyticsCrew()
    crew.crew().kickoff(inputs=inputs)


if __name__ == "__main__":
    run()
