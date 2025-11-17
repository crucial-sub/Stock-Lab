import os
import re
import asyncio
import types
import sys
import uuid
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import yaml

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

try:
    from langchain_aws import ChatBedrock  # type: ignore
except ImportError as e:
    print(f"경고: LangChain AWS(ChatBedrock) 컴포넌트가 없습니다. pip install langchain-aws 실행 필요. 오류: {e}")

try:
    from langchain.agents.tool_calling_agent.base import create_tool_calling_agent  # type: ignore
    from langchain.agents.agent import AgentExecutor  # type: ignore
except ImportError:
    try:
        from langchain.agents.tool_calling_agent import create_tool_calling_agent  # type: ignore
        from langchain.agents.agent import AgentExecutor  # type: ignore
    except ImportError:
        try:
            from langchain.agents import create_tool_calling_agent  # type: ignore
            from langchain.agents import AgentExecutor  # type: ignore
        except ImportError:
            try:
                # LangChain 0.3+ 계열에선 classic 네임스페이스로 이동
                from langchain_classic.agents import create_tool_calling_agent, AgentExecutor  # type: ignore
            except ImportError:
                try:
                    from langchain_core.agents import create_tool_calling_agent  # type: ignore
                    from langchain.agents import AgentExecutor  # type: ignore
                except ImportError as e:
                    print(
                        "경고: LangChain Agent 컴포넌트를 불러오지 못했습니다. "
                        "pip install langchain>=0.1,<0.3 또는 langchain-classic 설치를 확인하세요. "
                        f"오류: {e}"
                    )
                    create_tool_calling_agent = None
                    AgentExecutor = None

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
        # 설문/추천 상태
        self.session_state: Dict[str, Dict[str, Any]] = {}

        self._load_config()
        self._init_components()

        # 설문 질문 세트 (프론트 UI 사양 반영)
        self.questions = [
            {
                "question_id": "investment_period",
                "text": "보통 얼마 동안 보유할 생각으로 투자하시나요?",
                "order": 1,
                "options": [
                    {
                        "id": "short_term",
                        "label": "단기 투자 (며칠 ~ 몇 주)",
                        "description": "짧게 사고 팔면서 단기 수익을 노려요.",
                        "icon": "⚡",
                        "tags": ["short_term", "style_momentum"],
                    },
                    {
                        "id": "mid_term",
                        "label": "중기 투자 (몇 개월)",
                        "description": "몇 달 정도 흐름을 보면서 가져가는 편이에요.",
                        "icon": "📊",
                        "tags": ["mid_term"],
                    },
                    {
                        "id": "long_term",
                        "label": "장기 투자 (1년 이상)",
                        "description": "좋은 기업을 골라 오래 들고 가고 싶어요.",
                        "icon": "🏆",
                        "tags": ["long_term", "style_value"],
                    },
                ],
            },
            {
                "question_id": "investment_style",
                "text": "아래 중에서 가장 본인 스타일에 가까운 걸 골라주세요.",
                "order": 2,
                "options": [
                    {
                        "id": "value",
                        "label": "가치 / 저평가 위주",
                        "description": "싸게 사서 안전마진을 확보하는 것이 좋아요.",
                        "icon": "💎",
                        "tags": ["style_value"],
                    },
                    {
                        "id": "growth",
                        "label": "성장 / 실적 위주",
                        "description": "매출·이익이 빠르게 커지는 기업이 좋아요.",
                        "icon": "📈",
                        "tags": ["style_growth"],
                    },
                    {
                        "id": "momentum",
                        "label": "모멘텀 / 추세 위주",
                        "description": "최근에 많이 오르고 있는 강한 종목이 좋아요.",
                        "icon": "🚀",
                        "tags": ["style_momentum"],
                    },
                    {
                        "id": "dividend",
                        "label": "배당 수익 위주",
                        "description": "배당을 꾸준히 받으면서 안정적으로 가고 싶어요.",
                        "icon": "💰",
                        "tags": ["style_dividend"],
                    },
                ],
            },
            {
                "question_id": "risk_tolerance",
                "text": "투자 중에 일시적으로 -20% 같은 큰 손실이 나도 버틸 수 있나요?",
                "order": 3,
                "options": [
                    {
                        "id": "risk_high",
                        "label": "크게 흔들려도 괜찮아요",
                        "description": "-30% 변동도 상관없어요.",
                        "icon": "🎢",
                        "tags": ["risk_high"],
                    },
                    {
                        "id": "risk_mid",
                        "label": "어느 정도는 괜찮아요",
                        "description": "-10% ~ -20% 정도는 감수할 수 있어요.",
                        "icon": "⚖️",
                        "tags": ["risk_mid"],
                    },
                    {
                        "id": "risk_low",
                        "label": "손실은 최소화하고 싶어요",
                        "description": "-10%만 넘어가도 스트레스를 많이 받아요.",
                        "icon": "🛡️",
                        "tags": ["risk_low"],
                    },
                ],
            },
            {
                "question_id": "dividend_preference",
                "text": "아래 둘 중, 더 끌리는 쪽은 어디인가요?",
                "order": 4,
                "options": [
                    {
                        "id": "prefer_dividend",
                        "label": "배당이 중요하다",
                        "description": "꾸준한 현금 배당이 중요해요.",
                        "icon": "💵",
                        "tags": ["prefer_dividend"],
                    },
                    {
                        "id": "prefer_capital_gain",
                        "label": "배당보다 시세차익이 중요하다",
                        "description": "주가 상승이 더 중요해요.",
                        "icon": "📈",
                        "tags": ["prefer_capital_gain"],
                    },
                    {
                        "id": "prefer_both",
                        "label": "둘 다 적당히 있으면 좋다",
                        "description": "배당도 받고 주가도 오르면 베스트죠.",
                        "icon": "🎯",
                        "tags": ["prefer_both"],
                    },
                ],
            },
            {
                "question_id": "sector_preference",
                "text": "어떤 종류의 기업에 더 끌리나요?",
                "order": 5,
                "options": [
                    {
                        "id": "innovation",
                        "label": "혁신 기술/성장 섹터",
                        "description": "AI, 로봇, 바이오, 핀테크 같은 미래 기술 기업이 좋다.",
                        "icon": "🚀",
                        "tags": ["sector_innovation"],
                    },
                    {
                        "id": "bluechip",
                        "label": "전통 산업/우량 대형주",
                        "description": "안정적인 대형 기업이 좋다.",
                        "icon": "🏢",
                        "tags": ["sector_bluechip"],
                    },
                    {
                        "id": "smallmid",
                        "label": "중소형/숨은 진주형 종목",
                        "description": "덜 알려졌지만 개선 여지가 큰 중소형주.",
                        "icon": "💎",
                        "tags": ["sector_smallmid"],
                    },
                    {
                        "id": "any",
                        "label": "특별히 상관없다",
                        "description": "섹터는 상관없고 조건만 좋으면 된다.",
                        "icon": "🎲",
                        "tags": ["sector_any"],
                    },
                ],
            },
        ]

        # 기본 전략 태그 매핑 (간단 매칭용)
        self.strategy_tags_mapping = {
            "cathy_wood": {
                "strategy_id": "cathy_wood",
                "strategy_name": "캐시 우드의 전략",
                "summary": "혁신 기술 고성장주 중심의 장기 성장 전략",
                "tags": ["long_term", "style_growth", "risk_high", "sector_innovation"],
                "conditions": [
                    {"condition": "0 < PEG < 2"},
                    {"condition": "매출 성장률 > 20%"},
                ],
            },
            "peter_lynch": {
                "strategy_id": "peter_lynch",
                "strategy_name": "피터 린치의 전략",
                "summary": "PER·PEG로 저평가 성장주를 찾는 전략",
                "tags": ["long_term", "style_growth", "risk_mid"],
                "conditions": [
                    {"condition": "PER < 30"},
                    {"condition": "0 < PEG < 1.8"},
                ],
            },
            "value_income": {
                "strategy_id": "value_income",
                "strategy_name": "저평가 배당주",
                "summary": "저평가 + 배당 안정성 중심",
                "tags": ["long_term", "style_dividend", "risk_low", "prefer_dividend", "sector_bluechip"],
                "conditions": [
                    {"condition": "PBR < 1.0"},
                    {"condition": "배당수익률 > 3%"},
                ],
            },
        }

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
                # Throttling 대응: 재시도 설정 추가
                import boto3
                from botocore.config import Config

                retry_config = Config(
                    retries={
                        'max_attempts': 3,  # 최대 재시도 횟수 줄임 (기본 4 → 3)
                        'mode': 'adaptive'  # 적응형 재시도 (점진적 백오프)
                    },
                    read_timeout=120,  # 읽기 타임아웃 증가
                    connect_timeout=10
                )

                # Bedrock 클라이언트를 직접 생성 (retry_config 적용)
                bedrock_client = boto3.client(
                    service_name='bedrock-runtime',
                    region_name=aws_region,
                    config=retry_config
                )

                self.llm_client = ChatBedrock(
                    client=bedrock_client,
                    model_id=os.getenv("BEDROCK_MODEL_ID", self.config["llm"]["model"]),
                    model_kwargs={
                        "temperature": self.config["llm"]["temperature"],
                        "max_tokens": self.config["llm"]["max_tokens"],
                    },
                    streaming=False
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
                # Docker: /app/prompts/system.txt, Local: 상대경로
                prompt_path = Path("/app/prompts/system.txt")
                if not prompt_path.exists():
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
                    verbose=False,  # Throttling 방지를 위해 verbose 비활성화
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

    async def handle(self, message: str, session_id: Optional[str] = None, answer: Optional[dict] = None) -> dict:
        """사용자 메시지를 처리합니다.

        Args:
            message: 사용자 입력
            session_id: 선택사항 세션 ID
            answer: 설문 응답 (선택사항)

        Returns:
            응답 딕셔너리
        """
        if session_id is None:
            session_id = str(uuid.uuid4())

        # 설문/전략 추천 플로우 (ui_language)
        if answer or self._is_strategy_request(message):
            return await self._handle_questionnaire_flow(session_id, answer, message)

        # 0-0. 도메인(금융/투자) 외 질문 차단
        domain_violation = self._check_domain_restriction(message)
        if domain_violation:
            return {
                "answer": domain_violation,
                "intent": "policy_violation",
                "session_id": session_id,
                "sources": []
            }

        # 0. 정책 검사 (투자 조언 금지 정책)
        policy_violation = self._check_investment_advisory_policy(message)
        if policy_violation:
            return {
                "answer": policy_violation,
                "intent": "policy_violation",
                "session_id": session_id,
                "sources": []
            }

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

    def _is_strategy_request(self, message: str) -> bool:
        """전략 추천 설문을 시작할지 여부 판단."""
        msg = (message or "").lower()
        triggers = ["전략 추천", "추천받고 싶어요", "추천 해줘", "설문", "투자 성향"]
        return any(t in msg for t in triggers) or msg.strip() == ""

    async def _handle_questionnaire_flow(self, session_id: str, answer: Optional[dict], message: str) -> dict:
        """5문항 설문 → 전략 추천 UI Language 생성."""
        # 세션 초기화
        state = self.session_state.setdefault(session_id, {
            "current": 1,
            "answers": {},
            "completed": False,
        })

        # 응답 처리
        if answer and "question_id" in answer and "option_id" in answer:
            state["answers"][answer["question_id"]] = answer["option_id"]
            state["current"] += 1

        total = len(self.questions)

        # 모든 질문 완료 → 추천 생성
        if state["current"] > total:
            recs = self._build_recommendations(state["answers"])
            state["completed"] = True
            return {
                "answer": "고객님의 투자 성향을 분석한 결과, 다음 전략을 추천드려요!",
                "intent": "strategy_recommendation_complete",
                "session_id": session_id,
                "ui_language": {
                    "type": "strategy_recommendation",
                    "recommendations": recs,
                    "user_profile_summary": self._build_profile_summary(state["answers"]),
                },
            }

        # 다음 질문 렌더링
        question = sorted(self.questions, key=lambda q: q["order"])[state["current"] - 1]
        progress = int(((state["current"] - 1) / total) * 100)

        return {
            "answer": f"질문 {state['current']}/{total}: {question['text']}",
            "intent": "questionnaire_progress" if state["current"] > 1 else "questionnaire_start",
            "session_id": session_id,
            "ui_language": {
                "type": "questionnaire_progress" if state["current"] > 1 else "questionnaire_start",
                "total_questions": total,
                "current_question": state["current"],
                "progress_percentage": progress,
                "question": question,
            },
        }

    def _collect_user_tags(self, answers: Dict[str, str]) -> List[str]:
        """선택된 옵션에서 태그 수집."""
        tags: List[str] = []
        for q in self.questions:
            qid = q["question_id"]
            if qid not in answers:
                continue
            opt = next((o for o in q["options"] if o["id"] == answers[qid]), None)
            if opt:
                tags.extend(opt.get("tags", []))
        return tags

    def _build_recommendations(self, answers: Dict[str, str]) -> List[dict]:
        """태그 겹침 기반 추천 상위 3개."""
        user_tags = set(self._collect_user_tags(answers))
        scored = []
        for sid, meta in self.strategy_tags_mapping.items():
            stags = set(meta.get("tags", []))
            score = len(user_tags & stags) / (len(stags) or 1)
            scored.append((score, meta))
        scored.sort(key=lambda x: x[0], reverse=True)
        top = scored[:3]
        recs = []
        for rank, (score, meta) in enumerate(top, start=1):
            recs.append({
                "rank": rank,
                "strategy_id": meta["strategy_id"],
                "strategy_name": meta["strategy_name"],
                "summary": meta.get("summary", ""),
                "match_score": round(score, 2),
                "match_percentage": int(score * 100),
                "match_reasons": list(user_tags & set(meta.get("tags", []))),
                "tags": meta.get("tags", []),
                "conditions_preview": meta.get("conditions", []),
                "icon": meta.get("icon", "⭐"),
                "badge": meta.get("badge"),
            })
        return recs

    def _build_profile_summary(self, answers: Dict[str, str]) -> dict:
        """선택지 라벨을 요약으로 변환."""
        summary = {
            "investment_period": self._get_label("investment_period", answers.get("investment_period")),
            "investment_style": self._get_label("investment_style", answers.get("investment_style")),
            "risk_tolerance": self._get_label("risk_tolerance", answers.get("risk_tolerance")),
            "dividend_preference": self._get_label("dividend_preference", answers.get("dividend_preference")),
            "sector_preference": self._get_label("sector_preference", answers.get("sector_preference")),
        }
        return summary

    def _get_label(self, question_id: str, option_id: Optional[str]) -> str:
        if not option_id:
            return ""
        q = next((q for q in self.questions if q["question_id"] == question_id), None)
        if not q:
            return ""
        opt = next((o for o in q["options"] if o["id"] == option_id), None)
        return opt["label"] if opt else ""

    def _check_domain_restriction(self, message: str) -> Optional[str]:
        """금융/투자 관련 키워드가 없으면 차단 응답을 반환."""
        msg = message.lower()
        finance_keywords = [
            "주식", "종목", "투자", "전략", "시장", "증시", "etf", "펀드",
            "코스피", "코스닥", "나스닥", "s&p", "금리", "환율", "경제",
            "금융", "기업", "주가", "백테스트", "팩터", "리스크", "수익률",
            "재무", "배당", "차트", "매수", "매도", "포트폴리오", "퀀트",
            "per", "pbr", "roe", "eps", "valuation", "밸류에이션", "뉴스",
            "테마", "채권", "선물", "옵션", "원자재"
        ]

        # 전략 인물 이름(문서 내 등장) 허용
        strategy_people = [
            "워렌버핏", "워런 버핏", "버핏", "워렌 버핏",
            "벤저민 그레이엄", "그레이엄",
            "피터 린치", "린치",
            "레이 달리오", "달리오",
            "찰리 멍거", "멍거",
            "조엘 그린블라트", "그린블라트",
        ]

        if any(k.lower() in msg for k in finance_keywords + strategy_people):
            return None

        return (
            "이 서비스는 투자·금융 관련 질문에만 답변합니다. "
            "주식, 시장, 전략, 뉴스 등 금융 주제로 질문해주세요."
        )

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


            # LangChain 0.2+에서는 ainvoke 지원, 없으면 sync invoke를 쓰되 스레드로 오프로드
            if hasattr(self.agent_executor, "ainvoke"):
                response = await self.agent_executor.ainvoke(invoke_input)
            else:
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

            # Extract backtest conditions from intermediate steps if build_backtest_conditions was called
            backtest_conditions = None
            intermediate_steps = response.get("intermediate_steps", [])
            for step in intermediate_steps:
                if len(step) >= 2:
                    action, result = step[0], step[1]
                    # Check if this was a build_backtest_conditions tool call
                    if hasattr(action, 'tool') and action.tool == 'build_backtest_conditions':
                        if isinstance(result, dict) and result.get("success"):
                            backtest_conditions = result.get("conditions", [])
                            break

            result_dict = {
                "answer": answer,
                "intent": intent,
                "context": context
            }

            if backtest_conditions:
                result_dict["backtest_conditions"] = backtest_conditions

            return result_dict
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
