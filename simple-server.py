from fastmcp import FastMCP
import os
import aiohttp

# create mcp server
mcp = FastMCP("user weather server")

#create tool - get city from profile
@mcp.tool
async def get_city_from_profile(profile: str) -> str:
	"""Get user city from user profile""" 
	try:
		data = {"brian": "boston", "jocelyn": "san francisco"}
		profile = profile.strip().lower()

		if profile not in data:
			raise ValueError(f"profile '{profile}' not in data")

		return data[profile]

	except Exception as e:
		raise ValueError(f"Error getting city from profile: {str(e)}")


#create tool - get weather from city
@mcp.tool
async def get_weather_from_city(city: str) -> str:
	"""Get current weather for a city"""

	city = city.strip().lower()
	data = {"boston": "sunny, 80F", "san francisco": "windy, 60F"}
	return data[city]

if __name__=="__main__":
	print("Starting MCP server on http://localhost:8000")
	mcp.run(transport="http", host="localhost", port=8000)