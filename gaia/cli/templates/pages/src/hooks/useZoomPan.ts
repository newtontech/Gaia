import { useState, useCallback, useRef, useEffect } from 'react'

export interface Transform {
  x: number
  y: number
  scale: number
}

export interface UseZoomPanOptions {
  minScale?: number
  maxScale?: number
  zoomStep?: number
}

export function useZoomPan(options: UseZoomPanOptions = {}) {
  const { minScale = 0.1, maxScale = 3, zoomStep = 0.2 } = options
  const [transform, setTransform] = useState<Transform>({ x: 0, y: 0, scale: 1 })
  const [isDragging, setIsDragging] = useState(false)
  const dragStartRef = useRef<{ x: number; y: number } | null>(null)
  const transformStartRef = useRef<Transform | null>(null)

  const clampScale = useCallback((scale: number) => {
    return Math.max(minScale, Math.min(maxScale, scale))
  }, [minScale, maxScale])

  const setTransformValue = useCallback((t: Transform) => {
    setTransform({
      x: t.x,
      y: t.y,
      scale: clampScale(t.scale),
    })
  }, [clampScale])

  const zoom = useCallback((delta: number, center?: { x: number; y: number }) => {
    setTransform(prev => {
      const newScale = clampScale(prev.scale + delta)
      if (newScale === prev.scale) return prev

      if (center) {
        // Zoom towards center point
        const scaleRatio = newScale / prev.scale
        const newX = center.x - (center.x - prev.x) * scaleRatio
        const newY = center.y - (center.y - prev.y) * scaleRatio
        return { x: newX, y: newY, scale: newScale }
      }

      return { ...prev, scale: newScale }
    })
  }, [clampScale])

  const zoomIn = useCallback(() => zoom(zoomStep), [zoom, zoomStep])
  const zoomOut = useCallback(() => zoom(-zoomStep), [zoom, zoomStep])

  const reset = useCallback(() => {
    setTransform({ x: 0, y: 0, scale: 1 })
  }, [])

  const fitToBounds = useCallback((bounds: { width: number; height: number }, container: { width: number; height: number }, padding = 40) => {
    const graphWidth = bounds.width + padding * 2
    const graphHeight = bounds.height + padding * 2

    const scaleX = container.width / graphWidth
    const scaleY = container.height / graphHeight
    const scale = Math.max(minScale, Math.min(1.5, Math.min(scaleX, scaleY)))

    const x = container.width / 2 - (bounds.width / 2) * scale
    const y = container.height / 2 - (bounds.height / 2) * scale

    setTransform({ x, y, scale })
  }, [minScale])

  const setScale = useCallback((scale: number) => {
    setTransform(prev => ({ ...prev, scale: clampScale(scale) }))
  }, [clampScale])

  const getTransformString = useCallback(() => {
    return `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`
  }, [transform])

  // Mouse drag handlers
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // Don't drag if clicking on a node or interactive element
    if ((e.target as Element).closest('.graph-node, button, input')) return

    setIsDragging(true)
    dragStartRef.current = { x: e.clientX, y: e.clientY }
    transformStartRef.current = { ...transform }
    e.preventDefault()
  }, [transform])

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (!isDragging || !dragStartRef.current || !transformStartRef.current) return

    const dx = e.clientX - dragStartRef.current.x
    const dy = e.clientY - dragStartRef.current.y

    setTransform({
      ...transformStartRef.current,
      x: transformStartRef.current.x + dx,
      y: transformStartRef.current.y + dy,
    })
  }, [isDragging])

  const handleMouseUp = useCallback(() => {
    setIsDragging(false)
    dragStartRef.current = null
    transformStartRef.current = null
  }, [])

  // Wheel zoom handler
  const handleWheel = useCallback((e: React.WheelEvent) => {
    e.preventDefault()
    const delta = e.deltaY > 0 ? -zoomStep * 0.5 : zoomStep * 0.5
    zoom(delta)
  }, [zoom, zoomStep])

  // Touch support for mobile
  const touchStartRef = useRef<{ x: number; y: number } | null>(null)

  const handleTouchStart = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1) {
      touchStartRef.current = { x: e.touches[0].clientX, y: e.touches[0].clientY }
      transformStartRef.current = { ...transform }
    }
  }, [transform])

  const handleTouchMove = useCallback((e: React.TouchEvent) => {
    if (e.touches.length === 1 && touchStartRef.current && transformStartRef.current) {
      const dx = e.touches[0].clientX - touchStartRef.current.x
      const dy = e.touches[0].clientY - touchStartRef.current.y

      setTransform({
        ...transformStartRef.current,
        x: transformStartRef.current.x + dx,
        y: transformStartRef.current.y + dy,
      })
    }
  }, [])

  const handleTouchEnd = useCallback(() => {
    touchStartRef.current = null
    transformStartRef.current = null
  }, [])

  return {
    transform,
    isDragging,
    zoomIn,
    zoomOut,
    reset,
    fitToBounds,
    setScale,
    setTransform: setTransformValue,
    getTransformString,
    handleMouseDown,
    handleMouseMove,
    handleMouseUp,
    handleWheel,
    handleTouchStart,
    handleTouchMove,
    handleTouchEnd,
  }
}
