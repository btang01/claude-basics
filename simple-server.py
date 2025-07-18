from fastmcp import FastMCP

# create mcp server
mcp = FastMCP("user weather server")

#create tool - get city from profile
@mcp.tool 
async def get_city_from_profile(profile: str) -> str:
	"""Get user city from user profile - important, gets pulled from list_tools""" 
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
	"""Get weather from city"""
	try: 
		data = {"boston": "sunny, 80F", "san francisco": "windy, 60F"}

		city = city.strip().lower()

		if city not in data:
			raise ValueError(f"City '{city}' not in data")

		return data[city]

	except Exception as e:
		raise ValueError(f"Error getting weather from city: {str(e)}")


if __name__=="__main__":
	mcp.run()