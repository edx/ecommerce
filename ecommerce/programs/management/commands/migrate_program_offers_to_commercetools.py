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


# Commercetools API config
COMMERCETOOLS_API_URL = "https://api.commercetools.com"
PROJECT_KEY = "your_project_key"
AUTH_URL = "https://auth.commercetools.com/oauth/token"
CLIENT_ID = "your_client_id"
CLIENT_SECRET = "your_client_secret"
SCOPES = "manage_project:your_project_key"

CT_ABSOLUTE_DISCOUNT_TYPE = 'absolute'
CT_PERCENTAGE_DISCOUNT_TYPE = 'relative'

TEN_PERCENT_DISCOUNT_PERMYRIAD = 1000

CT_CART_DISCOUNT_TYPE_MAP = {
    Benefit.FIXED: CT_ABSOLUTE_DISCOUNT_TYPE,
    Benefit.PERCENTAGE: CT_PERCENTAGE_DISCOUNT_TYPE
}


class ProxyClassDiscountType(Enum):
    PERCENTAGE = "ecommerce.programs.benefits.PercentageDiscountBenefitWithoutRange"
    ABSOLUTE = "ecommerce.programs.benefits.AbsoluteDiscountBenefitWithoutRange"


def _query_existing_discount(client: CommercetoolsAPIClient, discount_type: str, discount_value: int):
    try:
        response = client.get_cart_discounts_without_code_by_type_and_value(discount_type, discount_value)
        return response
    except HTTPError as err:
        logger.error(["[migrate_program_offers_to_commercetools] - Failed to get existing cart discount", err])
        return None


def _get_highest_sort_order(client: CommercetoolsAPIClient):
    try:
        response = client.get_highest_sort_order_for_cart_discount_without_codes()
        if response['count'] > 0:
            return float(response['results'][0]['sortOrder'])
    except HTTPError as err:
        logger.error(["[migrate_program_offers_to_commercetools] - Failed to get highest sortOrder", err])

    return 0.00000000000001


def _update_cart_discount(client: CommercetoolsAPIClient, discount_id: str, predicate: str):
    try:
        response = client.update_cart_discount_target_predicate(discount_id, predicate)
        return response
    except HTTPError as err:
        logger.error(
            ["[migrate_program_offers_to_commercetools] - Failed to update cart discount target predicate", err]
        )
        return None


def _create_cart_discount(client: CommercetoolsAPIClient, discount_type: str, discount_value: int, sort_order: float,
                          predicate: str):
    try:
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
    except HTTPError as err:
        logger.error(["[migrate_program_offers_to_commercetools] - Failed to create cart discount", err])
        return None


def _create_target_predicate_from_program_uuids(program_uuids: list, is_ten_percent_discount: bool):
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
    uuids = re.findall(r'custom\.bundleId\s*(?:!=|=)\s*"([^"]+)"', predicate)
    combined_uuids = list(set(uuids) | set(program_uuids))
    return _create_target_predicate_from_program_uuids(combined_uuids, is_ten_percent_discount)


def _group_ten_percentage_offers(cart_discounts: list):
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
    Group offers by discount type and value.
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
            type_display_value = '%' if discount_type == CT_PERCENTAGE_DISCOUNT_TYPE else ''
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
    def handle(self, *args, **options):
        client = CommercetoolsAPIClient()
        sort_order = _get_highest_sort_order(client)

        cart_discounts = []
        _group_ten_percentage_offers(cart_discounts)
        _group_other_offers(cart_discounts)

        for discount_data in cart_discounts:
            discount_type = discount_data["type"]
            discount_value = discount_data["value"]
            ct_discount_value = int(discount_value * 100)

            existing = _query_existing_discount(client, discount_type, ct_discount_value)

            if existing is None:
                logger.info(
                    "Failed to get discount with type %s and value %s", discount_type, discount_value
                )
                continue

            is_ten_percent_discount = (
                discount_type == CT_PERCENTAGE_DISCOUNT_TYPE and ct_discount_value == TEN_PERCENT_DISCOUNT_PERMYRIAD
            )

            if existing['count'] == 0:
                print('Creating new discount', discount_data)
                sort_order += 0.00000000000001

                _create_cart_discount(
                    client=client,
                    discount_type=discount_type,
                    discount_value=ct_discount_value,
                    sort_order=sort_order,
                    predicate=_create_target_predicate_from_program_uuids(
                        discount_data["program_uuids"], is_ten_percent_discount
                    )
                )
            else:
                discount = existing['results'][0]
                predicate = discount['target']['predicate']

                updated_predicate = _combine_uuids_to_predicate(
                    predicate, is_ten_percent_discount, discount_data["program_uuids"]
                )
                _update_cart_discount(client, discount['id'], updated_predicate)
