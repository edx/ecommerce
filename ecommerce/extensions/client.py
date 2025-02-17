import logging

from commercetools import Client as CTClient
from commercetools.platform.models import Order as CTOrder
from django.conf import settings


logger = logging.getLogger(__name__)
class CommercetoolsAPIClient:
    """Commercetools API Client"""

    base_client = None

    def __init__(self):
        """
        Initialize CommercetoolsAPIClient, for use in an application, or (with an arg) testing.

        Args:
             client(CTClient): A mock client for testing (ONLY).
        """
        super().__init__()

        config = settings.COMMERCETOOLS_CONFIG
        self.base_client = CTClient(
            client_id=config["clientId"],
            client_secret=config["clientSecret"],
            scope=config["scopes"].split(" "),
            url=config["apiUrl"],
            token_url=config["authUrl"],
            project_key=config["projectKey"],
        )

    def get_non_code_cart_discount_by_type_and_value(self, order_id: str) -> CTOrder:
        """
        Fetch an order by the Order ID (UUID)

        Args:
            order_id (str): Order ID (UUID)
            expand: List of Order Parameters to expand

        Returns (CTOrder): Order with Expanded Properties
        """
        logger.info(f"[CommercetoolsAPIClient] - Attempting to find order with id: {order_id}")
        return self.base_client.orders.get_by_id(order_id)
