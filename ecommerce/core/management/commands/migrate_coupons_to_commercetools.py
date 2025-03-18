import logging
import re
from enum import Enum
from typing import Optional

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q, Prefetch
from django.utils import timezone
from ecommerce.invoice.models import Invoice
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient
from ecommerce.core.constants import (
    BUNDLE_CART_DISCOUNT_KEY_FORMAT,
    CT_ABSOLUTE_DISCOUNT_TYPE,
    CT_PERCENTAGE_DISCOUNT_TYPE,
    PROGRAM_OFFER_KEY,
    PROGRAM_OFFER_NAME,
    TEN_PERCENT_DISCOUNT_IN_CENTS,
)
from ecommerce.programs.utils import get_all_program_uuids

logger = logging.getLogger(__name__)


Product = get_model("catalogue", "Product")
ProductCategory = get_model("catalogue", "ProductCategory")
Voucher = get_model("voucher", "Voucher")
CouponVouchers = get_model("voucher", "CouponVouchers")
Benefit = get_model("offer", "Benefit")
Condition = get_model("offer", "Condition")
ConditionalOffer = get_model("offer", "ConditionalOffer")
SiteConfiguration = get_model("core", "SiteConfiguration")


def _map_benefit_to_ct_value(benefit):
    """
    Map Benefit to Commercetools discount value.
    """
    return {
        "type": {
            Benefit.FIXED: CT_ABSOLUTE_DISCOUNT_TYPE,
            Benefit.PERCENTAGE: CT_PERCENTAGE_DISCOUNT_TYPE,
        }.get(benefit.type),
        "permyriad": int(benefit.value * 100),
    }


def _map_voucher_usage_to_ct_code_applications(usage):
    """
    Map Voucher usage to Commercetools code applications.
    """
    return {
        "Single use": {
            "maxApplications": 1,
        },
        "Multi-use": {
            # TODO: Verify where to get maxApplications from if they are set via form
        },
        "Once per customer": {
            # TODO: Verify where to get maxApplications from if they are set via form
            "maxApplicationsPerCustomer": 1,
        },
    }[usage]


def _create_cart_predicate(*, seat_type, email_domain, catalog_query):
    # Implement Later
    print("kwargs", seat_type, email_domain, catalog_query)
    return "1=1"


def _get_client_for_coupon(coupon) -> Optional[str]:
    """
    Get the client for the coupon.
    """
    try:
        client = Invoice.objects.get(
            order__lines__product=coupon
        ).business_client.name
    except Exception:
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
    coupons = Product.objects.filter(
        product_class__slug="coupon",
    )
    results = []

    for coupon in coupons:
        # TODO exclude various types of coupons
        try:
            if coupon.attr.inactive:
                logger.info(f"Skipping coupon {coupon.title} as it is inactive")
                continue
        except AttributeError:
            ...

        coupon_vouchers = CouponVouchers.objects.get(coupon=coupon)
        voucher = coupon_vouchers.vouchers.first()
        offer = voucher.best_offer
        offer_range = offer.condition.range

        cart_discount = {
            "name": coupon.title,
            "key": coupon.slug,
            "description": _get_note_for_coupon(coupon),
            "custom": {
                "client": _get_client_for_coupon(coupon),
                "category": _get_category_for_coupon(coupon),
                "discountType": "Single Course",
            },
            "cartPredicate": _create_cart_predicate(
                seat_type=offer_range.course_seat_types,
                email_domain=offer.email_domains,
                catalog_query=offer_range.catalog_query,
            ),
            # TODO: fix this
            "sortOrder": 0.000001,
            "value": _map_benefit_to_ct_value(offer.benefit),
        }

        discount_codes = [
            {
                "name": voucher.name,
                "description": f"Code for {cart_discount['name']}",
                "key": voucher.code,
                "code": voucher.code,
                "validFrom": voucher.start_datetime,
                "validUntil": voucher.end_datetime,
                **_map_voucher_usage_to_ct_code_applications(voucher.usage),
            }
            for voucher in coupon_vouchers.vouchers.all()
        ]

        results.append((cart_discount, discount_codes))
    return results


def _migrate_coupons(client: CommercetoolsAPIClient):
    """
    Migrate coupons to Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """

    coupons = _get_non_multiuse_course_coupons()
    existing_cart_discounts_in_ct = client.get_ct_discounts_with_code()

    created_cart_discounts = []
    failed_cart_discounts = []
    updated_cart_discounts = []
    created_discount_codes = []
    failed_discount_codes = []
    updated_discount_codes = []

    for cart_discount, discount_codes in coupons:
        # Fix this logic as we don't have a unique key for each coupon,
        # maybe set condition_id as key
        if existing_cart_discounts_in_ct and existing_cart_discounts_in_ct.get(
            cart_discount["key"]
        ):
            logger.info(
                f"Discount {cart_discount['key']} already exists in Commercetools. Skipping migration.",
            )

            # TODO: update values if needed change
            continue

        cart_discount_response = client.create_cart_discount(**cart_discount)

        if not cart_discount_response:
            logger.error(
                f"Failed to create cart discount with name: {cart_discount['name']}."
            )
            failed_cart_discounts.append(
                {
                    "name": cart_discount["name"],
                    "reason": "Error while creating cart discount.",
                }
            )
            continue

        logger.info(
            f"Cart discount created successfully with name: {cart_discount['name']}."
        )
        created_cart_discounts.append(cart_discount)

        for discount_code in discount_codes:
            discount_code_response = client.create_discount_code(
                cartDiscountId=cart_discount_response.get("id"), **discount_code
            )

            if not discount_code_response:
                logger.error(
                    f"Failed to create discount code with name: {discount_code['name']} and code: {discount_code['code']}."
                )
                failed_discount_codes.append(
                    {
                        "name": discount_code["name"],
                        "code": discount_code["code"],
                        "reason": "Error while creating discount code.",
                    }
                )
                continue

            logger.info(
                f"Discount code created successfully with name: {discount_code['name']} and code: {discount_code['code']}."
            )
            created_discount_codes.append(discount_code)

    # if created_discounts:
    created_cart_discounts_summary = ", ".join(
        cart_discount["name"] for cart_discount in created_cart_discounts
    )
    logger.info(
        "Summary of created cart discounts: %s", created_cart_discounts_summary
    )
    created_discount_codes_summary = ", ".join(
        f"{discount_code['code']} - {discount_code['name']}"
        for discount_code in created_discount_codes
    )
    logger.info(
        "Summary of created discount codes: %s", created_discount_codes_summary
    )

    if failed_cart_discounts:
        failed_summary = ", ".join(
            f"{discount['name']} (Reason: {discount['reason']})"
            for discount in failed_cart_discounts
        )
        logger.error(
            "Summary of failed cart discount migrations: %s", failed_summary
        )
        raise CommandError("Command run completed with errors.")
    if failed_discount_codes:
        failed_summary = ", ".join(
            f"{discount['code']} - {discount['name']} (Reason: {discount['reason']})"
            for discount in failed_discount_codes
        )
        logger.error(
            "Summary of failed discount code migrations: %s", failed_summary
        )
        raise CommandError("Command run completed with errors.")

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
