/**
 * QuestionnaireFlow 컴포넌트 (누적 방식)
 *
 * @description 투자 성향 설문을 채팅처럼 누적하여 표시합니다.
 * - 모든 질문과 선택지가 화면에 누적되어 표시됨
 * - 선택 즉시 다음 질문 출력 (다음 버튼 없음)
 * - 이전 질문으로 돌아가서 답변 수정 가능
 */

"use client";

import { useState, useEffect, useRef } from "react";
import {
  QUESTIONNAIRE,
  TOTAL_QUESTIONS,
  type Question,
  type QuestionnaireAnswer,
  extractTagsFromAnswers,
} from "@/data/assistantQuestionnaire";

// ============================================================================
// 타입 정의
// ============================================================================

interface QuestionnaireFlowProps {
  /** 질문 답변 배열 */
  answers: QuestionnaireAnswer[];
  /** 답변 선택 핸들러 */
  onAnswerSelect: (questionId: string, optionId: string, answerText: string) => void;
  /** 설문 완료 핸들러 (전략 추천 요청) */
  onComplete: (tags: string[]) => void;
  /** 전략 추천이 표시되었는지 여부 */
  isRecommendationShown?: boolean;
  /** 다시 시작 핸들러 */
  onRestart?: () => void;
}

// ============================================================================
// 질문 카드 컴포넌트 (누적 방식)
// ============================================================================

interface QuestionCardProps {
  question: Question;
  selectedOptionId?: string;
  onSelect: (optionId: string) => void;
  isCompleted: boolean;
  isLocked?: boolean; // 전략 추천 후 수정 불가
}

function QuestionCard({ question, selectedOptionId, onSelect, isCompleted, isLocked = false }: QuestionCardProps) {
  return (
    <div className="w-full max-w-[800px] mx-auto mb-6">
      {/* 질문 텍스트 */}
      <div className="mb-4">
        <p className="text-lg font-semibold text-gray-900">
          Q{question.order}. {question.text}
        </p>
      </div>

      {/* 선택지 그리드 */}
      <div className="grid gap-3">
        {question.options.map((option) => {
          const isSelected = selectedOptionId === option.id;

          return (
            <button
              key={option.id}
              onClick={() => !isLocked && onSelect(option.id)}
              disabled={isLocked}
              className={`
                w-full p-4 rounded-lg border-2 transition-all text-left
                ${isLocked
                  ? "cursor-not-allowed opacity-70"
                  : "cursor-pointer"
                }
                ${isSelected
                  ? "border-blue-500 bg-blue-50"
                  : "border-gray-200 bg-white hover:border-gray-300"
                }
              `}
            >
              <div className="flex items-start gap-3">
                {/* 아이콘 */}
                <span className="text-2xl flex-shrink-0">{option.icon}</span>

                <div className="flex-1">
                  {/* 레이블 */}
                  <p className={`font-medium ${isSelected ? "text-blue-700" : "text-gray-900"}`}>
                    {option.label}
                  </p>

                  {/* 설명 */}
                  <p className="text-sm text-gray-600 mt-1">
                    {option.description}
                  </p>
                </div>

                {/* 선택 인디케이터 */}
                {isSelected && (
                  <div className="flex-shrink-0">
                    <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}

// ============================================================================
// 답변 검토 카드 컴포넌트
// ============================================================================

interface AnswerReviewCardProps {
  answers: QuestionnaireAnswer[];
  onConfirm: () => void;
}

function AnswerReviewCard({ answers, onConfirm }: AnswerReviewCardProps) {
  return (
    <div className="w-full max-w-[800px] mx-auto mb-6">
      {/* 제목 */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">✅ 모든 질문에 답변하셨습니다!</h3>
        <p className="text-sm text-gray-600 mt-1">
          위로 스크롤하여 답변을 수정할 수 있습니다. 확인 후 아래 버튼을 눌러주세요.
        </p>
      </div>

      {/* 전략 추천받기 버튼 */}
      <div className="flex justify-center">
        <button
          onClick={onConfirm}
          className="px-8 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold text-lg"
        >
          🎯 맞춤 전략 추천받기
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// 진행률 표시 컴포넌트
// ============================================================================

interface ProgressBarProps {
  current: number;
  total: number;
}

function ProgressBar({ current, total }: ProgressBarProps) {
  const percentage = (current / total) * 100;

  return (
    <div className="sticky top-0 z-10 bg-white border-b border-gray-200 py-4 px-6 mb-6">
      <div className="max-w-[800px] mx-auto">
        {/* 진행률 텍스트 */}
        <p className="text-sm text-gray-600 mb-3 text-center">
          진행률: {current}/{total} ({Math.round(percentage)}%)
        </p>

        {/* 진행률 바 */}
        <div className="w-full h-2 bg-gray-200 rounded-full overflow-hidden">
          <div
            className="h-full bg-blue-500 transition-all duration-300"
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 메인 컴포넌트
// ============================================================================

/**
 * QuestionnaireFlow (누적 방식)
 *
 * @description 설문을 채팅처럼 누적하여 표시하는 컴포넌트
 */
export function QuestionnaireFlow({
  answers,
  onAnswerSelect,
  onComplete,
  isRecommendationShown = false,
  onRestart,
}: QuestionnaireFlowProps) {
  // 현재까지 표시할 질문 개수 (답변 개수 + 1, 최소 1)
  const [visibleQuestionCount, setVisibleQuestionCount] = useState<number>(
    Math.max(1, answers.length + (answers.length < TOTAL_QUESTIONS ? 1 : 0))
  );

  // 각 질문 카드에 대한 ref 배열
  const questionRefs = useRef<(HTMLDivElement | null)[]>([]);

  // answers가 변경되면 visibleQuestionCount 업데이트 (세션 복원 시)
  useEffect(() => {
    // 답변이 있으면 해당 개수만큼 + 다음 질문 1개 표시
    // 모든 답변이 완료되면 전체 표시
    const newCount = Math.max(1, answers.length + (answers.length < TOTAL_QUESTIONS ? 1 : 0));
    if (newCount > visibleQuestionCount) {
      setVisibleQuestionCount(newCount);
    }
  }, [answers.length]);

  // 답변 선택 핸들러
  const handleAnswerSelect = (questionId: string, optionId: string) => {
    const question = QUESTIONNAIRE.find(q => q.id === questionId);
    const option = question?.options.find(opt => opt.id === optionId);

    if (!question || !option) return;

    const answerText = `${option.icon} ${option.label}`;

    // 부모 컴포넌트로 답변 전달
    onAnswerSelect(questionId, optionId, answerText);

    // visibleQuestionCount 증가는 useEffect에서만 처리 (중복 증가 방지)
  };

  // 새로운 질문이 추가되면 해당 질문으로 스크롤
  useEffect(() => {
    if (visibleQuestionCount > 1) {
      const newQuestionIndex = visibleQuestionCount - 1;
      const newQuestionElement = questionRefs.current[newQuestionIndex];

      if (newQuestionElement) {
        setTimeout(() => {
          newQuestionElement.scrollIntoView({
            behavior: 'smooth',
            block: 'start',
          });
        }, 400); // 질문이 렌더링된 후 스크롤
      }
    }
  }, [visibleQuestionCount]);

  // 전략 추천 확정 핸들러
  const handleConfirm = () => {
    const tags = extractTagsFromAnswers(answers);
    onComplete(tags);
  };

  // 표시할 질문 목록
  const visibleQuestions = QUESTIONNAIRE.slice(0, visibleQuestionCount);

  // 모든 질문에 답변했는지 체크
  const allAnswered = answers.length === TOTAL_QUESTIONS;

  return (
    <div className="flex-1 flex flex-col">
      {/* 진행률 바 */}
      <ProgressBar current={answers.length} total={TOTAL_QUESTIONS} />

      {/* 질문 카드 목록 (누적) */}
      <div className="flex-1 px-4 py-6">
        {visibleQuestions.map((question, index) => {
          const answer = answers.find(a => a.questionId === question.id);
          const isCompleted = !!answer;

          return (
            <div
              key={question.id}
              ref={(el) => { questionRefs.current[index] = el; }}
            >
              <QuestionCard
                question={question}
                selectedOptionId={answer?.optionId}
                onSelect={(optionId) => handleAnswerSelect(question.id, optionId)}
                isCompleted={isCompleted}
                isLocked={isRecommendationShown}
              />
            </div>
          );
        })}

        {/* 모든 질문 완료 시 답변 검토 카드 또는 다시 시작 버튼 표시 */}
        {allAnswered && !isRecommendationShown && (
          <AnswerReviewCard
            answers={answers}
            onConfirm={handleConfirm}
          />
        )}

        {/* 전략 추천 후 다시 시작 버튼 */}
        {isRecommendationShown && onRestart && (
          <div className="w-full max-w-[800px] mx-auto mb-6">
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-sm text-yellow-800 mb-3">
                ⚠️ 전략 추천이 완료되었습니다. 선택지를 수정하려면 설문조사를 다시 시작해주세요.
              </p>
              <button
                onClick={onRestart}
                className="px-6 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors font-semibold"
              >
                🔄 설문조사 다시 시작하기
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
