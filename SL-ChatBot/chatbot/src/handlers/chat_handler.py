import os
import re
import asyncio
import types
import sys
import uuid
import json
import traceback
import logging
import hashlib
from typing import Optional, List, Dict, Any
from pathlib import Path
from dotenv import load_dotenv
import yaml
try:
    import redis  # type: ignore
except ImportError:
    redis = None

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

# 자연어 → 상위 팩터 카테고리 매핑 (config/nl_category_mapping.json 파일에서 로드)

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
    from langchain.memory import ChatMessageHistory  # type: ignore
except ImportError:
    try:
        # LangChain 0.3+는 메모리 API가 classic/community 패키지로 이동했다.
        from langchain_community.chat_message_histories import ChatMessageHistory  # type: ignore
        print('정보: ChatMessageHistory를 langchain_community에서 로드했습니다.')
    except ImportError as e:
        print(f"경고: ChatMessageHistory를 불러오지 못했습니다. pip install langchain-community 실행 필요. 오류: {e}")
        ChatMessageHistory = None

# Load environment variables
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)
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
    from retrievers.news_retriever import NewsRetriever
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

    GREETING_KEYWORDS = {"안녕", "안녕하세요", "hi", "hello", "하이", "헬로"}
    DEFAULT_GREETING_RESPONSE = "안녕하세요! AI assistent 입니다 :) 어떤 도움이 필요하신가요?"
    DSL_CACHE_VERSION = "v1"

    def __init__(self, config_path: str = "config.yaml"):
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.config_path = config_path
        self.llm_client = None
        self.rag_retriever = None
        self.factor_sync = None
        self.news_retriever = None
        self.agent_executors: Dict[str, Any] = {}
        self.system_prompts: Dict[str, str] = {}
        self.conversation_history = {}
        self.cache_client = None
        # 설문/추천 상태
        self.session_state: Dict[str, Dict[str, Any]] = {}
        self.forbidden_patterns: Dict[str, List[str]] = {}
        self.questions: List[Dict[str, Any]] = []
        self.nl_category_mapping: Dict[str, List[str]] = {}
        # LLM 메타 데이터 (에러 로깅용)
        self.llm_region: Optional[str] = None
        self.llm_model_id: Optional[str] = None
        self.llm_inference_profile_id: Optional[str] = None
        self.llm_target_id: Optional[str] = None

        self._load_config()
        self._load_forbidden_patterns()
        self.questions = self._load_questions()
        self._load_strategies()
        self._load_nl_category_mapping()
        self._init_cache_client()
        self._init_components()
        self._ensure_news_retriever()

    def _needs_news_keyword(self, message: str) -> Optional[str]:
        """뉴스 의도지만 키워드가 없는 경우 간단 안내 반환."""
        msg = (message or "").strip()
        msg_lower = msg.lower()
        news_terms = ["뉴스", "기사", "동향", "헤드라인", "최근"]
        if any(t in msg for t in news_terms):
            cleaned = msg
            for t in news_terms:
                cleaned = cleaned.replace(t, "")
            cleaned = cleaned.strip()
            # 키워드 길이가 너무 짧으면 부족한 것으로 판단
            if len(cleaned) < 2:
                return "어떤 종목/테마 뉴스가 궁금한지 알려주세요. 예) '삼성전자 뉴스 알려줘', '반도체 테마 뉴스 요약해줘'"
        return None

    def _init_cache_client(self):
        """Redis 캐시 클라이언트 초기화."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url or not redis:
            return
        try:
            self.cache_client = redis.from_url(redis_url, decode_responses=True)
            self.logger.info(f"Redis cache enabled ({redis_url})")
        except Exception as e:
            self.logger.warning(f"Redis 초기화 실패: {e}")
            self.cache_client = None

    def _load_questions(self):
        """설문 질문을 외부 파일에서 로드하고, 실패하면 기본값 사용."""
        path = Path("/app/config/questionnaire.json")
        if not path.exists():
            path = Path(__file__).parent.parent.parent / "config" / "questionnaire.json"
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if isinstance(data, list) and data:
                    print(f"Loaded questionnaire ({len(data)} questions)")
                    return data
            except Exception as e:
                print(f"Failed to load questionnaire.json: {e}")

        # fallback 기본 설문 (5문항)
        return [
            {
                "question_id": "investment_period",
                "text": "보통 얼마 동안 보유할 생각으로 투자하시나요?",
                "order": 1,
                "options": [
                    {"id": "short_term", "label": "단기 투자 (며칠 ~ 몇 주)", "description": "짧게 사고 팔면서 단기 수익을 노려요.", "icon": "⚡", "tags": ["short_term", "style_momentum"]},
                    {"id": "mid_term", "label": "중기 투자 (몇 개월)", "description": "몇 달 정도 흐름을 보면서 가져가는 편이에요.", "icon": "📊", "tags": ["mid_term"]},
                    {"id": "long_term", "label": "장기 투자 (1년 이상)", "description": "좋은 기업을 골라 오래 들고 가고 싶어요.", "icon": "🏆", "tags": ["long_term", "style_value"]},
                ],
            },
            {
                "question_id": "investment_style",
                "text": "아래 중에서 가장 본인 스타일에 가까운 걸 골라주세요.",
                "order": 2,
                "options": [
                    {"id": "value", "label": "가치 / 저평가 위주", "description": "싸게 사서 안전마진을 확보하는 것이 좋아요.", "icon": "💎", "tags": ["style_value"]},
                    {"id": "growth", "label": "성장 / 실적 위주", "description": "매출·이익이 빠르게 커지는 기업이 좋아요.", "icon": "📈", "tags": ["style_growth"]},
                    {"id": "quality", "label": "우량 / 안정성", "description": "재무가 튼튼하고 변동성이 낮은 기업을 선호해요.", "icon": "🛡️", "tags": ["style_quality"]},
                    {"id": "momentum", "label": "모멘텀 / 추세", "description": "추세를 타는 종목, 빠르게 움직이는 종목을 좋아해요.", "icon": "🚀", "tags": ["style_momentum"]},
                    {"id": "dividend", "label": "배당 / 현금흐름", "description": "배당금으로 안정적인 수익을 얻고 싶어요.", "icon": "💰", "tags": ["style_dividend"]},
                ],
            },
            {
                "question_id": "risk_tolerance",
                "text": "가격이 내려가도 어느 정도까지 버틸 수 있나요?",
                "order": 3,
                "options": [
                    {"id": "low", "label": "10% 이하 하락까지만 허용", "description": "손실은 최소화하고 싶어요.", "icon": "🧊", "tags": ["risk_low"]},
                    {"id": "medium", "label": "20% 내외 하락까지 허용", "description": "중간 정도 리스크는 감내할 수 있어요.", "icon": "🌊", "tags": ["risk_medium"]},
                    {"id": "high", "label": "30% 이상도 감내 가능", "description": "수익을 위해 변동성을 감수할 수 있어요.", "icon": "🔥", "tags": ["risk_high"]},
                ],
            },
            {
                "question_id": "dividend_preference",
                "text": "배당을 선호하시나요?",
                "order": 4,
                "options": [
                    {"id": "prefer_dividend", "label": "배당 중요", "description": "배당을 주는 종목이 좋아요.", "icon": "💵", "tags": ["prefer_dividend"]},
                    {"id": "no_dividend", "label": "배당 상관없음", "description": "배당보다는 성장/가격 상승에 관심 있어요.", "icon": "🌱", "tags": ["no_dividend"]},
                ],
            },
            {
                "question_id": "sector_preference",
                "text": "선호하는 섹터가 있나요?",
                "order": 5,
                "options": [
                    {"id": "tech", "label": "기술/성장 섹터", "description": "AI, 반도체, 클라우드 등", "icon": "🤖", "tags": ["sector_innovation", "sector_tech"]},
                    {"id": "bluechip", "label": "전통 우량 섹터", "description": "은행, 통신, 필수소비재 등", "icon": "🏛️", "tags": ["sector_bluechip"]},
                    {"id": "healthcare", "label": "헬스케어/바이오", "description": "제약, 바이오, 의료기기 등", "icon": "🧬", "tags": ["sector_healthcare"]},
                    {"id": "sector_any", "label": "특별히 상관없다", "description": "섹터는 상관없고 조건만 좋으면 된다.", "icon": "🎲", "tags": ["sector_any"]},
                ],
            },
        ]

    def _load_nl_category_mapping(self):
        """자연어 → 상위 팩터 카테고리 매핑 로드."""
        path = Path("/app/config/nl_category_mapping.json")
        if not path.exists():
            path = Path(__file__).parent.parent.parent / "config" / "nl_category_mapping.json"

        if not path.exists():
            print(f"WARNING: nl_category_mapping.json not found at {path}")
            self.nl_category_mapping = {}
            return

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                self.nl_category_mapping = {k.upper(): v for k, v in data.items()}
                print(f"Loaded nl_category_mapping ({len(self.nl_category_mapping)} categories)")
            else:
                print(f"WARNING: nl_category_mapping.json has invalid format")
                self.nl_category_mapping = {}
        except Exception as e:
            print(f"ERROR: Failed to load nl_category_mapping.json: {e}")
            self.nl_category_mapping = {}

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

    def _load_strategies(self):
        """Load strategies from prompts/strategies.json and build mappings."""
        path = Path("/app/prompts/strategies.json")
        if not path.exists():
            path = Path(__file__).parent.parent.parent / "prompts" / "strategies.json"

        strategies = []
        try:
            if path.exists():
                data = json.loads(path.read_text(encoding="utf-8"))
                strategies = data.get("strategies", [])
                print(f"Loaded {len(strategies)} strategies from strategies.json")
            else:
                print("strategies.json not found; using defaults")
        except Exception as e:
            print(f"Failed to load strategies.json: {e}")

        # Build mappings
        self.strategies = {s["id"]: s for s in strategies if "id" in s}
        # For recommendation scoring
        self.strategy_tags_mapping = {}
        for s in strategies:
            sid = s.get("id")
            if not sid:
                continue
            self.strategy_tags_mapping[sid] = {
                "strategy_id": sid,
                "strategy_name": s.get("name", sid),
                "summary": s.get("summary", ""),
                "tags": s.get("tags", []),
                "conditions": s.get("conditions_preview") or s.get("conditions") or [],
            }
        # For backtest templates
        self.strategy_backtest_templates = {}
        self.strategy_alias_map = {}
        for s in strategies:
            sid = s.get("id")
            if not sid:
                continue
            self.strategy_backtest_templates[sid] = {
                "strategy_name": s.get("name", sid),
                "buy_conditions": self._filter_valid_conditions(s.get("buy_conditions", [])),
                "sell_conditions": self._filter_valid_conditions(s.get("sell_conditions", [])),
            }
            alias_tokens = self._build_strategy_aliases(
                sid,
                s.get("name"),
                s.get("aliases", []),
            )
            self.strategy_alias_map[sid] = alias_tokens

    def _load_forbidden_patterns(self):
        """금지 패턴을 외부 설정에서 로드 (없으면 기본값 사용)."""
        default_patterns = {
            "종목_추천": [
                r"(.*?)(삼성|SK|현대|LG|카카오|네이버|넥슨|엔씨소프트|셀트리온|"
                r"NVIDIA|애플|테슬라|마이크로소프트|구글|알파벳)\s*(추천|사세요|매수|매도|사달라|팔아야)",
                r"(이 종목|이 주식).*?(상승|하락|사세요|팔아야|매수)",
                r"(꼭|반드시|꼭꼭|적극)\s*(추천|추천함|포함)",
            ],
            "매매_시점": [
                r"(지금|현재|요즘|해야|해야 할)\s*(매수|매도|사세요|팔아야|타이밍|사나|파나)",
                r"(매수|매도|사야|파야)\s*(하나|할까|할지|해야|합니다)",
                r"(매수가|적정가|목표가|손절|익절)\s*(설정|하세요|해야)",
                r"(\d+원).*?(적정|맞는|타이밍)",
                r"(언제|어디서|어떻게)\s+(매수|매도|사야|파야)",
            ],
            "수익률_보장": [
                r"(보장|확실|확정|100%|무조건)\s*(수익|이익|수익률)",
                r"(수익|이익).*?(손실|위험).*?(없|없음)",
                r"(항상|반드시)\s*(수익)",
            ],
            "개인화_조언": [
                r"(당신|너|니|저는|우리는|우리)\s*(경우|상황|환경).*?(전략|투자|추천|사는|사세요)",
                r"(월|분기|년)\s*(\d+)\s*(만원|천원|원).*?(투자|사세요|해야)",
                r"(특별히|맞춤|특화|개인|따라).*?(투자|전략|추천)",
            ],
            "비속어": [
                r"(씨발|시발|좆|병신|개새끼|ㅅㅂ|ㅈㄴ|fuck|shit|bitch)",
            ],
            "도박": [
                r"(도박|카지노|토토|바카라|룰렛|베팅|배팅)",
            ],
        }

        path = Path("/app/config/forbidden_patterns.yaml")
        if not path.exists():
            path = Path(__file__).parent.parent.parent / "config" / "forbidden_patterns.yaml"

        if path.exists():
            try:
                data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
                if isinstance(data, dict) and data:
                    self.forbidden_patterns = data
                    print(f"Loaded forbidden patterns from {path}")
                    return
            except Exception as e:
                print(f"Failed to load forbidden_patterns.yaml: {e}")

        # fallback
        self.forbidden_patterns = default_patterns
        print("Using default forbidden patterns")

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

                model_id = os.getenv("BEDROCK_MODEL_ID", self.config["llm"]["model"])
                inference_profile_id = (
                    os.getenv("BEDROCK_INFERENCE_PROFILE_ID")
                    or os.getenv("BEDROCK_INFERENCE_PROFILE_ARN")
                    or self.config["llm"].get("inference_profile_id")
                )
                model_kwargs = {
                    "temperature": self.config["llm"]["temperature"],
                    "max_tokens": self.config["llm"]["max_tokens"],
                }
                chatbedrock_kwargs = {
                    "client": bedrock_client,
                    "model_kwargs": model_kwargs,
                    "streaming": False,
                }
                # inference_profile_id를 사용하면 provider 지정이 필요하다.
                if inference_profile_id:
                    chatbedrock_kwargs["provider"] = "anthropic"
                if inference_profile_id:
                    # For provisioned throughput deployments
                    chatbedrock_kwargs["inference_profile_id"] = inference_profile_id
                else:
                    chatbedrock_kwargs["model_id"] = model_id

                try:
                    self.llm_client = ChatBedrock(**chatbedrock_kwargs)
                except Exception as e:
                    # ValidationError (Pydantic) or TypeError (old langchain-aws versions)
                    error_msg = str(e)
                    if inference_profile_id and ("inference_profile_id" in error_msg or "extra fields not permitted" in error_msg):
                        # Older langchain-aws versions don't expose inference_profile_id;
                        # fall back to passing it as model_id so the client can still route.
                        print(f"⚠️  inference_profile_id 미지원 감지 ({type(e).__name__}), model_id로 fallback...")
                        chatbedrock_kwargs.pop("inference_profile_id", None)
                        chatbedrock_kwargs["model_id"] = inference_profile_id
                        chatbedrock_kwargs.setdefault("provider", "anthropic")
                        self.llm_client = ChatBedrock(**chatbedrock_kwargs)
                        print("✅ ChatBedrock을 inference_profile_id 대신 model_id로 초기화했습니다.")
                    else:
                        # 다른 에러는 재발생
                        raise

                target_id = inference_profile_id or model_id
                # 에러 로깅을 위해 메타 데이터 저장
                self.llm_region = aws_region
                self.llm_model_id = model_id
                self.llm_inference_profile_id = inference_profile_id
                self.llm_target_id = target_id

                print(
                    "Step 1 OK: AWS Bedrock 사용 - "
                    f"리전: {aws_region}, 대상: {target_id}, "
                    f"env_model: {os.getenv('BEDROCK_MODEL_ID')}, "
                    f"env_profile: {os.getenv('BEDROCK_INFERENCE_PROFILE_ID') or os.getenv('BEDROCK_INFERENCE_PROFILE_ARN')}"
                )

                # 2. 도구 초기화
                print("Step 2: 도구 초기화 중...")
                tools = get_tools(
                    news_retriever=self.news_retriever,
                    factor_sync=self.factor_sync
                )
                print(f"Step 2 OK: 도구 초기화 완료: {[tool.name for tool in tools]}")

                # 3. 시스템 프롬프트 로드
                print("Step 3: 시스템 프롬프트 로드 중...")
                prompt_specs = {
                    "assistant": {
                        "filename": "system_assistant.txt",
                        "fallback": "당신은 정량 투자 자문가이자 투자 개념을 설명하는 어시스턴트입니다."
                    },
                    "ai_helper": {
                        "filename": "system_ai_helper.txt",
                        "fallback": "당신은 백테스트 조건을 생성하고 DSL을 만드는 AI 헬퍼입니다."
                    },
                    "home_widget": {
                        "filename": "system_home_widget.txt",
                        "fallback": "당신은 홈 화면 위젯에서 간결하게 금융 질문을 돕는 어시스턴트입니다."
                    },
                }
                self.system_prompts = {}
                for mode, spec in prompt_specs.items():
                    self.system_prompts[mode] = self._load_system_prompt_content(
                        spec["filename"],
                        spec["fallback"]
                    )
                    print(f"  - {mode} 프롬프트 {len(self.system_prompts[mode])}자 로드")
                print("Step 3 OK: 시스템 프롬프트 로드 완료")

                # 4. Claude 도구 호출 프롬프트/에이전트 생성
                print("Step 4: Claude 프롬프트 및 AgentExecutor 생성 중...")
                self.agent_executors = {}
                for mode, system_prompt in self.system_prompts.items():
                    prompt_template = ChatPromptTemplate.from_messages([
                        (
                            "system",
                            system_prompt
                            + "\n\n필요할 때 다음 도구를 사용할 수 있습니다."
                            + "\n\n{agent_scratchpad}"
                        ),
                        MessagesPlaceholder("chat_history"),
                        ("user", "참고자료:\n{context}\n\n질문: {input}"),
                    ])
                    agent = create_tool_calling_agent(self.llm_client, tools, prompt_template)
                    executor = AgentExecutor(
                        agent=agent,
                        tools=tools,
                        verbose=False,
                        return_intermediate_steps=True,
                        handle_parsing_errors=True,
                        max_iterations=5
                    )
                    self.agent_executors[mode] = executor
                    print(f"  - {mode} AgentExecutor 생성 완료")
                print("Step 4 OK: 모든 AgentExecutor 생성 완료")

                print("✅ LangChain AgentExecutor 생성 성공")
            except Exception as e:
                print(f"❌ LangChain 에이전트 초기화 오류: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"경고: 에이전트 초기화 건너뜀. 제공자={self.provider}, get_tools={get_tools is not None}")

    async def handle(
        self,
        message: str,
        session_id: Optional[str] = None,
        answer: Optional[dict] = None,
        client_type: Optional[str] = "assistant"
    ) -> dict:
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

        # client_type이 명시되지 않았거나 "assistant"일 경우 자동 라우팅
        if not client_type or client_type.lower() == "assistant":
            client_type = self._route_client_type(message)
            print(f"[AUTO-ROUTING] '{message[:50]}...' -> {client_type}")
        else:
            client_type = client_type.lower()

        # 유효성 검증
        if client_type not in ("assistant", "ai_helper", "home_widget"):
            client_type = "assistant"

        # 설문/전략 추천 플로우 (ui_language)
        if answer or (client_type == "assistant" and self._is_strategy_request(message)):
            return await self._handle_questionnaire_flow(session_id, answer, message)

        if self._is_simple_greeting(message):
            return {
                "answer": self.DEFAULT_GREETING_RESPONSE,
                "intent": "greeting",
                "session_id": session_id,
                "sources": []
            }

        if client_type == "home_widget":
            # 먼저 shortcut 처리 시도 (뉴스/스크리닝 등)
            home_widget_response = await self._handle_home_widget_shortcuts(message)
            if home_widget_response:
                home_widget_response["session_id"] = session_id
                return home_widget_response
            # shortcut이 없으면 home_widget 프롬프트로 일반 처리
            # (계속 진행하여 _generate_response_langchain에서 home_widget 에이전트 사용)

        # 도메인(금융/투자) 필터 비활성화됨

        # 뉴스 요청인데 키워드가 부족한 경우 사전 안내
        news_hint = self._needs_news_keyword(message)
        if news_hint:
            return {
                "answer": news_hint,
                "intent": "news_keyword_required",
                "session_id": session_id,
                "sources": []
            }

        # 0. 정책 검사 (투자 조언 금지 정책)
        policy_violation = self._check_investment_advisory_policy(message, session_id=session_id)
        if policy_violation:
            return {
                "answer": policy_violation,
                "intent": "policy_violation",
                "session_id": session_id,
                "sources": []
            }

        # 카테고리 매핑 기반 간단 DSL 생성 (초보자 자연어 → 상위 카테고리)
        category_response = self._maybe_handle_category_mapping(message)
        if category_response:
            category_response["session_id"] = session_id
            return category_response

        # 뉴스/테마 요청인데 뉴스/테마 서비스가 없으면 즉시 템플릿형 안내로 응답
        self._ensure_news_retriever()
        if self._is_news_theme_request(message) and not self.news_retriever:
            unavailable_answer = self._format_news_unavailable(message)
            return {
                "answer": unavailable_answer,
                "intent": "news_unavailable",
                "session_id": session_id,
                "sources": []
            }

        # 1. Classify intent
        intent = await self._classify_intent(message)
        if client_type == "ai_helper" and intent not in {"dsl_generation", "backtest_configuration", "explain"}:
            intent = "dsl_generation"

        # 2. Intent에 따라 다른 핸들러 호출
        if intent == 'dsl_generation':
            response = await self._handle_dsl_mode(message, session_id)
        elif intent == 'explain':
            response = await self._handle_explain_mode(message, session_id, client_type)
        else:
            # 기존 통합 플로우 (recommend, general 등)
            # home_widget은 빠른 응답을 위해 RAG 검색 생략
            if client_type == "home_widget":
                context = ""
            else:
                context = await self._retrieve_context(message, intent)

            # 뉴스/테마 키워드 감지 시 강제로 뉴스 + 감성 분석 먼저 수행
            news_context = ""
            if self._is_news_theme_request(message) and self.news_retriever:
                news_context = await self._fetch_news_for_context(message)
                sentiment_context = await self._fetch_sentiment_for_context(message)

                combined_context = ""
                if news_context:
                    combined_context += f"[최신 뉴스 정보]\n{news_context}"
                if sentiment_context:
                    combined_context += f"\n\n[감성 분석 데이터]\n{sentiment_context}"

                if combined_context:
                    context = f"{context}\n\n{combined_context}" if context else combined_context

            if intent == 'backtest_configuration':
                response = self._handle_backtest_configuration(message, session_id)
            else:
                response = await self._generate_response_langchain(
                    message, intent, context, session_id, client_type
                )

        response["session_id"] = session_id
        return response

    def _is_simple_greeting(self, message: str) -> bool:
        if not message:
            return False
        plain = message.strip().lower()
        return plain in self.GREETING_KEYWORDS

    def _is_strategy_request(self, message: str) -> bool:
        """전략 추천 설문을 시작할지 여부 판단."""
        msg = (message or "").lower()
        triggers = ["전략 추천", "추천받고 싶어요", "추천 해줘", "설문", "투자 성향"]
        return any(t in msg for t in triggers) or msg.strip() == ""

    def _route_client_type(self, message: str) -> str:
        """메시지 내용을 분석하여 적절한 client_type을 자동으로 결정합니다.

        우선순위:
        1. AI_HELPER - 행동 요청 (조건 만들기, DSL 생성, 전략 적용 등)
        2. ASSISTANT - 개념 설명 요청 (뭐야, 의미, 차이, 설명 등)
        3. HOME_WIDGET - 짧은 질문, 요약 요청
        4. ASSISTANT - 나머지 모든 경우 (기본값)

        Args:
            message: 사용자 입력 메시지

        Returns:
            "ai_helper", "home_widget", 또는 "assistant"
        """
        if not message:
            return "assistant"

        text = message.strip()

        # === 1순위: AI HELPER 규칙 (행동 요청) ===

        # 예외: 백테스트 개념 질문은 헬퍼가 아님
        helper_exception_patterns = [
            r"백테스트.*(무엇|뭐|왜|어떻게|알아야|필요|의미|설명)",
        ]

        is_helper_exception = False
        for pattern in helper_exception_patterns:
            if re.search(pattern, text):
                is_helper_exception = True
                break

        if not is_helper_exception:
            # AI HELPER로 보내야 하는 패턴들 (매우 명확한 DSL 생성 요청만)
            helper_patterns = [
                # 구체적인 수치가 있는 조건
                r"(<=|>=|<|>|%|이상|이하).*(매수|매도)",
                r"\d+.*(이상|이하|초과|미만).*(매수|매도)",

                # 팩터 + 조건 명시
                r"(PER|PBR|ROE|RSI|MACD|볼린저).*(조건|매수|매도)",

                # 명확한 조건/DSL 생성 요청 (전략명 없이)
                r"^(조건|DSL).*(만들|생성|해줘)",
                r"^(룰|규칙).*(만들|생성)",

                # 백테스트 + 구체적 요청
                r"백테스트.*(조건|만들|생성)",
            ]

            for pattern in helper_patterns:
                if re.search(pattern, text):
                    return "ai_helper"

        # === 2순위: ASSISTANT 개념 설명 패턴 (짧은 문장이라도 설명 요청이면 assistant) ===

        # 투자 거장/전략명 패턴 (짧아도 assistant로)
        strategy_investor_patterns = [
            r"(워렌버핏|워렌|버핏|buffett)",
            r"(피터린치|피터|린치|lynch)",
            r"(벤자민그레이엄|벤자민|그레이엄|graham)",
            r"(레이달리오|레이|달리오|dalio)",
            r"(필립피셔|필립|피셔|fisher)",
            r"전략",  # "전략" 키워드
            r"(가치투자|성장투자|모멘텀투자|배당투자)",
        ]

        for pattern in strategy_investor_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return "assistant"

        explanation_patterns = [
            r"(뭐야|뭔데|무엇|뭔지|뭔가요|뭘까)",  # "PER이 뭐야?"
            r"(의미|뜻|개념|정의)(\?|$)",  # "RSI 의미?"
            r"(설명|알려|가르쳐|알아야|이해)",  # "쉽게 설명해줘"
            r"(차이|비교|다른점)",  # "모멘텀과 가치 전략 차이"
            r"(어떤|무슨).*전략",  # "어떤 전략이 맞아?"
            r"하기 전에",  # "백테스트 하기 전에"
            r"(\?|？).*\?",  # 물음표가 2개 이상
        ]

        for pattern in explanation_patterns:
            if re.search(pattern, text):
                return "assistant"

        # === 3순위: HOME WIDGET 규칙 (짧은 질문/요약) ===

        # 20자 이하이면서 간단한 문장 (? 하나만 있거나, 단어 2-3개)
        if len(text) <= 20:
            # 단어 개수 확인
            words = re.findall(r'\S+', text)
            if len(words) <= 3:
                return "home_widget"

        # 요약/간단 요청 키워드
        widget_patterns = [
            r"(요약|간단히|한줄|짧게|핵심만)",
        ]

        for pattern in widget_patterns:
            if re.search(pattern, text):
                return "home_widget"

        # === 4순위: ASSISTANT (기본값) ===
        return "assistant"

    async def _handle_home_widget_shortcuts(self, message: str) -> Optional[dict]:
        """홈 위젯에서 자주 요청되는 단순 응답 처리."""
        if not message:
            return None

        # 1) 팩터/스크리닝 요청을 간단 템플릿으로 처리 (종목명 금지)
        if self._is_home_widget_screening_request(message):
            per_threshold = self._extract_number(message, default=10)
            buy_conditions: List[Dict[str, Any]] = [
                {"factor": "PER", "params": [], "operator": "<=", "right_factor": None, "right_params": [], "value": per_threshold},
                {"factor": "revenue_cagr_3y", "params": [], "operator": ">", "right_factor": None, "right_params": [], "value": 10},
                {"factor": "eps_growth_rate", "params": [], "operator": ">", "right_factor": None, "right_params": [], "value": 10},
                {"factor": "ROE", "params": [], "operator": ">", "right_factor": None, "right_params": [], "value": 10},
                {"factor": "DebtRatio", "params": [], "operator": "<", "right_factor": None, "right_params": [], "value": 150},
            ]

            answer = (
                "## 요약\n"
                f"PER<={per_threshold}, 성장률>10%, ROE>10%, 부채비율<150% 조건을 버튼으로 추가할 수 있습니다.\n\n"
                "### 다음 단계\n"
                "- 매수/매도 조건 버튼으로 바로 적용\n"
                "- 수치 조정이 필요하면 말씀해 주세요"
            )

            return {
                "answer": answer,
                "intent": "dsl_suggestion",
                "sources": [],
                "backtest_conditions": {"buy": buy_conditions, "sell": []},
            }

        # 2) 뉴스/시장 요약 요청 처리
        if not self._is_home_widget_news_request(message):
            return None

        # 핵심 키워드 추출 (불필요한 단어 제거)
        search_query = message.strip()
        noise_words = ["테마", "동향", "뉴스", "알려줘", "확인해줘", "최근", "의", "을", "를", "이", "가"]
        for word in noise_words:
            search_query = search_query.replace(word, " ")
        # 연속된 공백을 하나로
        import re
        search_query = re.sub(r'\s+', ' ', search_query).strip()

        if not search_query:
            search_query = message.strip()

        print(f"[뉴스 검색] 원본: '{message}' → 검색어: '{search_query}'")

        news_items: List[Dict[str, Any]] = []
        if self.news_retriever:
            try:
                news_items = await self.news_retriever.search_news_by_keyword(search_query, max_results=3)
                print(f"[뉴스 검색] 결과 {len(news_items)}건")
            except Exception as exc:
                print(f"[WARN] 홈 위젯 뉴스 검색 실패: {exc}")

        if not news_items:
            return {
                "answer": "## 요약\n해당 종목의 최신 뉴스 데이터를 찾을 수 없습니다.\n\n### 다음 단계\n- 뉴스 탭에서 직접 최신 기사를 확인해주세요.\n- 다른 종목이나 지표를 입력해 주세요.",
                "intent": "news_summary",
                "sources": []
            }

        primary = news_items[0]
        title = primary.get("title") or "최신 뉴스"
        published = (
            primary.get("publishedAt")
            or (primary.get("date") or {}).get("display")
            or ""
        )
        snippet = primary.get("summary") or primary.get("content") or ""
        snippet = snippet.strip().replace("\n", " ")
        if len(snippet) > 160:
            snippet = snippet[:157] + "..."

        main_sentence = f"{title}"
        if published:
            main_sentence += f" ({published})"
        if snippet:
            main_sentence += f" - {snippet}"

        extras = []
        for item in news_items[1:3]:
            sub_title = item.get("title")
            if not sub_title:
                continue
            sub_published = (
                item.get("publishedAt")
                or (item.get("date") or {}).get("display")
                or ""
            )
            if sub_published:
                extras.append(f"{sub_title} ({sub_published})")
            else:
                extras.append(sub_title)

        if extras:
            secondary_sentence = f"추가 기사: {', '.join(extras)}."
        else:
            secondary_sentence = "추가로 궁금한 기업이 있으면 알려주세요."

        answer = (
            f"## 요약\n{main_sentence} {secondary_sentence}\n\n"
            "### 다음 단계\n"
            "- 뉴스 탭에서 나머지 기사와 세부 내용을 확인하세요.\n"
            "- 궁금한 다른 종목이나 지표를 알려주세요."
        )

        return {
            "answer": answer,
            "intent": "news_summary",
            "sources": []
        }

    def _extract_number(self, message: str, default: float = 10) -> float:
        """메시지에서 숫자를 추출합니다. 없으면 기본값 반환."""
        import re
        numbers = re.findall(r'\d+(?:\.\d+)?', message)
        if numbers:
            return float(numbers[0])
        return default

    def _is_home_widget_screening_request(self, message: str) -> bool:
        """홈 위젯 스크리닝 요청 여부 판단 (특정 키워드 기반)."""
        if not message:
            return False
        lower = message.lower()
        # 단순 스크리닝 키워드 (팩터 조합은 category_mapping에서 처리)
        keywords = ["per", "pbr", "roe", "스크리닝", "조건 찾", "필터링"]
        return any(kw in lower for kw in keywords)

    def _is_home_widget_news_request(self, message: str) -> bool:
        if not message:
            return False
        lower = message.lower()
        keywords = ["뉴스", "동향", "headline", "테마", "시장", "최근", "트렌드", "이슈"]
        return any(kw in lower for kw in keywords)

    def _is_news_theme_request(self, message: str) -> bool:
        """뉴스/테마 요청 여부 판단 (일반 모드용)"""
        if not message:
            return False
        lower = message.lower()
        keywords = ["뉴스", "동향", "headline", "테마", "시장", "최근", "트렌드", "이슈"]
        return any(kw in lower for kw in keywords)

    async def _fetch_news_for_context(self, message: str) -> str:
        """뉴스를 검색해서 컨텍스트 문자열로 반환"""
        # 핵심 키워드 추출
        search_query = message.strip()
        noise_words = ["테마", "동향", "뉴스", "알려줘", "확인해줘", "최근", "의", "을", "를", "이", "가"]
        for word in noise_words:
            search_query = search_query.replace(word, " ")
        import re
        search_query = re.sub(r'\s+', ' ', search_query).strip()

        # 검색어가 너무 짧으면 원본 사용
        if not search_query or len(search_query) < 2:
            search_query = message.strip()

        # IT는 정보기술로 확장
        if search_query.lower() in ["it", "i t"]:
            search_query = "정보기술"

        print(f"[뉴스 컨텍스트 검색] 원본: '{message}' → 검색어: '{search_query}'")

        try:
            news_items = await self.news_retriever.search_news_by_keyword(search_query, max_results=5)
            print(f"[뉴스 컨텍스트 검색] 결과 {len(news_items)}건")

            if not news_items:
                return ""

            # 뉴스를 컨텍스트 문자열로 변환
            news_lines = []
            for idx, item in enumerate(news_items[:5], 1):
                title = item.get("title", "제목 없음")
                summary = item.get("summary") or item.get("content") or ""
                summary = summary[:150] if summary else ""
                published = item.get("publishedAt") or item.get("date", {}).get("display") or ""

                news_lines.append(f"{idx}. {title}")
                if published:
                    news_lines.append(f"   발행일: {published}")
                if summary:
                    news_lines.append(f"   요약: {summary}")

            return "\n".join(news_lines)
        except Exception as exc:
            print(f"[WARN] 뉴스 컨텍스트 검색 실패: {exc}")
            return ""

    async def _fetch_sentiment_for_context(self, message: str) -> str:
        """감성 분석 데이터를 검색해서 컨텍스트 문자열로 반환"""
        if not self.sentiment_service:
            return ""

        print(f"[감성 분석 검색] 테마별 감성 데이터 조회")

        try:
            # 테마별 감성 인사이트 가져오기
            insights = await self.sentiment_service.get_theme_sentiment_insights(limit=10)
            print(f"[감성 분석 검색] 결과 {len(insights)}건")

            if not insights:
                return ""

            # 감성 데이터를 컨텍스트 문자열로 변환
            sentiment_lines = []
            for insight in insights[:10]:
                theme_name = insight.get("theme_name", "알 수 없는 테마")
                sentiment_score = insight.get("sentiment_score", 0)
                news_count = insight.get("news_count", 0)
                interpretation = insight.get("interpretation", "")

                # 긍정/부정 판단
                if sentiment_score > 0.2:
                    sentiment_label = "긍정적"
                elif sentiment_score < -0.2:
                    sentiment_label = "부정적"
                else:
                    sentiment_label = "중립적"

                sentiment_lines.append(
                    f"- {theme_name}: {sentiment_label} (점수: {sentiment_score:.2f}, 뉴스 {news_count}건)"
                )
                if interpretation:
                    sentiment_lines.append(f"  해석: {interpretation}")

            return "\n".join(sentiment_lines)
        except Exception as exc:
            print(f"[WARN] 감성 분석 검색 실패: {exc}")
            return ""

    def _detect_nl_categories(self, message: str) -> List[str]:
        """자연어 문장에서 상위 팩터 카테고리를 추출."""
        if not message or not self.nl_category_mapping:
            return []
        msg_lower = message.lower()
        detected = []
        for category, keywords in self.nl_category_mapping.items():
            for kw in keywords:
                if kw.lower() in msg_lower:
                    detected.append(category)
                    break
        return detected

    def _build_category_conditions(self, categories: List[str]) -> List[Dict[str, Any]]:
        """카테고리별 기본 DSL 조건 묶음 생성."""
        preset: Dict[str, List[Dict[str, Any]]] = {
            "VALUE": [
                {"factor": "PER", "params": [], "operator": "<=", "right_factor": None, "right_params": [], "value": 10},
                {"factor": "PBR", "params": [], "operator": "<=", "right_factor": None, "right_params": [], "value": 1.0},
            ],
            "QUALITY": [
                {"factor": "ROE", "params": [], "operator": ">=", "right_factor": None, "right_params": [], "value": 15},
                {"factor": "OperatingProfitMargin", "params": [], "operator": ">=", "right_factor": None, "right_params": [], "value": 10},
            ],
            "GROWTH": [
                {"factor": "revenue_cagr_3y", "params": [], "operator": ">", "right_factor": None, "right_params": [], "value": 10},
                {"factor": "eps_growth_rate", "params": [], "operator": ">", "right_factor": None, "right_params": [], "value": 10},
            ],
            "MOMENTUM": [
                {"factor": "RET_60D", "params": [], "operator": ">=", "right_factor": None, "right_params": [], "value": 0.05},
            ],
            "STABILITY": [
                {"factor": "VOLATILITY_60D", "params": [], "operator": "<=", "right_factor": None, "right_params": [], "value": 0.2},
            ],
            "DIVIDEND": [
                {"factor": "DividendYield", "params": [], "operator": ">=", "right_factor": None, "right_params": [], "value": 3},
            ],
        }
        conditions: List[Dict[str, Any]] = []
        for cat in categories:
            conditions.extend(preset.get(cat, []))
        return conditions

    def _maybe_handle_category_mapping(self, message: str) -> Optional[dict]:
        """자연어 카테고리 매핑으로 즉시 DSL 조건을 반환."""
        categories = self._detect_nl_categories(message)
        if not categories:
            return None

        conditions = self._build_category_conditions(categories)
        if not conditions:
            return None

        cat_text = ", ".join(categories)
        lines = [f"- {c['factor']} {c['operator']} {c['value']}" for c in conditions]
        answer = (
            "## 요약\n"
            f"{cat_text} 기준으로 스크리닝 조건을 만들었습니다.\n\n"
            "### 조건식\n" + "\n".join(lines) + "\n\n"
            "### 다음 단계\n- 매수/매도 조건에 추가 버튼을 눌러 적용하세요. \n"
        )

        return {
            "answer": answer,
            "intent": "dsl_suggestion",
            "sources": [],
            "backtest_conditions": {
                "buy": conditions,
                "sell": []
            }
        }

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

    # def _check_domain_restriction(self, message: str) -> Optional[str]:
    #     """금융/투자 관련 키워드가 없으면 차단 응답을 반환."""
    #     msg = (message or "").lower()
    #     finance_keywords = [

    #     # 투자/주식 일반
    #     "주식", "종목", "투자", "전략", "시장", "백테스트", "포트폴리오", "퀀트",
    #     "재무", "재무제표", "리스크", "수익률", "매수", "매도",

    #     # 기본 팩터/지표
    #     "per", "pbr", "psr", "roe", "roa", "eps", "ebitda", "ev", "fcf",

    #     # 기술적 지표
    #     "rsi", "macd", "sma", "ema", "볼린저", "stochastic",

    #     # 백테스트 주요 지표
    #     "cagr", "연환산", "연평균",
    #     "mdd", "max drawdown", "낙폭",
    #     "샤프", "sharpe",
    #     "소티노", "sortino",
    #     "승률", "win rate",
    #     "손익비", "profit factor", "pf",
    #     "변동성", "volatility",
    #     "누적 수익률", "cumulative",
    #     "연도별", "월별",
    #     "드로우다운", "drawdown",
    #     "회복기간", "duration",

    #     # 뉴스/테마
    #     "뉴스", "테마", "섹터", "감성",
    #     ]


    #     # 전략 인물 이름(문서 내 등장) 허용
    #     strategy_people = [
    #         "워렌버핏", "워런 버핏", "버핏", "워렌 버핏",
    #         "벤저민 그레이엄", "그레이엄",
    #         "피터 린치", "린치",
    #         "레이 달리오", "달리오",
    #         "찰리 멍거", "멍거",
    #         "조엘 그린블라트", "그린블라트",
    #     ]

    #     if any(k.lower() in msg for k in finance_keywords + strategy_people):
    #         return None
    #     # 자연어 카테고리 매핑에 걸리면 금융 질문으로 간주
    #     if self._detect_nl_categories(message):
    #         return None

    #     return (
    #         "이 서비스는 투자·금융 관련 질문에만 답변합니다. "
    #         "주식, 시장, 전략, 뉴스 등 금융 주제로 질문해주세요."
    #     )

    async def _classify_intent(self, message: str) -> str:
        """사용자 의도 분류. DSL 생성과 설명 모드를 명확히 구분합니다."""
        message_lower = message.strip().lower()
        message_norm = self._normalize_text(message)

        # 검증 관련 키워드 (최우선 - DSL 생성보다 먼저 체크)
        verification_keywords = ['맞아', '맞나', '맞는지', '맞니', '확인', '검증', '체크', '이게 맞', '맞는 거']
        
        # 현재 설정된 조건이 포함되어 있으면 검증 요청
        has_current_conditions = '[현재 설정된 조건]' in message

        # DSL 생성 키워드 (조건, 전략 생성 관련)
        dsl_keywords = ['만들', '생성', 'per', 'pbr', 'roe', 'roa',
                        'rsi', 'macd', 'sma', 'ema', '이하', '이상', '초과', '미만']

        # Explain 키워드 (설명, 해석 관련)
        explain_keywords = ['설명', 'explain', '뭐', '무엇', '어떻게', 'how', '왜', 'why',
                           '알려줘', '가르쳐', 'cagr', 'mdd', '샤프', 'sharpe', '의미']

        # 전략 추천 키워드
        recommend_keywords = ['전략 추천', 'recommend', '추천']
        backtest_keywords = [
            '백테스트 설정', '전략으로 진행', '전략으로 백테스트', '이 전략으로', '자동 설정','백테스팅', '백테스트',"테스트",
            '백테스트 진행', '설정해줘', '전략 실행', '전략 설정', '실행해줘','하고싶어','조건 설정','조건 만들어줘'
        ]

        # 단일 지표/팩터 + 질문형(뭐/의미/설명)은 explain으로 우선 처리
        factor_keywords = ['per', 'pbr', 'roe', 'roa', 'rsi', 'sma', 'ema', 'macd', 'mdd', '샤프', 'sharpe']
        if any(f in message_lower for f in factor_keywords) and any(k in message_lower for k in explain_keywords):
            return 'explain'

        # 전략명이 포함되어 있고 '백테스트' 키워드가 있으면 강제 backtest_configuration
        if "백테스트" in message_lower and self.strategy_backtest_templates:
            for sid, meta in self.strategy_backtest_templates.items():
                name_norm = self._normalize_text(meta["strategy_name"])
                if sid in message_norm or name_norm in message_norm:
                    return 'backtest_configuration'

        # 우선순위: 검증 > 백테스트 설정 > 전략 추천 > DSL 생성 > Explain > General
        if has_current_conditions or any(word in message_lower for word in verification_keywords):
            return 'explain'  # 검증은 explain 모드로 처리 (LLM이 자연어로 답변)
        elif any(word in message_lower for word in backtest_keywords):
            return 'backtest_configuration'
        elif any(word in message_lower for word in recommend_keywords):
            return 'recommend'
        elif any(word in message_lower for word in dsl_keywords):
            return 'dsl_generation'
        elif any(word in message_lower for word in explain_keywords):
            return 'explain'
        else:
            return 'general'

    def _handle_backtest_configuration(self, message: str, session_id: str) -> dict:
        """전략 선택 후 백테스트 설정 UI Language를 반환하고 기본 DSL을 저장."""
        state = self.session_state.get(session_id, {})
        message_lower = message.lower().strip()

        # 사용자가 이전에 선택지를 받았고 "1", "2", "3" 중 하나를 선택한 경우
        if "pending_custom_condition" in state:
            custom_info = state["pending_custom_condition"]
            user_choice = None

            # 사용자 선택 확인
            if message_lower in ["1", "①", "커스텀", "커스텀만", "커스텀 조건만"]:
                user_choice = 1
            elif message_lower in ["2", "②", "전략", "전략만", "전략만 적용"]:
                user_choice = 2
            elif message_lower in ["3", "③", "둘다", "모두", "전략 + 커스텀", "커스텀 + 전략"]:
                user_choice = 3

            if user_choice:
                # 선택에 따라 백테스트 조건 설정
                days = custom_info["days"]
                pct_value = custom_info["pct_value"]

                # 커스텀 매수 조건 생성
                custom_buy_condition = {
                    "factor": f"RET_{days}D",
                    "operator": ">",
                    "value": pct_value,
                    "params": []
                }

                if user_choice == 1:
                    # 커스텀 조건만 적용
                    state["backtest_conditions"] = {
                        "buy": [custom_buy_condition],
                        "sell": []
                    }
                    state["selected_strategy"] = "custom"
                    strategy_name = "커스텀 조건"
                elif user_choice == 2:
                    # 기본 전략만 적용 (워렌버핏)
                    matched_id = "warren_buffett"
                    tpl = self.strategy_backtest_templates[matched_id]
                    state["backtest_conditions"] = {
                        "buy": self._filter_valid_conditions(tpl["buy_conditions"]),
                        "sell": self._filter_valid_conditions(tpl["sell_conditions"]),
                    }
                    state["selected_strategy"] = matched_id
                    strategy_name = tpl["strategy_name"]
                else:  # user_choice == 3
                    # 전략 + 커스텀 조건 모두 적용
                    matched_id = "warren_buffett"
                    tpl = self.strategy_backtest_templates[matched_id]
                    buy_conditions = self._filter_valid_conditions(tpl["buy_conditions"])
                    buy_conditions.append(custom_buy_condition)
                    state["backtest_conditions"] = {
                        "buy": buy_conditions,
                        "sell": self._filter_valid_conditions(tpl["sell_conditions"]),
                    }
                    state["selected_strategy"] = f"{matched_id}_custom"
                    strategy_name = f"{tpl['strategy_name']} + 커스텀 조건"

                # pending_custom_condition 제거
                del state["pending_custom_condition"]

                # UI Language 생성 및 반환
                return self._generate_backtest_ui(state, strategy_name, session_id)

        # 커스텀 수익률 조건(예: 5일 전 대비 5% 상승) 여부를 먼저 감지해 전략 덮어쓰기 방지
        import re
        ret_pattern = re.search(r"(\d+)\s*일.*?(\d+)\s*%.*?(상승|증가|올라)", message)
        has_custom_return = bool(ret_pattern)

        # 전략 식별 (간단히 이름 매칭)
        message_norm = self._normalize_text(message)
        matched_id = None
        for sid, meta in self.strategy_backtest_templates.items():
            alias_tokens = self.strategy_alias_map.get(sid, [])
            if not alias_tokens:
                alias_tokens = [self._normalize_text(meta["strategy_name"])]
            if any(token and token in message_norm for token in alias_tokens):
                matched_id = sid
                break

        # 전략 미지정 + 커스텀 조건이 감지되면 자동 전략 설정을 피하고 명확화 질문
        if not matched_id and has_custom_return:
            days, pct, _ = ret_pattern.groups()
            pct_value = float(pct) / 100 if pct else None
            example = f"RET_{days}D > {pct_value:.2f}" if pct_value is not None else ""

            # 세션에 커스텀 조건 정보 저장 (사용자 선택을 위해)
            state = self.session_state.setdefault(session_id, {})
            state["pending_custom_condition"] = {
                "days": days,
                "pct": pct,
                "pct_value": pct_value,
                "example": example
            }

            return {
                "answer": (
                    f"{days}일 전 대비 {pct}% 상승 조건이 감지됐어요.\n"
                    "백테스트를 어떻게 진행할까요?\n"
                    "① 커스텀 조건만 적용 (예: "
                    f"{example})\n"
                    "② 특정 전략만 적용 (전략명 알려주세요)\n"
                    "③ 전략 + 커스텀 조건 모두 적용\n"
                    "원하는 번호나 전략명을 알려주세요."
                ),
                "intent": "clarify_backtest",
                "session_id": session_id,
            }

        # 기본값: 워렌버핏
        if not matched_id:
            matched_id = "warren_buffett"
        tpl = self.strategy_backtest_templates[matched_id]

        # 세션 상태에 DSL 저장 (백테스트 실행 시 사용)
        state = self.session_state.setdefault(session_id, {})
        state["backtest_conditions"] = {
            "buy": self._filter_valid_conditions(tpl["buy_conditions"]),
            "sell": self._filter_valid_conditions(tpl["sell_conditions"]),
        }
        state["selected_strategy"] = matched_id

        answer = (
            f"{tpl['strategy_name']}으로 진행할게요.\n"
            "해당 전략의 매수 기준과 매도 기준을 자동으로 설정했습니다.\n\n"
            "설정이 완료되면 바로 결과를 확인하실 수 있어요."
        )

        ui_language = {
            "type": "backtest_configuration",
            "strategy": {
                "strategy_id": matched_id,
                "strategy_name": tpl["strategy_name"],
            },
            "configuration_fields": [
                {
                    "field_id": "initial_capital",
                    "label": "초기 투자 금액",
                    "type": "number",
                    "unit": "원",
                    "default_value": 10000000,
                    "min_value": 1000000,
                    "max_value": 1000000000,
                    "step": 1000000,
                    "required": True,
                },
                {
                    "field_id": "start_date",
                    "label": "백테스트 시작일",
                    "type": "date",
                    "default_value": "2021-01-01",
                    "min_value": "2005-01-01",
                    "max_value": "2025-01-01",
                    "required": True,
                },
                {
                    "field_id": "end_date",
                    "label": "백테스트 종료일",
                    "type": "date",
                    "default_value": "2024-12-31",
                    "min_value": "2005-01-01",
                    "max_value": "2025-01-01",
                    "required": True,
                },
                {
                    "field_id": "rebalance_frequency",
                    "label": "리밸런싱 주기",
                    "type": "select",
                    "default_value": "MONTHLY",
                    "options": [
                        {"value": "DAILY", "label": "매일"},
                        {"value": "WEEKLY", "label": "매주"},
                        {"value": "MONTHLY", "label": "매월"},
                    ],
                    "required": True,
                },
            ],
        }

        return {
            "answer": answer,
            "intent": "backtest_configuration",
            "ui_language": ui_language,
            "backtest_conditions": state["backtest_conditions"],
        }

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

        # 2. RAG 지식 베이스 검색 (항상 활성화 - MDD, CAGR 등 용어 질문 처리)
        if self.rag_retriever:
            try:
                rag_context = await self.rag_retriever.get_context(
                    message,
                    top_k=self.config.get("rag", {}).get("top_k", 3)
                )
                if rag_context:
                    context_parts.append(f"\n[지식 베이스]\n{rag_context}")
                    print(f"DEBUG: RAG context retrieved ({len(rag_context)} chars)")
            except Exception as e:
                print(f"RAG retrieval error: {e}")

        # 3. 뉴스 검색은 Claude의 Tool Use로 처리 (자동 검색 비활성화)
        # Claude가 필요시 search_stock_news 도구를 직접 호출합니다

        return "\n".join(context_parts) if context_parts else ""

    def _ensure_news_retriever(self) -> None:
        """뉴스 리트리버가 없으면 환경 변수로 재초기화."""
        if self.news_retriever is not None:
            return
        backend_url = os.getenv("BACKEND_URL") or os.getenv("STOCK_LAB_API_URL")
        if not backend_url:
            backend_url = "http://backend:8000/api/v1"
        if NewsRetriever:
            try:
                self.news_retriever = NewsRetriever(backend_url)
                print(f"[NewsRetriever] Lazy initialized with {backend_url}")
            except Exception as exc:
                print(f"[NewsRetriever] Lazy init failed: {exc}")
                self.news_retriever = None

    def _format_news_unavailable(self, message: str) -> str:
        """뉴스 서비스 중단 시 템플릿형 안내 메시지 생성."""
        title = (message.strip() or "시장 동향")[:30]
        return (
            f"## {title}\n"
            "- **데이터 없음**: 현재 뉴스/테마 감성 데이터를 가져올 수 없습니다.\n"
            "- **대안**: 뉴스 서비스 복구 후 다시 요청해주세요.\n"
            "- **참고**: 다른 투자/전략 질문은 바로 답변할 수 있습니다.\n\n"
            "💡 다음 단계: 서비스 복구 시 다시 테마 동향을 요청해주세요"
        )

    def _generate_backtest_ui(self, state: dict, strategy_name: str) -> dict:
        """백테스트 UI Language 생성 헬퍼 함수"""
        answer = (
            f"{strategy_name}으로 진행할게요.\n"
            "해당 전략의 매수 기준과 매도 기준을 자동으로 설정했습니다.\n\n"
            "설정이 완료되면 바로 결과를 확인하실 수 있어요."
        )

        ui_language = {
            "type": "backtest_configuration",
            "strategy": {
                "strategy_id": state.get("selected_strategy", "custom"),
                "strategy_name": strategy_name,
            },
            "configuration_fields": [
                {
                    "field_id": "initial_capital",
                    "label": "초기 투자 금액",
                    "type": "number",
                    "unit": "원",
                    "default_value": 10000000,
                    "min_value": 1000000,
                    "max_value": 1000000000,
                    "step": 1000000,
                    "required": True,
                },
                {
                    "field_id": "start_date",
                    "label": "백테스트 시작일",
                    "type": "date",
                    "default_value": "2021-01-01",
                    "min_value": "2005-01-01",
                    "max_value": "2025-01-01",
                    "required": True,
                },
                {
                    "field_id": "end_date",
                    "label": "백테스트 종료일",
                    "type": "date",
                    "default_value": "2024-12-31",
                    "min_value": "2005-01-01",
                    "max_value": "2025-01-01",
                    "required": True,
                },
                {
                    "field_id": "rebalance_frequency",
                    "label": "리밸런싱 주기",
                    "type": "select",
                    "default_value": "MONTHLY",
                    "options": [
                        {"value": "DAILY", "label": "매일"},
                        {"value": "WEEKLY", "label": "매주"},
                        {"value": "MONTHLY", "label": "매월"},
                    ],
                    "required": True,
                },
            ],
        }

        return {
            "answer": answer,
            "intent": "backtest_configuration",
            "ui_language": ui_language,
            "backtest_conditions": state["backtest_conditions"],
        }

    def _filter_valid_conditions(self, conditions: List[dict]) -> List[dict]:
        """factor/operator 없는 조건은 백테스트 오류를 방지하기 위해 제거."""
        valid = [
            c for c in conditions
            if c.get("factor") and c.get("operator") is not None
        ]
        dropped = len(conditions) - len(valid)
        if dropped:
            print(f"DSL 조건 필터링: {dropped}개 필수 필드 누락으로 제거")
        return valid

    def _normalize_text(self, text: str) -> str:
        """소문자 + 공백 제거로 간단히 정규화."""
        return re.sub(r"\s+", "", text.lower())

    def _normalize_cache_text(self, text: str) -> str:
        """캐시 키용 정규화 (소문자 + 공백 축소)."""
        return re.sub(r"\s+", " ", (text or "").strip().lower())

    def _fallback_parse_simple_conditions(self, message: str) -> List[dict]:
        """LLM DSL 파싱 실패 시 간단한 규칙으로 조건 추출."""
        text = self._normalize_condition_separators(message.lower())
        # 문장 분할: 줄바꿈, 쉼표, 그리고/및
        chunks = re.split(r"[\n,]+|\s+그리고\s+|\s+및\s+", text)
        conditions: List[dict] = []

        op_map = {
            "이하": "<=",
            "미만": "<",
            "이상": ">=",
            "초과": ">",
        }

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            # 패턴: [팩터] [숫자][%옵션] [비교어]
            match = re.search(r"([a-zA-Z가-힣_]+)\s*([\d\.]+)\s*(%|퍼센트)?\s*(이상|초과|이하|미만)", chunk)
            if not match:
                # 패턴이 반대 순서인 경우 (예: 30 이하면 RSI)
                match_alt = re.search(r"([\d\.]+)\s*(%|퍼센트)?\s*(이상|초과|이하|미만)\s*([a-zA-Z가-힣_]+)", chunk)
                if not match_alt:
                    continue
                factor_raw = match_alt.group(4)
                value_raw = match_alt.group(1)
                pct = match_alt.group(2) or ""
                op_kr = match_alt.group(3)
            else:
                factor_raw = match.group(1)
                value_raw = match.group(2)
                pct = match.group(3) or ""
                op_kr = match.group(4)

            operator = op_map.get(op_kr)
            if not operator:
                continue

            try:
                value = float(value_raw)
            except ValueError:
                continue

            conditions.append({
                "factor": factor_raw.upper(),
                "params": [],
                "operator": operator,
                "right_factor": None,
                "right_params": [],
                "value": value,
            })

        if conditions:
            print(f"[DSL Fallback] {len(conditions)}개 조건을 규칙 기반으로 파싱")
        return conditions

    def _merge_text_extracted_conditions(self, conditions: List[dict], message: str) -> List[dict]:
        """텍스트에서 직접 감지한 조건을 추가로 병합."""
        existing_factors = {str(c.get("factor") or "").upper() for c in conditions}
        extracted = self._extract_conditions_from_text(message)

        for cond in extracted:
            factor = str(cond.get("factor") or "").upper()
            if not factor:
                continue
            if factor in existing_factors:
                continue
            conditions.append(cond)
            existing_factors.add(factor)

        return conditions

    def _extract_conditions_from_text(self, message: str) -> List[dict]:
        """자연어에서 직접 조건을 추출 (LLM 누락 대비)."""
        text = self._normalize_condition_separators((message or "").lower())
        chunks = re.split(r"[\n,]+|\s+그리고\s+|\s+및\s+", text)
        conditions: List[dict] = []

        op_map = {
            "이하": "<=",
            "미만": "<",
            "이상": ">=",
            "초과": ">",
        }

        for chunk in chunks:
            chunk = chunk.strip()
            if not chunk:
                continue

            m = re.search(r"([a-zA-Z가-힣_]+)\s*([\d\.]+)\s*(%|퍼센트)?\s*(이상|초과|이하|미만)", chunk)
            if not m:
                m = re.search(r"([\d\.]+)\s*(%|퍼센트)?\s*(이상|초과|이하|미만)\s*([a-zA-Z가-힣_]+)", chunk)
                if not m:
                    continue
                factor = m.group(4)
                value_raw = m.group(1)
                op_kr = m.group(3)
            else:
                factor = m.group(1)
                value_raw = m.group(2)
                op_kr = m.group(4)

            operator = op_map.get(op_kr)
            if not operator:
                continue

            try:
                value = float(value_raw)
            except ValueError:
                continue

            conditions.append({
                "factor": factor.upper(),
                "params": [],
                "operator": operator,
                "right_factor": None,
                "right_params": [],
                "value": value,
            })

        return conditions

    def _normalize_condition_separators(self, text: str) -> str:
        """조건 연결어를 표준화 (이하이고, 이상이고 등)."""
        if not text:
            return text
        # "이하이고" → "이하 그리고", 등 비교어 뒤에 붙은 '이고'를 분리
        text = re.sub(r"(이하|이상|미만|초과)\s*이고", r"\1 그리고", text)
        # 숫자/퍼센트 뒤에 바로 '이고'가 붙은 경우 분리
        text = re.sub(r"(\d+(?:\.\d+)?\s*%?)\s*이고", r"\1 그리고", text)
        return text

    def _make_dsl_cache_key(self, message: str) -> Optional[str]:
        """DSL 캐시 키 생성."""
        if not message:
            return None
        norm = self._normalize_cache_text(message)
        digest = hashlib.sha256(norm.encode("utf-8")).hexdigest()
        return f"dsl:{self.DSL_CACHE_VERSION}:{digest}"

    def _get_cache(self, key: Optional[str]) -> Optional[dict]:
        if not key or not self.cache_client:
            return None
        try:
            raw = self.cache_client.get(key)
            if raw:
                return json.loads(raw)
        except Exception as e:
            self.logger.warning(f"Redis 캐시 조회 실패: {e}")
        return None

    def _set_cache(self, key: Optional[str], value: dict, ttl: int = 600):
        if not key or not self.cache_client:
            return
        try:
            self.cache_client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            self.logger.warning(f"Redis 캐시 저장 실패: {e}")

    def _postprocess_condition_values(self, conditions: List[dict], message: str) -> List[dict]:
        """자연어 숫자/스케일을 문맥 기반으로 보정."""
        if not conditions:
            return conditions

        message_lower = (message or "").lower()
        raw_scale_factors = {"per", "pbr", "psr", "peg"}

        def _value_from_text(factor_token: str) -> Optional[float]:
            pattern = rf"{re.escape(factor_token)}\s*([0-9]+(?:\.[0-9]+)?)"
            m = re.search(pattern, message_lower)
            if m:
                try:
                    return float(m.group(1))
                except ValueError:
                    return None
            return None

        for cond in conditions:
            factor = str(cond.get("factor") or "").lower()
            value = cond.get("value")
            if not factor or value is None:
                continue

            text_value = _value_from_text(factor)
            if text_value is not None:
                cond["value"] = text_value
                continue

            if factor in raw_scale_factors and isinstance(value, (int, float)) and 0 < abs(value) < 1:
                cond["value"] = round(value * 100, 4)

        return conditions

    def _build_strategy_aliases(self, strategy_id: str, name: Optional[str], aliases: Optional[List[str]]) -> List[str]:
        """전략 이름/별칭을 정규화된 토큰 리스트로 생성."""
        tokens: set[str] = set()

        def _add(token: Optional[str]):
            if not token or not isinstance(token, str):
                return
            normalized = self._normalize_text(token)
            if normalized:
                tokens.add(normalized)

        _add(strategy_id)
        _add(name)
        if name:
            stripped = re.sub(r"전략$", "", name).strip()
            _add(stripped)

        if aliases and isinstance(aliases, list):
            for alias in aliases:
                if not isinstance(alias, str):
                    continue
                _add(alias)
                stripped_alias = re.sub(r"전략$", "", alias).strip()
                _add(stripped_alias)

        return list(tokens)

    def _load_dsl_system_prompt(self) -> Optional[str]:
        """Load DSL-specific portion from system.txt if present."""
        prompt_path = Path("/app/prompts/system.txt")
        if not prompt_path.exists():
            prompt_path = Path(__file__).parent.parent.parent / "prompts" / "system.txt"

        try:
            content = prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            print(f"DSL 시스템 프롬프트 로드 실패: {e}")
            return None

        marker = "📌 DSL 생성 템플릿"
        if marker not in content:
            return content

        # Grab DSL 섹션부터 다음 섹션 시작 전까지 추출
        import re
        match = re.search(r"📌 DSL 생성 템플릿.*?(?=\n=+\n📌 |\Z)", content, flags=re.DOTALL)
        if match:
            return match.group(0).strip()

        return content

    def _load_system_prompt_content(self, filename: str, fallback_text: str) -> str:
        """Load custom system prompt, fallback to legacy system.txt or default text."""
        prompt_path = Path("/app/prompts") / filename
        if not prompt_path.exists():
            prompt_path = Path(__file__).parent.parent.parent / "prompts" / filename

        if prompt_path.exists():
            try:
                return prompt_path.read_text(encoding="utf-8")
            except Exception as exc:
                print(f"경고: {filename} 로드 실패 ({exc}), 기본 프롬프트 사용")

        legacy_path = Path("/app/prompts/system.txt")
        if not legacy_path.exists():
            legacy_path = Path(__file__).parent.parent.parent / "prompts" / "system.txt"
        if legacy_path.exists():
            try:
                return legacy_path.read_text(encoding="utf-8")
            except Exception:
                pass

        return fallback_text

    def _get_agent_executor(self, client_type: str):
        """Return AgentExecutor for client_type (fallback to assistant)."""
        if client_type == "ai_helper":
            normalized = "ai_helper"
        elif client_type == "home_widget":
            normalized = "home_widget"
        else:
            normalized = "assistant"
        executor = self.agent_executors.get(normalized)
        if executor:
            return executor
        return self.agent_executors.get("assistant")

    async def _generate_response_langchain(
        self,
        message: str,
        intent: str,
        context: str,
        session_id: Optional[str],
        client_type: str = "assistant"
    ) -> dict:
        """Generate response using LangChain Agent."""
        executor = self._get_agent_executor(client_type)
        if not executor:
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
        memory_key = f"{client_type}:{session_id}"
        if memory_key not in self.conversation_history:
            self.conversation_history[memory_key] = ChatMessageHistory()
        memory = self.conversation_history[memory_key]

        try:
            # Use asyncio.to_thread to run the synchronous invoke method in a separate thread
            # Pass inputs in a structured dictionary, not a single message list
            chat_history = getattr(memory, "messages", []) if memory else []

            # Prepare invoke input
            # Note: agent_scratchpad is required for both tool-calling and ReAct agents
            # Pass as empty string for initial invocation
            print(f"DEBUG INVOKE: Message='{message}', Context length={len(context)} chars")
            if context:
                print(f"DEBUG CONTEXT: {context[:500]}...")
            invoke_input = {
                "input": message,
                "context": context,
                "chat_history": chat_history,
                "agent_scratchpad": ""  # Required by both agent types
            }


            # LangChain 0.2+에서는 ainvoke 지원, 없으면 sync invoke를 쓰되 스레드로 오프로드
            if hasattr(executor, "ainvoke"):
                response = await executor.ainvoke(invoke_input)
            else:
                response = await asyncio.to_thread(
                    executor.invoke,
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
            if memory:
                memory.add_user_message(message)
                memory.add_ai_message(answer)

            # Extract backtest conditions from intermediate steps if build_backtest_conditions was called
            backtest_conditions = None
            intermediate_steps = response.get("intermediate_steps", [])
            print(f"DEBUG: intermediate_steps count: {len(intermediate_steps)}")

            for i, step in enumerate(intermediate_steps):
                print(f"DEBUG: Step {i}: type={type(step)}, len={len(step) if hasattr(step, '__len__') else 'N/A'}")
                if len(step) >= 2:
                    action, result = step[0], step[1]
                    print(f"DEBUG: Action type: {type(action)}, has tool attr: {hasattr(action, 'tool')}")
                    if hasattr(action, 'tool'):
                        print(f"DEBUG: Action.tool = '{action.tool}'")
                    print(f"DEBUG: Result type: {type(result)}, content: {result}")

                    # Check if this was a build_backtest_conditions tool call
                    if hasattr(action, 'tool') and action.tool == 'build_backtest_conditions':
                        print(f"DEBUG: Found build_backtest_conditions tool!")
                        if isinstance(result, dict) and result.get("success"):
                            backtest_conditions = result.get("conditions", [])
                            print(f"DEBUG: Extracted conditions: {backtest_conditions}")
                            break
                        else:
                            print(f"DEBUG: Result not successful or not dict: {result}")

            result_dict = {
                "answer": answer,
                "intent": intent,
                "context": context
            }

            if backtest_conditions:
                result_dict["backtest_conditions"] = backtest_conditions

            return result_dict
        except Exception as e:
            error_str = str(e)
            self._log_agent_error(
                error=e,
                intent=intent,
                client_type=client_type,
                message=message,
                context=context
            )

            # Throttling 에러인 경우 친절한 메시지
            if "ThrottlingException" in error_str or "Too many requests" in error_str:
                user_message = "🚦 요청이 많아 일시적으로 응답이 지연되고 있습니다.\n\n잠시 후(2-3분) 다시 시도해주세요."
            else:
                user_message = "응답 생성 중 오류가 발생했습니다.\n\n다시 시도해주세요."

            return {
                "answer": user_message,
                "intent": intent
            }

    def _log_agent_error(
        self,
        error: Exception,
        intent: str,
        client_type: str,
        message: str,
        context: str
    ) -> None:
        """에이전트 실패 시 디버깅 정보를 구조화해 로깅."""
        bedrock_info = None
        if self.provider == "bedrock":
            bedrock_info = {
                "region": self.llm_region,
                "model_id": self.llm_model_id,
                "inference_profile_id": self.llm_inference_profile_id,
                "target_id": self.llm_target_id,
                "env_model_id": os.getenv("BEDROCK_MODEL_ID"),
                "env_inference_profile_id": os.getenv("BEDROCK_INFERENCE_PROFILE_ID") or os.getenv("BEDROCK_INFERENCE_PROFILE_ARN"),
            }

        error_log = {
            "event": "langchain_agent_error",
            "intent": intent,
            "client_type": client_type,
            "provider": self.provider,
            "error": str(error),
            "traceback": traceback.format_exc(),
            "context_chars": len(context or ""),
            "message_chars": len(message or ""),
            "bedrock": bedrock_info,
            "message_ko": "LangChain 에이전트 실행 중 오류가 발생했습니다.",
        }
        try:
            # 한국어 요약 + JSON 상세 모두 출력
            print(
                "ERROR: LangChain 에이전트 오류 발생 | "
                f"의도={intent}, 클라이언트={client_type}, 제공자={self.provider}, "
                f"Bedrock대상={self.llm_target_id or self.llm_model_id}"
            )
            print(f"ERROR: {json.dumps(error_log, ensure_ascii=False)}")
        except Exception:
            print(f"ERROR: langchain_agent_error (fallback print) {error_log}")

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

    async def _handle_dsl_mode(self, message: str, _session_id: str) -> dict:
        """DSL 생성 모드 처리.

        - RAG 검색 금지 (context 없음)
        - DSL 전용 system prompt 사용
        - build_backtest_conditions 도구 호출하여 JSON 생성
        - backtest_conditions 필드로 분리하여 반환
        """
        cache_key = self._make_dsl_cache_key(message)
        cached = self._get_cache(cache_key)
        if cached:
            return cached

        # system.txt에서 DSL 템플릿 영역을 추출해 dsl_generator에 적용
        dsl_system_prompt = self._load_dsl_system_prompt()

        # LLM 클라이언트 확인
        if not self.llm_client:
            return {
                "answer": "LLM 클라이언트가 초기화되지 않았습니다.",
                "intent": "dsl_generation"
        }

        try:
            # build_backtest_conditions 도구 직접 호출
            from schemas import dsl_generator
            original_prompt = getattr(dsl_generator, "CLAUDE_SYSTEM_PROMPT", "")

            if dsl_system_prompt:
                try:
                    # system.txt DSL 템플릿 + 기존 스키마 안내를 함께 전달해 포맷 유지
                    combined_prompt = (
                        f"{dsl_system_prompt}\n\n{original_prompt}" if original_prompt else dsl_system_prompt
                    )
                    dsl_generator.CLAUDE_SYSTEM_PROMPT = combined_prompt
                    print(f"DSL 시스템 프롬프트 적용 완료 ({len(combined_prompt)} 자)")
                except Exception as e:
                    print(f"DSL 시스템 프롬프트 적용 실패: {e}")

            parse_strategy_text = dsl_generator.parse_strategy_text

            # 자연어 → DSL 변환
            result = parse_strategy_text(message)

            # Condition 객체를 딕셔너리로 변환 (Pydantic v1 호환)
            conditions = [condition.dict() for condition in result.conditions]
            # 필수 필드 누락 조건은 제거
            conditions = self._filter_valid_conditions(conditions)

            # 기본 DSL 파싱이 실패하면 단순 규칙 기반 파서로 재시도
            if not conditions:
                conditions = self._fallback_parse_simple_conditions(message)

            # 텍스트에서 추가로 감지되는 조건을 병합 (LLM 누락 방지)
            conditions = self._merge_text_extracted_conditions(conditions, message)

            # 자연어 숫자와 스케일이 어긋나면 문장 기반으로 보정
            conditions = self._postprocess_condition_values(conditions, message)

            if not conditions:
                return {
                    "answer": "조건을 파싱할 수 없습니다. 더 구체적인 조건을 입력해주세요.\n\n예시:\n- PER 10 이하\n- ROE 15% 이상\n- RSI 30 이하면 매수",
                    "intent": "dsl_generation",
                    "backtest_conditions": {"buy": [], "sell": []}
                }

            # 메시지를 분석해서 매수/매도 조건 분리
            import re

            buy_keywords = ["매수", "상승", "오르면", "오를", "상향", "돌파"]
            sell_keywords = ["매도", "하락", "내리면", "떨어지면", "내림", "손절", "하향"]

            message_lower = message.lower()

            def _percent_variants(value: float) -> List[str]:
                """value(소수)를 사람이 입력한 퍼센트 표현으로 변환."""
                pct = abs(value * 100)
                variants = set()
                formatted = (
                    str(int(pct))
                    if float(pct).is_integer()
                    else f"{pct:.2f}".rstrip("0").rstrip(".")
                )
                variants.add(f"{formatted}%")
                variants.add(f"{formatted} %")
                variants.add(f"{formatted}퍼센트")
                variants.add(f"{formatted} 퍼센트")
                variants.add(f"{pct}%")
                variants.add(f"{pct} %")
                variants.add(str(value))
                return [v.lower() for v in variants if v]

            def _find_indicator_position(cond: Dict[str, Any]) -> int:
                """조건과 연관된 텍스트의 대략적인 위치 탐색."""
                factor = cond.get("factor", "")
                params = cond.get("params", []) or []
                value = cond.get("value")
                search_tokens: List[str] = []

                if isinstance(factor, str) and factor:
                    search_tokens.append(factor.lower())
                    match = re.match(r"(?:RET|PRICE_CHANGE)_(\d+)D", factor.upper())
                    if match:
                        days_token = match.group(1)
                        search_tokens.extend([
                            f"{days_token}일",
                            f"{days_token} 일",
                            f"{days_token}일간",
                            f"{days_token} 일간",
                        ])

                for param in params:
                    token = str(param).strip()
                    if token:
                        search_tokens.append(token.lower())

                if isinstance(value, (int, float)):
                    search_tokens.extend(_percent_variants(value))

                for token in search_tokens:
                    pos = message_lower.find(token)
                    if pos != -1:
                        return pos
                return -1

            def _find_keyword_after(start: int, keywords: List[str]) -> int:
                best = -1
                for kw in keywords:
                    idx = message_lower.find(kw, max(start, 0))
                    if idx != -1 and (best == -1 or idx < best):
                        best = idx
                return best

            def _find_keyword_before(start: int, keywords: List[str]) -> int:
                best = -1
                end = start if start != -1 else len(message_lower)
                for kw in keywords:
                    idx = message_lower.rfind(kw, 0, end)
                    if idx != -1 and idx > best:
                        best = idx
                return best

            def _classify_condition(cond: Dict[str, Any]) -> str:
                indicator_pos = _find_indicator_position(cond)
                start_idx = indicator_pos if indicator_pos != -1 else 0

                buy_pos = _find_keyword_after(start_idx, buy_keywords)
                sell_pos = _find_keyword_after(start_idx, sell_keywords)
                if buy_pos != -1 or sell_pos != -1:
                    if sell_pos == -1 or (buy_pos != -1 and buy_pos <= sell_pos):
                        return "buy"
                    return "sell"

                # 키워드를 뒤에서 찾는 경우 (예: "매도 조건: ...")
                buy_prev = _find_keyword_before(start_idx, buy_keywords)
                sell_prev = _find_keyword_before(start_idx, sell_keywords)
                if buy_prev == -1 and sell_prev == -1:
                    return "buy"
                if sell_prev == -1 or (buy_prev != -1 and buy_prev >= sell_prev):
                    return "buy"
                return "sell"

            buy_conditions: List[Dict[str, Any]] = []
            sell_conditions: List[Dict[str, Any]] = []
            for cond in conditions:
                target_bucket = _classify_condition(cond)
                if target_bucket == "sell":
                    sell_conditions.append(cond)
                else:
                    buy_conditions.append(cond)

            # 조건 포맷팅 (요약형)
            def _fmt_value(val: Any) -> str:
                if isinstance(val, (int, float)):
                    if float(val).is_integer():
                        return str(int(val))
                    return str(round(val, 6)).rstrip("0").rstrip(".")
                return str(val)

            def _fmt(cond: Dict[str, Any]) -> str:
                factor = cond['factor']
                operator = cond['operator']
                value = cond.get('value')
                params = cond.get('params', [])
                if params:
                    factor_str = f"{factor}({', '.join(map(str, params))})"
                else:
                    factor_str = factor
                return f"{factor_str} {operator} {_fmt_value(value)}" if value is not None else factor_str

            buy_summary = ", ".join([_fmt(c) for c in buy_conditions]) if buy_conditions else ""
            sell_summary = ", ".join([_fmt(c) for c in sell_conditions]) if sell_conditions else ""

            summary_lines = []
            if buy_summary:
                summary_lines.append(f"매수: {buy_summary}")
            if sell_summary:
                summary_lines.append(f"매도: {sell_summary}")
            summary_text = "\n".join(summary_lines) if summary_lines else "조건을 버튼으로 추가할 수 있습니다."

            answer_text = (
                "## 요약\n"
                f"{summary_text}\n\n"
                "### 다음 단계\n"
                "- 매수/매도 조건 버튼으로 바로 적용\n"
                "- 수치 조정이 필요하면 말씀해 주세요"
            )

            response_payload = {
                "answer": answer_text,
                "intent": "dsl_generation",
                "backtest_conditions": {
                    "buy": buy_conditions,
                    "sell": sell_conditions
                }
            }

            self._set_cache(cache_key, response_payload)
            return response_payload
        except Exception as e:
            print(f"DSL 생성 오류: {e}")
            import traceback
            traceback.print_exc()
            return {
                "answer": f"DSL 생성 중 오류가 발생했습니다: {str(e)}",
                "intent": "dsl_generation",
                "backtest_conditions": []
            }

    async def _handle_explain_mode(self, message: str, session_id: str, client_type: str) -> dict:
        """설명 모드 처리.

        - RAG 검색 활성화 (지식 베이스 활용)
        - Explain 전용 system prompt 사용
        - Markdown 형식으로 구조화된 답변 반환
        """
        # Explain 모드에서는 RAG 검색 활성화
        context = await self._retrieve_context(message, 'explain')

        # Explain 전용 프롬프트 로드
        prompt_path = Path("/app/prompts/explain.txt")
        if not prompt_path.exists():
            prompt_path = Path(__file__).parent.parent.parent / "prompts" / "explain.txt"

        if prompt_path.exists():
            explain_system_prompt = prompt_path.read_text(encoding='utf-8')
        else:
            explain_system_prompt = """
당신은 퀀트 투자 전문 AI 어드바이저입니다.

답변 규칙:
- 항상 한국어로 답변
- Markdown 형식으로 구조화된 답변 제공
- 섹션 제목 사용 (## 📌 제목)
- 초보자도 이해할 수 있게 친절하게 설명
- 전문성 유지
"""

        # LangChain Agent로 응답 생성 (RAG 컨텍스트 포함)
        return await self._generate_response_langchain(
            message, 'explain', context, session_id, client_type
        )

    def _check_investment_advisory_policy(self, message: str, session_id: Optional[str] = None) -> Optional[str]:
        """투자 조언 정책 위반 확인.

        Returns:
            정책 위반 메시지 (위반 시), None (정책 준수 시)
        """
        # 한글은 대소문자가 없으므로 그대로 사용
        message_check = message.strip()

        # 패턴 매칭
        violations_found = []
        for violation_type, patterns in self.forbidden_patterns.items():
            for pattern in patterns:
                if __import__('re').search(pattern, message_check):
                    violations_found.append(violation_type)
                    break

        if violations_found:
            violation_type = violations_found[0]
            self._log_policy_block(violation_type, session_id or "", message)
            return self._get_policy_violation_response(violation_type)

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
        elif violation_type == "비속어":
            return (
                "서비스 품질 유지를 위해 비속어·욕설은 차단하고 있습니다.\n"
                "궁금한 점을 정중한 표현으로 말씀해주시면 빠르게 도와드릴게요."
            )
        elif violation_type == "도박":
            return (
                "도박·베팅 관련 내용은 지원하지 않습니다. 투자·금융 관련 질문만 받아요.\n"
                "주식 시장, 전략, 지표 등에 대해 물어봐주세요."
            )

        return base_response

    def _log_policy_block(self, violation_type: str, session_id: str, message: str):
        """감사 추적용 정책 차단 로그."""
        try:
            snippet = (message or "").strip()
            if len(snippet) > 200:
                snippet = snippet[:200] + "...(truncated)"
            log_payload = {
                "event": "policy_block",
                "violation_type": violation_type,
                "session_id": session_id,
                "message": snippet,
            }
            if self.logger:
                self.logger.info(json.dumps(log_payload, ensure_ascii=False))
            else:
                print(json.dumps(log_payload, ensure_ascii=False))
        except Exception as e:
            print(f"Failed to log policy block: {e}")
