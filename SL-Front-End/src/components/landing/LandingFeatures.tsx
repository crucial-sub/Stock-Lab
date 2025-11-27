"use client";

import { motion } from "framer-motion";

const features = [
  {
    icon: "⚡",
    title: "초고속 백테스팅",
    description: "벡터화 알고리즘과 멀티프로세싱으로 1년 백테스트를 25-35초에 완료합니다.",
    gradient: "from-blue-500 to-cyan-500",
  },
  {
    icon: "📊",
    title: "140여개 금융 팩터",
    description: "기술적 지표, 재무 지표, 모멘텀 지표 등 다양한 팩터를 활용한 전략 수립이 가능합니다.",
    gradient: "from-purple-500 to-pink-500",
  },
  {
    icon: "🎯",
    title: "정교한 조건 설정",
    description: "논리식 기반 매수/매도 조건과 목표가/손절가 설정으로 세밀한 전략 시뮬레이션이 가능합니다.",
    gradient: "from-pink-500 to-rose-500",
  },
  {
    icon: "🚀",
    title: "실시간 성과 분석",
    description: "샤프지수, MDD, 승률 등 다양한 지표로 전략의 성과를 실시간으로 분석합니다.",
    gradient: "from-orange-500 to-amber-500",
  },
  {
    icon: "🔄",
    title: "리밸런싱 자동화",
    description: "일간/월간 자동 리밸런싱으로 최적의 포트폴리오를 유지합니다.",
    gradient: "from-green-500 to-emerald-500",
  },
  {
    icon: "💡",
    title: "AI 투자 어시스턴트",
    description: "AI 기반 전략 추천과 시장 분석으로 더 나은 투자 결정을 지원합니다.",
    gradient: "from-indigo-500 to-purple-500",
  },
];

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
    },
  },
};

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.5,
    },
  },
};

export function LandingFeatures() {
  return (
    <section className="relative py-24 px-6 overflow-hidden">
      <div className="absolute inset-0 bg-gradient-to-b from-slate-50 via-white to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950" />

      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-blue-500/30 dark:via-blue-500/50 to-transparent" />

      <div className="relative z-10 container mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
              강력한 기능들
            </span>
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-lg max-w-2xl mx-auto">
            투자 전략 수립부터 백테스팅, 성과 분석까지 모든 것을 한 곳에서
          </p>
        </motion.div>

        <motion.div
          variants={containerVariants}
          initial="hidden"
          whileInView="visible"
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"
        >
          {features.map((feature, index) => (
            <motion.div
              key={index}
              variants={itemVariants}
              whileHover={{ scale: 1.05, y: -5 }}
              className="group relative p-8 rounded-2xl bg-gradient-to-b from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 hover:border-blue-400 dark:hover:border-slate-600 transition-all cursor-pointer overflow-hidden shadow-sm hover:shadow-lg"
            >
              <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />

              <div className="relative z-10">
                <div
                  className={`inline-flex items-center justify-center w-14 h-14 rounded-xl bg-gradient-to-r ${feature.gradient} mb-6 text-2xl`}
                >
                  {feature.icon}
                </div>

                <h3 className="text-xl font-bold text-slate-900 dark:text-white mb-3 group-hover:text-blue-600 dark:group-hover:text-blue-300 transition-colors">
                  {feature.title}
                </h3>

                <p className="text-slate-600 dark:text-slate-400 leading-relaxed group-hover:text-slate-700 dark:group-hover:text-slate-300 transition-colors">
                  {feature.description}
                </p>
              </div>

              <div className="absolute top-0 right-0 w-32 h-32 bg-gradient-to-br from-blue-500/10 to-purple-500/10 rounded-full blur-2xl opacity-0 group-hover:opacity-100 transition-opacity" />
            </motion.div>
          ))}
        </motion.div>
      </div>
    </section>
  );
}
