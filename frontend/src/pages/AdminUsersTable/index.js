import React, { useState, useEffect } from 'react';
import Header from '../../components/common/Header';
import Breadcrumbs from '../../components/common/Breadcrumbs';
import AdminTable from '../../components/admin/AdminTable';
import { mockEmployee, mockCurrentUser, mockEmployeesByUnit } from '../../utils/mockData';
import './AdminUsersTable.css';

const AdminUsersTable = () => {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [editingId, setEditingId] = useState(null);
  const [editedUser, setEditedUser] = useState({});

  useEffect(() => {
    const loadUsers = async () => {
      try {
        // Имитация загрузки данных
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        // Собираем всех пользователей из моков
        const allUsers = [];
        
        // Добавляем базовых пользователей
        allUsers.push(mockEmployee, mockCurrentUser);
        
        // Добавляем пользователей из всех подразделений
        Object.values(mockEmployeesByUnit).forEach(unitUsers => {
          allUsers.push(...unitUsers);
        });
        
        // Убираем дубликаты по ID
        const uniqueUsers = allUsers.filter((user, index, self) => 
          index === self.findIndex(u => u.id === user.id)
        );
        
        setUsers(uniqueUsers);
      } catch (error) {
        console.error('Error loading users:', error);
      } finally {
        setLoading(false);
      }
    };

    loadUsers();
  }, []);

  const handleEdit = (user) => {
    setEditingId(user.id);
    setEditedUser({ 
      ...user,
      // Добавляем поля, которые могут редактироваться
      work_city: user.work_city || '',
      work_format: user.work_format || 'office',
      grade: user.grade || '',
    });
  };

  const handleSave = (id) => {
    setUsers(prevUsers => 
      prevUsers.map(user => 
        user.id === id ? { ...user, ...editedUser } : user
      )
    );
    setEditingId(null);
    setEditedUser({});
  };

  const handleCancel = () => {
    setEditingId(null);
    setEditedUser({});
  };

  const handleFieldChange = (field, value) => {
    setEditedUser(prev => ({
      ...prev,
      [field]: value,
    }));
  };

  // Функция для получения юридического лица по email
  const getLegalEntity = (email) => {
    if (!email) return '-';
    if (email.includes('trinitydata')) return 'ТриниДата';
    if (email.includes('vneocheredi')) return 'ВНЕ ОЧЕРЕДИ';
    if (email.includes('ft-soft')) return 'ФТ-СОФТ';
    if (email.includes('kit.ru')) return 'КИТ';
    if (email.includes('kit-r.ru')) return 'КИТ.Р';
    if (email.includes('cyberlimfa')) return 'Сайберлимфа';
    if (email.includes('vitrops')) return 'Витропс';
    if (email.includes('udv-group')) return 'UDV Group';
    return '-';
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
      render: (value, row) => {
        return getLegalEntity(row.email);
      },
    },
    {
      key: 'title',
      title: 'Должность',
      sortable: true,
      render: (value, row) => {
        return value || '-';
      },
    },
    {
      key: 'grade',
      title: 'Грейд',
      sortable: true,
      render: (value, row) => {
        if (editingId === row.id) {
          return (
            <select
              value={editedUser.grade || ''}
              onChange={(e) => handleFieldChange('grade', e.target.value)}
              className="inline-select"
            >
              <option value="">Не указан</option>
              <option value="Intern">Intern</option>
              <option value="Junior">Junior</option>
              <option value="Middle">Middle</option>
              <option value="Senior">Senior</option>
              <option value="Lead">Lead</option>
              <option value="Principal">Principal</option>
            </select>
          );
        }
        return value || 'Не указан';
      },
    },
    {
      key: 'work_city',
      title: 'Город',
      sortable: true,
      render: (value, row) => {
        if (editingId === row.id) {
          return (
            <input
              type="text"
              value={editedUser.work_city || ''}
              onChange={(e) => handleFieldChange('work_city', e.target.value)}
              className="inline-input"
              placeholder="Город"
            />
          );
        }
        return value || '-';
      },
    },
    {
      key: 'work_format',
      title: 'Формат работы',
      sortable: true,
      render: (value, row) => {
        if (editingId === row.id) {
          return (
            <select
              value={editedUser.work_format || 'office'}
              onChange={(e) => handleFieldChange('work_format', e.target.value)}
              className="inline-select"
            >
              <option value="office">Офис</option>
              <option value="hybrid">Гибрид</option>
              <option value="remote">Удаленно</option>
            </select>
          );
        }
        
        const formatMap = {
          'office': 'Офис',
          'hybrid': 'Гибрид', 
          'remote': 'Удаленно',
        };
        
        return formatMap[value] || value || '-';
      },
    },
  ];

  // Функция для рендеринга действий
  const renderActions = (row) => {
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
      {/* <Breadcrumbs /> */}
      
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