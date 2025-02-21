import logging
import re
from enum import Enum

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.extensions.client import CommercetoolsAPIClient
from ecommerce.programs.utils import get_all_programs

logger = logging.getLogger(__name__)


Benefit = get_model('offer', 'Benefit')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
SiteConfiguration = get_model('core', 'SiteConfiguration')


CT_ABSOLUTE_DISCOUNT_TYPE = 'absolute'
CT_PERCENTAGE_DISCOUNT_TYPE = 'relative'

TEN_PERCENT_DISCOUNT_IN_CENTS = 1000

CT_CART_DISCOUNT_TYPE_MAP = {
    Benefit.FIXED: CT_ABSOLUTE_DISCOUNT_TYPE,
    Benefit.PERCENTAGE: CT_PERCENTAGE_DISCOUNT_TYPE
}


class ProxyClassDiscountType(Enum):
    """Enumeration of discount types in the proxy class."""

    PERCENTAGE = "ecommerce.programs.benefits.PercentageDiscountBenefitWithoutRange"
    ABSOLUTE = "ecommerce.programs.benefits.AbsoluteDiscountBenefitWithoutRange"


def _get_highest_sort_order(client: CommercetoolsAPIClient):
    """
    Get the highest sort order for cart discounts without discount codes.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.

    Returns:
        float: The highest sort order.
    """
    response = client.get_highest_sort_order_for_cart_discount_without_codes()

    if response['count'] > 0:
        return float(response['results'][0]['sortOrder'])

    return 0.00000000000001


def _create_cart_discount(
    client: CommercetoolsAPIClient,
    discount_type: str,
    discount_value: int,
    sort_order: float,
    predicate: str
):
    """
    Create a new cart discount.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
        discount_type (str): Type of discount (e.g., "relative").
        discount_value (int): Value of the discount.
        sort_order (float): Sort order (Rank) for the cart discount.
        predicate (str): Predicate for the cart discount.

    Returns:
        Dict: Created cart discount data or None if request fails.
    """
    display_discount_value = int(discount_value / 100)
    response = client.create_cart_discount_without_code(
        key=f"{discount_type}-{display_discount_value}-program-offer",
        name=f"{discount_type.capitalize()} {display_discount_value} Program Offer",
        description=f"Program Offer with value: {display_discount_value} and type: {discount_type}",
        discount_type=discount_type,
        discount_value=discount_value,
        sort_order=sort_order,
        predicate=predicate
    )
    return response


def _create_target_predicate_from_program_uuids(program_uuids: list, is_ten_percent_discount: bool):
    """
    Create a target predicate for a cart discount based on program UUIDs.

    Args:
        program_uuids (list): List of program UUIDs.
        is_ten_percent_discount (bool): Flag indicating if the discount is a 10% discount.

    Returns:
        str: Target predicate for the cart discount.
    """
    predicate = "custom.bundleId is defined and "

    if is_ten_percent_discount:
        predicate += "("
        predicate += " and ".join([f"custom.bundleId != \"{program_uuid}\"" for program_uuid in program_uuids])
        predicate += ")"
    else:
        predicate += "("
        predicate += " or ".join([f"custom.bundleId = \"{program_uuid}\"" for program_uuid in program_uuids])
        predicate += ")"

    return predicate


# Function to extract UUIDs and condition type from a predicate
def _combine_uuids_to_predicate(predicate: str, is_ten_percent_discount: bool, program_uuids: list):
    """
    Combine UUIDs and condition type to create a target predicate for a cart discount.

    Args:
        predicate (str): Predicate for the cart discount.
        is_ten_percent_discount (bool): Flag indicating if the discount is a 10% discount.
        program_uuids (list): List of program UUIDs.

    Returns:
        str: Target predicate for the cart discount.
    """
    uuids = re.findall(r'custom\.bundleId\s*(?:!=|=)\s*"([^"]+)"', predicate)
    combined_uuids = list(set(uuids) | set(program_uuids))
    return _create_target_predicate_from_program_uuids(combined_uuids, is_ten_percent_discount)


def _group_ten_percentage_offers(cart_discounts: list):
    """
    Group offers of 10% discount.

    Args:
        cart_discounts (list): List to store cart discounts.
    """
    offers = ConditionalOffer.objects.filter(
        offer_type=ConditionalOffer.SITE,
        condition__program_uuid__isnull=False,
        benefit__value=10,
        benefit__proxy_class=ProxyClassDiscountType.PERCENTAGE.value
    ).select_related('benefit', 'condition')

    programs_with_offer = {offer.condition.program_uuid for offer in offers}

    site_configuration = SiteConfiguration.objects.first()
    programs_response = get_all_programs(site_configuration)
    if not programs_response:
        raise CommandError("Failed to retrieve all programs from course-discovery")

    all_programs = {program['uuid'] for program in programs_response['results']}
    programs_to_exclude = list(set(all_programs) - set(programs_with_offer))

    cart_discounts.append({
        "type": CT_PERCENTAGE_DISCOUNT_TYPE,
        "value": 10.00,
        "program_uuids": programs_to_exclude
    })


def _group_other_offers(cart_discounts: list):
    """
    Group offers by discount type and value that are not 10% discount.

    Args:
        cart_discounts (list): List to store cart discounts.
    """
    offers = ConditionalOffer.objects.filter(
        offer_type=ConditionalOffer.SITE,
        condition__program_uuid__isnull=False,
    ).exclude(
        Q(benefit__value=0) |
        Q(benefit__value=10, benefit__proxy_class=ProxyClassDiscountType.PERCENTAGE.value)
    ).select_related('benefit', 'condition')

    discount_groups = {}
    for offer in offers:
        program_uuid = offer.condition.program_uuid
        discount_type = CT_CART_DISCOUNT_TYPE_MAP.get(offer.benefit.proxy().benefit_class_type)
        discount_value = offer.benefit.value
        type_value_key = f"{discount_type}-{discount_value}"

        if type_value_key in discount_groups:
            discount_groups[type_value_key]["program_uuids"].append(program_uuid)
        else:
            discount_groups[type_value_key] = {
                "type": discount_type,
                "value": discount_value,
                "program_uuids": [program_uuid]
            }

    for _, value in discount_groups.items():
        cart_discounts.append({
            "type": value["type"],
            "value": value["value"],
            "program_uuids": value["program_uuids"]
        })


class Command(BaseCommand):
    """Command to migrate program offers to Commercetools."""

    def handle(self, *args, **options):
        """Handle the command."""
        client = CommercetoolsAPIClient()
        sort_order = _get_highest_sort_order(client)

        cart_discounts = []
        _group_ten_percentage_offers(cart_discounts)
        _group_other_offers(cart_discounts)

        for discount_data in cart_discounts:
            discount_type = discount_data["type"]
            discount_value = discount_data["value"]
            discount_value_in_cents = int(discount_value * 100)

            logger.info(
                "Checking existing cart discount with type %s and value %s in Commercetools.",
                discount_type, discount_value
            )
            existing = client.get_cart_discounts_without_code_by_type_and_value(discount_type, discount_value_in_cents)
            if not existing:
                logger.info(
                    "Failed to get discount with type %s and value %s. Cart discount not created.",
                    discount_type, discount_value
                )
                continue

            is_ten_percent_discount = (
                discount_type == CT_PERCENTAGE_DISCOUNT_TYPE and discount_value_in_cents == TEN_PERCENT_DISCOUNT_IN_CENTS
            )

            if existing['count'] == 0:
                sort_order += 0.00000000000001
                logger.info(
                    "Creating cart discount with type %s and value %s.",
                    discount_type, discount_value
                )
                response = _create_cart_discount(
                    client=client,
                    discount_type=discount_type,
                    discount_value=discount_value_in_cents,
                    sort_order=sort_order,
                    predicate=_create_target_predicate_from_program_uuids(
                        discount_data["program_uuids"], is_ten_percent_discount
                    )
                )

                if not response:
                    logger.error(
                        "Failed to create cart discount with type %s and value %s.",
                        discount_type, discount_value
                    )

                logger.info("Cart discount created successfully")
            else:
                discount = existing['results'][0]
                predicate = discount['target']['predicate']

                updated_predicate = _combine_uuids_to_predicate(
                    predicate, is_ten_percent_discount, discount_data["program_uuids"]
                )

                logger.info(
                    "Updating cart discount with type %s and value %s.",
                    discount_type, discount_value
                )
                response = client.update_cart_discount_target_predicate(discount['id'], updated_predicate)
                if not response:
                    logger.error(
                        "Failed to update cart discount with type %s and value %s.",
                        discount_type, discount_value
                    )

                logger.info("Cart discount updated successfully")
