"use client";

import { motion } from "framer-motion";
import Image from "next/image";

const aiFeatures = [
  {
    icon: "💬",
    title: "실시간 챗봇 지원",
    description: "투자 관련 질문을 실시간으로 답변받고, 백테스트 조건을 자동으로 생성할 수 있습니다.",
    features: [
      "퀀트 투자 전략 상담",
      "팩터 및 지표 설명",
      "백테스트 조건 자동 생성",
      "실시간 시장 분석"
    ],
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    icon: "🤖",
    title: "AI 투자 어시스턴트",
    description: "AI가 당신의 투자 성향을 분석하고, 최적의 퀀트 전략을 추천해드립니다.",
    features: [
      "투자 성향 분석 설문",
      "맞춤형 전략 추천",
      "자동 백테스트 실행",
      "성과 분석 및 리포트"
    ],
    gradient: "from-purple-500 to-pink-500",
  },
];

const chatbotExample = {
  userMessage: "저PER 고ROE 전략을 테스트하고 싶어요",
  aiResponse: "저PER, 고ROE 전략을 생성했습니다. 백테스트를 실행하시겠습니까?",
  conditions: [
    "PER < 10",
    "ROE > 10%"
  ]
};

export function LandingAI() {
  return (
    <section
      id="landing-ai"
      className="relative min-h-screen py-24 px-6 overflow-hidden snap-start"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-slate-100 via-white to-slate-50 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950" />

      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-indigo-500/30 dark:via-indigo-500/50 to-transparent" />

      <div className="relative z-10 container mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
              AI 기반 투자 지원
            </span>
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-lg max-w-2xl mx-auto">
            첨단 AI 기술로 당신의 투자 여정을 더욱 스마트하게
          </p>
        </motion.div>

        {/* AI 기능 카드 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          {aiFeatures.map((feature, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.8, delay: index * 0.1 }}
              viewport={{ once: true }}
              className="relative p-8 rounded-2xl bg-gradient-to-br from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 shadow-lg hover:shadow-xl transition-all"
            >
              <div className={`inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-gradient-to-r ${feature.gradient} mb-6 text-3xl shadow-lg`}>
                {feature.icon}
              </div>

              <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-3">
                {feature.title}
              </h3>

              <p className="text-slate-600 dark:text-slate-400 mb-6 leading-relaxed">
                {feature.description}
              </p>

              <ul className="space-y-3">
                {feature.features.map((item, idx) => (
                  <li key={idx} className="flex items-center gap-3 text-slate-700 dark:text-slate-300">
                    <div className={`flex-shrink-0 w-5 h-5 rounded-full bg-gradient-to-r ${feature.gradient} flex items-center justify-center`}>
                      <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                      </svg>
                    </div>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          ))}
        </div>

        {/* 챗봇 데모 섹션 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="relative rounded-3xl bg-gradient-to-br from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 p-8 md:p-12 overflow-hidden shadow-xl"
        >
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-indigo-500/5 via-transparent to-transparent" />

          <div className="relative z-10">
            <div className="text-center mb-8">
              <h3 className="text-3xl font-bold text-slate-900 dark:text-white mb-3">
                대화형 투자 전략 설계
              </h3>
              <p className="text-slate-600 dark:text-slate-400">
                AI와 대화하며 손쉽게 백테스트 조건을 만들어보세요
              </p>
            </div>

            <div className="max-w-3xl mx-auto">
              {/* 챗봇 대화 예시 */}
              <div className="space-y-4 mb-6">
                {/* 사용자 메시지 */}
                <motion.div
                  initial={{ opacity: 0, x: 20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 }}
                  viewport={{ once: true }}
                  className="flex justify-end"
                >
                  <div className="max-w-[80%] bg-gradient-to-r from-blue-600 to-indigo-600 text-white rounded-2xl px-6 py-4 shadow-lg">
                    <p className="text-sm font-medium mb-1">You</p>
                    <p>{chatbotExample.userMessage}</p>
                  </div>
                </motion.div>

                {/* AI 응답 */}
                <motion.div
                  initial={{ opacity: 0, x: -20 }}
                  whileInView={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.5, delay: 0.4 }}
                  viewport={{ once: true }}
                  className="flex justify-start"
                >
                  <div className="max-w-[80%] bg-slate-100 dark:bg-slate-800 text-slate-900 dark:text-slate-100 rounded-2xl px-6 py-4 shadow-lg">
                    <p className="text-sm font-medium mb-1 text-indigo-600 dark:text-indigo-400">AI Assistant</p>
                    <p className="mb-3">{chatbotExample.aiResponse}</p>
                    <div className="space-y-2 p-3 bg-white/50 dark:bg-slate-900/50 rounded-lg border border-indigo-200 dark:border-indigo-500/30">
                      {chatbotExample.conditions.map((condition, idx) => (
                        <div key={idx} className="flex items-center gap-2 text-sm">
                          <span className="text-indigo-600 dark:text-indigo-400 font-mono">✓</span>
                          <span className="font-medium">{condition}</span>
                        </div>
                      ))}
                    </div>
                    <button className="mt-3 px-4 py-2 bg-gradient-to-r from-indigo-600 to-purple-600 text-white text-sm font-semibold rounded-lg hover:shadow-lg transition-all">
                      백테스트 실행
                    </button>
                  </div>
                </motion.div>
              </div>

              {/* 특징 태그 */}
              <motion.div
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5, delay: 0.6 }}
                viewport={{ once: true }}
                className="flex flex-wrap justify-center gap-3"
              >
                {["자연어 이해", "조건 자동 생성", "즉시 실행", "성과 분석"].map((tag, idx) => (
                  <span
                    key={idx}
                    className="px-4 py-2 rounded-full bg-gradient-to-r from-indigo-500/10 to-purple-500/10 border border-indigo-500/30 dark:border-indigo-500/50 text-indigo-600 dark:text-indigo-300 text-sm font-medium"
                  >
                    {tag}
                  </span>
                ))}
              </motion.div>
            </div>
          </div>

          <div className="absolute -bottom-10 -right-10 w-40 h-40 bg-gradient-to-br from-indigo-500/20 to-purple-500/20 rounded-full blur-3xl" />
          <div className="absolute -top-10 -left-10 w-40 h-40 bg-gradient-to-br from-purple-500/20 to-pink-500/20 rounded-full blur-3xl" />
        </motion.div>

        {/* 통계 섹션 */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="grid grid-cols-2 md:grid-cols-4 gap-6 mt-16"
        >
          {[
            { label: "AI 응답 시간", value: "< 3초", subtitle: "실시간 답변" },
            { label: "전략 생성", value: "자동화", subtitle: "대화형 설계" },
            { label: "사용자 만족도", value: "95%", subtitle: "높은 신뢰도" },
            { label: "지원 언어", value: "한국어", subtitle: "최적화" },
          ].map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 * index }}
              viewport={{ once: true }}
              className="p-6 rounded-xl bg-gradient-to-br from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 hover:border-indigo-500 dark:hover:border-indigo-500/50 text-center transition-all shadow-lg"
            >
              <div className="text-3xl font-bold bg-gradient-to-r from-indigo-600 to-purple-600 dark:from-indigo-400 dark:to-purple-400 bg-clip-text text-transparent mb-2">
                {stat.value}
              </div>
              <div className="text-sm font-semibold text-slate-900 dark:text-slate-300 mb-1">{stat.label}</div>
              <div className="text-xs text-slate-600 dark:text-slate-500">{stat.subtitle}</div>
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
