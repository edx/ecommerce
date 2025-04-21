import logging
from collections import namedtuple
from time import sleep
from typing import Dict, List, Optional

import requests
from django.conf import settings
from requests.exceptions import HTTPError, RequestException

from ecommerce.core.constants import BUNDLE_CART_DISCOUNT_KEY_FORMAT, CT_ABSOLUTE_DISCOUNT_TYPE

logger = logging.getLogger(__name__)

PairedDiscount = namedtuple("PairedDiscount", ["cart_discount", "discount_codes"])


class CommercetoolsAPIClient:
    """Custom Commercetools API Client using requests."""

    def __init__(self):
        """
        Initialize the Commercetools client with configuration from Django settings.
        """
        self.config = settings.COMMERCETOOLS_CONFIG
        self.access_token = self._get_access_token()

    def _get_access_token(self) -> str:
        """
        Retrieve an access token using client credentials flow for Commercetools.

        Returns:
            str: Access token for API requests.
        """
        auth_url = self.config["authUrl"]
        auth = (self.config["clientId"], self.config["clientSecret"])
        data = {
            "grant_type": "client_credentials",
            "scope": self.config['scopes'],
        }

        response = requests.post(auth_url, auth=auth, data=data)
        response.raise_for_status()
        return response.json()["access_token"]

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
        return_on_404 = False,
    ) -> Optional[Dict]:
        """
        Make an HTTP request to the Commercetools API.

        Args:
            method (str): HTTP method (e.g., "GET", "POST").
            endpoint (str): API endpoint (e.g., "/cart-discounts").
            params (Optional[Dict]): Query parameters.
            json (Optional[Dict]): JSON payload for POST/PUT requests.
            return_on_404 (bool): Whether to return a 404 response as a dictionary.

        Returns:
            Union[Dict, List]: JSON response from the API or None if the request fails.
        """
        url = f"{self.config['apiUrl']}/{self.config['projectKey']}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        max_retries = 3 if method == "GET" else 0
        base_backoff = 2

        for attempt in range(max_retries + 1):
            next_attempt = attempt + 1
            next_backoff = base_backoff * next_attempt

            try:
                response = requests.request(
                    method, url, headers=headers, params=params, json=json
                )
                response.raise_for_status()
                return response.json()
            except HTTPError as err:
                if response is not None:
                    try:
                        response_message = response.json().get(
                            "message", "No message provided."
                        )
                    except (ValueError, AttributeError) as error:
                        response_message = str(error)

                    if response.status_code == 404 and return_on_404:
                        logger.error(
                            "API request for endpoint: %s failed with 404 error: %s",
                            endpoint,
                            response_message,
                        )
                        return {"status": 404}

                    if response.status_code in (500, 501, 502, 503, 504):
                        if attempt == max_retries:
                            logger.error(
                                "API request for endpoint: %s failed after "
                                "exceeding retries with error: %s and message: %s",
                                endpoint,
                                err,
                                response_message,
                            )
                            return None

                        logger.error(
                            "API request for endpoint: %s failed with error: %s "
                            "and message: %s. Retrying attempt #%s in %s seconds",
                            endpoint,
                            err,
                            response_message,
                            next_attempt,
                            next_backoff,
                        )
                        sleep(next_backoff)
                        continue

                    logger.error(
                        "API request for endpoint: %s failed with error: %s "
                        "and message: %s",
                        endpoint,
                        err,
                        response_message,
                    )
                else:
                    logger.error(
                        "API request for endpoint: %s failed with error: %s",
                        endpoint,
                        err,
                    )

                return None
            except RequestException as err:
                if attempt == max_retries:
                    logger.error(
                        "API request for endpoint: %s failed after "
                        "exceeding retries with error: %s",
                        endpoint,
                        err,
                    )
                    return None

                logger.warning(
                    "API request for endpoint: %s with error: %s. "
                    "Retrying attempt #%s in %s seconds",
                    endpoint,
                    err,
                    next_attempt,
                    next_backoff,
                )

                sleep(next_backoff)
            except Exception as err:  # pylint: disable=broad-except
                logger.error(
                    "API request for endpoint: %s failed with error: %s",
                    endpoint,
                    err,
                )

                return None

        return None

    def get_ct_discounts_with_code(
        self, page_size=500
    ) -> Optional[Dict[str, PairedDiscount]]:
        """
        Fetch cart discounts with a discount code from Commercetools.

        Returns a dictionary where the key is the cart discount key and
        the value is a tuple of the cart discount and the discount code.
        """
        existing_cart_discounts_in_ct = self.get_ct_cart_discounts(
            query_params='requiresDiscountCode=true'
        )

        if existing_cart_discounts_in_ct is None:
            logger.error("Failed to get existing cart discounts with code from Commercetools.")
            return None

        paired_discounts = {
            key: PairedDiscount(
                cart_discount=value,
                discount_codes={}
            )
            for key, value in existing_cart_discounts_in_ct.items()
        }

        lastId = None
        should_continue = True
        results = []
        while should_continue:
            if lastId is None:
                response = self._make_request(
                    "GET",
                    "discount-codes",
                    params={
                        "expand": "cartDiscounts[*]",
                        "withTotal": False,
                        "limit": page_size,
                        "sort": "id asc"
                    }
                )
            else:
                response = self._make_request(
                    "GET",
                    "discount-codes",
                    params={
                        "expand": "cartDiscounts[*]",
                        "withTotal": False,
                        "limit": page_size,
                        "sort": "id asc",
                        "where": f'id > "{lastId}"'
                    }
                )
            if not response:
                logger.error("Failed to get discount codes with code from Commercetools.")
                return None

            batch_results = response["results"]
            results.extend(batch_results)
            should_continue = (len(batch_results) == page_size)
            if batch_results:
                lastId = batch_results[-1]["id"]

        for discount_code in results:
            cart_discounts = discount_code.get("cartDiscounts", [{}])
            discount_code_data = {
                "key": discount_code.get("key"),
                "name": discount_code.get("name", {}).get("en-US"),
                "code": discount_code.get("code"),
                "validFrom": discount_code.get("validFrom"),
                "validUntil": discount_code.get("validUntil"),
                "maxApplications": discount_code.get("maxApplications"),
                "version": discount_code.get("version"),
            }
            discount_code_key = discount_code_data["key"]

            for discount in cart_discounts:
                cart_discount = discount.get("obj")
                cart_discount = {
                    "id": cart_discount.get("id"),
                    "key": cart_discount.get("key"),
                    "name": cart_discount.get("name", {}).get("en-US"),
                    "description": cart_discount.get("description", {}).get("en-US"),
                    "cartPredicate": cart_discount.get("cartPredicate"),
                    "value": cart_discount.get("value"),
                    "customFields": cart_discount.get("custom", {}).get(
                        "fields", {}
                    ),
                    "version": cart_discount.get("version"),
                }
                cart_discount_key = cart_discount["key"]

                # Almost non existent case for a cart discount to not have a key.
                if cart_discount_key is not None:
                    # Add the discount code to the existing discount codes for the cart discount.
                    paired_discounts[cart_discount_key].discount_codes[
                        discount_code_key
                    ] = discount_code_data

        return paired_discounts

    def get_ct_cart_discounts(self, query_params: str, page_size: int = 500) -> Optional[Dict]:
        """
        Fetch cart discounts from Commercetools.
        """
        lastId = None
        should_continue = True
        results = []
        while should_continue:
            if lastId is None:
                response = self._make_request(
                    "GET",
                    "cart-discounts",
                    params={
                        "withTotal": False,
                        "limit": page_size,
                        "sort": "id asc",
                        "where": query_params
                    }
                )
            else:
                response = self._make_request(
                    "GET",
                    "cart-discounts",
                    params={
                        "withTotal": False,
                        "limit": page_size,
                        "sort": "id asc",
                        "where": f'id>"{lastId}" and {query_params}'
                    }
                )
            if not response:
                logger.error("Failed to get cart discounts from Commercetools.")
                return None

            batch_results = response["results"]
            results.extend(batch_results)
            should_continue = (len(batch_results) == page_size)

            if batch_results:
                lastId = batch_results[-1]["id"]

        return {
            cart_discount.get("key"): {
                "id": cart_discount.get("id"),
                "key": cart_discount.get("key"),
                "name": cart_discount.get("name", {}).get("en-US"),
                "description": cart_discount.get("description", {}).get("en-US"),
                "cartPredicate": cart_discount.get("cartPredicate"),
                "value": cart_discount.get("value"),
                "customFields": cart_discount.get("custom", {}).get(
                    "fields", {}
                ),
                "version": cart_discount.get("version"),
            }
            for cart_discount in results
        }

    def get_cart_discount_by_key(self, key):
        """
        Fetch cart discount by its key.

        Args:
            key (str): Key of the cart discount.

        Returns:
            Dict: Cart discount data or None if not found.
        """
        response = self._make_request(
            "GET",
            f"cart-discounts/key={key}",
            return_on_404=True,
        )
        if not response:
            logger.error(
                "Failed to get cart discount with key '%s' from Commercetools.", key
            )
            return

        if response.get("status") == 404:
           return response

        cart_discount = response

        return {
            "id": cart_discount.get("id"),
            "key": cart_discount.get("key"),
            "name": cart_discount.get("name", {}).get("en-US"),
            "description": cart_discount.get("description", {}).get("en-US"),
            "cartPredicate": cart_discount.get("cartPredicate"),
            "value": cart_discount.get("value"),
            "customFields": cart_discount.get("custom", {}).get(
                "fields", {}
            ),
            "version": cart_discount.get("version"),
        }

    def get_discount_codes_for_cart_discount(
        self,
        *,
        cart_discount_name: str,
        cart_discount_id: str,
    ) -> Optional[Dict]:
        """
        Fetch discount codes for a specific cart discount ID.

        Args:
            cart_discount_id (str): ID of the cart discount.

        Returns:
            List[Dict]: List of discount codes associated with the cart discount.
        """
        query_params = f'cartDiscounts(id="{cart_discount_id}")'

        discount_codes = self._make_request(
            "GET",
            "discount-codes",
            params={"where": query_params},
        )
        if not discount_codes:
            logger.error(
                "Failed to get discount codes for cart discount '%s' from Commercetools.",
                cart_discount_name,
            )
            return None

        return {
            discount_code.get("key"): {
                "key": discount_code.get("key"),
                "name": discount_code.get("name", {}).get("en-US"),
                "code": discount_code.get("code"),
                "validFrom": discount_code.get("validFrom"),
                "validUntil": discount_code.get("validUntil"),
                "maxApplications": discount_code.get("maxApplications"),
                "version": discount_code.get("version"),
                "cartDiscountIds": [cartDiscount["id"] for cartDiscount in discount_code.get("cartDiscounts", [])],
            }
            for discount_code in discount_codes.get("results", [])
        }

    def get_ct_bundle_offers_without_code(
        self, failed_discounts: List
    ) -> Optional[Dict]:
        """
        Fetch bundle cart discounts without a discount code from Commercetools.

        Args:
            failed_discounts (list): List of failed discounts.

        Returns:
            Dict: Cart discount data or None if request fails.
        """
        # This query is used to get all cart discounts for program offers.
        query_params = 'requiresDiscountCode=false and target(type="lineItems")'

        bundle_offer_without_codes = self._make_request(
            "GET",
            "cart-discounts",
            params={"where": query_params},
        )
        if not bundle_offer_without_codes:
            return None

        ct_bundle_offers_without_code_dict = {}
        for cart_discount in bundle_offer_without_codes["results"]:
            discount_type = cart_discount['value']['type']

            if discount_type == CT_ABSOLUTE_DISCOUNT_TYPE:
                discount_value_in_cents = cart_discount['value']['money'][0]['centAmount']
            else:
                discount_value_in_cents = cart_discount['value']['permyriad']

            display_discount_value = discount_value_in_cents / 100
            key = BUNDLE_CART_DISCOUNT_KEY_FORMAT.format(type=discount_type, value=discount_value_in_cents)
            # This is rare scenario, but it can happen when someone has created a cart discount
            # with the same type and value for a bundle offer.
            if key in ct_bundle_offers_without_code_dict:
                logger.error(
                    "More than one cart discount exists with type: %s, and value: %s. Skipping it for now.",
                    discount_type, display_discount_value
                )
                failed_discounts.append({
                    "type": discount_type,
                    "value": display_discount_value,
                    "reason": "More than one cart discount exists with the same type and value."
                })
                continue

            ct_bundle_offers_without_code_dict[key] = {
                "id": cart_discount['id'],
                "type": discount_type,
                "display_value": display_discount_value,
                "version": cart_discount['version'],
                "target_predicate": cart_discount['target']['predicate']
            }

        return ct_bundle_offers_without_code_dict

    def get_highest_sort_order_for_cart_discount(
        self,
        where,
    ) -> Optional[Dict]:
        """
        Fetch the highest sort order for cart discounts with the course discount type.

        Returns:
            float: Highest sort order for course cart discounts.
        """
        return self._make_request(
            "GET",
            "cart-discounts",
            params={
                "where": where,
                "sort": ["sortOrder desc"],
                "limit": 1,
            },
        )

    def create_cart_discount(
        self,
        *,
        key: str,
        name: str,
        description: Optional[str],
        value: Dict,
        cartPredicate: str,
        sortOrder: float,
        customFields: Dict,
        target: Dict,
    ) -> Optional[Dict]:
        """
        Create a new cart discount.

        Args:
            payload (dict): Payload containing cart discount data.

        Returns:
            Dict: Created cart discount data or None if request fails.
        """
        payload = {
            "key": key,
            "name": {"en-us": name},
            "description": {"en-us": description},
            "value": value,
            "cartPredicate": cartPredicate,
            "target": target,
            "sortOrder": f"{sortOrder:.10f}".rstrip("0").rstrip("."),
            "isActive": True,
            "requiresDiscountCode": True,
            "stackingMode": "StopAfterThisDiscount",
            "custom": {
                "type": {
                    "key": "cartDiscountCustomType",
                },
                "fields": customFields,
            },
        }

        return self._make_request("POST", "cart-discounts", json=payload)

    def create_discount_code(
        self,
        *,
        cartDiscountIds: List[str],
        key: str,
        name: str,
        code: str,
        validFrom: Optional[str] = None,
        validUntil: Optional[str] = None,
        maxApplications: Optional[int] = None,
        maxApplicationsPerCustomer: Optional[int] = None,
    ) -> Optional[Dict]:
        """
        Create a new discount code.

        Args:
            payload (dict): Payload containing discount code data.

        Returns:
            Dict: Created discount code data or None if request fails.
        """
        payload = {
            "name": {"en-us": name},
            "key": key,
            "code": code,
            "validFrom": validFrom,
            "validUntil": validUntil,
            "maxApplications": maxApplications,
            "maxApplicationsPerCustomer": maxApplicationsPerCustomer,
            "isActive": True,
            "cartDiscounts": [
                {
                    "typeId": "cart-discount",
                    "id": cart_discount_id,
                }
                for cart_discount_id in cartDiscountIds
            ],
        }
        return self._make_request("POST", "discount-codes", json=payload)

    def create_bundle_cart_discount_without_code(
        self,
        key: str,
        name: str,
        description: str,
        discount_type: str,
        discount_value_in_cents: int,
        sort_order: float,
        predicate: str,
    ) -> Optional[Dict]:
        """
        Create a new cart discount.

        Args:
            key (str): Unique key for the cart discount.
            name (str): Name of the cart discount.
            description (str): Description of the cart discount.
            value (int): Discount value.
            cart_predicate (str): Predicate for the cart discount.
            cart_discount_type (str): Type of discount (e.g., "relative").
            target_type (str): Type of target (e.g., "lineItems").
            target_ids (List[str]): List of target IDs.

        Returns:
            Dict: Created cart discount data or None if request fails.
        """
        if discount_type == CT_ABSOLUTE_DISCOUNT_TYPE:
            discount_value_data = {
                "money": [{
                    "centAmount": discount_value_in_cents,
                    "currencyCode": "USD"
                }],
                "applicationMode": "ProportionateDistribution"
            }
        else:
            discount_value_data = {
                "permyriad": discount_value_in_cents
            }

        payload = {
            "key": key,
            "name": {"en-us": name},
            "description": {"en-us": description},
            "value": {
                "type": discount_type,
                **discount_value_data,
            },
            "cartPredicate": f"forAllLineItems({predicate}) = true",
            "target": {
                "type": "lineItems",
                "predicate": "1 = 1",
            },
            "sortOrder": f"{sort_order:.15f}".rstrip("0").rstrip("."),
            "isActive": True,
            "requiresDiscountCode": False,
            "stackingMode": "StopAfterThisDiscount",
            "custom": {
                "type": {
                    "key": "cartDiscountCustomType",
                },
                "fields": {
                    "discountType": "program-offer",
                },
            },
        }

        return self._make_request("POST", "cart-discounts", json=payload)

    def update_resource_by_key(
        self,
        *,
        resource_type: str,
        resource_key: str,
        version: int,
        actions: List[Dict],
    ) -> Optional[Dict]:
        """
        Update a resource by its key.

        Args:
            resource_type (str): Type of the resource to update.
            resource_key (str): Key of the resource to update.
            version (int): Version of the cart discount.
            actions (List[Dict]): List of actions to perform.

        Returns:
            Dict: Updated resource data or None if request fails.
        """
        payload = {
            "version": version,
            "actions": actions,
        }

        return self._make_request(
            "POST", f"{resource_type}/key={resource_key}", json=payload
        )

    def update_cart_discount_cart_predicate(
        self, cart_discount_id: str, predicate: str, version: int
    ) -> Optional[Dict]:
        """
        Update the cart predicate for a cart discount.

        Args:
            cart_discount_id (str): ID of the cart discount.
            predicate (str): Updated predicate for the cart discount.
            version (int): Version of the cart discount.

        Returns:
            Dict: Updated cart discount data or None if request fails.
        """
        payload = {
            "version": version,
            "actions": [
                {
                    "action": "changeCartPredicate",
                    "cartPredicate": f"forAllLineItems({predicate}) = true",
                }
            ]
        }
        return self._make_request("POST", f"cart-discounts/{cart_discount_id}", json=payload)

    def delete_cart_discount_by_id(
        self, cart_discount_id: str, version: int
    ) -> Optional[Dict]:
        """
        Delete a cart discount by its ID.

        Args:
            cart_discount_id (str): ID of the cart discount to delete.
            version (int): Version of the cart discount.

        Returns:
            Dict: Deleted cart discount data or None if request fails.
        """
        return self._make_request("DELETE", f"cart-discounts/{cart_discount_id}", params={"version": version})

    def delete_discount_code_by_key(
        self, discount_code_key: str, version: int
    ) -> Optional[Dict]:
        """
        Delete a discount code by its key.

        Args:
            discount_code_key (str): Key of the discount code to delete.
            version (int): Version of the discount code.

        Returns:
            Dict: Deleted discount code data or None if request fails.
        """
        return self._make_request(
            "DELETE",
            f"discount-codes/key={discount_code_key}",
            params={"version": version},
        )
