import { KiwoomConnectModal } from "@/components/modal/KiwoomConnectModal";
import { kiwoomApi } from "@/lib/api/kiwoom";
import { useEffect, useState } from "react";
import { HomePageClient } from "./HomePageClient";

/**
 * 홈 페이지 (서버 컴포넌트)
 *
 * @description 메인 홈 화면의 진입점입니다.
 * 서버에서 인증 상태를 확인하고, 적절한 화면을 렌더링합니다.
 *
 * @future
 * - 로그인 여부 확인: const session = await getServerSession();
 * - 로그인 안 되어 있으면: return <LoginPrompt />;
 * - 로그인 되어 있으면: return <HomePageClient userName={session.user.name} />;
 */

export default async function HomePage() {
  // TODO: 인증 구현 후 활성화
  // const session = await getServerSession();
  //
  // if (!session) {
  //   return <LoginPrompt />;
  // }

  const [isKiwoomModalOpen, setIsKiwoomModalOpen] = useState(false);
  const [isKiwoomConnected, setIsKiwoomConnected] = useState(false);

  useEffect(() => {
    const checkKiwoomStatus = async () => {
      try {
        const status = await kiwoomApi.getStatus();
        setIsKiwoomConnected(status.is_connected);
      } catch (error) {
        // 인증되지 않은 경우 무시
        console.log("키움증권 연동 상태 확인 실패 (로그인 필요)");
      }
    };
    checkKiwoomStatus();
  }, []);

  const handleKiwoomSuccess = () => {
    setIsKiwoomConnected(true);
  };

  return (
    <>
      <div className="">
        <div className="flex w-full flex-col gap-10 md:px-10 lg:px-0">
          {/* 키움증권 연동 버튼 */}
          <div className="flex justify-end">
            <button
              onClick={() => setIsKiwoomModalOpen(true)}
              className={`px-6 py-2 rounded-md font-medium transition-colors ${
                isKiwoomConnected
                  ? "bg-green-500 text-white hover:bg-green-600"
                  : "bg-primary-main text-white hover:bg-primary-dark"
              }`}
            >
              {isKiwoomConnected ? "✓ 증권사 연동됨" : "증권사 연동하기"}
            </button>
          </div>
        </div>
      </div>

      <KiwoomConnectModal
        isOpen={isKiwoomModalOpen}
        onClose={() => setIsKiwoomModalOpen(false)}
        onSuccess={handleKiwoomSuccess}
      />
      <HomePageClient userName="은따거" />
    </>
  );
}
