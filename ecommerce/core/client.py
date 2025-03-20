import logging
from typing import Dict, List, Optional, Union

import requests
from django.conf import settings
from requests.exceptions import HTTPError

from ecommerce.core.constants import BUNDLE_CART_DISCOUNT_KEY_FORMAT, CT_ABSOLUTE_DISCOUNT_TYPE

logger = logging.getLogger(__name__)


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
    ) -> Optional[Union[Dict, List]]:
        """
        Make an HTTP request to the Commercetools API.

        Args:
            method (str): HTTP method (e.g., "GET", "POST").
            endpoint (str): API endpoint (e.g., "/cart-discounts").
            params (Optional[Dict]): Query parameters.
            json (Optional[Dict]): JSON payload for POST/PUT requests.

        Returns:
            Union[Dict, List]: JSON response from the API or None if the request fails.
        """
        url = f"{self.config['apiUrl']}/{self.config['projectKey']}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(method, url, headers=headers, params=params, json=json)
            response.raise_for_status()
            return response.json()
        except HTTPError as err:
            if response is not None:
                response_message = response.json().get('message', 'No message provided.')
                logger.error(
                    "API request for endpoint: %s failed with error: %s and message: %s",
                    endpoint, err, response_message
                )
            else:
                logger.error("API request for endpoint: %s failed with error: %s", endpoint, err)

            return None

    def get_ct_discounts_with_code(self) -> Optional[Dict]:
        """
        Fetch cart discounts with a discount code from Commercetools.

        Returns a dictionary where the key is the cart discount key and the value is a tuple of the cart discount and the discount code.
        """

        expansion_query = "cartDiscounts[*]"

        discount_codes = self._make_request(
            "GET",
            "discount-codes",
            params={"expand": expansion_query},
        )

        if discount_codes and type(discount_codes) == dict:
            paired_discounts = {}
            for discount_code in discount_codes["results"]:
                for cart_discount in discount_code.get("cartDiscounts", []):
                    key = cart_discount.get("obj", {}).get("key")
                    if key is not None:
                        discount_code_copy = discount_code.copy()
                        discount_code_copy.pop("cartDiscounts")
                        if key in paired_discounts:
                            paired_discounts[key][1][
                                discount_code.get("key")
                            ] = discount_code_copy
                        else:
                            paired_discounts[key] = (
                                cart_discount.get("obj", {}),
                                {discount_code.get("key"): discount_code_copy},
                            )

            return paired_discounts
        else:
            return None

    def get_ct_bundle_offers_without_code(self, failed_discounts: List) -> Dict:
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

    def get_highest_sort_order_for_cart_discount_without_codes(self) -> Dict:
        """
        Fetch the latest sort order for cart discounts without codes.

        Returns:
            Dict: Latest cart discount data or None if request fails.
        """
        return self._make_request(
            "GET",
            "cart-discounts",
            params={
                "where": 'requiresDiscountCode=false and target(type="lineItems")',
                "sort": ["sortOrder desc"],
                "limit": 1,
            },
        )

    def create_cart_discount(
        self,
        *,
        key,
        name,
        description,
        value,
        cartPredicate,
        sortOrder,
        custom,
    ) -> Dict:
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
            "target": {
                "type": "totalPrice",
            },
            "sortOrder": f"{sortOrder:.14f}".rstrip("0").rstrip("."),
            "isActive": True,
            "requiresDiscountCode": True,
            "stackingMode": "StopAfterThisDiscount",
            "custom": {
                "type": {
                    "key": "cartDiscountCustomType",
                },
                "fields": custom,
            },
        }

        return self._make_request("POST", "cart-discounts", json=payload)

    def create_discount_code(
        self,
        *,
        name,
        key,
        code,
        validFrom=None,
        validUntil=None,
        maxApplications=None,
        maxApplicationsPerCustomer=None,
        cartDiscountId,
    ) -> Dict:
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
            "validFrom": validFrom if validFrom else None,
            "validUntil": validUntil if validUntil else None,
            "maxApplications": maxApplications,
            "maxApplicationsPerCustomer": maxApplicationsPerCustomer,
            "isActive": True,
            "cartDiscounts": [
                {
                    "typeId": "cart-discount",
                    "id": cartDiscountId,
                }
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
    ) -> Dict:
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
            # Equivalent to "At least one existing line item satisfies the condition(s) is True in CT."
            "cartPredicate": "lineItemExists(custom.bundleId is defined) = true",
            "target": {
                "type": "lineItems",
                "predicate": predicate,
            },
            "sortOrder": f"{sort_order:.14f}".rstrip("0").rstrip("."),
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

    def update_cart_discount_target_predicate(
        self, cart_discount_id: str, predicate: str, version: int
    ) -> Dict:
        """
        Update the target predicate for a cart discount.

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
                    "action": "changeTarget",
                    "target": {
                        "type": "lineItems",
                        "predicate": predicate
                    }
                }
            ]
        }
        return self._make_request("POST", f"cart-discounts/{cart_discount_id}", json=payload)

    def delete_cart_discount_by_id(self, cart_discount_id: str, version: int) -> Dict:
        """
        Delete a cart discount by its ID.

        Args:
            cart_discount_id (str): ID of the cart discount to delete.
            version (int): Version of the cart discount.

        Returns:
            Dict: Deleted cart discount data or None if request fails.
        """
        return self._make_request("DELETE", f"cart-discounts/{cart_discount_id}", params={"version": version})
