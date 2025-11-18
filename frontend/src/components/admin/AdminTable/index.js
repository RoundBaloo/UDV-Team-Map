import React from 'react';
import Table, { useTableSelection, useTableSort } from '../../common/Table';
import './AdminTable.css';

const AdminTable = ({ 
  data, 
  columns, 
  onEdit, 
  renderActions, 
  loading = false,
  selectable = false,
}) => {
  const { selectedRows, handleSelectAll, handleSelectRow } = useTableSelection(data);
  const { sortedData, handleSort, sortConfig } = useTableSort(data);

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

  const actionsRenderer = renderActions || defaultRenderActions;

  return (
    <Table
      data={sortedData}
      columns={columns}
      loading={loading}
      selectable={selectable}
      selectedRows={selectedRows}
      onSelectAll={handleSelectAll}
      onSelectRow={handleSelectRow}
      sortConfig={sortConfig}
      onSort={handleSort}
      renderRowActions={actionsRenderer}
    />
  );
};

export default AdminTable;