"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { ConfirmModal } from "@/components/modal/ConfirmModal";
import { RecommendationUILanguage, parseDSL } from "@/lib/api/chatbot";

interface RecommendationViewProps {
  uiLanguage: RecommendationUILanguage;
}

/**
 * 전략 추천 결과 화면
 *
 * @description 추천된 전략 목록과 사용자 프로필 요약을 표시합니다
 */
export function RecommendationView({ uiLanguage }: RecommendationViewProps) {
  const { recommendations, user_profile_summary } = uiLanguage;
  const router = useRouter();
  const [loadingStrategy, setLoadingStrategy] = useState<string | null>(null);

  // 알림 모달 상태
  const [alertModal, setAlertModal] = useState<{
    isOpen: boolean;
    title: string;
    message: string;
    iconType: "info" | "warning" | "error" | "success" | "question";
  }>({ isOpen: false, title: "", message: "", iconType: "info" });

  // 알림 모달 표시 헬퍼
  const showAlert = (
    title: string,
    message: string,
    iconType: "info" | "warning" | "error" | "success" | "question" = "info"
  ) => {
    setAlertModal({ isOpen: true, title, message, iconType });
  };

  /**
   * 백테스트 버튼 클릭 핸들러
   */
  const handleBacktest = async (strategyId: string, conditionsPreview: any[]) => {
    try {
      setLoadingStrategy(strategyId);

      // 조건 설명을 텍스트로 변환
      const conditionsText = conditionsPreview
        .map((cond) => cond.condition)
        .join(", ");

      // DSL API 호출하여 JSON 조건 생성
      const dslResponse = await parseDSL(conditionsText);

      // 백테스트 페이지로 이동하며 DSL 조건 전달
      const queryParams = new URLSearchParams({
        strategy_id: strategyId,
        conditions: JSON.stringify(dslResponse.conditions),
      });

      router.push(`/quant/new?${queryParams.toString()}`);
    } catch (error) {
      console.error("DSL 변환 실패:", error);
      showAlert("조건 변환 실패", "전략 조건을 변환하는 중 오류가 발생했습니다. 다시 시도해주세요.", "error");
    } finally {
      setLoadingStrategy(null);
    }
  };

  return (
    <div className="w-full max-w-[1200px] mx-auto p-8">
      {/* 제목 */}
      <h1 className="text-3xl font-bold text-black mb-8 text-center">
        회원님께 추천하는 투자 전략
      </h1>

      {/* 사용자 프로필 요약 */}
      <div className="mb-10 p-6 bg-blue-50 rounded-lg">
        <h2 className="text-xl font-bold text-black mb-4">회원님의 투자 성향</h2>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
          <div>
            <p className="text-sm text-gray-600 mb-1">투자 기간</p>
            <p className="font-semibold text-black">
              {user_profile_summary.investment_period}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">투자 스타일</p>
            <p className="font-semibold text-black">
              {user_profile_summary.investment_style}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">위험 감수도</p>
            <p className="font-semibold text-black">
              {user_profile_summary.risk_tolerance}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">배당 선호도</p>
            <p className="font-semibold text-black">
              {user_profile_summary.dividend_preference}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600 mb-1">선호 섹터</p>
            <p className="font-semibold text-black">
              {user_profile_summary.sector_preference}
            </p>
          </div>
        </div>
      </div>

      {/* 추천 전략 목록 */}
      <div className="space-y-6">
        {recommendations.map((rec) => (
          <div
            key={rec.strategy_id}
            className="p-6 bg-white border-2 rounded-lg shadow-md hover:shadow-lg transition-shadow"
          >
            <div className="flex items-start justify-between">
              {/* 왼쪽: 전략 정보 */}
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  {/* 순위 배지 */}
                  <div className="flex items-center justify-center w-10 h-10 bg-blue-600 text-white font-bold rounded-full">
                    {rec.rank}
                  </div>

                  {/* 아이콘 */}
                  <div className="text-3xl">{rec.icon}</div>

                  {/* 전략명 */}
                  <h3 className="text-xl font-bold text-black">
                    {rec.strategy_name}
                  </h3>

                  {/* 배지 */}
                  {rec.badge && (
                    <span className="px-3 py-1 bg-yellow-400 text-black text-sm font-semibold rounded-full">
                      {rec.badge}
                    </span>
                  )}
                </div>

                {/* 요약 */}
                <p className="text-gray-700 mb-4">{rec.summary}</p>

                {/* 매칭 이유 */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-gray-800 mb-2">
                    추천 이유:
                  </h4>
                  <ul className="space-y-1">
                    {rec.match_reasons.map((reason, idx) => (
                      <li key={idx} className="text-sm text-gray-600 flex items-start">
                        <span className="text-blue-600 mr-2">•</span>
                        {reason}
                      </li>
                    ))}
                  </ul>
                </div>

                {/* 조건 미리보기 */}
                {rec.conditions_preview && rec.conditions_preview.length > 0 && (
                  <div className="mb-4">
                    <h4 className="text-sm font-semibold text-gray-800 mb-2">
                      주요 조건:
                    </h4>
                    {rec.conditions_preview.map((cond, idx) => (
                      <div key={idx} className="mb-2">
                        <p className="text-sm font-medium text-gray-700">
                          {cond.condition}
                        </p>
                        {cond.condition_info && cond.condition_info.length > 0 && (
                          <ul className="ml-4 space-y-1">
                            {cond.condition_info.map((info, infoIdx) => (
                              <li
                                key={infoIdx}
                                className="text-xs text-gray-600"
                              >
                                - {info}
                              </li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                )}

                {/* 태그 */}
                {rec.tags && rec.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2">
                    {rec.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* 오른쪽: 매칭 점수 */}
              <div className="ml-6 text-center">
                <div className="mb-2">
                  <div className="text-4xl font-bold text-blue-600">
                    {rec.match_percentage}%
                  </div>
                  <p className="text-sm text-gray-600">매칭도</p>
                </div>
                <div className="w-24 h-24 mx-auto">
                  <svg className="transform -rotate-90" viewBox="0 0 100 100">
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#e5e7eb"
                      strokeWidth="10"
                    />
                    <circle
                      cx="50"
                      cy="50"
                      r="45"
                      fill="none"
                      stroke="#2563eb"
                      strokeWidth="10"
                      strokeDasharray={`${rec.match_percentage * 2.827} 283`}
                      strokeLinecap="round"
                    />
                  </svg>
                </div>
              </div>
            </div>

            {/* 백테스트 버튼 */}
            <div className="mt-4 pt-4 border-t">
              <button
                type="button"
                onClick={() => handleBacktest(rec.strategy_id, rec.conditions_preview)}
                disabled={loadingStrategy === rec.strategy_id}
                className="w-full py-3 bg-blue-600 text-white font-semibold rounded-lg hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {loadingStrategy === rec.strategy_id
                  ? "조건 생성 중..."
                  : "이 전략으로 백테스트 실행하기"}
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* 알림 모달 */}
      <ConfirmModal
        isOpen={alertModal.isOpen}
        onClose={() => setAlertModal((prev) => ({ ...prev, isOpen: false }))}
        onConfirm={() => setAlertModal((prev) => ({ ...prev, isOpen: false }))}
        title={alertModal.title}
        message={alertModal.message}
        confirmText="확인"
        iconType={alertModal.iconType}
        alertOnly
      />
    </div>
  );
}
