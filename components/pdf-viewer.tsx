"use client"

import { useEffect, useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ChevronLeft, ChevronRight, Download, X } from "lucide-react"

interface PDFViewerProps {
  paperId: string
  initialPage?: number
  onClose: () => void
}

export function PDFViewer({ paperId, initialPage = 1, onClose }: PDFViewerProps) {
  const [currentPage, setCurrentPage] = useState(initialPage)
  const [totalPages, setTotalPages] = useState(0)
  const [pdfUrl, setPdfUrl] = useState("")

  useEffect(() => {
    setPdfUrl(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/papers/${paperId}/download`)
  }, [paperId])

  const handleDownload = () => {
    window.open(pdfUrl, "_blank")
  }

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-w-4xl h-[90vh] flex flex-col p-0">
        <DialogHeader className="px-6 py-4 border-b border-border">
          <div className="flex items-center justify-between">
            <DialogTitle>PDF Viewer</DialogTitle>
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={handleDownload}>
                <Download className="h-4 w-4 mr-2" />
                Download
              </Button>
              <Button variant="ghost" size="icon" onClick={onClose}>
                <X className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </DialogHeader>

        <div className="flex-1 overflow-hidden bg-muted/20">
          <iframe src={pdfUrl} className="w-full h-full border-0" title="PDF Viewer" />
        </div>

        <div className="px-6 py-4 border-t border-border flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="icon"
              onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <div className="flex items-center gap-2">
              <Input
                type="number"
                value={currentPage}
                onChange={(e) => setCurrentPage(Number.parseInt(e.target.value) || 1)}
                className="w-16 text-center"
                min={1}
                max={totalPages || 999}
              />
              <span className="text-sm text-muted-foreground">/ {totalPages || "?"}</span>
            </div>
            <Button variant="outline" size="icon" onClick={() => setCurrentPage((p) => p + 1)}>
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}
