import asyncio
from typing import Dict, Any
import json
import random
from datetime import datetime, timedelta

# Mock stock data
STOCK_DATA = {
    "AAPL": {"price": 185.50, "change": 2.3, "volume": 52_000_000},
    "GOOGL": {"price": 142.80, "change": -1.2, "volume": 28_000_000},
    "MSFT": {"price": 380.20, "change": 0.8, "volume": 35_000_000},
    "TSLA": {"price": 245.30, "change": -3.5, "volume": 120_000_000},
    "AMZN": {"price": 152.60, "change": 1.5, "volume": 45_000_000}
}

# Define tools
async def get_stock_price(symbol: str) -> Dict[str, Any]:
    """Get current stock price for a given symbol"""
    symbol = symbol.upper()
    if symbol not in STOCK_DATA:
        return {"error": f"Stock symbol {symbol} not found"}
    
    stock = STOCK_DATA[symbol]
    return {
        "symbol": symbol,
        "price": stock["price"],
        "change_percent": stock["change"],
        "timestamp": datetime.now().isoformat()
    }

async def get_stock_volume(symbol: str) -> Dict[str, Any]:
    """Get trading volume for a given stock"""
    symbol = symbol.upper()
    if symbol not in STOCK_DATA:
        return {"error": f"Stock symbol {symbol} not found"}
    
    return {
        "symbol": symbol,
        "volume": STOCK_DATA[symbol]["volume"],
        "average_volume": int(STOCK_DATA[symbol]["volume"] * 0.9),  # Mock average
        "timestamp": datetime.now().isoformat()
    }

async def compare_stocks(symbols: list) -> Dict[str, Any]:
    """Compare multiple stock prices"""
    results = {}
    for symbol in symbols:
        symbol = symbol.upper()
        if symbol in STOCK_DATA:
            results[symbol] = {
                "price": STOCK_DATA[symbol]["price"],
                "change": STOCK_DATA[symbol]["change"]
            }
    
    if not results:
        return {"error": "No valid stock symbols provided"}
    
    # Find best and worst performers
    best = max(results.items(), key=lambda x: x[1]["change"])
    worst = min(results.items(), key=lambda x: x[1]["change"])
    
    return {
        "stocks": results,
        "best_performer": {"symbol": best[0], "change": best[1]["change"]},
        "worst_performer": {"symbol": worst[0], "change": worst[1]["change"]},
        "timestamp": datetime.now().isoformat()
    }

# Tool registry
TOOLS = {
    "get_stock_price": {
        "function": get_stock_price,
        "description": "Get current price for a stock symbol",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol (e.g., AAPL)"}
            },
            "required": ["symbol"]
        }
    },
    "get_stock_volume": {
        "function": get_stock_volume,
        "description": "Get trading volume information for a stock",
        "parameters": {
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"}
            },
            "required": ["symbol"]
        }
    },
    "compare_stocks": {
        "function": compare_stocks,
        "description": "Compare prices and performance of multiple stocks",
        "parameters": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of stock symbols to compare"
                }
            },
            "required": ["symbols"]
        }
    }
}

class StockAgent:
    """Simple stock market agent that can use tools to answer questions"""
    
    def __init__(self):
        self.tools = TOOLS
        self.conversation_history = []
    
    async def process_query(self, query: str) -> str:
        """Process a user query and return a response"""
        # Simple pattern matching for tool selection
        query_lower = query.lower()
        
        if "compare" in query_lower or "versus" in query_lower or "vs" in query_lower:
            # Extract stock symbols (simple approach)
            symbols = []
            for word in query.split():
                word_clean = word.strip('.,?!')
                if word_clean.upper() in STOCK_DATA:
                    symbols.append(word_clean)
            
            if len(symbols) >= 2:
                result = await self.tools["compare_stocks"]["function"](symbols)
                return self._format_comparison(result)
        
        elif "volume" in query_lower:
            # Find stock symbol in query
            for word in query.split():
                word_clean = word.strip('.,?!')
                if word_clean.upper() in STOCK_DATA:
                    result = await self.tools["get_stock_volume"]["function"](word_clean)
                    return self._format_volume(result)
        
        elif "price" in query_lower or any(symbol in query.upper() for symbol in STOCK_DATA):
            # Find stock symbol in query
            for word in query.split():
                word_clean = word.strip('.,?!')
                if word_clean.upper() in STOCK_DATA:
                    result = await self.tools["get_stock_price"]["function"](word_clean)
                    return self._format_price(result)
        
        return "I can help you with stock prices, volumes, and comparisons. Try asking about specific stocks like AAPL, GOOGL, MSFT, TSLA, or AMZN."
    
    def _format_price(self, result: Dict[str, Any]) -> str:
        if "error" in result:
            return result["error"]
        
        change_sign = "+" if result["change_percent"] >= 0 else ""
        return f"{result['symbol']} is currently trading at ${result['price']:.2f} ({change_sign}{result['change_percent']}%)"
    
    def _format_volume(self, result: Dict[str, Any]) -> str:
        if "error" in result:
            return result["error"]
        
        return f"{result['symbol']} volume: {result['volume']:,} shares (avg: {result['average_volume']:,})"
    
    def _format_comparison(self, result: Dict[str, Any]) -> str:
        if "error" in result:
            return result["error"]
        
        response = "Stock Comparison:\n"
        for symbol, data in result["stocks"].items():
            change_sign = "+" if data["change"] >= 0 else ""
            response += f"- {symbol}: ${data['price']:.2f} ({change_sign}{data['change']}%)\n"
        
        response += f"\nBest performer: {result['best_performer']['symbol']} (+{result['best_performer']['change']}%)"
        response += f"\nWorst performer: {result['worst_performer']['symbol']} ({result['worst_performer']['change']}%)"
        
        return response

# Demo function
async def main():
    agent = StockAgent()
    
    # Test queries
    test_queries = [
        "What's the price of AAPL?",
        "Show me the volume for TSLA",
        "Compare AAPL vs GOOGL vs MSFT",
        "How is Tesla doing?",
        "Compare tech stocks AAPL and AMZN"
    ]
    
    print("Stock Market Agent Demo")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\nUser: {query}")
        response = await agent.process_query(query)
        print(f"Agent: {response}")

if __name__ == "__main__":
    asyncio.run(main())