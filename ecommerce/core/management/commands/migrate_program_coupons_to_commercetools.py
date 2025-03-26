import logging
from typing import Optional

from dateutil import parser as dateutil_parser
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch, Q
from django.utils import timezone
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient
from ecommerce.core.constants import CT_ABSOLUTE_DISCOUNT_TYPE, CT_PERCENTAGE_DISCOUNT_TYPE, ProxyClassDiscountType
from ecommerce.invoice.models import Invoice

logger = logging.getLogger(__name__)


Product = get_model("catalogue", "Product")
ProductCategory = get_model("catalogue", "ProductCategory")
Voucher = get_model("voucher", "Voucher")
CouponVouchers = get_model("voucher", "CouponVouchers")
Benefit = get_model("offer", "Benefit")
Condition = get_model("offer", "Condition")
ConditionalOffer = get_model("offer", "ConditionalOffer")
SiteConfiguration = get_model("core", "SiteConfiguration")


def _get_highest_sort_order(client: CommercetoolsAPIClient):
    """
    Get the highest sort order for cart discounts without discount codes.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.

    Returns:
        float: The highest sort order.
    """
    response = client.get_highest_sort_order_for_cart_discount(
       where='requiresDiscountCode=true and custom(fields(discountType="program-discount"))'
    )

    if not response:
        raise CommandError("Failed to get highest sort order. Exiting command.")

    if response['count'] > 0:
        return float(response['results'][0]['sortOrder'])

    return 0.00000000001


def _get_cent_amount_from_value(value):
    """
    Get cent amount from value.
    """
    return value.get("permyriad", value.get("money", [{}])[0].get("centAmount"))


def _map_benefit_to_ct_value(benefit):
    """
    Map Benefit to Commercetools discount value.
    """
    cent_amount = int(benefit.value * 100)

    return {
        ProxyClassDiscountType.ABSOLUTE.value: {
            "type": CT_ABSOLUTE_DISCOUNT_TYPE,
            "money": [{"centAmount": cent_amount, "currencyCode": "USD"}],
            "applicationMode": "ProportionateDistribution",
        },
        ProxyClassDiscountType.PERCENTAGE.value: {
            "type": CT_PERCENTAGE_DISCOUNT_TYPE,
            "permyriad": cent_amount,
        },
    }[benefit.proxy_class]


def _map_voucher_usage_to_ct_code_applications(usage, max_global_applications):
    """
    Map Voucher usage to Commercetools code applications.
    """
    return {
        "Single use": {
            "maxApplications": 1,
        },
        "Multi-use": {
            "maxApplications": max_global_applications,
        },
        "Once per customer": {
            "maxApplications": max_global_applications,
            "maxApplicationsPerCustomer": 1,
        },
    }[usage]


def _map_coupons_to_ct_cart_discounts_and_discount_codes(coupons):
    """
    Map coupons to Commercetools cart discounts and discount codes.
    """
    results = []

    for coupon in coupons:
        try:
            if coupon.attr.inactive:
                logger.info(f"Skipping coupon {coupon.title} as it is inactive")
                continue
        except AttributeError:
            ...

        # Exclude consumed vouchers
        vouchers = coupon.attr.coupon_vouchers.vouchers.exclude(
            usage="Single use",
            num_orders=1,
        )

        voucher = vouchers.first()
        offer = voucher.best_offer
        program_uuid = offer.condition.program_uuid

        cart_discount = {
            "name": f'[Migrated Program Coupon] - {coupon.title}',
            "key": coupon.slug,
            "description": _get_note_for_coupon(coupon),
            "customFields": {
                "client": _get_client_for_coupon(coupon),
                "category": _get_category_for_coupon(coupon),
                "discountType": "program-discount",
            },
            "cartPredicate": f'forAllLineItems(custom.bundleId = "{program_uuid}") = true',
            "target": {
                "type": "lineItems",
                "predicate": "1 = 1",
            },
            "value": _map_benefit_to_ct_value(offer.benefit),
        }

        discount_codes = [
            {
                "name": voucher.name,
                "key": voucher.code,
                "code": voucher.code,
                "validFrom": voucher.start_datetime.isoformat(),
                "validUntil": voucher.end_datetime.isoformat(),
                **_map_voucher_usage_to_ct_code_applications(
                    voucher.usage, offer.max_global_applications
                ),
            }
            for voucher in vouchers.all()
        ]

        results.append((cart_discount, discount_codes))
    return results


def _get_client_for_coupon(coupon) -> Optional[str]:
    """
    Get the client for the coupon.
    """
    try:
        client = Invoice.objects.get(
            order__lines__product=coupon
        ).business_client.name
    except Invoice.DoesNotExist:
        client = None

    if not client:
        logger.warn(f"Client not found for coupon {coupon.title}.")

    return client


def _get_note_for_coupon(coupon) -> Optional[str]:
    """
    Get the note for the coupon.
    """
    try:
        note = coupon.attr.note
    except AttributeError:
        note = None

    return note


def _get_category_for_coupon(coupon) -> Optional[str]:
    """
    Get the category for the coupon.
    """
    try:
        category = ProductCategory.objects.get(product=coupon).category.name
    except ProductCategory.DoesNotExist:
        category = None

    if not category:
        logger.warn(f"Category not found for coupon {coupon.title}.")

    return category


def _get_program_coupons(partner_id):
    """
    Get program coupons from the database.
    """
    included_offers = ConditionalOffer.objects.filter(
        Q(end_datetime__isnull=True) | Q(end_datetime__gte=timezone.now()),
        offer_type=ConditionalOffer.VOUCHER,
        condition__program_uuid__isnull=False,
        partner_id=partner_id
    ).exclude(
        Q(benefit__type=Benefit.FIXED) |
        Q(benefit__type=Benefit.PERCENTAGE, benefit__value=100.00)
    )

    coupons = (
        Product.objects.filter(
            product_class__slug="coupon",
            coupon_vouchers__vouchers__end_datetime__gte=timezone.now(),
            coupon_vouchers__vouchers__offers__in=included_offers
        )
        .prefetch_related(
            Prefetch(
                "coupon_vouchers__vouchers",
            ),
            Prefetch(
                "coupon_vouchers__vouchers__offers",
            ),
            Prefetch(
                "coupon_vouchers__vouchers__offers__condition",
            ),
            Prefetch(
                "coupon_vouchers__vouchers__offers__benefit",
            ),
        )
        .distinct()
    )

    return coupons


def _make_update_actions_by_comparing_cart_discounts(
    *, discount_in_ecommerce, discount_in_ct
):
    """
    Create update actions after comparing discounts in ecommerce and commercetools.

    Returns:
        List: List of update actions.
    """
    def _make_update_action_for_key(key, value):
        return {
            "name": {
                "action": "changeName",
                "name": {
                    "en-US": value,
                },
            },
            "description": {
                "action": "setDescription",
                "description": {
                    "en-US": value,
                },
            },
            "cartPredicate": {
                "action": "changeCartPredicate",
                "cartPredicate": value,
            },
            "value": {
                "action": "changeValue",
                "value": value,
            },
            "customFields": lambda field_name: {
                "action": "setCustomField",
                "name": field_name,
                "value": value,
            },
        }[key]

    update_actions = []

    if discount_in_ecommerce["value"]["type"] != discount_in_ct["value"]["type"] or (
        _get_cent_amount_from_value(discount_in_ecommerce["value"]) !=
        _get_cent_amount_from_value(discount_in_ct["value"])
    ):
        update_actions.append(
            _make_update_action_for_key("value", discount_in_ecommerce["value"])
        )

    for key in ["name", "description", "cartPredicate"]:
        if discount_in_ecommerce[key] != discount_in_ct[key]:
            update_actions.append(
                _make_update_action_for_key(key, discount_in_ecommerce[key])
            )

    for field, field_value in discount_in_ecommerce["customFields"].items():
        if field_value != discount_in_ct["customFields"].get(field):
            update_actions.append(
                _make_update_action_for_key("customFields", field_value)(field)
            )

    return update_actions


def _make_update_actions_by_comparing_discount_codes(
    *,
    discount_in_ecommerce,
    discount_in_ct,
):
    def _make_update_action_for_key(key, value):
        return {
            "maxApplications": {
                "action": "setMaxApplications",
                "maxApplications": value,
            },
            "validFrom": {
                "action": "setValidFrom",
                "validFrom": value,
            },
            "validUntil": {
                "action": "setValidUntil",
                "validUntil": value,
            },
        }[key]

    update_actions = []

    if discount_in_ecommerce["maxApplications"] != discount_in_ct["maxApplications"]:
        update_actions.append(
            _make_update_action_for_key(
                "maxApplications", discount_in_ecommerce["maxApplications"]
            )
        )

    for key in ["validFrom", "validUntil"]:
        if not discount_in_ct.get(key) or dateutil_parser.isoparse(
            discount_in_ecommerce[key]
        ) != dateutil_parser.isoparse(discount_in_ct[key]):
            update_actions.append(
                _make_update_action_for_key(key, discount_in_ecommerce[key])
            )

    return update_actions


def _generate_summary(summary_info):
    """
    Generate summary of migration.
    """
    success_summary = {
        "created_cart_discounts": "\n".join(
            cart_discount["name"]
            for cart_discount in summary_info["cart_discounts"]["created"]
        ) or 'No cart discounts created.',
        "updated_cart_discounts": "\n".join(
            cart_discount["name"]
            for cart_discount in summary_info["cart_discounts"]["updated"]
        ) or 'No cart discounts updated.',
        "created_discount_codes": "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["created"]
        ) or 'No discount codes created.',
        "updated_discount_codes": "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["updated"]
        ) or 'No discount codes updated.',
    }

    for key, value in success_summary.items():
        humanized = " ".join(key.capitalize() for key in key.split("_"))
        logger.info(f"\nSummary of {humanized}:\n{value}\n")

    if (
        summary_info["cart_discounts"]["failed"] or
        summary_info["discount_codes"]["failed"]
    ):
        if summary_info["cart_discounts"]["failed"]:
            logger.error(
                "Summary of failed cart discount migrations: %s",
                ", ".join(
                    f"{discount['name']} (Reason: {discount['reason']})"
                    for discount in summary_info["cart_discounts"]["failed"]
                ),
            )
        if summary_info["discount_codes"]["failed"]:
            logger.error(
                "Summary of failed discount code migrations: %s",
                ", ".join(
                    f"{discount['code']} - {discount['name']} (Reason: {discount['reason']})"
                    for discount in summary_info["discount_codes"]["failed"]
                ),
            )

        raise CommandError("Command run completed with errors.")


def _migrate_program_coupons(client: CommercetoolsAPIClient):
    """
    Migrate program coupons to Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """
    sort_order = _get_highest_sort_order(client)
    sort_order += 0.00000000001

    site_configuration = SiteConfiguration.objects.first()
    partner_id = site_configuration.partner_id

    coupons = _get_program_coupons(partner_id)
    mapped_discounts = _map_coupons_to_ct_cart_discounts_and_discount_codes(coupons)

    existing_discounts_in_ct = client.get_ct_discounts_with_code()
    if not existing_discounts_in_ct:
        raise CommandError("Failed to get existing discounts in Commercetools. Exiting command.")

    summary_info = {
        "cart_discounts": {
            "created": [],
            "updated": [],
            "failed": [],
        },
        "discount_codes": {
            "created": [],
            "updated": [],
            "failed": [],
        },
    }

    def _migrate_discount_code(discount_code, cartDiscountId):
        discount_code_response = client.create_discount_code(
            cartDiscountId=cartDiscountId, **discount_code
        )

        if discount_code_response:
            logger.info(
                f"Discount code created successfully with name: {discount_code['name']} and code: {discount_code['code']}."
            )
            summary_info["discount_codes"]["created"].append(discount_code)
        else:
            logger.error(
                f"Failed to create discount code with name: {discount_code['name']} and code: {discount_code['code']}."
            )
            summary_info["discount_codes"]["failed"].append(
                {
                    "name": discount_code["name"],
                    "code": discount_code["code"],
                    "reason": "Error while creating discount code.",
                }
            )

    for cart_discount, discount_codes in mapped_discounts:
        if cart_discount["key"] in existing_discounts_in_ct:
            cart_discount_in_ct, discount_codes_in_ct = existing_discounts_in_ct[
                cart_discount["key"]
            ]

            update_actions_for_cart_discount = (
                _make_update_actions_by_comparing_cart_discounts(
                    discount_in_ecommerce=cart_discount,
                    discount_in_ct=cart_discount_in_ct,
                )
            )

            if update_actions_for_cart_discount:
                cart_discount_response = client.update_resource_by_key(
                    resource_type="cart-discounts",
                    resource_key=cart_discount_in_ct["key"],
                    version=cart_discount_in_ct["version"],
                    actions=update_actions_for_cart_discount,
                )

                if not cart_discount_response:
                    logger.error(
                        f"Failed to update cart discount with name: {cart_discount['name']}."
                    )
                    summary_info["cart_discounts"]["failed"].append(
                        {
                            "name": cart_discount["name"],
                            "reason": "Error while updating cart discount.",
                        }
                    )
                    continue
                summary_info["cart_discounts"]["updated"].append(cart_discount)

            for discount_code in discount_codes:
                discount_code_in_ct = discount_codes_in_ct.get(discount_code["key"])
                if discount_code_in_ct:
                    update_actions_for_discount_code = (
                        _make_update_actions_by_comparing_discount_codes(
                            discount_in_ecommerce=discount_code,
                            discount_in_ct=discount_code_in_ct,
                        )
                    )

                    if update_actions_for_discount_code:
                        discount_code_response = client.update_resource_by_key(
                            resource_type="discount-codes",
                            resource_key=discount_code_in_ct["key"],
                            version=discount_code_in_ct["version"],
                            actions=update_actions_for_discount_code,
                        )

                        if not discount_code_response:
                            logger.error(
                                f"Failed to update discount code with name: {discount_code['name']} and code: {discount_code['code']}."
                            )
                            summary_info["discount_codes"]["failed"].append(
                                {
                                    "name": discount_code["name"],
                                    "code": discount_code["code"],
                                    "reason": "Error while updating discount code.",
                                }
                            )
                            continue
                        summary_info["discount_codes"]["updated"].append(
                            discount_code
                        )
                else:
                    _migrate_discount_code(discount_code, cart_discount_in_ct["id"])

        else:
            cart_discount_response = client.create_cart_discount(sortOrder=sort_order, **cart_discount)

            if not cart_discount_response:
                logger.error(
                    f"Failed to create cart discount with name: {cart_discount['name']}."
                )
                summary_info["cart_discounts"]["failed"].append(
                    {
                        "name": cart_discount["name"],
                        "reason": "Error while creating cart discount.",
                    }
                )
                continue

            sort_order += 0.00000000001

            logger.info(
                f"Cart discount created successfully with name: {cart_discount['name']}."
            )
            summary_info["cart_discounts"]["created"].append(cart_discount)

            for discount_code in discount_codes:
                _migrate_discount_code(discount_code, cart_discount_response["id"])

    _generate_summary(summary_info)

    logger.info("Program coupons migrated to Commercetools successfully.")


class Command(BaseCommand):
    """Command to migrate program coupons to Commercetools."""

    def handle(self, *args, **options):
        """Handle the command."""
        try:
            client = CommercetoolsAPIClient()
        except HTTPError as error:
            raise CommandError(
                f"Failed to initialize Commercetools client. Error: {error}"
            ) from error

        _migrate_program_coupons(client)
