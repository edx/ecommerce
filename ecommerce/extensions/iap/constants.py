MOBILE_PAYMENT_PROCESSORS = ['android-iap', 'ios-iap']
ANDROID_SKU_PREFIX = 'android'
IOS_SKU_PREFIX = 'ios'
MISSING_WEB_SEAT_ERROR = "Couldn't find existing web seat for course [%s]"

# .. toggle_name: create_appstore_products_for_inapp
# .. toggle_type: waffle_switch
# .. toggle_default: False
# .. toggle_description: Create ios products on appstore using Apple in-app apis.
# .. toggle_use_cases: open_edx
# .. toggle_creation_date: 2023-07-25
# .. toggle_tickets: LEARNER-9951
# .. toggle_status: supported
CREATE_APPSTORE_PRODUCTS_FOR_INAPP = 'create_appstore_products_for_inapp'
