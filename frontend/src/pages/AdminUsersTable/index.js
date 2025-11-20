import React from 'react';
import Header from '../../components/common/Header';
import AdminTable from '../../components/admin/AdminTable';
import { useAdminUsers } from '../../hooks/useAdminUsers';
import { 
  getLegalEntity, 
  WORK_FORMAT_MAP, 
  GRADE_OPTIONS, 
  WORK_FORMAT_OPTIONS,
} from '../../utils/adminUsersConfig.js';
import './AdminUsersTable.css';

const AdminUsersTable = () => {
  const {
    users,
    loading,
    editingId,
    editedUser,
    handleEdit,
    handleSave,
    handleCancel,
    handleFieldChange,
  } = useAdminUsers();

  const getGradeCell = row => {
    if (editingId === row.id) {
      return (
        <select
          value={editedUser.grade || ''}
          onChange={e => handleFieldChange('grade', e.target.value)}
          className="inline-select"
        >
          {GRADE_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }
    return row.grade || 'Не указан';
  };

  const getWorkCityCell = row => {
    if (editingId === row.id) {
      return (
        <input
          type="text"
          value={editedUser.work_city || ''}
          onChange={e => handleFieldChange('work_city', e.target.value)}
          className="inline-input"
          placeholder="Город"
        />
      );
    }
    return row.work_city || '-';
  };

  const getWorkFormatCell = row => {
    if (editingId === row.id) {
      return (
        <select
          value={editedUser.work_format || 'office'}
          onChange={e => handleFieldChange('work_format', e.target.value)}
          className="inline-select"
        >
          {WORK_FORMAT_OPTIONS.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    }
    return WORK_FORMAT_MAP[row.work_format] || row.work_format || '-';
  };

  const columns = [
    {
      key: 'name',
      title: 'ФИО',
      sortable: true,
      render: (value, row) => {
        const fullName = `${row.last_name || ''} ${row.first_name || ''} ${row.middle_name || ''}`.trim();
        return <span title={fullName}>{fullName}</span>;
      },
    },
    {
      key: 'legal_entity',
      title: 'Юр лицо',
      sortable: true,
      render: (value, row) => getLegalEntity(row.email),
    },
    {
      key: 'title',
      title: 'Должность',
      sortable: true,
      render: value => value || '-',
    },
    {
      key: 'grade',
      title: 'Грейд',
      sortable: true,
      render: (value, row) => getGradeCell(row),
    },
    {
      key: 'work_city',
      title: 'Город',
      sortable: true,
      render: (value, row) => getWorkCityCell(row),
    },
    {
      key: 'work_format',
      title: 'Формат работы',
      sortable: true,
      render: (value, row) => getWorkFormatCell(row),
    },
  ];

  const renderActions = row => {
    if (editingId === row.id) {
      return (
        <div className="inline-actions">
          <button
            className="btn btn-success btn-sm"
            onClick={() => handleSave(row.id)}
            title="Сохранить"
          >
            ✅
          </button>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleCancel}
            title="Отмена"
          >
            ❌
          </button>
        </div>
      );
    }

    return (
      <button
        className="btn btn-primary btn-sm"
        onClick={() => handleEdit(row)}
        title="Редактировать"
      >
        ✏️
      </button>
    );
  };

  return (
    <div className="admin-users-page">
      <Header />
      
      <main className="admin-users-main">
        <div className="container">
          <div className="admin-users-header">
            <h1>Управление пользователями</h1>
            <div className="admin-users-stats">
              Всего пользователей: {users.length}
              {editingId && <span className="editing-notice"> • Редактирование</span>}
            </div>
          </div>

          <div className="admin-users-content">
            <AdminTable
              data={users}
              columns={columns}
              renderActions={renderActions}
              loading={loading}
              selectable={false}
            />
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminUsersTable;