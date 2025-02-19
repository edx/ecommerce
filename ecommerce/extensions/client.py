import logging
from typing import Dict, List, Optional, Union
import requests
from requests.exceptions import HTTPError, RequestException

from django.conf import settings

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
            "scope": f"manage_project:{self.config['projectKey']}",
        }

        try:
            response = requests.post(auth_url, auth=auth, data=data)
            response.raise_for_status()
            return response.json()["access_token"]
        except HTTPError as e:
            logger.error(f"Failed to retrieve access token: {e}")
            raise

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None,
    ) -> Union[Dict, List]:
        """
        Make an HTTP request to the Commercetools API.

        Args:
            method (str): HTTP method (e.g., "GET", "POST").
            endpoint (str): API endpoint (e.g., "/cart-discounts").
            params (Optional[Dict]): Query parameters.
            json (Optional[Dict]): JSON payload for POST/PUT requests.

        Returns:
            Union[Dict, List]: JSON response from the API.

        Raises:
            HTTPError: If the request fails.
        """
        url = f"{self.config['apiUrl']}/{self.config['projectKey']}/{endpoint}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json",
        }
        try:
            response = requests.request(method, url, headers=headers, params=params, json=json)
            response.raise_for_status()
            print('RESULT', response.json())
            return response.json()
        except HTTPError as err:
            if response is not None:
                response_message = response.json().get("message")
                logger.error(f"API request failed with error: {err} and message: {response_message}")
            raise

    def get_cart_discounts_without_code_by_type_and_value(
        self, discount_type: str, discount_value: int
    ) -> Dict:
        """
        Fetch cart discounts without a discount code by type and value.

        Args:
            discount_type (str): Type of discount (e.g., "relative").
            discount_value (str): Value of the discount.

        Returns:
            Dict: Cart discount data.
        """

        if discount_type == "absolute":
            discount_value_param = f' and value(money(centAmount={discount_value}))'
        else:
            discount_value_param = f' and value(permyriad={discount_value})'

        query_params = f'value(type="{discount_type}") and requiresDiscountCode=false and target(type="lineItems")'
        query_params += discount_value_param

        return self._make_request(
            "GET",
            "cart-discounts",
            params={"where": query_params},
        )

    def get_highest_sort_order_for_cart_discount_without_codes(self) -> Dict:
        """
        Fetch the latest sort order for cart discounts without codes.

        Returns:
            Dict: Latest cart discount data.
        """
        return self._make_request(
            "GET",
            "cart-discounts",
            params={
                "where": "requiresDiscountCode=false and target(type=\"lineItems\")",
                "sort": ["sortOrder desc"],
                "limit": 1,
            },
        )

    def create_cart_discount_without_code(
        self,
        key: str,
        name: str,
        description: str,
        discount_type: str,
        discount_value: int,
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
            Dict: Created cart discount data.
        """
        if discount_type == "absolute":
            discount_value_data = {
                "money": [{
                    "centAmount": discount_value,
                    "currencyCode": "USD"
                }],
                "applicationMode": "ProportionateDistribution"
            }
        else:
            discount_value_data = {
                "permyriad": discount_value
            }

        payload = {
            "key": key,
            "name": {"en-us": name},
            "description": {"en-us": description},
            "value": {
                "type": discount_type,
                **discount_value_data,
            },
            "cartPredicate": "lineItemExists(custom.bundleId is defined) = true",
            "target": {
                "type": "lineItems",
                "predicate": predicate,
            },
            "sortOrder": f"{sort_order:.20f}".rstrip('0').rstrip('.'),
            "isActive": True,
            "requiresDiscountCode": False,
            "stackingMode": "Stacking",
        }
        print('PAYLOAD', payload)
        return self._make_request("POST", "cart-discounts", json=payload)

    def update_cart_discount_target_predicate(self, cart_discount_id: str, predicate: str) -> Dict:
        """
        Update the target predicate for a cart discount.

        Args:
            cart_discount_id (str): ID of the cart discount.
            predicate (str): Updated predicate for the cart discount.

        Returns:
            Dict: Updated cart discount data.
        """
        payload = {
            "version": 1,
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
