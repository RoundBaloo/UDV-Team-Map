import React from 'react';
import TableHeader from './TableHeader';
import TableBody from './TableBody';
import TableLoading from './TableLoading';
import TableEmpty from './TableEmpty';
import './Table.css';

const Table = ({ 
  data, 
  columns, 
  loading = false,
  selectable = false,
  selectedRows = new Set(),
  onSelectAll,
  onSelectRow,
  sortConfig,
  onSort,
  renderRowActions,
}) => {
  if (loading) {
    return <TableLoading />;
  }

  return (
    <div className="table">
      <div className="table__container">
        <table className="table__table">
          <TableHeader
            columns={columns}
            sortConfig={sortConfig}
            onSort={onSort}
            selectable={selectable}
            onSelectAll={onSelectAll}
            data={data}
            selectedRows={selectedRows}
          />
          <TableBody
            data={data}
            columns={columns}
            selectable={selectable}
            selectedRows={selectedRows}
            onSelectRow={onSelectRow}
            renderRowActions={renderRowActions}
          />
        </table>
        {data.length === 0 && <TableEmpty />}
      </div>
    </div>
  );
};

export default Table;