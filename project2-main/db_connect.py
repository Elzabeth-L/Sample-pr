"""
Reusable database connection module for Amazon RDS MySQL instance.
Handles connection management and provides a simple interface for database operations.
"""

import os
import mysql.connector
from mysql.connector import Error

# Database connection configuration
DB_HOST = os.environ.get("DB_HOST", "elzabeth-db.cvyakmciw3a7.ap-south-1.rds.amazonaws.com")
DB_PORT = int(os.environ.get("DB_PORT", 3306))  # Standard MySQL RDS port
DB_USER = os.environ.get("DB_USER", "admin")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "DBpassword30")
DB_NAME = os.environ.get("DB_NAME", "restaurant")
DB_CONNECT_TIMEOUT = int(os.environ.get("DB_CONNECT_TIMEOUT", 10))
DB_SSL_CA = os.environ.get("DB_SSL_CA", "/root/global-bundle.pem")  # path to CA bundle, e.g. /home/ubuntu/global-bundle.pem
DB_SSL_VERIFY_CERT = os.environ.get("DB_SSL_VERIFY_CERT", "true").lower() in ("1", "true", "yes")


def get_connection():
    """
    Create and return a connection to the MySQL database.
    
    Returns:
        mysql.connector.MySQLConnection: A live database connection object.
        
    Raises:
        mysql.connector.Error: If connection fails.
    """
    try:
        # Build SSL options only when a CA path is provided
        ssl_opts = {}
        if DB_SSL_CA:
            ssl_opts["ssl_ca"] = DB_SSL_CA
            # mysql.connector expects ssl_verify_cert to be a boolean
            ssl_opts["ssl_verify_cert"] = DB_SSL_VERIFY_CERT

        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            connection_timeout=DB_CONNECT_TIMEOUT,
            autocommit=True,
            **ssl_opts
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL Database: {e}")
        raise


def get_connection_without_db():
    """
    Create and return a connection without specifying a database.
    Used for creating databases that don't exist yet.
    
    Returns:
        mysql.connector.MySQLConnection: A live database connection object.
        
    Raises:
        mysql.connector.Error: If connection fails.
    """
    try:
        ssl_opts = {}
        if DB_SSL_CA:
            ssl_opts["ssl_ca"] = DB_SSL_CA
            ssl_opts["ssl_verify_cert"] = DB_SSL_VERIFY_CERT

        conn = mysql.connector.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            connection_timeout=DB_CONNECT_TIMEOUT,
            autocommit=True,
            **ssl_opts
        )
        return conn
    except Error as e:
        print(f"Error connecting to MySQL Database (no-db): {e}")
        raise


if __name__ == "__main__":
    # Test connection with a simple SELECT NOW() query
    print("Testing database connection...")
    try:
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Run test query
        cursor.execute("SELECT NOW() as current_time")
        result = cursor.fetchone()
        print(f"✓ Connection successful!")
        print(f"  Server time: {result['current_time']}")
        
        cursor.close()
        conn.close()
        print("✓ Connection closed successfully.")
    except Exception as e:
        print(f"✗ Connection failed: {e}")
        # Helpful debug hints when connection hangs/fails
        print("Hints:")
        print(" - Verify RDS endpoint and port are correct:", DB_HOST, DB_PORT)
        print(" - Ensure the RDS security group allows inbound TCP/3306 from your IP or the EC2/host you're running from.")
        print(" - If RDS is not publicly accessible, run this from an AWS resource in the same VPC or use an SSH tunnel.")
        print(" - Try a raw TCP test: `nc -vz {host} {port}` or a Python socket connect to test reachability.")
        print("You can override connection settings with env vars: DB_HOST, DB_PORT, DB_USER, DB_PASSWORD, DB_NAME, DB_CONNECT_TIMEOUT")
