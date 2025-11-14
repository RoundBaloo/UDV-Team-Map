import './Alert.css';

const Alert = ({ type = 'info', message, onClose }) => {
  if (!message) return null;

  return (
    <div className={`alert alert--${type}`}>
      <div className="alert__content">
        <span className="alert__message">{message}</span>
        {onClose && (
          <button 
            className="alert__close"
            onClick={onClose}
            aria-label="Закрыть"
          >
            ×
          </button>
        )}
      </div>
    </div>
  );
};

export default Alert;