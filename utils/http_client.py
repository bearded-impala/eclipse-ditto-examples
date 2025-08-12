"""
HTTP client utilities for Eclipse Ditto examples.

This module provides a client for interacting with the Eclipse Ditto HTTP API
and is used across multiple example projects in this repository.
"""

from typing import Any, Dict, List, Optional

import httpx

from .config import Config


class DittoClient:
    """
    Client for interacting with the Eclipse Ditto HTTP API.
    """

    def __init__(self, config: Config):
        """
        Initialize the DittoClient.

        Args:
            config: Config instance with connection details
        """
        self.config = config
        self.base_url = config.ditto_url.rstrip("/")
        self.auth = (config.auth_user, config.auth_pass)
        self.session = httpx.Client()

    def create_policy(self, policy_id: str, policy_data: Dict[str, Any]) -> bool:
        """
        Create or update a policy in Ditto.

        Args:
            policy_id: The policy ID
            policy_data: The policy JSON data

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/policies/{policy_id}"
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.put(
                url, json=policy_data, auth=self.auth, headers=headers, timeout=10
            )
            return 200 <= response.status_code < 300
        except httpx.RequestError:
            return False

    def create_thing(self, thing_id: str, payload: Dict[str, Any]) -> bool:
        """
        Create or update a thing in Ditto.

        Args:
            thing_id: The thing ID
            payload: The thing JSON data

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/things/{thing_id}"
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.put(
                url, auth=self.auth, headers=headers, json=payload
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False
        except Exception:
            return False

    def get_thing(self, thing_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a thing by ID.

        Args:
            thing_id: The thing ID

        Returns:
            Thing data or None if not found
        """
        url = f"{self.base_url}/things/{thing_id}"
        try:
            response = self.session.get(url, auth=self.auth)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError:
            return None
        except Exception:
            return None

    def update_thing_property(self, thing_id: str, path: str, value: Any) -> bool:
        """
        Update a specific property of a thing.

        Args:
            thing_id: The thing ID
            path: Property path (e.g., "features/temperature/properties/value")
            value: The value to set

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/things/{thing_id}/{path}"
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.put(
                url, auth=self.auth, headers=headers, json=value
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False
        except Exception:
            return False

    def search_things(
        self, filter_expr: Optional[str] = None, page_size: int = 200
    ) -> Dict[str, Any]:
        """
        Search things with optional filter.

        Args:
            filter_expr: Optional filter expression
            page_size: Number of things per page

        Returns:
            Search results
        """
        search_url = f"{self.base_url}/search/things"
        params = {"option": f"size({page_size})"}

        if filter_expr:
            params["filter"] = filter_expr

        try:
            resp = self.session.get(search_url, auth=self.auth, params=params)
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError:
            return {"items": [], "cursor": None}
        except Exception:
            return {"items": [], "cursor": None}

    def list_thing_ids(self, page_size: int = 200) -> List[str]:
        """
        List all thing IDs in Ditto, handling pagination.

        Args:
            page_size: Number of things per page

        Returns:
            List of thing IDs
        """
        all_thing_ids: List[str] = []
        current_cursor: Optional[str] = None
        has_more_pages = True

        while has_more_pages:
            search_params = {"option": f"size({page_size})"}
            if current_cursor:
                search_params["option"] += f",cursor({current_cursor})"
            search_url = f"{self.base_url}/search/things"

            try:
                resp = self.session.get(
                    search_url, auth=self.auth, params=search_params
                )
                resp.raise_for_status()
                data = resp.json()
                items = data.get("items", [])
                for item in items:
                    thing_id = item.get("thingId")
                    if thing_id:
                        all_thing_ids.append(thing_id)
                current_cursor = data.get("cursor")
                has_more_pages = bool(current_cursor)
            except Exception:
                break

        return all_thing_ids

    def delete_thing(self, thing_id: str) -> bool:
        """
        Delete a thing by ID.

        Args:
            thing_id: The thing ID

        Returns:
            True if deleted or not found, False otherwise
        """
        url = f"{self.base_url}/things/{thing_id}"
        try:
            r = self.session.delete(url, auth=self.auth)
            return r.status_code in (204, 404)
        except Exception:
            return False

    def create_connection(self, connection_data: Dict[str, Any]) -> bool:
        """
        Create a connection in Ditto.

        Args:
            connection_data: The connection JSON data

        Returns:
            True if successful, False otherwise
        """
        url = f"{self.base_url}/connections"
        headers = {"Content-Type": "application/json"}
        try:
            response = self.session.put(
                url, auth=self.auth, headers=headers, json=connection_data
            )
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError:
            return False
        except Exception:
            return False

    async def async_delete_thing(
        self, thing_id: str, async_client: Optional[httpx.AsyncClient] = None
    ) -> bool:
        """
        Asynchronously delete a thing by ID.

        Args:
            thing_id: The thing ID
            async_client: Optional shared httpx.AsyncClient

        Returns:
            True if deleted or not found, False otherwise
        """
        url = f"{self.base_url}/things/{thing_id}"
        client = async_client or httpx.AsyncClient()
        try:
            r = await client.delete(url, auth=self.auth)
            return r.status_code in (204, 404)
        except Exception:
            return False
        finally:
            if async_client is None:
                await client.aclose()

    def close(self):
        """Close the HTTP session."""
        self.session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


def create_ditto_client(config: Config) -> DittoClient:
    """
    Create a DittoClient instance.

    Args:
        config: Config instance

    Returns:
        DittoClient instance
    """
    return DittoClient(config)
