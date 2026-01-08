"use client"

import { useEffect, useRef, useState } from "react"
import { Spinner } from "@/components/ui/spinner"

interface Node {
  id: string
  label: string
  size: number
  type: string
}

interface Edge {
  source: string
  target: string
  weight: number
}

interface GraphData {
  nodes: Node[]
  edges: Edge[]
  paper_id: string
}

interface KnowledgeGraphProps {
  paperId: string
}

export function KnowledgeGraph({ paperId }: KnowledgeGraphProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [graphData, setGraphData] = useState<GraphData | null>(null)
  const [loading, setLoading] = useState(true)
  const animationRef = useRef<number | undefined>(undefined)

  useEffect(() => {
    fetchGraphData()
  }, [paperId])

  const fetchGraphData = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/graph/${paperId}`)
      const data = await response.json()
      setGraphData(data)
    } catch (error) {
      console.error("[v0] Failed to fetch graph data:", error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!graphData || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    // Set canvas size
    const rect = canvas.getBoundingClientRect()
    canvas.width = rect.width * window.devicePixelRatio
    canvas.height = rect.height * window.devicePixelRatio
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio)

    const width = rect.width
    const height = rect.height

    // Initialize node positions
    const nodePositions = new Map<string, { x: number; y: number; vx: number; vy: number; radius: number }>()

    graphData.nodes.forEach((node, i) => {
      const angle = (i / graphData.nodes.length) * Math.PI * 2
      const radius = Math.min(width, height) * 0.3
      nodePositions.set(node.id, {
        x: width / 2 + Math.cos(angle) * radius,
        y: height / 2 + Math.sin(angle) * radius,
        vx: 0,
        vy: 0,
        radius: Math.max(8, Math.min(20, node.size * 2)),
      })
    })

    // Force-directed layout simulation
    const simulate = () => {
      const alpha = 0.1
      const repelStrength = 1000
      const attractStrength = 0.01

      // Apply forces
      nodePositions.forEach((pos1, id1) => {
        // Repulsion between all nodes
        nodePositions.forEach((pos2, id2) => {
          if (id1 === id2) return
          const dx = pos2.x - pos1.x
          const dy = pos2.y - pos1.y
          const distance = Math.sqrt(dx * dx + dy * dy) || 1
          const force = repelStrength / (distance * distance)
          pos1.vx -= (dx / distance) * force
          pos1.vy -= (dy / distance) * force
        })

        // Attraction along edges
        graphData.edges.forEach((edge) => {
          if (edge.source === id1) {
            const pos2 = nodePositions.get(edge.target)
            if (pos2) {
              const dx = pos2.x - pos1.x
              const dy = pos2.y - pos1.y
              pos1.vx += dx * attractStrength * edge.weight
              pos1.vy += dy * attractStrength * edge.weight
            }
          } else if (edge.target === id1) {
            const pos2 = nodePositions.get(edge.source)
            if (pos2) {
              const dx = pos2.x - pos1.x
              const dy = pos2.y - pos1.y
              pos1.vx += dx * attractStrength * edge.weight
              pos1.vy += dy * attractStrength * edge.weight
            }
          }
        })

        // Center gravity
        const centerDx = width / 2 - pos1.x
        const centerDy = height / 2 - pos1.y
        pos1.vx += centerDx * 0.001
        pos1.vy += centerDy * 0.001

        // Apply velocity with damping
        pos1.x += pos1.vx * alpha
        pos1.y += pos1.vy * alpha
        pos1.vx *= 0.9
        pos1.vy *= 0.9

        // Keep within bounds
        const padding = 50
        pos1.x = Math.max(padding, Math.min(width - padding, pos1.x))
        pos1.y = Math.max(padding, Math.min(height - padding, pos1.y))
      })
    }

    // Render function
    const render = () => {
      ctx.clearRect(0, 0, width, height)

      // Draw edges
      ctx.strokeStyle = "rgba(150, 150, 150, 0.3)"
      ctx.lineWidth = 1
      graphData.edges.forEach((edge) => {
        const source = nodePositions.get(edge.source)
        const target = nodePositions.get(edge.target)
        if (source && target) {
          ctx.beginPath()
          ctx.moveTo(source.x, source.y)
          ctx.lineTo(target.x, target.y)
          ctx.stroke()
        }
      })

      // Draw nodes
      graphData.nodes.forEach((node) => {
        const pos = nodePositions.get(node.id)
        if (!pos) return

        // Node circle
        ctx.beginPath()
        ctx.arc(pos.x, pos.y, pos.radius, 0, Math.PI * 2)
        ctx.fillStyle = "rgba(99, 102, 241, 0.8)"
        ctx.fill()
        ctx.strokeStyle = "rgba(255, 255, 255, 0.8)"
        ctx.lineWidth = 2
        ctx.stroke()

        // Label
        ctx.fillStyle = "rgba(255, 255, 255, 0.95)"
        ctx.font = "11px sans-serif"
        ctx.textAlign = "center"
        ctx.textBaseline = "middle"
        const maxWidth = pos.radius * 2 - 4
        const text = node.label.length > 12 ? node.label.substring(0, 10) + "..." : node.label
        ctx.fillText(text, pos.x, pos.y, maxWidth)
      })
    }

    // Animation loop
    let iterations = 0
    const maxIterations = 300

    const animate = () => {
      if (iterations < maxIterations) {
        simulate()
        iterations++
      }
      render()
      animationRef.current = requestAnimationFrame(animate)
    }

    animate()

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current)
      }
    }
  }, [graphData])

  if (loading) {
    return (
      <div className="h-full flex items-center justify-center">
        <Spinner className="h-6 w-6" />
      </div>
    )
  }

  if (!graphData || graphData.nodes.length === 0) {
    return (
      <div className="h-full flex items-center justify-center">
        <p className="text-sm text-muted-foreground text-center text-balance">
          No concepts extracted yet. Try asking a question first.
        </p>
      </div>
    )
  }

  return (
    <div className="h-full w-full relative">
      <canvas ref={canvasRef} className="w-full h-full rounded-lg bg-muted/10" />
      <div className="absolute top-2 left-2 bg-card/90 backdrop-blur-sm p-2 rounded-md border border-border">
        <p className="text-xs text-muted-foreground">
          {graphData.nodes.length} concepts, {graphData.edges.length} connections
        </p>
      </div>
    </div>
  )
}
