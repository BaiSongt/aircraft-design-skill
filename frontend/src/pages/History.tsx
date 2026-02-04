import { useState, useEffect } from 'react'
import { Search, Filter, Download, Trash2, Calendar, Clock, User } from 'lucide-react'

export interface HistoryItem {
  id: string
  type: 'chat' | 'skill_call' | 'envelope' | 'model'
  title: string
  description: string
  timestamp: string
  status: 'success' | 'error' | 'pending'
  metadata?: {
    skill?: string
    provider?: string
    parameters?: any
    result?: any
  }
}

export function History() {
  const [history, setHistory] = useState<HistoryItem[]>(() => {
    const saved = localStorage.getItem('history')
    return saved ? JSON.parse(saved) : []
  })

  const [filterType, setFilterType] = useState<string>('all')
  const [filterStatus, setFilterStatus] = useState<string>('all')
  const [searchText, setSearchText] = useState('')
  const [sortBy, setSortBy] = useState<'timestamp' | 'type' | 'status'>('timestamp')
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc')
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set())

  useEffect(() => {
    localStorage.setItem('history', JSON.stringify(history))
  }, [history])

  const filteredHistory = history.filter(item => {
    const matchesType = filterType === 'all' || item.type === filterType
    const matchesStatus = filterStatus === 'all' || item.status === filterStatus
    const matchesSearch = searchText === '' ||
      item.title.toLowerCase().includes(searchText.toLowerCase()) ||
      item.description.toLowerCase().includes(searchText.toLowerCase())

    return matchesType && matchesStatus && matchesSearch
  })

  const sortedHistory = [...filteredHistory].sort((a, b) => {
    let comparison = 0

    if (sortBy === 'timestamp') {
      comparison = new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
    } else if (sortBy === 'type') {
      comparison = a.type.localeCompare(b.type)
    } else if (sortBy === 'status') {
      comparison = a.status.localeCompare(b.status)
    }

    return sortOrder === 'asc' ? comparison : -comparison
  })

  const handleDelete = (id: string) => {
    if (confirm('确定要删除这条记录吗？')) {
      const newHistory = history.filter(item => item.id !== id)
      setHistory(newHistory)
    }
  }

  const handleDeleteSelected = () => {
    if (selectedItems.size === 0) {
      alert('请先选择要删除的记录')
      return
    }

    if (confirm(`确定要删除选中的 ${selectedItems.size} 条记录吗？`)) {
      const newHistory = history.filter(item => !selectedItems.has(item.id))
      setHistory(newHistory)
      setSelectedItems(new Set())
    }
  }

  const handleClearAll = () => {
    if (confirm('确定要清除所有历史记录吗？此操作不可恢复。')) {
      setHistory([])
      setSelectedItems(new Set())
    }
  }

  const handleExport = () => {
    const dataStr = JSON.stringify(sortedHistory, null, 2)
    const blob = new Blob([dataStr], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `history_${Date.now()}.json`
    link.click()
    URL.revokeObjectURL(url)
  }

  const handleSelectAll = () => {
    if (selectedItems.size === sortedHistory.length) {
      setSelectedItems(new Set())
    } else {
      setSelectedItems(new Set(sortedHistory.map(item => item.id)))
    }
  }

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'chat':
        return <User className="h-4 w-4" />
      case 'skill_call':
        return <Clock className="h-4 w-4" />
      case 'envelope':
        return <Filter className="h-4 w-4" />
      case 'model':
        return <Calendar className="h-4 w-4" />
      default:
        return <Calendar className="h-4 w-4" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-600 dark:text-green-400'
      case 'error':
        return 'text-red-600 dark:text-red-400'
      case 'pending':
        return 'text-yellow-600 dark:text-yellow-400'
      default:
        return 'text-muted-foreground'
    }
  }

  const formatDate = (timestamp: string) => {
    const date = new Date(timestamp)
    const now = new Date()
    const diff = now.getTime() - date.getTime()
    const minutes = Math.floor(diff / 60000)
    const hours = Math.floor(minutes / 60)
    const days = Math.floor(hours / 24)

    if (days > 0) {
      return `${days}天前`
    } else if (hours > 0) {
      return `${hours}小时前`
    } else if (minutes > 0) {
      return `${minutes}分钟前`
    } else {
      return '刚刚'
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="mb-8">
          <h1 className="text-3xl font-bold mb-2">历史记录</h1>
          <p className="text-muted-foreground">查看和管理您的设计历史</p>
        </div>

        <div className="flex flex-col gap-6">
          <div className="rounded-lg border bg-card p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold">筛选和搜索</h2>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleExport}
                  className="px-3 py-2 rounded-md border border-input bg-background hover:bg-accent transition-colors"
                >
                  <Download className="h-4 w-4 mr-2" />
                  导出
                </button>
                <button
                  onClick={handleClearAll}
                  className="px-3 py-2 rounded-md border border-input bg-background hover:bg-destructive/10 hover:text-destructive transition-colors"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  清除全部
                </button>
              </div>
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
              <div>
                <label className="block text-sm font-medium mb-2">类型</label>
                <select
                  value={filterType}
                  onChange={(e) => setFilterType(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                >
                  <option value="all">全部类型</option>
                  <option value="chat">聊天记录</option>
                  <option value="skill_call">SKILL调用</option>
                  <option value="envelope">包络图</option>
                  <option value="model">3D模型</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">状态</label>
                <select
                  value={filterStatus}
                  onChange={(e) => setFilterStatus(e.target.value)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                >
                  <option value="all">全部状态</option>
                  <option value="success">成功</option>
                  <option value="error">错误</option>
                  <option value="pending">进行中</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">排序</label>
                <select
                  value={sortBy}
                  onChange={(e) => setSortBy(e.target.value as any)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                >
                  <option value="timestamp">按时间</option>
                  <option value="type">按类型</option>
                  <option value="status">按状态</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">排序顺序</label>
                <select
                  value={sortOrder}
                  onChange={(e) => setSortOrder(e.target.value as any)}
                  className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
                >
                  <option value="desc">降序</option>
                  <option value="asc">升序</option>
                </select>
              </div>
            </div>

            <div className="relative">
              <Search className="absolute left-3 top-1/2 h-4 w-4 text-muted-foreground" />
              <input
                type="text"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="搜索历史记录..."
                className="w-full rounded-md border border-input bg-background pl-10 pr-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
              />
            </div>
          </div>

          {sortedHistory.length > 0 && (
            <div className="rounded-lg border bg-card p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">
                  历史记录 ({sortedHistory.length})
                </h2>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleSelectAll}
                    className="px-3 py-2 rounded-md border border-input bg-background hover:bg-accent transition-colors"
                  >
                    {selectedItems.size === sortedHistory.length ? '取消全选' : '全选'}
                  </button>
                  {selectedItems.size > 0 && (
                    <button
                      onClick={handleDeleteSelected}
                      className="px-3 py-2 rounded-md border border-input bg-background hover:bg-destructive/10 hover:text-destructive transition-colors"
                    >
                      <Trash2 className="h-4 w-4 mr-2" />
                      删除选中 ({selectedItems.size})
                    </button>
                  )}
                </div>
              </div>

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b bg-muted/50">
                      <th className="px-4 py-3 text-left text-sm font-medium">
                        <input
                          type="checkbox"
                          checked={selectedItems.size === sortedHistory.length}
                          onChange={handleSelectAll}
                          className="mr-2"
                        />
                        操作
                      </th>
                      <th className="px-4 py-3 text-left text-sm font-medium">类型</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">标题</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">描述</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">时间</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">状态</th>
                      <th className="px-4 py-3 text-left text-sm font-medium">操作</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sortedHistory.map((item) => (
                      <tr
                        key={item.id}
                        className={`border-b hover:bg-muted/50 transition-colors ${
                          selectedItems.has(item.id) ? 'bg-muted/30' : ''
                        }`}
                      >
                        <td className="px-4 py-3 text-sm">
                          <input
                            type="checkbox"
                            checked={selectedItems.has(item.id)}
                            onChange={(e) => {
                              const newSelected = new Set(selectedItems)
                              if (e.target.checked) {
                                newSelected.add(item.id)
                              } else {
                                newSelected.delete(item.id)
                              }
                              setSelectedItems(newSelected)
                            }}
                            className="mr-2"
                          />
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <div className="flex items-center gap-2">
                            {getTypeIcon(item.type)}
                            <span className="capitalize">{item.type.replace('_', ' ')}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm font-medium">{item.title}</td>
                        <td className="px-4 py-3 text-sm text-muted-foreground max-w-xs truncate">
                          {item.description}
                        </td>
                        <td className="px-4 py-3 text-sm text-muted-foreground">
                          {formatDate(item.timestamp)}
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <span className={getStatusColor(item.status)}>
                            {item.status === 'success' ? '成功' : item.status === 'error' ? '错误' : '进行中'}
                          </span>
                        </td>
                        <td className="px-4 py-3 text-sm">
                          <button
                            onClick={() => handleDelete(item.id)}
                            className="p-1 hover:bg-destructive/10 rounded transition-colors text-destructive"
                            title="删除"
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {sortedHistory.length === 0 && (
            <div className="rounded-lg border bg-card p-12 text-center">
              <div className="text-center">
                <Filter className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">没有找到匹配的记录</h3>
                <p className="text-muted-foreground mb-4">
                  请尝试调整筛选条件或搜索关键词
                </p>
                <button
                  onClick={() => {
                    setFilterType('all')
                    setFilterStatus('all')
                    setSearchText('')
                  }}
                  className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-colors"
                >
                  清除筛选
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
