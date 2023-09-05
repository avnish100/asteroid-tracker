# asteroid-tracker
An API to warn users about potentially dangerous Near Earth Objects (NEOs). The NEO data is fetched from NASAs NEO feed APi and then filtered to return only the NEOs with the highest percieved threat level.
This API also uses redis to cache the fetched data for 6 hours to prevent any rate-limiting the user might face.

## Usage
The REST API is described below
## Fetching the immediate threat to Earth
  Returns the the NEO with the highest percieved threat level, calculated by taking into account the closest apporach date as well as the object diameter. The "threat_level" is one a scale of 0-1 and helps determine the "threat_color"
  
`GET /immediate-threat`

    curl -i -H 'Accept: application/json' http://localhost:8000/immediate-threat
    HTTP/1.1 200 OK
    date: Tue, 05 Sep 2023 06:40:28 GMT
    server: uvicorn
    content-length: 172
    content-type: application/json
    
    {"name":"3671 Dionysus (1984 KD)","diameter":{"measure":"0.1","unit":"meters"},
    "closest_date":"2023-09-03","speed":"74,577 Km/h","threat_level":0.36,"threat_color":"green"}
    
## Fetching the top 5 threats to Earth
Returns the top 5 potentially dangerous NEOs sorted based on the "threat_level" calculated in the same fashion as the previous endpoint.
    
`GET /top-threats`

    curl -i -H 'Accept: application/json' http://localhost:8000/top-threats
    HTTP/1.1 200 OK
    date: Tue, 05 Sep 2023 06:48:39 GMT
    server: uvicorn
    content-length: 680
    content-type: application/json
    
    {"top_threats":[{"name":"164400 (2005 GN59)","diameter":{"measure":"0.1","unit":"meters"},"closest_date":"2023-09-03",
    "speed":"86,052 Km/h","threat_level":0.35,"threat_color":"green"},{"name":"414286 (2008 OC6)","diameter":{"measure":"0.1"
    ,"unit":"meters"},"closest_date":"2023-08-31","speed":"78,738 Km/h","threat_level":0.34,"threat_color":"green"},{"name":"
    (2007 RF2)","diameter":{"measure":"0.1","unit":"meters"},"closest_date":"2023-09-04","speed":"116,835 Km/h",
    "threat_level":0.32,"threat_color":"green"},{"name":"365014 (2008 OX2)","diameter":{"measure":"0.1","unit":"meters"},
    "closest_date":"2023-09-02","speed":"43,181 Km/h","threat_level":0.31,"threat_color":"green"}]}
