import { useState, useRef, useEffect } from 'react'
import { Canvas } from '@react-three/fiber'
import { OrbitControls, PerspectiveCamera, Grid, AxesHelper } from '@react-three/drei'
import { Box, Sphere } from '@react-three/drei'
import { RotateCw, ZoomIn, ZoomOut, Maximize2, Download, Grid3X3, BoxSelect } from 'lucide-react'

export interface Model3DViewerProps {
  modelUrl?: string
  showGrid?: boolean
  showAxes?: boolean
  showWireframe?: boolean
  backgroundColor?: string
}

export function Model3DViewer({
  modelUrl,
  showGrid = true,
  showAxes = true,
  showWireframe = false,
  backgroundColor = '#1a1a2e',
}: Model3DViewerProps) {
  const [isFullscreen, setIsFullscreen] = useState(false)
  const [viewMode, setViewMode] = useState<'perspective' | 'top' | 'side' | 'front'>('perspective')
  const [wireframe, setWireframe] = useState(showWireframe)
  const [grid, setGrid] = useState(showGrid)
  const [axes, setAxes] = useState(showAxes)
  const [autoRotate, setAutoRotate] = useState(false)
  const cameraRef = useRef<any>(null)
  const controlsRef = useRef<any>(null)

  const handleViewChange = (mode: 'perspective' | 'top' | 'side' | 'front') => {
    setViewMode(mode)
    if (cameraRef.current) {
      const camera = cameraRef.current
      switch (mode) {
        case 'top':
          camera.position.set(0, 10, 0)
          camera.lookAt(0, 0, 0)
          break
        case 'side':
          camera.position.set(10, 0, 0)
          camera.lookAt(0, 0, 0)
          break
        case 'front':
          camera.position.set(0, 0, 10)
          camera.lookAt(0, 0, 0)
          break
        default:
          camera.position.set(5, 5, 5)
          camera.lookAt(0, 0, 0)
      }
    }
  }

  const handleResetCamera = () => {
    if (cameraRef.current && controlsRef.current) {
      cameraRef.current.position.set(5, 5, 5)
      cameraRef.current.lookAt(0, 0, 0)
      controlsRef.current.reset()
    }
  }

  const handleZoomIn = () => {
    if (cameraRef.current) {
      const camera = cameraRef.current
      camera.position.multiplyScalar(0.9)
    }
  }

  const handleZoomOut = () => {
    if (cameraRef.current) {
      const camera = cameraRef.current
      camera.position.multiplyScalar(1.1)
    }
  }

  const handleRotate = () => {
    setAutoRotate(!autoRotate)
  }

  const toggleFullscreen = () => {
    if (!isFullscreen) {
      document.documentElement.requestFullscreen()
    } else {
      document.exitFullscreen()
    }
    setIsFullscreen(!isFullscreen)
  }

  const handleDownload = () => {
    if (modelUrl) {
      const link = document.createElement('a')
      link.href = modelUrl
      link.download = `model_${Date.now()}.obj`
      link.click()
    }
  }

  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }

    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => {
      document.removeEventListener('fullscreenchange', handleFullscreenChange)
    }
  }, [])

  return (
    <div className={`w-full h-full relative ${isFullscreen ? 'fixed inset-0 z-50' : ''}`}>
      <div className="absolute top-4 left-4 z-10 flex flex-col gap-2">
        <div className="bg-card/90 backdrop-blur-sm rounded-lg p-2 shadow-lg border border-border">
          <h3 className="text-sm font-semibold mb-2">视图模式</h3>
          <div className="flex flex-col gap-1">
            <button
              onClick={() => handleViewChange('perspective')}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors ${
                viewMode === 'perspective' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              透视视图
            </button>
            <button
              onClick={() => handleViewChange('top')}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors ${
                viewMode === 'top' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              顶视图
            </button>
            <button
              onClick={() => handleViewChange('side')}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors ${
                viewMode === 'side' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              侧视图
            </button>
            <button
              onClick={() => handleViewChange('front')}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors ${
                viewMode === 'front' ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              前视图
            </button>
          </div>
        </div>

        <div className="bg-card/90 backdrop-blur-sm rounded-lg p-2 shadow-lg border border-border">
          <h3 className="text-sm font-semibold mb-2">显示选项</h3>
          <div className="flex flex-col gap-1">
            <button
              onClick={() => setGrid(!grid)}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-2 ${
                grid ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              <Grid3X3 className="h-4 w-4" />
              显示网格
            </button>
            <button
              onClick={() => setAxes(!axes)}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-2 ${
                axes ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              <BoxSelect className="h-4 w-4" />
              显示坐标轴
            </button>
            <button
              onClick={() => setWireframe(!wireframe)}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-2 ${
                wireframe ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              <Box className="h-4 w-4" />
              线框模式
            </button>
            <button
              onClick={handleRotate}
              className={`text-left px-3 py-1.5 rounded text-sm transition-colors flex items-center gap-2 ${
                autoRotate ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
              }`}
            >
              <RotateCw className={`h-4 w-4 ${autoRotate ? 'animate-spin' : ''}`} />
              自动旋转
            </button>
          </div>
        </div>
      </div>

      <div className="absolute top-4 right-4 z-10 flex flex-col gap-2">
        <div className="bg-card/90 backdrop-blur-sm rounded-lg p-2 shadow-lg border border-border">
          <div className="flex flex-col gap-1">
            <button
              onClick={handleResetCamera}
              className="px-3 py-1.5 rounded text-sm transition-colors hover:bg-accent"
              title="重置相机"
            >
              重置
            </button>
            <button
              onClick={handleZoomIn}
              className="px-3 py-1.5 rounded text-sm transition-colors hover:bg-accent"
              title="放大"
            >
              <ZoomIn className="h-4 w-4" />
            </button>
            <button
              onClick={handleZoomOut}
              className="px-3 py-1.5 rounded text-sm transition-colors hover:bg-accent"
              title="缩小"
            >
              <ZoomOut className="h-4 w-4" />
            </button>
            <button
              onClick={handleDownload}
              className="px-3 py-1.5 rounded text-sm transition-colors hover:bg-accent"
              title="下载模型"
            >
              <Download className="h-4 w-4" />
            </button>
            <button
              onClick={toggleFullscreen}
              className="px-3 py-1.5 rounded text-sm transition-colors hover:bg-accent"
              title="全屏"
            >
              <Maximize2 className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>

      <Canvas
        style={{ background: backgroundColor }}
        camera={{ position: [5, 5, 5], fov: 50 }}
      >
        <PerspectiveCamera ref={cameraRef} makeDefault position={[5, 5, 5]} fov={50} />
        <OrbitControls
          ref={controlsRef}
          autoRotate={autoRotate}
          autoRotateSpeed={1.0}
          enableDamping
          dampingFactor={0.05}
          minDistance={2}
          maxDistance={50}
        />

        {grid && <Grid args={[20, 20]} cellSize={1} cellColor="#e5e7eb" sectionSize={5} sectionColor="#d1d5db" fadeDistance={25} fadeStrength={1} />}
        {axes && <AxesHelper args={[10]} />}

        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} />

        {modelUrl ? (
          <group>
            <mesh position={[0, 0, 0]} wireframe={wireframe}>
              <boxGeometry args={[2, 0.5, 4]} />
              <meshStandardMaterial color="#3b82f6" wireframe={wireframe} />
            </mesh>
            <mesh position={[0, 0.5, 0]} wireframe={wireframe}>
              <boxGeometry args={[0.5, 1, 2]} />
              <meshStandardMaterial color="#10b981" wireframe={wireframe} />
            </mesh>
            <mesh position={[0, -0.5, 0]} wireframe={wireframe}>
              <boxGeometry args={[0.5, 1, 2]} />
              <meshStandardMaterial color="#10b981" wireframe={wireframe} />
            </mesh>
          </group>
        ) : (
          <group>
            <mesh position={[0, 0, 0]} wireframe={wireframe}>
              <boxGeometry args={[2, 0.5, 4]} />
              <meshStandardMaterial color="#3b82f6" wireframe={wireframe} />
            </mesh>
            <mesh position={[0, 0.5, 0]} wireframe={wireframe}>
              <boxGeometry args={[0.5, 1, 2]} />
              <meshStandardMaterial color="#10b981" wireframe={wireframe} />
            </mesh>
            <mesh position={[0, -0.5, 0]} wireframe={wireframe}>
              <boxGeometry args={[0.5, 1, 2]} />
              <meshStandardMaterial color="#10b981" wireframe={wireframe} />
            </mesh>
          </group>
        )}
      </Canvas>
    </div>
  )
}
