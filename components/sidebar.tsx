"use client"

import type React from "react"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Upload, FileText, Trash2, ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

interface Paper {
  paper_id: string
  filename: string
  chunks_count: number
}

interface SidebarProps {
  selectedPaper: string | null
  onSelectPaper: (paperId: string | null) => void
  collapsed: boolean
  onToggleCollapse: () => void
}

export function Sidebar({ selectedPaper, onSelectPaper, collapsed, onToggleCollapse }: SidebarProps) {
  const [papers, setPapers] = useState<Paper[]>([])
  const [uploading, setUploading] = useState(false)

  useEffect(() => {
    fetchPapers()
  }, [])

  const fetchPapers = async () => {
    try {
      const response = await fetch("http://localhost:8000/api/papers/list")
      const data = await response.json()
      setPapers(data)
    } catch (error) {
      console.error("[v0] Failed to fetch papers:", error)
    }
  }

  const handleUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    setUploading(true)
    const formData = new FormData()
    formData.append("file", file)

    try {
      const response = await fetch("http://localhost:8000/api/ingest/upload", {
        method: "POST",
        body: formData,
      })

      if (response.ok) {
        await fetchPapers()
      }
    } catch (error) {
      console.error("[v0] Upload failed:", error)
    } finally {
      setUploading(false)
    }
  }

  const handleDelete = async (paperId: string) => {
    try {
      await fetch(`http://localhost:8000/api/ingest/paper/${paperId}`, {
        method: "DELETE",
      })
      if (selectedPaper === paperId) {
        onSelectPaper(null)
      }
      await fetchPapers()
    } catch (error) {
      console.error("[v0] Delete failed:", error)
    }
  }

  if (collapsed) {
    return (
      <div className="w-16 border-r border-border bg-card flex flex-col items-center py-4 gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="text-muted-foreground hover:text-foreground"
        >
          <ChevronRight className="h-5 w-5" />
        </Button>
        <div className="flex-1" />
      </div>
    )
  }

  return (
    <div className="w-80 border-r border-border bg-card flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-border flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-balance">Research Assistant</h1>
          <p className="text-sm text-muted-foreground mt-1">Deep RAG for Papers</p>
        </div>
        <Button
          variant="ghost"
          size="icon"
          onClick={onToggleCollapse}
          className="text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>
      </div>

      {/* Upload Button */}
      <div className="p-4">
        <label htmlFor="pdf-upload">
          <Button className="w-full" disabled={uploading} asChild>
            <div className="cursor-pointer">
              <Upload className="mr-2 h-4 w-4" />
              {uploading ? "Processing..." : "Upload PDF"}
            </div>
          </Button>
        </label>
        <input id="pdf-upload" type="file" accept=".pdf" className="hidden" onChange={handleUpload} />
      </div>

      {/* Papers List */}
      <ScrollArea className="flex-1 px-4">
        <div className="space-y-2 pb-4">
          {papers.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground text-sm">No papers yet. Upload a PDF to start.</div>
          ) : (
            papers.map((paper) => (
              <div
                key={paper.paper_id}
                className={cn(
                  "group p-3 rounded-lg border border-border bg-background/50 hover:bg-accent/50 transition-colors cursor-pointer",
                  selectedPaper === paper.paper_id && "bg-accent border-accent-foreground/20",
                )}
                onClick={() => onSelectPaper(paper.paper_id)}
              >
                <div className="flex items-start gap-3">
                  <FileText className="h-4 w-4 mt-0.5 text-muted-foreground flex-shrink-0" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium truncate">{paper.filename.replace(".pdf", "")}</p>
                    <p className="text-xs text-muted-foreground mt-1">{paper.chunks_count} chunks</p>
                  </div>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-7 w-7 opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation()
                      handleDelete(paper.paper_id)
                    }}
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </Button>
                </div>
              </div>
            ))
          )}
        </div>
      </ScrollArea>

      {/* Filter Section */}
      <div className="p-4 border-t border-border">
        <Button
          variant={selectedPaper ? "secondary" : "ghost"}
          size="sm"
          className="w-full"
          onClick={() => onSelectPaper(null)}
        >
          {selectedPaper ? "Search Selected Paper" : "Search All Papers"}
        </Button>
      </div>
    </div>
  )
}
