#!/usr/bin/env python3
"""
Complete diagnostic script for Dameng ORM issues
Helps identify table/column naming problems
"""

import asyncio
import dmPython
from typing import Any, Dict, List


def direct_db_check():
    """Direct database checks without ORM"""
    print("\n" + "=" * 80)
    print("DIRECT DATABASE CHECKS")
    print("=" * 80)
    
    try:
        conn = dmPython.connect('SYSDBA', 'SYSDBA', '10.50.1.108:30236', 'deepflow')
        cursor = conn.cursor()
        
        # Check 1: Find all tables with 'region' in name
        print("\n[1] Tables with 'region' in name:")
        cursor.execute("""
            SELECT table_name FROM all_tables 
            WHERE UPPER(table_name) LIKE '%REGION%'
        """)
        tables = cursor.fetchall()
        
        if tables:
            for (table_name,) in tables:
                print(f"    ✓ Found: {table_name}")
                
                # Get column info for this table
                cursor.execute(f"""
                    SELECT column_name, data_type, nullable, column_id
                    FROM all_tab_columns
                    WHERE table_name = '{table_name}'
                    ORDER BY column_id
                """)
                columns = cursor.fetchall()
                
                print(f"      Columns ({len(columns)}):")
                for col_name, col_type, nullable, col_id in columns:
                    null_str = "NULL" if nullable == "Y" else "NOT NULL"
                    print(f"        {col_id}: {col_name} ({col_type}) {null_str}")
                
                # Check row count
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                (count,) = cursor.fetchone()
                print(f"      Row count: {count}")
                
                # Try different quoting styles
                print(f"      Query tests:")
                
                # Test uppercase quotes
                try:
                    cursor.execute(f'SELECT * FROM "{table_name.upper()}" LIMIT 1')
                    rows = cursor.fetchall()
                    print(f"        ✓ \"{{table_name.upper()}}\" returned {len(rows)} row(s)")
                except Exception as e:
                    print(f"        ✗ \"{{table_name.upper()}}\" failed: {e}")
                
                # Test lowercase quotes  
                try:
                    cursor.execute(f'SELECT * FROM "{table_name.lower()}" LIMIT 1')
                    rows = cursor.fetchall()
                    print(f"        ✓ \"{{table_name.lower()}}\" returned {len(rows)} row(s)")
                except Exception as e:
                    print(f"        ✗ \"{{table_name.lower()}}\" failed: {e}")
                
                # Test unquoted
                try:
                    cursor.execute(f"SELECT * FROM {table_name} LIMIT 1")
                    rows = cursor.fetchall()
                    print(f"        ✓ unquoted returned {len(rows)} row(s)")
                except Exception as e:
                    print(f"        ✗ unquoted failed: {e}")
        else:
            print("    ✗ No tables found with 'region' in name")
            print("\n    Available tables:")
            cursor.execute("SELECT table_name FROM all_tables LIMIT 20")
            for (table_name,) in cursor.fetchall():
                print(f"      - {table_name}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"    ✗ Database error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def orm_check():
    """ORM-based checks"""
    print("\n" + "=" * 80)
    print("ORM-BASED CHECKS")
    print("=" * 80)
    
    try:
        from tortoise import Tortoise, fields
        from tortoise.models import Model
        
        # Define test model
        class Region(Model):
            id = fields.IntField(pk=True)
            name = fields.CharField(max_length=255)
            
            class Meta:
                table = "region"
        
        print("\n[2] Initializing Tortoise ORM...")
        await Tortoise.init(
            db_url="dm://SYSDBA:SYSDBA@10.50.1.108:30236/deepflow",
            modules={"models": ["__main__"]}
        )
        print("    ✓ ORM initialized")
        
        # Test queries
        print("\n[3] Testing ORM queries...")
        
        try:
            count = await Region.all().count()
            print(f"    ✓ Region.all().count() = {count}")
            
            if count > 0:
                region = await Region.first()
                print(f"    ✓ Region.first() = ID: {region.id}, Name: {region.name}")
                
                # List all
                all_regions = await Region.all()
                print(f"    ✓ Retrieved {len(all_regions)} regions")
                for i, r in enumerate(all_regions[:3]):
                    print(f"      [{i+1}] ID: {r.id}, Name: {r.name}")
                if len(all_regions) > 3:
                    print(f"      ... and {len(all_regions) - 3} more")
            else:
                print("    ✗ No regions found via ORM")
        
        except Exception as e:
            print(f"    ✗ ORM query failed: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
        
        await Tortoise.close_connections()
        
    except Exception as e:
        print(f"    ✗ ORM error: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


async def main():
    """Run all diagnostics"""
    print("\n" + "#" * 80)
    print("# DAMENG ORM DIAGNOSTIC REPORT")
    print("#" * 80)
    
    # Direct database checks
    direct_db_check()
    
    # ORM checks
    await orm_check()
    
    print("\n" + "#" * 80)
    print("# END OF DIAGNOSTIC REPORT")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
