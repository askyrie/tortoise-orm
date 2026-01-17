#!/usr/bin/env python3
"""
Diagnostic script to check Dameng schema and ORM query issues
"""

import asyncio
import dmPython

async def diagnose_dameng():
    """Diagnose Dameng database schema issues"""
    
    try:
        # Direct connection to Dameng
        conn = dmPython.connect(
            'SYSDBA',
            'SYSDBA',
            '10.50.1.108:30236',
            'deepflow'
        )
        
        cursor = conn.cursor()
        
        print("=" * 80)
        print("DAMENG DATABASE DIAGNOSTIC REPORT")
        print("=" * 80)
        
        # Check table structure
        print("\n1. TABLE STRUCTURE:")
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, NULLABLE
            FROM all_tab_columns
            WHERE TABLE_NAME = 'REGION'
            ORDER BY COLUMN_ID
        """)
        
        columns_info = cursor.fetchall()
        print(f"\nColumns in 'REGION' table:")
        print(f"{'Column Name':<20} {'Data Type':<15} {'Nullable':<10}")
        print("-" * 45)
        
        for col_info in columns_info:
            col_name = col_info[0]
            col_type = col_info[1]
            nullable = col_info[2]
            print(f"{col_name:<20} {col_type:<15} {nullable:<10}")
        
        # Check data count
        print("\n2. DATA VERIFICATION:")
        cursor.execute("SELECT COUNT(*) as row_count FROM \"REGION\"")
        result = cursor.fetchone()
        print(f"\nTotal rows in REGION table (uppercase quotes): {result[0]}")
        
        cursor.execute('SELECT COUNT(*) as row_count FROM "region"')
        result = cursor.fetchone()
        print(f"Total rows in region table (lowercase quotes): {result[0]}")
        
        # Check actual data
        print("\n3. DATA SAMPLE (with uppercase column references):")
        cursor.execute('SELECT "ID", "NAME" FROM "REGION" LIMIT 3')
        data = cursor.fetchall()
        print(f"\nUsing uppercase column names \"ID\", \"NAME\":")
        print(f"  Rows returned: {len(data)}")
        for row in data:
            print(f"  - {row}")
        
        print("\n4. DATA SAMPLE (with lowercase column references):")
        cursor.execute('SELECT "id", "name" FROM "REGION" LIMIT 3')
        data = cursor.fetchall()
        print(f"\nUsing lowercase column names \"id\", \"name\":")
        print(f"  Rows returned: {len(data)}")
        for row in data:
            print(f"  - {row}")
            
        except Exception as e:
            print(f"ERROR: {e}")
        finally:
            cursor.close()
            conn.close()

if __name__ == "__main__":
    asyncio.run(diagnose_dameng())
