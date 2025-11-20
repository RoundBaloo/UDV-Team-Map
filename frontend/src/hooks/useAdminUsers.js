import { useState, useEffect } from 'react';
import { mockEmployee, mockCurrentUser, mockEmployeesByUnit } from '../utils/mockData';

export const useAdminUsers = () => {
  const [state, setState] = useState({
    users: [],
    loading: true,
    editingId: null,
    editedUser: {},
  });

  useEffect(() => {
    loadUsers();
  }, []);

  const loadUsers = async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const allUsers = [mockEmployee, mockCurrentUser];
      Object.values(mockEmployeesByUnit).forEach(unitUsers => {
        allUsers.push(...unitUsers);
      });
      
      const uniqueUsers = allUsers.filter((user, index, self) => 
        index === self.findIndex(u => u.id === user.id)
      );
      
      setState(prev => ({ ...prev, users: uniqueUsers, loading: false }));
    } catch (error) {
      console.error('Error loading users:', error);
      setState(prev => ({ ...prev, loading: false }));
    }
  };

  const handleEdit = user => {
    setState(prev => ({
      ...prev,
      editingId: user.id,
      editedUser: {
        ...user,
        work_city: user.work_city || '',
        work_format: user.work_format || 'office',
        grade: user.grade || '',
      },
    }));
  };

  const handleSave = id => {
    setState(prev => ({
      ...prev,
      users: prev.users.map(user => 
        user.id === id ? { ...user, ...prev.editedUser } : user
      ),
      editingId: null,
      editedUser: {},
    }));
  };

  const handleCancel = () => {
    setState(prev => ({
      ...prev,
      editingId: null,
      editedUser: {},
    }));
  };

  const handleFieldChange = (field, value) => {
    setState(prev => ({
      ...prev,
      editedUser: { ...prev.editedUser, [field]: value },
    }));
  };

  return {
    ...state,
    handleEdit,
    handleSave,
    handleCancel,
    handleFieldChange,
  };
};