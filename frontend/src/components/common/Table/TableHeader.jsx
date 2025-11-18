import React from 'react';

const TableHeader = ({ 
  columns, 
  sortConfig, 
  onSort, 
  selectable, 
  onSelectAll, 
  data, 
  selectedRows,
}) => {
  return (
    <thead>
      <tr>
        {selectable && (
          <th className="table__checkbox-cell">
            <input
              type="checkbox"
              onChange={onSelectAll}
              checked={selectedRows.size === data.length && data.length > 0}
            />
          </th>
        )}
        {columns.map(column => (
          <th 
            key={column.key}
            className={`table__header ${column.sortable ? 'table__header--sortable' : ''}`}
            onClick={() => column.sortable && onSort(column.key)}
            style={{ width: column.width }}
          >
            <div className="table__header-content">
              {column.title}
              {column.sortable && (
                <span className="table__sort-indicator">
                  {sortConfig.key === column.key && (
                    sortConfig.direction === 'asc' ? '↑' : '↓'
                  )}
                </span>
              )}
            </div>
          </th>
        ))}
        <th className="table__actions-cell">Действия</th>
      </tr>
    </thead>
  );
};

export default TableHeader;