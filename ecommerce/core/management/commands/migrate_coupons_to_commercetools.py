import logging
import re
from typing import Optional

from dateutil import parser as dateutil_parser
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch, Q
from django.utils import timezone
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient
from ecommerce.core.constants import CT_ABSOLUTE_DISCOUNT_TYPE, CT_PERCENTAGE_DISCOUNT_TYPE
from ecommerce.core.utils import convert_querystring_to_predicate
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
        Benefit.FIXED: {
            "type": CT_ABSOLUTE_DISCOUNT_TYPE,
            "money": [{"centAmount": cent_amount, "currencyCode": "USD"}],
            "applicationMode": "ProportionateDistribution",
        },
        Benefit.PERCENTAGE: {
            "type": CT_PERCENTAGE_DISCOUNT_TYPE,
            "permyriad": cent_amount,
        },
    }[benefit.type]


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


def _map_voucher_criteria_to_cart_predicate(
    *, seat_types, email_domains, catalog_query, site_configuration
):

    def _join_conditions(conditions):
        return " and ".join(conditions)

    def _map_list_to_ct_predicate_condition(key, data):
        """
        Map a comma-separated list from database to commercetools predicate condition.
        """
        values = re.split(r"\s*,\s*", data)

        if len(values) == 1:
            return f'{key} = "{values[0]}"'
        else:
            values_string = ",".join(f'"{value}"' for value in values)

            return f"{key} in ({values_string})"

    cart_conditions = []
    lineItemConditions = [
        "quantity = 1",
        "custom.bundleId is not defined",
    ]

    if seat_types:
        lineItemConditions.append(
            _map_list_to_ct_predicate_condition("attributes.mode", seat_types)
        )

    if catalog_query:
        predicate = convert_querystring_to_predicate(
            catalog_query, site_configuration
        ).strip()
        if predicate:
            lineItemConditions.append(predicate)

    cart_conditions.append(
        f"lineItemCount({_join_conditions(lineItemConditions)}) = 1"
    )

    if email_domains:
        cart_conditions.append(
            _map_list_to_ct_predicate_condition("custom.emailDomain", email_domains)
        )

    cart_predicate = _join_conditions(cart_conditions)

    return cart_predicate


def _map_coupons_to_ct_cart_discounts_and_discount_codes(
    coupons, site_configuration
):
    """
    Map coupons to Commercetools cart discounts and discount codes.
    """
    results = []

    for i, coupon in enumerate(reversed(coupons)):
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
        offer_range = offer.condition.range

        cart_discount = {
            "name": coupon.title,
            "key": coupon.slug,
            "description": _get_note_for_coupon(coupon),
            "customFields": {
                "client": _get_client_for_coupon(coupon),
                "category": _get_category_for_coupon(coupon),
                "discountType": "course-discount",
            },
            "cartPredicate": _map_voucher_criteria_to_cart_predicate(
                seat_types=offer_range.course_seat_types,
                email_domains=offer.email_domains,
                catalog_query=offer_range.catalog_query,
                site_configuration=site_configuration,
            ),
            # TODO: fix this
            "sortOrder": 0.00001 - ((i + 1) / 1000000),
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


def _get_non_multiuse_course_coupons():
    """
    Get non-multiuse course coupons from the database.
    """

    excluded_offers = ConditionalOffer.objects.filter(
        Q(benefit__type="Percentage", benefit__value=100.00) |
        Q(condition__range__course_seat_types__icontains="credit") |
        Q(condition__range__catalog_query__isnull=True)
    )

    coupons = (
        Product.objects.filter(
            product_class__slug="coupon",
            coupon_vouchers__vouchers__end_datetime__gt=timezone.now(),
        )
        .exclude(
            Q(coupon_vouchers__vouchers__name__icontains="Financial Assistance") |
            Q(coupon_vouchers__vouchers__usage="Multi-use") |
            Q(coupon_vouchers__vouchers__offers__in=excluded_offers)
        )
        .prefetch_related(
            Prefetch(
                "coupon_vouchers__vouchers",
            ),
            Prefetch(
                "coupon_vouchers__vouchers__offers",
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
        if dateutil_parser.isoparse(
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
        ),
        "updated_cart_discounts": "\n".join(
            cart_discount["name"]
            for cart_discount in summary_info["cart_discounts"]["updated"]
        ),
        "created_discount_codes": "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["created"]
        ),
        "updated_discount_codes": "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["updated"]
        ),
    }

    for key, value in success_summary.items():
        if value:
            humanized = " ".join(key.capitalize() for key in key.split("_"))

            logger.info(f"Summary of {humanized}:\n{value}\n")

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


def _migrate_coupons(client: CommercetoolsAPIClient):
    """
    Migrate coupons to Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """

    site_configuration = SiteConfiguration.objects.first()
    coupons = _get_non_multiuse_course_coupons()
    mapped_discounts = _map_coupons_to_ct_cart_discounts_and_discount_codes(
        coupons, site_configuration
    )

    existing_discounts_in_ct = client.get_ct_discounts_with_code()

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
                                f"Failed to update discount code with name: {discount_codes['name']} and code: {discount_codes['code']}."
                            )
                            summary_info["discount_codes"]["failed"].append(
                                {
                                    "name": discount_codes["name"],
                                    "code": discount_codes["code"],
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
            cart_discount_response = client.create_cart_discount(**cart_discount)

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

            logger.info(
                f"Cart discount created successfully with name: {cart_discount['name']}."
            )
            summary_info["cart_discounts"]["created"].append(cart_discount)

            for discount_code in discount_codes:
                _migrate_discount_code(discount_code, cart_discount_response["id"])

    _generate_summary(summary_info)

    logger.info("Coupons migrated to Commercetools successfully.")


class Command(BaseCommand):
    """Command to migrate program offers to Commercetools."""

    def handle(self, *args, **options):
        """Handle the command."""
        try:
            client = CommercetoolsAPIClient()
        except HTTPError as error:
            raise CommandError(
                f"Failed to initialize Commercetools client. Error: {error}"
            ) from error

        _migrate_coupons(client)
