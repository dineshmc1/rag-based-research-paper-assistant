"use client"

import { useState } from "react"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Card } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, ChevronRight, ChevronLeft } from "lucide-react"
import { KnowledgeGraph } from "@/components/knowledge-graph"
import { PDFViewer } from "@/components/pdf-viewer"

interface ContextPanelProps {
  answer: any
  selectedPaper: string | null
}

export function ContextPanel({ answer, selectedPaper }: ContextPanelProps) {
  const [collapsed, setCollapsed] = useState(false)
  const [showPDF, setShowPDF] = useState(false)
  const [pdfPage, setPdfPage] = useState(1)

  if (collapsed) {
    return (
      <div className="w-16 border-l border-border bg-card flex flex-col items-center py-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setCollapsed(false)}
          className="text-muted-foreground hover:text-foreground"
        >
          <ChevronLeft className="h-5 w-5" />
        </Button>
      </div>
    )
  }

  return (
    <>
      <div className="w-96 border-l border-border bg-card flex flex-col">
        {/* Header */}
        <div className="p-4 border-b border-border flex items-center justify-between">
          <h3 className="font-semibold text-sm">Context</h3>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setCollapsed(true)}
            className="h-8 w-8 text-muted-foreground hover:text-foreground"
          >
            <ChevronRight className="h-4 w-4" />
          </Button>
        </div>

        {/* Content */}
        {!answer ? (
          <div className="flex-1 flex items-center justify-center p-6">
            <p className="text-sm text-muted-foreground text-center text-balance">
              Ask a question to see citations and context
            </p>
          </div>
        ) : (
          <Tabs defaultValue="citations" className="flex-1 flex flex-col">
            <TabsList className="mx-4 mt-4">
              <TabsTrigger value="citations" className="text-xs">
                Citations
              </TabsTrigger>
              <TabsTrigger value="chunks" className="text-xs">
                Retrieved
              </TabsTrigger>
              <TabsTrigger value="graph" className="text-xs">
                Graph
              </TabsTrigger>
            </TabsList>

            <TabsContent value="citations" className="flex-1 mt-0">
              <ScrollArea className="h-full px-4 py-4">
                {answer.citations.length === 0 ? (
                  <div className="text-sm text-muted-foreground text-center py-8">No citations available</div>
                ) : (
                  <div className="space-y-3">
                    {answer.citations.map((citation: any, idx: number) => (
                      <Card
                        key={citation.chunk_id}
                        className="p-4 hover:bg-accent/50 transition-colors cursor-pointer"
                        onClick={() => {
                          setPdfPage(citation.page)
                          setShowPDF(true)
                        }}
                      >
                        <div className="flex items-start gap-3">
                          <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                            <span className="text-xs font-semibold text-primary">{idx + 1}</span>
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-2">
                              <FileText className="h-3.5 w-3.5 text-muted-foreground" />
                              <span className="text-sm font-medium">Page {citation.page}</span>
                            </div>
                            <Badge variant="secondary" className="text-xs mb-2">
                              {citation.section}
                            </Badge>
                            <div className="flex items-center gap-2 mt-2">
                              <div className="flex-1 bg-muted/50 rounded-full h-1.5 overflow-hidden">
                                <div
                                  className="bg-primary h-full transition-all"
                                  style={{ width: `${citation.confidence * 100}%` }}
                                />
                              </div>
                              <span className="text-xs text-muted-foreground">
                                {Math.round(citation.confidence * 100)}%
                              </span>
                            </div>
                          </div>
                        </div>
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="chunks" className="flex-1 mt-0">
              <ScrollArea className="h-full px-4 py-4">
                {answer.retrieved_chunks.length === 0 ? (
                  <div className="text-sm text-muted-foreground text-center py-8">No chunks retrieved</div>
                ) : (
                  <div className="space-y-3">
                    {answer.retrieved_chunks.map((chunk: any, idx: number) => (
                      <Card key={idx} className="p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <Badge variant="outline" className="text-xs">
                              Page {chunk.page}
                            </Badge>
                            <span className="text-xs text-muted-foreground">{chunk.section}</span>
                          </div>
                          <Badge variant="secondary" className="text-xs">
                            {Math.round(chunk.confidence * 100)}%
                          </Badge>
                        </div>
                        <p className="text-xs text-muted-foreground leading-relaxed line-clamp-4">{chunk.text}</p>
                      </Card>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </TabsContent>

            <TabsContent value="graph" className="flex-1 mt-0">
              <div className="h-full p-4">
                {selectedPaper ? (
                  <KnowledgeGraph paperId={selectedPaper} />
                ) : (
                  <div className="h-full flex items-center justify-center">
                    <p className="text-sm text-muted-foreground text-center text-balance">
                      Select a paper to view its knowledge graph
                    </p>
                  </div>
                )}
              </div>
            </TabsContent>
          </Tabs>
        )}
      </div>

      {/* PDF Viewer Modal */}
      {showPDF && selectedPaper && (
        <PDFViewer paperId={selectedPaper} initialPage={pdfPage} onClose={() => setShowPDF(false)} />
      )}
    </>
  )
}
