import React, { useRef, useState } from 'react';
import { uploadAvatarWithModeration } from '../../../utils/uploadHelpers';
import './AvatarUpload.css';

const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5MB

const STATUS_TEXTS = {
  uploading: progress => `Загрузка... ${progress}%`,
  pending: 'На модерации',
  rejected: 'Фото отклонено',
};

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

  const handleFileSelect = async event => {
    const file = event.target.files[0];
    if (!file) return;

    const validationError = validateFile(file);
    if (validationError) {
      alert(validationError);
      return;
    }

    await showPreviewAndUpload(file);
  };

  const validateFile = file => {
    if (!file.type.startsWith('image/')) {
      return 'Пожалуйста, выберите изображение';
    }

    if (file.size > MAX_FILE_SIZE) {
      return 'Размер файла не должен превышать 5MB';
    }

    return null;
  };

  const showPreviewAndUpload = async file => {
    try {
      const preview = await createPreview(file);
      setPreviewUrl(preview);
      await uploadFile(file);
    } catch (error) {
      console.error('Preview creation failed:', error);
      onUploadError?.('Ошибка при создании превью');
    }
  };

  const createPreview = file => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader();
      reader.onload = e => resolve(e.target.result);
      reader.onerror = reject;
      reader.readAsDataURL(file);
    });
  };

  const uploadFile = async file => {
    setUploading(true);
    setUploadProgress(0);
    onUploadStart?.();

    try {
      const result = await uploadAvatarWithModeration(file, setUploadProgress);
      onUploadSuccess?.(result.moderation);
      
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
    if (uploading) return STATUS_TEXTS.uploading(uploadProgress);
    if (moderationStatus === 'pending') return STATUS_TEXTS.pending;
    if (moderationStatus === 'rejected') return STATUS_TEXTS.rejected;
    return null;
  };

  const displayAvatar = previewUrl || currentAvatar;

  return (
    <div className="avatar-upload">
      <AvatarPreview
        avatarUrl={displayAvatar}
        uploading={uploading}
        uploadProgress={uploadProgress}
        disabled={disabled}
        onClick={handleAvatarClick}
      />

      <HiddenFileInput
        ref={fileInputRef}
        onChange={handleFileSelect}
        disabled={disabled || uploading}
      />

      <UploadStatus statusText={getStatusText()} />
    </div>
  );
};

const AvatarPreview = ({
  avatarUrl,
  uploading,
  uploadProgress,
  disabled,
  onClick,
}) => {
  return (
    <div className="avatar-upload__preview" onClick={onClick}>
      {avatarUrl ? (
        <img 
          src={avatarUrl} 
          alt="Аватар"
          className="avatar-upload__image"
          onError={() => console.error('Image load failed for:', avatarUrl)}
        />
      ) : (
        <div className="avatar-upload__placeholder">📷</div>
      )}
      
      {uploading && (
        <div className="avatar-upload__progress">
          <div 
            className="avatar-upload__progress-bar" 
            style={{ width: `${uploadProgress}%` }} 
          />
        </div>
      )}
      
      {!disabled && !uploading && (
        <div className="avatar-upload__overlay">
          <span>Изменить фото</span>
        </div>
      )}
    </div>
  );
};

const HiddenFileInput = React.forwardRef(({ onChange, disabled }, ref) => (
  <input
    ref={ref}
    type="file"
    accept="image/*"
    onChange={onChange}
    style={{ display: 'none' }}
    disabled={disabled}
  />
));

const UploadStatus = ({ statusText }) => {
  if (!statusText) return null;

  return (
    <div className="avatar-upload__status">
      {statusText}
    </div>
  );
};

export default AvatarUpload;