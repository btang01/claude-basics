from fastmcp import FastMCP
import os
import aiohttp

# create mcp server
mcp = FastMCP("user weather server")

# Load OpenWeatherMap API key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "your_api_key_here")

#create tool - get city from profile
@mcp.tool 
async def get_city_from_profile(profile: str) -> str:
	"""Get user city from user profile - important, gets pulled from list_tools""" 
	try:
		# data = {"brian": "boston", "jocelyn": "san francisco"}
		profile = profile.strip().lower()

		if profile not in data:
			raise ValueError(f"profile '{profile}' not in data")

		return data[profile]

	except Exception as e:
		raise ValueError(f"Error getting city from profile: {str(e)}")


#create tool - get weather from city
@mcp.tool
async def get_weather_from_city(city: str) -> str:
	"""Get current weather for a city using OpenWeatherMap"""

	url = f"https://api.openweathermap.org/data/2.5/weather?q={city.strip().lower()}&appid={OPENWEATHER_API_KEY}&units=imperial"

	# data = {"boston": "sunny, 80F", "san francisco": "windy, 60F"}
	async with aiohttpClientSession() as session:
		async with session.get(url) as resp:
			data = await resp.json()

	weather = data["weather"][0]["description"]
	temp = data["main"]["temp"]

	return f"{weather}, {temp}F"

if __name__=="__main__":
	mcp.run()