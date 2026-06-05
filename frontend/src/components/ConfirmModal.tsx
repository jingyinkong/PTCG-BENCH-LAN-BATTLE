import { useTranslation } from 'react-i18next';

interface ConfirmModalProps {
  isOpen: boolean;
  title: string;
  message: string;
  confirmLabel?: string;
  cancelLabel?: string;
  confirmVariant?: 'danger' | 'primary';
  onConfirm: () => void;
  onCancel: () => void;
}

export default function ConfirmModal({
  isOpen,
  title,
  message,
  confirmLabel,
  cancelLabel,
  confirmVariant = 'primary',
  onConfirm,
  onCancel,
}: ConfirmModalProps) {
  const { t } = useTranslation(['common']);
  const finalConfirmLabel = confirmLabel ?? t('common:button.confirm');
  const finalCancelLabel = cancelLabel ?? t('common:button.cancel');
  if (!isOpen) return null;

  const confirmClasses = confirmVariant === 'danger'
    ? 'bg-red-600 hover:bg-red-500 text-white'
    : 'bg-sky-600 hover:bg-sky-500 text-white';

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm">
      <div className="bg-slate-900 border border-slate-600 rounded-xl p-6 max-w-sm w-full mx-4 text-center shadow-2xl">
        <div className="w-12 h-12 mx-auto mb-4 rounded-full bg-amber-500/20 flex items-center justify-center">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none"
            stroke="#f59e0b" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="12" cy="12" r="10" />
            <line x1="12" y1="8" x2="12" y2="12" />
            <line x1="12" y1="16" x2="12.01" y2="16" />
          </svg>
        </div>
        <h3 className="text-lg font-bold text-slate-50 mb-2">{title}</h3>
        <p className="text-slate-400 text-sm mb-6">{message}</p>
        <div className="flex gap-3">
          <button
            onClick={onCancel}
            className="flex-1 px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-lg font-semibold text-sm transition-colors"
          >
            {finalCancelLabel}
          </button>
          <button
            onClick={onConfirm}
            className={`flex-1 px-4 py-2 rounded-lg font-semibold text-sm transition-colors ${confirmClasses}`}
          >
            {finalConfirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
