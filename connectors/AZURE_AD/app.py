import argparse, os

from car_framework.context import context
from car_framework.app import BaseApp
from car_framework.extension import SchemaExtension

from connector.server_access import AssetServer
from connector.data_collector import DataCollector
from connector.full_import import FullImport
from connector.inc_import import IncrementalImport


version = '1.0.1'
os.environ["CURL_CA_BUNDLE"] = ""


class App(BaseApp):
    def __init__(self):
        super().__init__('This script is used for pushing asset data to CP4S CAR ingestion microservice')
        # Add parameters need to connect data source
        self.parser.add_argument('-subscriptionID', dest='subscription_id', default=os.getenv('CONFIGURATION_AUTH_SUBSCRIPTION_ID',None), type=str, required=False, 
                            help='Subscription ID for the data source account')
        self.parser.add_argument('-tenantID', dest='tenantID', default=os.getenv('CONFIGURATION_AUTH_TENANT_ID',None), type=str, required=False,
                            help='Tenant ID for data source account')
        self.parser.add_argument('-clientID', dest='clientID', default=os.getenv('CONFIGURATION_AUTH_CLIENT_ID',None), type=str, required=False,
                            help='Client ID for data source account')
        self.parser.add_argument('-clientSecret', dest='clientSecret', default=os.getenv('CONFIGURATION_AUTH_CLIENT_SECRET',None), type=str, required=False,
                            help='Client Secret value for data source account')
        self.parser.add_argument('-alerts', dest='alerts', type=bool, required=False, help=argparse.SUPPRESS)
        self.parser.add_argument('-vuln', dest='vuln', type=bool, required=False, help=argparse.SUPPRESS)


    def setup(self):
        super().setup()
        context().asset_server = AssetServer(tenantID = context().args.tenantID, clientID = context().args.clientID, clientSecret = context().args.clientSecret)
        context().data_collector = DataCollector()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

    # def get_schema_extension(self):
    #     # The following extension adds "browser" vertex collection, "account_ipaddress" and "browser_account" edges collection and adds additional fields to "user" and "ipaddress" vertices
    #
    #     return SchemaExtension(
    #         key='f1532f2f-32bf-4c39-9bcb-89643fcffd03',
    #         owner='IDR',
    #         version='1',
    #         schema='''
    #            {
    #                "edges": [
    #                      { "end1": "account", "end2": "account"}
    #                  ]
    #            }
    #            '''
    #     )
    # def get_schema_extension(self):
    #     # The following extension adds "browser" vertex collection, "account_ipaddress" and "browser_account" edges collection and adds additional fields to "user" and "ipaddress" vertices
    #
    #     return SchemaExtension(
    #         key='f1532f2f-32bf-4c39-9bcb-89643fcffd03',
    #         owner='IDR',
    #         version='3',
    #         schema='''
    #            {
    #                "vertices": [
    #                    {
    #                    "name": "group",
    #                    "properties": {
    #                        "description": {
    #                        "description": "An optional description for the group",
    #                        "type": "text"
    #                        },
    #                        "name": {
    #                        "description": "The display name for the group",
    #                        "type": "text"
    #                        },
    #                        "created_date_time": {
    #                        "description": "Timestamp of when the group was created",
    #                        "type": "text"
    #                        },
    #                        "deleted_date_time": {
    #                        "description": "If the object is deleted, it is first logically deleted, and this property is updated with the date and time when the object was deleted",
    #                        "type": "text"
    #                        },
    #                        "expiration_date_time": {
    #                        "description": "Timestamp of when the group is set to expire",
    #                        "type": "text"
    #                        },
    #                        "renewed_date_time": {
    #                        "description": "Timestamp of when the group was last renewed",
    #                        "type": "text"
    #                        },
    #                        "classification": {
    #                        "description": "Describes a classification for the group (such as low, medium or high business impact)",
    #                        "type": "text"
    #                        }
    #                      },
    #                      "name": "approle ",
    #                      "properties": {
    #                        "app_role_id ": {
    #                        "description": "The identifier (id) for the app role which is assigned to the principal",
    #                        "type": "text"
    #                        },
    #                        "principal_id ": {
    #                        "description": "The unique identifier (id) for the user, group, or service principal being granted the app role",
    #                        "type": "text"
    #                        },
    #                        "principal_name": {
    #                        "description": "The display name of the user, group, or service principal that was granted the app role assignment",
    #                        "type": "text"
    #                        },
    #                        "principal_type": {
    #                        "description": "The type of the assigned principal. This can either be User, Group, or ServicePrincipal",
    #                        "type": "text"
    #                        },
    #                        "resource_display_name": {
    #                        "description": "The type of the assigned principal. This can either be User, Group, or ServicePrincipal",
    #                        "type": "text"
    #                        },
    #                        "resource_id": {
    #                        "description": "The unique identifier (id) for the resource service principal for which the assignment is made",
    #                        "type": "text"
    #                        }
    #                      },
    #                      "name": "permissiongrants",
    #                      "properties": {
    #                        "client_id": {
    #                        "description": "ID of the Azure AD app that has been granted access",
    #                        "type": "text"
    #                        },
    #                        "client_app_id": {
    #                        "description": "ID of the service principal of the Azure AD app that has been granted access",
    #                        "type": "text"
    #                        },
    #                        "resource_app_id": {
    #                        "description": "ID of the Azure AD app that is hosting the resource",
    #                        "type": "text"
    #                        },
    #                        "permission_type": {
    #                        "description": "The type of permission. Possible values are: Application, Delegated",
    #                        "type": "text"
    #                        },
    #                        "permission": {
    #                        "description": "The name of the resource-specific permission",
    #                        "type": "text"
    #                        }
    #                      }
    #                    }
    #                ],
    #                "edges": [
    #                      { "end1": "account", "end2": "group"},
    #                      { "end1": "account", "end2": "approle"},
    #                      { "end1": "group", "end2": "approle"},
    #                      { "end1": "group", "end2": "permissiongrants"}
    #                  ]
    #            }
    #            '''
    #     )

    # def get_schema_extension(self):
    #     # The following extension adds "browser" vertex collection, "account_ipaddress" and "browser_account" edges collection and adds additional fields to "user" and "ipaddress" vertices
    #
    #     return SchemaExtension(
    #         key='f1532f2f-32bf-4c39-9bcb-89643fcffd05',
    #         owner='ITDR',
    #         version='1',
    #         schema='''
    #                 {
    #                     "vertices": [
    #                         {
    #                             "name": "user",
    #                             "properties": {
    #                                 "key_id": {
    #                                     "description": "The label of the public RSA key that was used to encrypt the encrypted user identifier",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "ipaddress",
    #                             "properties": {
    #                                 "ip_class": {
    #                                     "description": "Class of the IP address ",
    #                                     "type": "text"
    #                                 },
    #                                 "ip_time_zone": {
    #                                     "description": "The coordinated universal time (UTC) offset (in minutes) of the assumed geographic location from which the account was accessed",
    #                                     "type": "text"
    #                                 },
    #                                 "isp": {
    #                                     "description": "The assumed internet service provider for the device",
    #                                     "type": "text"
    #                                 },
    #                                 "org": {
    #                                     "description": "The assumed organization to which the device belongs",
    #                                     "type": "text"
    #                                 },
    #                                 "x_forwarded_for": {
    #                                     "description": "The x forwarded for header that was added by the device",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "browser",
    #                             "properties": {
    #                                 "user_id": {
    #                                     "description": "The user identifier encrypted with your company's public RSA key",
    #                                     "type": "text"
    #                                 },
    #                                 "browser": {
    #                                     "description": "The browser used by the user",
    #                                     "type": "text"
    #                                 },
    #                                 "browser_version": {
    #                                     "description": "The browser version",
    #                                     "type": "text"
    #                                 },
    #                                 "client_language": {
    #                                     "description": "The client default language",
    #                                     "type": "text"
    #                                 },
    #                                 "client_time_zone": {
    #                                     "description": "The client default time zone",
    #                                     "type": "text"
    #                                 },
    #                                 "user_agent": {
    #                                     "description": "The client user agent",
    #                                     "type": "text"
    #                                 },
    #                                 "agent_key": {
    #                                     "description": "The agent key of the Mobile SDK instance that is installed on the device (if present)",
    #                                     "type": "text"
    #                                 },
    #                                 "cpu": {
    #                                     "description": "The operation system full version",
    #                                     "type": "text"
    #                                 },
    #                                 "digest": {
    #                                     "description": "A hashed subset of the browser properties. It is used for identifying the device",
    #                                     "type": "text"
    #                                 },
    #                                 "machine_id": {
    #                                     "description": "The device ID of the Mobile SDK instance that is installed on the device (if present)",
    #                                     "type": "text"
    #                                 },
    #                                 "os": {
    #                                     "description": "The operating system of the device",
    #                                     "type": "text"
    #                                 },
    #                                 "platform": {
    #                                     "description": "The platform of the device that was used in this session",
    #                                     "type": "text"
    #                                 },
    #                                 "screen_dpi": {
    #                                     "description": "DPI of the device screen",
    #                                     "type": "numeric"
    #                                 },
    #                                 "screen_height": {
    #                                     "description": "The recorded screen height of the device",
    #                                     "type": "numeric"
    #                                 },
    #                                 "screen_width": {
    #                                     "description": "The recorded screen width of the device",
    #                                     "type": "numeric"
    #                                 },
    #                                 "screen_touch": {
    #                                     "description": "1 if the device has a touchscreen. • 0 otherwise",
    #                                     "type": "numeric"
    #                                 },
    #                                 "mobile_cpu_type": {
    #                                     "description": "The CPU model of the device",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_device_language": {
    #                                     "description": "The device language code",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_device_type": {
    #                                     "description": "The device manufacturer and model",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_line_carrier": {
    #                                     "description": "The name of the line carrier",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_mrst_app_count": {
    #                                     "description": "Indicates the number of mobile remote support tools that are installed on the device",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_number_of_installed_applications": {
    #                                     "description": "The number of installed applications on the device",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_os_version": {
    #                                     "description": "Indicates the OS version of the mobile device",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_root_hiders": {
    #                                     "description": "The value is true if there are root hiders on the device",
    #                                     "type": "text"
    #                                 },
    #                                 "sim_data_iccid": {
    #                                     "description": "The SIM Integrated Circuit Card Identifier",
    #                                     "type": "text"
    #                                 },
    #                                 "sim_data_imsi": {
    #                                     "description": "The International Mobile Subscriber Identity",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_time_zone": {
    #                                     "description": "The coordinated universal time (UTC) offset (in minutes) of the assumed geographic location from which the account was accessed. The time zone is collected from the device and therefore might include daylight saving time changes that depend on the device",
    #                                     "type": "text"
    #                                 },
    #                                 "mobile_wifi_bssid": {
    #                                     "description": "Hash of the MAC address of the wifi access point",
    #                                     "type": "text"
    #                                 },
    #                                 "wifi_mac_address": {
    #                                     "description": "Hash of the MAC address of the device",
    #                                     "type": "text"
    #                                 },
    #                                 "wifi_ssid": {
    #                                     "description": "Hash of the current wifi name",
    #                                     "type": "text"
    #                                 },
    #                                 "carrier_name": {
    #                                     "description": "Carrier name from third party intelligence",
    #                                     "type": "text"
    #                                 },
    #                                 "contact_city": {
    #                                     "description": "Contact city from third party intelligence",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "risk",
    #                             "properties": {
    #                                 "name": {
    #                                     "description": "The risk's name",
    #                                     "type": "text"
    #                                 },
    #                                 "description": {
    #                                     "description": "The risk's description",
    #                                     "type": "text"
    #                                 },
    #                                 "risk_score": {
    #                                     "description": "risk score",
    #                                     "type": "numeric"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "unifiedacc",
    #                             "properties": {
    #                                 "uac_id": {
    #                                     "description": "The unified account ID",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "asset",
    #                             "properties": {
    #                                 "ad_device_id": {
    #                                     "description": "Active Directory Device ID",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "application",
    #                             "properties": {
    #                                 "os_version": {
    #                                     "description": "Operation system version",
    #                                     "type": "text"
    #                                 },
    #                                 "os_architecture": {
    #                                     "description": "Operating system architecture. Possible values are: 32-bit, 64-bit",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "group",
    #                             "properties": {
    #                                 "description": {
    #                                     "description": "An optional description for the group",
    #                                     "type": "text"
    #                                 },
    #                                 "name": {
    #                                     "description": "The display name for the group",
    #                                     "type": "text"
    #                                 },
    #                                 "created_date_time": {
    #                                     "description": "Timestamp of when the group was created",
    #                                     "type": "text"
    #                                 },
    #                                 "deleted_date_time": {
    #                                     "description": "If the object is deleted, it is first logically deleted, and this property is updated with the date and time when the object was deleted",
    #                                     "type": "text"
    #                                 },
    #                                 "expiration_date_time": {
    #                                     "description": "Timestamp of when the group is set to expire",
    #                                     "type": "text"
    #                                 },
    #                                 "renewed_date_time": {
    #                                     "description": "Timestamp of when the group was last renewed",
    #                                     "type": "text"
    #                                 },
    #                                 "classification": {
    #                                     "description": "Describes a classification for the group (such as low, medium or high business impact)",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "approle",
    #                             "properties": {
    #                                 "app_role_id": {
    #                                     "description": "The identifier (id) for the app role which is assigned to the principal",
    #                                     "type": "text"
    #                                 },
    #                                 "principal_id": {
    #                                     "description": "The unique identifier (id) for the user, group, or service principal being granted the app role",
    #                                     "type": "text"
    #                                 },
    #                                 "principal_name": {
    #                                     "description": "The display name of the user, group, or service principal that was granted the app role assignment",
    #                                     "type": "text"
    #                                 },
    #                                 "principal_type": {
    #                                     "description": "The type of the assigned principal. This can either be User, Group, or ServicePrincipal",
    #                                     "type": "text"
    #                                 },
    #                                 "resource_display_name": {
    #                                     "description": "The type of the assigned principal. This can either be User, Group, or ServicePrincipal",
    #                                     "type": "text"
    #                                 },
    #                                 "resource_id": {
    #                                     "description": "The unique identifier (id) for the resource service principal for which the assignment is made",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "permissiongrants",
    #                             "properties": {
    #                                 "client_id": {
    #                                     "description": "ID of the Azure AD app that has been granted access",
    #                                     "type": "text"
    #                                 },
    #                                 "client_app_id": {
    #                                     "description": "ID of the service principal of the Azure AD app that has been granted access",
    #                                     "type": "text"
    #                                 },
    #                                 "resource_app_id": {
    #                                     "description": "ID of the Azure AD app that is hosting the resource",
    #                                     "type": "text"
    #                                 },
    #                                 "permission_type": {
    #                                     "description": "The type of permission. Possible values are: Application, Delegated",
    #                                     "type": "text"
    #                                 },
    #                                 "permission": {
    #                                     "description": "The name of the resource-specific permission",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "signin",
    #                             "properties": {
    #                                 "client_app_used": {
    #                                     "description": "Identifies the client used for the sign-in activity",
    #                                     "type": "text"
    #                                 },
    #                                 "created_time": {
    #                                     "description": "Date and time (UTC) the sign-in was initiated.",
    #                                     "type": "text"
    #                                 },
    #                                 "is_interactive": {
    #                                     "description": "Indicates if a sign-in is interactive or not.",
    #                                     "type": "text"
    #                                 },
    #                                 "risk_detail": {
    #                                     "description": "Provides the 'reason' behind a specific state of a risky user, sign-in or a risk event.",
    #                                     "type": "text"
    #                                 },
    #                                 "risk_level_aggregated": {
    #                                     "description": "Aggregated risk level. The possible values are: none, low, medium, high, hidden, and unknownFutureValue.",
    #                                     "type": "text"
    #                                 },
    #                                 "risk_level_during_signin": {
    #                                     "description": "Risk level during sign-in. The possible values are: none, low, medium, high, hidden, and unknownFutureValue.",
    #                                     "type": "text"
    #                                 },
    #                                 "risk_state": {
    #                                     "description": "Reports status of the risky user, sign-in, or a risk event. The possible values are: none, confirmedSafe, remediated, dismissed, atRisk, confirmedCompromised, unknownFutureValue.",
    #                                     "type": "text"
    #                                 },
    #                                 "risk_types": {
    #                                     "description": "Risk event types associated with the sign-in.",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "itdr",
    #                             "properties": {
    #                                 "description": {
    #                                     "description": "An optional description for the insight",
    #                                     "type": "text"
    #                                 },
    #                                 "name": {
    #                                     "description": "The display name for the insight",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         },
    #                         {
    #                             "name": "audit",
    #                             "properties": {
    #                                 "category": {
    #                                     "description": "Indicates which resource category that's targeted by the activity.",
    #                                     "type": "text"
    #                                 },
    #                                 "result": {
    #                                     "description": "Indicates the result of the activity. Possible values are: success, failure, timeout, unknownFutureValue",
    #                                     "type": "text"
    #                                 },
    #                                 "result_reason": {
    #                                     "description": "Indicates the reason for failure if the result is failure or timeout",
    #                                     "type": "text"
    #                                 },
    #                                 "name": {
    #                                     "description": "Indicates the activity name or the operation name.",
    #                                     "type": "text"
    #                                 },
    #                                 "logged_by": {
    #                                     "description": "Indicates information on which service initiated the activity",
    #                                     "type": "text"
    #                                 },
    #                                 "additional_details": {
    #                                     "description": "Indicates additional details on the activity.",
    #                                     "type": "text"
    #                                 }
    #                             }
    #                         }
    #
    #                     ],
    #                     "edges": [
    #                         {
    #                             "end1": "browser",
    #                             "end2": "account"
    #                         },
    #                         {
    #                             "end1": "browser",
    #                             "end2": "ipaddress"
    #                         },
    #                         {
    #                             "end1": "account",
    #                             "end2": "ipaddress"
    #                         },
    #                         {
    #                             "end1": "risk",
    #                             "end2": "ipaddress"
    #                         },
    #                         {
    #                             "end1": "account",
    #                             "end2": "unifiedacc"
    #                         },
    #                         {
    #                             "end1": "unifiedacc",
    #                             "end2": "vulnerability"
    #                         },
    #                         {
    #                             "end1": "account",
    #                             "end2": "group"
    #                         },
    #                         {
    #                             "end1": "account",
    #                             "end2": "approle"
    #                         },
    #                         {
    #                             "end1": "group",
    #                             "end2": "approle"
    #                         },
    #                         {
    #                             "end1": "group",
    #                             "end2": "permissiongrants"
    #                         },
    #                         {
    #                             "end1": "account",
    #                             "end2": "signin"
    #                         },
    #                         {
    #                             "end1": "signin",
    #                             "end2": "application"
    #                         },
    #                         {
    #                             "end1": "signin",
    #                             "end2": "ipaddress"
    #                         },
    #                         {
    #                             "end1": "signin",
    #                             "end2": "asset"
    #                         },
    #                         {
    #                             "end1": "signin",
    #                             "end2": "geolocation"
    #                         },
    #                         {
    #                             "end1": "signin",
    #                             "end2": "approle"
    #                         },
    #                         {
    #                             "end1": "unifiedacc",
    #                             "end2": "itdr"
    #                         },
    #                         {
    #                             "end1": "ipaddress",
    #                             "end2": "itdr"
    #                         },
    #                         {
    #                             "end1": "audit",
    #                             "end2": "account"
    #                         },
    #                         {
    #                             "end1": "audit",
    #                             "end2": "group"
    #                         },
    #                         {
    #                             "end1": "audit",
    #                             "end2": "application"
    #                         }
    #                     ]
    #                 }
    #            '''
    #     )

app = App()
app.setup()
app.run()