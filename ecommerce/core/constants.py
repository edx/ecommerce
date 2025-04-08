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

KEY_TO_PREDICATE_DICT = {
    'key: ("AlaskaX+GRANT1x" OR "AlaskaX+GRANT2x" OR "AlaskaX+GRANT3x")':
    'product.key = "AlaskaX+GRANT3x" or product.key = "AlaskaX+GRANT2x" or product.key = "AlaskaX+GRANT1x" ',
    'key: ("MITx+CTL.SC0x" OR "MITx+CTL.SC1x" OR "MITx+CTL.SC2x" OR "MITx+CTL.SC3x" OR "MITx+CTL.SC4x")':
    'product.key = "MITx+CTL.SC0x" or product.key = "MITx+CTL.SC1x" or product.key = "MITx+CTL.SC2x" or product.key = "MITx+CTL.SC3x" or product.key = "MITx+CTL.SC4x" ',
    'key: "W3Cx+JS.0x"': 'product.key = "W3Cx+JS.0x"',
    'key: "RICEx+RiceSBE01"': 'product.key = "RICEx+RiceSBE01"',
    'key: "Statistics.comX+MLOps2-GCP"': 'product.key = "Statistics.comX+MLOps2-GCP"',
    'key:"IsraelX+CriticalThinking"': 'product.key = "IsraelX+CriticalThinking"',
    'key: ("HP+HPGG01.en" OR "HP+HPGG01.es" OR "HP+HPGG02.en" OR "HP+HPGG03.en" '
    'OR "HP+HPGG01.ar" OR "HP+HPGG02.ar" OR "HP+HPGG02.es" OR "HP+HPGG03.ar" '
    'OR "HP+HPGG03.es" OR "HP+HPGG04.en")':
    'product.key = "HP+HPGG01.en" OR product.key = "HP+HPGG01.es" OR product.key = "HP+HPGG02.en" OR product.key = "HP+HPGG03.en" OR product.key = "HP+HPGG01.ar" OR product.key = "HP+HPGG02.ar" OR product.key = "HP+HPGG02.es" OR product.key = "HP+HPGG03.ar" OR product.key = "HP+HPGG03.es" OR product.key = "HP+HPGG04.en"',
    'key: ("GalileoX+EticaIA_01" OR "GalileoX+MM_01" OR "GalileoX+GalileoXAI002")': ''
    'product.key = "GalileoX+EticaIA_01" OR product.key = "GalileoX+MM_01" OR product.key = "GalileoX+GalileoXAI002"',
    'key: "DelftX+AIfE5x"': 'product.key = "DelftX+AIfE5x"',
    'key: "Statistics.comX+MLOps1-GCP"': 'product.key = "Statistics.comX+MLOps1-GCP"',
    'key: "UQx+Employ101x"': 'product.key = "UQx+Employ101x"',
    'key: "WasedaX+SIP111x"': 'product.key = "WasedaX+SIP111x"',
    'key: "UQx+CORPINN2x"': 'product.key = "UQx+CORPINN2x"',
    'key: "TUMx+LOOPx"': 'product.key = "TUMx+LOOPx"',
    'key: "UQx+CORPINN3x"': 'product.key = "UQx+CORPINN3x"',
    'key:(StudioX OR VideoX OR StudioAdv1 OR BlendedX OR edX101 OR '
    'BuildWedX OR RunningWedX OR DesignWedX OR BuildWedXNEW OR RunWedXNEW)':
    'product.key = "edX+RunWedXNEW" or product.key = "edX+DesignWedX" or product.key = "edX+BuildWedX" or product.key = "edX+BuildWedXNEW" or product.key = "edX+StudioAdv1" or product.key = "edX+VideoX" or product.key = "edX+edX101" or product.key = "edX+RunningWedX" or product.key = "edX+BlendedX" or product.key = "edX+StudioX"',
    'key: "UC3Mx IM.2-ESx"': 'product.key = "UC3Mx+IM.2-ESx"',
    'key: (lead1x)': 'product.key = "HarvardX+LEAD1x"',
    'key: ("AdelaideX+RiskX" OR "AdelaideX+Project101x" OR "AdelaideX+Entrep101X")':
    'product.key = "AdelaideX+Entrep101X" or product.key = "AdelaideX+Project101x" or product.key = "AdelaideX+RiskX"',
    'key: "DelftX+QTM4x+2T2024"': 'variant.key = "course-v1:DelftX+QTM4x+2T2024"',
    'key: "UQx+BUSLEAD1x"': 'product.key = "UQx+BUSLEAD1x"',
    'key: "AlaskaX+DODGS-402"': 'product.key = "AlaskaX+DODGS-402"',
    'key: ("AdelaideX+PolyTraX" OR "AdelaideX+SpecTraX" OR "AdelaideX+DiffTraX"'
    ' OR "AdelaideX+InteTraX" OR "AdelaideX+ProbTraX" OR "AdelaideX+StatTraX"'
    ' OR "AdelaideX+MathTrackX")':
    'product.key = "AdelaideX+PolyTraX" or product.key = "AdelaideX+SpecTraX" or product.key = "AdelaideX+DiffTraX" or product.key = "AdelaideX+InteTraX" or product.key = "AdelaideX+ProbTraX" or product.key = "AdelaideX+StatTraX" or product.key = "AdelaideX+MathTrackX"',
    'key: "StanfordOnline+Eesley2022"': 'product.key = "StanfordOnline+Eesley2022"',
    'key: "LouvainX+Louv36x"': 'product.key = "LouvainX+Louv36x"',
    'key: ("UAMx+Griegox" OR "UAMx+Griego1.5x")': 'product.key = "UAMx+Griegox" or product.key = "UAMx+Griego1.5x"',
    'key: "TecdeMonterreyX+HC_MFN.1x"': 'product.key = "TecdeMonterreyX+HC_MFN.1x"',
    'key: "edX+BC-OC-ai"': 'product.key = "edX+BC-OC-ai"',
    'key: "HKUx+HKU_09x"': 'product.key = "HKUx+HKU_09x"',
    'key:("MITx+6.431x" OR "MITx+6.86x" OR "MITx+18.6501x" '
    'OR "MITx+6.419x" OR "MITx+14.310Fx" OR "MITx+DS.CFx")':
    'product.key = "MITx+6.431x" or product.key = "MITx+6.86x" or product.key = "MITx+18.6501x" or product.key = "MITx+6.419x" or product.key = "MITx+14.310Fx" or product.key = "MITx+DS.CFx"',
    'key: "HKPolyUx+OPT101x"': 'product.key = "HKPolyUx+OPT101x"',
    'key: ("TecdeMonterreyX+CT01I.x" OR "TecdeMonterreyX+MMLO01I.x" OR "TecdeMonterreyX+MMLF01I.x")':
    'product.key = "TecdeMonterreyX+CT01I.x" or product.key = "TecdeMonterreyX+MMLO01I.x" or product.key = "TecdeMonterreyX+MMLF01I.x"',
    'key: "UQx+BUSLEAD4x"': 'product.key = "UQx+BUSLEAD4x"',
    'key:"UQx+CORPINN5x"': 'product.key = "UQx+CORPINN5x"',
    'key: "BerkeleyX+GG201x"': 'product.key = "BerkeleyX+GG201x"',
    'key: "RICEx+RiceSBE02"': 'product.key = "RICEx+RiceSBE02"',
    'key: "TUMx+iLabx"': 'product.key = "TUMx+iLabx"',
    'key: ("TecdeMonterreyX+CT01I.x" OR "TecdeMonterreyX+MMEC01I.x" OR "TecdeMonterreyX+MMLF01I.x" OR "TecdeMonterreyX+MMSE01I.x" OR "TecdeMonterreyX+MMSS01I.x" OR "TecdeMonterreyX+MMLO01I.x")':
    'product.key = "TecdeMonterreyX+CT01I.x" or product.key = "TecdeMonterreyX+MMEC01I.x" or product.key = "TecdeMonterreyX+MMLF01I.x" or product.key = "TecdeMonterreyX+MMSE01I.x" or product.key = "TecdeMonterreyX+MMSS01I.x" or product.key = "TecdeMonterreyX+MMLO01I.x"',
    'key: "AlaskaX+DODGS-400"': 'product.key = "AlaskaX+DODGS-400"',
    'key: "BayreuthX+ubt205mun"': 'product.key = "BayreuthX+ubt205mun"',
    'key: "TUGrazX+EMC1"': 'product.key = "TUGrazX+EMC1"',
    'key: "UQx+CALDCOMM1x"': 'product.key = "UQx+CALDCOMM1x"',
    'key: "DelftX+OS101x"': 'product.key = "DelftX+OS101x"',
    'key: ("UTAustinX+FINTECH-OVERVIEW" OR "UTAustinX+FINTECH-BT" OR'
    ' "UTAustinX+FINTECH-ML" OR "UTAustinX+FINTECH-IOT")':
    'product.key = "UTAustinX+FINTECH-OVERVIEW" OR product.key = "UTAustinX+FINTECH-BT" OR product.key = "UTAustinX+FINTECH-ML" OR product.key = "UTAustinX+FINTECH-IOT"',
    'key:"IsraelX+1_2020"': 'product.key = "IsraelX+1_2020"',
    'key: "DelftX+eCARS1x+2T2024"': 'variant.key = "course-v1:DelftX+eCARS1x+2T2024"',
    'key: ("DelftX+PV1Ex" OR "DelftX+PV2Ex" OR "DelftX+PV3Ex" OR "DelftX+PV4Ex")':
    'product.key = "DelftX+PV1Ex" OR product.key = "DelftX+PV2Ex" OR product.key = "DelftX+PV3Ex" OR product.key = "DelftX+PV4Ex"',
    'key: "UQx+ACE201x"': 'product.key = "UQx+ACE201x"',
    'key: "UQx+BUSLEAD5x"': 'product.key = "UQx+BUSLEAD5x"',
    'key: "DECx+B101Cx2"': 'product.key = "DECx+B101Cx2"',
    'key:("ColumbiaX+CU.OC.AI001" OR "ColumbiaX+CU.OC.AI002")':
    'product.key = "ColumbiaX+CU.OC.AI001" OR product.key = "ColumbiaX+CU.OC.AI002"',
    'key: "LouvainX+Louv32x"': 'product.key = "LouvainX+Louv32x"',
    'key: "AlaskaX+SPRT1x"': 'product.key = "AlaskaX+SPRT1x"',
    'key: "TUMx+MYOAx"': 'product.key = "TUMx+MYOAx"',
    'key: "MITx+15.516x+3T2024"': 'variant.key = "course-v1:MITx+15.516x+3T2024"',
    'key: "DelftX+OS101x+"': 'product.key = "DelftX+OS101x"',
    'key: "UQx+Teams101x"': 'product.key = "UQx+Teams101x"',
    'key: "TUGrazX+Pharm02"': 'product.key = "TUGrazX+Pharm02"',
    'key: "MITx+6.00.2x"': 'product.key = "MITx+6.00.2x"',
    'key: "UBCx+Biobank2x"': 'product.key = "UBCx+Biobank2x"',
    'key: "AlaskaX+DODGS-401"': 'product.key = "AlaskaX+DODGS-401"',
    'key: ("AlaskaX+DODGS-400" OR "AlaskaX+DODGS-401" OR "AlaskaX+DODGS-402")':
    'product.key = "AlaskaX+DODGS-400" OR product.key = "AlaskaX+DODGS-401" OR product.key = "AlaskaX+DODGS-402"',
    'key: "AlaskaX+MAKE1x"': 'product.key = "AlaskaX+MAKE1x"',
    'key: "Teams101x"': 'product.key = "UQx+Teams101x"',
    'key: "AlaskaX+SPRT3x"': 'product.key = "AlaskaX+SPRT3x"',
    'key: "CurtinX+NSSI1x"': 'product.key = "CurtinX+NSSI1x"',
    'key: ("UBCx+Biobank1x" OR "UBCx+Biobank2x")':
    'product.key = "UBCx+Biobank1x" OR product.key = "UBCx+Biobank2x" ',
    'key: "DelftX+eCARS2x+2T2024"': 'variant.key = "course-v1:DelftX+eCARS2x+2T2024"',
    'key: "AlaskaX+AI01x"': 'product.key = "AlaskaX+AI01x"',
    'key: "JesusCollegeCambridge+JCedX001"': 'product.key = "JesusCollegeCambridge+JCedX001"',
    'key: "UQx+ACE101x"': 'product.key = "UQx+ACE101x"',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_AB.2x")':
    'product.key = "TecdeMonterreyX+HC_CDE.1x" OR product.key = "TecdeMonterreyX+HC_AB.2x"',
    'key: "AlaskaX+UAS1x"': 'product.key = "AlaskaX+UAS1x"',
    'key: "UQx+CORPINN4x"': 'product.key = "UQx+CORPINN4x"',
    'key: "HKUx+Dentistry_6x"': 'product.key = "HKUx+Dentistry_6x"',
    'key: "UC3Mx IM.1x"': 'product.key = "UC3Mx+IM.1x"',
    'key: "DelftX+AIfE3x+3T2024"': 'variant.key = "course-v1:DelftX+AIfE3x+3T2024"',
    'key: "DelftX+TUDF-FE01x"': 'product.key = "DelftX+TUDF-FE01x"',
    'key: "UQx+BUSLEAD2x"': 'product.key = "UQx+BUSLEAD2x"',
    'key: ("TUGrazX+SCS1" OR "TUGrazX+SCS2" OR "TUGrazX+SCS3" '
    'OR "TUGrazX+SCS4" OR "TUGrazX+SCS5" OR "TUGrazX+SCS6")':
    'product.key = "TUGrazX+SCS1" OR product.key = "TUGrazX+SCS2" OR product.key = "TUGrazX+SCS3" OR product.key = "TUGrazX+SCS4" OR product.key = "TUGrazX+SCS5" OR product.key = "TUGrazX+SCS6"',
    'key: "IsraelX+CriticalThinking"': 'product.key = "IsraelX+CriticalThinking"',
    'key: "Statistics.comX+MLOps2-AWS"': 'product.key = "Statistics.comX+MLOps2-AWS"',
    'key: "DECx+DA101Cx1"': 'product.key = "DECx+DA101Cx1"',
    'key: ("MITx+DS.CFx" OR "MITx+6.431x" OR "MITx+6.86x" '
    'OR "MITx+18.6501x" OR "MITx+6.419x" OR "MITx+IDS.S24x" '
    'OR "MITx+14.310Fx")':
    'product.key = "MITx+DS.CFx" OR product.key = "MITx+6.431x" OR product.key = "MITx+6.86x" OR product.key = "MITx+18.6501x" OR product.key = "MITx+6.419x" OR product.key = "MITx+IDS.S24x" OR product.key = "MITx+14.310Fx"',
    'key: ("DelftX+QTM1x" OR "DelftX+QTM2x" OR "DelftX+QTM3x")':
    'product.key = "DelftX+QTM1x" OR product.key = "DelftX+QTM2x" OR product.key = "DelftX+QTM3x"',
    'key: "TUMx+AWMEx"': 'product.key = "TUMx+AWMEx"',
    'key: "UQx+DEEPx"': 'product.key = "UQx+DEEPx"',
    'key: ("DECx+B101Cx1" OR "DECx+B101Cx2" OR "DECx+DA101Cx1" OR "DECx+DA101Cx2")':
    'product.key = "DECx+B101Cx1" OR product.key = "DECx+B101Cx2" OR product.key = "DECx+DA101Cx1" OR product.key = "DECx+DA101Cx2"',
    'key: "IsraelX+0109434x"': 'product.key = "IsraelX+0109434x"',
    'key: ("DelftX+OS101x+1T2025" OR "DelftX+MathMod1x+1T2025" OR "DelftX+OT.1x+1T2025")':
    'variant.key = "course-v1:DelftX+OT.1x+1T2025" OR variant.key = "course-v1:DelftX+MathMod1x+1T2025" OR variant.key = "course-v1:DelftX+OS101x+1T2025"',
    'key: "UQx+Write101x"': 'product.key = "UQx+Write101x"',
    'key: "IsraelX+1_2020"': 'product.key = "IsraelX+1_2020"',
    'key: ("TecdeMonterreyX+HC_AB.2x" OR "TecdeMonterreyX+HC_MFN.1x")':
    'product.key = "TecdeMonterreyX+HC_AB.2x" OR product.key = "TecdeMonterreyX+HC_MFN.1x"',
    'key: "DelftX+OS101x+1T2025"': 'variant.key = "course-v1:DelftX+OS101x+1T2025"',
    'key: "HKUx+Genderx"': 'product.key = "HKUx+Genderx"',
    'key:"AlaskaX+GIS1x"': 'product.key = "AlaskaX+GIS1x"',
    'key: ("IsraelX+MBSE101" OR "IsraelX+MBSE102")':
    'product.key = "IsraelX+MBSE101" OR product.key = "IsraelX+MBSE102"',
    'key:"TUMx+MYOAx"': 'product.key = "TUMx+MYOAx"',
    'key: ("RiskX" OR "Entrep101x" OR "Project101x")':
    'product.key = "AdelaideX+Project101x" OR product.key = "AdelaideX+RiskX" OR product.key = "AdelaideX+Entrep101X"',
    'key: ("IsraelX+CONVERT" OR "IsraelX+resilience911" OR'
    ' "IsraelX+KAB1010x" OR "IsraelX+EPS1x" OR "IsraelX+WECS")':
    'product.key = "IsraelX+CONVERT" OR product.key = "IsraelX+resilience911" OR product.key = "IsraelX+KAB1010x" OR product.key = "IsraelX+EPS1x" OR product.key = "IsraelX+WECS"',
    'key: "SDGAcademyX+AMZN001"': 'product.key = "SDGAcademyX+AMZN001"',
    'key: "RITx+THINK501x"': 'product.key = "RITx+THINK501x"',
    'key: "UC3Mx+IM.3x"': 'product.key = "UC3Mx+IM.3x"',
    'key: "AdelaideX+Project101x"': 'product.key = "AdelaideX+Project101x"',
    'key: "IsraelX+gabi+"': 'product.key = "IsraelX+gabi"',
    'key:"LouvainX+Louv29x"': 'product.key = "LouvainX+Louv29x"',
    'key: ("TecdeMonterreyX+HC_AB.2x")': 'product.key = "TecdeMonterreyX+HC_AB.2x"',
    'key: ("TAUx+Viruses101" OR "TAUx+Viruses102")':
    'product.key = "TAUx+Viruses101" OR product.key = "TAUx+Viruses102"',
    'key: "UQx+CORPINN1x"': 'product.key = "UQx+CORPINN1x"',
    'key:"DelftX+OS101x"': 'product.key = "DelftX+OS101x"',
    'key: ("AdelaideX+RiskX" OR "AdelaideX+Entrep101X" OR "AdelaideX+Project101x")':
    'product.key = "AdelaideX+RiskX" OR product.key = "AdelaideX+Entrep101X" OR product.key = "AdelaideX+Project101x"',
    'key: ("DelftX+PV1x" OR "DelftX+PV2x" OR "DelftX+PV3x" OR "DelftX+PV4x")':
    'product.key = "DelftX+PV1x" OR product.key = "DelftX+PV2x" OR product.key = "DelftX+PV3x" OR product.key = "DelftX+PV4x"',
    'key: ("DelftX+AIfE5x+3T2024" OR "DelftX+AIfE6x+3T2024")':
    'variant.key = "course-v1:DelftX+AIfE6x+3T2024" OR variant.key = "course-v1:DelftX+AIfE5x+3T2024"',
    'key: "DelftX+MDRP1x"': 'product.key = "DelftX+MDRP1x"',
    'key: "DECx+CDAA1.3x"': 'product.key = "DECx+CDAA1.3x"',
    'key: "EPFLx+CycleVie1x"': 'product.key = "EPFLx+CycleVie1x"',
    'key:(*)': '',
    'key:(StudioX BlendedX edX101 VideoX StudioAdv1)':
    'product.key = "edX+BlendedX" OR product.key = "edX+edX101" OR product.key = "edX+StudioX" OR product.key = "edX+VideoX" OR product.key = "edX+StudioAdv1"',
    'key: ("AlaskaX+GIS1x" OR "AlaskaX+GIS2x" OR "AlaskaX+GIS3x" OR "AlaskaX+RSW1")':
    'product.key = "AlaskaX+GIS1x" OR product.key = "AlaskaX+GIS2x" OR product.key = "AlaskaX+GIS3x" OR product.key = "AlaskaX+RSW1"',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_MRL.2x" OR "TecdeMonterreyX+EGT-TD1x" )':
    'product.key = "TecdeMonterreyX+HC_CDE.1x" OR product.key = "TecdeMonterreyX+HC_MRL.2x" OR product.key = "TecdeMonterreyX+EGT-TD1x"',
    'key:("6.419x" or "6.86x" or "DS.CFx" or "14.310Fx" or "6.431x" or "18.6501x")':
    'product.key = "MITx+6.86x" OR product.key = "MITx+14.310Fx" OR product.key = "MITx+DS.CFx" OR product.key = "MITx+6.419x" OR product.key = "MITx+18.6501x" OR product.key = "MITx+6.431x"',
    'key: "Statistics.comX+MLOps1-Azure"': 'product.key = "Statistics.comX+MLOps1-Azure"',
    'key: ("15.415.1x/3T2024" OR "15.415.2x/2T2024" OR "15.516x/3T2024" OR "15.455x/1T2025")':
    'variant.key = "course-v1:MITx+15.455x+1T2025" OR variant.key = "course-v1:MITx+15.415.2x+2T2024" OR variant.key = "course-v1:MITx+15.516x+3T2024" OR variant.key = "course-v1:MITx+15.415.1x+3T2024"',
    'key: "DelftX+QTM2x+2T2024"': 'variant.key = "course-v1:DelftX+QTM2x+2T2024"',
    'key: "MITx+6.00.1x"': 'product.key = "MITx+6.00.1x"',
    'key: ("AlaskaX+UAS1x" OR "AlaskaX+UAS2x")':
    'product.key = "AlaskaX+UAS1x" OR product.key = "AlaskaX+UAS2x"',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_PEA.2x" '
    'OR "TecdeMonterreyX+HC_IFA.1x" OR "TecdeMonterreyX+HC_MRL.2x")':
    'product.key = "TecdeMonterreyX+HC_CDE.1x" OR product.key = "TecdeMonterreyX+HC_PEA.2x" OR product.key = "TecdeMonterreyX+HC_IFA.1x" OR product.key = "TecdeMonterreyX+HC_MRL.2x" ',
    'key: ("UCx+GEO03.1ucX" OR"UCx+GEO04.2ucX")': 'product.key = "UCx+GEO03.1ucX" OR product.key = "UCx+GEO04.2ucX"',
    'key: "RWTHx+RITx"': 'product.key = "RWTHx+RITx"',
    'key: "UQx+BUSLEAD3x"': 'product.key = "UQx+BUSLEAD3x"',
    'key: "CGI_U+CGIU.1x"': 'product.key = "CGI_U+CGIU.1x"',
    'key: "WasedaX+PSD111x"': 'product.key = "WasedaX+PSD111x"',
    'key: "UC3Mx+IM.4X"': 'product.key = "UC3Mx+IM.4X"',
    'key: "HKUx+ESGx"': 'product.key = "HKUx+ESGx"',
    'key: "Statistics.comX+MLOps2-Azure"': 'product.key = "Statistics.comX+MLOps2-Azure"',
    'key: "DA101Cx2"': 'product.key = "DECx+DA101Cx2"',
    'key: "WellesleyX+APIta.2023x"': 'product.key = "WellesleyX+APIta.2023x"',
    'key: ("TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_IFA.1x" '
    'OR "TecdeMonterreyX+HC_MFN.1x" OR "TecdeMonterreyX+HC_PEA.2x" '
    'OR "TecdeMonterreyX+HC_AB.2x" OR "TecdeMonterreyX+HC_MRL.2x")':
    'product.key = "TecdeMonterreyX+HC_CDE.1x" OR product.key = "TecdeMonterreyX+HC_IFA.1x" OR product.key = "TecdeMonterreyX+HC_MFN.1x" OR product.key = "TecdeMonterreyX+HC_PEA.2x" OR product.key = "TecdeMonterreyX+HC_AB.2x" OR product.key = "TecdeMonterreyX+HC_MRL.2x"',
    'key: ("TecdeMonterreyX+EGT-TD1x" OR "TecdeMonterreyX+HC_CDE.1x" OR "TecdeMonterreyX+HC_MRL.2x")':
    'product.key = "TecdeMonterreyX+EGT-TD1x" OR product.key = "TecdeMonterreyX+HC_CDE.1x" OR product.key = "TecdeMonterreyX+HC_MRL.2x"',
    'key: "Statistics.comX+MLOps1-AWS"': 'product.key = "Statistics.comX+MLOps1-AWS"',
    'key: ("MITx+18.6501x" OR "MITx+6.419x" OR '
    '"MITx+6.431x" OR "MITx+6.86x" OR "MITx+DS.CFx" OR "MITx+IDS.S24x" OR "MITx+14.310Fx")':
    'product.key = "MITx+18.6501x" OR product.key = "MITx+6.419x" OR product.key = "MITx+6.431x" OR product.key = "MITx+6.86x" OR product.key = "MITx+DS.CFx" OR product.key = "MITx+IDS.S24x" OR product.key = "MITx+14.310Fx"',
    'key: ("HP+HPGG01.en" OR "HP+HPGG01.es" OR '
    '"HP+HPGG02.en" OR "HP+HPGG03.en" OR "HP+HPGG01.ar" OR '
    '"HP+HPGG02.ar" OR "HP+HPGG02.es" OR "HP+HPGG03.ar" OR '
    '"HP+HPGG03.es" OR "HP+HPGG04.en" OR "HP+HPGG04.ar" OR "HP+HPGG04.es")':
    'product.key = "HP+HPGG01.en" OR product.key = "HP+HPGG01.es" OR product.key = "HP+HPGG02.en" OR product.key = "HP+HPGG03.en" OR product.key = "HP+HPGG01.ar" OR product.key = "HP+HPGG02.ar" OR product.key = "HP+HPGG02.es" OR product.key = "HP+HPGG03.ar" OR product.key = "HP+HPGG03.es" OR product.key = "HP+HPGG04.en" OR product.key = "HP+HPGG04.ar" OR product.key = "HP+HPGG04.es"',
    'key: "MITx+FIN.CFx"': 'product.key = "MITx+FIN.CFx"',
    'key: ("ChalmersX+ChM005x" OR "ChalmersX+ChM006x")': 'product.key = "ChalmersX+ChM005x" OR product.key = "ChalmersX+ChM006x"',
    'key: ("TecdeMonterreyX+EGT-TD1x" OR "TecdeMonterreyX+HC_CDE.1x" '
    'OR "TecdeMonterreyX+HC_MRL.2x" OR "TecdeMonterreyX+MMEC01I.x" '
    'OR "TecdeMonterreyX+MMSE01I.x" OR "TecdeMonterreyX+MMSS01I.x")':
    'product.key = "TecdeMonterreyX+EGT-TD1x" OR product.key = "TecdeMonterreyX+HC_CDE.1x" OR product.key = "TecdeMonterreyX+HC_MRL.2x" OR product.key = "TecdeMonterreyX+MMEC01I.x" OR product.key = "TecdeMonterreyX+MMSE01I.x" OR product.key = "TecdeMonterreyX+MMSS01I.x"',
    'key: "DECx+B101Cx1"': 'product.key = "DECx+B101Cx1"',
    'key: ("DelftX+AIfE5x" OR "DelftX+AIfE6x" OR "DelftX+AIfE3x")':
    'product.key = "DelftX+AIfE5x" OR product.key = "DelftX+AIfE6x" OR product.key = "DelftX+AIfE3x"',
    'key:(-IOT?x AND -MGT6203x AND -CSE6040x AND -ISYE6501x)':
    'product.key not in ("CurtinX+IOT2x",'
    ' "CurtinX+IOT4x", '
    '"CurtinX+IOT3x", "CurtinX+IOT6x", "CurtinX+IOT5x", '
    '"CurtinX+IOT1x", "GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x")',
    'key:(-MGT6203x AND -CSE6040x AND -ISYE6501x)':
    'product.key not in ("GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x")',
    'key:(-CORPFIN1x AND -CORPFIN2x AND -CORPFIN3x '
    'AND -CSE6040x AND -ISYE6501x AND -MGT6203x)':
    'product.key not in ("ColumbiaX+CORPFIN1x", '
    '"ColumbiaX+CORPFIN2x", "ColumbiaX+CORPFIN3x", '
    '"GTx+CSE6040x", "GTx+ISYE6501x", "GTx+MGT6203x" )',
    'key:(-IOT6x AND -MGT6203x AND -CSE6040x AND -ISYE6501x AND -3.46.2x)':
    'product.key not in ("CurtinX+IOT6x", "GTx+MGT6203x", "GTx+CSE6040x", '
    '"GTx+ISYE6501x", "MITx+3.46.2x" )',
    'key:(-CORPFIN2x AND -CORPFIN3x AND -CORPFIN1x AND -CSE6040x AND '
    '-ISYE6501x AND -MGT6203x)':
    'product.key not in ("ColumbiaX+CORPFIN2x", "ColumbiaX+CORPFIN3x", '
    '"ColumbiaX+CORPFIN1x","GTx+CSE6040x", "GTx+ISYE6501x", "GTx+MGT6203x" )',
    'key:(-CSMM* AND -MGT6203x AND -CSE6040x AND -ISYE6501x)':
    'product.key not in ("ColumbiaX+CSMM.104x", '
    '"ColumbiaX+CSMM.103x", "ColumbiaX+CSMM.101x", '
    '"ColumbiaX+CSMM.102x", "MichiganX+CSMM.103x", '
    '"MichiganX+CSMM.104x", "GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x" )',
    'number:"Louv25.1x"': 'product.key in ("LouvainX+Louv25.1")',
    'number:(LEAD1x)': 'product.key in ("HarvardX+LEAD1x")',
    'number:Louv21x': 'product.key in ("LouvainX+Louv21x")',
    'number:Louv13x': 'product.key in ("LouvainX+Louv13x")',
    'number:URX37': 'product.key in ("URosarioX+URX37")',
    'number:"Louv25.2x"': 'product.key in ("LouvainX+Louv25.2x")',
    'number:Louv31x': 'product.key in ("LouvainX+Louv31x")',
    'number:(CONVERT OR resilience911 OR KAB1010x OR EPS1x OR WECS)':
    'product.key = "IsraelX+EPS1x" or product.key = "IsraelX+resilience911" or product.key = "IsraelX+CONVERT" or product.key = "IsraelX+KAB1010x" or product.key = "IsraelX+WECS"',
    'key:("6.419x" or ""6.86x" or "DS.CFx" or "14.310Fx" or "6.431x" or "18.6501x")':
    'product.key = "MITx+6.419x" or product.key = "MITx+DS.CFx" or product.key = "MITx+14.310Fx" or product.key = "MITx+6.86x" or product.key = "MITx+6.431x" or product.key = "MITx+18.6501"',
    'start:[2023-01-01 TO 2061-12-31]': '',
    'key:(JuilliardOpenClassroom+JCx001+2T2017 OR JuilliardOpenClassroom+JCx002+3T2017 OR JuilliardOpenClassroom+JCx003+1T2017 OR JuilliardOpenClassroom+JC004+1T2017)':
    'variant.key = "course-v1:JuilliardOpenClassroom+JCx001+2T2017" or variant.key = "course-v1:JuilliardOpenClassroom+JCx002+3T2017" or variant.key = "course-v1:JuilliardOpenClassroom+JCx003+1T2017" or variant.key = "course-v1:JuilliardOpenClassroom+JC004+1T2017"',
    'key: ("DelftX" AND "AIfE6x")': 'product.key = "DelftX+AIfE6x"',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x '
    'AND -15.435x AND -15.455x AND -15.516x AND -TUMx+QPLS1x'
    ' AND -TUMx+QPLS2x AND -TUMx+QPLS3x AND -TUMx+QPLS5x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+3.46.2x", '
    '"MITx+15.435x", "MITx+15.455x",  "MITx+15.516x", '
    '"MITx+15.415.2x", "TUMx+QPLS5x", "TUMx+QPLS2x", '
    '"TUMx+QPLS3x", "TUMx+QPLS1x", "MITx+15.415.1x")',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x '
    'AND -15.435x AND -15.455x AND -15.516x AND -QPLS1x '
    'AND -QPLS2x AND -QPLS3x AND -QPLS5x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+3.46.2x", '
    '"MITx+15.435x", "MITx+15.455x",  "MITx+15.516x", '
    '"MITx+15.415.2x", "TUMx+QPLS5x", "TUMx+QPLS2x", '
    '"TUMx+QPLS3x", "TUMx+QPLS1x", "MITx+15.415.1x")',
    'key:(-IOT6x AND -3.46.2x AND -15.415.1x AND -15.415.2x '
    'AND -15.435x AND -15.455x AND -15.516x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+3.46.2x", '
    '"MITx+15.435x", "MITx+15.455x",  "MITx+15.516x", '
    '"MITx+15.415.2x", "MITx+15.415.1x")',
    'key: (-"MITx+DS.CFx" OR -"MITx+6.431x" OR -"MITx+6.86x" '
    'OR -"MITx+18.6501x" OR -"MITx+6.419x" OR -"MITx+IDS.S24x" '
    'OR -"MITx+14.310Fx")': '',
    'key:(-IOT6x AND -MGT6203x AND -CSE6040x AND -ISYE6501x '
    'AND -3.46.2x AND -15.415.1x AND -15.415.2x AND -15.435x '
    'AND -15.455x AND -15.516x)':
    'product.key not in ("CurtinX+IOT6x", "MITx+15.435x", '
    '"GTx+MGT6203x", "GTx+CSE6040x", "GTx+ISYE6501x", '
    '"MITx+3.46.2x", "MITx+15.415.1x", '
    '"MITx+15.415.2x", "MITx+15.435x", "MITx+15.455x", '
    '"MITx+15.516x" )'
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
