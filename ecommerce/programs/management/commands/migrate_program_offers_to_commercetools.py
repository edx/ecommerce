from enum import Enum
from django.db import connection
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q
from ecommerce.programs.api import ProgramsApiClient
from ecommerce.programs.utils import get_all_programs
from oscar.core.loading import get_model

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

class ProxyClassDiscountType(Enum):
    PERCENTAGE = "ecommerce.programs.benefits.PercentageDiscountBenefitWithoutRange"
    ABSOLUTE = "ecommerce.programs.benefits.AbsoluteDiscountBenefitWithoutRange"

# def query_existing_discount(discount_type, discount_value):
#     query = {
#         "where": f'value(type="{discount_type}") and value(permyriad="{discount_value}") and requiresDiscountCode = false and target(type="lineItems")'
#     }
#     return commercetools_request("GET", "cart-discounts", data=query)

def group_ten_percentage_offers(cart_discounts: list):
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

    predicate = "custom.bundleId is defined"
    if programs_to_exclude:
        predicate += " and " + " and ".join(
            [f'custom.bundleId != "{uuid}"' for uuid in programs_to_exclude]
        )

    cart_discounts.append({
        "type": "relative",
        "value": 1000,  # 10% in permyriad
        "key": "program-offer-10-percent",
        "name": "10% off on Programs (Exclusions)",
        "description": "10% discount excluding specific programs",
        "predicate": predicate
    })

def group_other_offers(cart_discounts: list):
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
        discount_type = offer.benefit.proxy().benefit_class_type
        discount_value = offer.benefit.value
        type_value_key = f"{discount_type}-{discount_value}"

        if type_value_key in discount_groups:
            discount_groups[type_value_key]["program_uuids"].append(program_uuid)
        else:
            discount_groups[type_value_key] = {
                "type": discount_type,
                "value": discount_value,
                "key": f"program-offer-{discount_type}-{discount_value}",
                "name": f"{discount_value}{'%' if discount_type == 'relative' else ''} off on Programs",
                "description": f"{discount_value}{'%' if discount_type == 'relative' else ''} off on specific programs",
                "program_uuids": [program_uuid]
            }

    for _, value in discount_groups.items():
        predicate = "custom.bundleId is defined and "
        cart_discounts.append({
            "type": value["type"],
            "value": value["value"],
            "key": value["key"],
            "name": value["name"],
            "description": value["description"],
            "predicate": predicate + " or ".join([f'custom.bundleId == "{uuid}"' for uuid in value["program_uuids"]])
        })


class Command(BaseCommand):
    def handle(self, *args, **options):
        cart_discounts = []
        group_ten_percentage_offers(cart_discounts)
        group_other_offers(cart_discounts)

        print('LENGTH', len(cart_discounts))

        for discount_data in cart_discounts:
            print(discount_data['predicate'], discount_data['type'], discount_data['value'])

        # for discount_data in cart_discounts:
        #     # existing = query_existing_discount(discount_data["type"], discount_data["value"])
        #     existing = {}

        #     if existing.get("count", 0) == 0:
        #         # Create new discount with full body
        #         commercetools_request("POST", "cart-discounts", {
        #             "key": discount_data["key"],
        #             "name": {"en": discount_data["name"]},
        #             "description": {"en": discount_data["description"]},
        #             "value": {"type": discount_data["type"], "permyriad": discount_data["value"]},
        #             "cartPredicate": "lineItemExists(custom.bundleId is defined) = true",
        #             "target": {"type": "lineItems", "predicate": discount_data["predicate"]},
        #             "sortOrder": "0.00000000000001",
        #             "isActive": True,
        #             "requiresDiscountCode": False,
        #             "stackingMode": "Stacking"
        #         })
        #     else:
        #         discount = existing["results"][0]
        #         commercetools_request("POST", f"cart-discounts/{discount['id']}", {
        #             "version": discount["version"],
        #             "actions": [{
        #                 "action": "changeTarget",
        #                 "target": {
        #                     "type": "lineItems",
        #                     "predicate": discount_data["predicate"]
        #                 }
        #             }]
        #         })
