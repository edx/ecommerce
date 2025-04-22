# pylint: disable=W1203

import gc
import logging
import re
from collections import deque
from decimal import Decimal
from time import sleep
from typing import Deque, Dict, List, Optional, Tuple

from dateutil import parser as dateutil_parser
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch, Q
from django.utils import timezone
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient
from ecommerce.core.constants import COUPONS_DEFAULT_SORT_ORDER, CT_ABSOLUTE_DISCOUNT_TYPE, CT_PERCENTAGE_DISCOUNT_TYPE
from ecommerce.core.utils import (
    convert_querystring_to_predicate,
    get_category_for_coupon,
    get_next_sort_order_for_coupons
)
from ecommerce.invoice.models import Invoice

logger = logging.getLogger(__name__)

COOLDOWN_TIME = 5
COOLDOWN_LIMIT = 5000

Product = get_model("catalogue", "Product")
ProductCategory = get_model("catalogue", "ProductCategory")
Voucher = get_model("voucher", "Voucher")
CouponVouchers = get_model("voucher", "CouponVouchers")
Benefit = get_model("offer", "Benefit")
Condition = get_model("offer", "Condition")
ConditionalOffer = get_model("offer", "ConditionalOffer")
SiteConfiguration = get_model("core", "SiteConfiguration")


def _get_seat_type_and_course_predicate_from_range(
    *,
    offer_range,
    coupon_name: str,
    summary_info: Dict,
) -> Tuple:
    if offer_range.catalog:
        product = offer_range.catalog.stock_records.first().product
        seat_types = product.attr.certificate_type
        query_predicate = f'variant.key = "{product.course_id}"'
    else:
        seat_types = offer_range.course_seat_types
        catalog_query = offer_range.catalog_query
        if not catalog_query or catalog_query.strip().replace(" ", "") in (
            "*",
            "key:(*)",
            "org:(*)",
        ):
            query_predicate = ""
        else:
            query_predicate = convert_querystring_to_predicate(catalog_query)

            if not query_predicate:
                log_message = (
                    "Catalog Query unable to be converted. Check if the "
                    "KEY_TO_PREDICATE_DICT needs to be updated with the new key. "
                    "Skipping migration of coupon."
                )
                logger.error(log_message)

                summary_info["cart_discounts"]["failed"].append(
                    {
                        "name": f"Coupon: {coupon_name} with Catalog Query: {catalog_query}",
                        "reason": log_message,
                    }
                )
                return None, None

    return seat_types, query_predicate


def _get_cent_amount_from_value(value: Dict) -> Optional[int]:
    """
    Get cent amount from value.
    """
    return value.get("permyriad", value.get("money", [{}])[0].get("centAmount"))


def _map_benefit_to_ct_value(benefit) -> Dict:
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


def _map_voucher_to_ct_code_applications(
    voucher, max_global_applications: Optional[int]
) -> Dict:
    """
    Map Voucher usage to Commercetools code applications.
    """
    max_applications = (
        (max_global_applications) - voucher.num_orders
        if max_global_applications
        else None
    )

    return {
        "Single use": {
            "maxApplications": 1,
        },
        "Multi-use": {
            "maxApplications": max_applications,
        },
        "Once per customer": {
            "maxApplications": max_applications,
            "maxApplicationsPerCustomer": 1,
        },
    }[voucher.usage]


def _map_voucher_criteria_to_cart_predicate(
    *,
    seat_types: Optional[str],
    email_domains: Optional[str],
    query_predicate: str,
    for_program: bool = False,
) -> str:

    def _join_conditions(conditions: Deque[str]) -> str:
        return " and ".join(conditions)

    def _map_list_to_ct_predicate_condition(key: str, data: str) -> str:
        """
        Map a comma-separated list from database to commercetools predicate condition.
        """
        values = re.split(r"\s*,\s*", data)

        if len(values) == 1:
            return f'{key} = "{values[0]}"'

        values_string = ",".join(f'"{value}"' for value in values)

        return f"{key} in ({values_string})"

    cart_conditions = deque()
    lineItemConditions = deque()

    if seat_types:
        lineItemConditions.append(
            _map_list_to_ct_predicate_condition("attributes.mode", seat_types)
        )

    if query_predicate:
        lineItemConditions.append(
            query_predicate.replace("product.key", "attributes.`course-key`")
            if for_program
            else query_predicate
        )

    if email_domains:
        cart_conditions.append(
            _map_list_to_ct_predicate_condition("custom.emailDomain", email_domains)
        )

    if for_program:
        lineItemConditions.appendleft("custom.bundleId is defined")
        cart_conditions.appendleft(
            f"forAllLineItems({_join_conditions(lineItemConditions)}) = true"
        )
    else:
        lineItemConditions.extendleft(
            [
                "custom.bundleId is not defined",
                "quantity = 1",
            ]
        )
        cart_conditions.appendleft(
            f"lineItemCount({_join_conditions(lineItemConditions)}) = 1"
        )

    cart_predicate = _join_conditions(cart_conditions)

    return cart_predicate


def _map_coupon_to_ct_cart_discounts_and_discount_codes(
    coupon, summary_info: Dict
) -> Optional[Tuple]:
    """
    Map coupon to Commercetools cart discounts and discount codes.
    """
    try:
        if coupon.attr.inactive:
            logger.info(f"Skipping coupon {coupon.title} as it is inactive")
            return None
    except AttributeError:
        ...

    vouchers = coupon.attr.coupon_vouchers.vouchers
    voucher = vouchers.first()
    offer = voucher.best_offer
    offer_benefit = offer.benefit

    seat_types, query_predicate = _get_seat_type_and_course_predicate_from_range(
        offer_range=offer.condition.range,
        coupon_name=coupon.title,
        summary_info=summary_info,
    )

    if seat_types is None and query_predicate is None:
        return None

    if offer_benefit.type == Benefit.PERCENTAGE and offer_benefit.value == 100:
        discount_type = "enrollment-code"
        name = "Enrollment Code"
        program_name = "Program Enrollment Code"
    else:
        discount_type = "course-discount"
        name = "Course Discount"
        program_name = "Program Discount"

    if voucher.usage == Voucher.MULTI_USE:
        name = f"Multiuse {name}"

    ct_category, channel = get_category_for_coupon(
        coupon, ProductCategory, summary_info
    )

    cart_discount = {
        "name": f"[Migrated - {name}] - {coupon.title}",
        "key": coupon.slug,
        "description": _get_note_for_coupon(coupon) or "",
        "customFields": {
            "client": _get_client_for_coupon(coupon),
            "category": ct_category,
            "channel": channel,
            "discountType": discount_type,
        },
        "cartPredicate": _map_voucher_criteria_to_cart_predicate(
            seat_types=seat_types,
            email_domains=offer.email_domains,
            query_predicate=query_predicate,
        ),
        "value": _map_benefit_to_ct_value(offer_benefit),
    }

    cart_discount_for_program = None
    is_applicable_for_program = False
    if voucher.usage == Voucher.MULTI_USE:
        cart_discount_for_program = {
            "name": f"[Migrated - {program_name}] - {coupon.title}",
            "key": f"program-{coupon.slug}",
            "cartPredicate": _map_voucher_criteria_to_cart_predicate(
                seat_types=seat_types,
                email_domains=offer.email_domains,
                query_predicate=query_predicate,
                for_program=True,
            ),
            "description": cart_discount["description"],
            "customFields": cart_discount["customFields"],
            "value": cart_discount["value"],
        }
        is_applicable_for_program = offer_benefit.max_affected_items == 0

    discount_codes = [
        {
            "name": voucher.name,
            "key": voucher.code,
            "code": voucher.code,
            "validFrom": voucher.start_datetime.isoformat(),
            "validUntil": voucher.end_datetime.isoformat(),
            **_map_voucher_to_ct_code_applications(
                voucher, offer.max_global_applications
            ),
        }
        for voucher in vouchers.all()
        if not (voucher.usage == "Single use" and voucher.num_orders == 1)
    ]

    excluded_discount_codes = [
        voucher.code
        for voucher in vouchers.all()
        if voucher.usage == "Single use" and voucher.num_orders == 1
    ]

    return (
        cart_discount,
        discount_codes,
        excluded_discount_codes,
        cart_discount_for_program,
        is_applicable_for_program,
    )


def _map_enrollment_offer_to_ct_cart_discounts_and_discount_codes(
    offer,
) -> Tuple:
    """
    Map enrollment offer to Commercetools cart discounts and discount codes.
    """
    vouchers = offer.vouchers.all()
    product = offer.benefit.range.included_products.first()
    seat_type = product.attr.certificate_type
    course_id = product.course_id

    cart_discount = {
        "name": f"[Migrated - Enrollment Code] - Enrollment code for {product.title}",
        "key": f"enrollment-code-for-offer-{offer.id}",
        "description": f"Enrollment code for {course_id}",
        "customFields": {
            "discountType": "enrollment-code",
        },
        "cartPredicate": _map_voucher_criteria_to_cart_predicate(
            seat_types=seat_type,
            email_domains=offer.email_domains,  # always None
            query_predicate=f'variant.key = "{course_id}"',
        ),
        "value": _map_benefit_to_ct_value(offer.benefit),
    }

    discount_codes = [
        {
            "name": voucher.name,
            "key": voucher.code,
            "code": voucher.code,
            "validFrom": voucher.start_datetime.isoformat(),
            "validUntil": voucher.end_datetime.isoformat(),
            **_map_voucher_to_ct_code_applications(
                voucher, offer.max_global_applications  # always None
            ),
        }
        for voucher in vouchers
        if not (voucher.usage == "Single use" and voucher.num_orders == 1)
    ]

    excluded_discount_codes = [
        voucher.code
        for voucher in vouchers
        if voucher.usage == "Single use" and voucher.num_orders == 1
    ]

    return (
        cart_discount,
        discount_codes,
        excluded_discount_codes,
        None,
        False,
    )


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
        logger.info(f"Client not found for coupon {coupon.title}.")

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


def _get_course_coupons(partner_id: str, to_migrate: List[str]):
    """
    Get course coupons from the database.
    """
    if "enrollment" in to_migrate and "non-enrollment" in to_migrate:
        excluded_offers = ConditionalOffer.objects.filter(
            ~Q(partner_id=partner_id) |
            Q(
                condition__range__catalog_query__isnull=True,
                condition__range__catalog__isnull=True,
            )
        )
    elif "non-enrollment" in to_migrate:
        excluded_offers = ConditionalOffer.objects.filter(
            ~Q(partner_id=partner_id) |
            Q(
                condition__range__catalog_query__isnull=True,
                condition__range__catalog__isnull=True,
            ) |
            Q(benefit__type=Benefit.PERCENTAGE, benefit__value=100.00)
        )
    elif "enrollment" in to_migrate:
        excluded_offers = ConditionalOffer.objects.filter(
            ~Q(partner_id=partner_id) |
            Q(
                condition__range__catalog_query__isnull=True,
                condition__range__catalog__isnull=True,
            ) |
            ~Q(benefit__type=Benefit.PERCENTAGE, benefit__value=100.00)
        )

    coupons = (
        Product.objects.filter(
            product_class__slug="coupon",
            coupon_vouchers__vouchers__end_datetime__gte=timezone.now(),
        )
        .exclude(
            Q(slug__in=[
                "edxwelcome",
                "welcome-code-new2edx-30-724",
                "2025-springfall-promo-refresh"
            ]) | Q(coupon_vouchers__vouchers__offers__in=excluded_offers)
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


def _get_enrollment_code_offers():
    """
    Get enrollment code offers from the database
    """
    offers = (
        ConditionalOffer.objects.filter(
            vouchers__end_datetime__gte=timezone.now(),
            benefit__type=Benefit.PERCENTAGE,
            benefit__value=100.00,
            benefit__range__included_products__isnull=False,
        )
        .prefetch_related(
            "vouchers",
            "condition",
            "benefit",
            "benefit__range",
            "benefit__range__included_products",
        )
        .distinct()
    )

    return offers


def _make_update_actions_by_comparing_cart_discounts(
    *,
    discount_in_ecommerce: Dict,
    discount_in_ct: Dict,
) -> List[Dict]:
    """
    Create update actions after comparing discounts in ecommerce and commercetools.

    Returns:
        List: List of update actions.
    """

    def _make_update_action_for_key(key: str, value: str):
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
    discount_in_ecommerce: Dict,
    discount_in_ct: Dict,
) -> List[Dict]:
    """
    Create update actions after comparing discounts in ecommerce and commercetools.

    Returns:
        List: List of update actions.
    """

    def _make_update_action_for_key(key, value) -> Dict:
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


def _generate_summary(summary_info: Dict) -> None:
    """
    Generate summary of migration.
    """

    success_summary = {
        ("created", "Cart Discount"): "\n".join(
            summary_info["cart_discounts"]["created"]
        ),
        ("updated", "Cart Discount"): "\n".join(
            f"{name} - Update actions: {update_actions}"
            for name, update_actions in summary_info["cart_discounts"]["updated"]
        ),
        ("created", "Discount Code"): "\n".join(
            summary_info["discount_codes"]["created"]
        ),
        ("updated", "Discount Code"): "\n".join(
            f"{name} - Update actions: {update_actions}"
            for name, update_actions in summary_info["discount_codes"]["updated"]
        ),
        ("deleted", "Discount Code"): "\n".join(
            summary_info["discount_codes"]["deleted"]
        ),
    }

    for key, value in success_summary.items():
        action, discount_type = key

        if value:
            logger.info(f"\nSummary of {action} {discount_type}:\n{value}\n")
        else:
            logger.info(f"No {discount_type} were {action}.")

    if (
        summary_info["cart_discounts"]["failed"] or
        summary_info["discount_codes"]["failed"]
    ):
        if summary_info["cart_discounts"]["failed"]:
            logger.error(
                "Summary of failed cart discount migrations: %s",
                ", ".join(
                    f"\n{discount['name']} (Reason: {discount['reason']})"
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


def _create_cart_discount(
    *,
    client: CommercetoolsAPIClient,
    cart_discount: Dict,
    sort_order: Decimal,
    summary_info: Dict,
    for_program: bool = False,
) -> Tuple:
    target = (
        {"type": "lineItems", "predicate": "1=1"}
        if for_program
        else {"type": "totalPrice"}
    )

    cart_discount_response = client.create_cart_discount(
        sortOrder=sort_order, target=target, **cart_discount
    )

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
        return None, sort_order

    sort_order += COUPONS_DEFAULT_SORT_ORDER
    logger.info(
        f"Cart discount created successfully with name: {cart_discount['name']}."
    )
    summary_info["cart_discounts"]["created"].append(cart_discount["name"])
    return cart_discount_response["id"], sort_order


def _create_discount_code(
    *,
    client: CommercetoolsAPIClient,
    cart_discount_ids: List[str],
    discount_code: Dict,
    summary_info: Dict,
) -> None:
    discount_code_response = client.create_discount_code(
        cartDiscountIds=cart_discount_ids, **discount_code
    )
    if (
        summary_info["discount_codes"]["created"] and
        len(summary_info["discount_codes"]["created"]) % COOLDOWN_LIMIT == 0
    ):
        logger.info("Cooling down for 5 seconds...")
        sleep(COOLDOWN_TIME)

    if discount_code_response:
        logger.info(
            f"Discount code created successfully with name: {discount_code['name']} and code: {discount_code['code']}."
        )
        summary_info["discount_codes"]["created"].append(
            f"{discount_code['code']} - {discount_code['name']}"
        )
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


def _update_existing_cart_discount(
    *,
    client: CommercetoolsAPIClient,
    cart_discount: Dict,
    cart_discount_in_ct: Dict,
    summary_info: Dict,
) -> None:
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
            return

        summary_update_actions = ", ".join(
            update_action["action"]
            for update_action in update_actions_for_cart_discount
        )

        summary_info["cart_discounts"]["updated"].append(
            (cart_discount["name"], summary_update_actions)
        )


def _update_existing_discount(
    *,
    client: CommercetoolsAPIClient,
    cart_discount: Dict,
    cart_discount_in_ct: Dict,
    cart_discount_for_program: Dict,
    cart_discount_in_ct_for_program: Optional[Dict],
    discount_codes: List[Dict],
    discount_codes_in_ct: Dict,
    excluded_discount_codes: List[str],
    is_applicable_for_program: bool,
    sort_order: Decimal,
    summary_info: Dict,
) -> Decimal:
    cart_discount_ids = [cart_discount_in_ct["id"]]

    _update_existing_cart_discount(
        client=client,
        cart_discount=cart_discount,
        cart_discount_in_ct=cart_discount_in_ct,
        summary_info=summary_info,
    )

    if cart_discount_in_ct_for_program:
        _update_existing_cart_discount(
            client=client,
            cart_discount=cart_discount_for_program,
            cart_discount_in_ct=cart_discount_in_ct_for_program,
            summary_info=summary_info,
        )
        if is_applicable_for_program:
            cart_discount_ids.append(cart_discount_in_ct_for_program["id"])
    elif is_applicable_for_program:
        cart_discount_id, sort_order = _create_cart_discount(
            client=client,
            cart_discount=cart_discount_for_program,
            sort_order=sort_order,
            summary_info=summary_info,
            for_program=True,
        )
        if cart_discount_id:
            cart_discount_ids.append(cart_discount_id)

    for discount_code in discount_codes:
        discount_code_in_ct = discount_codes_in_ct.get(discount_code["key"])
        if discount_code_in_ct:
            update_actions_for_discount_code = (
                _make_update_actions_by_comparing_discount_codes(
                    discount_in_ecommerce=discount_code,
                    discount_in_ct=discount_code_in_ct,
                )
            )

            # Attach or detach program cart discount from discount code
            if set(cart_discount_ids) != set(discount_code_in_ct["cartDiscountIds"]):
                update_actions_for_discount_code.append(
                    {
                        "action": "changeCartDiscounts",
                        "cartDiscounts": [
                            {"typeId": "cart-discount", "id": cart_discount_id}
                            for cart_discount_id in cart_discount_ids
                        ],
                    }
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
                        "Failed to update discount code with name: "
                        f"{discount_code['name']} and "
                        f"code: {discount_code['code']}."
                    )
                    summary_info["discount_codes"]["failed"].append(
                        {
                            "name": discount_code["name"],
                            "code": discount_code["code"],
                            "reason": "Error while updating discount code.",
                        }
                    )
                    continue

                summary_update_actions = ", ".join(
                    update_action["action"]
                    for update_action in update_actions_for_discount_code
                )

                summary_info["discount_codes"]["updated"].append(
                    (
                        f"{discount_code['code']} - {discount_code['name']}",
                        summary_update_actions,
                    )
                )
        else:
            _create_discount_code(
                client=client,
                cart_discount_ids=cart_discount_ids,
                discount_code=discount_code,
                summary_info=summary_info,
            )

    for discount_code_key in excluded_discount_codes:
        discount_code_in_ct = discount_codes_in_ct.get(discount_code_key)

        if discount_code_in_ct:
            discount_code_response = client.delete_discount_code_by_key(
                discount_code_key, discount_code_in_ct["version"]
            )

            if not discount_code_response:
                logger.error(
                    f"Failed to delete discount code with code: {discount_code_key}."
                )
                summary_info["discount_codes"]["failed"].append(
                    {
                        "name": discount_code_in_ct["name"],
                        "code": discount_code_in_ct["code"],
                        "reason": "Error while deleting discount code.",
                    }
                )
                continue
            summary_info["discount_codes"]["deleted"].append(
                f"{discount_code_in_ct['code']} - {discount_code_in_ct['name']}"
            )

    return sort_order


def _has_valid_orgs_in_cart_predicate(
    *,
    name: str,
    cart_predicate: str,
    client: CommercetoolsAPIClient,
    summary_info: Dict,
) -> bool:
    match_orgs = re.search(
        r"attributes\.`brand-text`\s+(not\s+)?in\s+\(([^)]+)\)",
        cart_predicate,
    )
    if match_orgs:
        orgs = re.findall(r'"(.*?)"', match_orgs.groups()[-1])
        for org in orgs:
            if org not in summary_info["orgs"]:
                is_valid_org = client.has_product_for_org(org)
                if is_valid_org is None:
                    log_message = f"Failed to check if org {org} exists."
                    logger.error(log_message)
                    summary_info["cart_discounts"]["failed"].append(
                        {
                            "name": name,
                            "reason": log_message,
                        }
                    )
                    continue

                summary_info["orgs"].add(org)

                if not is_valid_org:
                    log_message = f"Org {org} does not exist in Commercetools."
                    logger.error(log_message)
                    summary_info["cart_discounts"]["failed"].append(
                        {
                            "name": name,
                            "reason": log_message,
                        }
                    )
                    return False
    return True


def _migrate_single_coupon_or_offer(
    *,
    client: CommercetoolsAPIClient,
    data: Tuple,
    sort_order: Decimal,
    summary_info: Dict,
) -> Decimal:
    (
        cart_discount,
        discount_codes,
        excluded_discount_codes,
        cart_discount_for_program,
        is_applicable_for_program,
    ) = data
    if not _has_valid_orgs_in_cart_predicate(
        name=cart_discount["name"],
        cart_predicate=cart_discount["cartPredicate"],
        client=client,
        summary_info=summary_info,
    ):
        return sort_order

    cart_discount_in_ct = client.get_cart_discount_by_key(key=cart_discount["key"])
    if cart_discount_in_ct is None:
        logger.error(f"Failed to get cart discount of {cart_discount['name']}.")
        summary_info["cart_discounts"]["failed"].append(
            {
                "name": cart_discount["name"],
                "reason": "Error while getting cart discount.",
            }
        )
        return sort_order
    if cart_discount_in_ct.get("status") == 404:
        if not discount_codes:
            # No need to create cart discount if there are no discount codes.
            return sort_order

        cart_discount_ids = []

        cart_discount_id, sort_order = _create_cart_discount(
            client=client,
            cart_discount=cart_discount,
            sort_order=sort_order,
            summary_info=summary_info,
        )
        if cart_discount_id:
            cart_discount_ids.append(cart_discount_id)

            # only create cart discount for program if
            # - course cart discount is created without error
            # - discount is applicable for program
            if is_applicable_for_program:
                cart_discount_id, sort_order = _create_cart_discount(
                    client=client,
                    cart_discount=cart_discount_for_program,
                    sort_order=sort_order,
                    summary_info=summary_info,
                    for_program=True,
                )
                if cart_discount_id:
                    cart_discount_ids.append(cart_discount_id)

        if not cart_discount_ids:
            return sort_order

        for discount_code in discount_codes:
            _create_discount_code(
                client=client,
                cart_discount_ids=cart_discount_ids,
                discount_code=discount_code,
                summary_info=summary_info,
            )
    else:
        discount_codes_in_ct = client.get_discount_codes_for_cart_discount(
            cart_discount_name=cart_discount["name"],
            cart_discount_id=cart_discount_in_ct["id"],
        )

        if discount_codes_in_ct is None:
            logger.error(
                f"Failed to get discount codes for cart discount: {cart_discount['name']}."
            )
            summary_info["cart_discounts"]["failed"].append(
                {
                    "name": cart_discount["name"],
                    "reason": "Error while getting discount codes.",
                }
            )
            return sort_order

        if cart_discount_for_program:
            cart_discount_in_ct_for_program = client.get_cart_discount_by_key(
                key=cart_discount_for_program["key"]
            )
            if cart_discount_in_ct_for_program is None:
                logger.error(
                    f"Failed to get cart discount of {cart_discount_for_program['name']}."
                )
                summary_info["cart_discounts"]["failed"].append(
                    {
                        "name": cart_discount_for_program["name"],
                        "reason": "Error while getting cart discount.",
                    }
                )
                return sort_order

            if cart_discount_in_ct_for_program.get("status") == 404:
                cart_discount_in_ct_for_program = None
        else:
            cart_discount_in_ct_for_program = None

        sort_order = _update_existing_discount(
            client=client,
            cart_discount=cart_discount,
            cart_discount_in_ct=cart_discount_in_ct,
            cart_discount_for_program=cart_discount_for_program,
            cart_discount_in_ct_for_program=cart_discount_in_ct_for_program,
            discount_codes=discount_codes,
            discount_codes_in_ct=discount_codes_in_ct,
            excluded_discount_codes=excluded_discount_codes,
            is_applicable_for_program=is_applicable_for_program,
            sort_order=sort_order,
            summary_info=summary_info,
        )

    return sort_order


def _migrate_coupons(client: CommercetoolsAPIClient, to_migrate: List[str]) -> None:
    """
    Migrate coupons to Commercetools.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.
    """
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
            "deleted": [],
        },
        "orgs": set(),
    }

    site_configuration = SiteConfiguration.objects.first()
    sort_order = get_next_sort_order_for_coupons(client)

    coupons = _get_course_coupons(site_configuration.partner_id, to_migrate)

    for coupon in coupons:
        data = _map_coupon_to_ct_cart_discounts_and_discount_codes(
            coupon, summary_info
        )
        if data:
            sort_order = _migrate_single_coupon_or_offer(
                client=client,
                data=data,
                sort_order=sort_order,
                summary_info=summary_info,
            )

    del coupons
    gc.collect()

    if "enrollment" in to_migrate:
        offers = _get_enrollment_code_offers()
        for offer in offers:
            data = _map_enrollment_offer_to_ct_cart_discounts_and_discount_codes(
                offer
            )
            sort_order = _migrate_single_coupon_or_offer(
                client=client,
                data=data,
                sort_order=sort_order,
                summary_info=summary_info,
            )

    _generate_summary(summary_info)

    logger.info("Coupons migrated to Commercetools successfully.")


class Command(BaseCommand):
    """Command to migrate course coupons to Commercetools."""

    def add_arguments(self, parser):
        parser.add_argument(
            "--only", type=str, help="Specify which type of coupons to migrate"
        )

    def handle(self, *args, **options):
        """Handle the command."""
        try:
            client = CommercetoolsAPIClient()
        except HTTPError as error:
            raise CommandError(
                f"Failed to initialize Commercetools client. Error: {error}"
            ) from error

        migrate_only = options.get("only")
        if migrate_only == "non-enrollment":
            to_migrate = ["non-enrollment"]
        elif migrate_only == "enrollment":
            to_migrate = ["enrollment"]
        else:
            to_migrate = ["non-enrollment", "enrollment"]

        _migrate_coupons(client, to_migrate=to_migrate)
