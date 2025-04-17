"""Constants core to the ecommerce app."""

from decimal import Decimal
from enum import Enum

ISO_8601_FORMAT = '%Y-%m-%dT%H:%M:%SZ'

# Regex used to match course IDs.
COURSE_ID_REGEX = r'[^/+]+(/|\+)[^/+]+(/|\+)[^/]+'
COURSE_ID_PATTERN = r'(?P<course_id>{})'.format(COURSE_ID_REGEX)

UUID_REGEX_PATTERN = r'[0-9a-fA-F]{8}-?[0-9a-fA-F]{4}-?4[0-9a-fA-F]{3}-?[89abAB][0-9a-fA-F]{3}-?[0-9a-fA-F]{12}'

# Seat constants
SEAT_PRODUCT_CLASS_NAME = 'Seat'

# switch is used to disable/enable USER table list/change view in django admin
USER_LIST_VIEW_SWITCH = 'enable_user_list_view'

# Coupon constant
COUPON_PRODUCT_CLASS_NAME = 'Coupon'

# Donations from checkout tests constant
# Don't use this code for your own purposes, thanks.
DONATIONS_FROM_CHECKOUT_TESTS_PRODUCT_TYPE_NAME = 'Donation'

# Enrollment Code constants
ENROLLMENT_CODE_PRODUCT_CLASS_NAME = 'Enrollment Code'
ENROLLMENT_CODE_SWITCH = 'create_enrollment_codes'
ENROLLMENT_CODE_SEAT_TYPES = ['verified', 'professional', 'no-id-professional']

# Braze
ENABLE_BRAZE = 'enable_braze'

# Course Entitlement constant
COURSE_ENTITLEMENT_PRODUCT_CLASS_NAME = 'Course Entitlement'

# Discovery Service constants
DEFAULT_CATALOG_PAGE_SIZE = 100

ENTERPRISE_COUPON_ADMIN_ROLE = 'enterprise_coupon_admin'
ENTERPRISE_COUPON_LEARNER_ROLE = 'enterprise_coupon_learner'
ENTERPRISE_OFFER_ADMIN_ROLE = 'enterprise_offer_admin'
ENTERPRISE_OFFER_LEARNER_ROLE = 'enterprise_offer_learner'
ORDER_MANAGER_ROLE = 'order_manager'

SYSTEM_ENTERPRISE_ADMIN_ROLE = 'enterprise_admin'
SYSTEM_ENTERPRISE_LEARNER_ROLE = 'enterprise_learner'
SYSTEM_ENTERPRISE_OPERATOR_ROLE = 'enterprise_openedx_operator'

STUDENT_SUPPORT_ADMIN_ROLE = 'student_support_admin'

# Context to give access to all resources
ALL_ACCESS_CONTEXT = '*'

# .. toggle_name: allow_missing_lms_user_id
# .. toggle_type: feature_flag
# .. toggle_default: False
# .. toggle_description: Toggle for allowing a missing LMS user id without raising an exception
# .. toggle_use_cases: open_edx
# .. toggle_warning: Other systems and micro frontends may assume that all users have an LMS user id
# .. toggle_tickets: REVMI-156
# .. toggle_status: supported
ALLOW_MISSING_LMS_USER_ID = 'allow_missing_lms_user_id'

# .. toggle_name: hubspot_forms_integration_enabled
# .. toggle_implementation: WaffleSwitch
# .. toggle_default: False
# .. toggle_description: Toggle for allowing order data for Enterprise purchases to be transmitted to Hubspot
# .. toggle_use_cases: open_edx
# .. toggle_tickets: ENT-2317
# .. toggle_status: supported
HUBSPOT_FORMS_INTEGRATION_ENABLE = "hubspot_forms_integration_enable"

CT_ABSOLUTE_DISCOUNT_TYPE = 'absolute'
CT_PERCENTAGE_DISCOUNT_TYPE = 'relative'

TEN_PERCENT_DISCOUNT_IN_CENTS = 1000

PROGRAM_OFFER_KEY = 'program-offer'
PROGRAM_OFFER_NAME = 'Program Offer'

BUNDLE_CART_DISCOUNT_KEY_FORMAT = "{type}-{value}"

COUPONS_DEFAULT_SORT_ORDER = Decimal('0.0000000001')  # 10 decimal places
PROGRAM_OFFERS_DEFAULT_SORT_ORDER = Decimal('0.000000000000001')  # 15 decimal places

DEFAULT_PRODUCT_CATEGORY = 'other'

LEGACY_CATEGORY_TO_CT_CATEGORY_MAPPING = {
    'affiliate-promotion': 'affiliate-promotion',
    'b2b-affiliate-promotion': 'b2b-affiliate-promotion',
    'bulk-enrollment': 'bulk-enrollment-prepay',
    'bulk-enrollment-integration': 'bulk-enrollment-prepay',
    'bulk-enrollment-prepay': 'bulk-enrollment-prepay',
    'bulk-enrollment-upon-redemption': 'bulk-enrollment-upon-redemption',
    'connected': 'other',
    'course-promotion': 'other',
    'customer-service': 'customer-service',
    'edx-employee-request': 'other',
    'financial-assistance': 'financial-assistance',
    'geography-promotion': 'marketing-other',
    'marketing-other': 'marketing-other',
    'marketing-partner-promotion': 'marketing-other',
    'on-campus-learners': 'on-campus-learners',
    'other': 'other',
    'partner-no-rev-orap': 'other',
    'partner-no-rev-prepay': 'partner-no-rev-prepay',
    'partner-no-rev-rap': 'other',
    'partner-no-rev-upon-redemption': 'partner-no-rev-prepay',
    'retention-promotion': 'marketing-other',
    'scholarship': 'other',
    'security-disclosure-reward': 'other',
    'services-other': 'customer-service',
    'support-other': 'customer-service',
    'upsell-promotion': 'marketing-other'
}

LEGACY_CATEGORY_TO_CHANNEL_MAPPING = {
    'affiliate-promotion': 'affiliate',
    'b2b-affiliate-promotion': 'enterprise-b2b',
    'bulk-enrollment': 'enterprise-b2b',
    'bulk-enrollment-integration': 'enterprise-b2b',
    'bulk-enrollment-prepay': 'enterprise-b2by',
    'bulk-enrollment-upon-redemption': 'enterprise-b2b',
    'connected': 'other',
    'course-promotion': 'other',
    'customer-service': 'other',
    'edx-employee-request': 'other',
    'financial-assistance': 'organic-edx',
    'geography-promotion': 'display-pmax',
    'marketing-other': 'organic-edx',
    'marketing-partner-promotion': 'organic-edx',
    'on-campus-learners': 'email',
    'other': 'other',
    'partner-no-rev-orap': 'enterprise-b2b',
    'partner-no-rev-prepay': 'enterprise-b2b',
    'partner-no-rev-rap': 'enterprise-b2b',
    'partner-no-rev-upon-redemption': 'enterprise-b2b',
    'retention-promotion': 'email',
    'scholarship': 'other',
    'security-disclosure-reward': 'other',
    'services-other': 'other',
    'support-other': 'other',
    'upsell-promotion': 'email'
}

KEY_TO_PREDICATE_DICT = {
    'key: ("AlaskaX+GRANT1x" OR "AlaskaX+GRANT2x" OR "AlaskaX+GRANT3x")':
    '(product.key = "AlaskaX+GRANT3x" or product.key = "AlaskaX+GRANT2x" or product.key = "AlaskaX+GRANT1x")',
    'key: ("MITx+CTL.SC0x" OR "MITx+CTL.SC1x" OR "MITx+CTL.SC2x" OR "MITx+CTL.SC3x" OR "MITx+CTL.SC4x")':
    '(product.key = "MITx+CTL.SC0x" or product.key = "MITx+CTL.SC1x" or product.key = "MITx+CTL.SC2x"'
    ' or product.key = "MITx+CTL.SC3x" or product.key = "MITx+CTL.SC4x")',
    'key: "RICEx+RiceSBE01"': 'product.key = "RICEx+RiceSBE01"',
    'key: "Statistics.comX+MLOps2-GCP"': 'product.key = "Statistics.comX+MLOps2-GCP"',
    'key: ("HP+HPGG01.en" OR "HP+HPGG01.es" OR "HP+HPGG02.en" OR "HP+HPGG03.en" '
    'OR "HP+HPGG01.ar" OR "HP+HPGG02.ar" OR "HP+HPGG02.es" OR "HP+HPGG03.ar" '
    'OR "HP+HPGG03.es" OR "HP+HPGG04.en")':
    '(product.key = "HP+HPGG01.en" or product.key = "HP+HPGG01.es" or product.key = "HP+HPGG02.en"'
    ' or product.key = "HP+HPGG03.en" or product.key = "HP+HPGG01.ar" or product.key = "HP+HPGG02.ar"'
    ' or product.key = "HP+HPGG02.es" or product.key = "HP+HPGG03.ar" or product.key = "HP+HPGG03.es"'
    ' or product.key = "HP+HPGG04.en")',
    'key: ("GalileoX+EticaIA_01" OR "GalileoX+MM_01" OR "GalileoX+GalileoXAI002")':
    '(product.key = "GalileoX+EticaIA_01" or product.key = "GalileoX+MM_01" or product.key = "GalileoX+GalileoXAI002")',
    'key: "DelftX+AIfE5x"': 'product.key = "DelftX+AIfE5x"',
    'key: "Statistics.comX+MLOps1-GCP"': 'product.key = "Statistics.comX+MLOps1-GCP"',
    'key:(StudioX OR VideoX OR StudioAdv1 OR BlendedX OR edX101 OR '
    'BuildWedX OR RunningWedX OR DesignWedX OR BuildWedXNEW OR RunWedXNEW)':
    '(product.key = "edX+RunWedXNEW" or product.key = "edX+DesignWedX" or product.key = "edX+StudioAdv1"'
    ' or product.key = "edX+VideoX" or product.key = "edX+edX101" or product.key = "edX+RunningWedX"'
    ' or product.key = "edX+BlendedX" or product.key = "edX+StudioX")',
    'key: "UC3Mx IM.2-ESx"': 'product.key = "UC3Mx+IM.2-ESx"',
    'key: (lead1x)': 'product.key = "HarvardX+LEAD1x"',
    'key: ("AdelaideX+RiskX" OR "AdelaideX+Project101x" OR "AdelaideX+Entrep101X")':
    '(product.key = "AdelaideX+Entrep101X" or product.key = "AdelaideX+Project101x"'
    ' or product.key = "AdelaideX+RiskX")',
    'key: "DelftX+QTM4x+2T2024"': 'variant.key = "course-v1:DelftX+QTM4x+2T2024"',
    'key: ("AdelaideX+PolyTraX" OR "AdelaideX+SpecTraX" OR "AdelaideX+DiffTraX"'
    ' OR "AdelaideX+InteTraX" OR "AdelaideX+ProbTraX" OR "AdelaideX+StatTraX"'
    ' OR "AdelaideX+MathTrackX")':
    '(product.key = "AdelaideX+PolyTraX" or product.key = "AdelaideX+SpecTraX"'
    ' or product.key = "AdelaideX+DiffTraX" or product.key = "AdelaideX+InteTraX" or product.key = "AdelaideX+ProbTraX"'
    ' or product.key = "AdelaideX+StatTraX" or product.key = "AdelaideX+MathTrackX")',
    'key: ("UAMx+Griegox" OR "UAMx+Griego1.5x")': '(product.key = "UAMx+Griegox" or product.key = "UAMx+Griego1.5x")',
    'key:("MITx+6.431x" OR "MITx+6.86x" OR "MITx+18.6501x" '
    'OR "MITx+6.419x" OR "MITx+14.310Fx" OR "MITx+DS.CFx")':
    '(product.key = "MITx+6.431x" or product.key = "MITx+6.86x" or product.key = "MITx+18.6501x"'
    ' or product.key = "MITx+6.419x" or product.key = "MITx+14.310Fx" or product.key = "MITx+DS.CFx")',
    'key: ("TecdeMonterreyX+CT01I.x" OR "TecdeMonterreyX+MMLO01I.x" OR "TecdeMonterreyX+MMLF01I.x")':
    '(product.key = "TecdeMonterreyX+CT01I.x" or product.key = "TecdeMonterreyX+MMLO01I.x"'
    ' or product.key = "TecdeMonterreyX+MMLF01I.x")',
    'key: "RICEx+RiceSBE02"': 'product.key = "RICEx+RiceSBE02"',
    'key: ("TecdeMonterreyX+CT01I.x" OR "TecdeMonterreyX+MMEC01I.x" '
    'OR "TecdeMonterreyX+MMLF01I.x" OR "TecdeMonterreyX+MMSE01I.x" OR'
    ' "TecdeMonterreyX+MMSS01I.x" OR "TecdeMonterreyX+MMLO01I.x")':
    '(product.key = "TecdeMonterreyX+CT01I.x" or product.key = "TecdeMonterreyX+MMEC01I.x"'
    ' or product.key = "TecdeMonterreyX+MMLF01I.x" or product.key = "TecdeMonterreyX+MMSE01I.x"'
    ' or product.key = "TecdeMonterreyX+MMSS01I.x" or product.key = "TecdeMonterreyX+MMLO01I.x")',
    'key: "TUGrazX+EMC1"': 'product.key = "TUGrazX+EMC1"',
    'key: "DelftX+OS101x"': 'product.key = "DelftX+OS101x"',
    'key: ("UTAustinX+FINTECH-OVERVIEW" OR "UTAustinX+FINTECH-BT" OR'
    ' "UTAustinX+FINTECH-ML" OR "UTAustinX+FINTECH-IOT")':
    '(product.key = "UTAustinX+FINTECH-OVERVIEW" or product.key = "UTAustinX+FINTECH-BT"'
    ' or product.key = "UTAustinX+FINTECH-ML" or product.key = "UTAustinX+FINTECH-IOT")',
    'key: "DelftX+eCARS1x+2T2024"': 'variant.key = "course-v1:DelftX+eCARS1x+2T2024"',
    'key: ("DelftX+PV1Ex" OR "DelftX+PV2Ex" OR "DelftX+PV3Ex" OR "DelftX+PV4Ex")':
    '(product.key = "DelftX+PV1Ex" or product.key = "DelftX+PV2Ex"'
    ' or product.key = "DelftX+PV3Ex" or product.key = "DelftX+PV4Ex")',
    'key: "DECx+B101Cx2"': 'product.key = "DECx+B101Cx2"',
    'key:("ColumbiaX+CU.OC.AI001" OR "ColumbiaX+CU.OC.AI002")':
    '(product.key = "ColumbiaX+CU.OC.AI001" or product.key = "ColumbiaX+CU.OC.AI002")',
    'key: "MITx+15.516x+3T2024"': 'variant.key = "course-v1:MITx+15.516x+3T2024"',
    'key: "DelftX+OS101x+"': 'product.key = "DelftX+OS101x"',
    'key: ("AlaskaX+DODGS-400" OR "AlaskaX+DODGS-401" OR "AlaskaX+DODGS-402")':
    '(product.key = "AlaskaX+DODGS-400" or product.key = "AlaskaX+DODGS-401" or product.key = "AlaskaX+DODGS-402")',
    'key: "Teams101x"': 'product.key = "UQx+Teams101x"',
    'key: ("UBCx+Biobank1x" OR "UBCx+Biobank2x")':
    '(product.key = "UBCx+Biobank1x" or product.key = "UBCx+Biobank2x")',
    'key: "DelftX+eCARS2x+2T2024"': 'variant.key = "course-v1:DelftX+eCARS2x+2T2024"',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_AB.2x")':
    '(product.key = "TecdeMonterreyX+HC_CDE.1x" or product.key = "TecdeMonterreyX+HC_AB.2x")',
    'key: "UC3Mx IM.1x"': 'product.key = "UC3Mx+IM.1x"',
    'key: "DelftX+AIfE3x+3T2024"': 'variant.key = "course-v1:DelftX+AIfE3x+3T2024"',
    'key: "DelftX+TUDF-FE01x"': 'product.key = "DelftX+TUDF-FE01x"',
    'key: ("TUGrazX+SCS1" OR "TUGrazX+SCS2" OR "TUGrazX+SCS3" '
    'OR "TUGrazX+SCS4" OR "TUGrazX+SCS5" OR "TUGrazX+SCS6")':
    '(product.key = "TUGrazX+SCS1" or product.key = "TUGrazX+SCS2" or product.key = "TUGrazX+SCS3"'
    ' or product.key = "TUGrazX+SCS4" or product.key = "TUGrazX+SCS5" or product.key = "TUGrazX+SCS6")',
    'key: "DECx+DA101Cx1"': 'product.key = "DECx+DA101Cx1"',
    'key: ("MITx+DS.CFx" OR "MITx+6.431x" OR "MITx+6.86x" '
    'OR "MITx+18.6501x" OR "MITx+6.419x" OR "MITx+IDS.S24x" '
    'OR "MITx+14.310Fx")':
    '(product.key = "MITx+DS.CFx" or product.key = "MITx+6.431x" or product.key = "MITx+6.86x"'
    ' or product.key = "MITx+18.6501x" or product.key = "MITx+6.419x" or product.key = "MITx+IDS.S24x"'
    ' or product.key = "MITx+14.310Fx")',
    'key: ("DelftX+QTM1x" OR "DelftX+QTM2x" OR "DelftX+QTM3x")':
    '(product.key = "DelftX+QTM1x" or product.key = "DelftX+QTM2x" or product.key = "DelftX+QTM3x")',
    'key: ("DECx+B101Cx1" OR "DECx+B101Cx2" OR "DECx+DA101Cx1" OR "DECx+DA101Cx2")':
    '(product.key = "DECx+B101Cx1" or product.key = "DECx+B101Cx2" or product.key = "DECx+DA101Cx1"'
    ' or product.key = "DECx+DA101Cx2")',
    'key: ("DelftX+OS101x+1T2025" OR "DelftX+MathMod1x+1T2025" OR "DelftX+OT.1x+1T2025")':
    '(variant.key = "course-v1:DelftX+OT.1x+1T2025" or variant.key = "course-v1:DelftX+MathMod1x+1T2025"'
    ' or variant.key = "course-v1:DelftX+OS101x+1T2025")',
    'key: ("TecdeMonterreyX+HC_AB.2x" OR "TecdeMonterreyX+HC_MFN.1x")':
    '(product.key = "TecdeMonterreyX+HC_AB.2x" or product.key = "TecdeMonterreyX+HC_MFN.1x")',
    'key: "DelftX+OS101x+1T2025"': 'variant.key = "course-v1:DelftX+OS101x+1T2025"',
    'key: ("IsraelX+MBSE101" OR "IsraelX+MBSE102")':
    '(product.key = "IsraelX+MBSE101" or product.key = "IsraelX+MBSE102")',
    'key: ("RiskX" OR "Entrep101x" OR "Project101x")':
    '(product.key = "AdelaideX+Project101x" or product.key = "AdelaideX+RiskX"'
    ' or product.key = "AdelaideX+Entrep101X")',
    'key: ("IsraelX+CONVERT" OR "IsraelX+resilience911" OR'
    ' "IsraelX+KAB1010x" OR "IsraelX+EPS1x" OR "IsraelX+WECS")':
    '(product.key = "IsraelX+CONVERT" or product.key = "IsraelX+resilience911" or product.key = "IsraelX+KAB1010x"'
    ' or product.key = "IsraelX+EPS1x" or product.key = "IsraelX+WECS")',
    'key: "UC3Mx+IM.3x"': 'product.key = "UC3Mx+IM.3x"',
    'key: ("TecdeMonterreyX+HC_AB.2x")': 'product.key = "TecdeMonterreyX+HC_AB.2x"',
    'key: ("TAUx+Viruses101" OR "TAUx+Viruses102")':
    '(product.key = "TAUx+Viruses101" or product.key = "TAUx+Viruses102")',
    'key:"DelftX+OS101x"': 'product.key = "DelftX+OS101x"',
    'key: ("AdelaideX+RiskX" OR "AdelaideX+Entrep101X" OR "AdelaideX+Project101x")':
    '(product.key = "AdelaideX+RiskX" or product.key = "AdelaideX+Entrep101X"'
    ' or product.key = "AdelaideX+Project101x")',
    'key: ("DelftX+PV1x" OR "DelftX+PV2x" OR "DelftX+PV3x" OR "DelftX+PV4x")':
    '(product.key = "DelftX+PV1x" or product.key = "DelftX+PV2x" or product.key = "DelftX+PV3x"'
    ' or product.key = "DelftX+PV4x")',
    'key: ("DelftX+AIfE5x+3T2024" OR "DelftX+AIfE6x+3T2024")':
    '(variant.key = "course-v1:DelftX+AIfE6x+3T2024" or variant.key = "course-v1:DelftX+AIfE5x+3T2024")',
    'key: "DelftX+MDRP1x"': 'product.key = "DelftX+MDRP1x"',
    'key: "DECx+CDAA1.3x"': 'product.key = "DECx+CDAA1.3x"',
    'key:(*)': '',
    'key:(StudioX BlendedX edX101 VideoX StudioAdv1)':
    '(product.key = "edX+BlendedX" or product.key = "edX+edX101" or product.key = "edX+StudioX"'
    ' or product.key = "edX+VideoX" or product.key = "edX+StudioAdv1")',
    'key: ("AlaskaX+GIS1x" OR "AlaskaX+GIS2x" OR "AlaskaX+GIS3x" OR "AlaskaX+RSW1")':
    '(product.key = "AlaskaX+GIS1x" or product.key = "AlaskaX+GIS2x" or product.key = "AlaskaX+GIS3x"'
    ' or product.key = "AlaskaX+RSW1")',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_MRL.2x" OR "TecdeMonterreyX+EGT-TD1x" )':
    '(product.key = "TecdeMonterreyX+HC_CDE.1x" or product.key = "TecdeMonterreyX+HC_MRL.2x"'
    ' or product.key = "TecdeMonterreyX+EGT-TD1x")',
    'key:("6.419x" or "6.86x" or "DS.CFx" or "14.310Fx" or "6.431x" or "18.6501x")':
    '(product.key = "MITx+6.86x" or product.key = "MITx+14.310Fx" or product.key = "MITx+DS.CFx"'
    ' or product.key = "MITx+6.419x" or product.key = "MITx+18.6501x" or product.key = "MITx+6.431x")',
    'key: ("15.415.1x/3T2024" OR "15.415.2x/2T2024" OR "15.516x/3T2024" OR "15.455x/1T2025")':
    '(variant.key = "course-v1:MITx+15.455x+1T2025" or variant.key = "course-v1:MITx+15.415.2x+2T2024"'
    ' or variant.key = "course-v1:MITx+15.516x+3T2024" or variant.key = "course-v1:MITx+15.415.1x+3T2024")',
    'key: "DelftX+QTM2x+2T2024"': 'variant.key = "course-v1:DelftX+QTM2x+2T2024"',
    'key: ("AlaskaX+UAS1x" OR "AlaskaX+UAS2x")':
    '(product.key = "AlaskaX+UAS1x" or product.key = "AlaskaX+UAS2x")',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_PEA.2x" '
    'OR "TecdeMonterreyX+HC_IFA.1x" OR "TecdeMonterreyX+HC_MRL.2x")':
    '(product.key = "TecdeMonterreyX+HC_CDE.1x" or product.key = "TecdeMonterreyX+HC_PEA.2x"'
    ' or product.key = "TecdeMonterreyX+HC_IFA.1x" or product.key = "TecdeMonterreyX+HC_MRL.2x")',
    'key: ("UCx+GEO03.1ucX" OR"UCx+GEO04.2ucX")': '(product.key = "UCx+GEO03.1ucX" or product.key = "UCx+GEO04.2ucX")',
    'key: "DA101Cx2"': 'product.key = "DECx+DA101Cx2"',
    'key: "WellesleyX+APIta.2023x"': 'product.key = "WellesleyX+APIta.2023x"',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_IFA.1x" '
    'OR "TecdeMonterreyX+HC_MFN.1x" OR "TecdeMonterreyX+HC_PEA.2x" '
    'OR "TecdeMonterreyX+HC_AB.2x" OR "TecdeMonterreyX+HC_MRL.2x")':
    '(product.key = "TecdeMonterreyX+HC_CDE.1x" or product.key = "TecdeMonterreyX+HC_IFA.1x"'
    ' or product.key = "TecdeMonterreyX+HC_MFN.1x" or product.key = "TecdeMonterreyX+HC_PEA.2x"'
    ' or product.key = "TecdeMonterreyX+HC_AB.2x" or product.key = "TecdeMonterreyX+HC_MRL.2x")',
    'key: ("TecdeMonterreyX+EGT-TD1x" OR "TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_MRL.2x")':
    '(product.key = "TecdeMonterreyX+EGT-TD1x" or product.key = "TecdeMonterreyX+HC_CDE.1x"'
    ' or product.key = "TecdeMonterreyX+HC_MRL.2x")',
    'key: ("MITx+18.6501x" OR "MITx+6.419x" OR '
    '"MITx+6.431x" OR "MITx+6.86x" OR "MITx+DS.CFx" OR "MITx+IDS.S24x" OR "MITx+14.310Fx")':
    '(product.key = "MITx+18.6501x" or product.key = "MITx+6.419x" or product.key = "MITx+6.431x"'
    ' or product.key = "MITx+6.86x" or product.key = "MITx+DS.CFx" or product.key = "MITx+IDS.S24x"'
    ' or product.key = "MITx+14.310Fx")',
    'key: ("HP+HPGG01.en" OR "HP+HPGG01.es" OR '
    '"HP+HPGG02.en" OR "HP+HPGG03.en" OR "HP+HPGG01.ar" OR '
    '"HP+HPGG02.ar" OR "HP+HPGG02.es" OR "HP+HPGG03.ar" OR '
    '"HP+HPGG03.es" OR "HP+HPGG04.en" OR "HP+HPGG04.ar" OR "HP+HPGG04.es")':
    '(product.key = "HP+HPGG01.en" or product.key = "HP+HPGG01.es" or product.key = "HP+HPGG02.en"'
    ' or product.key = "HP+HPGG03.en" or product.key = "HP+HPGG01.ar" or product.key = "HP+HPGG02.ar"'
    ' or product.key = "HP+HPGG02.es" or product.key = "HP+HPGG03.ar" or product.key = "HP+HPGG03.es"'
    ' or product.key = "HP+HPGG04.en" or product.key = "HP+HPGG04.ar" or product.key = "HP+HPGG04.es")',
    'key: ("ChalmersX+ChM005x" OR "ChalmersX+ChM006x")':
    '(product.key = "ChalmersX+ChM005x" or product.key = "ChalmersX+ChM006x")',
    'key: ("TecdeMonterreyX+EGT-TD1x" OR "TecdeMonterreyX+HC_CDE.1x" '
    'OR "TecdeMonterreyX+HC_MRL.2x" OR "TecdeMonterreyX+MMEC01I.x" '
    'OR "TecdeMonterreyX+MMSE01I.x" OR "TecdeMonterreyX+MMSS01I.x")':
    '(product.key = "TecdeMonterreyX+EGT-TD1x" or product.key = "TecdeMonterreyX+HC_CDE.1x"'
    ' or product.key = "TecdeMonterreyX+HC_MRL.2x" or product.key = "TecdeMonterreyX+MMEC01I.x"'
    ' or product.key = "TecdeMonterreyX+MMSE01I.x" or product.key = "TecdeMonterreyX+MMSS01I.x")',
    'key: "DECx+B101Cx1"': 'product.key = "DECx+B101Cx1"',
    'key: ("DelftX+AIfE5x" OR "DelftX+AIfE6x" OR "DelftX+AIfE3x")':
    '(product.key = "DelftX+AIfE5x" or product.key = "DelftX+AIfE6x" or product.key = "DelftX+AIfE3x")',
    'key:(-IOT?x AND -MGT6203x AND -CSE6040x AND -ISYE6501x)':
    '(product.key != "CurtinX+IOT2x" and product.key != "CurtinX+IOT4x" and product.key != "CurtinX+IOT3x"'
    ' and product.key != "CurtinX+IOT6x" and product.key != "CurtinX+IOT5x" and product.key != "CurtinX+IOT1x"'
    ' and product.key != "GTx+MGT6203x" and product.key != "GTx+CSE6040x" and product.key != "GTx+ISYE6501x")',
    'key:(-MGT6203x AND -CSE6040x AND -ISYE6501x)':
    '(product.key != "GTx+MGT6203x" and product.key != "GTx+CSE6040x" and product.key != "GTx+ISYE6501x")',
    'key:(-CORPFIN1x AND -CORPFIN2x AND -CORPFIN3x '
    'AND -CSE6040x AND -ISYE6501x AND -MGT6203x)':
    '(product.key != "ColumbiaX+CORPFIN1x" and product.key != "ColumbiaX+CORPFIN2x"'
    ' and product.key != "ColumbiaX+CORPFIN3x" and product.key != "GTx+CSE6040x" and product.key != "GTx+ISYE6501x"'
    ' and product.key != "GTx+MGT6203x")',
    'key:(-IOT6x AND -MGT6203x AND -CSE6040x AND -ISYE6501x AND -3.46.2x)':
    '(product.key != "CurtinX+IOT6x" and product.key != "GTx+MGT6203x" and product.key != "GTx+CSE6040x"'
    ' and product.key != "GTx+ISYE6501x" and product.key != "MITx+3.46.2x")',
    'key:(-CORPFIN2x AND -CORPFIN3x AND -CORPFIN1x AND -CSE6040x AND '
    '-ISYE6501x AND -MGT6203x)':
    '(product.key != "ColumbiaX+CORPFIN2x" and product.key != "ColumbiaX+CORPFIN3x"'
    ' and product.key != "ColumbiaX+CORPFIN1x" and product.key != "GTx+CSE6040x" and product.key != "GTx+ISYE6501x"'
    ' and product.key != "GTx+MGT6203x")',
    'key:(-CSMM* AND -MGT6203x AND -CSE6040x AND -ISYE6501x)':
    '(product.key != "ColumbiaX+CSMM.104x" and product.key != "ColumbiaX+CSMM.103x"'
    ' and product.key != "ColumbiaX+CSMM.101x" and product.key != "ColumbiaX+CSMM.102x"'
    ' and product.key != "MichiganX+CSMM.103x" and product.key != "MichiganX+CSMM.104x"'
    ' and product.key != "GTx+MGT6203x" and product.key != "GTx+CSE6040x" and product.key != "GTx+ISYE6501x")',
    'number:"Louv25.1x"': 'product.key = "LouvainX+Louv25.1"',
    'number:(LEAD1x)': 'product.key = "HarvardX+LEAD1x"',
    'number:Louv21x': 'product.key = "LouvainX+Louv21x"',
    'number:Louv13x': 'product.key = "LouvainX+Louv13x"',
    'number:URX37': 'product.key = "URosarioX+URX37"',
    'number:"Louv25.2x"': 'product.key = "LouvainX+Louv25.2x"',
    'number:Louv31x': 'product.key = "LouvainX+Louv31x"',
    'number:(CONVERT OR resilience911 OR KAB1010x OR EPS1x OR WECS)':
    '(product.key = "IsraelX+EPS1x" or product.key = "IsraelX+resilience911" or product.key = "IsraelX+CONVERT"'
    ' or product.key = "IsraelX+KAB1010x" or product.key = "IsraelX+WECS")',
    'key:("6.419x" or ""6.86x" or "DS.CFx" or "14.310Fx" or "6.431x" or "18.6501x")':
    '(product.key = "MITx+6.419x" or product.key = "MITx+DS.CFx" or product.key = "MITx+14.310Fx"'
    ' or product.key = "MITx+6.86x" or product.key = "MITx+6.431x" or product.key = "MITx+18.6501")',
    'start:[2023-01-01 TO 2061-12-31]': '',
    'key:(JuilliardOpenClassroom+JCx001+2T2017 OR '
    'JuilliardOpenClassroom+JCx002+3T2017 OR '
    'JuilliardOpenClassroom+JCx003+1T2017 OR '
    'JuilliardOpenClassroom+JC004+1T2017)':
    '(variant.key = "course-v1:JuilliardOpenClassroom+JCx001+2T2017"'
    ' or variant.key = "course-v1:JuilliardOpenClassroom+JCx002+3T2017"'
    ' or variant.key = "course-v1:JuilliardOpenClassroom+JCx003+1T2017"'
    ' or variant.key = "course-v1:JuilliardOpenClassroom+JC004+1T2017")',
    'key: ("DelftX" AND "AIfE6x")': 'product.key = "DelftX+AIfE6x"',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x '
    'AND -15.435x AND -15.455x AND -15.516x AND -TUMx+QPLS1x'
    ' AND -TUMx+QPLS2x AND -TUMx+QPLS3x AND -TUMx+QPLS5x)':
    '(product.key != "CurtinX+IOT6x" and product.key != "MITx+3.46.2x" and product.key != "MITx+15.435x"'
    ' and product.key != "MITx+15.455x" and product.key != "MITx+15.516x" and product.key != "MITx+15.415.2x"'
    ' and product.key != "TUMx+QPLS5x" and product.key != "TUMx+QPLS2x" and product.key != "TUMx+QPLS3x"'
    ' and product.key != "TUMx+QPLS1x" and product.key != "MITx+15.415.1x")',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x '
    'AND -15.435x AND -15.455x AND -15.516x AND -QPLS1x '
    'AND -QPLS2x AND -QPLS3x AND -QPLS5x)':
    '(product.key != "CurtinX+IOT6x" and product.key != "MITx+3.46.2x" and product.key != "MITx+15.435x"'
    ' and product.key != "MITx+15.455x" and product.key != "MITx+15.516x" and product.key != "MITx+15.415.2x"'
    ' and product.key != "TUMx+QPLS5x" and product.key != "TUMx+QPLS2x" and product.key != "TUMx+QPLS3x"'
    ' and product.key != "TUMx+QPLS1x" and product.key != "MITx+15.415.1x")',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x '
    'AND -15.435x AND -15.455x AND -15.516x)':
    '(product.key != "CurtinX+IOT6x" and product.key != "MITx+3.46.2x" and product.key != "MITx+15.435x"'
    ' and product.key != "MITx+15.455x" and product.key != "MITx+15.516x" and product.key != "MITx+15.415.2x"'
    ' and product.key != "MITx+15.415.1x")',
    'key: (-"MITx+DS.CFx" OR -"MITx+6.431x" OR -"MITx+6.86x" '
    'OR -"MITx+18.6501x" OR -"MITx+6.419x" OR -"MITx+IDS.S24x" '
    'OR -"MITx+14.310Fx")': '(product.key != "MITx+DS.CFx" or product.key != "MITx+6.431x"'
    ' or product.key != "MITx+6.86x" or product.key != "MITx+18.6501x" or product.key != "MITx+6.419x"'
    ' or product.key != "MITx+IDS.S24x" or product.key != "MITx+14.310Fx")',
    'key:(-IOT6x AND -MGT6203x AND -CSE6040x AND -ISYE6501x '
    'AND -3.46.2x AND -15.415.1x AND -15.415.2x AND -15.435x '
    'AND -15.455x AND -15.516x)':
    '(product.key != "CurtinX+IOT6x" and product.key != "MITx+15.435x" and product.key != "GTx+MGT6203x"'
    ' and product.key != "GTx+CSE6040x" and product.key != "GTx+ISYE6501x" and product.key != "MITx+3.46.2x"'
    ' and product.key != "MITx+15.415.1x" and product.key != "MITx+15.415.2x" and product.key != "MITx+15.435x"'
    ' and product.key != "MITx+15.455x" and product.key != "MITx+15.516x")',
    'key: "UBCx+AI.02x"': 'product.key = "UBCx+AI.02x"',
    '"NUS+QQRB001x"': 'product.key = "NUS+QQRB001x"',
    'key: "AnahuacX"': 'attributes.`brand-text` = "AnahuacX"',
    'key: "AdelaideX+Project101x"': 'product.key = "AdelaideX+Project101x"',
    'key:"AlaskaX+GIS1x"': 'product.key = "AlaskaX+GIS1x"',
    'key: "AlaskaX+AI01x"': 'product.key = "AlaskaX+AI01x"',
    'key: "AlaskaX+DODGS-400"': 'product.key = "AlaskaX+DODGS-400"',
    'key: "AlaskaX+DODGS-401"': 'product.key = "AlaskaX+DODGS-401"',
    'key: "AlaskaX+DODGS-402"': 'product.key = "AlaskaX+DODGS-402"',
    'key: "AlaskaX+MAKE1x"': 'product.key = "AlaskaX+MAKE1x"',
    'key: "AlaskaX+SPRT1x"': 'product.key = "AlaskaX+SPRT1x"',
    'key: "AlaskaX+SPRT3x"': 'product.key = "AlaskaX+SPRT3x"',
    'key: "AlaskaX+UAS1x"': 'product.key = "AlaskaX+UAS1x"',
    'key: "BayreuthX+ubt205mun"': 'product.key = "BayreuthX+ubt205mun"',
    'key: "BerkeleyX+GG102x"': 'product.key = "BerkeleyX+GG102x"',
    'key: "BerkeleyX+GG201x"': 'product.key = "BerkeleyX+GG201x"',
    'key: "CGI_U+CGIU.1x"': 'product.key = "CGI_U+CGIU.1x"',
    'key: "ColumbiaX+PCH1x"': 'product.key = "ColumbiaX+PCH1x"',
    'key: "CurtinX+NSSI1x"': 'product.key = "CurtinX+NSSI1x"',
    'key: "DelftX+AIfE3x"': 'product.key = "DelftX+AIfE3x"',
    'key: "DelftX+AIIP2x+"': 'product.key = "DelftX+AIIP2x"',
    'key: "DelftX+OT.1x"': 'product.key = "DelftX+OT.1x"',
    'key: "edX+BC-OC-ai"': 'product.key = "edX+BC-OC-ai"',
    'key: "EPFLx+CycleVie1x"': 'product.key = "EPFLx+CycleVie1x"',
    'key: "HKPolyUx+OPT101x"': 'product.key = "HKPolyUx+OPT101x"',
    'key: "HKUx+Dentistry_6x"': 'product.key = "HKUx+Dentistry_6x"',
    'key: "HKUx+ESGx"': 'product.key = "HKUx+ESGx"',
    'key: "HKUx+Genderx"': 'product.key = "HKUx+Genderx"',
    'key: "HKUx+HKU_09x"': 'product.key = "HKUx+HKU_09x"',
    'key: "IsraelX+0109434x"': 'product.key = "IsraelX+0109434x"',
    'key:"IsraelX+1_2020"': 'product.key = "IsraelX+1_2020"',
    'key: "IsraelX+1_2020"': 'product.key = "IsraelX+1_2020"',
    'key: "IsraelX+1_2020+"': 'product.key = "IsraelX+1_2020"',
    'key:"IsraelX+CriticalThinking"': 'product.key = "IsraelX+CriticalThinking"',
    'key: "IsraelX+CriticalThinking"': 'product.key = "IsraelX+CriticalThinking"',
    'key: "IsraelX+DevPsy2019+"': 'product.key = "IsraelX+DevPsy2019"',
    'key: "IsraelX+gabi+"': 'product.key = "IsraelX+gabi"',
    'key: "IsraelX+ISLAM101x"': 'product.key = "IsraelX+ISLAM101x"',
    'key: "JesusCollegeCambridge+JCedX001"': 'product.key = "JesusCollegeCambridge+JCedX001"',
    'key:"LouvainX+Louv29x"': 'product.key = "LouvainX+Louv29x"',
    'key: "LouvainX+Louv32x"': 'product.key = "LouvainX+Louv32x"',
    'key: "LouvainX+Louv36x"': 'product.key = "LouvainX+Louv36x"',
    'key: "MITx+6.00.1x"': 'product.key = "MITx+6.00.1x"',
    'key: "MITx+6.00.2x"': 'product.key = "MITx+6.00.2x"',
    'key: "MITx+FIN.CFx"': 'product.key = "MITx+FIN.CFx"',
    'key: "RITx+THINK501x"': 'product.key = "RITx+THINK501x"',
    'key: "RWTHx+RITx"': 'product.key = "RWTHx+RITx"',
    'key: "SDGAcademyX+AMZN001"': 'product.key = "SDGAcademyX+AMZN001"',
    'key: "StanfordOnline+Eesley2022"': 'product.key = "StanfordOnline+Eesley2022"',
    'key: "Statistics.comX+MLOps1-AWS"': 'product.key = "Statistics.comX+MLOps1-AWS"',
    'key: "Statistics.comX+MLOps1-Azure"': 'product.key = "Statistics.comX+MLOps1-Azure"',
    'key: "Statistics.comX+MLOps2-AWS"': 'product.key = "Statistics.comX+MLOps2-AWS"',
    'key: "Statistics.comX+MLOps2-Azure"': 'product.key = "Statistics.comX+MLOps2-Azure"',
    'key: "TecdeMonterreyX+HC_AB.2x"': 'product.key = "TecdeMonterreyX+HC_AB.2x"',
    'key: "TecdeMonterreyX+HC_MFN.1x"': 'product.key = "TecdeMonterreyX+HC_MFN.1x"',
    'key: "TUGrazX+Pharm02"': 'product.key = "TUGrazX+Pharm02"',
    'key: "TUMx+AWMEx"': 'product.key = "TUMx+AWMEx"',
    'key: "TUMx+iLabx"': 'product.key = "TUMx+iLabx"',
    'key: "TUMx+LOOPx"': 'product.key = "TUMx+LOOPx"',
    'key:"TUMx+MYOAx"': 'product.key = "TUMx+MYOAx"',
    'key: "TUMx+MYOAx"': 'product.key = "TUMx+MYOAx"',
    'key: "UBCx+Biobank2x"': 'product.key = "UBCx+Biobank2x"',
    'key: "UC3Mx+IM.4X"': 'product.key = "UC3Mx+IM.4X"',
    'key: "UQx+ACE101x"': 'product.key = "UQx+ACE101x"',
    'key: "UQx+ACE201x"': 'product.key = "UQx+ACE201x"',
    'key: "UQx+BUSLEAD1x"': 'product.key = "UQx+BUSLEAD1x"',
    'key: "UQx+BUSLEAD2x"': 'product.key = "UQx+BUSLEAD2x"',
    'key: "UQx+BUSLEAD3x"': 'product.key = "UQx+BUSLEAD3x"',
    'key: "UQx+BUSLEAD4x"': 'product.key = "UQx+BUSLEAD4x"',
    'key: "UQx+BUSLEAD5x"': 'product.key = "UQx+BUSLEAD5x"',
    'key: "UQx+CALDCOMM1x"': 'product.key = "UQx+CALDCOMM1x"',
    'key: "UQx+CORPINN1x"': 'product.key = "UQx+CORPINN1x"',
    'key: "UQx+CORPINN2x"': 'product.key = "UQx+CORPINN2x"',
    'key: "UQx+CORPINN3x"': 'product.key = "UQx+CORPINN3x"',
    'key: "UQx+CORPINN4x"': 'product.key = "UQx+CORPINN4x"',
    'key:"UQx+CORPINN5x"': 'product.key = "UQx+CORPINN5x"',
    'key: "UQx+DEEPx"': 'product.key = "UQx+DEEPx"',
    'key: "UQx+Employ101x"': 'product.key = "UQx+Employ101x"',
    'key: "UQx+Teams101x"': 'product.key = "UQx+Teams101x"',
    'key: "UQx+Write101x"': 'product.key = "UQx+Write101x"',
    'key: "USMx+GSC100"': 'product.key = "USMx+GSC100"',
    'key: "W3Cx+JS.0x"': 'product.key = "W3Cx+JS.0x"',
    'key: "WasedaX+PSD111x"': 'product.key = "WasedaX+PSD111x"',
    'key: "WasedaX+SIP111x"': 'product.key = "WasedaX+SIP111x"',
    'key: ("AdelaideX+EthicalAIProfX")': 'product.key = "AdelaideX+EthicalAIProfX"',
    'key: ("DelftX+AIfE6x" OR "DelftX+BMI.2x" OR "DelftX+MED01x")':
    '(product.key = "DelftX+AIfE6x" or product.key = "DelftX+BMI.2x" or product.key = "DelftX+MED01x")',
    'key: ("UChicagoX+QCS11000+1T2025a" OR "UChicagoX+QCS12000+1T2025a" OR "UChicagoX+QCS13000+1T2025a")':
    '(variant.key = "course-v1:UChicagoX+QCS11000+1T2025a" or variant.key = "course-v1:UChicagoX+QCS12000+1T2025a"'
    ' or variant.key = "course-v1:UChicagoX+QCS13000+1T2025a")',
}


class Status:
    """Health statuses."""
    OK = 'OK'
    UNAVAILABLE = 'UNAVAILABLE'


class UnavailabilityMessage:
    """Messages to be logged when services are unavailable."""
    DATABASE = 'Unable to connect to database'
    LMS = 'Unable to connect to LMS'


class ProxyClassDiscountType(Enum):
    """Enumeration of discount types in the proxy class."""

    PERCENTAGE = "ecommerce.programs.benefits.PercentageDiscountBenefitWithoutRange"
    ABSOLUTE = "ecommerce.programs.benefits.AbsoluteDiscountBenefitWithoutRange"
