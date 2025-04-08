"""Constants core to the ecommerce app."""

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

COURSE_DISCOUNT_DEFAULT_SORT_ORDER = 0.00000001
PROGRAM_DISCOUNT_DEFAULT_SORT_ORDER = 0.0000000000001
PROGRAM_OFFER_DEFAULT_SORT_ORDER = 0.000000000000000001

DEFAULT_PRODUCT_CATEGORY = 'other'

LEGACY_CATEGORY_TO_CT_CATEGORY_MAPPING = {
    'affiliate-promotion': 'affiliate-promotion',
    'b2b-affiliate-promotion': 'b2b-affiliate-promotion',
    'bulk-enrollment': 'bulk-enrollment-prepay',
    'bulk-enrollment-integration': 'bulk-enrollment-prepay',
    'bulk-enrollment-prepay': 'bulk-enrollment-prepay',
    'bulk-enrollment-upon-redemption': 'bulk-enrollment-upon-redemption',
    'connected': 'other',
    'course-promotion': 'other',  # TODO: update this based on reply from cmelo
    'customer-service': 'customer-service',
    'edx-employee-request': 'other',
    'financial-assistance': 'financial-assistance',
    'geography-promotion': 'marketing-other',
    'marketing-other': 'marketing-other',
    'marketing-partner-promotion': 'marketing-other',
    'on-campus-learners': 'on-campus-learners',
    'other': 'other',
    'partner-no-rev-orap': 'other',  # TODO: update this based on reply from cmelo
    'partner-no-rev-prepay': 'partner-no-rev-prepay',
    'partner-no-rev-rap': 'other',  # TODO: update this based on reply from cmelo
    'partner-no-rev-upon-redemption': 'partner-no-rev-prepay',
    'retention-promotion': 'marketing-other',
    'scholarship': 'other',
    'security-disclosure-reward': 'other',
    'services-other': 'customer-service',
    'support-other': 'customer-service',
    'upsell-promotion': 'marketing-other'
}

KEY_TO_PREDICATE_DICT = {
    'key: ("AlaskaX+GRANT1x" OR "AlaskaX+GRANT2x" OR "AlaskaX+GRANT3x")':
    'product.key in ("AlaskaX+GRANT3x", "AlaskaX+GRANT2x", "AlaskaX+GRANT1x") ',
    'key: ("MITx+CTL.SC0x" OR "MITx+CTL.SC1x" OR "MITx+CTL.SC2x" OR "MITx+CTL.SC3x" OR "MITx+CTL.SC4x")':
    'product.key in ("MITx+CTL.SC0x", "MITx+CTL.SC1x", "MITx+CTL.SC2x", "MITx+CTL.SC3x", "MITx+CTL.SC4x") ',
    'key: "W3Cx+JS.0x"': 'product.key in ("W3Cx+JS.0x") ',
    'key: "RICEx+RiceSBE01"': 'product.key in ("RICEx+RiceSBE01") ',
    'key: "Statistics.comX+MLOps2-GCP"': 'product.key in ("Statistics.comX+MLOps2-GCP") ',
    'key:"IsraelX+CriticalThinking"': 'product.key in ("IsraelX+CriticalThinking") ',
    'key: ("HP+HPGG01.en" OR "HP+HPGG01.es" OR "HP+HPGG02.en" OR "HP+HPGG03.en" '
    'OR "HP+HPGG01.ar" OR "HP+HPGG02.ar" OR "HP+HPGG02.es" OR "HP+HPGG03.ar" '
    'OR "HP+HPGG03.es" OR "HP+HPGG04.en")':
    'product.key in ("HP+HPGG01.en", "HP+HPGG01.es", "HP+HPGG02.en",'
    ' "HP+HPGG03.en", "HP+HPGG01.ar", "HP+HPGG02.ar", "HP+HPGG02.es", '
    '"HP+HPGG03.ar", "HP+HPGG03.es", "HP+HPGG04.en")',
    'key: ("GalileoX+EticaIA_01" OR "GalileoX+MM_01" OR "GalileoX+GalileoXAI002")': ''
    'product.key in ("GalileoX+EticaIA_01", "GalileoX+MM_01", "GalileoX+GalileoXAI002")',
    'key: "DelftX+AIfE5x"': 'product.key in ("DelftX+AIfE5x")',
    'key: "Statistics.comX+MLOps1-GCP"': 'product.key in ("Statistics.comX+MLOps1-GCP")',
    'key: "UQx+Employ101x"': 'product.key in ("UQx+Employ101x")',
    'key: "WasedaX+SIP111x"': 'product.key in ("WasedaX+SIP111x")',
    'key: "UQx+CORPINN2x"': 'product.key in ("UQx+CORPINN2x")',
    'key: "TUMx+LOOPx"': 'product.key in ("TUMx+LOOPx")',
    'key: "UQx+CORPINN3x"': 'product.key in ("UQx+CORPINN3x")',
    'key:(StudioX OR VideoX OR StudioAdv1 OR BlendedX OR edX101 OR '
    'BuildWedX OR RunningWedX OR DesignWedX OR BuildWedXNEW OR RunWedXNEW)':
    'product.key in ("edX+RunWedXNEW", "edX+DesignWedX", "edX+StudioAdv1", '
    '"edX+VideoX", "edX+edX101", "edX+RunningWedX", "edX+BlendedX", "edX+StudioX")',
    'key: "UC3Mx IM.2-ESx"': 'product.key in ("UC3Mx+IM.2-ESx")',
    'key: (lead1x)': 'product.key in ("HarvardX+LEAD1x")',
    'key: ("AdelaideX+RiskX" OR "AdelaideX+Project101x" OR "AdelaideX+Entrep101X")':
    'product.key in ("AdelaideX+Entrep101X", "AdelaideX+Project101x", "AdelaideX+RiskX")',
    'key: "DelftX+QTM4x+2T2024"': 'product.key in ("DelftX+QTM4x+2T2024")',
    'key: "UQx+BUSLEAD1x"': 'product.key in ("UQx+BUSLEAD1x")',
    'key: "AlaskaX+DODGS-402"': 'product.key in ("AlaskaX+DODGS-402")',
    'key: ("AdelaideX+PolyTraX" OR "AdelaideX+SpecTraX" OR "AdelaideX+DiffTraX"'
    ' OR "AdelaideX+InteTraX" OR "AdelaideX+ProbTraX" OR "AdelaideX+StatTraX"'
    ' OR "AdelaideX+MathTrackX")':
    'product.key in ("AdelaideX+PolyTraX", "AdelaideX+SpecTraX", '
    '"AdelaideX+DiffTraX", "AdelaideX+InteTraX", "AdelaideX+ProbTraX", '
    '"AdelaideX+StatTraX", "AdelaideX+MathTrackX")',
    'key: "StanfordOnline+Eesley2022"': 'product.key in ("StanfordOnline+Eesley2022")',
    'key: "LouvainX+Louv36x"': 'product.key in ("LouvainX+Louv36x")',
    'key: ("UAMx+Griegox" OR "UAMx+Griego1.5x")': 'product.key in ("UAMx+Griegox", "UAMx+Griego1.5x")',
    'key: "TecdeMonterreyX+HC_MFN.1x"': 'product.key in ("TecdeMonterreyX+HC_MFN.1x")',
    'key: "edX+BC-OC-ai"': 'product.key in ("edX+BC-OC-ai")',
    'key: "HKUx+HKU_09x"': 'product.key in ("HKUx+HKU_09x")',
    'key:("MITx+6.431x" OR "MITx+6.86x" OR "MITx+18.6501x" '
    'OR "MITx+6.419x" OR "MITx+14.310Fx" OR "MITx+DS.CFx")':
    'product.key in ("MITx+6.431x" , "MITx+6.86x",  "MITx+18.6501x", '
    '"MITx+6.419x", "MITx+14.310Fx", "MITx+DS.CFx")',
    'key: "HKPolyUx+OPT101x"': 'product.key in ("HKPolyUx+OPT101x")',
    'key: ("TecdeMonterreyX+CT01I.x" OR "TecdeMonterreyX+MMLO01I.x" '
    'OR "TecdeMonterreyX+MMLF01I.x")':
    'product.key in ("TecdeMonterreyX+CT01I.x", "TecdeMonterreyX+MMLO01I.x", "TecdeMonterreyX+MMLF01I.x")',
    'key: "UQx+BUSLEAD4x"': 'product.key in ("UQx+BUSLEAD4x")',
    'key:"UQx+CORPINN5x"': 'product.key in ("UQx+CORPINN5x")',
    'key: "BerkeleyX+GG201x"': 'product.key in ("BerkeleyX+GG201x")',
    'key: "RICEx+RiceSBE02"': 'product.key in ("RICEx+RiceSBE02")',
    'key: "TUMx+iLabx"': 'product.key in ("TUMx+iLabx")',
    'key: ("TecdeMonterreyX+CT01I.x" OR "TecdeMonterreyX+MMEC01I.x" OR '
    '"TecdeMonterreyX+MMLF01I.x" OR "TecdeMonterreyX+MMSE01I.x" OR'
    ' "TecdeMonterreyX+MMSS01I.x" OR "TecdeMonterreyX+MMLO01I.x")':
    'product.key in ("TecdeMonterreyX+CT01I.x", "TecdeMonterreyX+MMEC01I.x",'
    ' "TecdeMonterreyX+MMLF01I.x", "TecdeMonterreyX+MMSE01I.x",'
    ' "TecdeMonterreyX+MMSS01I.x", "TecdeMonterreyX+MMLO01I.x")',
    'key: "AlaskaX+DODGS-400"': 'product.key in ("AlaskaX+DODGS-400")',
    'key: "BayreuthX+ubt205mun"': 'product.key in ("BayreuthX+ubt205mun")',
    'key: "TUGrazX+EMC1"': 'product.key in ("TUGrazX+EMC1")',
    'key: "UQx+CALDCOMM1x"': 'product.key in ("UQx+CALDCOMM1x")',
    'key: "DelftX+OS101x"': 'product.key in ("DelftX+OS101x")',
    'key: ("UTAustinX+FINTECH-OVERVIEW" OR "UTAustinX+FINTECH-BT" OR'
    ' "UTAustinX+FINTECH-ML" OR "UTAustinX+FINTECH-IOT")':
    'product.key in ("UTAustinX+FINTECH-OVERVIEW", "UTAustinX+FINTECH-BT",'
    ' "UTAustinX+FINTECH-ML", "UTAustinX+FINTECH-IOT")',
    'key:"IsraelX+1_2020"': 'product.key in ("IsraelX+1_2020")',
    'key: "DelftX+eCARS1x+2T2024"': 'product.key in ("DelftX+eCARS1x+2T2024")',
    'key: ("DelftX+PV1Ex" OR "DelftX+PV2Ex" OR "DelftX+PV3Ex" OR "DelftX+PV4Ex")':
    'product.key in ("DelftX+PV1Ex", "DelftX+PV2Ex", "DelftX+PV3Ex", "DelftX+PV4Ex")',
    'key: "UQx+ACE201x"': 'product.key in ("UQx+ACE201x")',
    'key: "UQx+BUSLEAD5x"': 'product.key in ("UQx+BUSLEAD5x")',
    'key: "DECx+B101Cx2"': 'product.key in ("DECx+B101Cx2")',
    'key:("ColumbiaX+CU.OC.AI001" OR "ColumbiaX+CU.OC.AI002")':
    'product.key in ("ColumbiaX+CU.OC.AI001", "ColumbiaX+CU.OC.AI002")',
    'key: "LouvainX+Louv32x"': 'product.key in ("LouvainX+Louv32x")',
    'key: "AlaskaX+SPRT1x"': 'product.key in ("AlaskaX+SPRT1x")',
    'key: "TUMx+MYOAx"': 'product.key in ("TUMx+MYOAx")',
    'key: "MITx+15.516x+3T2024"': 'variant.key in ("course-v1:MITx+15.516x+3T2024")',
    'key: "DelftX+OS101x+"': 'product.key in ("DelftX+OS101x")',
    'key: "UQx+Teams101x"': 'product.key in ("UQx+Teams101x")',
    'key: "TUGrazX+Pharm02"': 'product.key in ("TUGrazX+Pharm02")',
    'key: "MITx+6.00.2x"': 'product.key in ("MITx+6.00.2x")',
    'key: "UBCx+Biobank2x"': 'product.key in ("UBCx+Biobank2x")',
    'key: "AlaskaX+DODGS-401"': 'product.key in ("AlaskaX+DODGS-401")',
    'key: ("AlaskaX+DODGS-400" OR "AlaskaX+DODGS-401" OR "AlaskaX+DODGS-402")':
    'product.key in ("AlaskaX+DODGS-400", "AlaskaX+DODGS-401", "AlaskaX+DODGS-402")',
    'key: "AlaskaX+MAKE1x"': 'product.key in ("AlaskaX+MAKE1x")',
    'key: "Teams101x"': 'product.key in ("UQx+Teams101x")',
    'key: "AlaskaX+SPRT3x"': 'product.key in ("AlaskaX+SPRT3x")',
    'key: "CurtinX+NSSI1x"': 'product.key in ("CurtinX+NSSI1x")',
    'key: ("UBCx+Biobank1x" OR "UBCx+Biobank2x")':
    'product.key in ("UBCx+Biobank1x", "UBCx+Biobank2x")',
    'key: "DelftX+eCARS2x+2T2024"': 'variant.key in ("course-v1:DelftX+eCARS2x+2T2024")',
    'key: "AlaskaX+AI01x"': 'product.key in ("AlaskaX+AI01x")',
    'key: "JesusCollegeCambridge+JCedX001"': 'product.key in ("JesusCollegeCambridge+JCedX001")',
    'key: "UQx+ACE101x"': 'product.key in ("UQx+ACE101x")',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_AB.2x")':
    'product.key in ("TecdeMonterreyX+HC_CDE.1x", "TecdeMonterreyX+HC_AB.2x")',
    'key: "AlaskaX+UAS1x"': 'product.key in ("AlaskaX+UAS1x")',
    'key: "UQx+CORPINN4x"': 'product.key in ("UQx+CORPINN4x")',
    'key: "HKUx+Dentistry_6x"': 'product.key in ("HKUx+Dentistry_6x")',
    'key: "UC3Mx IM.1x"': 'product.key in ("UC3Mx+IM.1x")',
    'key: "DelftX+AIfE3x+3T2024"': 'variant.key in ("course-v1:DelftX+AIfE3x+3T2024")',
    'key: "DelftX+TUDF-FE01x"': 'product.key in ("DelftX+TUDF-FE01x")',
    'key: "UQx+BUSLEAD2x"': 'product.key in ("UQx+BUSLEAD2x")',
    'key: ("TUGrazX+SCS1" OR "TUGrazX+SCS2" OR "TUGrazX+SCS3" '
    'OR "TUGrazX+SCS4" OR "TUGrazX+SCS5" OR "TUGrazX+SCS6")':
    'product.key in ("TUGrazX+SCS1", "TUGrazX+SCS2", "TUGrazX+SCS3", '
    '"TUGrazX+SCS4","TUGrazX+SCS5", "TUGrazX+SCS6")',
    'key: "IsraelX+CriticalThinking"': 'product.key in ("IsraelX+CriticalThinking")',
    'key: "Statistics.comX+MLOps2-AWS"': 'product.key in ("Statistics.comX+MLOps2-AWS")',
    'key: "DECx+DA101Cx1"': 'product.key in ("DECx+DA101Cx1")',
    'key: ("MITx+DS.CFx" OR "MITx+6.431x" OR "MITx+6.86x" '
    'OR "MITx+18.6501x" OR "MITx+6.419x" OR "MITx+IDS.S24x" '
    'OR "MITx+14.310Fx")':
    'product.key in ("MITx+DS.CFx", "MITx+6.431x", "MITx+6.86x", '
    '"MITx+18.6501x", "MITx+6.419x", "MITx+IDS.S24x", "MITx+14.310Fx")',
    'key: ("DelftX+QTM1x" OR "DelftX+QTM2x" OR "DelftX+QTM3x")':
    'product.key in ("DelftX+QTM1x", "DelftX+QTM2x", "DelftX+QTM3x")',
    'key: "TUMx+AWMEx"': 'product.key in ("TUMx+AWMEx")',
    'key: "UQx+DEEPx"': 'product.key in ("UQx+DEEPx")',
    'key: ("DECx+B101Cx1" OR "DECx+B101Cx2" OR "DECx+DA101Cx1" OR "DECx+DA101Cx2")':
    'product.key in ("DECx+B101Cx1", "DECx+B101Cx2", "DECx+DA101Cx1", "DECx+DA101Cx2")',
    'key: "IsraelX+0109434x"': 'product.key in ("IsraelX+0109434x")',
    'key: ("DelftX+OS101x+1T2025" OR "DelftX+MathMod1x+1T2025" OR "DelftX+OT.1x+1T2025")':
    'variant.key in ("course-v1:DelftX+OT.1x+1T2025", '
    '"course-v1:DelftX+MathMod1x+1T2025", "course-v1:DelftX+OS101x+1T2025")',
    'key: "UQx+Write101x"': 'product.key in ("UQx+Write101x")',
    'key: "IsraelX+1_2020"': 'product.key in ("IsraelX+1_2020")',
    'key: ("TecdeMonterreyX+HC_AB.2x" OR "TecdeMonterreyX+HC_MFN.1x")':
    'product.key in ("TecdeMonterreyX+HC_AB.2x", "TecdeMonterreyX+HC_MFN.1x")',
    'key: "DelftX+OS101x+1T2025"': 'variant.key in ("course-v1:DelftX+OS101x+1T2025")',
    'key: "HKUx+Genderx"': 'product.key in ("HKUx+Genderx")',
    'key:"AlaskaX+GIS1x"': 'product.key in ("AlaskaX+GIS1x")',
    'key: ("IsraelX+MBSE101" OR "IsraelX+MBSE102")':
    'product.key in ("IsraelX+MBSE101", "IsraelX+MBSE102")',
    'key:"TUMx+MYOAx"': 'product.key in ("TUMx+MYOAx")',
    'key: ("RiskX" OR "Entrep101x" OR "Project101x")':
    'product.key in ("AdelaideX+Project101x", "AdelaideX+RiskX", "AdelaideX+Entrep101X")',
    'key: ("IsraelX+CONVERT" OR "IsraelX+resilience911" OR'
    ' "IsraelX+KAB1010x" OR "IsraelX+EPS1x" OR "IsraelX+WECS")':
    'product.key in ("IsraelX+CONVERT", "IsraelX+resilience911",'
    ' "IsraelX+KAB1010x", "IsraelX+EPS1x", "IsraelX+WECS")',
    'key: "SDGAcademyX+AMZN001"': 'product.key in ("SDGAcademyX+AMZN001")',
    'key: "RITx+THINK501x"': 'product.key in ("RITx+THINK501x")',
    'key: "UC3Mx+IM.3x"': 'product.key in ("UC3Mx+IM.3x")',
    'key: "AdelaideX+Project101x"': 'product.key in ("AdelaideX+Project101x")',
    'key: "IsraelX+gabi+"': 'product.key in ("IsraelX+gabi")',
    'key:"LouvainX+Louv29x"': 'product.key in ("LouvainX+Louv29x")',
    'key: ("TecdeMonterreyX+HC_AB.2x")': 'product.key in ("TecdeMonterreyX+HC_AB.2x")',
    'key: ("TAUx+Viruses101" OR "TAUx+Viruses102")':
    'product.key in ("TAUx+Viruses101", "TAUx+Viruses102")',
    'key: "UQx+CORPINN1x"': 'product.key in ("UQx+CORPINN1x")',
    'key:"DelftX+OS101x"': 'product.key in ("DelftX+OS101x")',
    'key: ("AdelaideX+RiskX" OR "AdelaideX+Entrep101X" OR "AdelaideX+Project101x")':
    'product.key in ("AdelaideX+RiskX", "AdelaideX+Entrep101X", "AdelaideX+Project101x")',
    'key: ("DelftX+PV1x" OR "DelftX+PV2x" OR "DelftX+PV3x" OR "DelftX+PV4x")':
    'product.key in ("DelftX+PV1x", "DelftX+PV2x", "DelftX+PV3x", "DelftX+PV4x")',
    'key: ("DelftX+AIfE5x+3T2024" OR "DelftX+AIfE6x+3T2024")':
    'variant.key in ("course-v1:DelftX+AIfE6x+3T2024", "course-v1:DelftX+AIfE5x+3T2024" )',
    'key: "DelftX+MDRP1x"': 'product.key in ("DelftX+MDRP1x")',
    'key: "DECx+CDAA1.3x"': 'product.key in ("DECx+CDAA1.3x")',
    'key: "EPFLx+CycleVie1x"': 'product.key in ("EPFLx+CycleVie1x")',
    'key:(*)': '',
    'key:(StudioX BlendedX edX101 VideoX StudioAdv1)':
    'product.key in ("edX+BlendedX", "edX+edX101", '
    '"edX+StudioX", "edX+VideoX",  "edX+StudioAdv1" )',
    'key: ("AlaskaX+GIS1x" OR "AlaskaX+GIS2x" OR "AlaskaX+GIS3x" OR "AlaskaX+RSW1")':
    'product.key in ("AlaskaX+GIS1x", "AlaskaX+GIS2x", "AlaskaX+GIS3x", "AlaskaX+RSW1")',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_MRL.2x" OR "TecdeMonterreyX+EGT-TD1x" )':
    'product.key in ("TecdeMonterreyX+HC_CDE.1x", "TecdeMonterreyX+HC_MRL.2x", "TecdeMonterreyX+EGT-TD1x")',
    'key:("6.419x" or "6.86x" or "DS.CFx" or "14.310Fx" or "6.431x" or "18.6501x")':
    'product.key in ("MITx+6.86x", "MITx+14.310Fx", "MITx+DS.CFx", "MITx+6.419x", "MITx+18.6501x", "MITx+6.431x")',
    'key: "Statistics.comX+MLOps1-Azure"': 'product.key in ("Statistics.comX+MLOps1-Azure")',
    'key: ("15.415.1x/3T2024" OR "15.415.2x/2T2024" OR "15.516x/3T2024" OR "15.455x/1T2025")':
    'variant.key in ("course-v1:MITx+15.455x+1T2025", '
    '"course-v1:MITx+15.516x+3T2024", "course-v1:MITx+15.415.1x+3T2024" )',
    'key: "DelftX+QTM2x+2T2024"': 'product.key in ("DelftX+QTM2x+2T2024")',
    'key: "MITx+6.00.1x"': 'product.key in ("MITx+6.00.1x")',
    'key: ("AlaskaX+UAS1x" OR "AlaskaX+UAS2x")':
    'product.key in ("AlaskaX+UAS1x", "AlaskaX+UAS2x")',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_PEA.2x" '
    'OR "TecdeMonterreyX+HC_IFA.1x" OR "TecdeMonterreyX+HC_MRL.2x")':
    'product.key in ("TecdeMonterreyX+HC_CDE.1x", '
    '"TecdeMonterreyX+HC_PEA.2x", "TecdeMonterreyX+HC_IFA.1x", "TecdeMonterreyX+HC_MRL.2x")',
    'key: ("UCx+GEO03.1ucX" OR"UCx+GEO04.2ucX")': 'product.key in ("UCx+GEO03.1ucX", "UCx+GEO04.2ucX")',
    'key: "RWTHx+RITx"': 'product.key in ("RWTHx+RITx")',
    'key: "UQx+BUSLEAD3x"': 'product.key in ("UQx+BUSLEAD3x")',
    'key: "CGI_U+CGIU.1x"': 'product.key in ("CGI_U+CGIU.1x")',
    'key: "WasedaX+PSD111x"': 'product.key in ("WasedaX+PSD111x")',
    'key: "UC3Mx+IM.4X"': 'product.key in ("UC3Mx+IM.4X")',
    'key: "HKUx+ESGx"': 'product.key in ("HKUx+ESGx")',
    'key: "Statistics.comX+MLOps2-Azure"': 'product.key in ("Statistics.comX+MLOps2-Azure")',
    'key: "DA101Cx2"': 'product.key in ("DECx+DA101Cx2")',
    'key: "WellesleyX+APIta.2023x"': 'product.key in ("WellesleyX+APIta.2023x")',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_IFA.1x" '
    'OR "TecdeMonterreyX+HC_MFN.1x" OR "TecdeMonterreyX+HC_PEA.2x" '
    'OR "TecdeMonterreyX+HC_AB.2x" OR "TecdeMonterreyX+HC_MRL.2x")':
    'product.key in ("TecdeMonterreyX+HC_CDE.1x", '
    '"TecdeMonterreyX+HC_IFA.1x", "TecdeMonterreyX+HC_MFN.1x", '
    '"TecdeMonterreyX+HC_PEA.2x", "TecdeMonterreyX+HC_AB.2x", "TecdeMonterreyX+HC_MRL.2x")',
    'key: ("TecdeMonterreyX+EGT-TD1x" OR "TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_MRL.2x")':
    'product.key in ("TecdeMonterreyX+EGT-TD1x", '
    '"TecdeMonterreyX+HC_CDE.1x", "TecdeMonterreyX+HC_MRL.2x")',
    'key: "Statistics.comX+MLOps1-AWS"': 'product.key in ("Statistics.comX+MLOps1-AWS")',
    'key: ("MITx+18.6501x" OR "MITx+6.419x" OR '
    '"MITx+6.431x" OR "MITx+6.86x" OR "MITx+DS.CFx" OR "MITx+IDS.S24x" OR "MITx+14.310Fx")':
    'product.key in ("MITx+18.6501x", "MITx+6.419x", '
    '"MITx+6.431x" OR "MITx+6.86x", "MITx+DS.CFx", "MITx+IDS.S24x", "MITx+14.310Fx")',
    'key: ("HP+HPGG01.en" OR "HP+HPGG01.es" OR '
    '"HP+HPGG02.en" OR "HP+HPGG03.en" OR "HP+HPGG01.ar" OR '
    '"HP+HPGG02.ar" OR "HP+HPGG02.es" OR "HP+HPGG03.ar" OR '
    '"HP+HPGG03.es" OR "HP+HPGG04.en" OR "HP+HPGG04.ar" OR "HP+HPGG04.es")':
    'product.key in  ("HP+HPGG01.en", "HP+HPGG01.es", "HP+HPGG02.en", '
    '"HP+HPGG03.en", "HP+HPGG01.ar", "HP+HPGG02.ar", "HP+HPGG02.es", '
    '"HP+HPGG03.ar", "HP+HPGG03.es", "HP+HPGG04.en", "HP+HPGG04.ar", "HP+HPGG04.es")',
    'key: "MITx+FIN.CFx"': 'product.key in  ("MITx+FIN.CFx")',
    'key: ("ChalmersX+ChM005x" OR "ChalmersX+ChM006x")': 'product.key in  '
    '("ChalmersX+ChM005x", "ChalmersX+ChM006x")',
    'key: ("TecdeMonterreyX+EGT-TD1x" OR "TecdeMonterreyX+HC_CDE.1x" '
    'OR "TecdeMonterreyX+HC_MRL.2x" OR "TecdeMonterreyX+MMEC01I.x" '
    'OR "TecdeMonterreyX+MMSE01I.x" OR "TecdeMonterreyX+MMSS01I.x")':
    'product.key in  ("TecdeMonterreyX+EGT-TD1x", "TecdeMonterreyX+HC_CDE.1x",'
    ' "TecdeMonterreyX+HC_MRL.2x", "TecdeMonterreyX+MMEC01I.x", '
    '"TecdeMonterreyX+MMSE01I.x", "TecdeMonterreyX+MMSS01I.x")',
    'key: "DECx+B101Cx1"': 'product.key in  ("DECx+B101Cx1")',
    'key: ("DelftX+AIfE5x" OR "DelftX+AIfE6x" OR "DelftX+AIfE3x")':
    'product.key in  ("DelftX+AIfE5x", "DelftX+AIfE6x", "DelftX+AIfE3x")',
    'key:(-IOT?x AND -MGT6203x AND -CSE6040x AND -ISYE6501x)':
    'product.key not in ("CurtinX+IOT2x", "CurtinX+IOT4x", '
    '"CurtinX+IOT3x", "CurtinX+IOT6x", "CurtinX+IOT5x", '
    '"CurtinX+IOT1x", "GTx+MGT6203x",  "GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x")',
    'key:(-MGT6203x AND -CSE6040x AND -ISYE6501x)':
    'product.key not in ("GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x")',
    'key:(-CORPFIN1x AND -CORPFIN2x AND -CORPFIN3x '
    'AND -CSE6040x AND -ISYE6501x AND -MGT6203x)':
    'product.key not in ("ColumbiaX+CORPFIN1x", '
    '"ColumbiaX+CORPFIN2x", "ColumbiaX+CORPFIN3x", '
    '"GTx+CSE6040x", "GTx+ISYE6501x", "GTx+MGT6203x" )',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x '
    'AND -15.415.2x AND -15.435x AND -15.455x AND -15.516x '
    'AND -TUMx+QPLS1x AND -TUMx+QPLS2x AND -TUMx+QPLS3x AND -TUMx+QPLS5x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+3.46.2x", "MITx+15.415.1x", '
    '"MITx+15.415.2x", "MITx+15.435x", "MITx+15.455x", "MITx+15.516x", '
    '"TUMx+QPLS1x", "TUMx+QPLS2x", "TUMx+QPLS3x", "TUMx+QPLS5x" )',
    'key:(-IOT6x AND -MGT6203x AND -CSE6040x AND -ISYE6501x AND -3.46.2x)':
    'product.key not in ("CurtinX+IOT6x", "GTx+MGT6203x", "GTx+CSE6040x", '
    '"GTx+ISYE6501x", "MITx+3.46.2x" )',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x AND -15.435x '
    'AND -15.455x AND -15.516x AND -QPLS1x AND -QPLS2x AND -QPLS3x AND -QPLS5x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+3.46.2x", "MITx+15.415.2x", '
    '"MITx+15.415.1x", "MITx+15.435x", "MITx+15.455x", "MITx+15.516x", '
    '"TUMx+QPLS1x", "TUMx+QPLS2x", "TUMx+QPLS3x", "TUMx+QPLS5x" )',
    'key:(-CORPFIN2x AND -CORPFIN3x AND -CORPFIN1x AND -CSE6040x AND '
    '-ISYE6501x AND -MGT6203x)':
    'product.key not in ("ColumbiaX+CORPFIN2x", "ColumbiaX+CORPFIN3x", '
    '"ColumbiaX+CORPFIN1x","GTx+CSE6040x", "GTx+ISYE6501x", "GTx+MGT6203x" )',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x AND -15.435x '
    'AND -15.455x AND -15.516x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+3.46.2x", "MITx+15.415.1x", '
    '"MITx+15.415.2x", "MITx+15.435x", "MITx+15.455x", "MITx+15.516x" )',
    'key:(-CSMM* AND -MGT6203x AND -CSE6040x AND -ISYE6501x)':
    'product.key not in ("ColumbiaX+CSMM.104x", '
    '"ColumbiaX+CSMM.103x", "ColumbiaX+CSMM.101x", '
    '"ColumbiaX+CSMM.102x", "MichiganX+CSMM.103x", '
    '"MichiganX+CSMM.104x", "GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x" )',
    'key:(-IOT6x AND -MGT6203x AND -CSE6040x AND '
    '-ISYE6501x AND -3.46.2x AND -15.415.1x AND -15.415.2x AND -15.435x AND -15.455x AND -15.516x)':
    'product.key not in ("CurtinX+IOT6x", "GTx+MGT6203x", '
    '"GTx+CSE6040x", "GTx+ISYE6501x", "MITx+3.46.2x", '
    '"MITx+15.415.1x", "MITx+15.415.2x", "MITx+15.435x", "MITx+15.455x", "MITx+15.516x")',
    'number:"Louv25.1x"': 'product.key in ("LouvainX+Louv25.1")',
    'number:(LEAD1x)': 'product.key in ("HarvardX+LEAD1x")',
    'number:Louv21x': 'product.key in ("LouvainX+Louv21x")',
    'number:Louv13x': 'product.key in ("LouvainX+Louv13x")',
    'number:URX37': 'product.key in ("URosarioX+URX37")',
    'number:"Louv25.2x"': 'product.key in ("LouvainX+Louv25.2x")',
    'number:Louv31x': 'product.key in ("LouvainX+Louv31x")',
    'number:(CONVERT OR resilience911 OR KAB1010x OR EPS1x OR WECS)':
    'product.key in ("IsraelX+EPS1x", "IsraelX+resilience911", '
    '"IsraelX+CONVERT", "IsraelX+KAB1010x", "IsraelX+WECS")',
    'key:("6.419x" or ""6.86x" or "DS.CFx" or "14.310Fx" or "6.431x" or "18.6501x")':
    'product.key in ("MITx+6.419x", "MITx+DS.CFx", "MITx+14.310Fx", "MITx+6.86x", '
    '"MITx+6.431x", "MITx+18.6501")',
    'start:[2023-01-01 TO 2061-12-31]': '',
    'key:(JuilliardOpenClassroom+JCx001+2T2017 OR '
    'JuilliardOpenClassroom+JCx002+3T2017 OR '
    'JuilliardOpenClassroom+JCx003+1T2017 OR '
    'JuilliardOpenClassroom+JC004+1T2017)':
    'variant.key in ("course-v1:JuilliardOpenClassroom+JCx001+2T2017",'
    '"course-v1:JuilliardOpenClassroom+JCx002+3T2017", '
    '"course-v1:JuilliardOpenClassroom+JCx003+1T2017",'
    '"course-v1:JuilliardOpenClassroom+JC004+1T2017")',
    'key: ("DelftX" AND "AIfE6x")': 'product.key in ("DelftX+AIfE6x")',
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
