export PYTHONPATH=$PYTHONPATH:$PWD/.venv/lib/python3.12/site-packages
export PATH=$PATH:$PWD/.venv/bin
FLASK_APP=gentelella.py flask run --host=0.0.0.0 --port=4534
