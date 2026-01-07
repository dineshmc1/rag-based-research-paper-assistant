"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Send, Loader2 } from "lucide-react"
import { AnswerBlock } from "@/components/answer-block"
import { useWorkspace } from "@/lib/workspace-store"

interface Message {
  id: string
  type: "question" | "answer"
  content: any
  timestamp: Date
}

interface WorkspaceChatPanelProps {
  onAnswerReceived: (answer: any) => void
}

export function WorkspaceChatPanel({ onAnswerReceived }: WorkspaceChatPanelProps) {
  const { activeFolderId, activeChatId, getActiveFolder, getActiveChat, updateChatMessages } = useWorkspace()
  const [input, setInput] = useState("")
  const [loading, setLoading] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const activeFolder = getActiveFolder()
  const activeChat = getActiveChat()
  const messages = activeChat?.messages || []

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading || !activeFolderId || !activeChatId) return

    const question = input.trim()
    setInput("")

    const questionMsg: Message = {
      id: Date.now().toString(),
      type: "question",
      content: question,
      timestamp: new Date(),
    }
    const newMessages = [...messages, questionMsg]
    updateChatMessages(activeFolderId, activeChatId, newMessages)
    setLoading(true)

    try {
      const pdfIds = activeFolder?.pdfFiles.map((pdf) => pdf.paperId) || []

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/chat/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: question,
          paper_ids: pdfIds,
          include_reasoning: false,
        }),
      })

      const data = await response.json()

      const answerMsg: Message = {
        id: (Date.now() + 1).toString(),
        type: "answer",
        content: data,
        timestamp: new Date(),
      }
      updateChatMessages(activeFolderId, activeChatId, [...newMessages, answerMsg])
      onAnswerReceived(data)
    } catch (error) {
      console.error("[v0] Query failed:", error)
    } finally {
      setLoading(false)
    }
  }

  if (!activeFolderId || !activeChatId) {
    return (
      <div className="flex flex-col h-full items-center justify-center p-8">
        <div className="text-center max-w-md space-y-4">
          <h3 className="text-2xl font-semibold text-balance">Welcome to Research Assistant</h3>
          <p className="text-muted-foreground leading-relaxed">
            Create a folder and start a new chat to begin your research journey. Upload PDFs to your folder and ask
            questions across all your papers.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-border px-8 py-4 bg-card">
        <h2 className="text-lg font-semibold">{activeChat?.name}</h2>
        <p className="text-sm text-muted-foreground mt-1">
          {activeFolder?.name} • {activeFolder?.pdfFiles.length || 0} PDFs
        </p>
      </div>

      {/* Messages */}
      <ScrollArea className="flex-1 min-h-0 px-8 py-6" ref={scrollRef}>
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md space-y-4">
              <h3 className="text-2xl font-semibold text-balance">Ask Your First Question</h3>
              <p className="text-muted-foreground leading-relaxed">
                The system will search across all PDFs in this folder, retrieve relevant sections, and provide grounded
                answers with citations.
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
          <div className="relative">
            <Textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a question about your research papers..."
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
