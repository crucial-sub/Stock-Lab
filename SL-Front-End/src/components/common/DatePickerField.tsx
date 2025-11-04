"use client";

import { formatDateToServerFromDate, parseServerDate } from "@/lib/date-utils";
import { format } from "date-fns";
import { ko } from "date-fns/locale";
import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { DayPicker, type Matcher } from "react-day-picker";
import "react-day-picker/dist/style.css";
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

interface PopoverPosition {
  top: number;
  left: number;
  width: number;
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
  const triggerRef = useRef<HTMLButtonElement | null>(null);
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<PopoverPosition | null>(null);

  const selectedDate = value ? parseServerDate(value) : undefined;
  const currentYear = selectedDate?.getFullYear() ?? new Date().getFullYear();

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
      width: rect.width,
    });
  }, []);

  useEffect(() => {
    if (!isOpen) return;
    updatePosition();

    const handle = () => updatePosition();
    window.addEventListener("resize", handle);
    window.addEventListener("scroll", handle, true);
    return () => {
      window.removeEventListener("resize", handle);
      window.removeEventListener("scroll", handle, true);
    };
  }, [isOpen, updatePosition]);

  const handleSelect = (date: Date | undefined) => {
    if (!date) return;
    onChange(formatDateToServerFromDate(date));
    setIsOpen(false);
  };

  const displayValue = selectedDate ? format(selectedDate, "yyyy-MM-dd") : "";

  return (
    <div className={`relative ${className}`}>
      <button
        ref={triggerRef}
        type="button"
        disabled={disabled}
        onClick={() => !disabled && setIsOpen((prev) => !prev)}
        className="quant-input flex w-full items-center justify-between text-left"
      >
        <span className={displayValue ? "text-text-primary" : "text-text-secondary"}>
          {displayValue || placeholder}
        </span>
        <span className="text-text-secondary">📅</span>
      </button>

      {isOpen && position &&
        createPortal(
          <>
            <div
              className="fixed inset-0 z-[999]"
              onClick={() => setIsOpen(false)}
            />
            <div
              className="fixed z-[1000] rounded-xl border border-border-subtle bg-bg-surface/95 p-4 shadow-[0_18px_40px_rgba(0,0,0,0.2)] backdrop-blur-xl"
              style={{ top: position.top, left: position.left, minWidth: Math.max(280, position.width) }}
            >
              <DayPicker
                mode="single"
                selected={selectedDate}
                onSelect={handleSelect}
                locale={ko}
                showOutsideDays
                captionLayout="dropdown"
                fromYear={minDate?.getFullYear() ?? currentYear - 20}
                toYear={maxDate?.getFullYear() ?? currentYear + 20}
                fromDate={minDate}
                toDate={maxDate}
                disabled={disabledMatchers}
                className="text-text-primary"
                classNames={{
                  months: "flex flex-col space-y-4",
                  month: "space-y-4",
                  caption: "flex items-center justify-between gap-2 text-sm font-medium",
                  caption_label: "capitalize",
                  caption_dropdowns: "flex items-center gap-2",
                  table: "w-full border-collapse",
                  head_row:
                    "grid grid-cols-7 text-center text-[0.7rem] font-medium uppercase tracking-tight text-text-tertiary",
                  head_cell: "py-2",
                  row: "grid grid-cols-7 text-center text-sm",
                  cell: "relative h-10 w-10 place-items-center justify-center",
                  day: "mx-auto flex h-9 w-9 items-center justify-center rounded-full text-sm font-medium text-text-primary transition hover:bg-brand/15 hover:text-brand",
                  day_selected:
                    "bg-brand text-white hover:bg-brand hover:text-white focus:bg-brand focus:text-white",
                  day_today: "border border-brand/40 text-brand",
                  day_outside: "text-text-tertiary opacity-40",
                  day_disabled: "text-text-tertiary opacity-30",
                  day_range_middle: "bg-brand/10 text-text-primary",
                  day_hidden: "invisible",
                }}
              />
            </div>
          </>,
          document.body,
        )}
    </div>
  );
}
