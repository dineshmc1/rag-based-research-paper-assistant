import { create } from "zustand"
import { persist } from "zustand/middleware"

export interface ChatSession {
  id: string
  name: string
  messages: any[]
  createdAt: number
  updatedAt: number
}

export interface PDFFile {
  id: string
  filename: string
  originalName: string
  paperId: string
  chunksCount: number
  folderId: string
  uploadedAt: number
}

export interface Folder {
  id: string
  name: string
  createdAt: number
  updatedAt: number
  chatSessions: ChatSession[]
  pdfFiles: PDFFile[]
}

interface WorkspaceState {
  folders: Folder[]
  activeFolderId: string | null
  activeChatId: string | null

  // Folder operations
  createFolder: (name: string) => void
  renameFolder: (folderId: string, newName: string) => void
  deleteFolder: (folderId: string) => void
  setActiveFolder: (folderId: string | null) => void

  // Chat operations
  createChatSession: (folderId: string, name?: string) => string
  renameChatSession: (folderId: string, chatId: string, newName: string) => void
  deleteChatSession: (folderId: string, chatId: string) => void
  setActiveChat: (chatId: string | null) => void
  updateChatMessages: (folderId: string, chatId: string, messages: any[]) => void

  // PDF operations
  addPDFToFolder: (folderId: string, pdf: Omit<PDFFile, "folderId">) => void
  movePDFToFolder: (pdfId: string, targetFolderId: string) => void
  renamePDF: (pdfId: string, newName: string) => void
  deletePDF: (pdfId: string) => void

  // Getters
  getActiveFolder: () => Folder | null
  getActiveChat: () => ChatSession | null
  getPDFsInFolder: (folderId: string) => PDFFile[]
}

export const useWorkspace = create<WorkspaceState>()(
  persist(
    (set, get) => ({
      folders: [],
      activeFolderId: null,
      activeChatId: null,

      createFolder: (name: string) => {
        const newFolder: Folder = {
          id: `folder-${Date.now()}`,
          name,
          createdAt: Date.now(),
          updatedAt: Date.now(),
          chatSessions: [],
          pdfFiles: [],
        }
        set((state) => ({ folders: [...state.folders, newFolder] }))
      },

      renameFolder: (folderId: string, newName: string) => {
        set((state) => ({
          folders: state.folders.map((folder) =>
            folder.id === folderId ? { ...folder, name: newName, updatedAt: Date.now() } : folder,
          ),
        }))
      },

      deleteFolder: (folderId: string) => {
        set((state) => ({
          folders: state.folders.filter((folder) => folder.id !== folderId),
          activeFolderId: state.activeFolderId === folderId ? null : state.activeFolderId,
        }))
      },

      setActiveFolder: (folderId: string | null) => {
        set({ activeFolderId: folderId, activeChatId: null })
      },

      createChatSession: (folderId: string, name?: string) => {
        const chatId = `chat-${Date.now()}`
        const newChat: ChatSession = {
          id: chatId,
          name: name || `Chat ${Date.now()}`,
          messages: [],
          createdAt: Date.now(),
          updatedAt: Date.now(),
        }
        set((state) => ({
          folders: state.folders.map((folder) =>
            folder.id === folderId
              ? { ...folder, chatSessions: [...folder.chatSessions, newChat], updatedAt: Date.now() }
              : folder,
          ),
          activeChatId: chatId,
        }))
        return chatId
      },

      renameChatSession: (folderId: string, chatId: string, newName: string) => {
        set((state) => ({
          folders: state.folders.map((folder) =>
            folder.id === folderId
              ? {
                  ...folder,
                  chatSessions: folder.chatSessions.map((chat) =>
                    chat.id === chatId ? { ...chat, name: newName, updatedAt: Date.now() } : chat,
                  ),
                  updatedAt: Date.now(),
                }
              : folder,
          ),
        }))
      },

      deleteChatSession: (folderId: string, chatId: string) => {
        set((state) => ({
          folders: state.folders.map((folder) =>
            folder.id === folderId
              ? {
                  ...folder,
                  chatSessions: folder.chatSessions.filter((chat) => chat.id !== chatId),
                  updatedAt: Date.now(),
                }
              : folder,
          ),
          activeChatId: state.activeChatId === chatId ? null : state.activeChatId,
        }))
      },

      setActiveChat: (chatId: string | null) => {
        set({ activeChatId: chatId })
      },

      updateChatMessages: (folderId: string, chatId: string, messages: any[]) => {
        set((state) => ({
          folders: state.folders.map((folder) =>
            folder.id === folderId
              ? {
                  ...folder,
                  chatSessions: folder.chatSessions.map((chat) =>
                    chat.id === chatId ? { ...chat, messages, updatedAt: Date.now() } : chat,
                  ),
                  updatedAt: Date.now(),
                }
              : folder,
          ),
        }))
      },

      addPDFToFolder: (folderId: string, pdf: Omit<PDFFile, "folderId">) => {
        const newPDF: PDFFile = { ...pdf, folderId }
        set((state) => ({
          folders: state.folders.map((folder) =>
            folder.id === folderId
              ? { ...folder, pdfFiles: [...folder.pdfFiles, newPDF], updatedAt: Date.now() }
              : folder,
          ),
        }))
      },

      movePDFToFolder: (pdfId: string, targetFolderId: string) => {
        set((state) => {
          let pdfToMove: PDFFile | null = null
          const updatedFolders = state.folders.map((folder) => {
            const pdf = folder.pdfFiles.find((p) => p.id === pdfId)
            if (pdf) {
              pdfToMove = { ...pdf, folderId: targetFolderId }
              return {
                ...folder,
                pdfFiles: folder.pdfFiles.filter((p) => p.id !== pdfId),
                updatedAt: Date.now(),
              }
            }
            return folder
          })

          if (pdfToMove) {
            return {
              folders: updatedFolders.map((folder) =>
                folder.id === targetFolderId
                  ? { ...folder, pdfFiles: [...folder.pdfFiles, pdfToMove!], updatedAt: Date.now() }
                  : folder,
              ),
            }
          }
          return { folders: updatedFolders }
        })
      },

      renamePDF: (pdfId: string, newName: string) => {
        set((state) => ({
          folders: state.folders.map((folder) => ({
            ...folder,
            pdfFiles: folder.pdfFiles.map((pdf) => (pdf.id === pdfId ? { ...pdf, originalName: newName } : pdf)),
          })),
        }))
      },

      deletePDF: (pdfId: string) => {
        set((state) => ({
          folders: state.folders.map((folder) => ({
            ...folder,
            pdfFiles: folder.pdfFiles.filter((pdf) => pdf.id !== pdfId),
            updatedAt: Date.now(),
          })),
        }))
      },

      getActiveFolder: () => {
        const state = get()
        return state.folders.find((f) => f.id === state.activeFolderId) || null
      },

      getActiveChat: () => {
        const state = get()
        const activeFolder = state.getActiveFolder()
        if (!activeFolder) return null
        return activeFolder.chatSessions.find((c) => c.id === state.activeChatId) || null
      },

      getPDFsInFolder: (folderId: string) => {
        const state = get()
        const folder = state.folders.find((f) => f.id === folderId)
        return folder?.pdfFiles || []
      },
    }),
    {
      name: "research-workspace",
    },
  ),
)
