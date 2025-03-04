import logging
import re
from enum import Enum

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient
from ecommerce.core.constants import (
    CT_ABSOLUTE_DISCOUNT_TYPE,
    CT_PERCENTAGE_DISCOUNT_TYPE,
    PROGRAM_OFFER_KEY,
    PROGRAM_OFFER_NAME,
    TEN_PERCENT_DISCOUNT_IN_CENTS
)
from ecommerce.programs.utils import get_all_program_uuids

logger = logging.getLogger(__name__)


Benefit = get_model('offer', 'Benefit')
ConditionalOffer = get_model('offer', 'ConditionalOffer')
SiteConfiguration = get_model('core', 'SiteConfiguration')

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

    if not response:
        raise CommandError("Failed to get highest sort order for cart discounts without codes. Exiting command.")

    if response['count'] > 0:
        return float(response['results'][0]['sortOrder'])

    return 0.00000000000001


def _create_cart_discount(
    client: CommercetoolsAPIClient,
    discount_type: str,
    discount_value_in_cents: int,
    discount_value: float,
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
    is_absolute = discount_type == CT_ABSOLUTE_DISCOUNT_TYPE
    display_discount_type = "Fixed" if is_absolute else "Percentage"
    display_discount_symbol = "%" if is_absolute else "USD"
    response = client.create_bundle_cart_discount_without_code(
        key=f"{discount_type}-{discount_value_in_cents}-{PROGRAM_OFFER_KEY}",
        name=f"{discount_type.capitalize()} {discount_value} {PROGRAM_OFFER_NAME}",
        name=f"[{PROGRAM_OFFER_NAME} - {display_discount_type}] {discount_value} {display_discount_symbol}",
        description=f"{PROGRAM_OFFER_NAME} with value: {discount_value} and type: {display_discount_type}",
        discount_type=discount_type,
        discount_value=discount_value_in_cents,
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


def _combine_uuids_to_predicate(predicate: str, is_ten_percent_discount: bool, legacy_program_uuids: list):
    """
    Combine UUIDs and condition type to create a target predicate for a cart discount.

    Args:
        predicate (str): Predicate for the cart discount.
        is_ten_percent_discount (bool): Flag indicating if the discount is a 10% discount.
        program_uuids (list): List of program UUIDs.

    Returns:
        tuple: A tuple where the first item is a boolean indicating if an update call is needed,
               and the second item is the updated target predicate or None if no update is needed.
    """
    extracted_uuids_from_predicate = re.findall(r'custom\.bundleId\s*(?:!=|=)\s*"([^"]+)"', predicate)

    existing_uuids = set(extracted_uuids_from_predicate)
    legacy_uuids = set(legacy_program_uuids)
    new_uuids_in_legacy = list(legacy_uuids - existing_uuids)

    if not new_uuids_in_legacy:
        return False, None, []

    combined_uuids = list(existing_uuids | legacy_uuids)
    updated_predicate = _create_target_predicate_from_program_uuids(combined_uuids, is_ten_percent_discount)

    return True, updated_predicate, new_uuids_in_legacy


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

    programs_with_offer = [offer.condition.program_uuid for offer in offers]

    site_configuration = SiteConfiguration.objects.first()
    program_uuids = get_all_program_uuids(site_configuration)

    if not program_uuids:
        raise CommandError("Failed to retrieve programs uuids from course-discovery. Exiting command.")

    programs_to_exclude = list(set(program_uuids) - set(programs_with_offer))

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
        program_uuid = str(offer.condition.program_uuid)
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

def _migrate_program_offers(client):
    """
    Migrate program offers to Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """
    sort_order = _get_highest_sort_order(client)

    cart_discounts = []
    _group_ten_percentage_offers(cart_discounts)
    _group_other_offers(cart_discounts)

    created_discounts = []
    updated_discounts = []
    failed_discounts = []

    command_soft_failed = False
    for discount_data in cart_discounts:
        discount_type = discount_data["type"]
        discount_value = discount_data["value"]
        discount_value_in_cents = int(discount_value * 100)

        logger.info(
            "Fetching existing cart discount with type: %s, and value: %s in Commercetools.",
            discount_type, discount_value
        )

        # TODO: [Future performance issue] - Fetch all cart discounts outside loop and
        # process in the memory to save multiple CT calls.
        existing = client.get_cart_discounts_without_code_by_type_and_value(discount_type, discount_value_in_cents)
        if not existing:
            logger.error(
                "Error while fetching cart discount with type: %s, and value: %s. Skipping this group for now.",
                discount_type, discount_value
            )

            command_soft_failed = True
            failed_discounts.append({
                "type": discount_type,
                "value": discount_value,
                "reason": "Error while fetching cart discount."
            })
            continue

        is_ten_percent_discount = (
            discount_type == CT_PERCENTAGE_DISCOUNT_TYPE and
            discount_value_in_cents == TEN_PERCENT_DISCOUNT_IN_CENTS
        )

        if existing['count'] == 0:
            logger.info(
                "No cart discount exists with type: %s, and value: %s. Creating a new one.",
                discount_type, discount_value
            )

            sort_order += 0.00000000000001

            if not is_ten_percent_discount:
                logger.info(
                    "Creating cart discount with type: %s, value: %s, sort order: %s, including program uuids: %s.",
                    discount_type,
                    discount_value,
                    f"{sort_order:.14f}",
                    ", ".join(discount_data["program_uuids"])
                )
            else:
                logger.info(
                    "Creating cart discount with type: %s, value: %s, and sort order: %s.",
                    discount_type,
                    discount_value,
                    f"{sort_order:.14f}"
                )

            response = _create_cart_discount(
                client=client,
                discount_type=discount_type,
                discount_value_in_cents=discount_value_in_cents,
                discount_value=discount_value,
                sort_order=sort_order,
                predicate=_create_target_predicate_from_program_uuids(
                    discount_data["program_uuids"], is_ten_percent_discount
                )
            )

            if not response:
                logger.error(
                    "Failed to create cart discount with type: %s, and value: %s.",
                    discount_type, discount_value
                )

                command_soft_failed = True
                failed_discounts.append({
                    "type": discount_type,
                    "value": discount_value,
                    "reason": "Error while creating cart discount."
                })
                continue

            logger.info(
                "Cart discount created successfully with type: %s, and value: %s.",
                discount_type, discount_value
            )
            created_discounts.append({
                "type": discount_type,
                "value": discount_value
            })
        else:
            if existing['count'] > 1:
                logger.error(
                    "More than one cart discount exists with type: %s, and value: %s. Skipping this group for now.",
                    discount_type, discount_value
                )

                command_soft_failed = True
                failed_discounts.append({
                    "type": discount_type,
                    "value": discount_value,
                    "reason": "Multiple cart discounts found for same type and value."
                })
                continue

            logger.info(
                "Existing cart discount found with type %s and value %s.",
                discount_type, discount_value
            )

            discount = existing['results'][0]
            version = discount['version']
            predicate = discount['target']['predicate']

            needs_update, updated_predicate, uuids_being_added = _combine_uuids_to_predicate(
                predicate, is_ten_percent_discount, discount_data["program_uuids"]
            )

            if not needs_update:
                logger.info(
                    "Cart discount with type: %s, and value: %s is up to date.",
                    discount_type, discount_value
                )
                continue

            logger.info(
                "Updating existing cart discount with type: %s, value: %s, and predicate with program uuids: %s.",
                discount_type,
                discount_value,
                ", ".join(uuids_being_added)
            )
            response = client.update_cart_discount_target_predicate(discount['id'], updated_predicate, version)

            if not response:
                logger.error(
                    "Failed to update cart discount with type: %s, and value: %s.",
                    discount_type, discount_value
                )
                command_soft_failed = True
                failed_discounts.append({
                    "type": discount_type,
                    "value": discount_value,
                    "reason": "Error while updating cart discount."
                })
                continue

            logger.info(
                "Cart discount updated successfully with type: %s, value: %s, and predicate with program uuids: %s.",
                discount_type,
                discount_value,
                ", ".join(uuids_being_added)
            )
            updated_discounts.append({
                "type": discount_type,
                "value": discount_value,
                "uuids_added": uuids_being_added
            })

    if created_discounts:
        created_summary = ", ".join(
            f"{d['type']} {d['value']}" for d in created_discounts
        )
        logger.info("Summary of created discounts: %s", created_summary)
    else:
        logger.info("No discounts were created.")

    if updated_discounts:
        updated_summary = ", ".join(
            f"{d['type']} {d['value']} (UUIDs: {', '.join(d['uuids_added'])})"
            for d in updated_discounts
        )
        logger.info("Summary of updated discounts: %s", updated_summary)
    else:
        logger.info("No discounts were updated.")

    if command_soft_failed:
        failed_summary = ", ".join(
            f"{d['type']} {d['value']} (Reason: {d['reason']})"
            for d in failed_discounts
        )
        logger.error("Summary of failed discount migrations: %s", failed_summary)
        raise CommandError("Command run completed with errors.")

    logger.info("Program offers migrated to Commercetools successfully.")


class Command(BaseCommand):
    """Command to migrate program offers to Commercetools."""

    def handle(self, *args, **options):
        """Handle the command."""
        try:
            client = CommercetoolsAPIClient()
        except HTTPError as error:
            raise CommandError(f"Failed to initialize Commercetools client. Error: {error}")

        _migrate_program_offers(client)


