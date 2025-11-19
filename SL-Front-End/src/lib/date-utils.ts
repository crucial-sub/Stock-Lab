/**
 * 날짜 관련 유틸리티 함수 모음
 * - 백테스트 설정에서 사용하는 날짜 형식 변환
 * - YYYYMMDD ↔ YYYY-MM-DD ↔ Date 객체 변환
 */

/**
 * Date 객체를 YYYY-MM-DD 형식 문자열로 변환
 * @param date Date 객체
 * @returns YYYY-MM-DD 형식 문자열
 */
export function formatDateToDisplay(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

/**
 * YYYY-MM-DD 형식 문자열을 YYYYMMDD 형식으로 변환
 * @param dateStr YYYY-MM-DD 형식 문자열
 * @returns YYYYMMDD 형식 문자열 (서버 전송용)
 */
export function formatDateToServer(dateStr: string): string {
  return dateStr.replace(/-/g, "");
}

/**
 * YYYYMMDD 형식 문자열을 YYYY-MM-DD 형식으로 변환
 * @param dateStr YYYYMMDD 형식 문자열
 * @returns YYYY-MM-DD 형식 문자열 (UI 표시용)
 */
export function formatDateFromServer(dateStr: string): string {
  if (dateStr.length !== 8) return dateStr;
  return `${dateStr.slice(0, 4)}-${dateStr.slice(4, 6)}-${dateStr.slice(6, 8)}`;
}

/**
 * YYYYMMDD 형식 문자열을 Date 객체로 변환
 * @param dateStr YYYYMMDD 형식 문자열
 * @returns Date 객체
 */
export function parseServerDate(dateStr: string): Date {
  if (dateStr.length !== 8) return new Date();
  const year = parseInt(dateStr.slice(0, 4), 10);
  const month = parseInt(dateStr.slice(4, 6), 10) - 1; // 월은 0부터 시작
  const day = parseInt(dateStr.slice(6, 8), 10);
  return new Date(year, month, day);
}

/**
 * 현재 날짜를 YYYYMMDD 형식으로 반환
 * @returns YYYYMMDD 형식 문자열
 */
export function getCurrentDate(): string {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

/**
 * 1년 전 날짜를 YYYYMMDD 형식으로 반환
 * @returns YYYYMMDD 형식 문자열
 */
export function getOneYearAgo(): string {
  const now = new Date();
  const oneYearAgo = new Date(now);
  oneYearAgo.setFullYear(now.getFullYear() - 1);
  const year = oneYearAgo.getFullYear();
  const month = String(oneYearAgo.getMonth() + 1).padStart(2, "0");
  const day = String(oneYearAgo.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

/**
 * Date 객체를 YYYYMMDD 형식 문자열로 변환
 * @param date Date 객체
 * @returns YYYYMMDD 형식 문자열
 */
export function formatDateToServerFromDate(date: Date): string {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}${month}${day}`;
}

/**
 * ISO 8601 날짜 문자열을 YY.MM.DD 형식으로 변환
 * @param isoDateStr ISO 8601 형식 날짜 문자열 (예: "2025-12-31T00:00:00.000Z")
 * @returns YY.MM.DD 형식 문자열 (예: "25.12.31")
 */
export function formatDateToCard(isoDateStr: string): string {
  const date = new Date(isoDateStr);
  const year = String(date.getFullYear()).slice(-2); // 뒤 2자리
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}.${month}.${day}`;
}

/**
 * 밀리초를 사람이 읽기 쉬운 시간 형식으로 변환
 * @param milliseconds 밀리초
 * @returns "Xs" 또는 "Xm Ys" 형식 문자열
 *
 * @example
 * formatDuration(5000) // "5초"
 * formatDuration(65000) // "1분 5초"
 * formatDuration(125000) // "2분 5초"
 */
export function formatDuration(milliseconds: number): string {
  const seconds = Math.floor(milliseconds / 1000);

  if (seconds < 60) {
    return `${seconds}초`;
  }

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;

  if (remainingSeconds === 0) {
    return `${minutes}분`;
  }

  return `${minutes}분 ${remainingSeconds}초`;
}
