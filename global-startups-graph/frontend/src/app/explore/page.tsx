'use client'

import { useState, useEffect, useCallback, useRef, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { fetchNeighborhood, fetchAutocomplete, fetchShortestPath } from '@/lib/api'
import { NODE_COLORS, NODE_SIZES } from '@/lib/fmt'
import { Loading, EntityBadge, Card, SectionHeader } from '@/components/shared'
import { Search, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react'
import type { GraphData, GraphNode, SearchResult, PathResult } from '@/lib/api'

export default function ExplorePage() {
  return <Suspense fallback={<Loading />}><ExploreInner /></Suspense>
}

function ExploreInner() {
  const searchParams = useSearchParams()
  const initialQ = searchParams.get('q') ?? ''

  const [searchInput, setSearchInput] = useState(initialQ)
  const [selectedEntity, setSelectedEntity] = useState(initialQ)
  const [depth, setDepth] = useState(1)
  const [suggestions, setSuggestions] = useState<SearchResult[]>([])
  const [showSuggestions, setShowSuggestions] = useState(false)

  // Path finder state
  const [pathFrom, setPathFrom] = useState('')
  const [pathTo, setPathTo] = useState('')
  const [findPath, setFindPath] = useState(false)

  const { data: graphData, isLoading } = useQuery({
    queryKey: ['neighborhood', selectedEntity, depth],
    queryFn: () => fetchNeighborhood(selectedEntity, depth),
    enabled: !!selectedEntity,
  })

  const { data: pathData } = useQuery({
    queryKey: ['path', pathFrom, pathTo],
    queryFn: () => fetchShortestPath(pathFrom, pathTo),
    enabled: findPath && !!pathFrom && !!pathTo,
  })

  const { data: autoResults } = useQuery({
    queryKey: ['autocomplete', searchInput],
    queryFn: () => fetchAutocomplete(searchInput),
    enabled: searchInput.length >= 2,
  })

  useEffect(() => {
    if (autoResults) {
      setSuggestions(autoResults)
      setShowSuggestions(true)
    }
  }, [autoResults])

  const handleSelect = (name: string) => {
    setSelectedEntity(name)
    setSearchInput(name)
    setShowSuggestions(false)
  }

  // Canvas rendering for graph
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [nodePositions, setNodePositions] = useState<Map<string, {x: number; y: number}>>(new Map())
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null)

  useEffect(() => {
    if (!graphData?.nodes?.length || !canvasRef.current) return

    const canvas = canvasRef.current
    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const W = canvas.width = canvas.offsetWidth * 2
    const H = canvas.height = canvas.offsetHeight * 2
    ctx.scale(2, 2)
    const w = W / 2, h = H / 2

    // Simple force layout
    const nodes = graphData.nodes
    const edges = graphData.edges
    const pos = new Map<string, {x: number; y: number; vx: number; vy: number}>()

    // Initialize positions in circle
    nodes.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / nodes.length
      const r = Math.min(w, h) * 0.35
      pos.set(n.id, {
        x: w / 2 + r * Math.cos(angle) + (Math.random() - 0.5) * 30,
        y: h / 2 + r * Math.sin(angle) + (Math.random() - 0.5) * 30,
        vx: 0, vy: 0,
      })
    })

    // Center the selected entity
    const center = pos.get(selectedEntity)
    if (center) { center.x = w / 2; center.y = h / 2 }

    // Run force simulation
    const edgeIndex = new Map<string, string[]>()
    edges.forEach(e => {
      if (!edgeIndex.has(e.source)) edgeIndex.set(e.source, [])
      if (!edgeIndex.has(e.target)) edgeIndex.set(e.target, [])
      edgeIndex.get(e.source)!.push(e.target)
      edgeIndex.get(e.target)!.push(e.source)
    })

    for (let iter = 0; iter < 100; iter++) {
      // Repulsion
      nodes.forEach(a => {
        nodes.forEach(b => {
          if (a.id === b.id) return
          const pa = pos.get(a.id)!, pb = pos.get(b.id)!
          const dx = pa.x - pb.x, dy = pa.y - pb.y
          const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1)
          const force = 2000 / (dist * dist)
          pa.vx += (dx / dist) * force
          pa.vy += (dy / dist) * force
        })
      })

      // Attraction (edges)
      edges.forEach(e => {
        const pa = pos.get(e.source), pb = pos.get(e.target)
        if (!pa || !pb) return
        const dx = pb.x - pa.x, dy = pb.y - pa.y
        const dist = Math.max(Math.sqrt(dx * dx + dy * dy), 1)
        const force = dist * 0.01
        pa.vx += (dx / dist) * force; pa.vy += (dy / dist) * force
        pb.vx -= (dx / dist) * force; pb.vy -= (dy / dist) * force
      })

      // Center gravity
      nodes.forEach(n => {
        const p = pos.get(n.id)!
        p.vx += (w / 2 - p.x) * 0.001
        p.vy += (h / 2 - p.y) * 0.001
      })

      // Apply velocities
      const cooling = 1 - iter / 100
      nodes.forEach(n => {
        const p = pos.get(n.id)!
        p.x += p.vx * 0.5 * cooling
        p.y += p.vy * 0.5 * cooling
        p.vx *= 0.8; p.vy *= 0.8
        p.x = Math.max(30, Math.min(w - 30, p.x))
        p.y = Math.max(30, Math.min(h - 30, p.y))
      })
    }

    // Draw
    ctx.clearRect(0, 0, w, h)

    // Edges
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 0.5
    edges.forEach(e => {
      const pa = pos.get(e.source), pb = pos.get(e.target)
      if (!pa || !pb) return
      ctx.beginPath()
      ctx.moveTo(pa.x, pa.y)
      ctx.lineTo(pb.x, pb.y)
      ctx.stroke()
    })

    // Nodes
    nodes.forEach(n => {
      const p = pos.get(n.id)!
      const color = NODE_COLORS[n.type] || '#6b7280'
      const size = NODE_SIZES[n.type] || 4
      const isCenter = n.id === selectedEntity || n.label === selectedEntity

      ctx.beginPath()
      ctx.arc(p.x, p.y, isCenter ? size + 3 : size, 0, 2 * Math.PI)
      ctx.fillStyle = color
      ctx.fill()
      if (isCenter) {
        ctx.strokeStyle = '#fff'
        ctx.lineWidth = 2
        ctx.stroke()
      }

      // Label
      ctx.fillStyle = '#374151'
      ctx.font = `${isCenter ? 11 : 9}px system-ui`
      ctx.textAlign = 'center'
      ctx.fillText(n.label?.substring(0, 20) || '', p.x, p.y + size + 12)
    })

    // Store positions for click detection
    const posMap = new Map<string, {x: number; y: number}>()
    pos.forEach((v, k) => posMap.set(k, {x: v.x, y: v.y}))
    setNodePositions(posMap)

  }, [graphData, selectedEntity])

  // Canvas click handler
  const handleCanvasClick = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current
    if (!canvas || !graphData) return
    const rect = canvas.getBoundingClientRect()
    const x = e.clientX - rect.left
    const y = e.clientY - rect.top

    for (const node of graphData.nodes) {
      const pos = nodePositions.get(node.id)
      if (!pos) continue
      const size = NODE_SIZES[node.type] || 4
      const dx = x - pos.x, dy = y - pos.y
      if (dx * dx + dy * dy < (size + 5) * (size + 5)) {
        handleSelect(node.label || node.id)
        return
      }
    }
  }, [graphData, nodePositions])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Graph Explorer</h1>
          <p className="text-sm text-gray-500">Click any node to explore its connections</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Controls */}
        <div className="space-y-4">
          {/* Search */}
          <Card>
            <SectionHeader>Search</SectionHeader>
            <div className="relative mt-3">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                placeholder="Type any entity..."
                value={searchInput}
                onChange={e => { setSearchInput(e.target.value); setShowSuggestions(true) }}
                onKeyDown={e => e.key === 'Enter' && handleSelect(searchInput)}
                className="w-full pl-9 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-brand-500"
              />
              {showSuggestions && suggestions.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-200 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {suggestions.map((s, i) => (
                    <button key={i}
                      onClick={() => handleSelect(s.name)}
                      className="w-full flex items-center gap-2 px-3 py-2 text-sm hover:bg-gray-50 text-left">
                      <EntityBadge type={s.type} />
                      <span>{s.name}</span>
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Depth control */}
            <div className="mt-4">
              <p className="text-xs font-medium text-gray-500 mb-2">Depth</p>
              <div className="flex gap-1">
                {[1, 2, 3].map(d => (
                  <button key={d}
                    onClick={() => setDepth(d)}
                    className={`px-3 py-1 rounded text-sm ${d === depth ? 'bg-brand-600 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'}`}>
                    {d}-hop
                  </button>
                ))}
              </div>
            </div>
          </Card>

          {/* Path Finder */}
          <Card>
            <SectionHeader>Path Finder</SectionHeader>
            <div className="space-y-2 mt-3">
              <input placeholder="From..." value={pathFrom}
                onChange={e => { setPathFrom(e.target.value); setFindPath(false) }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
              <input placeholder="To..." value={pathTo}
                onChange={e => { setPathTo(e.target.value); setFindPath(false) }}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm" />
              <button onClick={() => setFindPath(true)}
                className="w-full bg-brand-600 text-white py-2 rounded-lg text-sm hover:bg-brand-700">
                Find Path
              </button>
            </div>

            {pathData && !pathData.error && (
              <div className="mt-3 space-y-2">
                <p className="text-xs text-gray-500">{pathData.path_length} hops</p>
                <div className="flex flex-wrap gap-1">
                  {pathData.path_nodes?.map((n, i) => (
                    <div key={i} className="flex items-center gap-1">
                      <button onClick={() => handleSelect(n.name)}
                        className="px-2 py-1 rounded text-xs bg-gray-100 hover:bg-gray-200">
                        {n.name}
                      </button>
                      {i < (pathData.path_nodes?.length ?? 0) - 1 && (
                        <span className="text-gray-300 text-xs">&rarr;</span>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </Card>

          {/* Legend */}
          <Card>
            <SectionHeader>Legend</SectionHeader>
            <div className="space-y-1.5 mt-3">
              {Object.entries(NODE_COLORS).filter(([k]) => !['FundingBracket','FoundedCohort','IndustryCategory'].includes(k)).map(([type, color]) => (
                <div key={type} className="flex items-center gap-2 text-xs">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span>{type}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Graph stats */}
          {graphData && (
            <Card>
              <div className="text-xs text-gray-500 space-y-1">
                <p>Nodes: {graphData.nodes?.length ?? 0}</p>
                <p>Edges: {graphData.edges?.length ?? 0}</p>
              </div>
            </Card>
          )}
        </div>

        {/* Graph canvas */}
        <div className="lg:col-span-3">
          <Card className="p-2">
            {isLoading ? <Loading /> : !selectedEntity ? (
              <div className="h-[600px] flex items-center justify-center text-gray-400">
                Search for an entity to explore the graph
              </div>
            ) : (
              <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                className="w-full h-[600px] cursor-pointer rounded-lg bg-gray-50"
                style={{ imageRendering: 'auto' }}
              />
            )}
          </Card>
        </div>
      </div>
    </div>
  )
}
