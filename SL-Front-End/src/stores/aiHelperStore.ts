import { create } from "zustand";

interface Message {
  role: "user" | "assistant";
  content: string;
  backtestConditionsBuy?: any[];
  backtestConditionsSell?: any[];
  appliedBuy?: boolean;
  appliedSell?: boolean;
  backtestConfig?: any;
}

interface AIHelperState {
  messages: Message[];
  sessionId: string;
  isLoading: boolean;
  addMessage: (msg: Message) => void;
  updateMessage: (index: number, updates: Partial<Message>) => void;
  setSessionId: (id: string) => void;
  setIsLoading: (loading: boolean) => void;
  reset: () => void;
}

export const useAIHelperStore = create<AIHelperState>((set) => ({
  messages: [],
  sessionId: "",
  isLoading: false,
  addMessage: (msg) =>
    set((state) => ({
      messages: [...state.messages, msg],
    })),
  updateMessage: (index, updates) =>
    set((state) => ({
      messages: state.messages.map((m, i) =>
        i === index ? { ...m, ...updates } : m
      ),
    })),
  setSessionId: (id) => set({ sessionId: id }),
  setIsLoading: (loading) => set({ isLoading: loading }),
  reset: () => set({ messages: [], sessionId: "", isLoading: false }),
}));
