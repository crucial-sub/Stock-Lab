"""챗 핸들러 - RAG와 LLM을 오케스트레이션합니다."""
import os
import re
import asyncio
import types
import sys
import warnings
import uuid
from typing import Optional, List
from pathlib import Path
from dotenv import load_dotenv
import yaml

# LangChain deprecation 경고 무시
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', message='.*migration guide.*')

_pydantic_v1_module = None
try:
    import pydantic as _pydantic
    import pydantic.class_validators as _pydantic_class_validators

    _pydantic_v1_module = types.ModuleType("langchain_core.pydantic_v1")
    for attr in dir(_pydantic):
        if attr.startswith("__"):
            continue
        setattr(_pydantic_v1_module, attr, getattr(_pydantic, attr))
    for attr in dir(_pydantic_class_validators):
        if attr.startswith("__"):
            continue
        if hasattr(_pydantic_v1_module, attr):
            continue
        setattr(_pydantic_v1_module, attr, getattr(_pydantic_class_validators, attr))
    _pydantic_v1_module.__all__ = [name for name in dir(_pydantic_v1_module) if not name.startswith("__")]
    sys.modules.setdefault("langchain_core.pydantic_v1", _pydantic_v1_module)
except ImportError:
    pass

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "bedrock").lower()

# LangChain 의존성은 버전에 따라 모듈 경로가 달라지므로 개별적으로 로드한다.
ChatBedrock = None
create_tool_calling_agent = None
AgentExecutor = None
ChatPromptTemplate = None
MessagesPlaceholder = None
BaseMessage = None
ConversationBufferWindowMemory = None
create_react_agent = None
initialize_agent = None
AgentType = None

try:
    from langchain_aws import ChatBedrock  # type: ignore
except ImportError as e:
    print(f"경고: LangChain AWS(ChatBedrock) 컴포넌트가 없습니다. pip install langchain-aws 실행 필요. 오류: {e}")

# LangChain 0.2.x 호환 간단한 에이전트 래퍼
class SimpleLLMAgent:
    """LangChain 0.2.x 호환 간단한 LLM 에이전트"""
    def __init__(self, llm, tools, prompt):
        self.llm = llm
        self.tools = tools
        self.prompt = prompt
        self.tool_map = {tool.name: tool for tool in tools}

    def invoke(self, inputs):
        """에이전트 호출"""
        try:
            # 프롬프트에 입력 바인딩
            if hasattr(self.prompt, 'format_prompt'):
                formatted = self.prompt.format_prompt(**inputs)
                response = self.llm.invoke(formatted)
            elif hasattr(self.prompt, 'format'):
                # ChatPromptTemplate는 format 대신 다른 방식 사용
                messages = self.prompt.format_messages(**inputs)
                response = self.llm.invoke(messages)
            else:
                response = self.llm.invoke(inputs)
            return response
        except Exception as e:
            return f"에러: {str(e)}"

def _create_simple_agent(llm, tools, prompt):
    """SimpleLLMAgent 생성 함수"""
    return SimpleLLMAgent(llm, tools, prompt)

create_tool_calling_agent = _create_simple_agent
AgentExecutor = None
try:
    from langchain.agents import create_react_agent, AgentType, initialize_agent  # type: ignore
except ImportError:
    # Fallbacks may not be available depending on LangChain version
    pass

try:
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder  # type: ignore
except ImportError as e:
    print(f"경고: LangChain Prompt 컴포넌트를 불러오지 못했습니다. 오류: {e}")
    ChatPromptTemplate = None
    MessagesPlaceholder = None

try:
    from langchain_core.messages import BaseMessage  # type: ignore
except ImportError as e:
    print(f"경고: LangChain Message 컴포넌트를 불러오지 못했습니다. 오류: {e}")
    BaseMessage = None

try:
    from langchain.memory import ConversationBufferWindowMemory  # type: ignore
except ImportError:
    try:
        # LangChain 0.3+는 메모리 API가 classic 패키지로 이동했다.
        from langchain_classic.memory import ConversationBufferWindowMemory  # type: ignore
        print('정보: langchain.memory 대신 langchain_classic.memory에서 ConversationBufferWindowMemory를 로드했습니다.')
    except ImportError as e:
        print(f"경고: ConversationBufferWindowMemory를 불러오지 못했습니다. pip install langchain-classic 실행 필요. 오류: {e}")
        ConversationBufferWindowMemory = None

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
    from retrievers.factory import RetrieverFactory
    from retrievers.base_retriever import BaseRetriever
except ImportError:
    print("Warning: Retriever modules not imported")
    RetrieverFactory = None
    BaseRetriever = None

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

try:
    from ui_language import (
        QUESTIONS_DATA,
        STRATEGY_TAGS_MAPPING,
        UILanguageType,
        UILanguageQuestionnaire,
        UILanguageRecommendation,
        UILanguageBacktestConfiguration,
        Question,
        OptionCard,
        StrategyRecommendation,
        ConditionPreview,
        UserProfileSummary,
        ConfigurationField
    )
except ImportError:
    print("Warning: UI Language modules not imported")
    QUESTIONS_DATA = None
    STRATEGY_TAGS_MAPPING = None


class SimpleAgentExecutor:
    """LangChain 0.2.x 호환 간단한 에이전트 실행기"""
    def __init__(self, agent, tools, **kwargs):
        self.agent = agent
        self.tools = {tool.name: tool for tool in tools}
        self.verbose = kwargs.get('verbose', False)
        self.return_intermediate_steps = kwargs.get('return_intermediate_steps', False)
        self.handle_parsing_errors = kwargs.get('handle_parsing_errors', True)

    def invoke(self, inputs):
        """에이전트 실행"""
        try:
            # Agent에 input 전달
            result = self.agent.invoke(inputs)

            # LangChain 0.2.x: AIMessage 객체 처리
            if hasattr(result, 'content'):
                # AIMessage 객체
                return {"output": result.content}
            elif isinstance(result, dict):
                # 딕셔너리 반환
                return {"output": result.get("output") or result}
            elif isinstance(result, str):
                # 문자열 반환
                return {"output": result}
            else:
                # 기타 객체
                return {"output": str(result)}
        except Exception as e:
            if self.verbose:
                print(f"Agent execution error: {e}")
            return {"output": str(e)}


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

        # UI Language 및 세션 관리
        self.session_data = {}  # {session_id: {question_answers, current_question, user_tags}}
        self.session_state = {}  # {session_id: {"in_questionnaire": bool, "answers": {...}}}

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
        if RetrieverFactory:
            try:
                self.rag_retriever = RetrieverFactory.create_retriever(
                    retriever_type=os.getenv("RETRIEVER_TYPE"),
                    config=self.config.get("rag", {})
                )
                print("RAG Retriever initialized - Knowledge base loaded")
                
                # 헬스 체크
            except Exception as e:
                print(f"Warning: RAG Retriever initialization failed: {e}")
                self.rag_retriever = None

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
                agent = None
                self.agent_type = None

                # Claude는 도구 호출(Tool Calling)을 기본 지원
                if create_tool_calling_agent:
                    try:
                        agent = create_tool_calling_agent(self.llm_client, tools, tool_calling_prompt)
                        self.agent_type = "simple_llm"
                        print("  SimpleLLMAgent 기반 에이전트를 생성했습니다.")
                    except Exception as e:
                        print(f"  에이전트 생성 실패: {e}")
                        agent = None

                # 에이전트가 성공적으로 생성되었으면 SimpleAgentExecutor로 래핑
                if agent:
                    try:
                        self.agent_executor = SimpleAgentExecutor(
                            agent=agent,
                            tools=tools,
                            verbose=True,
                            return_intermediate_steps=True,
                            handle_parsing_errors=True
                        )
                        print("Step 5 OK: SimpleAgentExecutor 생성 완료")
                    except Exception as e:
                        print(f"  SimpleAgentExecutor 생성 실패: {e}")
                        self.agent_executor = None

                if not self.agent_executor:
                    print("경고: 사용 가능한 LangChain 에이전트를 생성하지 못했습니다.")
                    return

                print("[OK] LangChain 에이전트 생성 성공")
            except Exception as e:
                print(f"[ERROR] LangChain 에이전트 초기화 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"경고: 에이전트 초기화 건너뜀. 제공자={self.provider}, get_tools={get_tools is not None}")

    async def handle(self, message: str, session_id: Optional[str] = None, answer: Optional[dict] = None) -> dict:
        """사용자 메시지를 처리합니다.

        Args:
            message: 사용자 입력
            session_id: 선택사항 세션 ID
            answer: 선택사항 질문 응답 데이터 {question_id, option_id}

        Returns:
            응답 딕셔너리 (ui_language 포함)
        """
        # 세션 ID가 없으면 생성
        if session_id is None:
            session_id = str(uuid.uuid4())

        # 0. 정책 검사 (투자 조언 금지 정책)
        policy_violation = self._check_investment_advisory_policy(message)
        if policy_violation:
            print(f"DEBUG: Policy violation detected")
            return {
                "answer": policy_violation,
                "intent": "policy_violation",
                "session_id": session_id,
                "sources": []
            }

        # 전략 추천 플로우 감지
        print(f"DEBUG: Checking _is_strategy_recommendation_request...")
        # 이미 설문조사 진행 중이거나 새로운 전략 추천 요청인 경우
        in_questionnaire = session_id in self.session_state
        if in_questionnaire or self._is_strategy_recommendation_request(message):
            print(f"DEBUG: Strategy recommendation flow triggered! (in_questionnaire={in_questionnaire})")
            return await self._handle_strategy_recommendation_flow(message, session_id, answer)

        # 1. Classify intent
        intent = await self._classify_intent(message)

        # 2. Retrieve relevant knowledge (RAG)
        context = await self._retrieve_context(message, intent)

        # 3. Generate response with LangChain Agent
        response = await self._generate_response_langchain(
            message, intent, context, session_id
        )

        response["session_id"] = session_id
        return response

    async def _classify_intent(self, message: str) -> str:
        """사용자 의도 분류. 테마 분석, 전략 설명 등을 감지합니다."""
        message_lower = message.strip().lower()

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
                rag_context = await self.rag_retriever.get_context(
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
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
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
            if isinstance(answer, list):
                formatted_parts = []
                for element in answer:
                    if isinstance(element, str):
                        formatted_parts.append(element)
                    elif isinstance(element, dict):
                        text = element.get("text") or element.get("message") or element.get("output")
                        if isinstance(text, str):
                            formatted_parts.append(text)
                        else:
                            formatted_parts.append(str(text))
                    else:
                        formatted_parts.append(str(element))
                answer = "\n".join(formatted_parts)

            
            answer = self._clean_tool_calls_from_response(answer)

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

    def _clean_tool_calls_from_response(self, response: str) -> str:
        """LangChain의 내부 도구 호출 형식(<function_calls>, <invoke> 등)을 제거합니다."""
        # <function_calls> 블록 제거
        response = re.sub(
            r'<function_calls>.*?</function_calls>',
            '',
            response,
            flags=re.DOTALL
        )

        # <invoke> 블록 제거
        response = re.sub(
            r'<invoke>.*?</invoke>',
            '',
            response,
            flags=re.DOTALL
        )

        # 연속된 빈 줄 제거
        response = re.sub(r'\n\n+', '\n\n', response)

        # CP949에서 인코딩 불가능한 문자 제거 (이모지, 특수 기호 등)
        try:
            response.encode('cp949')
        except UnicodeEncodeError:
            # 한글과 ASCII만 남기고 나머지는 제거
            response = ''.join(
                c if ord(c) < 128 or '\uac00' <= c <= '\ud7a3' or c in '\n\t '
                else '' for c in response
            )

        return response.strip()

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

    # =============== UI Language 메서드 ===============

    async def _handle_strategy_recommendation_flow(self, message: str, session_id: str, answer: Optional[dict]) -> dict:
        """전략 추천 플로우 핸들러"""
        # 세션 초기화
        if session_id not in self.session_state:
            self.session_state[session_id] = {
                "in_questionnaire": True,
                "current_question": 1,
                "answers": {}
            }

        state = self.session_state[session_id]

        # 질문 진행 중
        if state["in_questionnaire"]:
            # 유저 응답 저장
            if answer:
                state["answers"][answer["question_id"]] = answer["option_id"]
                state["current_question"] += 1

            # 5개 질문 모두 완료
            if state["current_question"] > 5:
                # 전략 추천 생성
                user_tags = self._collect_user_tags(state["answers"])
                ui_language = self._generate_strategy_recommendations(user_tags)

                # 투자 프로필 저장
                state["user_tags"] = user_tags
                state["in_questionnaire"] = False

                return {
                    "answer": "분석 완료! 당신의 투자 성향에 맞는 3가지 전략을 추천합니다.",
                    "intent": "strategy_recommendation_complete",
                    "session_id": session_id,
                    "ui_language": ui_language
                }
            else:
                # 다음 질문 렌더링
                ui_language = self._generate_questionnaire_response(session_id, state["current_question"])

                question_message = f"질문 {state['current_question']}/5: {ui_language['question']['text']}"

                return {
                    "answer": question_message,
                    "intent": "questionnaire_progress",
                    "session_id": session_id,
                    "ui_language": ui_language
                }
        else:
            # 전략 선택 처리
            if answer and "strategy_id" in answer:
                strategy_id = answer["strategy_id"]
                state["selected_strategy"] = strategy_id

                # 백테스트 설정 UI 생성
                ui_language = self._generate_backtest_configuration_response(strategy_id)

                if ui_language:
                    return {
                        "answer": f"선택하신 전략으로 백테스트 설정을 진행하겠습니다.",
                        "intent": "backtest_configuration",
                        "session_id": session_id,
                        "ui_language": ui_language
                    }

        return {
            "answer": "요청을 처리할 수 없습니다.",
            "intent": "error",
            "session_id": session_id
        }

    def _collect_user_tags(self, answers: dict) -> List[str]:
        """답변으로부터 유저 태그 수집"""
        user_tags = []

        if not QUESTIONS_DATA:
            return user_tags

        for question_id, option_id in answers.items():
            if question_id in QUESTIONS_DATA:
                question_data = QUESTIONS_DATA[question_id]
                for option in question_data["options"]:
                    if option["id"] == option_id:
                        user_tags.extend(option["tags"])
                        break

        return user_tags

    def _is_strategy_recommendation_request(self, message: str) -> bool:
        """전략 추천 요청인지 판단 - 명시적인 추천 요청만 감지"""
        if not QUESTIONS_DATA:
            # UI Language 데이터 미로드 시 전략 추천 비활성화
            print(f"DEBUG: QUESTIONS_DATA not loaded")
            return False

        msg_lower = message.lower().strip()

        # 명시적인 추천 요청 패턴만 감지
        explicit_patterns = [
            "전략 추천",
            "추천해",
            "추천 받",
            "추천 해",
            "strategy recommend",
            "recommend strategy"
        ]

        result = any(pattern in msg_lower for pattern in explicit_patterns)
        print(f"DEBUG: _is_strategy_recommendation_request('{message}') = {result}")
        return result

    def _generate_questionnaire_response(self, session_id: str, question_num: int) -> dict:
        """질문 UI Language 응답 생성"""
        if not QUESTIONS_DATA:
            return {}

        # 질문 순서대로 가져오기
        questions_list = sorted(QUESTIONS_DATA.values(), key=lambda x: x["order"])
        if question_num > len(questions_list):
            return {}

        question_data = questions_list[question_num - 1]

        # OptionCard 객체 생성
        options = [
            OptionCard(
                id=opt["id"],
                label=opt["label"],
                description=opt["description"],
                icon=opt["icon"],
                tags=opt["tags"]
            )
            for opt in question_data["options"]
        ]

        # Question 객체 생성
        question = Question(
            question_id=question_data["question_id"],
            text=question_data["text"],
            options=options
        )

        # UILanguageQuestionnaire 생성
        ui_language_type = UILanguageType.QUESTIONNAIRE_START if question_num == 1 else UILanguageType.QUESTIONNAIRE_PROGRESS
        progress_percentage = (question_num / 5) * 100

        ui_lang = UILanguageQuestionnaire(
            type=ui_language_type,
            total_questions=5,
            current_question=question_num,
            progress_percentage=int(progress_percentage) if question_num > 1 else None,
            question=question
        )

        return ui_lang.to_dict()

    def _calculate_strategy_match_score(self, user_tags: List[str], strategy_tags: List[str]) -> tuple:
        """전략 매칭 점수 계산 (점수, 퍼센티지)"""
        if not strategy_tags:
            return 0.0, 0

        matching_tags = set(user_tags) & set(strategy_tags)
        match_score = len(matching_tags) / len(strategy_tags)
        match_percentage = int(match_score * 100)

        return match_score, match_percentage

    def _generate_matching_reasons(self, user_tags: List[str], strategy_tags: List[str]) -> List[str]:
        """매칭 이유 생성"""
        reasons = []

        if "long_term" in user_tags and "long_term" in strategy_tags:
            reasons.append("장기 투자 성향 일치")
        if "short_term" in user_tags and "short_term" in strategy_tags:
            reasons.append("단기 매매 성향 일치")

        for style in ["style_value", "style_growth", "style_momentum", "style_dividend"]:
            if style in user_tags and style in strategy_tags:
                style_name = {
                    "style_value": "저평가주 선호",
                    "style_growth": "성장주 선호",
                    "style_momentum": "모멘텀 선호",
                    "style_dividend": "배당주 선호"
                }
                reasons.append(style_name.get(style, ""))

        for risk in ["risk_high", "risk_mid", "risk_low"]:
            if risk in user_tags and risk in strategy_tags:
                risk_name = {
                    "risk_high": "높은 위험 감수 의향",
                    "risk_mid": "중간 정도의 위험 감수",
                    "risk_low": "저위험 선호"
                }
                reasons.append(risk_name.get(risk, ""))

        return [r for r in reasons if r]

    def _generate_strategy_recommendations(self, user_tags: List[str]) -> dict:
        """전략 추천 응답 생성"""
        if not STRATEGY_TAGS_MAPPING:
            return {}

        # 모든 전략의 점수 계산
        strategy_scores = []

        for strategy_id, strategy_data in STRATEGY_TAGS_MAPPING.items():
            match_score, match_percentage = self._calculate_strategy_match_score(
                user_tags, strategy_data["tags"]
            )
            matching_reasons = self._generate_matching_reasons(user_tags, strategy_data["tags"])

            # ConditionPreview 생성
            conditions_preview = [
                ConditionPreview(
                    condition=cond["condition"],
                    condition_info=cond["condition_info"]
                )
                for cond in strategy_data.get("conditions", [])
            ]

            recommendation = StrategyRecommendation(
                rank=0,  # 임시, 정렬 후 설정
                strategy_id=strategy_id,
                strategy_name=strategy_data["strategy_name"],
                summary=strategy_data["summary"],
                match_score=round(match_score, 2),
                match_percentage=match_percentage,
                match_reasons=matching_reasons,
                tags=strategy_data["tags"],
                conditions_preview=conditions_preview,
                icon="",  # 전략에 맞게 설정
                badge=None
            )

            strategy_scores.append((match_score, recommendation))

        # 점수로 정렬 및 상위 3개 선택
        strategy_scores.sort(key=lambda x: x[0], reverse=True)
        top_3_strategies = strategy_scores[:3]

        # rank 설정 및 badge 추가
        recommendations = []
        for rank, (_, recommendation) in enumerate(top_3_strategies, 1):
            recommendation.rank = rank
            if rank == 1:
                recommendation.badge = "최고 추천"
            recommendations.append(recommendation)

        # UserProfileSummary 생성 (태그로부터)
        profile = UserProfileSummary(
            investment_period=self._get_tag_display_name("investment_period", user_tags),
            investment_style=self._get_tag_display_name("investment_style", user_tags),
            risk_tolerance=self._get_tag_display_name("risk_tolerance", user_tags),
            dividend_preference=self._get_tag_display_name("dividend_preference", user_tags),
            sector_preference=self._get_tag_display_name("sector_preference", user_tags)
        )

        ui_lang = UILanguageRecommendation(
            type=UILanguageType.STRATEGY_RECOMMENDATION,
            recommendations=recommendations,
            user_profile_summary=profile
        )

        return ui_lang.to_dict()

    def _get_tag_display_name(self, category: str, user_tags: List[str]) -> str:
        """태그로부터 표시 이름 추출"""
        if not QUESTIONS_DATA or category not in QUESTIONS_DATA:
            return ""

        question_data = QUESTIONS_DATA[category]
        for option in question_data["options"]:
            if option["id"] in user_tags:
                return option["label"]
        return ""

    def _generate_backtest_configuration_response(self, strategy_id: str) -> dict:
        """백테스트 설정 UI Language 응답 생성"""
        if not STRATEGY_TAGS_MAPPING or strategy_id not in STRATEGY_TAGS_MAPPING:
            return {}

        strategy_data = STRATEGY_TAGS_MAPPING[strategy_id]

        configuration_fields = [
            ConfigurationField(
                field_id="initial_capital",
                label="초기 투자 금액",
                type="number",
                unit="원",
                default_value=100000000,
                min_value=10000000,
                max_value=1000000000,
                step=10000000,
                required=True,
                description="백테스트에 사용할 초기 투자 금액을 설정하세요."
            ),
            ConfigurationField(
                field_id="start_date",
                label="백테스트 시작일",
                type="date",
                default_value="2024-01-01",
                min_value="2020-01-01",
                max_value="2024-12-31",
                required=True
            ),
            ConfigurationField(
                field_id="end_date",
                label="백테스트 종료일",
                type="date",
                default_value="2024-12-31",
                min_value="2020-01-01",
                max_value="2024-12-31",
                required=True
            ),
            ConfigurationField(
                field_id="rebalance_frequency",
                label="리밸런싱 주기",
                type="select",
                default_value="MONTHLY",
                options=[
                    {"value": "DAILY", "label": "매일"},
                    {"value": "WEEKLY", "label": "매주"},
                    {"value": "MONTHLY", "label": "매월"}
                ],
                required=True
            ),
            ConfigurationField(
                field_id="max_positions",
                label="최대 보유 종목 수",
                type="number",
                unit="개",
                default_value=20,
                min_value=5,
                max_value=50,
                step=5,
                required=True
            )
        ]

        ui_lang = UILanguageBacktestConfiguration(
            type=UILanguageType.BACKTEST_CONFIGURATION,
            strategy={"strategy_id": strategy_id, "strategy_name": strategy_data["strategy_name"]},
            configuration_fields=configuration_fields
        )

        return ui_lang.to_dict()
