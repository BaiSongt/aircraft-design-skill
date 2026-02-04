import { useState, useMemo } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown, Filter, Download, Trash2, Search } from 'lucide-react'

export interface TableColumn {
  key: string
  title: string
  sortable?: boolean
  filterable?: boolean
  render?: (value: any, row: any) => React.ReactNode
}

export interface ResultTableProps {
  data: any[]
  columns: TableColumn[]
  onRowClick?: (row: any) => void
  onExport?: () => void
  onDelete?: (row: any) => void
  pageSize?: number
}

export function ResultTable({
  data,
  columns,
  onRowClick,
  onExport,
  onDelete,
  pageSize = 10,
}: ResultTableProps) {
  const [sortColumn, setSortColumn] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc')
  const [filterText, setFilterText] = useState('')
  const [currentPage, setCurrentPage] = useState(1)

  const filteredAndSortedData = useMemo(() => {
    let result = [...data]

    if (filterText) {
      result = result.filter(row =>
        columns.some(column => {
          const value = row[column.key]
          return String(value).toLowerCase().includes(filterText.toLowerCase())
        })
      )
    }

    if (sortColumn) {
      result.sort((a, b) => {
        const aValue = a[sortColumn]
        const bValue = b[sortColumn]

        if (typeof aValue === 'number' && typeof bValue === 'number') {
          return sortDirection === 'asc' ? aValue - bValue : bValue - aValue
        }

        const aString = String(aValue).toLowerCase()
        const bString = String(bValue).toLowerCase()

        if (sortDirection === 'asc') {
          return aString.localeCompare(bString)
        } else {
          return bString.localeCompare(aString)
        }
      })
    }

    return result
  }, [data, sortColumn, sortDirection, filterText, columns])

  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * pageSize
    return filteredAndSortedData.slice(startIndex, startIndex + pageSize)
  }, [filteredAndSortedData, currentPage, pageSize])

  const totalPages = Math.ceil(filteredAndSortedData.length / pageSize)

  const handleSort = (column: TableColumn) => {
    if (!column.sortable) return

    if (sortColumn === column.key) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc')
    } else {
      setSortColumn(column.key)
      setSortDirection('asc')
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handleExport = () => {
    if (onExport) {
      onExport()
    }
  }

  const handleDelete = (row: any) => {
    if (onDelete) {
      onDelete(row)
    }
  }

  const renderSortIcon = (column: TableColumn) => {
    if (sortColumn !== column.key) {
      return <ArrowUpDown className="h-4 w-4 ml-2" />
    }

    return sortDirection === 'asc' ? (
      <ArrowUp className="h-4 w-4 ml-2" />
    ) : (
      <ArrowDown className="h-4 w-4 ml-2" />
    )
  }

  const renderCell = (column: TableColumn, row: any) => {
    if (column.render) {
      return column.render(row[column.key], row)
    }

    const value = row[column.key]

    if (typeof value === 'number') {
      return <span className="font-mono">{value.toFixed(2)}</span>
    }

    if (typeof value === 'boolean') {
      return value ? '是' : '否'
    }

    return String(value)
  }

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              value={filterText}
              onChange={(e) => setFilterText(e.target.value)}
              placeholder="搜索..."
              className="pl-10 pr-4 py-2 rounded-md border border-input bg-background text-sm focus:outline-none focus:ring-2 focus:ring-slate-950"
            />
          </div>
          <div className="text-sm text-muted-foreground">
            共 {filteredAndSortedData.length} 条记录
          </div>
        </div>
        <div className="flex items-center gap-2">
          {onExport && (
            <button
              onClick={handleExport}
              className="px-3 py-2 rounded-md border border-input bg-background hover:bg-accent transition-colors"
            >
              <Download className="h-4 w-4" />
            </button>
          )}
        </div>
      </div>

      <div className="overflow-x-auto border rounded-lg">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              {columns.map((column) => (
                <th
                  key={column.key}
                  onClick={() => column.sortable && handleSort(column)}
                  className={`px-4 py-3 text-left text-sm font-medium ${
                    column.sortable ? 'cursor-pointer hover:bg-muted' : ''
                  }`}
                >
                  <div className="flex items-center gap-2">
                    {column.title}
                    {column.sortable && renderSortIcon(column)}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedData.map((row, index) => (
              <tr
                key={index}
                onClick={() => onRowClick && onRowClick(row)}
                className={`border-b hover:bg-muted/50 transition-colors ${
                  onRowClick ? 'cursor-pointer' : ''
                }`}
              >
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-3 text-sm">
                    {renderCell(column, row)}
                  </td>
                ))}
                {onDelete && (
                  <td className="px-4 py-3 text-sm">
                    <button
                      onClick={(e) => {
                        e.stopPropagation()
                        handleDelete(row)
                      }}
                      className="p-1 hover:bg-destructive/10 rounded transition-colors"
                    >
                      <Trash2 className="h-4 w-4 text-destructive" />
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-center gap-2 mt-4">
          <button
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            className="px-3 py-2 rounded-md border border-input bg-background hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            上一页
          </button>
          <div className="flex items-center gap-1">
            {Array.from({ length: totalPages }, (_, i) => (
              <button
                key={i}
                onClick={() => handlePageChange(i + 1)}
                className={`px-3 py-2 rounded-md border border-input transition-colors ${
                  currentPage === i + 1
                    ? 'bg-primary text-primary-foreground'
                    : 'bg-background hover:bg-accent'
                }`}
              >
                {i + 1}
              </button>
            ))}
          </div>
          <button
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            className="px-3 py-2 rounded-md border border-input bg-background hover:bg-accent disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            下一页
          </button>
        </div>
      )}

      {paginatedData.length === 0 && (
        <div className="flex items-center justify-center py-12 text-muted-foreground">
          <div className="text-center">
            <Filter className="h-12 w-12 mx-auto mb-4" />
            <p className="text-lg font-medium mb-2">没有找到匹配的记录</p>
            <p className="text-sm">请尝试调整搜索条件</p>
          </div>
        </div>
      )}
    </div>
  )
}
