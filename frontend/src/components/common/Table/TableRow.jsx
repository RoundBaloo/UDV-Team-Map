import React from 'react';

const TableRow = ({ 
  row, 
  columns, 
  selectable, 
  isSelected, 
  onSelect, 
  renderRowActions,
}) => {
  return (
    <tr className="table__row">
      {selectable && (
        <td className="table__checkbox-cell">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onSelect(row.id)}
          />
        </td>
      )}
      {columns.map(column => (
        <td key={column.key} className="table__cell">
          {column.render ? column.render(row[column.key], row) : row[column.key]}
        </td>
      ))}
      <td className="table__actions-cell">
        {renderRowActions && renderRowActions(row)}
      </td>
    </tr>
  );
};

export default TableRow;