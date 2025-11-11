"""Chat Handler - Orchestrates RAG and LLM."""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import yaml
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bedrock").lower()

try:
    import boto3
    from botocore.config import Config
except ImportError:
    print("Warning: boto3 not installed. Run: pip install boto3")
try:
    from langchain_aws import ChatBedrock
    # LangChain 0.2.x import paths
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    # create_react_agent may not exist in some 0.2.x builds; import defensively
    try:
        from langchain.agents import create_react_agent  # type: ignore
    except Exception:
        create_react_agent = None  # type: ignore
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import BaseMessage
    from langchain.memory import ConversationBufferWindowMemory
except ImportError as e:
    print(f"Warning: LangChain components not installed. Run: pip install langchain langchain-aws. Error: {e}")
    ChatBedrock = None
    create_tool_calling_agent = None
    AgentExecutor = None
    ChatPromptTemplate = None
    ConversationBufferWindowMemory = None
    BaseMessage = None

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
import asyncio
try:
    from factor_sync import FactorSync
except ImportError:
    print("Warning: FactorSync not imported")
    FactorSync = None

try:
    from rag_retriever import RAGRetriever
except ImportError:
    print("Warning: RAGRetriever not imported")
    RAGRetriever = None

try:
    from news_retriever import NewsRetriever
except ImportError:
    print("Warning: NewsRetriever not imported")
    NewsRetriever = None

try:
    from tools import get_tools
except ImportError:
    print("Warning: Tools not imported")
    get_tools = None


class ChatHandler:
    """Handles conversation flow and orchestrates components."""

    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.llm_client = None
        self.rag_retriever = None
        self.factor_sync = None
        self.news_retriever = None
        self.agent_executor = None
        self.conversation_history = {}
        self.agent_type = None  # Track which agent type is being used

        self._load_config()
        self._init_components()

    def _load_config(self):
        """Load configuration."""
        config_file = Path(__file__).parent.parent / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
        else:
            # Fallback config
            self.config = {
                "llm": {
                    "provider": LLM_PROVIDER,
                    "model": "mistral.mixtral-8x7b-instruct-v0:1",
                    "temperature": 0.7,
                    "max_tokens": 2000,
                    "region": "us-east-1"
                },
                "rag": {
                    "top_k": 3
                }
            }

    def _init_components(self):
        """Initialize RAG, MCP, and LLM clients."""
        provider = self.config["llm"].get("provider", LLM_PROVIDER).lower()
        self.provider = provider

        # Initialize components regardless of provider first
        print(f"LLM Provider: {self.provider}")

        # Initialize FactorSync for Backend integration
        if FactorSync:
            self.factor_sync = FactorSync()
            print("FactorSync initialized - Backend integration enabled")

        # Initialize RAG retriever
        if RAGRetriever:
            self.rag_retriever = RAGRetriever(self.config.get("rag", {}))
            print("RAG Retriever initialized - Knowledge base loaded")

        # Initialize News retriever
        if NewsRetriever:
            backend_url = os.getenv("BACKEND_URL", "http://backend:8000/api/v1")
            self.news_retriever = NewsRetriever(backend_url)
            print(f"News Retriever initialized - Backend URL: {backend_url}")

        # Initialize LangChain Agent if provider is bedrock
        if self.provider == "bedrock":
            if not get_tools:
                print("Warning: get_tools not available. Agent will not be initialized.")
                return

            try:
                # 1. Initialize LLM with AWS credentials
                print("Step 1: Initializing LLM client...")
                aws_region = os.getenv("AWS_REGION", self.config["llm"].get("region", "us-east-1"))
                # Use default AWS credential chain (env, profile, ECS/EKS, instance role)
                if not ChatBedrock:
                    print("Warning: ChatBedrock not available. Install langchain-aws.")
                    return

                self.llm_client = ChatBedrock(
                    region_name=aws_region,
                    model_id=os.getenv("BEDROCK_MODEL_ID", self.config["llm"]["model"]),
                    model_kwargs={
                        "temperature": self.config["llm"]["temperature"],
                        "max_tokens": self.config["llm"]["max_tokens"],
                    },
                    streaming=False,
                )
                print(f"Step 1 OK: Using AWS Bedrock - Region: {aws_region}, Model: {self.llm_client.model_id}")

                # 2. Initialize Tools
                print("Step 2: Initializing tools...")
                tools = get_tools(
                    news_retriever=self.news_retriever,
                    factor_sync=self.factor_sync
                )
                print(f"Step 2 OK: Tools initialized: {[tool.name for tool in tools]}")

                # 3. Create Agent with system prompt
                print("Step 3: Loading system prompt...")
                # Ensure prompt_path is correct relative to the project root or current file
                # Assuming system.txt is in SL-ChatBot/chatbot/prompts
                prompt_path = Path(__file__).parent.parent.parent / "chatbot" / "prompts" / "system.txt"
                system_prompt = prompt_path.read_text(encoding='utf-8') if prompt_path.exists() else "You are a quant investment advisor."
                print(f"Step 3 OK: System prompt loaded ({len(system_prompt)} chars)")

                # 4. Create Agent Prompt Template(s)
                print("Step 4: Creating prompt templates...")
                # Tool-calling models (e.g., Anthropic Claude 3) can use the tool-calling agent.
                # For models without native tool-calling (e.g., Meta Llama, Mistral), use ReAct agent.
                tool_calling_prompt = ChatPromptTemplate.from_messages([
                    (
                        "system",
                        system_prompt
                        + "\n\nYou have access to the following tools and must call them when needed."
                        + "\n\n{agent_scratchpad}"
                    ),
                    MessagesPlaceholder("chat_history"),
                    ("user", "Context:\n{context}\n\nQuestion: {input}"),
                ])

                # Format tool list for ReAct prompt
                tool_strings = "\n".join([f"{tool.name}: {tool.description}" for tool in tools])

                react_prompt = ChatPromptTemplate.from_messages([
                    (
                        "system",
                        system_prompt
                        + "\n\nYou can use the following tools:\n" + tool_strings
                        + "\n\nWhen needed, follow this ReAct format strictly:\n"
                          "Question: {input}\n"
                          "Thought: You should think about what to do next\n"
                          "Action: <tool name>\n"
                          "Action Input: <JSON input>\n"
                          "Observation: <tool result>\n"
                          "... (repeat Thought/Action/Action Input/Observation as needed)\n"
                          "Final Answer: <concise answer using observations>\n"
                        + "\n\n{agent_scratchpad}"
                    ),
                    MessagesPlaceholder("chat_history"),
                    ("user", "Context:\n{context}\n\nQuestion: {input}"),
                ])
                print("Step 4 OK: Prompts created")

                # 5. Create Agent and AgentExecutor
                print("Step 5: Creating agent and executor...")
                model_id = getattr(self.llm_client, "model_id", "").lower()
                # Tool-calling models: Claude, Llama 3.1+, etc.
                supports_tool_calling = (
                    ("anthropic" in model_id) or
                    ("claude" in model_id) or
                    ("llama3-1" in model_id) or  # Llama 3.1 supports tool-calling
                    ("llama-3.1" in model_id)
                )
                # Nova and Mistral models use ReAct instead of tool-calling
                is_nova = "nova" in model_id
                is_mistral = "mistral" in model_id
                print(f"  Model: {model_id}, Supports tool calling: {supports_tool_calling}, Is Nova: {is_nova}, Is Mistral: {is_mistral}")
                # If ReAct agent factory is unavailable, fall back to tool-calling agent
                # Nova and Mistral models use ReAct format instead of tool-calling
                if (is_nova or is_mistral) and create_react_agent is not None:
                    print("  Using ReAct agent (Nova model)...")
                    try:
                        agent = create_react_agent(self.llm_client, tools, react_prompt)  # type: ignore
                        self.agent_type = "react"
                    except ValueError as ve:
                        print(f"  ReAct agent creation failed: {ve}")
                        print("  Falling back to tool-calling agent...")
                        agent = create_tool_calling_agent(self.llm_client, tools, tool_calling_prompt)
                        self.agent_type = "tool_calling"
                elif supports_tool_calling or (create_react_agent is None):
                    print("  Using tool-calling agent...")
                    agent = create_tool_calling_agent(self.llm_client, tools, tool_calling_prompt)
                    self.agent_type = "tool_calling"
                else:
                    print("  Using ReAct agent...")
                    try:
                        agent = create_react_agent(self.llm_client, tools, react_prompt)  # type: ignore
                        self.agent_type = "react"
                    except ValueError as ve:
                        print(f"  ReAct agent creation failed: {ve}")
                        print("  Falling back to tool-calling agent...")
                        agent = create_tool_calling_agent(self.llm_client, tools, tool_calling_prompt)
                        self.agent_type = "tool_calling"
                print(f"  Agent created ({self.agent_type}), creating AgentExecutor...")
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    return_intermediate_steps=True,
                    handle_parsing_errors=True
                )
                print("Step 5 OK: AgentExecutor created")

                print("LangChain AgentExecutor created successfully.")
            except Exception as e:
                print(f"Error initializing LangChain agent: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"Warning: Agent initialization skipped. Provider={self.provider}, get_tools={get_tools is not None}")

    async def handle(self, message: str, session_id: Optional[str] = None) -> dict:
        """Handle user message.

        Args:
            message: User input
            session_id: Optional session ID

        Returns:
            Response dictionary
        """
        # 1. Classify intent
        intent = await self._classify_intent(message)

        # For 'theme_search', guide the LLM to perform a market analysis
        if intent == 'theme_search':
            # Prepend a clear instruction to the user message
            message = f"'get_theme_sentiment_summary' 도구를 사용하여 현재 시장의 주요 테마 동향을 '유형 4' 형식으로 분석하고 관련주를 제안해줘. 사용자의 원래 질문: '{message}'"
            print(f"Guiding LLM for theme_search. New message: {message}")

        # 2. Retrieve relevant knowledge (RAG)
        context = await self._retrieve_context(message, intent)

        # 3. Generate response with LangChain Agent
        response = await self._generate_response_langchain(
            message, intent, context, session_id
        )

        return response

    async def _classify_intent(self, message: str) -> str:
        """Classify user intent.

        Returns:
            Intent type: 'explain', 'recommend', 'build', 'general'
        """
        message_lower = message.strip().lower()

        # "종목 추천"과 같은 일반적인 추천 요청을 'theme_search'로 분류
        if "종목 추천" in message_lower or message_lower == "종목추천":
            return 'theme_search'
        
        if any(word in message_lower for word in ['전략 추천', 'recommend', '전략']):
            return 'recommend'
        elif any(word in message_lower for word in ['설명', 'explain', '뭐', '무엇']):
            return 'explain'
        elif any(word in message_lower for word in ['조건', 'condition', '만들']):
            return 'build'
        else:
            return 'general'

    async def _retrieve_context(self, message: str, intent: str) -> str:
        """Retrieve relevant context from RAG and Backend."""
        context_parts = []

        # 1. Backend 팩터 정보 조회
        if self.factor_sync and intent in ["recommend", "build"]:
            try:
                # 메시지에서 팩터 키워드 추출 시도
                message_lower = message.lower()

                # 전략 키워드 매핑
                strategy_keywords = {
                    "가치": "value", "저평가": "value", "per": "value", "pbr": "value",
                    "성장": "growth", "매출": "growth", "이익": "growth",
                    "우량": "quality", "roe": "quality", "roa": "quality",
                    "모멘텀": "momentum", "추세": "momentum", "수익률": "momentum",
                    "배당": "dividend"
                }

                detected_strategy = None
                for keyword, strategy in strategy_keywords.items():
                    if keyword in message_lower:
                        detected_strategy = strategy
                        break

                if detected_strategy:
                    # 전략별 팩터 정보 가져오기
                    strategy_info = await self.factor_sync.build_strategy_recommendation(detected_strategy)
                    context_parts.append(f"전략: {strategy_info['description']}")
                    context_parts.append(f"주요 팩터: {', '.join(strategy_info['primary_factors'])}")
                else:
                    # 전체 팩터 목록 요약
                    all_factors = await self.factor_sync.get_all_factors()
                    if all_factors:
                        factor_summary = f"사용 가능한 팩터 수: {len(all_factors)}"
                        context_parts.append(factor_summary)
            except Exception as e:
                print(f"Backend context retrieval error: {e}")

        # 2. RAG 지식 베이스 검색 (설명 의도일 때만)
        if self.rag_retriever and intent == "explain":
            try:
                rag_context = self.rag_retriever.get_context(
                    message,
                    top_k=self.config.get("rag", {}).get("top_k", 3)
                )
                if rag_context:
                    context_parts.append(f"\n[지식 베이스]\n{rag_context}")
            except Exception as e:
                print(f"RAG retrieval error: {e}")

        # 3. 뉴스 검색은 Claude의 Tool Use로 처리 (자동 검색 비활성화)
        # Claude가 필요시 search_stock_news 도구를 직접 호출합니다

        return "\n".join(context_parts) if context_parts else ""

    async def _generate_response_langchain(
        self,
        message: str,
        intent: str,
        context: str,
        session_id: Optional[str]
    ) -> dict:
        """Generate response using LangChain Agent."""
        if not self.agent_executor:
            error_msg = (
                "LangChain Agent not initialized. "
                f"Provider: {self.provider}, "
                f"LLM Client: {self.llm_client is not None}, "
                f"ChatBedrock available: {ChatBedrock is not None}"
            )
            print(error_msg)
            return {
                "answer": error_msg,
                "intent": intent
            }

        # Get or create conversation memory for the session
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = ConversationBufferWindowMemory(
                k=5, memory_key="chat_history", return_messages=True
            )
        memory = self.conversation_history[session_id]

        try:
            # Use asyncio.to_thread to run the synchronous invoke method in a separate thread
            # Pass inputs in a structured dictionary, not a single message list
            chat_history = memory.load_memory_variables({})["chat_history"]
            # Ensure chat_history is a list of BaseMessage objects
            if isinstance(chat_history, str):
                chat_history = []

            # Prepare invoke input
            # Note: agent_scratchpad is required for both tool-calling and ReAct agents
            # Pass as empty string for initial invocation
            invoke_input = {
                "input": message,
                "context": context,
                "chat_history": chat_history,
                "agent_scratchpad": ""  # Required by both agent types
            }


            response = await asyncio.to_thread(
                self.agent_executor.invoke,
                invoke_input
            )

            answer = response.get("output", "No response generated.")

            # Manually save conversation history to the session's memory
            memory.save_context({"input": message}, {"output": answer})

            return {
                "answer": answer,
                "intent": intent,
                "context": context
            }
        except Exception as e:
            print(f"LangChain Agent execution error: {e}")
            return {
                "answer": f"An error occurred while processing your request: {e}",
                "intent": intent
            }

    async def recommend(self, user_profile: dict) -> dict:
        """Recommend strategy based on user profile."""
        # TODO: Implement strategy recommendation
        return {
            "strategy": "value",
            "conditions": []
        }
