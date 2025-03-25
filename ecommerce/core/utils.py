import logging
import re
from urllib.parse import parse_qs, urlparse

import waffle
from django.conf import settings
from django.core.exceptions import ValidationError
from edx_django_utils.cache import get_cache_key as get_django_cache_key
from requests.exceptions import ConnectionError as ReqConnectionError
from requests.exceptions import RequestException, Timeout

from ecommerce.core.constants import KEY_TO_PREDICATE_DICT

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


def _extract_orgs(text: str) -> str:
    """
    Extracts organization values from a query string and formats them into a predicate.

    This function identifies and processes organization values provided in the input string
    (in formats such as `org:(A OR B)` or `org:"A"` or `org:A`). It handles multiple organizations,
    splits them on logical operators (AND/OR), removes duplicates, and returns a formatted predicate
    for querying.

    Args:
        text (str): The input query string containing organization information.

    Returns:
        str: A formatted predicate string of the form:
            'attributes.`brand-text` in ("org1", "org2", "org3")'

    Examples:
        >>> extract_orgs('org:(MITx OR HarvardX)')
        'attributes.`brand-text` in ("HarvardX","MITx")'

    Notes:
        - Supports organization values with or without parentheses or quotes.
        - Case-insensitive handling of logical operators (AND, OR).
        - Removes duplicate organization values from the output.
    """
    # Regular expression to find values after 'org:'
    org_pattern = re.findall(r'org:\s*(?:\((.*?)\)|"(.*?)"|([\w]+))', text)

    # Extract and clean orgs from the captured groups
    orgs = [org.strip().replace('"', '') for group in org_pattern for org in group if org]

    # Split on AND/OR (case-insensitive) and flatten the list
    split_orgs = [item for org in orgs for item in re.split(r'\s+(?:AND|OR)\s+', org, flags=re.IGNORECASE)]

    # Removing duplicates and joining as a single string
    orgs_str = ",".join(sorted(set(f'"{org}"' for org in split_orgs)))

    return f'attributes.`brand-text` in ({orgs_str})'


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


def _process_values(values):
    """
    Processes a string of values by transforming logical operators and removing hyphens.

    This function performs the following transformations:
    1. Splits the input string on the logical operators "AND" and "OR" (case-insensitive),
       while preserving the delimiters.
    2. Swaps "AND" with "OR" and vice versa, tracking the changes.
    3. Removes any hyphens from the values.
    4. Returns the processed string and a list of the changed operators.

    Args:
        values (str): The input string containing values and logical operators.

    Returns:
        tuple:
            - str: The processed string with modified logical operators and hyphen-free values.
            - list: A list of strings describing the changed operators (e.g., "AND → OR").

    Example:
        >>> _process_values("A AND B OR -C")
        ('A OR B AND C', ['AND → OR', 'OR → AND'])

        >>> _process_values("A AND -B")
        ('A OR B', ['AND → OR'])
    """
    # Split on AND/OR (case-insensitive) while keeping delimiters
    tokens = re.split(r'(\s+(?i:AND|OR)\s+)', values)

    # Track changed operators
    changed_operators = []

    # Process each token
    processed_tokens = []
    for token in tokens:
        token_upper = token.strip().upper()
        if token_upper == "AND":
            processed_tokens.append(" OR ")
            changed_operators.append("AND → OR")
        elif token_upper == "OR":
            processed_tokens.append(" AND ")
            changed_operators.append("OR → AND")
        else:
            # Remove '-' from values
            processed_tokens.append(token.replace("-", ""))

    return "".join(processed_tokens), changed_operators


def _modify_key_values(input_string):
    # Regex pattern to find key, org, or number values
    pattern = r'(key|number|org|start):\((.*?)\)'

    modified_string = input_string
    all_changed_operators = []

    for match in re.finditer(pattern, input_string):
        category, values = match.groups()
        if "-" in values:  # Only modify if values contain '-'
            modified_values, changed_operators = _process_values(values)
            all_changed_operators.extend(changed_operators)
            modified_string = modified_string.replace(match.group(0), f"{category}:({modified_values})")

    return modified_string, all_changed_operators


def _extract_course_info(course_string):
    """
    Extracts organization, course number, and course run information from a course string.

    This function parses a course identifier in the format `course-v1:<org>+<number>+<courserun>`
    and extracts the corresponding values for 'org', 'number', and 'courserun'.

    Args:
        course_string (str): The input string containing the course identifier.

    Returns:
        dict or str:
            - If the course string matches the expected format, a dictionary is returned with:
                - 'org' (str): The organization offering the course.
                - 'number' (str): The course number.
                - 'courserun' (str): The specific course run identifier.
            - If the input does not match the expected format, the string "Invalid course format" is returned.

    Example:
        >>> extract_course_info("course-v1:MITx+6.00.1x+2024_T1")
        {
            'org': 'MITx',
            'number': '6.00.1x',
            'courserun': '2024_T1'
        }

        >>> extract_course_info("invalid-course-string")
        "Invalid course format"

    Notes:
        - The function assumes the course identifier is in the format: `course-v1:<org>+<number>+<courserun>`.
        - If the format does not match, the function returns an error message instead of raising an exception.
    """
    # Define the regex pattern to extract org, number, and courserun
    pattern = r'course-v1:([a-zA-Z0-9_]+)\+([a-zA-Z0-9_\.]+)\+([a-zA-Z0-9_]+)'

    # Search for the pattern in the input string
    match = re.search(pattern, course_string)

    if match:
        org, number, courserun = match.groups()
        return {
            'org': org,
            'number': number,
            'courserun': courserun
        }
    logger.error('Invalid course format: %s', course_string)
    return "Invalid course format"


def _process_number_value(course_ids):
    """
    Generates a product key predicate from a list of course identifiers.

    This function takes a list of course IDs, extracts the organization and course number
    from the first course ID using the `extract_course_info` function, and returns a predicate
    in the format `product.key in (<org>+<number>)`.

    Args:
        course_ids (list of str): A list of course identifier strings in the format:
                                  "course-v1:<org>+<number>+<courserun>".

    Returns:
        str: A predicate string in the format `product.key in (<org>+<number>)` based on the
             organization and course number extracted from the first course ID.

    Example:
        >>> process_number_value(["course-v1:MITx+6.00.1x+2024_T1"])
        'product.key in (MITx+6.00.1x)'

    Notes:
        - This function only processes the first course ID from the input list.
        - Ensure the input is in the correct course identifier format. If the input does not match
          the expected format, the function may raise a KeyError or return incorrect results.
    """
    course_run_parsed_info = _extract_course_info(course_ids[0])
    return f'product.key in ({course_run_parsed_info["org"]}+{course_run_parsed_info["number"]})'


def _fetch_catalog_course_runs(query, limit, site_configuration):
    """
    Fetches a list of course run keys from the catalog service.

    This function queries the catalog service using the provided search query and limit,
    retrieves the matching course runs, and returns their course keys.

    Args:
        query (str): The search query to filter the catalog course runs.
        limit (int): The maximum number of course runs to retrieve.
        site_configuration (SiteConfiguration): The current site configuration object used
                                                to identify the partner's default site.

    Returns:
        list of str: A list of course run keys (e.g., "course-v1:MITx+6.00.1x+2024_T1").
                     Returns an empty list if the Catalog API request fails or no results are found.

    Raises:
        None: All exceptions related to the Catalog API request are caught and logged.

    Example:
        >>> fetch_catalog_course_runs("data science", 5, site_configuration)
        ['course-v1:HarvardX+PH526.1x+2024_T1', 'course-v1:MITx+6.00.1x+2024_T2']

    Notes:
        - The function assumes the catalog service is accessible and the partner with
          short code 'edX' exists in the database.
        - If the Catalog API request fails due to connection issues, it logs an error
          and returns an empty list.
    """

    from ecommerce.coupons.utils import get_catalog_course_runs  # pylint: disable=import-outside-toplevel

    try:
        response = get_catalog_course_runs(site=site_configuration.site, query=query, limit=limit, offset=0)
        results = response['results']
        course_ids = [result['key'] for result in results]
        return course_ids
    except (ReqConnectionError, RequestException, Timeout) as exc:
        logger.error('Unable to connect to Catalog API. %s', exc)
        return []


def _create_predicate_from_course_run(course_rns, all_changed_operators):
    """
    Generates a predicate string based on course run keys and specified operators.

    This function takes a list of course run identifiers and a list of operators. It removes duplicates,
    sorts the course runs for consistency, and formats them into a predicate string suitable for use in queries.
    If `all_changed_operators` contains any elements, the predicate uses `not in`, otherwise it uses `in`.

    Args:
        course_rns (list of str): A list of course run identifiers (e.g., ["org+number+run"]).
        all_changed_operators (list): A list indicating whether to apply exclusion logic (`not in`).

    Returns:
        str: A predicate string in the form of either:
             - `"variant.key not in (<formatted_courses>)"` if `all_changed_operators` is not empty.
             - `"variant.key in (<formatted_courses>)"` otherwise.

    Example:
        >>> create_predicate_from_course_run(["MITx+CS101+2024", "HarvardX+CS50+2023"], [])
        'variant.key in ("HarvardX+CS50+2023", "MITx+CS101+2024")'

        >>> create_predicate_from_course_run(["MITx+CS101+2024", "HarvardX+CS50+2023"], ["NOT"])
        'variant.key not in ("HarvardX+CS50+2023", "MITx+CS101+2024")'
    """
    # Remove duplicates and sort for consistency
    unique_courses = set(course_rns)

    # Properly format the output string
    formatted_courses = ', '.join(f'"{course}"' for course in unique_courses)
    if len(all_changed_operators) > 0:
        return f"variant.key not in ({formatted_courses})"
    # Return the desired output
    return f"variant.key in ({formatted_courses})"


def _concat_operator(operator):
    return f' {operator} ' if (operator is not None) else ''


def _process_query_string(query, site_configuration, summary_info):
    """
    Processes a query string by detecting its type and generating the corresponding predicate.

    This function parses the input query string, determines the type of each component (
    e.g., 'org', 'number', 'key', 'start'),
    and applies the appropriate processing function to generate a predicate.
    Certain query types require the `site_configuration`
    argument, while others do not. The resulting predicates are concatenated
    using the detected logical operators ('AND' or 'OR').

    Args:
        query (str): The query string to be processed, containing components like
        'org:', 'number:', 'key:', or 'start:'.
        site_configuration (object): Configuration object required for some query
        handlers (e.g., 'number' and 'key').
        summary_info (dict): Dictionary to store summary information including failures.

    Returns:
        str: A processed predicate string for use in further filtering or querying.
        If no matching query type is found,
             it returns ''.

    Query Types and Handlers:
        - 'number': Processed by `process_number` (requires `site_configuration`)
        - 'key': Processed by `process_key` (requires `site_configuration`)
        - 'org': Processed by `process_org_values` (does not require `site_configuration`)
        - 'start': Processed by `process_date` (does not require `site_configuration`)

    Example:
        >>> process_query_string('org: ("edX" OR "MITx") AND number: ("CS101")', site_config)
        'attributes.`brand-text` in ("MITx", "edX") AND product.key in ("edX+CS101")'

        >>> process_query_string('key: ("CS50") OR start: [2023-01-01 TO 2024-01-01]',
        site_config)
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
            predicate += query_handlers_with_site_config[query_type](component, site_configuration, summary_info)
            predicate += _concat_operator(operator)

        elif query_type in query_handlers_without_site_config:
            predicate += query_handlers_without_site_config[query_type](component)
            predicate += _concat_operator(operator)

        else:
            logger.info('No match found for %s', component)

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


def _has_wildcards_or_negatives(component):
    """
    Check if the component contains wildcards or negative signs in course keys.
    Only checks for negative signs within individual course keys after the prefix (key:, number:, etc.).

    Args:
        component (str): The component to check (e.g., "key:(-edx+DemoX AND -edx+InjuryPrevention)")

    Returns:
        bool: True if wildcards are found or negative signs are present in course keys, False otherwise.
    """
    if any(char in component for char in ['*', '?']):
        return True

    if ':' in component:
        component = component.split(':', 1)[1].strip()

    component = component.strip('()')
    parts = re.split(r'\s+(?:AND|OR)\s+', component, flags=re.IGNORECASE)

    # Checking each part for negative signs in keys
    for part in parts:
        part = part.strip()
        key_parts = part.split('+')

        if any(key_part.strip().startswith('-') for key_part in key_parts):
            return True

    return False


def _process_number(component, site_configuration, summary_info):
    """
    Processes a course number component to generate a corresponding query predicate.

    This function checks if the provided component exists in the `KEY_TO_PREDICATE_DICT`
    dictionary and returns the corresponding predicate if found. If not found, it queries
    the catalog API to fetch course run IDs and generates a predicate using those IDs.
    If the component contains wildcards or starts with a negative sign, it skips the fetch call and logs an error.

    Args:
        component (str): The course number component to be processed.
        site_configuration (object): The site configuration object used to interact
                                     with the catalog API.
        summary_info (dict): Dictionary to store summary information including failures.

    Returns:
        str: A predicate string representing the course number in the format:
             'product.key in ("org+number")'. Returns an empty string if no matching
             course runs are found.

    Example:
        >>> process_number("edX+CS50", site_configuration, summary_info)
        'product.key in ("edX+CS50")'

        >>> process_number("unknown_course", site_configuration, summary_info)
        ''
    """
    if component in KEY_TO_PREDICATE_DICT:
        return KEY_TO_PREDICATE_DICT[component]

    logger.error('Key not found in KEY_TO_PREDICATE_DICT: %s', component)

    if _has_wildcards_or_negatives(component):
        logger.error('Query contains wildcards or negative signs: %s', component)
        summary_info["cart_discounts"]["failed"].append({
            "name": component,
            "reason": f"Query contains wildcards or negative signs: '{component}'"
        })
        return ''

    summary_info["cart_discounts"]["failed"].append({
        "name": component,
        "reason": f"Key '{component}' not found in KEY_TO_PREDICATE_DICT"
    })

    course_ids = _fetch_catalog_course_runs(component, 1, site_configuration)
    if course_ids:
        return _process_number_value(course_ids)
    return ''


def _process_key(component, site_configuration, summary_info):
    """
    Processes a key component to generate a corresponding query predicate.

    This function checks if the provided component exists in the `KEY_TO_PREDICATE_DICT`
    dictionary and returns the corresponding predicate if found. If not, it modifies the
    key values, fetches matching course run IDs from the catalog API, and generates a
    predicate using the retrieved course runs.
    If the component contains wildcards or starts with a negative sign, it skips the fetch call and logs an error.

    Args:
        component (str): The key component to be processed.
        site_configuration (object): The site configuration object used to interact
                                     with the catalog API.
        summary_info (dict): Dictionary to store summary information including failures.

    Returns:
        str: A predicate string representing the course key. If the component is not
             found in the dictionary and no matching course runs are retrieved, it
             returns an empty string.

    Example:
        >>> process_key("edX+CS50", site_configuration, summary_info)
        'variant.key in ("edX+CS50")'

        >>> process_key("-unknown_key", site_configuration, summary_info)
        ''
    """
    if component in KEY_TO_PREDICATE_DICT:
        return KEY_TO_PREDICATE_DICT[component]

    logger.error('Key not found in KEY_TO_PREDICATE_DICT: %s', component)

    if _has_wildcards_or_negatives(component):
        logger.error('Query contains wildcards or negative signs: %s', component)
        summary_info["cart_discounts"]["failed"].append({
            "name": component,
            "reason": f"Query contains wildcards or negative signs: '{component}'"
        })
        return ''

    summary_info["cart_discounts"]["failed"].append({
        "name": component,
        "reason": f"Key '{component}' not found in KEY_TO_PREDICATE_DICT"
    })

    modified_str, all_changed_operators = _modify_key_values(component)
    course_ids = _fetch_catalog_course_runs(modified_str, 10000, site_configuration)

    if course_ids:
        return _create_predicate_from_course_run(course_ids, all_changed_operators)

    return ''


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


def convert_querystring_to_predicate(query, site_configuration, summary_info):
    """
    Convert a catalog querystring to a Commercetools predicate.

    Args:
        query (str): Catalog querystring.
        site_configuration: SiteConfiguration.
        summary_info (Dict): The summary information to be updated.

    Returns:
        str: Commercetools predicate converted from catalog querystring.
    """
    cleaned_query = _query_cleaning_process(query)
    logger.info('Query to be processed: %s', cleaned_query)

    processed_query = _process_query_string(cleaned_query, site_configuration, summary_info)
    predicate = _remove_leading_trailing_and_or(processed_query)

    if predicate:
        logger.info('Catalog querystring converted into predicate: %s', predicate)

    return predicate
