
Interface Description

Query the track information of the shipment through the tracking number

Interface information

Test address:https://demoopenapi.jtjms-br.com/webopenplatformapi/api/logistics/trace

Official address:https://openapi.jtjms-br.com/webopenplatformapi/api/logistics/trace

Test apiAccount:

Test privateKey:

Request method:POST

type of data:X-WWW-FORM-URLENCODED

Response type:JSON

Parameter Description

Headers
apiAccount
Number
Y
The api account ID of the access party on the platform
digest
String
Y
Signature string
timestamp
Number
Y
Timestamp, milliseconds
Request parameter
bizContent
String
Y
Business parameters
The string type in json format in the business parameter module
Business parameters
command
int(5)
N
0
Query Command: If not specified or left blank: By default, use billCodes to perform the tracking search;
0: billCodes (query based on waybill numbers)

1: invoiceAccessKey (query using the invoice access key)

2: customerOrderNumber (query using the customer order number)

customerCode
String
C
0
Customer Code

When requesting a tracking query using the customerOrderNumber, the customer code must be provided.
billCodes
String
N
UT0000352320970
Waybill Numbers Multiple waybill numbers should be separated by an English comma, and currently, the system allows for a maximum of 30 waybills to be queried in a single request.
invoiceAccessKey
String
N
33240442446277000354554629302337581016930063
Invoice Access Key Multiple key should be separated by an English comma, and currently, the system allows for a maximum of 30 waybills to be queried in a single request.
customerOrderNumber
String
N
BR2455090392188U
Customer Order Number Multiple key should be separated by an English comma, and currently, the system allows for a maximum of 30 waybills to be queried in a single request.
Message description

Response parameters
code
String
Y
Return code, see appendix
msg
String
Y
Description
data
Object
Y
Business data
Data type description
billCode
String
Y
Waybill number
invoiceAccessKey
String
Y
Invoice Access Key
customerOrderNumber
String
Y
Customer order number
details
Array
Y
Waybill track details
details type description
scanTime
String
Y
Scan time
desc
String
Y
Trajectory description
scanType
String
Y
Scan type
1.Express mail collection

2.In-stock scanning (disabled)

3.Outgoing scanning

4.Incoming scanning

5.Outbound scanning

10.Express delivery

11.Problem scanning

12.Return scanning

13.Center arrival

16.Outbound Item Receiving Scan

scanCode
String
Y
scan type code:
express mail collection: 10

in-stock scanning (disabled): 20

outgoing scanning: 50

Center arrival: 90

incoming scanning: 92

Outbound scanning: 94

Express delivery: 100

Problem scanning: 110

Return scanning: 172

Outbound Item Receiving Scan: 210

problemType
String
N
P71a Non-compliant packaging on collection

P13a Incomplete collection address

P13b Incorrect collection address

D13a Incomplete address

D13b Incorrect address

D16a Refusal of receipt by the customer (recipient)

D65a Inability to arrive at the given address

D65b Absence of recipient

D65n Absence of recipient in several delivery attempts

D66b Tax inspection

D66c Abnormal weather

R17a Devolution

R73b Failure to return to customer or PA.

83a Return to platform

S70a Theft or Assault

S41a Order lost during delivery

Z41d Lost internal product and damaged packaging

Z41e Lost internal product and packaging in good condition

Z27a Damaged packaging and internal product

Z27b Internal product damaged, packaging in good condition

scanNetworkName
String
Y
Scan site name
scanNetworkId
String
Y
Scan site ID
staffName
String
Y
Salesman's name
staffContact
String
Y
Salesman contact information
scanNetworkContact
String
Y
Scan the contact information of outlets
scanNetworkProvince
String
Y
Scan the provinces of outlets
scanNetworkCity
String
Y
Scan the city
scanNetworkArea
String
Y
Scanning outlet district/county
nextStopName
String
Y
Last stop (arrival) or next stop name (sent)
nextNetworkProvinceName
String
Y
Next stop province (provided when sending scan type
nextNetworkCityName
String
Y
Next stop city (provided when sending scan type)
nextNetworkAreaName
String
Y
Next stop district/county (provided when sending scan type)
staffLng
String
N
Longitude
staffLat
String
N
Latitude
signer
String
N
Recipient
signName
String
N
Signature Type Name
1.Consignee（Personal Receipt）
2.Collection point/store（Self-Pickup）
3.Others（Third-Party Collection）
signatureUrl
String
N
Electronic Signature Image
sigPicUrl
String
N
Receipt Image
Request example

"Header：
apiAccount=1627
digest=U40e5sumorgd3YgZzU61Mw==
timestamp=1565238848921

Body：
bizContent= {
"command": "",//非必填，空或者不存在默认为使用billcodes查询，0：billCodes/ 1: invoiceAccessKey / 2: customerOrderNumber
"billCodes": "UT0000352320970,UT0000359748995",
"customerCode":"J1999999",
"invoiceAccessKey": "33240442446277000354554629302337581016930063,33240442446277000354554629302337581016930064",
"customerOrderNumber": "BR2455090392188U,BR2455090392189U"
}"
Return example

{
code:"1"
msg:"success"
data:[
0:{
billCode:"UT0000352320970"
invoiceAccesskey:"33240442446277000354554629302337581016930063"
customerorderNumber:"BR2455090392188U"
details:[
0:{
scanTime:"2024-04-09 07:30:33"
desc:""
scanType:"assinatura de encomenda"
scanNetworkTypeName:"网点"
scanNetworkName:"叙中村网点"
scanNetworkId:96
scanNetworkProvince:"SP"
scanNetworkCity:"Adamantina"
scanNetworkArea:"Centro"
scanCode:100
signer:"RGM100_新一"
signName:"本人签收"
signatureUrl:""
sigPicUrl:""
}
]
}
1:{
billCode:"UT0000359748995"
invoiceAccesskey:"33240442446277000354554629302337581016930064"
customerorderNumber:"BR2455090392189U"
details:[
0:{
scanTime:"2024-04-09 07:30:33"
desc:""
scanType:"assinatura de encomenda"
scanNetworkTypeName:"网点"
scanNetworkName:"叙中村网点"
scanNetworkId:96
scanNetworkProvince:"SP"
scanNetworkCity:"Adamantina"
scanNetworkArea:"Centro"
scanCode:100
signer:"RGM100_新一"
signName:"本人签收"
signatureUrl:""
sigPicUrl:""
}
]
}
]
}
Error code

1
success
0
fail
145003030
headers signature verification failed
145003040
Internal call exception
145003071
apiAccount is empty!
145003052
digest is empty!
145003053
timestamp is empty!
145005000
System error
145003050
Illegal parameters
145003100
Illegal waybill number
145003502
The quantity of the waybill number exceeds 30