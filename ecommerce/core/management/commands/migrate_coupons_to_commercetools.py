# pylint: disable=W1203

import logging
import re
from collections import deque
from typing import Deque, Dict, List, Optional, Tuple

from dateutil import parser as dateutil_parser
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Prefetch, Q
from django.utils import timezone
from oscar.core.loading import get_model
from requests.exceptions import HTTPError

from ecommerce.core.client import CommercetoolsAPIClient, PairedDiscount
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


def _get_highest_sort_order(client: CommercetoolsAPIClient, discount_type: str) -> float:
    """
    Get the highest sort order for cart discounts without discount codes.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.

    Returns:
        float: The highest sort order.
    """
    response = client.get_highest_sort_order_for_cart_discount(
        where=f'requiresDiscountCode=true and custom(fields(discountType="{discount_type}"))'
    )

    if not response:
        raise CommandError("Failed to get highest sort order. Exiting command.")

    if response["count"] > 0:
        return float(response["results"][0]["sortOrder"])

    return 0.00000001


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


def _map_coupons_to_ct_cart_discounts_and_discount_codes(
    coupons, summary_info
) -> List:
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
        vouchers = coupon.attr.coupon_vouchers.vouchers
        voucher = vouchers.first()
        offer = voucher.best_offer
        offer_range = offer.condition.range

        catalog_query = offer_range.catalog_query
        if not catalog_query or catalog_query.strip() in ("*", "key:(*)"):
            query_predicate = ""
        else:
            query_predicate = convert_querystring_to_predicate(catalog_query)

            if not query_predicate:
                log_message = f'Unable to convert catalog query to predicate. '
                log_message += f'Check if the KEY_TO_PREDICATE_DICT needs to be updated with the new key. '
                log_message += f'Skipping migration of coupon.'
                logger.error(log_message)

                summary_info["cart_discounts"]["failed"].append({
                    "name": f'Coupon: {coupon.title} with Catalog Query: {catalog_query}',
                    "reason": log_message,
                })
                continue

        name = (
            f"[Migrated - Multiuse Course Discount] - {coupon.title}"
            if voucher.usage == Voucher.MULTI_USE
            else f"[Migrated - Course Discount] - {coupon.title}"
        )

        cart_discount = {
            "name": name,
            "key": coupon.slug,
            "description": _get_note_for_coupon(coupon) or "",
            "customFields": {
                "client": _get_client_for_coupon(coupon),
                "category": _get_category_for_coupon(coupon),
                "discountType": "course-discount",
            },
            "cartPredicate": _map_voucher_criteria_to_cart_predicate(
                seat_types=offer_range.course_seat_types,
                email_domains=offer.email_domains,
                query_predicate=query_predicate,
            ),
            "value": _map_benefit_to_ct_value(offer.benefit),
        }

        cart_discount_for_program = None
        if voucher.usage == Voucher.MULTI_USE:
            cart_discount_for_program = {
                "name": f"[Migrated - Multiuse Program Discount] - {coupon.title}",
                "key": f"program-{coupon.slug}",
                "cartPredicate": _map_voucher_criteria_to_cart_predicate(
                    seat_types=offer_range.course_seat_types,
                    email_domains=offer.email_domains,
                    query_predicate=query_predicate,
                    for_program=True,
                ),
                "description": cart_discount["description"],
                "customFields": {
                    "client": cart_discount["customFields"]["client"],
                    "category": cart_discount["customFields"]["category"],
                    "discountType": "program-discount",
                },
                "value": cart_discount["value"],
            }

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

        results.append(
            (
                cart_discount,
                discount_codes,
                excluded_discount_codes,
                cart_discount_for_program,
            )
        )
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


def _get_category_for_coupon(coupon) -> Optional[str]:
    """
    Get the category for the coupon.
    """
    try:
        category = ProductCategory.objects.get(product=coupon).category.name
    except ProductCategory.DoesNotExist:
        category = None

    if not category:
        logger.info(f"Category not found for coupon {coupon.title}.")

    return category


def _get_course_coupons(partner_id):
    """
    Get course coupons from the database.
    """
    excluded_offers = ConditionalOffer.objects.filter(
        ~Q(partner_id=partner_id) |
        Q(benefit__type=Benefit.PERCENTAGE, benefit__value=100.00) |
        Q(condition__range__catalog_query__isnull=True)
    )

    coupons = (
        Product.objects.filter(
            product_class__slug="coupon",
            coupon_vouchers__vouchers__end_datetime__gte=timezone.now(),
        )
        .exclude(
            Q(slug__in=["edxwelcome", "welcome-code-new2edx-30-724"]) |
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
            discount_name
            for discount_name in summary_info["cart_discounts"]["created"]
        ),
        ("updated", "Cart Discount"): "\n".join(
            f"{discount_name} - Update actions: {update_actions}"
            for discount_name, update_actions in summary_info["cart_discounts"][
                "updated"
            ]
        ),
        ("created", "Discount Code"): "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["created"]
        ),
        ("updated", "Discount Code"): "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["updated"]
        ),
        ("deleted", "Discount Code"): "\n".join(
            f"{discount_code['code']} - {discount_code['name']}"
            for discount_code in summary_info["discount_codes"]["deleted"]
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
    sort_order: float,
    summary_info,
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

    sort_order += 0.00000001
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
    cart_discount_for_program: Dict,
    discount_codes: List[Dict],
    excluded_discount_codes: List[str],
    existing_discount_in_ct: PairedDiscount,
    existing_discount_in_ct_for_program: Optional[PairedDiscount],
    summary_info: Dict,
) -> None:
    cart_discount_in_ct, discount_codes_in_ct = existing_discount_in_ct
    cart_discount_ids = [cart_discount_in_ct["id"]]

    _update_existing_cart_discount(
        client=client,
        cart_discount=cart_discount,
        cart_discount_in_ct=cart_discount_in_ct,
        summary_info=summary_info,
    )

    if cart_discount_for_program and existing_discount_in_ct_for_program:
        cart_discount_in_ct_for_program = (
            existing_discount_in_ct_for_program.cart_discount
        )
        cart_discount_ids.append(cart_discount_in_ct_for_program["id"])

        _update_existing_cart_discount(
            client=client,
            cart_discount=cart_discount_for_program,
            cart_discount_in_ct=cart_discount_in_ct_for_program,
            summary_info=summary_info,
        )

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
                summary_info["discount_codes"]["updated"].append(discount_code)
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
            summary_info["discount_codes"]["deleted"].append(discount_code_in_ct)


def _migrate_coupons(client: CommercetoolsAPIClient):
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
    }

    site_configuration = SiteConfiguration.objects.first()
    coupons = _get_course_coupons(site_configuration.partner_id)
    mapped_discounts = _map_coupons_to_ct_cart_discounts_and_discount_codes(
        coupons, summary_info
    )

    existing_discounts_in_ct = client.get_ct_discounts_with_code()
    course_sort_order = _get_highest_sort_order(client, "course-discount")
    program_sort_order = _get_highest_sort_order(client, "program-discount")
    course_sort_order += 0.00000001
    program_sort_order += 0.00000000001

    if not existing_discounts_in_ct:
        raise CommandError(
            "Failed to get existing discounts from Commercetools. Exiting command."
        )

    for (
        cart_discount,
        discount_codes,
        excluded_discount_codes,
        cart_discount_for_program,
    ) in mapped_discounts:
        if cart_discount["key"] in existing_discounts_in_ct:
            _update_existing_discount(
                client=client,
                cart_discount=cart_discount,
                cart_discount_for_program=cart_discount_for_program,
                discount_codes=discount_codes,
                excluded_discount_codes=excluded_discount_codes,
                existing_discount_in_ct=existing_discounts_in_ct[
                    cart_discount["key"]
                ],
                existing_discount_in_ct_for_program=(
                    existing_discounts_in_ct[cart_discount_for_program["key"]]
                    if cart_discount_for_program
                    else None
                ),
                summary_info=summary_info,
            )
        else:
            if not discount_codes:
                # No need to create cart discount if there are no discount codes.
                continue

            cart_discount_ids = []

            cart_discount_id, course_sort_order = _create_cart_discount(
                client=client,
                cart_discount=cart_discount,
                sort_order=course_sort_order,
                summary_info=summary_info,
            )
            if cart_discount_id:
                cart_discount_ids.append(cart_discount_id)

            if cart_discount_for_program:
                cart_discount_id, program_sort_order = _create_cart_discount(
                    client=client,
                    cart_discount=cart_discount_for_program,
                    sort_order=program_sort_order,
                    summary_info=summary_info,
                    for_program=True,
                )
                if cart_discount_id:
                    cart_discount_ids.append(cart_discount_id)

            if not cart_discount_ids:
                continue

            for discount_code in discount_codes:
                _create_discount_code(
                    client=client,
                    cart_discount_ids=cart_discount_ids,
                    discount_code=discount_code,
                    summary_info=summary_info,
                )

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
