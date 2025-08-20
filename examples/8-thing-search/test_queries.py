#!/usr/bin/env python3
"""
Simple query execution script for Eclipse Ditto.
Executes each query once and pretty prints the results.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

import httpx

# Determine important directories
THIS_FILE: Path = Path(__file__).resolve()
TEST_ROOT: Path = THIS_FILE.parent


def load_queries(query_file: str) -> List[Tuple[str, str]]:
    """Load queries from a JSON file."""
    try:
        query_path = TEST_ROOT / query_file
        if not query_path.exists():
            print(f"❌ Query file not found: {query_path}")
            sys.exit(1)
            
        with open(query_path, 'r') as f:
            data = json.load(f)
        
        queries = []
        for query in data.get("queries", []):
            description = query.get("description", "Unknown query")
            rql = query.get("rql", "")
            if rql:
                queries.append((description, rql))
        
        if not queries:
            print("❌ No valid queries found in the file")
            sys.exit(1)
            
        return queries
        
    except Exception as e:
        print(f"❌ Error loading queries: {e}")
        sys.exit(1)


def execute_query(client: httpx.Client, rql: str, ditto_url: str, 
                 auth_user: str, auth_pass: str) -> Dict[str, Any]:
    """Execute a single RQL query and return the result."""
    try:
        url = f"{ditto_url}/search/things"
        params = {"filter": rql}
        
        response = client.get(
            url,
            params=params,
            auth=(auth_user, auth_pass),
            timeout=60.0
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "status_code": response.status_code,
                "data": response.json(),
                "count": len(response.json().get("items", [])),
                "response_size": len(response.content)
            }
        else:
            return {
                "status": "error",
                "status_code": response.status_code,
                "error": response.text,
                "count": 0,
                "response_size": len(response.content)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "status_code": None,
            "error": str(e),
            "count": 0,
            "response_size": 0
        }


def get_all_things(client: httpx.Client, ditto_url: str, 
                   auth_user: str, auth_pass: str) -> Dict[str, Any]:
    """Get all things in the system."""
    try:
        url = f"{ditto_url}/search/things"
        
        response = client.get(
            url,
            auth=(auth_user, auth_pass),
            timeout=60.0
        )
        
        if response.status_code == 200:
            return {
                "status": "success",
                "status_code": response.status_code,
                "data": response.json(),
                "count": len(response.json().get("items", [])),
                "response_size": len(response.content)
            }
        else:
            return {
                "status": "error",
                "status_code": response.status_code,
                "error": response.text,
                "count": 0,
                "response_size": len(response.content)
            }
            
    except Exception as e:
        return {
            "status": "error",
            "status_code": None,
            "error": str(e),
            "count": 0,
            "response_size": 0
        }


def pretty_print_result(description: str, rql: str, result: Dict[str, Any]):
    """Pretty print a query result."""
    print("=" * 80)
    print(f"🔍 Query: {description}")
    print("-" * 80)
    print(f"📝 RQL: {rql}")
    print("-" * 80)
    
    if result["status"] == "success":
        print(f"✅ Status: HTTP {result['status_code']}")
        print(f"📊 Results: {result['count']} things found")
        print(f"📦 Response size: {result['response_size']} bytes")
        
        # Show first few results if any
        items = result["data"].get("items", [])
        if items:
            print(f"\n📋 First {min(3, len(items))} results:")
            for i, item in enumerate(items[:3]):
                thing_id = item.get("thingId", "Unknown")
                print(f"  {i+1}. {thing_id}")
            
            if len(items) > 3:
                print(f"  ... and {len(items) - 3} more")
        else:
            print("\n📋 No results found")
            
    else:
        print(f"❌ Status: Error")
        if result["status_code"]:
            print(f"📊 HTTP Status: {result['status_code']}")
        print(f"💥 Error: {result['error']}")
    
    print()


def pretty_print_all_things(result: Dict[str, Any]):
    """Pretty print all things in the system."""
    print("=" * 80)
    print("🔍 ALL THINGS IN SYSTEM")
    print("=" * 80)
    
    if result["status"] == "success":
        print(f"✅ Status: HTTP {result['status_code']}")
        print(f"📊 Total things: {result['count']}")
        print(f"📦 Response size: {result['response_size']} bytes")
        
        # Show all things
        items = result["data"].get("items", [])
        if items:
            print(f"\n📋 All things:")
            for i, item in enumerate(items):
                thing_id = item.get("thingId", "Unknown")
                print(f"  {i+1:2d}. {thing_id}")
        else:
            print("\n📋 No things found")
            
    else:
        print(f"❌ Status: Error")
        if result["status_code"]:
            print(f"📊 HTTP Status: {result['status_code']}")
        print(f"💥 Error: {result['error']}")
    
    print()


def main():
    parser = argparse.ArgumentParser(description="Execute RQL queries against Eclipse Ditto")
    parser.add_argument("--queries", type=str, default="queries/camera.json",
                       help="Path to query file (default: queries/camera.json)")
    parser.add_argument("--ditto-url", type=str, default="http://localhost:8080/api/2",
                       help="Ditto API URL (default: http://localhost:8080/api/2)")
    parser.add_argument("--auth-user", type=str, default="ditto",
                       help="Authentication username (default: ditto)")
    parser.add_argument("--auth-pass", type=str, default="ditto",
                       help="Authentication password (default: ditto)")
    
    args = parser.parse_args()
    
    # Load queries
    queries = load_queries(args.queries)
    
    # Create HTTP client
    client = httpx.Client(timeout=60.0)
    
    print(f"🔧 Executing {len(queries)} queries from: {args.queries}")
    print(f"🌐 Ditto URL: {args.ditto_url}")
    
    print("=" * 80)
    
    success_count = 0
    
    try:
        for i, (description, rql) in enumerate(queries, 1):
            print(f"Query {i}/{len(queries)}")
            
            # Execute query
            result = execute_query(client, rql, args.ditto_url, args.auth_user, args.auth_pass)
            
            # Pretty print result
            pretty_print_result(description, rql, result)
            
            if result["status"] == "success":
                success_count += 1
    
    finally:
        client.close()
    
    print("=" * 80)
    print(f"✅ Successfully executed {success_count}/{len(queries)} queries")


if __name__ == "__main__":
    main()


