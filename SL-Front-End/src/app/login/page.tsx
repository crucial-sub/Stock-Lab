"use client";

import Image from "next/image";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { Input } from "@/components/common/Input";

const socialLogins = [
  {
    id: "kakao",
    label: "카카오로 로그인",
    display: "talk",
    bg: "#FFE812",
    text: "#000000",
    icon: "/icons/kakao.png",
  },
  {
    id: "naver",
    label: "네이버로 로그인",
    display: "N",
    bg: "#03C75A",
    text: "#ffffff",
    icon: "/icons/naver.png",
  },
  {
    id: "google",
    label: "구글로 로그인",
    display: "G",
    bg: "#ffffff",
    text: "#5F6368",
    border: "#E0E0E0",
    icon: "/icons/google.png",
  },
];

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string }>(
    {},
  );
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const nextErrors: typeof errors = {};

    if (!email.trim()) {
      nextErrors.email = "이메일을 입력해주세요.";
    }

    if (!password.trim()) {
      nextErrors.password = "비밀번호를 입력해주세요.";
    }

    setErrors(nextErrors);

    if (Object.keys(nextErrors).length === 0) {
      setIsSubmitting(true);
      // TODO: 실제 로그인 API 연동
      setTimeout(() => {
        setIsSubmitting(false);
        router.push("/");
      }, 800);
    }
  };

  const emailLabelClass = errors.email
    ? "text-brand-primary"
    : "text-text-strong";
  const passwordLabelClass = errors.password
    ? "text-brand-primary"
    : "text-text-strong";

  return (
    <div className="flex min-h-screen items-center justify-center bg-bg-app px-[2.5rem] py-[3.75rem] text-text-body">
      <div className="w-full max-w-[520px] rounded-[8px] border border-border-subtle bg-white px-[2.5rem] py-[3.75rem] shadow-card">
        <Link
          href="/"
          className="flex items-center gap-1 text-[0.75rem] font-normal text-text-body hover:text-brand-primary"
        >
          <Image
            src="/icons/arrow_left.svg"
            alt="뒤로가기"
            width={20}
            height={20}
          />
          메인으로 돌아가기
        </Link>

        <div className="flex flex-col">
          <Link href="/" className="font-circular self-center my-[40px]">
            <div className="flex h-[4rem] items-start justify-center">
              <span className="text-[2rem] font-sembold text-brand-primary">stock</span>
              <span className="self-end text-[2rem] font-semibold text-accent-primary">lab</span>
            </div>
          </Link>
          <div>
            <h1 className="text-[1.5rem] font-semibold text-text-strong text-left">
              로그인
            </h1>
            <p className="text-text-body text-left">
              서비스 사용을 위해서는 로그인이 필요합니다.
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="mt-8 space-y-6">
          <div>
            <p className={`mb-2 text-sm font-normal ${emailLabelClass}`}>
              이메일을 입력해주세요.
            </p>
            <Input
              type="email"
              autoComplete="email"
              placeholder="이메일"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              className={`h-14 w-full rounded-[8px] border px-5 text-base font-normal text-text-body placeholder:text-text-muted focus:outline-none ${
                errors.email
                  ? "border-brand-primary bg-[#FFF6F6]"
                  : "border-border-default bg-white focus:border-accent-primary"
              }`}
            />
          </div>

          <div>
            <p className={`mb-2 text-sm font-normal ${passwordLabelClass}`}>
              비밀번호를 입력해주세요.
            </p>
            <Input
              type="password"
              autoComplete="current-password"
              placeholder="********"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              className={`h-14 w-full rounded-[8px] border px-5 text-base font-normal text-text-body placeholder:text-text-muted focus:outline-none ${
                errors.password
                  ? "border-brand-primary bg-[#FFF6F6]"
                  : "border-border-default bg-white focus:border-accent-primary"
              }`}
            />
          </div>

          <button
            type="submit"
            disabled={isSubmitting}
            className="h-14 w-full rounded-[8px] border border-brand-primary bg-[#FFD7DB] text-lg font-semibold text-brand-primary transition hover:bg-brand-primary hover:text-white disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "로그인 중..." : "로그인"}
          </button>
        </form>

        <div className="my-8 flex items-center gap-4 text-sm text-text-muted">
          <span className="flex-1 border-t border-border-subtle" />
          혹은
          <span className="flex-1 border-t border-border-subtle" />
        </div>

        <div className="flex justify-center gap-4">
          {socialLogins.map((social) => (
            <button
              key={social.id}
              type="button"
              aria-label={social.label}
              className="rounded-[8px] hover:-translate-y-0.5"
              style={{
                backgroundColor: social.bg,
                color: social.text,
                borderColor: social.border ?? "transparent",
              }}
            >
              <Image
                src={social.icon}
                alt={social.label}
                width={52}
                height={52}
              />
            </button>
          ))}
        </div>

        <p className="mt-10 text-center text-sm text-text-body">
          회원이 아니신가요?{" "}
          <Link
            href="/signup"
            className="font-semibold text-brand-primary hover:underline"
          >
            회원가입하기
          </Link>
        </p>
      </div>
    </div>
  );
}
