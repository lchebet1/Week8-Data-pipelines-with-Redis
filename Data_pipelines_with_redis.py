# -*- coding: utf-8 -*-
"""Data Pipelines with Redis.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1_SN2iz8ldvWo9Qo3QZrhK-OAmWztweRd
"""

!pip install redis
import pandas as pd
import psycopg2
import redis

# Redis Cloud Instance Information
redis_host = 'redis-10924.c305.ap-south-1-1.ec2.cloud.redislabs.com'
redis_port = 10924
redis_password =  'UemTkdIXbK5G0vUKtBHU16SU8qoB9V3e'

# Postgres Database Information
pg_host = 'localhost'
pg_database = 'customer_call_logs'
pg_user = 'postgres'
pg_password = 'Dice'

# Redis Client Object
r = redis.Redis(host=redis_host, port=redis_port, password=redis_password, decode_responses=True)


def extract_data():
    # Extract data from CSV file using pandas
    data = pd.read_csv('customer_call_logs.csv')
       
    # Cache data in Redis for faster retrieval
    r.set('customer_call_logs', data.to_json(orient='records'))
    return data


def transform_data():
    # Retrieve data from Redis cache
    if r.exists('customer_call_logs'):
        data = pd.read_json(r.get('customer_call_logs'), orient='records')
    else:
        data = extract_data()

    # Transform data (clean, structure, format)
    # ...
    #remove the dollar sign from call cost and convert to numeric
    data['call_cost'] = data['call_cost'].str.replace("$", "")
    data['call_cost'] = pd.to_numeric(data['call_cost'])
    #convert call_date to datetime dtype
    data['call_date'] = pd.to_datetime(data['call_date'])
    #convert the call duration to total time(second)
    data['call_duration'] = data.loc[:, 'call_duration'].apply(lambda x: int(x[3:5])*60 + int(x[6:8]))
  
    #return transformed_data
    return data

def load_data(transformed_data:pd.DataFrame):
    # Connect to Postgres database
    conn = psycopg2.connect(host=pg_host, database=pg_database, user=pg_user, password=pg_password)

    # Create a cursor object
    cur = conn.cursor()

    # Create a table to store the data
    cur.execute('CREATE TABLE IF NOT EXISTS customer_call_logs (\
                 customer_id INT,\
                 call_cost FLOAT,\
                 call_destination VARCHAR,\
                 call_date TIMESTAMP,\
                 call_duration_sec FLOAT\
                 )')

    # Insert the transformed data into the database
    for i, row in transformed_data.iterrows():
        cur.execute(f"INSERT INTO customer_call_logs (customer_id, call_cost, call_destination, call_date, call_duration_sec) VALUES ({row['customer_id']}, {row['call_cost']}, '{row['call_destination']}', '{row['call_date']}', {row['call_duration']})")

    # Commit the changes
    conn.commit()

    # Close the cursor and connection
    cur.close()
    conn.close()

def data_pipeline():
    # Data pipeline function
    extract_data()
    transformed_data = transform_data()
    # load_data(transformed_data)
    load_data(transformed_data)

if __name__ == '__main__':
    # Run the data pipeline function
    data_pipeline()