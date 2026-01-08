"use client"

import type React from "react"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Input } from "@/components/ui/input"
import {
  FolderPlus,
  ChevronLeft,
  ChevronRight,
  Folder,
  FolderOpen,
  MoreVertical,
  Trash2,
  Edit2,
  MessageSquarePlus,
  MessageSquare,
  FileText,
  Upload,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useWorkspace } from "@/lib/workspace-store"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog"
import { Label } from "@/components/ui/label"

interface WorkspaceSidebarProps {
  collapsed: boolean
  onToggleCollapse: () => void
}

export function WorkspaceSidebar({ collapsed, onToggleCollapse }: WorkspaceSidebarProps) {
  const {
    folders,
    activeFolderId,
    activeChatId,
    createFolder,
    renameFolder,
    deleteFolder,
    setActiveFolder,
    createChatSession,
    renameChatSession,
    deleteChatSession,
    setActiveChat,
    addPDFToFolder,
    renamePDF,
    deletePDF,
    movePDFToFolder,
  } = useWorkspace()

  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set())
  const [showNewFolderDialog, setShowNewFolderDialog] = useState(false)
  const [newFolderName, setNewFolderName] = useState("")
  const [editingItem, setEditingItem] = useState<{ id: string; type: "folder" | "chat" | "pdf"; name: string } | null>(
    null,
  )
  const [uploading, setUploading] = useState(false)
  const [draggedPDF, setDraggedPDF] = useState<string | null>(null)

  const toggleFolder = (folderId: string) => {
    setExpandedFolders((prev) => {
      const next = new Set(prev)
      if (next.has(folderId)) {
        next.delete(folderId)
      } else {
        next.add(folderId)
      }
      return next
    })
  }

  const handleCreateFolder = () => {
    if (newFolderName.trim()) {
      createFolder(newFolderName.trim())
      setNewFolderName("")
      setShowNewFolderDialog(false)
    }
  }

  const handleUploadPDF = async (folderId: string, event: React.ChangeEvent<HTMLInputElement>) => {
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
        const data = await response.json()
        addPDFToFolder(folderId, {
          id: `pdf-${Date.now()}`,
          filename: data.filename,
          originalName: file.name,
          paperId: data.paper_id,
          chunksCount: data.chunks_count,
          uploadedAt: Date.now(),
        })
      }
    } catch (error) {
      console.error("[v0] Upload failed:", error)
    } finally {
      setUploading(false)
    }
  }

  const handleDragStart = (pdfId: string) => {
    setDraggedPDF(pdfId)
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
  }

  const handleDrop = (targetFolderId: string) => {
    if (draggedPDF) {
      movePDFToFolder(draggedPDF, targetFolderId)
      setDraggedPDF(null)
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
      </div>
    )
  }

  return (
    <>
      <div className="w-80 border-r border-border bg-card flex flex-col">
        {/* Header */}
        <div className="p-6 border-b border-border flex items-center justify-between">
          <div>
            <h1 className="text-xl font-semibold text-balance">Workspace</h1>
            <p className="text-sm text-muted-foreground mt-1">Organize your research</p>
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

        {/* New Folder Button */}
        <div className="p-4">
          <Button className="w-full" onClick={() => setShowNewFolderDialog(true)}>
            <FolderPlus className="mr-2 h-4 w-4" />
            New Folder
          </Button>
        </div>

        {/* Folders List */}
        <ScrollArea className="flex-1">
          <div className="px-4 flex flex-col gap-2 pb-4">
            {folders.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground text-sm">
                Create a folder to organize your research
              </div>
            ) : (
              folders.map((folder) => {
                const isExpanded = expandedFolders.has(folder.id)
                const isActive = activeFolderId === folder.id

                return (
                  <div key={folder.id}>
                    {/* Folder Header */}
                    <div
                      className={cn(
                        "group flex items-center gap-2 p-3 rounded-lg border border-border hover:bg-accent/50 transition-colors w-full relative",
                        isActive && "bg-accent border-accent-foreground/20",
                      )}
                      onDragOver={handleDragOver}
                      onDrop={(e) => {
                        e.preventDefault()
                        handleDrop(folder.id)
                      }}
                    >
                      <Button variant="ghost" size="icon" className="h-5 w-5 shrink-0" onClick={() => toggleFolder(folder.id)}>
                        {isExpanded ? <FolderOpen className="h-4 w-4" /> : <Folder className="h-4 w-4" />}
                      </Button>
                      <div
                        className="flex-1 min-w-0 cursor-pointer"
                        onClick={() => {
                          setActiveFolder(folder.id)
                          if (!isExpanded) toggleFolder(folder.id)
                        }}
                      >
                        <p className="text-sm font-medium truncate">{folder.name}</p>
                        <p className="text-xs text-muted-foreground truncate">
                          {folder.pdfFiles.length} PDFs • {folder.chatSessions.length} chats
                        </p>
                      </div>
                      <div className="flex items-center shrink-0 z-10">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-7 w-7 text-muted-foreground hover:text-foreground"
                              onClick={(e) => e.stopPropagation()}
                            >
                              <MoreVertical className="h-4 w-4" />
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuItem
                              onClick={() => setEditingItem({ id: folder.id, type: "folder", name: folder.name })}
                            >
                              <Edit2 className="mr-2 h-4 w-4" />
                              Rename
                            </DropdownMenuItem>
                            <DropdownMenuItem
                              onClick={() => deleteFolder(folder.id)}
                              className="text-destructive focus:text-destructive"
                            >
                              <Trash2 className="mr-2 h-4 w-4" />
                              Delete
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </div>
                    </div>

                    {/* Expanded Folder Content */}
                    {isExpanded && (
                      <div className="ml-4 mt-2 space-y-2 border-l-2 border-border pl-3">
                        {/* Upload PDF Button */}
                        <label htmlFor={`pdf-upload-${folder.id}`}>
                          <div className="flex items-center gap-2 p-2 rounded-lg hover:bg-accent/30 transition-colors cursor-pointer">
                            <Upload className="h-3.5 w-3.5 text-muted-foreground" />
                            <span className="text-xs text-muted-foreground">
                              {uploading ? "Uploading..." : "Upload PDF"}
                            </span>
                          </div>
                        </label>
                        <input
                          id={`pdf-upload-${folder.id}`}
                          type="file"
                          accept=".pdf"
                          className="hidden"
                          onChange={(e) => handleUploadPDF(folder.id, e)}
                          disabled={uploading}
                        />

                        {/* PDFs */}
                        {folder.pdfFiles.map((pdf) => (
                          <div
                            key={pdf.id}
                            draggable
                            onDragStart={() => handleDragStart(pdf.id)}
                            className="group flex items-center gap-2 p-2 rounded-lg hover:bg-accent/30 transition-colors cursor-move"
                          >
                            <FileText className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs truncate">{pdf.originalName.replace(".pdf", "")}</p>
                            </div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6 opacity-0 group-hover:opacity-100 shrink-0"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <MoreVertical className="h-3 w-3" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  onClick={() => setEditingItem({ id: pdf.id, type: "pdf", name: pdf.originalName })}
                                >
                                  <Edit2 className="mr-2 h-4 w-4" />
                                  Rename
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => deletePDF(pdf.id)}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        ))}

                        {/* New Chat Button */}
                        <Button
                          variant="ghost"
                          size="sm"
                          className="w-full justify-start h-8 text-xs"
                          onClick={() => {
                            const chatId = createChatSession(folder.id)
                            setActiveChat(chatId)
                          }}
                        >
                          <MessageSquarePlus className="mr-2 h-3.5 w-3.5" />
                          New Chat
                        </Button>

                        {/* Chat Sessions */}
                        {folder.chatSessions.map((chat) => (
                          <div
                            key={chat.id}
                            className={cn(
                              "group flex items-center gap-2 p-2 rounded-lg hover:bg-accent/30 transition-colors cursor-pointer",
                              activeChatId === chat.id && "bg-accent",
                            )}
                            onClick={() => {
                              setActiveFolder(folder.id)
                              setActiveChat(chat.id)
                            }}
                          >
                            <MessageSquare className="h-3.5 w-3.5 text-muted-foreground flex-shrink-0" />
                            <div className="flex-1 min-w-0">
                              <p className="text-xs truncate">{chat.name}</p>
                            </div>
                            <DropdownMenu>
                              <DropdownMenuTrigger asChild>
                                <Button
                                  variant="ghost"
                                  size="icon"
                                  className="h-6 w-6 opacity-0 group-hover:opacity-100 shrink-0"
                                  onClick={(e) => e.stopPropagation()}
                                >
                                  <MoreVertical className="h-3 w-3" />
                                </Button>
                              </DropdownMenuTrigger>
                              <DropdownMenuContent align="end">
                                <DropdownMenuItem
                                  onClick={() => setEditingItem({ id: chat.id, type: "chat", name: chat.name })}
                                >
                                  <Edit2 className="mr-2 h-4 w-4" />
                                  Rename
                                </DropdownMenuItem>
                                <DropdownMenuItem
                                  onClick={() => deleteChatSession(folder.id, chat.id)}
                                  className="text-destructive focus:text-destructive"
                                >
                                  <Trash2 className="mr-2 h-4 w-4" />
                                  Delete
                                </DropdownMenuItem>
                              </DropdownMenuContent>
                            </DropdownMenu>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )
              })
            )}
          </div>
        </ScrollArea>
      </div>

      {/* New Folder Dialog */}
      <Dialog open={showNewFolderDialog} onOpenChange={setShowNewFolderDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Folder</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="folder-name">Folder Name</Label>
              <Input
                id="folder-name"
                value={newFolderName}
                onChange={(e) => setNewFolderName(e.target.value)}
                placeholder="e.g., Machine Learning Papers"
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    handleCreateFolder()
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowNewFolderDialog(false)}>
              Cancel
            </Button>
            <Button onClick={handleCreateFolder}>Create</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Edit Dialog */}
      <Dialog open={!!editingItem} onOpenChange={() => setEditingItem(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              Rename {editingItem?.type === "folder" ? "Folder" : editingItem?.type === "chat" ? "Chat" : "PDF"}
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="edit-name">Name</Label>
              <Input
                id="edit-name"
                value={editingItem?.name || ""}
                onChange={(e) => setEditingItem(editingItem ? { ...editingItem, name: e.target.value } : null)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && editingItem) {
                    if (editingItem.type === "folder") {
                      renameFolder(editingItem.id, editingItem.name)
                    } else if (editingItem.type === "chat") {
                      const folder = folders.find((f) => f.chatSessions.some((c) => c.id === editingItem.id))
                      if (folder) renameChatSession(folder.id, editingItem.id, editingItem.name)
                    } else if (editingItem.type === "pdf") {
                      renamePDF(editingItem.id, editingItem.name)
                    }
                    setEditingItem(null)
                  }
                }}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setEditingItem(null)}>
              Cancel
            </Button>
            <Button
              onClick={() => {
                if (editingItem) {
                  if (editingItem.type === "folder") {
                    renameFolder(editingItem.id, editingItem.name)
                  } else if (editingItem.type === "chat") {
                    const folder = folders.find((f) => f.chatSessions.some((c) => c.id === editingItem.id))
                    if (folder) renameChatSession(folder.id, editingItem.id, editingItem.name)
                  } else if (editingItem.type === "pdf") {
                    renamePDF(editingItem.id, editingItem.name)
                  }
                  setEditingItem(null)
                }
              }}
            >
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  )
}
