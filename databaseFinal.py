import pandas as pd
import numpy as np
import mysql.connector
from mysql.connector import Error

def create_database_connection():
    try:
        connection = mysql.connector.connect(
            host="localhost",
            user="root",
            password="Password123",
            database="finalProject"
        )
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def organize_data_by_tables(df):
    df_copy = df.copy()
    df_copy.columns = df_copy.columns.str.lower()
    required_columns = ['product_name', 'upc']
    
    missing_columns = [col for col in required_columns if col not in df_copy.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")
    
    column_types = {}
    for column in df_copy.columns:
        first_value = df_copy[column].iloc[0]
        column_type = 'string'
        
        if isinstance(first_value, (int, float, np.int64, np.float64)):
            if '$' in str(first_value) or '.' in str(first_value):
                column_type = 'dollar'
            else:
                column_type = 'number'
        
        column_types[column] = column_type

    for column, type_ in column_types.items():
        if type_ == 'dollar':
            df_copy[column] = df_copy[column].apply(lambda x: float(str(x).replace('$', '').replace(',', '')))

    return {'data': df_copy, 'column_types': column_types}

def create_table(connection, table_name, df, column_types):
    cursor = connection.cursor()
    
    mysql_data_types = {
        'string': 'VARCHAR(255)',
        'dollar': 'DECIMAL(10,2)',
        'number': 'BIGINT'
    }
    
    columns = []
    for col in df.columns:
        dtype = mysql_data_types.get(column_types.get(col, 'string'), 'VARCHAR(255)')
        columns.append(f"`{col}` {dtype}")
    
    create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INT AUTO_INCREMENT PRIMARY KEY,
        {', '.join(columns)},
        UNIQUE KEY `upc` (`upc`)
    )
    """
    
    cursor.execute(create_table_query)
    connection.commit()

def validate_data(df):
    print(f"\nValidating {len(df)} records...")
    print("Checking for null values...")
    null_counts = df.isnull().sum()
    if null_counts.sum() > 0:
        print("Warning: Null values found in the following columns:")
        print(null_counts[null_counts > 0])
    else:
        print("No null values found.")
    
    print(f"\nUPC range: {df['upc'].min()} to {df['upc'].max()}")
    return True

def insert_data(connection, table_name, df):
    cursor = connection.cursor()
    
    try:
        columns = [f"`{col}`" for col in df.columns]
        placeholders = ["%s"] * len(df.columns)
        
        insert_query = f"""
        INSERT INTO {table_name} ({', '.join(columns)})
        VALUES ({', '.join(placeholders)})
        ON DUPLICATE KEY UPDATE
        {', '.join([f"`{col}` = VALUES(`{col}`)" for col in df.columns])}
        """
        
        values = df.replace({np.nan: None}).values.tolist()
        cursor.executemany(insert_query, values)
        connection.commit()
        
        print(f"Number of records processed: {cursor.rowcount}")
        
    except Error as e:
        print(f"Error inserting data: {e}")
        connection.rollback()
        raise
    finally:
        cursor.close()

def main():
    try:
        excel_file = "testData.xlsx"
        table_name = excel_file.replace('.xlsx', '').replace('.xls', '').lower()
        
        print("Starting database operations...")
        print(f"Processing file: {excel_file}")
        
        df = pd.read_excel(excel_file)
        df.columns = df.columns.str.lower().str.replace(' ', '_')
        
        connection = create_database_connection()
        if connection is None:
            return
        
        data_info = organize_data_by_tables(df)
        
        if not validate_data(data_info['data']):
            print("Data validation failed. Aborting.")
            return
        
        cursor = connection.cursor()
        cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        connection.commit()
        
        create_table(connection, table_name, data_info['data'], data_info['column_types'])
        insert_data(connection, table_name, data_info['data'])
        
        cursor = connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"\nTotal records in database: {count}")
        
        print("\nOperation completed successfully")
        
    except Exception as e:
        print(f"\nError: {type(e).__name__}")
        print(f"Description: {str(e)}")
        
    finally:
        if 'connection' in locals() and connection.is_connected():
            connection.close()
            print("\nDatabase connection closed")

if __name__ == "__main__":
    main()