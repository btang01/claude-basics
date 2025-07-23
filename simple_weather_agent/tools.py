from fastmcp import FastMCP
import os
import aiohttp
from pydantic import BaseModel, Field

# create mcp server
mcp = FastMCP("user weather server")

# args in tools.py needs to match pydantic models.py so that client can pick up descriptions properly without breaking stuff

#create tool - get city from name
@mcp.tool
async def get_city_from_name(name: str) -> str:
	"""Get user city, context like notes from first name""" 
	try:
		data = [
				{
					"id": "brian1",
					"first_name": "Brian",
					"last_name": "Wang",
					"department": "Engineering",
					"job_title": "Solutions Architect",
					"email": "brian.wang@company.com",
					"locations": [
					{ "city": "Boston", "state": "MA", "country": "USA", "effective_date": "2024-06-01" }
					],
					"notes": [
					"Works at AWS",
					"Leads cloud migration projects"
					],
					"last_updated": "2025-07-23T10:15:00Z"
				},
				{
					"id": "brian2",
					"first_name": "Brian",
					"last_name": "Johnson",
					"department": "Marketing",
					"job_title": "Campaign Manager",
					"email": "brian.johnson@company.com",
					"locations": [
					{ "city": "Seattle", "state": "WA", "country": "USA", "effective_date": "2024-02-15" }
					],
					"notes": [
					"Plays hockey with you",
					"Manages product launch events"
					],
					"last_updated": "2025-07-20T08:00:00Z"
				},
				{
					"id": "brian3",
					"first_name": "Brian",
					"last_name": "Smith",
					"department": "Accounting",
					"job_title": "Financial Analyst",
					"email": "brian.smith@company.com",
					"locations": [
					{ "city": "Chicago", "state": "IL", "country": "USA", "effective_date": "2023-11-10" }
					],
					"notes": [
					"Specializes in tax compliance",
					"Recently transferred from NY office"
					],
					"last_updated": "2025-06-30T12:45:00Z"
				},
				{
					"id": "kristina1",
					"first_name": "Kristina",
					"last_name": "Lopez",
					"department": "Design",
					"job_title": "UX Researcher",
					"email": "kristina.lopez@company.com",
					"locations": [
					{ "city": "San Francisco", "state": "CA", "country": "USA", "effective_date": "2024-08-12" }
					],
					"notes": [
					"Focuses on accessibility",
					"Leads cross-functional user studies"
					],
					"last_updated": "2025-07-10T14:25:00Z"
				},
				{
					"id": "kristina2",
					"first_name": "Kristina",
					"last_name": "Patel",
					"department": "Sales",
					"job_title": "Account Executive",
					"email": "kristina.patel@company.com",
					"locations": [
					{ "city": "Austin", "state": "TX", "country": "USA", "effective_date": "2024-04-20" }
					],
					"notes": [
					"Top-performing sales rep in Q2",
					"Speaks at industry conferences"
					],
					"last_updated": "2025-07-15T09:30:00Z"
				}
			]

		name = name.strip().lower()

		for record in data:
			if record["first_name"].lower() == name:
				return record["locations"][0]["city"]

		# If not found
		raise ValueError(f"name '{name}' not in data")

	except Exception as e:
		raise ValueError(f"Error getting city from name: {str(e)}")


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