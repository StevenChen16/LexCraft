# tools/db_cleanup.py

import psycopg2
import json
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DB_CONFIG

def clean_database():
    """清理数据库中的重复数据"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # 删除所有现有数据
        cur.execute("TRUNCATE TABLE contract_templates CASCADE")
        cur.execute("TRUNCATE TABLE special_clauses CASCADE")
        
        conn.commit()
        print("Database cleaned successfully")
        
    except Exception as e:
        print(f"Error cleaning database: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def seed_special_clauses():
    """添加完整的特殊条款集"""
    clauses = [
        # BC省特殊条款
        {
            "province": "British Columbia",
            "category": "pet",
            "clause_text": """
            Pet Addendum:
            1. The Landlord permits the Tenant to keep the following pets in the rental unit: {pet_types}.
            2. The Tenant must pay a pet damage deposit of {deposit_amount}.
            3. The Tenant is responsible for any damage caused by their pets.
            4. The Tenant must follow all strata/building rules regarding pets.
            5. The Tenant must immediately clean up after their pets in all areas.
            6. Excessive noise or disturbance from pets may result in withdrawal of permission.
            """,
            "variables": {
                "pet_types": "string",
                "deposit_amount": "currency"
            }
        },
        {
            "province": "British Columbia",
            "category": "balcony",
            "clause_text": """
            Balcony Usage Terms:
            1. The rental unit includes a private balcony for Tenant use.
            2. Tenant must keep the balcony clean and well-maintained.
            3. No alterations or installations without written permission.
            4. BBQs and other cooking equipment must comply with strata rules.
            5. No storage of unsightly items or debris on balcony.
            6. Plants must be properly contained to prevent water damage.
            7. No items to be hung over balcony railings.
            """
        },
        {
            "province": "British Columbia",
            "category": "parking",
            "clause_text": """
            Parking Agreement:
            1. Tenant is assigned parking stall(s): {stall_numbers}
            2. Monthly parking fee: {fee_amount} per stall
            3. Parking is for private passenger vehicles only
            4. No vehicle repairs or maintenance in parking area
            5. Vehicles must be licensed and in operating condition
            6. No storage of other items in parking stall
            7. Tenant must follow all parking area rules and regulations
            """,
            "variables": {
                "stall_numbers": "string",
                "fee_amount": "currency"
            }
        },
        {
            "province": "British Columbia",
            "category": "smoking",
            "clause_text": """
            Smoking Policy:
            1. This is a {smoking_status} building
            2. Smoking is {smoking_areas}
            3. Policy applies to tobacco, cannabis, and vaping
            4. Tenant responsible for any smoking-related damage
            5. Violation may result in tenancy termination
            """,
            "variables": {
                "smoking_status": "string",
                "smoking_areas": "string"
            }
        },
        
        # Ontario省特殊条款
        {
            "province": "Ontario",
            "category": "pet",
            "clause_text": """
            Pet Policy:
            1. Tenant may keep the following pets: {pet_types}
            2. All pets must be licensed and vaccinated as required by law
            3. Tenant responsible for pet-related damages
            4. Tenant must clean up after pets immediately
            5. Excessive noise or disturbance not permitted
            6. No breeding or commercial pet activities
            """,
            "variables": {
                "pet_types": "string"
            }
        },
        {
            "province": "Ontario",
            "category": "balcony",
            "clause_text": """
            Balcony Agreement:
            1. Balcony is for residential use only
            2. Must maintain cleanliness and appearance
            3. No permanent alterations without consent
            4. No storage of unsightly items
            5. BBQ use subject to local bylaws
            6. No throwing items or shaking rugs/mops
            7. Snow/ice must be removed from balcony
            """
        },
        {
            "province": "Ontario",
            "category": "maintenance",
            "clause_text": """
            Maintenance Terms:
            1. Tenant responsible for basic unit maintenance
            2. Must report needed repairs promptly
            3. Keep all fixtures clean and well-maintained
            4. Proper garbage/recycling disposal required
            5. No modifications without written consent
            6. Maintain reasonable humidity levels
            7. Regular cleaning of appliances required
            """
        },
        {
            "province": "Ontario",
            "category": "insurance",
            "clause_text": """
            Insurance Requirements:
            1. Tenant must maintain insurance with {min_coverage} liability
            2. Policy must cover: {coverage_types}
            3. Landlord to be named as additional insured
            4. Proof of insurance required annually
            5. Coverage must be maintained throughout tenancy
            """,
            "variables": {
                "min_coverage": "currency",
                "coverage_types": "string"
            }
        }
    ]
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        for clause in clauses:
            cur.execute("""
                INSERT INTO special_clauses 
                (province, category, clause_text, variables)
                VALUES (%s, %s, %s, %s)
            """, (
                clause['province'],
                clause['category'],
                clause['clause_text'],
                json.dumps(clause.get('variables', {}))
            ))
        
        conn.commit()
        print("Special clauses added successfully")
        
    except Exception as e:
        print(f"Error adding special clauses: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    print("Starting database cleanup and initialization...")
    clean_database()
    seed_special_clauses()
    print("Database cleanup and initialization completed")
    print("Please use ContractParser to import standard lease PDFs")
    print("Example usage:")
    print("  from tools.contract_parser import import_contract_template")
    print("  import_contract_template('path/to/ontario_lease.pdf', 'Ontario')")
    print("  import_contract_template('path/to/bc_lease.pdf', 'British Columbia')")