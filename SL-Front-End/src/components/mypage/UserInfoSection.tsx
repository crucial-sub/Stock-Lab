"use client";

import { ReactNode, useState } from "react";
import { UserResponse } from "@/lib/api/auth";
import { NicknameChangeModal } from "@/components/modal/NicknameChangeModal";
import { DeleteAccountModal } from "@/components/modal/DeleteAccountModal";
import { PasswordChangeModal } from "@/components/modal/PasswordChangeModal";

interface UserInfoSectionProps {
  user: UserResponse;
  formattedCreatedAt: string;
  onUserUpdate: () => void;
}

export function UserInfoSection({ user, formattedCreatedAt, onUserUpdate }: UserInfoSectionProps) {
  const [isNicknameModalOpen, setIsNicknameModalOpen] = useState(false);
  const [isPasswordModalOpen, setIsPasswordModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const renderField = (label: string, value: ReactNode) => (
    <div className="flex flex-col gap-2">
      <span className="text-[0.875rem] font-semibold text-[#646464]">{label}</span>
      <div className="flex items-center border-[0.5px] border-[#C8C8C8] rounded-[12px] bg-[#FFFFFF33] px-5 py-3 text-[1rem] font-normal text-[#000000] shadow-elev-card-soft">
        {value ?? "-"}
      </div>
    </div>
  );

  return (
    <section className="rounded-[12px] p-7 shadow-elev-card backdrop-blur bg-[#1822340D]">
      <div className="flex flex-col gap-8">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-[0.75rem] font-normal uppercase tracking-widest text-[#646464]">Profile</p>
            <h2 className="text-[1.5rem] font-semibold text-[#000000]">기본 정보</h2>
          </div>
          <button
            onClick={() => setIsNicknameModalOpen(true)}
            className="rounded-full bg-brand-purple px-5 py-2 text-[0.875rem] font-semibold text-white transition hover:bg-brand-purple/80"
          >
            닉네임 변경
          </button>
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          {renderField("이름", user.name)}
          {renderField("닉네임", user.nickname)}
          {renderField("이메일", user.email)}
          {renderField("가입일", formattedCreatedAt)}
        </div>

        <div className="grid gap-4 md:grid-cols-2">
          <div>
            <h3 className="text-[1.25rem] font-semibold text-[#000000]">비밀번호 변경</h3>
            <p className="text-[0.875rem] font-normal text-muted">안전한 이용을 위해 주기적으로 비밀번호를 변경해주세요.</p>
            <button
              onClick={() => setIsPasswordModalOpen(true)}
              className="mt-5 w-full rounded-[12px] bg-brand-purple py-3 text-[1rem] font-semibold text-white shadow-elev-card transition hover:bg-brand-purple/80"
            >
              비밀번호 변경하기
            </button>
          </div>

          <div>
            <h3 className="text-[1.25rem] font-semibold text-price-up">회원 탈퇴하기</h3>
            <p className="text-[0.875rem] font-normal text-muted">
              회원 탈퇴 시 모든 데이터가 삭제되며 복구할 수 없습니다.
            </p>
            <button
              onClick={() => setIsDeleteModalOpen(true)}
              className="mt-5 w-full rounded-[12px] bg-price-up py-3 text-[1rem] font-semibold text-white shadow-elev-card transition hover:bg-[#FF6464CC]"
            >
              회원 탈퇴하기
            </button>
          </div>
        </div>
      </div>

      {/* 모달 */}
      <NicknameChangeModal
        isOpen={isNicknameModalOpen}
        onClose={() => setIsNicknameModalOpen(false)}
        currentNickname={user.nickname}
        onSuccess={onUserUpdate}
      />

      <PasswordChangeModal
        isOpen={isPasswordModalOpen}
        onClose={() => setIsPasswordModalOpen(false)}
      />

      <DeleteAccountModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        userEmail={user.email}
        userPhone={user.phone_number}
      />
    </section>
  );
}
