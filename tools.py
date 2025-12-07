import os
import requests
import orjson as json
from dotenv import load_dotenv
from spoon_ai.tools import BaseTool
from pydantic import Field
import time

load_dotenv()


class MarketDataTool(BaseTool):
    api_key: str | None = None

    def __init__(self):
        super().__init__(
            name="market_data_retriever",
            description="Fetches the average market price of a used item in the UK. The input should be a string describing the item.",
            parameters={"query": Field(..., description="The string description of the item to search for.")}
        )
        self.api_key = os.getenv("PERPLEXITY_API_KEY")
        if not self.api_key or "your-secret" in self.api_key:
            print("WARNING: PERPLEXITY_API_KEY not found. Market tool will use a default value.")
            self.api_key = None

    def execute(self, query: str) -> str:
        price = self.get_average_uk_price(query)
        return f"The average market price for a '{query}' in the UK is approximately £{price:.2f}."

    def _run(self, query: str) -> str:
        return self.execute(query)

    async def _arun(self, query: str) -> str:
        return self.execute(query)

    def get_average_uk_price(self, item_description: str) -> float:
        if not self.api_key: return 180.0
        print(f"TOOL: Querying Perplexity for average price of '{item_description}'...")
        url = "https://api.perplexity.ai/chat/completions"
        prompt = f"What is the average market price for a used '{item_description}' in the UK? Respond with ONLY the price in GBP as a floating-point number. Do not include currency symbols, text, or explanations. Just the number."
        payload = {"model": "sonar", "messages": [{"role": "user", "content": prompt}]}
        headers = {"accept": "application/json", "content-type": "application/json",
                   "authorization": f"Bearer {self.api_key}"}
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            data = response.json()
            price_str = data['choices'][0]['message']['content'].strip()
            price_str_cleaned = ''.join(c for c in price_str if c.isdigit() or c == '.')
            price_float = float(price_str_cleaned)
            print(f"TOOL: Perplexity responded with price: £{price_float:.2f}")
            return price_float
        except Exception as e:
            print(f"TOOL ERROR: Could not get price from Perplexity: {e}")
            return 180.0


# --- FINAL POWER-UP: THE NEO TRANSACTION TOOL ---
class NeoTransactionTool(BaseTool):
    node_url: str = "http://seed1t5.neo.org:20332"

    def __init__(self):
        super().__init__(
            name="neo_transaction_settler",
            description="Connects to the Neo N3 network to get the current block height and executes a mock transaction, returning a mock hash.",
            parameters={
                "seller_address": Field(
                    ...,
                    description="The Neo N3 wallet address of the person receiving the funds."
                )
            }
        )

    # --- NEW METHOD ---
    def get_current_block_height(self) -> str:
        """Fetches only the current block height from the Neo N3 node."""
        try:
            payload = {"jsonrpc": "2.0", "method": "getblockcount", "params": [], "id": 1}
            response = requests.post(self.node_url, json=payload, timeout=3).json()
            # The RPC result is the total number of blocks, so the latest block index is result - 1.
            block_count = response.get("result", 0)
            if block_count > 0:
                latest_block = block_count - 1
                return f"{latest_block:,}"  # Format with commas for readability
            else:
                return "Offline"
        except Exception as e:
            print(f"TOOL INFO: Could not fetch block height: {e}")
            return "Offline"

    # --- END NEW METHOD ---

    def execute(self, seller_address: str) -> dict:
        """The main entry point for the tool."""
        print(f"TOOL: Executing mock Neo transaction to {seller_address}...")
        try:
            # Use the new method internally to get the block height
            block_height_str = self.get_current_block_height()
            if block_height_str == "Offline":
                raise ConnectionError("Could not connect to Neo node to get block height.")

            # Remove comma formatting for internal use
            block_height = int(block_height_str.replace(",", ""))

            tx_hash = f"0x{str(time.time()).replace('.', '')[:64]}"
            return {"success": True, "tx": tx_hash, "block": block_height}
        except Exception as e:
            print(f"TOOL ERROR: Neo connection failed: {e}")
            return {"success": False, "error": "Neo node is offline."}

    def _run(self, seller_address: str) -> str:
        res = self.execute(seller_address)
        return json.dumps(res)

    async def _arun(self, seller_address: str) -> str:
        res = self.execute(seller_address)
        return json.dumps(res)
# --- END POWER-UP ---