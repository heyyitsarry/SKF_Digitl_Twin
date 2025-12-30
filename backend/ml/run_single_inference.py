#!/usr/bin/env python3
"""
Single inference runner - called by Node.js API
Usage: python run_single_inference.py '{"id": 1, "SPEED": 16000, ...}'
"""

import sys
import json
from spindle_inference_PCA import run_inference

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No input data provided"}))
        sys.exit(1)
    
    try:
        # Parse input JSON
        raw_row = json.loads(sys.argv[1])
        
        # Run inference
        result = run_inference(raw_row)
        
        # Output as JSON
        print(json.dumps(result))
        sys.exit(0)
        
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)
