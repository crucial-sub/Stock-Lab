"""챗 핸들러 - RAG와 LLM을 오케스트레이션합니다."""
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
    # Claude 도구 호출 에이전트
    from langchain.agents import create_tool_calling_agent, AgentExecutor
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import BaseMessage
    from langchain.memory import ConversationBufferWindowMemory
except ImportError as e:
    print(f"경고: LangChain 컴포넌트가 설치되지 않았습니다. 실행: pip install langchain langchain-aws. 오류: {e}")
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

        # Bedrock 제공자용 LangChain 에이전트 초기화
        if self.provider == "bedrock":
            if not get_tools:
                print("경고: get_tools를 사용할 수 없습니다. 에이전트가 초기화되지 않습니다.")
                return

            try:
                # 1. LLM 클라이언트 초기화
                print("Step 1: LLM 클라이언트 초기화 중...")
                aws_region = os.getenv("AWS_REGION", self.config["llm"].get("region", "us-east-1"))

                if not ChatBedrock:
                    print("경고: ChatBedrock을 사용할 수 없습니다. langchain-aws를 설치하세요.")
                    return

                # AWS Bedrock으로 Claude LLM 초기화
                self.llm_client = ChatBedrock(
                    region_name=aws_region,
                    model_id=os.getenv("BEDROCK_MODEL_ID", self.config["llm"]["model"]),
                    model_kwargs={
                        "temperature": self.config["llm"]["temperature"],
                        "max_tokens": self.config["llm"]["max_tokens"],
                    },
                    streaming=False,
                )
                print(f"Step 1 OK: AWS Bedrock 사용 - 리전: {aws_region}, 모델: {self.llm_client.model_id}")

                # 2. 도구 초기화
                print("Step 2: 도구 초기화 중...")
                tools = get_tools(
                    news_retriever=self.news_retriever,
                    factor_sync=self.factor_sync
                )
                print(f"Step 2 OK: 도구 초기화 완료: {[tool.name for tool in tools]}")

                # 3. 시스템 프롬프트 로드
                print("Step 3: 시스템 프롬프트 로드 중...")
                prompt_path = Path(__file__).parent.parent.parent / "chatbot" / "prompts" / "system.txt"
                system_prompt = prompt_path.read_text(encoding='utf-8') if prompt_path.exists() else "당신은 정량 투자 자문가입니다."
                print(f"Step 3 OK: 시스템 프롬프트 로드 완료 ({len(system_prompt)} 자)")

                # 4. Claude 도구 호출 프롬프트 생성
                print("Step 4: Claude 프롬프트 템플릿 생성 중...")
                # Claude는 도구 호출을 기본 지원
                tool_calling_prompt = ChatPromptTemplate.from_messages([
                    (
                        "system",
                        system_prompt
                        + "\n\n필요할 때 다음 도구를 사용할 수 있습니다."
                        + "\n\n{agent_scratchpad}"
                    ),
                    MessagesPlaceholder("chat_history"),
                    ("user", "참고자료:\n{context}\n\n질문: {input}"),
                ])
                print("Step 4 OK: Claude 프롬프트 템플릿 생성 완료")

                # 5. Claude 에이전트 생성
                print("Step 5: Claude 에이전트와 Executor 생성 중...")
                # Claude는 도구 호출(Tool Calling)을 기본 지원
                agent = create_tool_calling_agent(self.llm_client, tools, tool_calling_prompt)
                self.agent_type = "tool_calling"
                print(f"  Claude 에이전트 생성 완료, AgentExecutor 생성 중...")
                self.agent_executor = AgentExecutor(
                    agent=agent,
                    tools=tools,
                    verbose=True,
                    return_intermediate_steps=True,
                    handle_parsing_errors=True
                )
                print("Step 5 OK: AgentExecutor 생성 완료")

                print("✅ LangChain AgentExecutor 생성 성공")
            except Exception as e:
                print(f"❌ LangChain 에이전트 초기화 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"경고: 에이전트 초기화 건너뜀. 제공자={self.provider}, get_tools={get_tools is not None}")

    async def handle(self, message: str, session_id: Optional[str] = None) -> dict:
        """사용자 메시지를 처리합니다.

        Args:
            message: 사용자 입력
            session_id: 선택사항 세션 ID

        Returns:
            응답 딕셔너리
        """
        # 0. 정책 검사 (투자 조언 금지 정책)
        policy_violation = self._check_investment_advisory_policy(message)
        if policy_violation:
            return {
                "response": policy_violation,
                "intent": "policy_violation",
                "sources": []
            }

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

    def _check_investment_advisory_policy(self, message: str) -> Optional[str]:
        """투자 조언 정책 위반 확인.

        Returns:
            정책 위반 메시지 (위반 시), None (정책 준수 시)
        """
        # 한글은 대소문자가 없으므로 그대로 사용
        message_check = message.strip()

        # 금지된 패턴들 (투자 조언 금지 정책에서 정의)
        forbidden_patterns = {
            # 1. 종목 추천 패턴
            "종목_추천": [
                r"(.*?)(삼성|SK|현대|LG|카카오|네이버|넥슨|엔씨소프트|셀트리온|"
                r"NVIDIA|애플|테슬라|마이크로소프트|구글|알파벳)\s*(추천|사세요|매수|매도|사달라|팔아야)",
                r"(이 종목|이 주식).*?(상승|하락|사세요|팔아야|매수)",
                r"(꼭|반드시|꼭꼭|적극)\s*(추천|추천함|포함)",
            ],
            # 2. 매매 시점 조언 패턴
            "매매_시점": [
                r"(지금|현재|요즘|해야|해야 할)\s*(매수|매도|사세요|팔아야|타이밍|사나|파나)",
                r"(매수|매도|사야|파야)\s*(하나|할까|할지|해야|합니다)",
                r"(매수가|적정가|목표가|손절|익절)\s*(설정|하세요|해야)",
                r"(\d+원).*?(적정|맞는|타이밍)",
                r"(언제|어디서|어떻게)\s+(매수|매도|사야|파야)",
            ],
            # 3. 수익률 보장 패턴
            "수익률_보장": [
                r"(보장|확실|확정|100%|무조건)\s*(수익|이익|수익률)",
                r"(수익|이익).*?(손실|위험).*?(없|없음)",
                r"(항상|반드시)\s*(수익)",
            ],
            # 4. 개인화 조언 패턴
            "개인화_조언": [
                r"(당신|너|니|저는|우리는|우리)\s*(경우|상황|환경).*?(전략|투자|추천|사는|사세요)",
                r"(월|분기|년)\s*(\d+)\s*(만원|천원|원).*?(투자|사세요|해야)",
                r"(특별히|맞춤|특화|개인|따라).*?(투자|전략|추천)",
            ],
        }

        # 패턴 매칭
        violations_found = []
        for violation_type, patterns in forbidden_patterns.items():
            for pattern in patterns:
                if __import__('re').search(pattern, message_check):
                    violations_found.append(violation_type)
                    break

        if violations_found:
            return self._get_policy_violation_response(violations_found[0])

        return None

    def _get_policy_violation_response(self, violation_type: str) -> str:
        """정책 위반에 따른 응답 메시지 반환."""
        base_response = (
            "죄송합니다. 저는 특정 종목에 대한 투자 조언을 제공할 수 없습니다.\n\n"
            "대신 도움드릴 수 있는 것:\n"
            "- 종목 분석 방법 설명\n"
            "- 재무제표 읽는 법\n"
            "- 투자 지표 계산 방법\n"
            "-  리스크 관리 원칙\n\n"
            "투자 결정은 반드시 본인의 판단으로 하시기 바랍니다."
        )

        if violation_type == "종목_추천":
            return (
                "죄송합니다. 저는 특정 종목을 추천해드릴 수 없습니다.\n\n"
                "대신 다음을 도움드릴 수 있습니다:\n"
                "- 팩터 분석 방법\n"
                "- 종목 평가 방법\n"
                "- 투자 전략 설명\n\n"
                "투자 결정은 충분한 리서치 후 본인의 판단으로 하시기 바랍니다."
            )
        elif violation_type == "매매_시점":
            return (
                "죄송합니다. 매매 타이밍에 대한 조언은 드릴 수 없습니다.\n\n"
                "대신 다음을 도움드릴 수 있습니다:\n"
                "- 기술적 분석 방법\n"
                "- 차트 읽는 법\n"
                "- 리스크 관리 전략\n\n"
                "매매 타이밍은 본인의 투자 계획과 판단으로 결정하시기 바랍니다."
            )
        elif violation_type == "수익률_보장":
            return (
                "죄송합니다. 수익을 보장해드릴 수는 없습니다.\n\n"
                "투자에는 항상 손실의 위험이 존재합니다. 대신 다음을 도움드릴 수 있습니다:\n"
                "- 리스크 관리 방법\n"
                "- 포트폴리오 분산 전략\n"
                "- 역사적 수익률 데이터 분석\n\n"
                "안정적인 장기 투자 계획을 세우시기 바랍니다."
            )
        elif violation_type == "개인화_조언":
            return (
                "죄송합니다. 개인의 상황에 맞춘 투자 조언은 드릴 수 없습니다.\n\n"
                "대신 다음을 도움드릴 수 있습니다:\n"
                "- 일반적인 투자 전략 설명\n"
                "- 자산배분 원칙\n"
                "- 투자 목표 설정 방법\n\n"
                "본인의 상황과 목표에 맞는 투자 계획을 세우시기 바랍니다."
            )

        return base_response
