from flask import Flask, render_template, jsonify, request
import mysql.connector
from mysql.connector import Error
import decimal

app = Flask(__name__)

def get_database_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Password123",
        database="finalProject"
    )

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/data')
def get_data():
    try:
        connection = get_database_connection()
        cursor = connection.cursor(dictionary=True)
        
        search_term = request.args.get('search', '').strip()
        search_type = request.args.get('searchType', 'product_name')
        compare_type = request.args.get('compareType', 'contains')
        dimension_type = request.args.get('dimensionType', 'height')
        sort_column = request.args.get('sort', 'product_name')
        sort_direction = request.args.get('direction', 'asc')
        
        # Ensure the sort column is properly escaped
        sort_column = f"`{sort_column}`"
        
        query = "SELECT * FROM testdata WHERE 1=1"
        params = []
        
        if search_term:
            if search_type == 'upc':
                query += " AND CAST(upc AS CHAR) LIKE %s"
                params.append(f"%{search_term}%")
            elif search_type == 'product_type':
                query += " AND LOWER(product_type) LIKE LOWER(%s)"
                params.append(f"%{search_term}%")
            elif search_type == 'box_dimensions':
                try:
                    search_value = float(search_term)
                    dimension_index = {'height': 1, 'width': 2, 'length': 3}[dimension_type]
                    
                    if dimension_index == 1:
                        dimension_extract = "CAST(SUBSTRING_INDEX(`box_dimensions_(inches)`, 'x', 1) AS DECIMAL)"
                    elif dimension_index == 2:
                        dimension_extract = "CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(`box_dimensions_(inches)`, 'x', 2), 'x', -1) AS DECIMAL)"
                    else:
                        dimension_extract = "CAST(SUBSTRING_INDEX(`box_dimensions_(inches)`, 'x', -1) AS DECIMAL)"
                    
                    if compare_type == 'greater_equal':
                        query += f" AND {dimension_extract} >= %s"
                    elif compare_type == 'less_equal':
                        query += f" AND {dimension_extract} <= %s"
                    elif compare_type == 'equals':
                        query += f" AND {dimension_extract} = %s"
                    
                    params.append(search_value)
                except ValueError:
                    return jsonify({'error': 'Invalid number format'}), 400
            elif search_type == 'shipping_dimensions':
                try:
                    search_value = float(search_term)
                    dimension_index = {'height': 1, 'width': 2, 'length': 3}[dimension_type]
                    
                    if dimension_index == 1:
                        dimension_extract = "CAST(SUBSTRING_INDEX(`shipping_box_dimensions_(inches)`, 'x', 1) AS DECIMAL)"
                    elif dimension_index == 2:
                        dimension_extract = "CAST(SUBSTRING_INDEX(SUBSTRING_INDEX(`shipping_box_dimensions_(inches)`, 'x', 2), 'x', -1) AS DECIMAL)"
                    else:
                        dimension_extract = "CAST(SUBSTRING_INDEX(`shipping_box_dimensions_(inches)`, 'x', -1) AS DECIMAL)"
                    
                    if compare_type == 'greater_equal':
                        query += f" AND {dimension_extract} >= %s"
                    elif compare_type == 'less_equal':
                        query += f" AND {dimension_extract} <= %s"
                    elif compare_type == 'equals':
                        query += f" AND {dimension_extract} = %s"
                    
                    params.append(search_value)
                except ValueError:
                    return jsonify({'error': 'Invalid number format'}), 400
            elif search_type == 'cost_unit':
                if compare_type == 'greater_equal':
                    query += " AND `cost_per_unit_(usd)` >= %s"
                elif compare_type == 'less_equal':
                    query += " AND `cost_per_unit_(usd)` <= %s"
                elif compare_type == 'equals':
                    query += " AND `cost_per_unit_(usd)` = %s"
                try:
                    params.append(float(search_term))
                except ValueError:
                    return jsonify({'error': 'Invalid number format'}), 400
            elif search_type == 'cost_box':
                if compare_type == 'greater_equal':
                    query += " AND `cost_per_shipping_box_(usd)` >= %s"
                elif compare_type == 'less_equal':
                    query += " AND `cost_per_shipping_box_(usd)` <= %s"
                elif compare_type == 'equals':
                    query += " AND `cost_per_shipping_box_(usd)` = %s"
                try:
                    params.append(float(search_term))
                except ValueError:
                    return jsonify({'error': 'Invalid number format'}), 400
            elif search_type == 'sell_rate':
                if compare_type == 'greater_equal':
                    query += " AND sell_rate >= %s"
                elif compare_type == 'less_equal':
                    query += " AND sell_rate <= %s"
                elif compare_type == 'equals':
                    query += " AND sell_rate = %s"
                try:
                    params.append(float(search_term))
                except ValueError:
                    return jsonify({'error': 'Invalid number format'}), 400
            else:  # product_name
                query += " AND LOWER(product_name) LIKE LOWER(%s)"
                params.append(f"%{search_term}%")
        
        # Special handling for shipping size sorting
        if sort_column == '`standard_shipping_size`':
            query += " ORDER BY FIELD(standard_shipping_size, 'Small', 'Medium', 'Large', 'Oversized')"
            if sort_direction == 'desc':
                query += " DESC"
        else:
            query += f" ORDER BY {sort_column} {sort_direction}"
        
        cursor.execute(query, params)
        data = cursor.fetchall()
        
        # Convert Decimal objects to float for JSON serialization
        for row in data:
            for key, value in row.items():
                if isinstance(value, decimal.Decimal):
                    row[key] = float(value)
        
        return jsonify(data)
        
    except Error as e:
        print(f"Database error: {str(e)}")
        return jsonify({'error': str(e)}), 500
    finally:
        if connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True)