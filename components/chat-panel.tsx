"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Loader2, FileText, BarChart3 } from "lucide-react"
import { AnswerBlock } from "@/components/answer-block"

interface Message {
  id: string
  type: "question" | "answer"
  content: any
  timestamp: Date
}

interface ChatPanelProps {
  selectedPaper: string | null
  onAnswerReceived: (answer: any) => void
}

export function ChatPanel({ selectedPaper, onAnswerReceived }: ChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const [executionMode, setExecutionMode] = useState<"text" | "python">("text")
  const scrollRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const question = input.trim()
    setInput("")

    // Add question to messages
    const questionMsg: Message = {
      id: Date.now().toString(),
      type: "question",
      content: question,
      timestamp: new Date(),
    }
    setMessages((prev) => [...prev, questionMsg])
    setLoading(true)

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          paper_id: selectedPaper,
          include_reasoning: false,
          execution_mode: executionMode,
        }),
      })

      const data = await response.json()

      // Add answer to messages
      const answerMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: "answer",
        content: data,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, answerMsg])
      onAnswerReceived(data)
    } catch (error) {
      console.error("[v0] Query failed:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border px-8 py-4 bg-card">
        <h2 className="text-lg font-semibold">{selectedPaper ? "Querying Selected Paper" : "Querying All Papers"}</h2>
        <p className="text-sm text-muted-foreground mt-1">Ask questions about your research papers</p>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 px-8 py-6" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md space-y-4">
              <h3 className="text-2xl font-semibold text-balance">Start Your Research Journey</h3>
              <p className="text-muted-foreground leading-relaxed">
                Upload research papers and ask questions. The system will retrieve relevant sections, re-rank them for
                relevance, and provide grounded answers with citations.
              </p>
            </div>
          </div>
        ) : (
          <div className="space-y-8 max-w-4xl mx-auto">
            {messages.map((message) => (
              <div key={message.id}>
                {message.type === "question" ? (
                  <div className="flex justify-end">
                    <div className="bg-primary text-primary-foreground px-5 py-3 rounded-2xl max-w-2xl">
                      <p className="text-sm leading-relaxed">{message.content}</p>
                    </div>
                  </div>
                ) : (
                  <AnswerBlock answer={message.content} />
                )}
              </div>
            ))}
            {loading && (
              <div className="flex items-center gap-3 text-muted-foreground">
                <Loader2 className="h-4 w-4 animate-spin" />
                <span className="text-sm">Searching and analyzing papers...</span>
              </div>
            )}
          </div>
        )}
      </ScrollArea>

      {/* Input */}
      <div className="border-t border-border px-8 py-6 bg-card">
        <form onSubmit={handleSubmit} className="max-w-4xl mx-auto">
          {/* Mode Selector */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-sm text-muted-foreground mr-2">Mode:</span>
            <Button
              type="button"
              variant={executionMode === "text" ? "default" : "outline"}
              size="sm"
              onClick={() => setExecutionMode("text")}
              className="gap-1.5"
            >
              <FileText className="h-3.5 w-3.5" />
              Text
            </Button>
            <Button
              type="button"
              variant={executionMode === "python" ? "default" : "outline"}
              size="sm"
              onClick={() => setExecutionMode("python")}
              className="gap-1.5"
            >
              <BarChart3 className="h-3.5 w-3.5" />
              Visualization
            </Button>
          </div>

          <div className="relative">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder={executionMode === "python" ? "Describe the visualization you need (e.g., 'plot accuracy metrics')..." : "Ask a question about your research papers..."}
              className="pr-12 resize-none min-h-[60px] text-base"
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault()
                  handleSubmit(e)
                }
              }}
            />
            <Button
              type="submit"
              size="icon"
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-2 h-9 w-9"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
