## Randori pre-req

Access Token
Hostname of Randori instance

API:
```https://github.com/RandoriDev/randori-api-sdk/blob/master/docs/DefaultApi.md#get_all_detections_for_target```

with query for full import:
```
query = {
            'condition': "AND",
            'rules': [
                {
                  'field': "table.target_last_seen",
                  'operator': "greater_or_equal",
                  'value': three_months_back
                }
            ]
        }
```


## Mapping

|  CAR vertex/edge  |   CAR field   |  Data source field  |
|  :------------:    |:---------------:| :-----:|
| Asset      | external_id | target_id |
|            | description | description |
|            | name | vendor + "," + name + "," + version |
|            | perspective_name | perspective_name |
|            | randori_notes | randori_notes |
|            | first_seen | timestamp(first_seen) |
|            | last_seen | timestamp(last_seen) |
|            | risk | if priority_score > 200 risk = 10; if priority_score <= 40 risk = priority_score/40 * 7; else risk = 7 + ((priority_score-40)/160 * 3) |
|            | business_value | if impact_score == Low business_value = 2; if impact_score == Medium business_value = 5; if impact_score == High business_value = 8; else business_value = 0 |
| ipaddress | _key | ip |
| hostname | _key | hostname |
|          | path | path |
| application | external_id | target_id |
|          | name | vendor + "," + name + "," + version |
| ports | external_id | target_id |
|          | port_number | port |
|          | protocol | protocol |
| asset_ipaddress | _from_external_id | target_id |
|                 | _to | 'ipaddress/' + ip |
| asset_hostname | _from_external_id | target_id |
|                 | _to | 'hostname/' + hostname |
| asset_application | _from_external_id | target_id |
|                 | _to_external_id | 'application/' + target_id |
| application_port | _from_external_id | target_id |
|                 | _to_external_id | 'port/' + target_id |
| ipaddress_port | _from_external_id | ip |
|                 | _to_external_id | 'port/' + target_id |

## Connector

Install python dependencies
```
pip3 install -r requirements.txt
```

Running the connector:
```
python3 app.py -access_token=<Access token of the Randori data source> -host="<hostname of randori instance>" -car-service-key "<car-service-key>" -car-service-password "<car-service-password>" -car-service-url "<car-service-url>" -source=randori
```

