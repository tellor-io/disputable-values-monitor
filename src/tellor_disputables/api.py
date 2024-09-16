from flask import Flask, send_file, abort
import os

app = Flask(__name__)

@app.route('/')
def home():
    return 'Welcome to the Flask File API!'

@app.route('/price-data/<string:id>/csv', methods=['GET'])
def get_price_data_csv(id): 
    csv_path = f'../../{id}_data.csv'
    
    # Check if the file exists
    if not os.path.exists(csv_path):
        abort(404, description=f'CSV file with ID {id} not found.')
    
    # Send the file
    return send_file(csv_path, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)