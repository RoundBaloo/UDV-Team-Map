import React, { useRef, useState } from 'react';
import { uploadAvatarWithModeration } from '../../../utils/uploadHelpers';
import './AvatarUpload.css';

const AvatarUpload = ({ 
  currentAvatar, 
  onAvatarChange, 
  disabled = false,
  moderationStatus = null,
  onUploadStart,
  onUploadSuccess,
  onUploadError,
}) => {
  const fileInputRef = useRef();
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);

  const handleFileSelect = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      alert('Пожалуйста, выберите изображение');
      return;
    }

    if (file.size > 5 * 1024 * 1024) {
      alert('Размер файла не должен превышать 5MB');
      return;
    }

    // Локальный preview
    const reader = new FileReader();
    reader.onload = (e) => setPreviewUrl(e.target.result);
    reader.readAsDataURL(file);

    await uploadFile(file);
  };

  const uploadFile = async (file) => {
    setUploading(true);
    setUploadProgress(0);
    onUploadStart?.();

    try {
      const result = await uploadAvatarWithModeration(file, setUploadProgress);
      
      onUploadSuccess?.(result.moderation);
      
      // Пробуем использовать publicUrl
      if (result.publicUrl) {
        console.log('Setting preview to publicUrl:', result.publicUrl);
        setPreviewUrl(result.publicUrl);
      }
      
    } catch (error) {
      console.error('Upload failed:', error);
      onUploadError?.(error.message);
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const handleAvatarClick = () => {
    if (!disabled && !uploading) {
      fileInputRef.current?.click();
    }
  };

  const getStatusText = () => {
    if (uploading) return `Загрузка... ${uploadProgress}%`;
    if (moderationStatus === 'pending') return 'На модерации';
    if (moderationStatus === 'rejected') return 'Фото отклонено';
    return null;
  };

  const displayAvatar = previewUrl || currentAvatar;

  return (
    <div className="avatar-upload">
      <div className="avatar-upload__preview" onClick={handleAvatarClick}>
        {displayAvatar ? (
          <img 
            src={displayAvatar} 
            alt="Аватар"
            className="avatar-upload__image"
            onError={() => console.error('Image load failed for:', displayAvatar)}
          />
        ) : (
          <div className="avatar-upload__placeholder">📷</div>
        )}
        
        {uploading && (
          <div className="avatar-upload__progress">
            <div className="avatar-upload__progress-bar" style={{ width: `${uploadProgress}%` }} />
          </div>
        )}
        
        {!disabled && !uploading && (
          <div className="avatar-upload__overlay">
            <span>Изменить фото</span>
          </div>
        )}
      </div>

      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileSelect}
        style={{ display: 'none' }}
        disabled={disabled || uploading}
      />

      {getStatusText() && (
        <div className="avatar-upload__status">{getStatusText()}</div>
      )}
    </div>
  );
};

export default AvatarUpload;