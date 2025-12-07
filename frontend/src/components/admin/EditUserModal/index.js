import React, { useState, useEffect } from 'react';
import { apiClient } from '../../../services/api/apiClient';
import { API_ENDPOINTS } from '../../../utils/constants';
import { WORK_FORMAT_OPTIONS } from '../../../utils/adminUsersConfig';
import './EditUserModal.css';


const EditUserModal = ({ 
  userId, 
  isOpen, 
  onClose, 
  onSaveSuccess,
}) => {
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [formData, setFormData] = useState({
    is_blocked: false,
    skill1: '',
    skill1Level: '',
    skill2: '',
    skill2Level: '',
    skill3: '',
    skill3Level: '',
    work_format: 'office',
  });

  // Загружаем данные пользователя при открытии модалки
  useEffect(() => {
    if (isOpen && userId) {
      loadUserData();
    }
  }, [isOpen, userId]);

  const loadUserData = async () => {
    try {
      setLoading(true);
      const endpoint = API_ENDPOINTS.EMPLOYEES.DETAIL.replace('{employee_id}', userId);
      const data = await apiClient.get(endpoint);
      
      // Преобразуем skill_ratings в форму
      const skills = data.skill_ratings || {};
      const skillEntries = Object.entries(skills);
      
      setFormData({
        is_blocked: data.is_blocked || false,
        skill1: skillEntries[0]?.[0] || '',
        skill1Level: skillEntries[0]?.[1]?.toString() || '',
        skill2: skillEntries[1]?.[0] || '',
        skill2Level: skillEntries[1]?.[1]?.toString() || '',
        skill3: skillEntries[2]?.[0] || '',
        skill3Level: skillEntries[2]?.[1]?.toString() || '',
        work_format: data.work_format || 'office',
      });
    } catch (error) {
      console.error('Error loading user data:', error);
      alert('Ошибка загрузки данных пользователя');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      
      // Формируем данные для отправки
      const updateData = {};
      
      // Добавляем поле только если оно есть
      if (formData.work_format) {
        updateData.work_format = formData.work_format;
      }
      
      updateData.is_blocked = formData.is_blocked;
      
      // Формируем skill_ratings
      const skillRatings = {};
      
      if (formData.skill1.trim()) {
        const level = parseInt(formData.skill1Level);
        if (level >= 1 && level <= 5) {
          skillRatings[formData.skill1] = level;
        }
      }
      if (formData.skill2.trim()) {
        const level = parseInt(formData.skill2Level);
        if (level >= 1 && level <= 5) {
          skillRatings[formData.skill2] = level;
        }
      }
      if (formData.skill3.trim()) {
        const level = parseInt(formData.skill3Level);
        if (level >= 1 && level <= 5) {
          skillRatings[formData.skill3] = level;
        }
      }
      
      if (Object.keys(skillRatings).length > 0) {
        updateData.skill_ratings = skillRatings;
      }
      
      const endpoint = API_ENDPOINTS.EMPLOYEES.DETAIL.replace('{employee_id}', userId);
      await apiClient.patch(endpoint, updateData);
      
      onSaveSuccess();
      onClose();
    } catch (error) {
      console.error('Error saving user:', error);
      alert('Ошибка сохранения: ' + error.message);
    } finally {
      setSaving(false);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="modal-header">
          <h2>Редактирование пользователя</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>
        
        <div className="modal-body">
          {loading ? (
            <div className="loading">Загрузка данных пользователя...</div>
          ) : (
            <div className="simple-form">
              {/* Заблокирован? */}
              <div className="form-group checkbox-group">
                <label className="checkbox-label">
                  <input
                    type="checkbox"
                    name="is_blocked"
                    checked={formData.is_blocked}
                    onChange={handleInputChange}
                  />
                  <span>Заблокирован?</span>
                </label>
              </div>
              
              {/* Навыки */}
              <div className="form-group">
                <h3 className="section-title">Навыки:</h3>
                
                <div className="skill-row">
                  <div className="skill-input-group">
                    <input
                      type="text"
                      name="skill1"
                      placeholder="Навык 1"
                      value={formData.skill1}
                      onChange={handleInputChange}
                      className="skill-input"
                    />
                    <input
                      type="number"
                      name="skill1Level"
                      placeholder="Уровень (1-5)"
                      min="1"
                      max="5"
                      value={formData.skill1Level}
                      onChange={handleInputChange}
                      className="skill-level-input"
                    />
                  </div>
                </div>
                
                <div className="skill-row">
                  <div className="skill-input-group">
                    <input
                      type="text"
                      name="skill2"
                      placeholder="Навык 2"
                      value={formData.skill2}
                      onChange={handleInputChange}
                      className="skill-input"
                    />
                    <input
                      type="number"
                      name="skill2Level"
                      placeholder="Уровень (1-5)"
                      min="1"
                      max="5"
                      value={formData.skill2Level}
                      onChange={handleInputChange}
                      className="skill-level-input"
                    />
                  </div>
                </div>
                
                <div className="skill-row">
                  <div className="skill-input-group">
                    <input
                      type="text"
                      name="skill3"
                      placeholder="Навык 3"
                      value={formData.skill3}
                      onChange={handleInputChange}
                      className="skill-input"
                    />
                    <input
                      type="number"
                      name="skill3Level"
                      placeholder="Уровень (1-5)"
                      min="1"
                      max="5"
                      value={formData.skill3Level}
                      onChange={handleInputChange}
                      className="skill-level-input"
                    />
                  </div>
                </div>
              </div>
              
              {/* Формат работы */}
              <div className="form-group">
                <h3 className="section-title">Формат работы:</h3>
                <select
                  name="work_format"
                  value={formData.work_format}
                  onChange={handleInputChange}
                  className="work-format-select"
                >
                  {WORK_FORMAT_OPTIONS.map(option => (
                    <option key={option.value} value={option.value}>
                      {option.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}
        </div>
        
        <div className="modal-footer">
          <button 
            className="btn btn-secondary" 
            onClick={onClose}
            disabled={saving}
          >
            Закрыть
          </button>
          <button 
            className="btn btn-primary" 
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? 'Сохранение...' : 'Сохранить'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default EditUserModal;