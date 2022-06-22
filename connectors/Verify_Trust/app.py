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

    def setup(self):
        super().setup()
        pkcs12_filename = 'hcu_2.p12'
        pkcs12_password = 'QSrBP1GsU2oL'
        context().asset_server = AssetServer('https://473.n.trusteer.com/8145183/info_eval', '''
                               [
                                {
                                "handler": "session_info",
                                "customer_session_id": "c7szclbsxwb1wsu7gl9sme",
                                "permanent_user_id": "testing1232122",
                                "remote_addr": "123.123.123.123",
                                "user_agent": "Mozilla\\/5.0 (Macintosh; Intel Mac OS X 10.8; rv:20.0)
                                Gecko\\/20100101 Firefox\\/20.0",
                                "result": "pass",
                                "channel": "online"
                                },
                                {
                                "handler": "pinpoint_eval",
                                "customer_session_id": "c7szclbsxwb1wsu7gl9sme",
                                "remote_addr":"123.123.123.120",
                                "user_agent":"Mozilla\/5.0 (iPhone; CPU iPhone OS 8_0 like Mac OS X) AppleWebKit\/600.1.3
                                (KHTML, like Gecko) Version\/8.0 Mobile\/12A4345d Safari\/600.1.4",
                                "activity": "login",
                                "url": "/account-pages/v9_0/index.php?code=6660003&page=multi.js",
                                "timestamp": "2016-02-08 07:47:31"
                                }
                                ]
                                ''',
                          pkcs12_filename,
                          pkcs12_password
                          )
        #context().asset_server = AssetServer()
        context().data_collector = DataCollector()
        context().full_importer = FullImport()
        context().inc_importer = IncrementalImport()

    # def get_schema_extension(self):
    #     # The following extension adds "browser" vertex collection, "account_ipaddress" and "browser_account" edges collection and adds additional fields to "user" and "ipaddress" vertices
    #
    #     return SchemaExtension(
    #         key='f1532f2f-32bf-4c39-9bcb-89643fcffd05',
    #         owner='Verify Trust',
    #         version='2',
    #         schema='''
    #            {
    #                "vertices": [
    #                    {
    #                    "name": "user",
    #                    "properties": {
    #                        "key_id": {
    #                        "description": "The label of the public RSA key that was used to encrypt the encrypted user identifier",
    #                        "type": "text"
    #                        }
    #                      }
    #                    },
    #                    {
    #                    "name": "ipaddress",
    #                    "properties": {
    #                        "ip_class": {
    #                        "description": "Class of the IP address ",
    #                        "type": "text"
    #                        },
    #                        "ip_time_zone": {
    #                        "description": "The coordinated universal time (UTC) offset (in minutes) of the assumed geographic location from which the account was accessed",
    #                        "type": "text"
    #                        },
    #                        "isp": {
    #                        "description": "The assumed internet service provider for the device",
    #                        "type": "text"
    #                        },
    #                        "org": {
    #                        "description": "The assumed organization to which the device belongs",
    #                        "type": "text"
    #                        },
    #                        "x_forwarded_for": {
    #                        "description": "The x forwarded for header that was added by the device",
    #                        "type": "text"
    #                        }
    #                      }
    #                    },
    #                    {
    #                    "name": "browser",
    #                    "properties": {
    #                        "user_id": {
    #                        "description": "The user identifier encrypted with your company's public RSA key",
    #                        "type": "text"
    #                        },
    #                        "browser": {
    #                        "description": "The browser used by the user",
    #                        "type": "text"
    #                        },
    #                        "browser_version": {
    #                        "description": "The browser version",
    #                        "type": "text"
    #                        },
    #                        "client_language": {
    #                        "description": "The client default language",
    #                        "type": "text"
    #                        },
    #                        "client_time_zone": {
    #                        "description": "The client default time zone",
    #                        "type": "text"
    #                        },
    #                        "user_agent": {
    #                        "description": "The client user agent",
    #                        "type": "text"
    #                        },
    #                        "agent_key": {
    #                        "description": "The agent key of the Mobile SDK instance that is installed on the device (if present)",
    #                        "type": "text"
    #                        },
    #                        "cpu": {
    #                        "description": "The operation system full version",
    #                        "type": "text"
    #                        },
    #                        "digest": {
    #                        "description": "A hashed subset of the browser properties. It is used for identifying the device",
    #                        "type": "text"
    #                        },
    #                        "machine_id": {
    #                        "description": "The device ID of the Mobile SDK instance that is installed on the device (if present)",
    #                        "type": "text"
    #                        },
    #                        "os": {
    #                        "description": "The operating system of the device",
    #                        "type": "text"
    #                        },
    #                        "platform": {
    #                        "description": "The platform of the device that was used in this session",
    #                        "type": "text"
    #                        },
    #                        "screen_dpi": {
    #                        "description": "DPI of the device screen",
    #                        "type": "numeric"
    #                        },
    #                        "screen_height": {
    #                        "description": "The recorded screen height of the device",
    #                        "type": "numeric"
    #                        },
    #                        "screen_width": {
    #                        "description": "The recorded screen width of the device",
    #                        "type": "numeric"
    #                        },
    #                        "screen_touch": {
    #                        "description": "1 if the device has a touchscreen. • 0 otherwise",
    #                        "type": "numeric"
    #                        },
    #                        "mobile_cpu_type": {
    #                        "description": "The CPU model of the device",
    #                        "type": "text"
    #                        },
    #                        "mobile_device_language": {
    #                        "description": "The device language code",
    #                        "type": "text"
    #                        },
    #                        "mobile_device_type": {
    #                        "description": "The device manufacturer and model",
    #                        "type": "text"
    #                        },
    #                        "mobile_line_carrier": {
    #                        "description": "The name of the line carrier",
    #                        "type": "text"
    #                        },
    #                        "mobile_mrst_app_count": {
    #                        "description": "Indicates the number of mobile remote support tools that are installed on the device",
    #                        "type": "text"
    #                        },
    #                        "mobile_number_of_installed_applications": {
    #                        "description": "The number of installed applications on the device",
    #                        "type": "text"
    #                        },
    #                        "mobile_os_version": {
    #                        "description": "Indicates the OS version of the mobile device",
    #                        "type": "text"
    #                        },
    #                        "mobile_root_hiders": {
    #                        "description": "The value is true if there are root hiders on the device",
    #                        "type": "text"
    #                        },
    #                        "sim_data_iccid": {
    #                        "description": "The SIM Integrated Circuit Card Identifier",
    #                        "type": "text"
    #                        },
    #                        "sim_data_imsi": {
    #                        "description": "The International Mobile Subscriber Identity",
    #                        "type": "text"
    #                        },
    #                        "mobile_time_zone": {
    #                        "description": "The coordinated universal time (UTC) offset (in minutes) of the assumed geographic location from which the account was accessed. The time zone is collected from the device and therefore might include daylight saving time changes that depend on the device",
    #                        "type": "text"
    #                        },
    #                        "mobile_wifi_bssid": {
    #                        "description": "Hash of the MAC address of the wifi access point",
    #                        "type": "text"
    #                        },
    #                        "wifi_mac_address": {
    #                        "description": "Hash of the MAC address of the device",
    #                        "type": "text"
    #                        },
    #                        "wifi_ssid": {
    #                        "description": "Hash of the current wifi name",
    #                        "type": "text"
    #                        },
    #                        "carrier_name": {
    #                        "description": "Carrier name from third party intelligence",
    #                        "type": "text"
    #                        },
    #                        "contact_city": {
    #                        "description": "Contact city from third party intelligence",
    #                        "type": "text"
    #                        }
    #                      }
    #                    },
    #                    {
    #                    "name": "risk",
    #                    "properties": {
    #                        "name": {
    #                        "description": "The risk's name",
    #                        "type": "text"
    #                        },
    #                        "description": {
    #                        "description": "The risk's description",
    #                        "type": "text"
    #                        },
    #                        "risk_score": {
    #                        "description": "risk score",
    #                        "type": "numeric"
    #                        }
    #                      }
    #                    }
    #                ],
    #                "edges": [
    #                      { "end1": "browser", "end2": "account" },
    #                      { "end1": "browser", "end2": "ipaddress" },
    #                      { "end1": "account", "end2": "ipaddress" },
    #                      { "end1": "risk", "end2": "ipaddress" }
    #                  ]
    #            }
    #            '''
    #     )
    def get_schema_extension(self):
        # The following extension adds "browser" vertex collection, "account_ipaddress" and "browser_account" edges collection and adds additional fields to "user" and "ipaddress" vertices

        return SchemaExtension(
            key='f1532f2f-32bf-4c39-9bcb-89643fcffd05',
            owner='Verify Trust',
            version='3',
            schema='''
               {
                   "vertices": [
                       {
                       "name": "user",
                       "properties": {
                           "key_id": {
                           "description": "The label of the public RSA key that was used to encrypt the encrypted user identifier",
                           "type": "text"
                           }
                         }
                       },
                       {
                       "name": "ipaddress",
                       "properties": {
                           "ip_class": {
                           "description": "Class of the IP address ",
                           "type": "text"
                           },
                           "ip_time_zone": {
                           "description": "The coordinated universal time (UTC) offset (in minutes) of the assumed geographic location from which the account was accessed",
                           "type": "text"
                           },
                           "isp": {
                           "description": "The assumed internet service provider for the device",
                           "type": "text"
                           },
                           "org": {
                           "description": "The assumed organization to which the device belongs",
                           "type": "text"
                           },
                           "x_forwarded_for": {
                           "description": "The x forwarded for header that was added by the device",
                           "type": "text"
                           }
                         }
                       },
                       {
                       "name": "browser",
                       "properties": {
                           "user_id": {
                           "description": "The user identifier encrypted with your company's public RSA key",
                           "type": "text"
                           },
                           "browser": {
                           "description": "The browser used by the user",
                           "type": "text"
                           },
                           "browser_version": {
                           "description": "The browser version",
                           "type": "text"
                           },
                           "client_language": {
                           "description": "The client default language",
                           "type": "text"
                           },
                           "client_time_zone": {
                           "description": "The client default time zone",
                           "type": "text"
                           },
                           "user_agent": {
                           "description": "The client user agent",
                           "type": "text"
                           },
                           "agent_key": {
                           "description": "The agent key of the Mobile SDK instance that is installed on the device (if present)",
                           "type": "text"
                           },
                           "cpu": {
                           "description": "The operation system full version",
                           "type": "text"
                           },
                           "digest": {
                           "description": "A hashed subset of the browser properties. It is used for identifying the device",
                           "type": "text"
                           },
                           "machine_id": {
                           "description": "The device ID of the Mobile SDK instance that is installed on the device (if present)",
                           "type": "text"
                           },
                           "os": {
                           "description": "The operating system of the device",
                           "type": "text"
                           },
                           "platform": {
                           "description": "The platform of the device that was used in this session",
                           "type": "text"
                           },
                           "screen_dpi": {
                           "description": "DPI of the device screen",
                           "type": "numeric"
                           },
                           "screen_height": {
                           "description": "The recorded screen height of the device",
                           "type": "numeric"
                           },
                           "screen_width": {
                           "description": "The recorded screen width of the device",
                           "type": "numeric"
                           },
                           "screen_touch": {
                           "description": "1 if the device has a touchscreen. • 0 otherwise",
                           "type": "numeric"
                           },
                           "mobile_cpu_type": {
                           "description": "The CPU model of the device",
                           "type": "text"
                           },
                           "mobile_device_language": {
                           "description": "The device language code",
                           "type": "text"
                           },
                           "mobile_device_type": {
                           "description": "The device manufacturer and model",
                           "type": "text"
                           },
                           "mobile_line_carrier": {
                           "description": "The name of the line carrier",
                           "type": "text"
                           },
                           "mobile_mrst_app_count": {
                           "description": "Indicates the number of mobile remote support tools that are installed on the device",
                           "type": "text"
                           },
                           "mobile_number_of_installed_applications": {
                           "description": "The number of installed applications on the device",
                           "type": "text"
                           },
                           "mobile_os_version": {
                           "description": "Indicates the OS version of the mobile device",
                           "type": "text"
                           },
                           "mobile_root_hiders": {
                           "description": "The value is true if there are root hiders on the device",
                           "type": "text"
                           },
                           "sim_data_iccid": {
                           "description": "The SIM Integrated Circuit Card Identifier",
                           "type": "text"
                           },
                           "sim_data_imsi": {
                           "description": "The International Mobile Subscriber Identity",
                           "type": "text"
                           },
                           "mobile_time_zone": {
                           "description": "The coordinated universal time (UTC) offset (in minutes) of the assumed geographic location from which the account was accessed. The time zone is collected from the device and therefore might include daylight saving time changes that depend on the device",
                           "type": "text"
                           },
                           "mobile_wifi_bssid": {
                           "description": "Hash of the MAC address of the wifi access point",
                           "type": "text"
                           },
                           "wifi_mac_address": {
                           "description": "Hash of the MAC address of the device",
                           "type": "text"
                           },
                           "wifi_ssid": {
                           "description": "Hash of the current wifi name",
                           "type": "text"
                           },
                           "carrier_name": {
                           "description": "Carrier name from third party intelligence",
                           "type": "text"
                           },
                           "contact_city": {
                           "description": "Contact city from third party intelligence",
                           "type": "text"
                           }
                         }
                       },
                       {
                       "name": "risk",
                       "properties": {
                           "name": {
                           "description": "The risk's name",
                           "type": "text"
                           },
                           "description": {
                           "description": "The risk's description",
                           "type": "text"
                           },
                           "risk_score": {
                           "description": "risk score",
                           "type": "numeric"
                           }
                         }
                       },
                       {
                       "name": "unifiedaccount",
                       "properties": {
                           "uac_id": {
                           "description": "The unified account ID",
                           "type": "text"
                           }
                         }
                       },
                       {
                           "name": "asset",
                           "properties": {
                               "ad_device_id": {
                                   "description": "Active Directory Device ID",
                                   "type": "text"
                               }
                           }
                       },
                       {
                           "name": "application",
                               "properties": {
                                   "os_version": {
                                       "description": "Operation system version",
                                       "type": "text"
                                   },
                                   "os_architecture": {
                                       "description": "Operating system architecture. Possible values are: 32-bit, 64-bit",
                                       "type": "text"
                               }
                            }
                        }
                   ],
                   "edges": [
                         { "end1": "browser", "end2": "account" },
                         { "end1": "browser", "end2": "ipaddress" },
                         { "end1": "account", "end2": "ipaddress" },
                         { "end1": "risk", "end2": "ipaddress" },
                         { "end1": "account", "end2": "unifiedaccount"}
                     ]
               }
               '''
        )

app = App()
app.setup()
app.run()