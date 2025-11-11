"""
애플리케이션 전반에서 사용되는 공유 데이터
"""

AVAILABLE_THEMES = [
    {"id": "construction", "name": "건설"},
    {"id": "metal", "name": "금속"},
    {"id": "finance", "name": "금융"},
    {"id": "machinery", "name": "기계 / 장비"},
    {"id": "other-finance", "name": "기타 금융"},
    {"id": "other-manufacturing", "name": "기타 제조"},
    {"id": "other", "name": "기타"},
    {"id": "agriculture", "name": "농업 / 임업 / 어업"},
    {"id": "insurance", "name": "보험"},
    {"id": "real-estate", "name": "부동산"},
    {"id": "non-metal", "name": "비금속"},
    {"id": "textile", "name": "섬유 / 의류"},
    {"id": "entertainment", "name": "오락 / 문화"},
    {"id": "transport", "name": "운송 / 창고"},
    {"id": "transport-equipment", "name": "운송장비 / 부품"},
    {"id": "distribution", "name": "유통"},
    {"id": "bank", "name": "은행"},
    {"id": "food", "name": "음식료 / 담배"},
    {"id": "medical", "name": "의료 / 정밀기기"},
    {"id": "service", "name": "일반 서비스"},
    {"id": "utility", "name": "전기 / 가스 / 수도"},
    {"id": "electronics", "name": "전기 / 전자"},
    {"id": "pharma", "name": "제약"},
    {"id": "paper", "name": "종이 / 목재"},
    {"id": "securities", "name": "증권"},
    {"id": "publishing", "name": "출판 / 매체 복제"},
    {"id": "telecom", "name": "통신"},
    {"id": "chemical", "name": "화학"},
    {"id": "it-service", "name": "IT서비스"},
    # 챗봇이 자주 사용하는 주요 테마 추가
    {"id": "semiconductor", "name": "반도체"},
    {"id": "ai", "name": "AI"},
    {"id": "secondary_battery", "name": "2차전지"},
    {"id": "bio_pharma", "name": "바이오/제약"}, # '제약'과 중복될 수 있으나 별도 관리
    {"id": "robot", "name": "로봇"},
    {"id": "renewable_energy", "name": "신재생에너지"},
]