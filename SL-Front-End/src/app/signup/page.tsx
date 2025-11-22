"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Input } from "@/components/common/Input";
import { authApi } from "@/lib/api/auth";

interface SignUpErrors {
  name?: string;
  nickname?: string;
  phone?: string;
  email?: string;
  password?: string;
  passwordConfirm?: string;
}

export default function SignUpPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    name: "",
    nickname: "",
    phone: "",
    email: "",
    password: "",
    passwordConfirm: "",
  });
  const [errors, setErrors] = useState<SignUpErrors>({});
  const [isEmailVerified, setIsEmailVerified] = useState(false);
  const [isNicknameChecked, setIsNicknameChecked] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleChange =
    (field: keyof typeof form) =>
      (event: React.ChangeEvent<HTMLInputElement>) => {
        const value = event.target.value;
        setForm((prev) => ({ ...prev, [field]: value }));
        if (field === "email") {
          setIsEmailVerified(false);
        }
        if (field === "nickname") {
          setIsNicknameChecked(false);
        }
      };

  const validate = () => {
    const nextErrors: SignUpErrors = {};
    if (!form.name.trim()) nextErrors.name = "이름을 입력해주세요.";
    if (!form.nickname.trim()) {
      nextErrors.nickname = "닉네임을 입력해주세요.";
    } else if (form.nickname.length < 2 || form.nickname.length > 8) {
      nextErrors.nickname = "닉네임은 2~8자로 입력해주세요.";
    } else if (!isNicknameChecked) {
      nextErrors.nickname = "닉네임 중복 확인을 해주세요.";
    }
    if (!form.phone.trim()) nextErrors.phone = "전화번호를 입력해주세요.";
    if (!form.email.trim()) nextErrors.email = "이메일을 입력해주세요.";
    if (!form.password.trim()) nextErrors.password = "비밀번호를 입력해주세요.";
    if (!form.passwordConfirm.trim()) {
      nextErrors.passwordConfirm = "비밀번호를 다시 입력해주세요.";
    } else if (form.password !== form.passwordConfirm) {
      nextErrors.passwordConfirm = "비밀번호가 일치하지 않습니다.";
    }
    setErrors(nextErrors);
    return Object.keys(nextErrors).length === 0;
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!validate()) return;

    setIsSubmitting(true);
    try {
      await authApi.register({
        name: form.name,
        nickname: form.nickname,
        email: form.email,
        phone_number: form.phone,
        password: form.password,
      });
      router.push("/login");
    } catch (error: any) {
      const errorMessage =
        error?.response?.data?.detail || "회원가입에 실패했습니다.";
      setErrors({ email: errorMessage });
    } finally {
      setIsSubmitting(false);
    }
  };

  const labelClass = (hasError?: string) =>
    hasError ? "text-brand-primary" : "text-text-strong";

  const inputClass = (hasError?: string) =>
    `py-[0.75rem] w-full rounded-[12px] px-4 font-normal text-body placeholder:text-muted focus:outline-none shadow-elev-card-soft ${hasError
      ? "bg-[#1822340D] border-[0.5px] border-[#FF6464]"
      : "bg-[#1822340D] border-[0.5px] border-[#18223433] focus:border-brand-purple"
    }`;

  const handleEmailVerify = () => {
    if (!form.email.trim()) {
      setErrors((prev) => ({ ...prev, email: "이메일을 입력해주세요." }));
      setIsEmailVerified(false);
      return;
    }
    setErrors((prev) => ({ ...prev, email: undefined }));
    setIsEmailVerified(true);
  };

  const handleNicknameCheck = async () => {
    if (!form.nickname.trim()) {
      setErrors((prev) => ({ ...prev, nickname: "닉네임을 입력해주세요." }));
      setIsNicknameChecked(false);
      return;
    }
    if (form.nickname.length < 2 || form.nickname.length > 8) {
      setErrors((prev) => ({ ...prev, nickname: "닉네임은 2~8자로 입력해주세요." }));
      setIsNicknameChecked(false);
      return;
    }
    try {
      const result = await authApi.checkNickname(form.nickname);
      if (result.available) {
        setErrors((prev) => ({ ...prev, nickname: undefined }));
        setIsNicknameChecked(true);
      } else {
        setErrors((prev) => ({ ...prev, nickname: "이미 사용 중인 닉네임입니다." }));
        setIsNicknameChecked(false);
      }
    } catch (error) {
      setErrors((prev) => ({ ...prev, nickname: "닉네임 확인에 실패했습니다." }));
      setIsNicknameChecked(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center px-[2.5rem] py-[3.75rem] text-body">
      <div className="w-full max-w-[520px] px-[2.5rem] py-[3.75rem]">
        <Link
          href="/login"
          className="flex items-center gap-1 text-[0.75rem] font-normal text-muted"
        >
          <Image
            src="/icons/arrow_left.svg"
            alt="뒤로가기"
            width={20}
            height={20}
          />
          로그인으로 돌아가기
        </Link>

        <div>
          <h1 className="mt-[1.75rem] text-[1.5rem] font-semibold text-body text-left">
            회원가입
          </h1>
          <p className="text-muted text-left">
            원활한 서비스 사용을 위해 회원가입을 진행해주세요.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="mt-10 space-y-6">
          <div>
            <p className={`mb-1 text-[0.875rem] font-normal ${labelClass(errors.name)}`}>
              이름을 입력해주세요.
            </p>
            <Input
              type="text"
              placeholder="이름"
              value={form.name}
              onChange={handleChange("name")}
              className={inputClass(errors.name)}
            />
          </div>
          <div>
            <p
              className={`mb-1 text-[0.875rem] font-normal ${labelClass(errors.nickname)}`}
            >
              닉네임을 입력해주세요.
            </p>
            <div className="flex gap-3">
              <Input
                type="text"
                placeholder="닉네임 (2~8자)"
                value={form.nickname}
                onChange={handleChange("nickname")}
                maxLength={8}
                className={inputClass(errors.nickname)}
              />
              <button
                type="button"
                onClick={handleNicknameCheck}
                className={`px-5 rounded-[12px] bg-brand-purple text-[0.875rem] font-semibold text-white hover:opacity-80 disabled:opacity-60 whitespace-nowrap`}
              >
                중복 확인
              </button>
            </div>
            {isNicknameChecked && !errors.nickname && (
              <p className="mt-2 text-sm font-semibold text-brand-primary">
                사용 가능한 닉네임입니다.
              </p>
            )}
            {errors.nickname && (
              <p className="mt-2 text-sm font-semibold text-brand-primary">
                {errors.nickname}
              </p>
            )}
          </div>
          <div>
            <p
              className={`mb-1 text-[0.875rem] font-normal ${labelClass(errors.phone)}`}
            >
              전화번호를 입력해주세요.
            </p>
            <Input
              type="tel"
              autoComplete="tel"
              placeholder="01012345678 (- 없이)"
              value={form.phone}
              onChange={handleChange("phone")}
              className={inputClass(errors.phone)}
            />
          </div>
          <div>
            <p
              className={`mb-1 text-[0.875rem] font-normal ${labelClass(errors.email)}`}
            >
              이메일을 입력해주세요.
            </p>
            <div className="flex gap-3">
              <Input
                type="email"
                autoComplete="email"
                placeholder="example@stocklab.com"
                value={form.email}
                onChange={handleChange("email")}
                className={inputClass(errors.email)}
              />
              <button
                type="button"
                onClick={handleEmailVerify}
                className={`px-5 rounded-[12px] bg-brand-purple text-[0.875rem] font-semibold text-white hover:opacity-80 disabled:opacity-60 whitespace-nowrap`}              >
                인증하기
              </button>
            </div>
            {isEmailVerified && !errors.email && (
              <p className="mt-2 text-sm font-semibold text-brand-primary">
                인증되었습니다.
              </p>
            )}
          </div>
          <div>
            <p
              className={`mb-1 text-[0.875rem] font-normal ${labelClass(errors.password)}`}
            >
              비밀번호를 입력해주세요.
            </p>
            <Input
              type="password"
              autoComplete="new-password"
              placeholder="********"
              value={form.password}
              onChange={handleChange("password")}
              className={inputClass(errors.password)}
            />
          </div>
          <div>
            <p
              className={`mb-1 text-[0.875rem] font-normal ${labelClass(
                errors.passwordConfirm,
              )}`}
            >
              비밀번호를 다시 입력해주세요.
            </p>
            <Input
              type="password"
              autoComplete="new-password"
              placeholder="********"
              value={form.passwordConfirm}
              onChange={handleChange("passwordConfirm")}
              className={`${inputClass(errors.passwordConfirm)} mb-5`}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="py-2.5 w-full rounded-[12px] bg-brand-purple text-[1.125rem] font-semibold text-white transition hover:opacity-80 disabled:opacity-60"          >
            {isSubmitting ? "가입 중..." : "회원가입"}
          </button>
        </form>

        <p className={`mt-10 text-center text-sm text-muted `}>
          이미 계정이 있으신가요?{" "}
          <Link
            href="/login"
            className="font-semibold text-brand-purple hover:underline"
          >
            로그인하기
          </Link>
        </p>
      </div>
    </div>
  );
}
