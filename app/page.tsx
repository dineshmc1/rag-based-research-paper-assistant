"use client"

import { useState } from "react"
import { WorkspaceSidebar } from "@/components/workspace-sidebar"
import { WorkspaceChatPanel } from "@/components/workspace-chat-panel"
import { ContextPanel } from "@/components/context-panel"

export default function ResearchRAG() {
  const [currentAnswer, setCurrentAnswer] = useState<any>(null)
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)

  return (
    <div className="flex h-screen bg-background text-foreground">
      {/* Workspace Sidebar */}
      <WorkspaceSidebar collapsed={sidebarCollapsed} onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)} />

      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <WorkspaceChatPanel onAnswerReceived={setCurrentAnswer} />
      </div>

      {/* Context Panel */}
      <ContextPanel answer={currentAnswer} selectedPaper={null} />
    </div>
  )
}
