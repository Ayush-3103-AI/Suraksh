"use client";

import { useState, useRef, useEffect, useCallback } from "react";
import {
  Send,
  Loader2,
  Bot,
  User,
  FileText,
  Sparkles,
  ChevronDown,
  RefreshCw,
  Trash2,
  Copy,
  Check,
  AlertCircle,
  BookOpen,
} from "lucide-react";
import {
  deepSearch,
  ChatMessage,
  generateMessageId,
  Citation,
  SourceSummary,
} from "@/lib/api/deepsearch";
import { cn } from "@/lib/utils";

// Markdown-like formatting for the response
function formatAnswer(text: string): JSX.Element {
  // Split by code blocks first
  const parts = text.split(/(```[\s\S]*?```)/g);

  return (
    <>
      {parts.map((part, i) => {
        if (part.startsWith("```")) {
          // Code block
          const codeContent = part.replace(/```\w*\n?/g, "").replace(/```$/, "");
          return (
            <pre
              key={i}
              className="my-3 p-4 bg-space-100 rounded-lg border border-cyan-500/20 overflow-x-auto"
            >
              <code className="text-sm text-cyan-300 font-mono">
                {codeContent}
              </code>
            </pre>
          );
        }

        // Process inline formatting
        return (
          <span key={i}>
            {part.split("\n").map((line, j) => {
              // Headers
              if (line.startsWith("### ")) {
                return (
                  <h3 key={j} className="text-lg font-semibold text-cyan-400 mt-4 mb-2">
                    {line.replace("### ", "")}
                  </h3>
                );
              }
              if (line.startsWith("## ")) {
                return (
                  <h2 key={j} className="text-xl font-semibold text-cyan-300 mt-4 mb-2">
                    {line.replace("## ", "")}
                  </h2>
                );
              }
              if (line.startsWith("# ")) {
                return (
                  <h1 key={j} className="text-2xl font-bold text-cyan-200 mt-4 mb-2">
                    {line.replace("# ", "")}
                  </h1>
                );
              }

              // Blockquote
              if (line.startsWith("> ")) {
                return (
                  <blockquote
                    key={j}
                    className="pl-4 border-l-2 border-cyber-purple/50 text-slate-300 italic my-2"
                  >
                    {line.replace("> ", "")}
                  </blockquote>
                );
              }

              // Bold text
              let formattedLine = line.replace(
                /\*\*(.*?)\*\*/g,
                '<strong class="text-white font-semibold">$1</strong>'
              );

              // Source citations [Source: filename, Page X]
              formattedLine = formattedLine.replace(
                /\[Source: ([^\]]+)\]/g,
                '<span class="inline-flex items-center gap-1 px-2 py-0.5 bg-cyber-purple/20 border border-cyber-purple/30 rounded text-cyber-purple text-xs font-mono">📄 $1</span>'
              );

              // Bullet points
              if (line.trim().startsWith("- ") || line.trim().startsWith("• ")) {
                return (
                  <div key={j} className="flex items-start gap-2 my-1 ml-2">
                    <span className="text-cyan-500 mt-1">•</span>
                    <span
                      className="text-slate-200"
                      dangerouslySetInnerHTML={{
                        __html: formattedLine.replace(/^[-•]\s*/, ""),
                      }}
                    />
                  </div>
                );
              }

              // Numbered lists
              const numberedMatch = line.trim().match(/^(\d+)\.\s(.+)/);
              if (numberedMatch) {
                return (
                  <div key={j} className="flex items-start gap-2 my-1 ml-2">
                    <span className="text-cyan-500 font-mono text-sm min-w-[1.5rem]">
                      {numberedMatch[1]}.
                    </span>
                    <span
                      className="text-slate-200"
                      dangerouslySetInnerHTML={{ __html: numberedMatch[2] }}
                    />
                  </div>
                );
              }

              // Regular paragraph
              if (line.trim()) {
                return (
                  <p
                    key={j}
                    className="my-2 text-slate-200 leading-relaxed"
                    dangerouslySetInnerHTML={{ __html: formattedLine }}
                  />
                );
              }

              return <br key={j} />;
            })}
          </span>
        );
      })}
    </>
  );
}

// Citation Badge Component
function CitationBadge({ citation }: { citation: Citation }) {
  return (
    <div className="inline-flex items-center gap-1.5 px-2 py-1 bg-cyber-purple/10 border border-cyber-purple/30 rounded-lg text-xs">
      <FileText className="w-3 h-3 text-cyber-purple" />
      <span className="text-cyber-purple font-medium">{citation.filename}</span>
      {citation.page && (
        <span className="text-slate-400">Page {citation.page}</span>
      )}
      {citation.confidence && (
        <span className="text-emerald-400 font-mono">
          {(citation.confidence * 100).toFixed(0)}%
        </span>
      )}
    </div>
  );
}

// Source Summary Component
function SourcesSummary({ sources }: { sources: SourceSummary[] }) {
  const [expanded, setExpanded] = useState(false);

  if (!sources || sources.length === 0) return null;

  return (
    <div className="mt-4 pt-4 border-t border-glass-border">
      <button
        onClick={() => setExpanded(!expanded)}
        className="flex items-center gap-2 text-sm text-slate-400 hover:text-cyan-400 transition-colors"
      >
        <BookOpen className="w-4 h-4" />
        <span>{sources.length} source{sources.length !== 1 ? "s" : ""} referenced</span>
        <ChevronDown
          className={cn(
            "w-4 h-4 transition-transform",
            expanded && "rotate-180"
          )}
        />
      </button>
      {expanded && (
        <div className="mt-3 space-y-2">
          {sources.map((source, idx) => (
            <div
              key={idx}
              className="flex items-center justify-between px-3 py-2 bg-space-100 rounded-lg border border-glass-border"
            >
              <div className="flex items-center gap-2">
                <FileText className="w-4 h-4 text-cyber-cyan" />
                <span className="text-sm text-slate-200">{source.filename}</span>
              </div>
              <div className="flex items-center gap-3">
                {source.pages.length > 0 && (
                  <span className="text-xs text-slate-400">
                    Pages: {source.pages.join(", ")}
                  </span>
                )}
                {source.confidence && (
                  <span className="text-xs text-emerald-400 font-mono">
                    {(source.confidence * 100).toFixed(0)}% confidence
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Message Component
function MessageBubble({
  message,
  onRetry,
  onCopy,
}: {
  message: ChatMessage;
  onRetry?: () => void;
  onCopy?: () => void;
}) {
  const [copied, setCopied] = useState(false);
  const isUser = message.role === "user";

  const handleCopy = () => {
    navigator.clipboard.writeText(message.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onCopy?.();
  };

  return (
    <div
      className={cn(
        "flex gap-3 group animate-in fade-in slide-in-from-bottom-2 duration-300",
        isUser ? "flex-row-reverse" : ""
      )}
    >
      {/* Avatar */}
      <div
        className={cn(
          "flex-shrink-0 w-9 h-9 rounded-xl flex items-center justify-center border",
          isUser
            ? "bg-cyber-cyan/20 border-cyber-cyan/40"
            : "bg-cyber-purple/20 border-cyber-purple/40"
        )}
      >
        {isUser ? (
          <User className="w-5 h-5 text-cyber-cyan" />
        ) : (
          <Bot className="w-5 h-5 text-cyber-purple" />
        )}
      </div>

      {/* Message Content */}
      <div className={cn("flex-1 max-w-[85%]", isUser ? "flex justify-end" : "")}>
        <div
          className={cn(
            "rounded-2xl px-4 py-3 relative",
            isUser
              ? "bg-cyber-cyan/10 border border-cyber-cyan/30 rounded-tr-sm"
              : "bg-glass-medium border border-glass-border rounded-tl-sm"
          )}
        >
          {/* Loading State */}
          {message.isLoading && (
            <div className="flex items-center gap-3 py-2">
              <div className="flex gap-1">
                <span className="w-2 h-2 bg-cyber-purple rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                <span className="w-2 h-2 bg-cyber-purple rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                <span className="w-2 h-2 bg-cyber-purple rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
              </div>
              <span className="text-slate-400 text-sm">Searching knowledge base...</span>
            </div>
          )}

          {/* Error State */}
          {message.error && (
            <div className="flex items-start gap-2 text-threat-critical">
              <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-medium">Error</p>
                <p className="text-sm text-slate-400 mt-1">{message.error}</p>
                {onRetry && (
                  <button
                    onClick={onRetry}
                    className="mt-2 flex items-center gap-1 text-sm text-cyber-cyan hover:text-cyber-cyan/80 transition-colors"
                  >
                    <RefreshCw className="w-4 h-4" />
                    Retry
                  </button>
                )}
              </div>
            </div>
          )}

          {/* Message Content */}
          {!message.isLoading && !message.error && (
            <>
              {isUser ? (
                <p className="text-slate-100">{message.content}</p>
              ) : (
                <div className="prose prose-invert max-w-none">
                  {formatAnswer(message.content)}
                </div>
              )}

              {/* Citations */}
              {message.citations && message.citations.length > 0 && (
                <div className="flex flex-wrap gap-2 mt-3 pt-3 border-t border-glass-border">
                  {message.citations.slice(0, 5).map((citation, idx) => (
                    <CitationBadge key={idx} citation={citation} />
                  ))}
                  {message.citations.length > 5 && (
                    <span className="text-xs text-slate-500">
                      +{message.citations.length - 5} more
                    </span>
                  )}
                </div>
              )}

              {/* Sources Summary */}
              {message.sources && <SourcesSummary sources={message.sources} />}
            </>
          )}

          {/* Actions */}
          {!isUser && !message.isLoading && !message.error && (
            <div className="absolute -bottom-6 left-0 opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-2">
              <button
                onClick={handleCopy}
                className="p-1 text-slate-500 hover:text-slate-300 transition-colors"
                title="Copy response"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-emerald-400" />
                ) : (
                  <Copy className="w-4 h-4" />
                )}
              </button>
            </div>
          )}
        </div>

        {/* Timestamp */}
        <p
          className={cn(
            "text-xs text-slate-600 mt-1",
            isUser ? "text-right mr-1" : "ml-1"
          )}
        >
          {message.timestamp.toLocaleTimeString([], {
            hour: "2-digit",
            minute: "2-digit",
          })}
        </p>
      </div>
    </div>
  );
}

// Main Chatbot Component
export function RAGChatbot() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Auto-scroll to bottom
  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = "auto";
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`;
    }
  }, [input]);

  // Demo messages for investigation scenario
  const getDemoMessages = (): ChatMessage[] => {
    const baseTime = new Date();
    baseTime.setHours(9, 0, 0, 0); // Start at 9:00 AM
    
    return [
      {
        id: generateMessageId(),
        role: "user",
        content: "What are the main suspects in CASE-2024-042 and what evidence links them to the crime?",
        timestamp: new Date(baseTime.getTime() + 0 * 60000),
      },
      {
        id: generateMessageId(),
        role: "assistant",
        content: `Based on the investigation documents, **CASE-2024-042** involves **four primary suspects**:

**Primary Suspects:**
1. **Rajesh Kumar** - Identified in [Source: FIR-2024-RC-001, Page 3] as the alleged ringleader. Multiple witness statements [Source: Witness Statements, Page 12] place him at the crime scene.

2. **Vikram Singh** - Connected through financial transaction records [Source: Financial Transaction Records, Page 8]. His vehicle (MH-12-AB-1234) was spotted at the location [Source: CCTV Footage Analysis, Page 5].

3. **Amit Sharma** - Linked via digital evidence including phone records [Source: Digital Evidence Report, Page 15] showing communication with other suspects on the day of the incident.

4. **Deepak Patel** - Identified through fingerprint evidence [Source: Forensic Analysis Report, Page 22] found at the warehouse location.

**Key Evidence Connections:**
- **Fingerprint Evidence** links Deepak Patel to the crime scene [Source: Forensic Analysis Report, Page 22]
- **DNA Sample** recovered from evidence item #7 matches Vikram Singh [Source: Medical Examiner Report, Page 18]
- **Digital Evidence** shows coordinated communication between all four suspects [Source: Digital Evidence Report, Pages 15-17]
- **Vehicle Registration** data confirms presence of suspect vehicles at multiple crime locations [Source: Case File: Initial Report, Page 9]`,
        timestamp: new Date(baseTime.getTime() + 2 * 60000),
        citations: [
          { filename: "FIR-2024-RC-001", page: 3, confidence: 0.95 },
          { filename: "Witness Statements", page: 12, confidence: 0.88 },
          { filename: "Financial Transaction Records", page: 8, confidence: 0.92 },
          { filename: "CCTV Footage Analysis", page: 5, confidence: 0.90 },
          { filename: "Digital Evidence Report", page: 15, confidence: 0.94 },
          { filename: "Forensic Analysis Report", page: 22, confidence: 0.96 },
          { filename: "Medical Examiner Report", page: 18, confidence: 0.91 },
          { filename: "Case File: Initial Report", page: 9, confidence: 0.89 },
        ],
        sources: [
          { filename: "FIR-2024-RC-001", pages: [3, 4], confidence: 0.95 },
          { filename: "Witness Statements", pages: [12, 13], confidence: 0.88 },
          { filename: "Forensic Analysis Report", pages: [22, 23], confidence: 0.96 },
          { filename: "Digital Evidence Report", pages: [15, 16, 17], confidence: 0.94 },
        ],
      },
      {
        id: generateMessageId(),
        role: "user",
        content: "Show me the timeline of events for this case based on all available documents",
        timestamp: new Date(baseTime.getTime() + 5 * 60000),
      },
      {
        id: generateMessageId(),
        role: "assistant",
        content: `**Timeline of Events - CASE-2024-042:**

**Day 1 - Incident Date (March 15, 2024):**
- **14:30** - Initial incident reported at Warehouse Complex, Sector 12 [Source: FIR-2024-RC-001, Page 1]
- **14:45** - First responding officers arrive at scene [Source: Case File: Initial Report, Page 2]
- **15:20** - Evidence collection begins; fingerprint evidence recovered [Source: Forensic Analysis Report, Page 4]
- **16:00** - CCTV footage secured from nearby locations [Source: CCTV Footage Analysis, Page 1]
- **18:30** - Suspect vehicle (MH-12-AB-1234) identified from traffic cameras [Source: Case File: Initial Report, Page 6]

**Day 2 - Investigation (March 16, 2024):**
- **09:00** - Digital evidence analysis begins; phone records obtained [Source: Digital Evidence Report, Page 2]
- **11:30** - Financial transaction records reveal suspicious activity [Source: Financial Transaction Records, Page 3]
- **14:00** - DNA sample analysis completed; match identified [Source: Medical Examiner Report, Page 8]
- **16:45** - Witness statements collected from three key witnesses [Source: Witness Statements, Page 1]

**Day 3 - Follow-up (March 17, 2024):**
- **10:00** - Additional evidence recovered from Residential Area, Block C [Source: Case File: Initial Report, Page 11]
- **13:20** - Ballistics report confirms weapon type [Source: Ballistics Report, Page 5]
- **15:00** - Court documents filed for search warrants [Source: Court Documents, Page 2]

**Key Locations:**
1. Warehouse Complex, Sector 12 (Primary crime scene) [Source: FIR-2024-RC-001, Page 2]
2. Residential Area, Block C (Secondary location) [Source: Case File: Initial Report, Page 11]
3. Highway Checkpoint KM-45 (Vehicle sighting) [Source: CCTV Footage Analysis, Page 7]`,
        timestamp: new Date(baseTime.getTime() + 7 * 60000),
        citations: [
          { filename: "FIR-2024-RC-001", page: 1, confidence: 0.97 },
          { filename: "Case File: Initial Report", page: 2, confidence: 0.94 },
          { filename: "Forensic Analysis Report", page: 4, confidence: 0.93 },
          { filename: "CCTV Footage Analysis", page: 1, confidence: 0.91 },
          { filename: "Digital Evidence Report", page: 2, confidence: 0.95 },
          { filename: "Financial Transaction Records", page: 3, confidence: 0.92 },
          { filename: "Medical Examiner Report", page: 8, confidence: 0.96 },
          { filename: "Witness Statements", page: 1, confidence: 0.89 },
          { filename: "Ballistics Report", page: 5, confidence: 0.94 },
          { filename: "Court Documents", page: 2, confidence: 0.90 },
        ],
        sources: [
          { filename: "FIR-2024-RC-001", pages: [1, 2], confidence: 0.97 },
          { filename: "Case File: Initial Report", pages: [2, 6, 11], confidence: 0.94 },
          { filename: "Forensic Analysis Report", pages: [4, 5], confidence: 0.93 },
          { filename: "CCTV Footage Analysis", pages: [1, 7], confidence: 0.91 },
        ],
      },
      {
        id: generateMessageId(),
        role: "user",
        content: "What connections exist between the suspects and the locations mentioned in the case?",
        timestamp: new Date(baseTime.getTime() + 10 * 60000),
      },
      {
        id: generateMessageId(),
        role: "assistant",
        content: `**Suspect-Location Connections:**

**Rajesh Kumar:**
- **Warehouse Complex, Sector 12** - Primary crime scene; witness statements confirm his presence [Source: Witness Statements, Page 14]
- **Residential Area, Block C** - Known residence; search warrant executed [Source: Case File: Initial Report, Page 13]
- **Highway Checkpoint KM-45** - Vehicle spotted on day of incident [Source: CCTV Footage Analysis, Page 9]

**Vikram Singh:**
- **Warehouse Complex, Sector 12** - Vehicle (MH-12-AB-1234) captured on CCTV entering at 14:25 [Source: CCTV Footage Analysis, Page 6]
- **Abandoned Factory, Industrial Zone** - Financial records show transactions linked to this location [Source: Financial Transaction Records, Page 12]

**Amit Sharma:**
- **Residential Area, Block C** - Phone records show location data placing him here during incident [Source: Digital Evidence Report, Page 19]
- **Warehouse Complex, Sector 12** - Digital evidence trail confirms communication from this location [Source: Digital Evidence Report, Page 20]

**Deepak Patel:**
- **Warehouse Complex, Sector 12** - Fingerprint evidence directly links him to this location [Source: Forensic Analysis Report, Page 25]
- **Highway Checkpoint KM-45** - Vehicle registration (DL-08-CD-5678) linked to him spotted here [Source: Case File: Initial Report, Page 15]

**Cross-Connections:**
- All four suspects have connections to **Warehouse Complex, Sector 12** [Source: Case File: Initial Report, Page 16]
- **Rajesh Kumar** and **Vikram Singh** both linked to **Highway Checkpoint KM-45** on the same day [Source: CCTV Footage Analysis, Page 10]`,
        timestamp: new Date(baseTime.getTime() + 12 * 60000),
        citations: [
          { filename: "Witness Statements", page: 14, confidence: 0.92 },
          { filename: "Case File: Initial Report", page: 13, confidence: 0.94 },
          { filename: "CCTV Footage Analysis", page: 9, confidence: 0.91 },
          { filename: "CCTV Footage Analysis", page: 6, confidence: 0.95 },
          { filename: "Financial Transaction Records", page: 12, confidence: 0.93 },
          { filename: "Digital Evidence Report", page: 19, confidence: 0.96 },
          { filename: "Digital Evidence Report", page: 20, confidence: 0.94 },
          { filename: "Forensic Analysis Report", page: 25, confidence: 0.97 },
          { filename: "Case File: Initial Report", page: 15, confidence: 0.92 },
          { filename: "Case File: Initial Report", page: 16, confidence: 0.95 },
          { filename: "CCTV Footage Analysis", page: 10, confidence: 0.93 },
        ],
        sources: [
          { filename: "Witness Statements", pages: [14, 15], confidence: 0.92 },
          { filename: "CCTV Footage Analysis", pages: [6, 9, 10], confidence: 0.93 },
          { filename: "Case File: Initial Report", pages: [13, 15, 16], confidence: 0.94 },
          { filename: "Digital Evidence Report", pages: [19, 20], confidence: 0.95 },
        ],
      },
      {
        id: generateMessageId(),
        role: "user",
        content: "What evidence do we have that can be used in court? List the strongest pieces of evidence.",
        timestamp: new Date(baseTime.getTime() + 15 * 60000),
      },
      {
        id: generateMessageId(),
        role: "assistant",
        content: `**Court-Ready Evidence for CASE-2024-042:**

**1. Forensic Evidence (Strongest):**
- **Fingerprint Evidence** - Direct match to Deepak Patel at crime scene [Source: Forensic Analysis Report, Page 22]. Chain of custody documented [Source: Case File: Initial Report, Page 18]
- **DNA Sample** - Recovered from evidence item #7, matches Vikram Singh with 99.8% confidence [Source: Medical Examiner Report, Page 18]

**2. Digital Evidence:**
- **Phone Records** - Complete call logs showing coordination between all suspects [Source: Digital Evidence Report, Page 15]. Legally obtained through court order [Source: Court Documents, Page 4]
- **CCTV Footage** - High-resolution video showing suspect vehicles and individuals at crime scene [Source: CCTV Footage Analysis, Page 5]. Timestamped and authenticated [Source: CCTV Footage Analysis, Page 3]

**3. Financial Evidence:**
- **Transaction Records** - Bank statements showing suspicious money transfers between suspects [Source: Financial Transaction Records, Page 8]. Subpoenaed through proper legal channels [Source: Court Documents, Page 6]

**4. Physical Evidence:**
- **Weapon: Pistol (Serial: XYZ-123)** - Recovered and linked to crime through ballistics [Source: Ballistics Report, Page 7]
- **Vehicle Registration Data** - Confirms suspect vehicle presence at multiple locations [Source: Case File: Initial Report, Page 9]

**5. Witness Testimony:**
- **Three credible witnesses** with detailed statements [Source: Witness Statements, Pages 1-15]. All statements recorded and signed [Source: Witness Statements, Page 16]

**Evidence Strength Ranking:**
1. DNA Sample (99.8% match) - **Strongest**
2. Fingerprint Evidence (Direct match) - **Very Strong**
3. CCTV Footage (Visual confirmation) - **Strong**
4. Phone Records (Communication trail) - **Strong**
5. Financial Records (Transaction evidence) - **Moderate-Strong**`,
        timestamp: new Date(baseTime.getTime() + 17 * 60000),
        citations: [
          { filename: "Forensic Analysis Report", page: 22, confidence: 0.98 },
          { filename: "Case File: Initial Report", page: 18, confidence: 0.95 },
          { filename: "Medical Examiner Report", page: 18, confidence: 0.99 },
          { filename: "Digital Evidence Report", page: 15, confidence: 0.96 },
          { filename: "Court Documents", page: 4, confidence: 0.94 },
          { filename: "CCTV Footage Analysis", page: 5, confidence: 0.97 },
          { filename: "CCTV Footage Analysis", page: 3, confidence: 0.95 },
          { filename: "Financial Transaction Records", page: 8, confidence: 0.93 },
          { filename: "Court Documents", page: 6, confidence: 0.92 },
          { filename: "Ballistics Report", page: 7, confidence: 0.96 },
          { filename: "Case File: Initial Report", page: 9, confidence: 0.94 },
          { filename: "Witness Statements", pages: [1, 15, 16], confidence: 0.91 },
        ],
        sources: [
          { filename: "Forensic Analysis Report", pages: [22, 23], confidence: 0.98 },
          { filename: "Medical Examiner Report", pages: [18, 19], confidence: 0.99 },
          { filename: "CCTV Footage Analysis", pages: [3, 5], confidence: 0.96 },
          { filename: "Digital Evidence Report", pages: [15, 16], confidence: 0.96 },
          { filename: "Witness Statements", pages: [1, 15, 16], confidence: 0.91 },
        ],
      },
    ];
  };

  // Load messages from localStorage or show demo
  useEffect(() => {
    const saved = localStorage.getItem("rag-chat-history");
    const hasSeenDemo = localStorage.getItem("rag-chat-demo-seen");
    
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        const restored = parsed.map((msg: any) => ({
          ...msg,
          timestamp: new Date(msg.timestamp),
        }));
        setMessages(restored);
      } catch (e) {
        console.error("Failed to load chat history:", e);
      }
    } else if (!hasSeenDemo) {
      // Show demo messages on first visit
      const demoMessages = getDemoMessages();
      setMessages(demoMessages);
      localStorage.setItem("rag-chat-demo-seen", "true");
    }
  }, []);

  // Save messages to localStorage
  useEffect(() => {
    if (messages.length > 0) {
      const toSave = messages.filter((m) => !m.isLoading);
      localStorage.setItem("rag-chat-history", JSON.stringify(toSave));
    }
  }, [messages]);

  const sendMessage = async (queryOverride?: string) => {
    const query = queryOverride || input.trim();
    if (!query || isLoading) return;

    const userMessage: ChatMessage = {
      id: generateMessageId(),
      role: "user",
      content: query,
      timestamp: new Date(),
    };

    const loadingMessage: ChatMessage = {
      id: generateMessageId(),
      role: "assistant",
      content: "",
      timestamp: new Date(),
      isLoading: true,
    };

    setMessages((prev) => [...prev, userMessage, loadingMessage]);
    setInput("");
    setIsLoading(true);

    try {
      const response = await deepSearch(query);

      const assistantMessage: ChatMessage = {
        id: loadingMessage.id,
        role: "assistant",
        content: response.answer,
        timestamp: new Date(),
        citations: response.citations,
        sources: response.source_summary,
      };

      setMessages((prev) =>
        prev.map((m) => (m.id === loadingMessage.id ? assistantMessage : m))
      );
    } catch (error: any) {
      const errorMessage: ChatMessage = {
        id: loadingMessage.id,
        role: "assistant",
        content: "",
        timestamp: new Date(),
        error: error.response?.data?.detail || error.message || "Failed to get response",
      };

      setMessages((prev) =>
        prev.map((m) => (m.id === loadingMessage.id ? errorMessage : m))
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem("rag-chat-history");
  };

  const retryMessage = (userMsgId: string) => {
    const userMsg = messages.find((m) => m.id === userMsgId);
    if (userMsg) {
      // Remove the error message
      setMessages((prev) => prev.filter((m) => m.role === "user" || !m.error));
      sendMessage(userMsg.content);
    }
  };

  const suggestedQueries = [
    "What are the main suspects in CASE-2024-042?",
    "Show me the timeline of events for this case",
    "What connections exist between suspects and locations?",
    "What evidence do we have for court?",
  ];

  const loadDemoChat = () => {
    const demoMessages = getDemoMessages();
    setMessages(demoMessages);
    localStorage.setItem("rag-chat-history", JSON.stringify(demoMessages));
    localStorage.setItem("rag-chat-demo-seen", "true");
  };

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-glass-border">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-cyber-purple to-cyber-cyan flex items-center justify-center">
            <Sparkles className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-lg font-display uppercase tracking-wider text-white">
              RAG Intelligence Agent
            </h2>
            <p className="text-xs text-slate-500">
              Powered by File Vault Knowledge Base
            </p>
          </div>
        </div>
        {messages.length > 0 && (
          <button
            onClick={clearChat}
            className="flex items-center gap-2 px-3 py-1.5 text-sm text-slate-400 hover:text-threat-critical border border-glass-border rounded-lg hover:border-threat-critical/30 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
            Clear
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-6 space-y-6 custom-scrollbar">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center space-y-6">
            {/* Empty State Illustration */}
            <div className="relative">
              <div className="w-24 h-24 rounded-full bg-gradient-to-br from-cyber-purple/20 to-cyber-cyan/20 flex items-center justify-center">
                <Bot className="w-12 h-12 text-cyber-purple" />
              </div>
              <div className="absolute -bottom-1 -right-1 w-8 h-8 rounded-full bg-cyber-cyan/20 flex items-center justify-center border border-cyber-cyan/30">
                <FileText className="w-4 h-4 text-cyber-cyan" />
              </div>
            </div>

            <div className="space-y-2 max-w-md">
              <h3 className="text-xl font-display uppercase tracking-wider text-white">
                Ask About Your Documents
              </h3>
              <p className="text-slate-400 text-sm">
                I can search through all files in your File Vault and provide
                accurate, cited answers. Try asking about entities, relationships,
                or specific information from your documents.
              </p>
            </div>

            {/* Demo Chat Button */}
            <button
              onClick={loadDemoChat}
              className="px-6 py-3 bg-gradient-to-r from-cyber-cyan/20 to-cyber-purple/20 border border-cyber-cyan/30 rounded-xl hover:border-cyber-cyan/50 hover:bg-gradient-to-r hover:from-cyber-cyan/30 hover:to-cyber-purple/30 transition-all text-cyber-cyan font-medium text-sm flex items-center gap-2"
            >
              <FileText className="w-4 h-4" />
              Load Demo Investigation Chat
            </button>

            {/* Suggested Queries */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 w-full max-w-2xl mt-4">
              {suggestedQueries.map((query, idx) => (
                <button
                  key={idx}
                  onClick={() => {
                    setInput(query);
                    inputRef.current?.focus();
                  }}
                  className="flex items-start gap-3 p-4 text-left bg-glass-light border border-glass-border rounded-xl hover:border-cyber-cyan/30 hover:bg-glass-medium transition-all group"
                >
                  <Sparkles className="w-5 h-5 text-cyber-cyan flex-shrink-0 mt-0.5 group-hover:scale-110 transition-transform" />
                  <span className="text-sm text-slate-300 group-hover:text-white transition-colors">
                    {query}
                  </span>
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            {messages.map((message, idx) => (
              <MessageBubble
                key={message.id}
                message={message}
                onRetry={
                  message.error && idx > 0
                    ? () => retryMessage(messages[idx - 1]?.id)
                    : undefined
                }
              />
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-4 border-t border-glass-border bg-space-50/50 backdrop-blur-sm">
        <div className="flex gap-3 items-end max-w-4xl mx-auto">
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your documents..."
              disabled={isLoading}
              rows={1}
              className="w-full px-4 py-3 pr-12 bg-glass-medium border border-glass-border rounded-xl text-slate-200 placeholder-slate-500 focus:outline-none focus:border-cyber-cyan/50 focus:ring-1 focus:ring-cyber-cyan/20 resize-none transition-all disabled:opacity-50"
              style={{ minHeight: "48px" }}
            />
            <div className="absolute right-2 bottom-2 text-xs text-slate-600">
              {input.length > 0 && `${input.length} chars`}
            </div>
          </div>
          <button
            onClick={() => sendMessage()}
            disabled={isLoading || !input.trim() || input.trim().length < 3}
            className={cn(
              "flex items-center justify-center w-12 h-12 rounded-xl transition-all",
              isLoading || !input.trim() || input.trim().length < 3
                ? "bg-glass-medium border border-glass-border text-slate-500 cursor-not-allowed"
                : "bg-gradient-to-r from-cyber-cyan to-cyber-purple text-white hover:shadow-glow-cyan hover:scale-105"
            )}
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
          </button>
        </div>
        <p className="text-center text-xs text-slate-600 mt-2">
          Press <kbd className="px-1.5 py-0.5 bg-glass-medium rounded text-slate-500">Enter</kbd> to send, <kbd className="px-1.5 py-0.5 bg-glass-medium rounded text-slate-500">Shift + Enter</kbd> for new line
        </p>
      </div>
    </div>
  );
}


