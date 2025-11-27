"use client";

import { motion } from "framer-motion";

const optimizations = [
  {
    title: "병렬 데이터 로드",
    before: "100%",
    beforeWidth: "100%",
    after: "60%",
    afterWidth: "60%",
    improvement: "40%",
    color: "from-blue-500 to-cyan-500",
  },
  {
    title: "멀티프로세싱 팩터 계산",
    before: "100%",
    beforeWidth: "100%",
    after: "10%",
    afterWidth: "10%",
    improvement: "10배",
    color: "from-purple-500 to-pink-500",
  },
  {
    title: "포트폴리오 벡터화",
    before: "100%",
    beforeWidth: "100%",
    after: "5-10%",
    afterWidth: "20%",
    improvement: "10-20배",
    color: "from-pink-500 to-rose-500",
  },
  {
    title: "벡터화 조건 평가",
    before: "100%",
    beforeWidth: "100%",
    after: "0.1-0.2%",
    afterWidth: "8%",
    improvement: "500-1000배",
    color: "from-orange-500 to-red-500",
  },
];

const benchmarks = [
  {
    period: "1개월 백테스트",
    before: "21-35초",
    after: "3-5초",
    improvement: "7-10배 개선",
  },
  {
    period: "1년 백테스트",
    before: "250-350초",
    after: "25-35초",
    improvement: "10-14배 개선",
  },
];

export function LandingPerformance() {
  return (
    <section
      id="landing-performance"
      className="relative min-h-screen py-24 px-6 overflow-hidden snap-start"
    >
      <div className="absolute inset-0 bg-gradient-to-b from-white via-slate-50 to-slate-100 dark:from-slate-950 dark:via-slate-900 dark:to-slate-950" />

      <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-transparent via-purple-500/30 dark:via-purple-500/50 to-transparent" />

      <div className="relative z-10 container mx-auto max-w-7xl">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="text-center mb-16"
        >
          <h2 className="text-4xl md:text-5xl font-bold mb-6">
            <span className="bg-gradient-to-r from-purple-400 to-pink-400 bg-clip-text text-transparent">
              검증된 성능
            </span>
          </h2>
          <p className="text-slate-600 dark:text-slate-400 text-lg max-w-2xl mx-auto">
            다양한 최적화 기법으로 업계 최고 수준의 백테스팅 속도를 제공합니다
          </p>
        </motion.div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="p-8 rounded-2xl bg-gradient-to-br from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 shadow-lg"
          >
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">최적화 성과</h3>
            <div className="space-y-6">
              {optimizations.map((opt, index) => (
                <div key={index} className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-slate-700 dark:text-slate-300 font-medium">{opt.title}</span>
                    <span className={`text-sm font-bold bg-gradient-to-r ${opt.color} bg-clip-text text-transparent`}>
                      {opt.improvement} ↑
                    </span>
                  </div>
                  <div className="relative h-3 bg-slate-200 dark:bg-slate-800 rounded-full overflow-hidden">
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: opt.beforeWidth }}
                      transition={{ duration: 1, delay: 0.2 + index * 0.1 }}
                      viewport={{ once: true }}
                      className="absolute h-full bg-slate-300 dark:bg-slate-700 rounded-full"
                    />
                    <motion.div
                      initial={{ width: 0 }}
                      whileInView={{ width: opt.afterWidth }}
                      transition={{ duration: 1, delay: 0.4 + index * 0.1 }}
                      viewport={{ once: true }}
                      className={`absolute h-full bg-gradient-to-r ${opt.color} rounded-full`}
                    />
                  </div>
                  <div className="flex justify-between text-xs text-slate-600 dark:text-slate-500">
                    <span>최적화 전: {opt.before}</span>
                    <span>최적화 후: {opt.after}</span>
                  </div>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            whileInView={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.8 }}
            viewport={{ once: true }}
            className="p-8 rounded-2xl bg-gradient-to-br from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 shadow-lg"
          >
            <h3 className="text-2xl font-bold text-slate-900 dark:text-white mb-6">백테스트 속도</h3>
            <div className="space-y-8">
              {benchmarks.map((bench, index) => (
                <motion.div
                  key={index}
                  initial={{ opacity: 0, y: 20 }}
                  whileInView={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.5, delay: 0.2 + index * 0.1 }}
                  viewport={{ once: true }}
                  className="space-y-4"
                >
                  <div className="flex items-center justify-between">
                    <span className="text-lg font-semibold text-slate-900 dark:text-slate-200">{bench.period}</span>
                    <span className="px-3 py-1 rounded-full bg-gradient-to-r from-green-500/20 to-emerald-500/20 border border-green-500/30 text-green-600 dark:text-green-300 text-sm font-bold">
                      {bench.improvement}
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="p-4 rounded-xl bg-slate-100 dark:bg-slate-800/50 border border-slate-300 dark:border-slate-700">
                      <div className="text-xs text-slate-600 dark:text-slate-500 mb-1">최적화 전</div>
                      <div className="text-2xl font-bold text-slate-700 dark:text-slate-400">{bench.before}</div>
                    </div>
                    <div className="p-4 rounded-xl bg-gradient-to-r from-blue-50 to-purple-50 dark:from-blue-500/10 dark:to-purple-500/10 border border-blue-300 dark:border-blue-500/30">
                      <div className="text-xs text-blue-600 dark:text-blue-300 mb-1">최적화 후</div>
                      <div className="text-2xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent">
                        {bench.after}
                      </div>
                    </div>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          viewport={{ once: true }}
          className="grid grid-cols-1 md:grid-cols-4 gap-6"
        >
          {[
            { label: "재무 팩터 캐싱", value: "244배", subtitle: "DB 쿼리 절감" },
            { label: "UPSERT 최적화", value: "10배", subtitle: "DB 저장 개선" },
            { label: "Redis 캐싱", value: "500배", subtitle: "반복 조회 개선" },
            { label: "전체 최적화", value: "10-14배", subtitle: "End-to-End" },
          ].map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.9 }}
              whileInView={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5, delay: 0.1 * index }}
              viewport={{ once: true }}
              className="p-6 rounded-xl bg-gradient-to-br from-white/90 to-slate-50/90 dark:from-slate-800/50 dark:to-slate-900/50 backdrop-blur-sm border border-slate-200/80 dark:border-slate-700/50 hover:border-blue-500 dark:hover:border-blue-500/50 text-center transition-all shadow-lg"
            >
              <div className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 dark:from-blue-400 dark:to-purple-400 bg-clip-text text-transparent mb-2">
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
