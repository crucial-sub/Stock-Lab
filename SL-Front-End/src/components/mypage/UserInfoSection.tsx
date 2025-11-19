"use client";

import { useState } from "react";
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

  return (
    <div className="quant-shell mb-6">
      <h2 className="text-2xl font-bold text-text-body mb-6">기본 정보</h2>

      <div className="space-y-4">
        {/* 이름 */}
        <div className="flex items-center py-3 border-b border-surface">
          <span className="w-32 text-text-muted">이름</span>
          <span className="text-text-body">{user.name}</span>
        </div>

        {/* 닉네임 */}
        <div className="flex items-center py-3 border-b border-surface">
          <span className="w-32 text-text-muted">닉네임</span>
          <span className="flex-1 text-text-body">{user.nickname}</span>
          <button
            onClick={() => setIsNicknameModalOpen(true)}
            className="px-4 py-2 bg-button-primary-soft text-brand rounded-md hover:bg-brand hover:text-base-0 transition-colors"
          >
            닉네임 변경
          </button>
        </div>

        {/* 이메일 */}
        <div className="flex items-center py-3 border-b border-surface">
          <span className="w-32 text-text-muted">이메일</span>
          <span className="text-text-body">{user.email}</span>
        </div>

        {/* 가입일 */}
        <div className="flex items-center py-3 border-b border-surface">
          <span className="w-32 text-text-muted">가입일</span>
          <span className="text-text-body">{formattedCreatedAt}</span>
        </div>

        {/* 버튼 영역 */}
        <div className="flex gap-3 pt-4">
          <button
            onClick={() => setIsPasswordModalOpen(true)}
            className="px-6 py-3 bg-surface text-text-body rounded-lg hover:bg-button-primary-soft hover:text-brand transition-colors"
          >
            비밀번호 변경
          </button>
          <button
            onClick={() => setIsDeleteModalOpen(true)}
            className="px-6 py-3 bg-surface text-price-down rounded-lg hover:bg-price-up transition-colors"
          >
            회원탈퇴
          </button>
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
    </div>
  );
}
