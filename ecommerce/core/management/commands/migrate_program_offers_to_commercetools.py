import logging
import re

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from django.utils import timezone
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient
from ecommerce.core.constants import (
    BUNDLE_CART_DISCOUNT_KEY_FORMAT,
    CT_ABSOLUTE_DISCOUNT_TYPE,
    CT_PERCENTAGE_DISCOUNT_TYPE,
    PROGRAM_OFFER_DEFAULT_SORT_ORDER,
    PROGRAM_OFFER_KEY,
    PROGRAM_OFFER_NAME,
    TEN_PERCENT_DISCOUNT_IN_CENTS,
    ProxyClassDiscountType
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


def _get_highest_sort_order(client: CommercetoolsAPIClient):
    """
    Get the highest sort order for cart discounts without discount codes.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.

    Returns:
        float: The highest sort order.
    """
    response = client.get_highest_sort_order_for_cart_discount(
        where='requiresDiscountCode=false and target(type="lineItems")'
    )

    if not response:
        raise CommandError("Failed to get highest sort order for cart discounts without codes. Exiting command.")

    if response['count'] > 0:
        return float(response['results'][0]['sortOrder'])

    return PROGRAM_OFFER_DEFAULT_SORT_ORDER


def _get_ct_bundle_offers_without_code(client: CommercetoolsAPIClient, failed_discounts: list):
    """
    Get existing bundle cart discounts (program discounts without codes) from Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.

    Returns:
        List: List of existing cart discounts without discount codes.
    """
    response = client.get_ct_bundle_offers_without_code(failed_discounts)

    if response is None:
        raise CommandError("Failed to get existing cart discounts without discount codes. Exiting command.")

    return response


def _create_cart_discount(
    client: CommercetoolsAPIClient,
    is_ten_percent_discount: bool,
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
    display_discount_symbol = " USD" if is_absolute else "%"
    program_name = f"[{PROGRAM_OFFER_NAME} - {display_discount_type}] {discount_value}{display_discount_symbol}"

    if is_ten_percent_discount:
        program_name += " (Default)"
        program_description = f"Default {PROGRAM_OFFER_NAME.lower()} with value: {discount_value}"
        program_description += f" and type: {display_discount_type}"
    else:
        program_description = f"{PROGRAM_OFFER_NAME} with value: {discount_value} and type: {display_discount_type}"

    response = client.create_bundle_cart_discount_without_code(
        key=f"{discount_type}-{discount_value_in_cents}-{PROGRAM_OFFER_KEY}",
        name=program_name,
        description=program_description,
        discount_type=discount_type,
        discount_value_in_cents=discount_value_in_cents,
        sort_order=sort_order,
        predicate=predicate
    )
    return response


def _delete_extra_ct_bundle_offers(
    client: CommercetoolsAPIClient,
    cart_discounts: list,
    deleted_discounts: list,
    failed_discounts: list
):
    """
    Delete a cart discount from Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """
    ct_bundle_offers_without_code = _get_ct_bundle_offers_without_code(client, failed_discounts)

    cart_discount_keys = {
        BUNDLE_CART_DISCOUNT_KEY_FORMAT.format(
            type=discount["type"],
            value=int(discount["value"] * 100)  # Convert to cents
        ) for discount in cart_discounts
    }

    # Finding discounts in CT that has been removed from legacy ecommerce
    for key, ct_discount in ct_bundle_offers_without_code.items():
        if key not in cart_discount_keys:
            logger.info(
                "Deleting cart discount with type: %s and value: %s as it no longer exists in legacy ecommerce.",
                ct_discount['type'], ct_discount['display_value']
            )

            response = client.delete_cart_discount_by_id(ct_discount['id'], ct_discount['version'])
            if not response:
                logger.error(
                    "Failed to delete cart discount with type: %s and value: %s.",
                    ct_discount['type'], ct_discount['display_value']
                )
                failed_discounts.append({
                    "type": ct_discount['type'],
                    "value": ct_discount['display_value'],
                    "reason": "Error while deleting cart discount."
                })
                continue

            deleted_discounts.append({
                "type": ct_discount['type'],
                "value": ct_discount['display_value']
            })
            logger.info(
                "Cart discount with type: %s and value: %s deleted successfully.",
                ct_discount['type'], ct_discount['display_value']
            )


def _create_target_predicate_from_program_uuids(program_uuids: list, is_ten_percent_discount: bool):
    """
    Create a target predicate for a cart discount based on program UUIDs.

    Args:
        program_uuids (list): List of program UUIDs.
        is_ten_percent_discount (bool): Flag indicating if the discount is a 10% discount.

    Returns:
        str: Target predicate for the cart discount.
    """
    if is_ten_percent_discount:
        predicate = "custom.bundleId is defined and "
        predicate += "("
        predicate += " and ".join([f"custom.bundleId != \"{program_uuid}\"" for program_uuid in program_uuids])
        predicate += ")"
    else:
        predicate = "("
        predicate += " or ".join([f"custom.bundleId = \"{program_uuid}\"" for program_uuid in program_uuids])
        predicate += ")"

    return predicate


def _extract_uuids_from_predicate(predicate: str):
    """
    Extract program UUIDs from a predicate.

    Args:
        predicate (str): Predicate for the cart discount.

    Returns:
        list: List of program UUIDs.
    """
    return re.findall(r'custom\.bundleId\s*(?:!=|=)\s*"([^"]+)"', predicate)


def _combine_uuids_to_predicate(
    target_predicate: str,
    is_ten_percent_discount: bool,
    legacy_program_uuids: list,
    non_ten_percentage_offer_uuids: set,
):
    """
    Combine UUIDs and condition type to create a target predicate for a cart discount.

    Args:
        predicate (str): Predicate for the cart discount.
        is_ten_percent_discount (bool): Flag indicating if the discount is a 10% discount.
        program_uuids (list): List of program UUIDs.
        non_ten_percentage_offer_uuids (set): Set of UUIDs for non-10% discounts.

    Returns:
        tuple: A tuple where the first item is a boolean indicating if an update call is needed,
               the second item is the updated target predicate or None if no update is needed,
               the third item is the list of uuids being added,
               and the forth item is the list of uuids being removed.
    """
    extracted_uuids_from_predicate = _extract_uuids_from_predicate(target_predicate)

    uuids_in_ct = set(extracted_uuids_from_predicate)
    legacy_uuids = set(legacy_program_uuids)

    # Handling 10% discount case separately as it deals with exclusion filter
    if is_ten_percent_discount:
        # Removing uuids that are not in the non-10% discounts to allow default 10% discount no new programs
        uuids_not_to_add = set()
        for uuid in (legacy_uuids - uuids_in_ct):
            if uuid not in non_ten_percentage_offer_uuids:
                uuids_not_to_add.add(uuid)

        updated_uuids = legacy_uuids - uuids_not_to_add
        if updated_uuids == uuids_in_ct:
            return False, None, [], []

        updated_predicate = _create_target_predicate_from_program_uuids(
            list(updated_uuids),
            is_ten_percent_discount
        )
        uuids_added = list(updated_uuids - uuids_in_ct)
        uuids_removed = list(uuids_in_ct - updated_uuids)
    else:
        if uuids_in_ct == legacy_uuids:
            return False, None, [], []

        updated_predicate = _create_target_predicate_from_program_uuids(
            list(legacy_uuids),
            is_ten_percent_discount
        )
        uuids_added = list(legacy_uuids - uuids_in_ct)
        uuids_removed = list(uuids_in_ct - legacy_uuids)

    return True, updated_predicate, uuids_added, uuids_removed


def _group_ten_percentage_offers(cart_discounts: list, site_configuration):
    """
    Group offers of 10% discount.

    Args:
        cart_discounts (list): List to store cart discounts.
    """
    partner_id = site_configuration.partner_id
    offers = ConditionalOffer.objects.filter(
        Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()),
        offer_type=ConditionalOffer.SITE,
        condition__program_uuid__isnull=False,
        benefit__value=10,
        benefit__proxy_class=ProxyClassDiscountType.PERCENTAGE.value,
        partner_id=partner_id
    ).select_related('benefit', 'condition')

    programs_with_offer = [str(offer.condition.program_uuid) for offer in offers]

    program_uuids = get_all_program_uuids(site_configuration)

    if not program_uuids:
        raise CommandError("Failed to retrieve programs uuids from course-discovery. Exiting command.")

    programs_to_exclude = list(set(program_uuids) - set(programs_with_offer))

    cart_discounts.append({
        "type": CT_PERCENTAGE_DISCOUNT_TYPE,
        "value": 10.00,
        "program_uuids": programs_to_exclude
    })


def _group_other_offers(cart_discounts: list, partner_id: int):
    """
    Group offers by discount type and value that are not 10% discount.

    Args:
        cart_discounts (list): List to store cart discounts.
    """
    offers = ConditionalOffer.objects.filter(
        Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()),
        offer_type=ConditionalOffer.SITE,
        condition__program_uuid__isnull=False,
        partner_id=partner_id
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


def _get_non_ten_percentage_offer_uuids():
    """
    Get non-10% discount offer uuids from legacy ecommerce.

    Args:
        cart_discounts (set): List of cart discounts.
    """
    # Getting non-10% discount offer uuids from legacy ecommerce
    non_ten_percentage_offer_uuids = {
        str(uuid) for uuid in ConditionalOffer.objects.filter(
            offer_type=ConditionalOffer.SITE,
            condition__program_uuid__isnull=False,
        ).exclude(
            benefit__value=10,
            benefit__proxy_class=ProxyClassDiscountType.PERCENTAGE.value
        ).values_list('condition__program_uuid', flat=True)
    }

    # Getting 10% discount offer uuids from legacy ecommerce that are expired
    non_ten_percentage_offer_uuids |= {
        str(uuid) for uuid in ConditionalOffer.objects.filter(
            end_datetime__lt=timezone.now(),
            offer_type=ConditionalOffer.SITE,
            condition__program_uuid__isnull=False,
            benefit__value=10,
            benefit__proxy_class=ProxyClassDiscountType.PERCENTAGE.value
        ).values_list('condition__program_uuid', flat=True)
    }

    return non_ten_percentage_offer_uuids


def _migrate_program_offers(client):  # pylint: disable=too-many-statements
    """
    Migrate program offers to Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """
    created_discounts = []
    updated_discounts = []
    failed_discounts = []
    deleted_discounts = []

    sort_order = _get_highest_sort_order(client)
    non_ten_percentage_offer_uuids = _get_non_ten_percentage_offer_uuids()

    site_configuration = SiteConfiguration.objects.first()
    partner_id = site_configuration.partner_id

    cart_discounts = []
    _group_ten_percentage_offers(cart_discounts, site_configuration)
    _group_other_offers(cart_discounts, partner_id)

    # Delete cart discounts that are no longer in legacy ecommerce
    _delete_extra_ct_bundle_offers(
        client,
        cart_discounts,
        deleted_discounts,
        failed_discounts
    )

    # Getting fresh cart discounts from Commercetools after deleting extra cart discounts
    existing_cart_discounts_in_ct = _get_ct_bundle_offers_without_code(client, failed_discounts)

    for discount_data in cart_discounts:
        discount_type = discount_data["type"]
        discount_value = discount_data["value"]
        discount_value_in_cents = int(discount_value * 100)

        logger.info(
            "Checking if cart discount already exists in Commercetools with type: %s, and value: %s.",
            discount_type, discount_value
        )

        existing_discount = existing_cart_discounts_in_ct.get(
            BUNDLE_CART_DISCOUNT_KEY_FORMAT.format(type=discount_type, value=discount_value_in_cents)
        )

        is_ten_percent_discount = (
            discount_type == CT_PERCENTAGE_DISCOUNT_TYPE and
            discount_value_in_cents == TEN_PERCENT_DISCOUNT_IN_CENTS
        )

        if not existing_discount:
            logger.info(
                "No cart discount exists with type: %s, and value: %s. Creating a new one.",
                discount_type, discount_value
            )

            sort_order += PROGRAM_OFFER_DEFAULT_SORT_ORDER

            if not is_ten_percent_discount:
                logger.info(
                    "Creating cart discount with type: %s, value: %s, sort order: %s, including program uuids: %s.",
                    discount_type,
                    discount_value,
                    f"{sort_order:.18f}".rstrip("0").rstrip("."),
                    ", ".join(discount_data["program_uuids"])
                )
            else:
                logger.info(
                    "Creating cart discount with type: %s, value: %s, and sort order: %s.",
                    discount_type,
                    discount_value,
                    f"{sort_order:.18f}".rstrip("0").rstrip(".")
                )

            response = _create_cart_discount(
                client=client,
                is_ten_percent_discount=is_ten_percent_discount,
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
            logger.info(
                "Existing cart discount found with type %s and value %s.",
                discount_type, discount_value
            )

            version = existing_discount['version']
            target_predicate = existing_discount['target_predicate']

            needs_update, updated_predicate, uuids_added, uuids_removed = _combine_uuids_to_predicate(
                target_predicate,
                is_ten_percent_discount,
                discount_data["program_uuids"],
                non_ten_percentage_offer_uuids
            )

            if not needs_update:
                logger.info(
                    "Cart discount with type: %s, and value: %s is up to date.",
                    discount_type, discount_value
                )
                continue

            update_log = f"Updating existing cart discount with type: {discount_type}, value: {discount_value}"
            if uuids_added:
                update_log += f" and adding uuids:{', '.join(uuids_added)}"
            if uuids_removed:
                update_log += f" and removing uuids:{', '.join(uuids_removed)}"
            logger.info(update_log)
            response = client.update_cart_discount_target_predicate(existing_discount['id'], updated_predicate, version)

            if not response:
                logger.error(
                    "Failed to update cart discount with type: %s, and value: %s.",
                    discount_type, discount_value
                )
                failed_discounts.append({
                    "type": discount_type,
                    "value": discount_value,
                    "reason": "Error while updating cart discount."
                })
                continue

            update_log = f"Cart discount updated successfully with type: {discount_type}, value: {discount_value}"
            if uuids_added:
                update_log += f" and adding uuids:{', '.join(uuids_added)}"
            if uuids_removed:
                update_log += f" and removing uuids:{', '.join(uuids_removed)}"
            logger.info(update_log)
            updated_discounts.append({
                "type": discount_type,
                "value": discount_value,
                "uuids_added": uuids_added,
                "uuids_removed": uuids_removed
            })

    if created_discounts:
        created_summary = ", ".join(
            f"{d['type']} {d['value']}" for d in created_discounts
        )
        logger.info("Summary of created discounts: %s", created_summary)
    else:
        logger.info("No discounts were created.")

    if updated_discounts:
        updated_summary = []
        for discount in updated_discounts:
            update_log = f"{discount['type']} {discount['value']}"

            if discount['uuids_added']:
                update_log += f" (added uuids: {', '.join(discount['uuids_added'])})"
            if discount['uuids_removed']:
                update_log += f" (removed uuids: {', '.join(discount['uuids_removed'])})"

            updated_summary.append(update_log)

        updated_summary = ", ".join(updated_summary)
        logger.info("Summary of updated discounts: %s", updated_summary)
    else:
        logger.info("No discounts were updated.")

    if deleted_discounts:
        deleted_summary = ", ".join(
            f"{discount['type']} {discount['value']}" for discount in deleted_discounts
        )
        logger.info("Summary of deleted discounts: %s", deleted_summary)
    else:
        logger.info("No discounts were deleted.")

    if failed_discounts:
        failed_summary = ", ".join(
            f"{discount['type']} {discount['value']} (Reason: {discount['reason']})"
            for discount in failed_discounts
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
            raise CommandError(f"Failed to initialize Commercetools client. Error: {error}") from error

        _migrate_program_offers(client)
