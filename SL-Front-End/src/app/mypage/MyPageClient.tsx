"use client";

import { useState } from "react";
import { UserResponse, authApi } from "@/lib/api/auth";
import { UserInfoSection } from "@/components/mypage/UserInfoSection";
import { AccountSection } from "@/components/mypage/AccountSection";
import { MyPostsSection } from "@/components/mypage/MyPostsSection";

interface MyPageClientProps {
  initialUser: UserResponse;
  formattedCreatedAt: string;
}

export function MyPageClient({ initialUser, formattedCreatedAt }: MyPageClientProps) {
  const [user, setUser] = useState<UserResponse>(initialUser);
  const [createdAtFormatted, setCreatedAtFormatted] = useState(formattedCreatedAt);

  const fetchUserInfo = async () => {
    try {
      const userData = await authApi.getCurrentUser();
      setUser(userData);

      // 클라이언트에서 날짜 재포맷
      const formatted = new Date(userData.created_at).toLocaleDateString("ko-KR", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
      setCreatedAtFormatted(formatted);
    } catch (error) {
      console.error("사용자 정보 조회 실패:", error);
    }
  };

  return (
    <div className="mx-auto flex w-full max-w-[1000px] py-[60px] flex-col gap-8">
      <div className="flex flex-col gap-2">
        <span className="text-[1.5rem] font-semibold text-[#000000]">마이페이지</span>
      </div>

      {/* 기본 정보 섹션 */}
      <UserInfoSection
        user={user}
        formattedCreatedAt={createdAtFormatted}
        onUserUpdate={fetchUserInfo}
      />

      {/* 연동 계좌 관리 섹션 */}
      <AccountSection />

      {/* 내 게시물 모아보기 섹션 */}
      <MyPostsSection userId={user.user_id} />
    </div>
  );
}
