# Neo Nomad 🌏
The AI Agent that translates Value, not just Currency.

## End-to-End User Flow
Our complete, end-to-end user flow is as follows:

1.  **Perception:** The user selects their location (e.g., Japan) and enters a product and its price in the local currency (e.g., 50,000 Yen for a camera).
2.  **Contextualisation:** The agent uses a custom SpoonOS Tool to get real-time market data for that item in the user's home market (UK), establishing a "fair value" benchmark.
3.  **Reasoning:** The agent sends all this data—the asking price, the home market value, and the location context—through the SpoonOS LLMManager. The AI reasons about the price difference and determines if it's a fair deal.
4.  **Action (Negotiation):** If the item is overpriced, the agent generates a polite but firm negotiation script in the local language (e.g., Japanese). The user can then play this audio directly to the vendor using our integrated ElevenLabs voice synthesis.
5.  **Action (Settlement):** Once a price is agreed upon, the user enters the seller's wallet address. The agent then calls our NeoTransactionTool, which connects to the Neo N3 TestNet to confirm the live block height and executes a transaction, providing a transaction hash as a receipt.
6.  **Memory:** Every successful purchase is added as a node to a persistent, interactive knowledge graph, building a visual "Nomad's Journey" of the user's travels and purchases.

## Technical Architecture & Hackathon Requirements
We have successfully implemented a robust agentic architecture that not only meets but exceeds the hackathon's requirements.

*   ✅ **SpoonOS LLM Integration (Core Requirement):** Our agent's entire reasoning and language generation process is powered by the spoon_ai.llm.LLMManager. We configured it with a fallback chain (openrouter -> gemini) and environment variables for maximum reliability, demonstrating a best-practice implementation.
*   ✅ **SpoonOS Tool Integration (Core Requirement):** We built two custom tools inheriting from spoon_ai.tools.BaseTool, showcasing a deep understanding of the framework:
    *   **MarketDataTool:** A tool that calls the Perplexity API to fetch real-time pricing data, which is then used as context for the agent's main reasoning step.
    *   **NeoTransactionTool:** This tool encapsulates all blockchain logic. It connects to a live Neo N3 node to get the block height, demonstrating a clean separation of concerns and fulfilling the Neo bonus criterion.

### 🏆 Bonus Achievements
*   **Bonus - Neo Technologies:** Our NeoTransactionTool successfully interacts with the Neo N3 TestNet for every transaction, confirming the network is live by fetching the current block height.
*   **Bonus - Graph Technologies:** Our application features a "Nomad's Journey" knowledge graph built with networkx and pyvis. The agent's "Settle" action directly modifies this graph, creating a persistent memory of the user's economic journey. This is a perfect implementation of the "Graph + Agent" bonus criterion.

## Process & Challenges
Our journey mirrored the real-world challenges of AI engineering. We navigated significant hurdles with Python environment conflicts, library version incompatibilities (elevenlabs, spoon-ai-sdk), and the strict, undocumented requirements of the underlying Pydantic models in the SpoonOS BaseTool. Through systematic debugging—isolating issues in the terminal, inspecting traceback errors, and strategically swapping components like the JSON parser—we successfully built a stable, robust, and feature-complete application.

## Future Vision
Neo Nomad is not just a demo; it's the blueprint for a new class of "sentient" financial tools. The graph-based memory is the foundation for true long-term intelligence, allowing a user to ask their agent questions like, "Where did I get the best deal on electronics?" or "What's my average spending when I'm in France?" This is the future of personalised, agentic finance, built on the flexible and powerful foundation of SpoonOS.
