import React, { useState } from 'react';
import './AdminTable.css';

const AdminTable = ({ 
  data, 
  columns, 
  onEdit, 
  renderActions, 
  loading = false,
  selectable = false,
}) => {
  const [selectedRows, setSelectedRows] = useState(new Set());
  const [sortConfig, setSortConfig] = useState({ key: null, direction: 'asc' });

  const handleSort = (key) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleSelectAll = (e) => {
    if (e.target.checked) {
      setSelectedRows(new Set(data.map(item => item.id)));
    } else {
      setSelectedRows(new Set());
    }
  };

  const handleSelectRow = (id) => {
    const newSelected = new Set(selectedRows);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    setSelectedRows(newSelected);
  };

  const sortedData = React.useMemo(() => {
    if (!sortConfig.key) return data;

    return [...data].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, sortConfig]);

  // Функция рендеринга действий по умолчанию
  const defaultRenderActions = (row) => {
    return (
      <button
        className="btn btn-primary btn-sm"
        onClick={() => onEdit?.(row)}
        title="Редактировать"
      >
        ✏️
      </button>
    );
  };

  // Используем кастомный рендеринг или рендеринг по умолчанию
  const getActionsRenderer = () => {
    return renderActions || defaultRenderActions;
  };

  if (loading) {
    return (
      <div className="admin-table-loading">
        <div className="loading-spinner">Загрузка данных...</div>
      </div>
    );
  }

  return (
    <div className="admin-table">

      <div className="admin-table__container">
        <table className="admin-table__table">
          <thead>
            <tr>
              {selectable && (
                <th className="admin-table__checkbox-cell">
                  <input
                    type="checkbox"
                    onChange={handleSelectAll}
                    checked={selectedRows.size === data.length && data.length > 0}
                  />
                </th>
              )}
              {columns.map(column => (
                <th 
                  key={column.key}
                  className={`admin-table__header ${column.sortable ? 'admin-table__header--sortable' : ''}`}
                  onClick={() => column.sortable && handleSort(column.key)}
                  style={{ width: column.width }}
                >
                  <div className="admin-table__header-content">
                    {column.title}
                    {column.sortable && (
                      <span className="admin-table__sort-indicator">
                        {sortConfig.key === column.key && (
                          sortConfig.direction === 'asc' ? '↑' : '↓'
                        )}
                      </span>
                    )}
                  </div>
                </th>
              ))}
              <th className="admin-table__actions-cell">Действия</th>
            </tr>
          </thead>
          <tbody>
            {sortedData.map(row => (
              <tr key={row.id} className="admin-table__row">
                {selectable && (
                  <td className="admin-table__checkbox-cell">
                    <input
                      type="checkbox"
                      checked={selectedRows.has(row.id)}
                      onChange={() => handleSelectRow(row.id)}
                    />
                  </td>
                )}
                {columns.map(column => (
                  <td key={column.key} className="admin-table__cell">
                    {column.render ? column.render(row[column.key], row) : row[column.key]}
                  </td>
                ))}
                <td className="admin-table__actions-cell">
                  {getActionsRenderer()(row)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {data.length === 0 && (
          <div className="admin-table__empty">
            Нет данных для отображения
          </div>
        )}
      </div>
    </div>
  );
};

export default AdminTable;