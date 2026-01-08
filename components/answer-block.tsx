"use client"

import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, ChevronDown, ChevronUp } from "lucide-react"
import { useState } from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"

interface AnswerBlockProps {
  answer: {
    answer: string
    citations: Array<{
      paper: string
      page: number
      chunk_id: string
      confidence: number
      section: string
    }>
    retrieved_chunks: Array<{
      text: string
      page: number
      section: string
      confidence: number
    }>
    concepts: string[]
  }
}

export function AnswerBlock({ answer }: AnswerBlockProps) {
  const [showSources, setShowSources] = useState(false)

  return (
    <Card className="p-6 bg-card border-border">
      {/* Answer */}
      <div className="prose prose-sm max-w-none dark:prose-invert">
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            // Ensure images (plots) are responsive and handled correctly
            img: ({ node, ...props }) => <img {...props} className="max-w-full h-auto rounded-lg" />,
            // Style tables
            table: ({ node, ...props }) => <div className="overflow-x-auto my-4"><table {...props} className="w-full border-collapse text-sm" /></div>,
            th: ({ node, ...props }) => <th {...props} className="border border-border bg-muted p-2 text-left font-medium" />,
            td: ({ node, ...props }) => <td {...props} className="border border-border p-2" />,
          }}
        >
          {answer.answer}
        </ReactMarkdown>
      </div>

      {/* Citations */}
      {answer.citations?.length > 0 && (
        <div className="mt-6 pt-6 border-t border-border">
          <div className="flex items-center justify-between mb-3">
            <h4 className="text-sm font-medium flex items-center gap-2">
              <FileText className="h-4 w-4 text-muted-foreground" />
              Sources ({answer.citations.length})
            </h4>
            <Button variant="ghost" size="sm" onClick={() => setShowSources(!showSources)} className="text-xs">
              {showSources ? (
                <>
                  <ChevronUp className="h-3.5 w-3.5 mr-1" />
                  Hide
                </>
              ) : (
                <>
                  <ChevronDown className="h-3.5 w-3.5 mr-1" />
                  Show
                </>
              )}
            </Button>
          </div>

          {showSources && (
            <div className="space-y-2">
              {answer.citations.map((citation, idx) => (
                <div key={`${citation.chunk_id}-${idx}`} className="flex items-center gap-3 p-3 rounded-lg bg-muted/50 text-sm">
                  <span className="font-medium text-muted-foreground">[{idx + 1}]</span>
                  <div className="flex-1">
                    <span className="text-foreground">Page {citation.page}</span>
                    <span className="text-muted-foreground mx-2">•</span>
                    <span className="text-muted-foreground">{citation.section}</span>
                  </div>
                  <Badge variant="secondary" className="text-xs">
                    {citation.confidence ? Math.round(citation.confidence * 100) : 0}%
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Concepts */}
      {answer.concepts?.length > 0 && (
        <div className="mt-4 pt-4 border-t border-border">
          <h4 className="text-sm font-medium mb-3 text-muted-foreground">Key Concepts</h4>
          <div className="flex flex-wrap gap-2">
            {answer.concepts.map((concept, idx) => (
              <Badge key={idx} variant="outline" className="text-xs">
                {concept}
              </Badge>
            ))}
          </div>
        </div>
      )}
    </Card>
  )
}
