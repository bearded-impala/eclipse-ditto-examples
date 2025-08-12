"""
Bulk operations utilities for Eclipse Ditto examples.

This module provides utilities for bulk operations on Eclipse Ditto things,
including creation, deletion, and management of large numbers of things.
It is used across multiple example projects in this repository.
"""

import asyncio
import logging
import time
from typing import List, Optional, Dict, Any, Tuple
from tqdm import tqdm
import httpx
from .http_client import DittoClient
from .data_generation import (
    generate_thing_descriptor,
    generate_thing_descriptor_from_json_schema,
    load_policy,
)
from .validation import detect_schema_type
import json


def collect_thing_ids_with_progress(
    client: DittoClient, 
    page_size: int = 200, 
    count: Optional[int] = None
) -> List[str]:
    """
    Collect thing IDs page by page, showing a progress bar and stopping at count if specified.
    
    Args:
        client: DittoClient instance
        page_size: Number of things per page
        count: Optional maximum number of things to collect
        
    Returns:
        List of thing IDs
    """
    all_thing_ids: List[str] = []
    current_cursor = None
    has_more_pages = True
    total_to_collect = count if count is not None else None
    
    pbar = tqdm(desc="Collecting IDs", ncols=80, unit="thing", total=total_to_collect)
    
    while has_more_pages:
        search_params = {"fields": "thingId", "option": f"size({page_size})"}
        if current_cursor:
            search_params["option"] += f",cursor({current_cursor})"
        search_url = f"{client.base_url}/search/things"
        
        try:
            resp = client.session.get(search_url, auth=client.auth, params=search_params)
            resp.raise_for_status()
            data = resp.json()
            items = data.get("items", [])
            
            for item in items:
                thing_id = item.get("thingId")
                if thing_id:
                    all_thing_ids.append(thing_id)
                    pbar.update(1)
                    if total_to_collect is not None and len(all_thing_ids) >= total_to_collect:
                        has_more_pages = False
                        break
                        
            current_cursor = data.get("cursor")
            has_more_pages = has_more_pages and bool(current_cursor)
        except Exception as e:
            logging.warning(f"Error collecting IDs: {e}")
            break
            
    pbar.close()
    return all_thing_ids


async def delete_all_things_parallel(
    client: DittoClient, 
    page_size: int = 200, 
    max_concurrent: int = 20, 
    count: Optional[int] = None,
    enable_retry: bool = True,
    max_retries: int = 3
) -> Dict[str, Any]:
    """
    Deletes all Things from Eclipse Ditto in parallel using asyncio.
    
    Args:
        client: DittoClient instance
        page_size: Number of things to fetch per page
        max_concurrent: Maximum number of concurrent deletions
        count: If specified, only delete up to this many things
        enable_retry: Whether to retry failed deletions
        max_retries: Maximum number of retry attempts for failed deletions
        
    Returns:
        Dictionary with deletion summary
    """
    all_thing_ids: List[str] = collect_thing_ids_with_progress(
        client, page_size=page_size, count=count
    )
    
    logging.info(f"Finished collecting IDs. Found {len(all_thing_ids)} Things to delete.")
    
    if not all_thing_ids:
        logging.info("No Things found to delete.")
        return {
            "total_found": 0,
            "deleted_count": 0,
            "failed_deletions": [],
            "retry_success": [],
            "retry_failed": [],
            "success": True
        }
    
    deleted_count = 0
    failed_deletions = []
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async with httpx.AsyncClient() as async_client:
        async def sem_delete(thing_id: str) -> Tuple[str, bool]:
            async with semaphore:
                success = await client.async_delete_thing(thing_id, async_client)
                return thing_id, success
                
        tasks = [sem_delete(thing_id) for thing_id in all_thing_ids]
        
        with tqdm(total=len(all_thing_ids), desc="Deleting", ncols=80) as pbar:
            for coro in asyncio.as_completed(tasks):
                thing_id, success = await coro
                if success:
                    deleted_count += 1
                else:
                    failed_deletions.append(thing_id)
                    logging.warning(f"Failed to delete {thing_id}")
                pbar.update(1)
    
    # Retry failed deletions if requested
    retry_success = []
    retry_failed = []
    
    if enable_retry and failed_deletions:
        logging.info(f"Retrying {len(failed_deletions)} failed deletions...")
        
        for attempt in range(1, max_retries + 1):
            if not failed_deletions:
                break
                
            logging.info(f"Retry attempt {attempt}/{max_retries} for {len(failed_deletions)} things")
            
            # Create retry tasks
            retry_tasks = [sem_delete(thing_id) for thing_id in failed_deletions]
            still_failed = []
            
            with tqdm(total=len(failed_deletions), desc=f"Retry {attempt}", ncols=80) as pbar:
                for coro in asyncio.as_completed(retry_tasks):
                    thing_id, success = await coro
                    if success:
                        retry_success.append(thing_id)
                        deleted_count += 1
                        logging.info(f"Successfully deleted {thing_id} on retry attempt {attempt}")
                    else:
                        still_failed.append(thing_id)
                        logging.warning(f"Still failed to delete {thing_id} on retry attempt {attempt}")
                    pbar.update(1)
            
            failed_deletions = still_failed
            
            if failed_deletions:
                logging.warning(f"After retry attempt {attempt}: {len(failed_deletions)} things still failed")
            else:
                logging.info(f"All remaining things successfully deleted on retry attempt {attempt}")
                break
        
        # Any remaining failed deletions after all retries
        retry_failed = failed_deletions
        failed_deletions = []  # Clear the original list since we've handled retries
    
    # Log summary
    logging.info("--- Deletion Summary ---")
    logging.info(f"Total Things found: {len(all_thing_ids)}")
    logging.info(f"Successfully deleted: {deleted_count}")
    
    if retry_success:
        logging.info(f"Successfully deleted on retry: {len(retry_success)}")
        for rid in retry_success:
            logging.info(f"  - {rid}")
    
    if retry_failed:
        logging.warning(f"Failed to delete after all retries: {len(retry_failed)}")
        for fid in retry_failed:
            logging.warning(f"  - {fid}")
    elif retry_success:
        logging.info("All Things successfully processed for deletion after retries.")
    else:
        logging.info("All Things successfully processed for deletion.")
    
    return {
        "total_found": len(all_thing_ids),
        "deleted_count": deleted_count,
        "failed_deletions": retry_failed if enable_retry else failed_deletions,  # Final failed deletions after retries
        "retry_success": retry_success,
        "retry_failed": retry_failed,
        "success": len(retry_failed if enable_retry else failed_deletions) == 0
    }


def spawn_fleet(
    client: DittoClient,
    schema_path: str,
    policy_path: str,
    count: int,
    logger: Optional[logging.Logger] = None,
    interval: Optional[float] = None
) -> Dict[str, Any]:
    """
    Create a fleet of things using the provided DittoClient.
    
    Args:
        client: DittoClient instance
        schema_path: Path to schema JSON file
        policy_path: Path to policy JSON file
        count: Number of things to create
        logger: Optional logger instance
        interval: Optional delay in seconds between thing creations
        
    Returns:
        Dictionary with creation summary
    """
    # Load policy
    policy_id, policy_data = load_policy(policy_path)
    client.create_policy(policy_id, policy_data)
    
    # Determine schema type
    schema_type = "ditto-template"
    try:
        with open(schema_path, 'r') as f:
            schema_json = json.load(f)
            schema_type = detect_schema_type(schema_json)
    except Exception:
        # Fallback to ditto-template behavior if detection fails; actual error will surface during generation
        schema_type = "ditto-template"

    if logger:
        logger.info(f"Creating {count} things...")
        logger.info(f"Detected schema type: {schema_type}")
    
    created_count = 0
    failed_creations = []
    
    for _ in tqdm(range(count), desc="Progress", ncols=80):
        try:
            if schema_type == "json-schema":
                thing_id, payload = generate_thing_descriptor_from_json_schema(schema_path, policy_id, logger)
            else:
                thing_id, payload = generate_thing_descriptor(schema_path, policy_id, logger)
            success = client.create_thing(thing_id, payload)
            
            if success:
                created_count += 1
            else:
                failed_creations.append(thing_id)
                if logger:
                    logger.warning(f"[!] Failed to create {thing_id}")
        except Exception as e:
            if logger:
                logger.error(f"Error creating thing: {e}")
            failed_creations.append(f"unknown-{created_count}")
        
        # Add interval delay if specified
        if interval is not None:
            time.sleep(interval)
    
    if logger:
        logger.info(f"--- Creation Summary ---")
        logger.info(f"Successfully created: {created_count}")
        if failed_creations:
            logger.warning(f"Failed to create: {len(failed_creations)}")
    
    return {
        "requested_count": count,
        "created_count": created_count,
        "failed_creations": failed_creations,
        "success": len(failed_creations) == 0
    } 