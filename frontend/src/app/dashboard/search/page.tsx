"use client";

import { RAGChatbot } from "@/components/chat/rag-chatbot";

export default function DeepSearchPage() {
  return (
    <div className="h-full flex flex-col">
      {/* Main Chat Interface */}
      <div className="flex-1 min-h-0">
        <RAGChatbot />
      </div>
    </div>
  );
}
