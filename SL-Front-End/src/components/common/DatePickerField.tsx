"use client";

import { formatDateFromServer, formatDateToServerFromDate, parseServerDate } from "@/lib/date-utils";
import { ko } from "date-fns/locale";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { DayPicker, type Matcher } from "react-day-picker";
import { createPortal } from "react-dom";

interface DatePickerFieldProps {
  value: string;
  onChange: (date: string) => void;
  placeholder?: string;
  disabled?: boolean;
  className?: string;
  minDate?: Date;
  maxDate?: Date;
}

export function DatePickerField({
  value,
  onChange,
  placeholder = "날짜 선택",
  disabled = false,
  className = "",
  minDate,
  maxDate,
}: DatePickerFieldProps) {
  // const triggerRef = useRef<HTMLButtonElement | null>(null);
  const triggerRef = useRef<HTMLInputElement | null>(null);
  const popoverRef = useRef<HTMLDivElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<{ top: number; left: number } | null>(null);

  const selectedDate = value ? parseServerDate(value) : undefined;
  const displayValue = value ? formatDateFromServer(value) : "";

  const disabledMatchers = useMemo(() => {
    const matchers: Matcher[] = [];
    if (minDate) matchers.push({ before: minDate });
    if (maxDate) matchers.push({ after: maxDate });
    return matchers.length > 0 ? matchers : undefined;
  }, [minDate, maxDate]);

  const updatePosition = useCallback(() => {
    if (!triggerRef.current) return;
    const rect = triggerRef.current.getBoundingClientRect();
    setPosition({
      top: rect.bottom + window.scrollY + 8,
      left: rect.left + window.scrollX,
    });
  }, []);

  useEffect(() => {
    if (!isOpen) return;

    updatePosition();

    const handleClickOutside = (event: MouseEvent) => {
      if (
        popoverRef.current?.contains(event.target as Node) ||
        triggerRef.current?.contains(event.target as Node)
      ) {
        return;
      }
      setIsOpen(false);
    };

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") setIsOpen(false);
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [isOpen, updatePosition]);

  return (
    <div className={`relative ${className}`} onClick={() => {
      if (!isOpen) updatePosition();
      setIsOpen((prev) => !prev);
    }}>
      <div className="relative h-[40px] border-b border-[#a0a0a0]">
        <input
          type="text"
          onChange={() => { }}
          ref={triggerRef}
          value={displayValue}
          disabled={disabled}
          style={{
            color: displayValue ? '#e5e5e5' : '#a3a3a3',
          }}
          className="absolute left-0 top-1/2 -translate-y-1/2 bg-transparent border-none outline-none font-['Pretendard:Bold',sans-serif] text-[20px] tracking-[-0.6px] w-[100px]"
        />
        <span className="absolute right-0 top-[20%] text-[#a3a3a3]">📅</span>
      </div>

      {isOpen && position && createPortal(
        <div
          ref={popoverRef}
          className="absolute rounded-xl border border-white/10 bg-[#0a0a0a]/95 backdrop-blur-xl p-5 shadow-2xl"
          style={{
            minWidth: '320px',
            top: `${position.top}px`,
            left: `${position.left}px`,
            zIndex: 99999,
            boxShadow: '0 20px 60px -15px rgba(0, 0, 0, 0.8), 0 0 0 1px rgba(255, 255, 255, 0.05)'
          }}
        >
          <style dangerouslySetInnerHTML={{
            __html: `
              .rdp {
                --rdp-accent-color: #60a5fa !important;
                --rdp-accent-background-color: #60a5fa !important;
                --rdp-background-color: rgba(96, 165, 250, 0.12) !important;
                color: #f5f5f5 !important;
                font-size: 13px;
                font-weight: 400;
                margin: 0;
              }
              .rdp * {
                color: #f5f5f5 !important;
              }
              .rdp-selected {
                background-color: #60a5fa !important;
                color: white !important;
                border-radius: 20%
              }
              .rdp-selected * {
                color: white !important;
              }
              .rdp-month_caption {
                color: #ffffff !important;
                font-weight: 600;
                font-size: 15px;
                margin-bottom: 16px;
                padding-bottom: 12px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.08);
              }
              .rdp-weekday {
                color: #888888 !important;
                font-size: 11px;
                font-weight: 500;
                text-transform: uppercase;
                letter-spacing: 0.5px;
              }
              .rdp-day {
                color: #f5f5f5 !important;
              }
              .rdp-day_button {
                color: #f5f5f5 !important;
                border-radius: 8px;
                width: 36px;
                height: 36px;
                font-size: 13px;
                font-weight: 400;
                transition: all 0.15s ease;
              }
              .rdp-day_button:hover:not(.rdp-day_selected):not(.rdp-day_disabled) {
                background-color: rgba(96, 165, 250, 0.15) !important;
                color: #ffffff !important;
                transform: scale(1.05);
              }
              button[name="day"].rdp-day_button[aria-pressed="true"],
              button[name="day"].rdp-day_button[aria-selected="true"],
              .rdp-day[aria-selected="true"] button,
              .rdp-day_button[aria-pressed="true"],
              .rdp-day_button[data-selected="true"],
              button.rdp-day_button[aria-selected="true"],
              .rdp-day_selected button,
              .rdp-day_selected .rdp-day_button,
              .rdp-day_selected,
              .rdp-selected,
              .rdp-day.rdp-selected button,
              .rdp-day[data-selected="true"] button {
                background: #60a5fa !important;
                background-color: #60a5fa !important;
                background-image: linear-gradient(135deg, #60a5fa 0%, #3b82f6 100%) !important;
                color: #ffffff !important;
                font-weight: 600 !important;
                box-shadow: 0 4px 12px rgba(96, 165, 250, 0.4) !important;
              }
              button[name="day"].rdp-day_button[aria-pressed="true"]:hover,
              .rdp-day_button[aria-pressed="true"]:hover,
              .rdp-day_selected .rdp-day_button:hover {
                background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
                transform: scale(1.05);
              }
              .rdp-day_today:not(.rdp-day_selected) .rdp-day_button {
                border: 1px solid rgba(96, 165, 250, 0.5);
                background-color: rgba(96, 165, 250, 0.08);
              }
              .rdp-day_outside {
                opacity: 0.3;
              }
              .rdp-day_disabled {
                opacity: 0.25;
                cursor: not-allowed;
              }
              .rdp-caption {
                display: block !important;
                margin-bottom: 16px;
              }
              .rdp-caption > * {
                display: inline-flex !important;
                vertical-align: middle !important;
              }
              .rdp-nav {
                display: inline-flex !important;
                gap: 12px;
                width: 100% !important;
                justify-content: space-between !important;
                align-items: center !important;
              }
              .rdp-dropdowns {
                display: inline-flex !important;
                position: absolute !important;
                left: 50% !important;
                top: 6% !important;
                transform: translateX(-50%) !important;
                z-index: 10 !important;
                gap: 8px;
                align-items: center;
              }
              .rdp-button_previous {
                color: #ffffff !important;
                width: 32px;
                height: 32px;
                border-radius: 6px;
                transition: all 0.15s ease;
                display: inline-flex !important;
                align-items: center;
                justify-content: center;
                background: rgba(255, 255, 255, 0.15) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                cursor: pointer;
              }
              .rdp-button_next {
                color: #ffffff !important;
                width: 32px;
                height: 32px;
                border-radius: 6px;
                transition: all 0.15s ease;
                display: inline-flex !important;
                align-items: center;
                justify-content: center;
                background: rgba(255, 255, 255, 0.15) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                cursor: pointer;
              }
              .rdp-button_previous:hover,
              .rdp-button_next:hover {
                background-color: rgba(96, 165, 250, 0.4) !important;
                border-color: rgba(96, 165, 250, 0.6) !important;
                color: #ffffff !important;
              }
              .rdp-button_previous svg,
              .rdp-button_next svg {
                width: 16px;
                height: 16px;
                fill: #ffffff !important;
                stroke: #ffffff !important;
              }
              .rdp-caption_label {
                display: none !important;
              }
              .rdp-dropdown_root {
                display: inline-block !important;
              }
              .rdp-dropdown {
                color: #ffffff !important;
                background-color: rgba(255, 255, 255, 0.1) !important;
                border: 1px solid rgba(255, 255, 255, 0.3) !important;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 14px;
                font-weight: 500;
                cursor: pointer;
                appearance: none;
                -webkit-appearance: none;
                -moz-appearance: none;
              }
              .rdp-dropdown:hover {
                border-color: rgba(96, 165, 250, 0.6) !important;
                background-color: rgba(255, 255, 255, 0.15) !important;
              }
              .rdp-dropdown option {
                background-color: #1a1a1a !important;
                color: #ffffff !important;
              }
              .rdp-dropdown_year,
              .rdp-dropdown_month {
                display: inline-block !important;
              }
              .rdp-month {
                width: 100%;
              }
              .rdp-month_grid {
                width: 100%;
              }
            `
          }} />
          <DayPicker
            mode="single"
            selected={selectedDate}
            onSelect={(date) => {
              if (!date) return;
              onChange(formatDateToServerFromDate(date));
              setIsOpen(false);
            }}
            locale={ko}
            defaultMonth={selectedDate ?? minDate ?? new Date()}
            fromDate={minDate}
            toDate={maxDate}
            disabled={disabledMatchers}
            showOutsideDays
            captionLayout="dropdown"
            startMonth={minDate ?? new Date(2000, 0, 1)}
            endMonth={maxDate ?? new Date(2030, 11, 31)}
          />
        </div>,
        document.body
      )}
    </div>
  );
}
