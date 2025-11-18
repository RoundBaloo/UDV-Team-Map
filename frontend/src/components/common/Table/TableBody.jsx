import React from 'react';
import TableRow from './TableRow';

const TableBody = ({ 
  data, 
  columns, 
  selectable, 
  selectedRows, 
  onSelectRow, 
  renderRowActions,
}) => {
  return (
    <tbody>
      {data.map(row => (
        <TableRow
          key={row.id}
          row={row}
          columns={columns}
          selectable={selectable}
          isSelected={selectedRows.has(row.id)}
          onSelect={onSelectRow}
          renderRowActions={renderRowActions}
        />
      ))}
    </tbody>
  );
};

export default TableBody;