from fastapi import FastAPI, HTTPException
import httpx  # Import ReplitDB
import datetime
import time
import os
import json
import redis
from dotenv import load_dotenv
from fastapi.encoders import jsonable_encoder
from ast import literal_eval

app = FastAPI()
load_dotenv()
# NASA NEO API endpoint
NEO_API_URL = "https://api.nasa.gov/neo/rest/v1/feed"
today = datetime.datetime.today().date().strftime("%Y-%m-%d")
weeklater = (datetime.datetime.now() -
             datetime.timedelta(days=7)).date().strftime("%Y-%m-%d")
pool = redis.ConnectionPool(host=os.environ["REDIS_URL"], port=os.environ["REDIS_PORT"], db=0)
redis = redis.Redis(connection_pool=pool)
# Define a function to retrieve cached data or fetch it if not cached
async def get_cached_or_fetch_data(endpoint_key,
                                   fetch_function,
                                   cache_duration=30):  # 6 hours
    cached_data = redis.get(endpoint_key)

    if cached_data is not None:
        try:
            # Deserialize cached data from JSON
            cached_data = json.loads(cached_data.decode('utf-8'))
            data, timestamp = cached_data

            current_time = time.time()

            if current_time - timestamp <= cache_duration:
                return data  # Return cached data if it's within the expiration window
        except json.JSONDecodeError:
            pass

    # Fetch data and store it in Redis with a timestamp
    data = await fetch_function()
    timestamp = time.time()
    redis.setex(endpoint_key, cache_duration, json.dumps((data, timestamp)))  # Set cache with expiration

    return data


async def fetch_immediate_threat_data():
  try:
    # You need to replace 'YOUR_API_KEY' with your NASA API key
    api_key = os.environ["NASA_API_KEY"]
    print(0)
    params = {"start_date": today, "end_date": weeklater, "api_key": api_key}
    async with httpx.AsyncClient() as client:
      response = await client.get(NEO_API_URL, params=params)
    print(1)
    if response.status_code == 200:
      neo_data = response.json()
      immediate_threat_data = get_immediate_threat_data(neo_data)
      return immediate_threat_data
    else:
      raise HTTPException(status_code=response.status_code,
                          detail="Failed to fetch NEO data")

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


async def fetch_top_threats_data():
  try:
    # You need to replace 'YOUR_API_KEY' with your NASA API key
    print("1")
    api_key = os.environ["NASA_API_KEY"]
    print("2")
    params = {"start_date": today, "end_date": weeklater, "api_key": api_key}
    async with httpx.AsyncClient() as client:
      response = await client.get(NEO_API_URL, params=params)
    print("3")
    if response.status_code == 200:
      neo_data = jsonable_encoder(response.json())
      top_threats_data = get_top_threats_data(neo_data)
      return top_threats_data
    else:
      raise HTTPException(status_code=response.status_code,
                          detail="Failed to fetch NEO data")

  except Exception as e:
    raise HTTPException(status_code=500, detail=str(e))


def get_immediate_threat_data(neo_data):
  immediate_threat_neo = None
  highest_threat_level = 0.0

  # Iterate through NEOs to find the immediate threat
  for date in neo_data["near_earth_objects"]:
    for neo in neo_data["near_earth_objects"][date]:
      if neo["is_potentially_hazardous_asteroid"]:
        # Calculate the diameter
        estimated_diameter_max = neo["estimated_diameter"]["kilometers"][
          "estimated_diameter_max"]
        estimated_diameter_min = neo["estimated_diameter"]["kilometers"][
          "estimated_diameter_min"]
        diameter = (estimated_diameter_max - estimated_diameter_min) / 2.0

        # Calculate normalized distance
        miss_distance = float(
          neo["close_approach_data"][0]["miss_distance"]["kilometers"])
        normalized_distance = (diameter + miss_distance) / 2.0

        # Calculate threat level
        threat_level = normalized_distance / 100000000.0  # You can adjust the scaling factor as needed

        if threat_level > highest_threat_level:
          highest_threat_level = threat_level
          immediate_threat_neo = neo

  if immediate_threat_neo:
    result = {
      "name":
      immediate_threat_neo["name"],
      "diameter": {
        "measure": f"{diameter:.1f}",
        "unit": "meters"
      },
      "closest_date":
      immediate_threat_neo["close_approach_data"][0]["close_approach_date"],
      "speed":
      f"{float(immediate_threat_neo['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']):,.0f} Km/h",
      "threat_level":
      round(highest_threat_level, 2),
      "threat_color":
      "red" if highest_threat_level > 0.5 else
      "green"  # Adjust the threshold as needed
    }
    return result

  return None


def get_top_threats_data(neo_data):
  top_threats = []
  threat_levels = []  # Store threat levels of all potentially hazardous NEOs

  # Iterate through NEOs to calculate and store threat levels
  for date in neo_data["near_earth_objects"]:
    for neo in neo_data["near_earth_objects"][date]:
      if neo["is_potentially_hazardous_asteroid"]:
        # Calculate the diameter
        estimated_diameter_max = neo["estimated_diameter"]["kilometers"][
          "estimated_diameter_max"]
        estimated_diameter_min = neo["estimated_diameter"]["kilometers"][
          "estimated_diameter_min"]
        diameter = (estimated_diameter_max - estimated_diameter_min) / 2.0

        # Calculate normalized distance
        miss_distance = float(
          neo["close_approach_data"][0]["miss_distance"]["kilometers"])
        normalized_distance = (diameter + miss_distance) / 2.0

        # Calculate threat level
        threat_level = normalized_distance / 100000000.0  # You can adjust the scaling factor as needed

        threat_levels.append((neo, threat_level))

  # Sort NEOs by threat level in descending order
  threat_levels.sort(key=lambda x: x[1], reverse=True)

  # Get the top 4 threats (excluding the immediate threat)
  for i in range(1, min(5, len(threat_levels))):
    neo, threat_level = threat_levels[i]
    result = {
      "name": neo["name"],
      "diameter": {
        "measure": f"{diameter:.1f}",
        "unit": "meters"
      },
      "closest_date": neo["close_approach_data"][0]["close_approach_date"],
      "speed":
      f"{float(neo['close_approach_data'][0]['relative_velocity']['kilometers_per_hour']):,.0f} Km/h",
      "threat_level": round(threat_level, 2),
      "threat_color": "red"
      if threat_level > 0.5 else "green"  # Adjust the threshold as needed
    }
    top_threats.append(result)

  return {"top_threats": top_threats}


@app.get("/immediate-threat")
async def get_immediate_threat():
  # Use the caching function to retrieve or fetch data
  return await get_cached_or_fetch_data("immediate_threat_data",
                                        fetch_immediate_threat_data)


@app.get("/top-threats")
async def get_top_threats():
  # Use the caching function to retrieve or fetch data
  return await get_cached_or_fetch_data("top_threats_data",
                                        fetch_top_threats_data)


if __name__ == "__main__":
  import uvicorn

  uvicorn.run(app, host="0.0.0.0", port=8000)
