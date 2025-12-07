import streamlit as st
import requests
import time
import orjson as json
import asyncio
import os
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import networkx as nx
from pyvis.network import Network
import streamlit.components.v1 as components
from pydantic import Field

# --- GLOBAL AGENT UPGRADE (Country Context) ---
COUNTRY_CONTEXT = {
    "Japan": {"currency": "Yen", "language": "Japanese", "voice": "Mimi", "rate_to_gbp": 0.0052},
    "France": {"currency": "Euro", "language": "French", "voice": "Nicole", "rate_to_gbp": 0.85},
    "USA": {"currency": "Dollar", "language": "English", "voice": "Rachel", "rate_to_gbp": 0.79},
    "Brazil": {"currency": "Real", "language": "Portuguese", "voice": "Camila", "rate_to_gbp": 0.15}
}
# --- END UPGRADE ---

load_dotenv()

try:
    from spoon_ai.llm import LLMManager, ConfigurationManager
    from spoon_ai.schema import Message
    # Import BOTH tools now
    from tools import MarketDataTool, NeoTransactionTool

    SPOON_AVAILABLE = True
    try:
        from spoon_ai import __version__ as spoon_version
    except ImportError:
        spoon_version = "0.3.4 (installed)"
    SPOON_VERSION = spoon_version
except ImportError:
    st.error("FATAL: SpoonOS SDK could not be imported.")
    SPOON_AVAILABLE = False
    SPOON_VERSION = "Not Detected"


    class LLMManager:
        pass


    class ConfigurationManager:
        pass


    class MarketDataTool:
        pass


    class NeoTransactionTool:
        # Add dummy class with the new method for when SDK is not found
        def get_current_block_height(self):
            return "Offline"


    class Message:
        pass

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")


class VoiceModule:
    def __init__(self, api_key):
        self.api_key = api_key
        if self.api_key and "your-secret" not in self.api_key:
            self.client = ElevenLabs(api_key=self.api_key)
        else:
            self.client = None

    def speak(self, text, voice_name="Mimi"):
        if not self.client: return st.warning("ElevenLabs API Key not set.")
        try:
            audio_generator = self.client.text_to_speech.convert(
                voice_id="EXAVITQu4vr4xnSDxMaL", text=text, model_id="eleven_multilingual_v2")
            audio_bytes = b"".join(audio_generator)
            st.audio(audio_bytes, format="audio/mp3", autoplay=True)
        except Exception as e:
            st.error(f"Voice Error: {e}")


class NeoNomadAgent:
    def __init__(self):
        self.name = "NeoNomad"
        self.voice_tool = VoiceModule(ELEVENLABS_API_KEY)

        if 'journey_graph' not in st.session_state:
            st.session_state.journey_graph = nx.DiGraph()
            st.session_state.journey_graph.add_node("Me", label="Me", title="Starting Point", color="#FF5733", size=25)

        if SPOON_AVAILABLE:
            config_manager = ConfigurationManager()
            self.llm_manager = LLMManager(config_manager)
            self.market_tool = MarketDataTool()
            self.neo_tx_tool = NeoTransactionTool()  # Initialize the new tool
            self.llm_manager.set_fallback_chain(["openrouter", "gemini"])
            print("SpoonOS agent initialized successfully.")
        else:
            self.llm_manager = None
            self.market_tool = None
            self.neo_tx_tool = NeoTransactionTool()  # Use dummy class if not available

    async def run_cycle(self, item, ask_price_local, country_context):
        # This method is now perfect.
        language, currency, rate_gbp = country_context["language"], country_context["currency"], country_context[
            "rate_to_gbp"]
        cost_gbp = ask_price_local * rate_gbp
        if not self.llm_manager or not self.market_tool: return {}
        fair_value_gbp = self.market_tool.get_average_uk_price(item)

        prompt = f"""
        You are a JSON API. Your ONLY job is to analyze the following data and return a single, valid JSON object.
        You are an expert negotiator for a world traveler currently in {country_context['name']}.

        DATA:
        - Item: "{item}"
        - Asking Price ({currency}): {ask_price_local}
        - Asking Price (GBP): {cost_gbp:.2f}
        - Real-time Fair Market Value in UK (GBP): {fair_value_gbp:.2f}

        RULES:
        1. Compare the asking price to the fair value. If it's overpriced by more than £20, the status is 'overpriced'.
        2. The "script" field MUST be a polite but firm negotiation script written in {language}.
        3. The "reasoning" field MUST remain in English.
        4. Your entire response MUST be ONLY the JSON object and nothing else. Do not add any text, explanations, or markdown formatting.

        You MUST follow this exact nested JSON structure:
        {{
            "metrics": {{"ask_gbp": {cost_gbp:.2f}, "fair_gbp": {fair_value_gbp:.2f}}},
            "insight": {{"status": "...", "reasoning": "..."}},
            "action": {{"label": "...", "script": "..."}}
        }}
        """

        messages = [Message(role="user", content=prompt)]

        try:
            response = await self.llm_manager.chat(messages)
            raw_content = response.content

            import re
            json_match = re.search(r'\{.*\}', raw_content, re.DOTALL)
            if not json_match:
                raise ValueError(
                    f"Could not find a valid JSON object in the LLM response. The API returned: '{raw_content}'")

            json_string = json_match.group(0)
            analysis = json.loads(json_string)
            return analysis
        except Exception as e:
            st.error(f"SpoonOS LLM Error: {e}")
            return {}

    def execute_transaction(self, amount, currency, item_name, location, seller_address):
        if not self.neo_tx_tool or not SPOON_AVAILABLE: return {"success": False, "error": "Neo tool not available."}

        # The agent's job is to call the tool with the correct parameters.
        res = self.neo_tx_tool.execute(seller_address=seller_address)

        if res['success']:
            graph = st.session_state.journey_graph
            item_node_id = f"{item_name}_{int(time.time())}"
            graph.add_node(item_node_id, label=item_name, title=f"{amount} {currency}", color="#97C2FC")
            if not graph.has_node(location):
                graph.add_node(location, label=location, title="Location", color="#DAF7A6")
            graph.add_edge("Me", location, label="Visited")
            graph.add_edge(location, item_node_id, label="Purchased")
        return res


async def run_agent_analysis(agent_instance, item, price, context):
    st.session_state.context = context
    decision = await agent_instance.run_cycle(item, price, context)
    st.session_state['decision'] = decision
    st.session_state['step'] = 1


agent = NeoNomadAgent()

st.set_page_config(page_title="Neo Nomad", page_icon="🌏", layout="wide")

with st.sidebar:
    st.image("https://cryptologos.cc/logos/neo-neo-logo.png", width=40)
    st.header("System Status")
    if SPOON_AVAILABLE:
        st.success(f"🥄 **SpoonOS SDK v{SPOON_VERSION}**\n\nStatus: `Active`")
    else:
        st.warning(f"🥄 **SpoonOS SDK**\n\nStatus: `Not Detected`")

    # --- CHANGE IS HERE ---
    # Get block height from the tool instance on the agent and display it
    block_height = agent.neo_tx_tool.get_current_block_height()
    st.metric("Neo N3 Block Height", block_height)
    # --- END CHANGE ---

st.title("Neo Nomad 🌏")
st.markdown("**The Agentic Wallet for the Sentient Economy.**")
st.caption("Powered by SpoonOS x Neo N3 x ElevenLabs x Pyvis")
st.divider()

col_left, col_right = st.columns([1, 1])

with col_left:
    st.subheader("🛍️ Perception")
    selected_country = st.selectbox("Select your current location", options=list(COUNTRY_CONTEXT.keys()))
    context = COUNTRY_CONTEXT[selected_country]
    context["name"] = selected_country
    item_in = st.text_input("Item", "Used Canon AE-1 Camera")
    price_in = st.number_input(f"Ask Price ({context['currency']})", 1, 1000000, 50000, step=100)

    if st.button("🤖 Agent: Analyse", type="primary"):
        with st.spinner("SpoonOS Agent is using tools and reasoning..."):
            asyncio.run(run_agent_analysis(agent, item_in, price_in, context))
        st.rerun()

with col_right:
    st.subheader("🧠 Reasoning")
    if 'decision' in st.session_state and st.session_state.decision:
        data = st.session_state.decision
        st.code(
            f"> INPUT: {price_in} {st.session_state.context['currency'].upper()}\n> REAL-TIME DATA: UK FAIR VALUE £{data['metrics']['fair_gbp']:.2f}\n> THOUGHT: {data['insight']['reasoning']}")
        c_a, c_b = st.columns(2)
        c_a.metric("Your Cost", f"£{data['metrics']['ask_gbp']:.2f}")
        c_b.metric("Fair Value", f"£{data['metrics']['fair_gbp']:.2f}")
        if data['insight']['status'] == "overpriced":
            st.error("🚨 **RIP-OFF DETECTED**")
        else:
            st.success("✅ **Fair Price Detected**")

if 'decision' in st.session_state and st.session_state.decision:
    data = st.session_state.decision
    st.markdown("---")
    st.subheader("⚡ Action")
    act_col1, act_col2 = st.columns(2)
    with act_col1:
        if st.button(f"🗣️ {data['action']['label']} (Voice)"):
            st.info(f"Agent says: '{data['action']['script']}'")
            agent.voice_tool.speak(data['action']['script'], voice_name=st.session_state.context["voice"])
    with act_col2:
        # --- WALLET ADDRESS UPGRADE ---
        seller_address = st.text_input("Seller's Neo Wallet Address", "Nbn72p1Qhp1aZ3fgDRaC2s2j5T35S3bWc4")
        if st.button("💸 Settle (Neo N3)"):
            res = agent.execute_transaction(price_in, st.session_state.context["currency"], item_in,
                                            location=st.session_state.context["name"], seller_address=seller_address)
            if res['success']:
                st.balloons()
                st.success(f"Transaction to {seller_address[:10]}... Finalized on Neo N3 (Block: {res['block']})")
                st.code(f"Tx Hash (Mock): {res['tx']}")
            else:
                st.error(f"Transaction Failed: {res.get('error', 'Unknown error')}")
            st.rerun()
        # --- END UPGRADE ---

if 'journey_graph' in st.session_state and len(st.session_state.journey_graph.nodes) > 1:
    st.markdown("---")
    st.subheader("🌍 My Nomad's Journey")
    st.caption("This graph is built in real-time as you make purchases.")
    try:
        net = Network(height='450px', width='100%', bgcolor='#222222', font_color='white', notebook=True,
                      cdn_resources='in_line')
        net.from_nx(st.session_state.journey_graph)
        net.show_buttons(filter_=['physics'])
        net.show('journey_graph.html')
        components.html(open('journey_graph.html', 'r', encoding='utf-8').read(), height=475)
    except Exception as e:
        st.error(f"Could not render graph: {e}")