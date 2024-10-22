from flask import Flask, render_template_string
import  pandas as pd
from tabulate import tabulate
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Welcome to DVM API!'

@app.route('/dvm-data/', methods=['GET'])
def get_dvm_data_csv(): 
    data = pd.read_csv('table.csv')
    data_inverted = data.sort_index(ascending=False)
    # Render an HTML table using tabulate
    column_names = ['timestamp', 'Tellor submitValue transaction link', 'query_type', 'asset', 'currency', 'value', 'disputable?', 'chain_id']
    table_html = '<pre>' + tabulate(data_inverted.values[:, 1:], headers=column_names, tablefmt="grid") + '</pre>'
    return render_template_string(table_html)

if __name__ == '__main__':
    app.run(debug=True)