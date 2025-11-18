/**
 * QuestionnaireFlow 컴포넌트
 *
 * @description 투자 성향 설문 진행 흐름을 관리합니다.
 * - 질문을 순차적으로 채팅 메시지에 추가
 * - 유저 답변을 메시지로 추가
 * - 답변 검토 카드 렌더링
 * - 전략 추천받기 버튼 제공
 */

"use client";

import { useState, useEffect } from "react";
import {
  QUESTIONNAIRE,
  TOTAL_QUESTIONS,
  type Question,
  type QuestionnaireAnswer,
  createAnswer,
  extractTagsFromAnswers,
} from "@/data/assistantQuestionnaire";

// ============================================================================
// 타입 정의
// ============================================================================

interface QuestionnaireFlowProps {
  /** 현재 질문 순서 (1부터 시작) */
  currentStep: number;
  /** 질문 답변 배열 */
  answers: QuestionnaireAnswer[];
  /** 답변 선택 핸들러 */
  onAnswerSelect: (questionId: string, optionId: string, answerText: string) => void;
  /** 설문 완료 핸들러 (전략 추천 요청) */
  onComplete: (tags: string[]) => void;
  /** 이전 질문으로 이동 핸들러 */
  onNavigateToQuestion?: (order: number) => void;
}

// ============================================================================
// 질문 카드 컴포넌트
// ============================================================================

interface QuestionCardProps {
  question: Question;
  onSelect: (optionId: string) => void;
  selectedOptionId?: string;
}

function QuestionCard({ question, onSelect, selectedOptionId }: QuestionCardProps) {
  const [localSelection, setLocalSelection] = useState<string | null>(selectedOptionId || null);

  return (
    <div className="w-full max-w-[800px] mx-auto mb-6">
      {/* 질문 텍스트 */}
      <div className="mb-4">
        <p className="text-lg font-semibold text-gray-900">
          {question.text}
        </p>
        <p className="text-sm text-gray-500 mt-1">
          질문 {question.order}/{TOTAL_QUESTIONS}
        </p>
      </div>

      {/* 선택지 그리드 */}
      <div className="grid gap-3 mb-4">
        {question.options.map((option) => {
          const isSelected = localSelection === option.id;

          return (
            <button
              key={option.id}
              onClick={() => {
                setLocalSelection(option.id);
              }}
              className={`
                w-full p-4 rounded-lg border-2 transition-all text-left
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

      {/* 다음 버튼 */}
      {localSelection && (
        <div className="flex justify-end">
          <button
            onClick={() => onSelect(localSelection)}
            className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
          >
            {question.order === TOTAL_QUESTIONS ? "답변 완료" : "다음"}
          </button>
        </div>
      )}
    </div>
  );
}

// ============================================================================
// 답변 검토 카드 컴포넌트
// ============================================================================

interface AnswerReviewCardProps {
  answers: QuestionnaireAnswer[];
  onEdit: (questionOrder: number) => void;
  onConfirm: () => void;
}

function AnswerReviewCard({ answers, onEdit, onConfirm }: AnswerReviewCardProps) {
  return (
    <div className="w-full max-w-[800px] mx-auto mb-6">
      {/* 제목 */}
      <div className="mb-4">
        <h3 className="text-xl font-bold text-gray-900">답변 검토</h3>
        <p className="text-sm text-gray-600 mt-1">
          선택하신 답변을 확인하고 수정할 수 있습니다.
        </p>
      </div>

      {/* 답변 리스트 */}
      <div className="bg-white rounded-lg border border-gray-200 divide-y divide-gray-200 mb-6">
        {answers.map((answer, index) => {
          const question = QUESTIONNAIRE.find(q => q.id === answer.questionId);
          const option = question?.options.find(opt => opt.id === answer.optionId);

          if (!question || !option) return null;

          return (
            <div key={answer.questionId} className="p-4 hover:bg-gray-50 transition-colors">
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  {/* 질문 */}
                  <p className="text-sm font-medium text-gray-700 mb-2">
                    Q{question.order}. {question.text}
                  </p>

                  {/* 선택한 답변 */}
                  <div className="flex items-center gap-2">
                    <span className="text-lg">{option.icon}</span>
                    <p className="text-gray-900 font-medium">{option.label}</p>
                  </div>
                </div>

                {/* 수정 버튼 */}
                <button
                  onClick={() => onEdit(question.order)}
                  className="px-3 py-1 text-sm text-blue-600 hover:bg-blue-50 rounded transition-colors flex-shrink-0"
                >
                  수정
                </button>
              </div>
            </div>
          );
        })}
      </div>

      {/* 전략 추천받기 버튼 */}
      <div className="flex justify-center">
        <button
          onClick={onConfirm}
          className="px-8 py-3 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-semibold text-lg"
        >
          전략 추천받기
        </button>
      </div>
    </div>
  );
}

// ============================================================================
// Stepper 컴포넌트 (진행률 표시)
// ============================================================================

interface StepperProps {
  currentStep: number;
  totalSteps: number;
  onStepClick?: (step: number) => void;
  completedSteps: number[];
}

function Stepper({ currentStep, totalSteps, onStepClick, completedSteps }: StepperProps) {
  return (
    <div className="sticky top-0 z-10 bg-white border-b border-gray-200 py-4 px-6 mb-6">
      <div className="max-w-[800px] mx-auto">
        {/* 진행률 텍스트 */}
        <p className="text-sm text-gray-600 mb-3 text-center">
          질문 {currentStep}/{totalSteps}
        </p>

        {/* 진행률 바 */}
        <div className="flex items-center gap-2">
          {Array.from({ length: totalSteps }, (_, i) => i + 1).map((step) => {
            const isCompleted = completedSteps.includes(step);
            const isCurrent = step === currentStep;
            const isClickable = isCompleted || isCurrent;

            return (
              <div key={step} className="flex-1 flex items-center">
                <button
                  onClick={() => isClickable && onStepClick?.(step)}
                  disabled={!isClickable}
                  className={`
                    w-full h-2 rounded-full transition-all
                    ${isCompleted
                      ? "bg-blue-500 cursor-pointer hover:bg-blue-600"
                      : isCurrent
                      ? "bg-blue-300"
                      : "bg-gray-200 cursor-not-allowed"
                    }
                  `}
                  aria-label={`질문 ${step}`}
                />
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// 메인 컴포넌트
// ============================================================================

/**
 * QuestionnaireFlow
 *
 * @description 설문 진행 흐름을 관리하는 메인 컴포넌트
 */
export function QuestionnaireFlow({
  currentStep,
  answers,
  onAnswerSelect,
  onComplete,
  onNavigateToQuestion,
}: QuestionnaireFlowProps) {
  const [showReview, setShowReview] = useState(false);
  const [completedSteps, setCompletedSteps] = useState<number[]>([]);

  // 현재 질문 가져오기
  const currentQuestion = QUESTIONNAIRE.find(q => q.order === currentStep);

  // 현재 질문에 대한 기존 답변 (수정 모드)
  const currentAnswer = answers.find(a => a.questionId === currentQuestion?.id);

  // 답변 선택 핸들러
  const handleAnswerSelect = (optionId: string) => {
    if (!currentQuestion) return;

    const option = currentQuestion.options.find(opt => opt.id === optionId);
    if (!option) return;

    const answerText = `${option.icon} ${option.label}`;

    // 부모 컴포넌트로 답변 전달
    onAnswerSelect(currentQuestion.id, optionId, answerText);

    // 완료된 스텝 추가
    if (!completedSteps.includes(currentStep)) {
      setCompletedSteps(prev => [...prev, currentStep]);
    }

    // 마지막 질문이면 답변 검토 화면 표시
    if (currentStep === TOTAL_QUESTIONS) {
      setShowReview(true);
    }
  };

  // Stepper 클릭 핸들러
  const handleStepClick = (step: number) => {
    setShowReview(false);
    onNavigateToQuestion?.(step);
  };

  // 답변 수정 핸들러
  const handleEdit = (questionOrder: number) => {
    setShowReview(false);
    onNavigateToQuestion?.(questionOrder);
  };

  // 전략 추천 확정 핸들러
  const handleConfirm = () => {
    const tags = extractTagsFromAnswers(answers);
    onComplete(tags);
  };

  // 답변 완료 체크 (모든 질문에 답변했는지)
  useEffect(() => {
    if (answers.length === TOTAL_QUESTIONS && !showReview) {
      setShowReview(true);
    }
  }, [answers.length, showReview]);

  return (
    <div className="flex-1 flex flex-col">
      {/* Stepper - 설문 진행 중에만 표시 */}
      {!showReview && (
        <Stepper
          currentStep={currentStep}
          totalSteps={TOTAL_QUESTIONS}
          onStepClick={handleStepClick}
          completedSteps={completedSteps}
        />
      )}

      {/* 메인 콘텐츠 */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        {showReview ? (
          /* 답변 검토 카드 */
          <AnswerReviewCard
            answers={answers}
            onEdit={handleEdit}
            onConfirm={handleConfirm}
          />
        ) : currentQuestion ? (
          /* 질문 카드 */
          <QuestionCard
            question={currentQuestion}
            onSelect={handleAnswerSelect}
            selectedOptionId={currentAnswer?.optionId}
          />
        ) : (
          /* 질문을 찾을 수 없는 경우 */
          <div className="text-center text-gray-500 py-10">
            질문을 불러올 수 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}
