"""
Start the Control Catalogue authoring web interface.

    pip install flask
    python run_authoring.py

Then open http://127.0.0.1:5001
"""
from rule_authoring.app import app

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5001, debug=True)
