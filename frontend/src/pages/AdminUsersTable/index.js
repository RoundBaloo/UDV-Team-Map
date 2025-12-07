// components/admin/AdminUsersTable.js
import React, { useState } from 'react';
import Header from '../../components/common/Header';
import AdminTable from '../../components/admin/AdminTable';
import EditUserModal from '../../components/admin/EditUserModal/index';
import { useAdminUsers } from '../../hooks/useAdminUsers';
import { 
  getLegalEntity, 
  WORK_FORMAT_MAP,
} from '../../utils/adminUsersConfig.js';
import './AdminUsersTable.css';

const AdminUsersTable = () => {
  const {
    users,
    loading,
    editingId,
    handleEdit,
    refreshUsers,
  } = useAdminUsers();

  const [modalOpen, setModalOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState(null);

  const handleEditClick = (row) => {
    handleEdit(row);
    setSelectedUserId(row.id);
    setModalOpen(true);
  };

  const handleModalClose = () => {
    setModalOpen(false);
    setSelectedUserId(null);
  };

  const handleSaveSuccess = () => {
    refreshUsers(); // Обновляем список после сохранения
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
      key: 'email',
      title: 'Email',
      sortable: true,
      render: (value, row) => {
        return (
          <a href={`mailto:${row.email}`} title={row.email}>
            {row.email}
          </a>
        );
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
      key: 'work_city',
      title: 'Город',
      sortable: true,
      render: (value, row) => row.work_city || '-',
    },
    {
      key: 'work_format',
      title: 'Формат работы',
      sortable: true,
      render: (value, row) => WORK_FORMAT_MAP[row.work_format] || row.work_format || '-',
    },
    {
      key: 'org_unit',
      title: 'Подразделение',
      sortable: true,
      render: (value, row) => row.org_unit?.name || '-',
    },
    {
      key: 'status',
      title: 'Статус',
      sortable: true,
      render: (value, row) => {
        if (row.is_blocked) return 'Заблокирован';
        return row.status === 'active' ? 'Активен' : (row.status || '-');
      },
    },
  ];

  const renderActions = row => {
    return (
      <button
        className="btn btn-primary btn-sm"
        onClick={() => handleEditClick(row)}
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
              <span>Всего пользователей: {users.length}</span>
              {loading && <span className="loading-indicator"> • Загрузка...</span>}
              <button 
                className="btn btn-secondary btn-sm" 
                onClick={refreshUsers}
                style={{ marginLeft: '10px' }}
              >
                Обновить
              </button>
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

      <EditUserModal
        userId={selectedUserId}
        isOpen={modalOpen}
        onClose={handleModalClose}
        onSaveSuccess={handleSaveSuccess}
      />
    </div>
  );
};

export default AdminUsersTable;