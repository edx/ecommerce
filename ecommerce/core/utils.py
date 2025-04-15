import logging
import re
from decimal import Decimal
from typing import Optional, Tuple
from urllib.parse import parse_qs, urlparse

import waffle
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import CommandError
from edx_django_utils.cache import get_cache_key as get_django_cache_key

from ecommerce.core.constants import (
    COUPONS_DEFAULT_SORT_ORDER,
    DEFAULT_PRODUCT_CATEGORY,
    KEY_TO_PREDICATE_DICT,
    LEGACY_CATEGORY_TO_CHANNEL_MAPPING,
    LEGACY_CATEGORY_TO_CT_CATEGORY_MAPPING
)

logger = logging.getLogger(__name__)


def log_message_and_raise_validation_error(message):
    """
    Logs provided message and raises a ValidationError with the same message.

    Args:
        message (str): Message to be logged and handled by the ValidationError.

    Raises:
        ValidationError: Raise with message provided by developer.
    """
    logger.error(message)
    raise ValidationError(message)


def get_cache_key(**kwargs):
    """
    Wrapper method on edx_django_utils get_cache_key utility.
    """
    return get_django_cache_key(**kwargs)


def deprecated_traverse_pagination(response, client, api_url):
    """
    Traverse a paginated API response.

    Note: This method should be deprecated since it defeats the purpose
    of pagination.

    Extracts and concatenates "results" (list of dict) returned by DRF-powered
    APIs.

    Arguments:
        response (Dict): Current response dict from service API
        client (requests.Session): OAuthAPIClient object from edx-rest-api-client
        api_url (str): API endpoint URL

    Returns:
        list of dict.

    """
    results = response.get('results', [])

    next_page = response.get('next')
    while next_page:
        if waffle.switch_is_active("debug_logging_for_deprecated_traverse_pagination"):  # pragma: no cover
            logger.info("deprecated_traverse_pagination method is called for endpoint %s", api_url)
        querystring = parse_qs(urlparse(next_page).query, keep_blank_values=True)
        response = client.get(api_url, params=querystring)
        response.raise_for_status()
        response = response.json()
        results += response.get('results', [])
        next_page = response.get('next')

    return results


def use_read_replica_if_available(queryset):
    """
    If there is a database called 'read_replica', use that database for the queryset.
    """
    return queryset.using("read_replica") if "read_replica" in settings.DATABASES else queryset


def _process_org_values(input_string):
    """
    Processes organization values from the input string and generates a SQL-like predicate.

    This function identifies and processes organization values following the 'org:' keyword.
    It handles both positive and negative organization values, supporting multiple formats:
    - Parentheses with AND/OR operators (e.g., org:(A OR B AND -C))
    - Quoted strings (e.g., org:"A")
    - Plain values (e.g., org:A)

    Negative organization values (preceded by '-') are processed using the `not in` clause, while
    positive values are processed using the `in` clause.

    Args:
        input_string (str): Input query string containing organization values.

    Returns:
        str: A formatted SQL-like predicate string:
            - For negative values: 'attributes.`brand-text` not in ("org1", "org2", ...)'
            - For positive values: 'attributes.`brand-text` in ("org1", "org2", ...)'
            - If no matching orgs are found: "No org values found"

    Examples:
        >>> _process_org_values('org:(-MITx OR HarvardX)')
        'attributes.`brand-text` not in ("MITx")'

        >>> _process_org_values('org:(HarvardX AND MITx)')
        'attributes.`brand-text` in ("HarvardX","MITx")'

    Notes:
        - Supports both positive and negative org values.
        - Handles logical operators (AND, OR) case-insensitively.
        - Removes duplicate values in the output.
        - If no org values are found, returns "No org values found".
    """
    # Updated regex to capture org values without empty groups
    pattern = r'org:\s*(?:\(([^)]+)\)|"([^"]+)"|([\w-]+))'

    # Extract org values from input
    matches = re.findall(pattern, input_string)

    if not matches:
        logger.info('No valid org values found in input: %s', input_string)
        return ""

    negative_orgs = []
    positive_orgs = []
    for match in matches:
        # Get the first non-empty value from the match tuple
        combined_match = ""
        for m in match:
            if m:  # If the value is not empty, assign it and break
                combined_match = m
                break
        # Split values on AND/OR (case-insensitive)
        values = re.split(r'\s+(?:AND|OR)\s+', combined_match, flags=re.IGNORECASE)

        for value in values:
            value = value.strip()
            if value.startswith('-'):
                negative_orgs.append(value[1:])  # Remove the negative sign
            else:
                positive_orgs.append(value)

    if negative_orgs:
        # Handle negative orgs by using 'not in'
        negative_orgs_str = ",".join(sorted(set(f'"{org}"' for org in negative_orgs)))
        return f'attributes.`brand-text` not in ({negative_orgs_str})'

    # If no negative orgs, process positive orgs
    positive_orgs_str = ",".join(sorted(set(f'"{org}"' for org in positive_orgs)))
    return f'attributes.`brand-text` in ({positive_orgs_str})'


def _detect_string_type(input_string):
    """
    Detects the type of a given input string based on specific prefixes.

    This function identifies whether the input string corresponds to one of the following types:
    - "org" for organization-related strings (e.g., 'org:MITx')
    - "key" for key-related strings (e.g., 'key:("course1" OR "course2")')
    - "number" for number-related strings (e.g., 'number:12345')
    - "start" for date range or start-related strings (e.g., 'start:[2023-08-01 TO 2061-12-31]')

    If the string does not match any of these patterns, the function returns "unknown".

    Args:
        input_string (str): The input query string to analyze.

    Returns:
        str: One of the following values:
            - "org" if the input string is organization-related.
            - "key" if the input string is key-related.
            - "number" if the input string is number-related.
            - "start" if the input string is start-related (e.g., a date range).
            - "unknown" if no known type is detected.

    Examples:
        >>> detect_string_type('org:(MITx OR HarvardX)')
        'org'

        >>> detect_string_type('key:("course1" OR "course2")')
        'key'

        >>> detect_string_type('number:12345')
        'number'

        >>> detect_string_type('start:[2023-08-01 TO 2061-12-31]')
        'start'

        >>> detect_string_type('random:unknown_value')
        'unknown'

    Notes:
        - The function is case-insensitive when matching prefixes (e.g., 'ORG:' is valid).
        - It supports both quoted and unquoted values as well as parentheses for multiple values.
    """
    input_string = input_string.strip()

    # Check if it's an org
    if re.match(r'^org:\s*(\"?.+?\"?|\(.+?\))$', input_string, re.IGNORECASE):
        return "org"
    # Check if it's a key
    if re.match(r'^key:\s*(\"?.+?\"?|\(.+?\))$', input_string, re.IGNORECASE):
        return "key"
    # Check if it's a number
    if re.match(r'^number:\s*(\"?.+?\"?|\(.+?\))$', input_string, re.IGNORECASE):
        return "number"
    # Check if it's a start date
    if re.match(r'^start:\s*(\"?.+?\"?|\(.+?\))$', input_string, re.IGNORECASE):
        return "start"

    return "unknown"


def _split_components_on_operator(input_string):
    """
    Splits the input query string into components based on the logical operators 'AND' or 'OR'.

    This function parses a query string containing conditions prefixed by 'key:', 'org:', 'number:', or 'start:'.
    It identifies logical operators ('AND' or 'OR') and separates the string into structured components.

    Args:
        input_string (str): The input query string to be parsed.

    Returns:
        list[dict]: A list of dictionaries where each dictionary contains:
            - "component" (str): A segment of the query (e.g., 'key:("value1" OR "value2")').
            - "operator" (str or None): The logical operator ('AND', 'OR') connecting to the next component.

    Example:
        >>> _split_components_on_operator('org:MITx AND key:("course1" OR "course2") OR number:12345')
        [
            {'component': 'org:MITx', 'operator': 'AND'},
            {'component': 'key:("course1" OR "course2")', 'operator': 'OR'},
            {'component': 'number:12345', 'operator': None}
        ]

    Notes:
        - The function is case-sensitive regarding the prefixes ('key:', 'org:', 'number:', 'start:').
        - Logical operators ('AND', 'OR') are case-insensitive and are captured if they precede a recognized prefix.
        - The last component will have `None` as its operator if there is no subsequent logical connection.
    """
    input_string = input_string.strip()  # Normalize input

    # Updated regex to detect 'AND' or 'OR' before 'key:', 'org:', or 'number:' using a non-capturing group
    pattern = r'(\s+(?:AND|OR)\s+)(?=key:|org:|number:|start:)'

    # Split the input string while keeping the delimiters
    query_parts = re.split(pattern, input_string)
    result = []

    # Iterate through parts and capture components with their operators
    for i in range(0, len(query_parts), 2):
        component = query_parts[i].strip()

        # Identify the operator if present
        operator = query_parts[i + 1].strip() if i + 1 < len(query_parts) else None

        if component:
            result.append({"component": component, "operator": operator})
        else:
            logger.info('Empty component found in input: %s', input_string)

    return result


def _concat_operator(operator):
    return f' {operator} ' if (operator is not None) else ''


def _process_query_string(query):
    """
    Processes a query string by detecting its type and generating the corresponding predicate.

    This function parses the input query string, determines the type of each component (
    e.g., 'org', 'number', 'key', 'start'),
    and applies the appropriate processing function to generate a predicate.
    The resulting predicates are concatenated using the detected logical operators ('AND' or 'OR').

    Args:
        query (str): The query string to be processed, containing components like
        'org:', 'number:', 'key:', or 'start:'.

    Returns:
        str: A processed predicate string for use in further filtering or querying.
        If no matching query type is found,
             it returns ''.

    Query Types and Handlers:
        - 'number': Processed by `process_number`
        - 'key': Processed by `process_key`
        - 'org': Processed by `process_org_values`
        - 'start': Processed by `process_date`

    Example:
        >>> process_query_string('org: ("edX" OR "MITx") AND number: ("CS101")')
        'attributes.`brand-text` in ("MITx", "edX") AND product.key in ("edX+CS101")'

        >>> process_query_string('key: ("CS50") OR start: [2023-01-01 TO 2024-01-01]')
        'variant.key in ("CS50") OR attributes.`courserun-start` >= "2023-01-01"
        AND attributes.`courserun-start` < "2024-01-02"'
    """
    predicate = ''
    components = _split_components_on_operator(query)

    # Mapping of query types to processing functions
    query_handlers_with_site_config = {
        'number': _process_number,
        'key': _process_key,
    }
    query_handlers_without_site_config = {
        'org': _process_org_values,
        'start': _process_date,
    }

    for comp in components:
        component = comp['component']
        operator = comp['operator']

        query_type = _detect_string_type(component)

        if query_type in query_handlers_with_site_config:
            query_predicate = query_handlers_with_site_config[query_type](component)
            if not query_predicate:
                return None

            predicate += query_predicate
            predicate += _concat_operator(operator)

        elif query_type in query_handlers_without_site_config:
            predicate += query_handlers_without_site_config[query_type](component)
            predicate += _concat_operator(operator)

        else:
            logger.error('Query type not handled in _process_query_string: %s', component)
            return None

    return predicate


def _process_date(component):
    component = component.replace('"', '')

    return _convert_date_range_to_predicate(component)


def _convert_date_range_to_predicate(date_range):
    """
    Converts a date range string into a predicate for filtering course start dates.

    This function extracts the start and end dates from the provided date range string
    in the format 'start:[YYYY-MM-DD TO YYYY-MM-DD]' and generates a corresponding
    SQL-like predicate for use in queries.

    Args:
        date_range (str): The date range string in the format
        'start:[YYYY-MM-DD TO YYYY-MM-DD]'.

    Returns:
        str: A predicate string in the format:
             'attributes.`courserun-start` >= "YYYY-MM-DD" AND attributes.
             `courserun-start` <= "YYYY-MM-DD"'.
             Returns an empty string if the input format is invalid.

    Example:
        >>> convert_date_range_to_predicate('start:[2023-01-01 TO 2023-12-31]')
        'attributes.`courserun-start` >= "2023-01-01" AND attributes.
        `courserun-start` <= "2023-12-31"'

        >>> convert_date_range_to_predicate('invalid_input')
        ''
    """
    # Regular expression to extract the start and end dates
    match = re.search(r'start:\[(\d{4}-\d{2}-\d{2}) TO (\d{4}-\d{2}-\d{2})\]', date_range)

    if not match:
        logger.error('Invalid date range format: %s', date_range)
        return ""

    start_date, end_date = match.groups()

    # Construct the desired predicate
    predicate = (
        f'attributes.`courserun-start` >= "{start_date}" '
        f'AND attributes.`courserun-start` < "{end_date}"'
    )

    return predicate


def _process_number(component):
    """
    Processes a course number component to generate a corresponding query predicate.

    This function checks if the provided component exists in the `KEY_TO_PREDICATE_DICT`
    dictionary and returns the corresponding predicate if found. If not found, it queries
    the catalog API to fetch course run IDs and generates a predicate using those IDs.
    If the component contains wildcards or starts with a negative sign, it skips the fetch call and logs an error.

    Args:
        component (str): The course number component to be processed.

    Returns:
        str: A predicate string representing the course number in the format:
             'product.key in ("org+number")'. Returns an empty string if no matching
             course runs are found.

    Example:
        >>> process_number("edX+CS50")
        'product.key in ("edX+CS50")'

        >>> process_number("unknown_course")
        ''
    """
    if component in KEY_TO_PREDICATE_DICT:
        return KEY_TO_PREDICATE_DICT[component]

    logger.error('Key not found in KEY_TO_PREDICATE_DICT: %s', component)
    return None


def _process_key(component):
    """
    Processes a key component to generate a corresponding query predicate.

    This function checks if the provided component exists in the `KEY_TO_PREDICATE_DICT`
    dictionary and returns the corresponding predicate if found. If not, it modifies the
    key values, fetches matching course run IDs from the catalog API, and generates a
    predicate using the retrieved course runs.
    If the component contains wildcards or starts with a negative sign, it skips the fetch call and logs an error.

    Args:
        component (str): The key component to be processed.

    Returns:
        str: A predicate string representing the course key. If the component is not
             found in the dictionary and no matching course runs are retrieved, it
             returns an empty string.

    Example:
        >>> process_key("edX+CS50")
        'variant.key in ("edX+CS50")'

        >>> process_key("-unknown_key")
        ''
    """
    if component in KEY_TO_PREDICATE_DICT:
        return KEY_TO_PREDICATE_DICT[component]

    logger.error('Key not found in KEY_TO_PREDICATE_DICT: %s', component)
    return None


def _remove_leading_trailing_and_or(query):
    # Remove leading AND/OR with optional whitespace
    query = re.sub(r'^\s*(AND|OR)\s+', '', query, flags=re.IGNORECASE)
    # Remove trailing AND/OR with optional whitespace
    query = re.sub(r'\s+(AND|OR)\s*$', '', query, flags=re.IGNORECASE)
    return query


def _query_cleaning_process(query):
    query = re.sub(r'"(key:|org:|number:|start:)', r'\1', query.replace('""', '"').replace('""', '"'))
    if query.endswith(')"'):
        return query[:-1]
    return query


def convert_querystring_to_predicate(query):
    """
    Convert a catalog querystring to a Commercetools predicate.

    Args:
        query (str): Catalog querystring.

    Returns:
        str: Commercetools predicate converted from catalog querystring.
    """
    cleaned_query = _query_cleaning_process(query)
    logger.info('Query to be processed: %s', cleaned_query)

    processed_query = _process_query_string(cleaned_query)
    if not processed_query:
        return None

    predicate = _remove_leading_trailing_and_or(processed_query)

    if predicate:
        logger.info('Catalog querystring converted into predicate: %s', predicate)

    return predicate.strip()


def get_category_for_coupon(coupon, product_category_model, summary_info) -> Tuple:
    """
    Get the category for the coupon.
    """
    try:
        category = product_category_model.objects.get(product=coupon).category.slug
    except product_category_model.DoesNotExist:
        category = None

    if not category:
        log_message = f"Product category object not found for for coupon {coupon.title}."
        logger.error(log_message)
        summary_info["cart_discounts"]["failed"].append({
            "name": 'Product category object not found.',
            "reason": log_message,
        })
        category = DEFAULT_PRODUCT_CATEGORY

    ct_category = LEGACY_CATEGORY_TO_CT_CATEGORY_MAPPING.get(category)
    if not ct_category:
        log_message = f"Category mapping not found for for coupon {coupon.title} with legacy category {category}."
        logger.error(log_message)
        summary_info["cart_discounts"]["failed"].append({
            "name": 'Category mapping not found.',
            "reason": log_message,
        })
        ct_category = DEFAULT_PRODUCT_CATEGORY

    channel = LEGACY_CATEGORY_TO_CHANNEL_MAPPING.get(category)
    if not channel:
        log_message = f"Channel mapping not found for for coupon {coupon.title} with legacy category {category}."
        logger.error(log_message)
        summary_info["cart_discounts"]["failed"].append({
            "name": 'Channel mapping not found.',
            "reason": log_message,
        })
        channel = DEFAULT_PRODUCT_CATEGORY

    return ct_category, channel


def get_next_sort_order_for_coupons(client) -> Decimal:
    """
    Get the highest sort order for cart discounts without discount codes.

    Args:
        client (CommercetoolsAPIClient): Commercetools API client.

    Returns:
        Decimal: The highest sort order.
    """
    where_query = 'requiresDiscountCode=true'
    where_query += ' and custom(fields(discountType in ("course-discount", "program-discount", "enrollment-code")))'
    response = client.get_highest_sort_order_for_cart_discount(
        where=where_query
    )

    if not response:
        raise CommandError("Failed to get highest sort order. Exiting command.")

    if response["count"] > 0:
        highest_sort_order = Decimal(response["results"][0]["sortOrder"])
        return highest_sort_order + COUPONS_DEFAULT_SORT_ORDER

    return COUPONS_DEFAULT_SORT_ORDER
