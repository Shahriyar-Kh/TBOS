// ============================================================
// components/common/ConfirmDialog.tsx
// ============================================================
"use client";

import { AlertTriangle, Trash2, Archive, CheckCircle } from "lucide-react";
import {
  Modal,
  ModalContent,
  ModalHeader,
  ModalTitle,
  ModalDescription,
  ModalFooter,
} from "@/components/ui/Modal";
import { Button } from "@/components/ui/Button";

type ConfirmVariant = "danger" | "warning" | "success";

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
  isLoading?: boolean;
  loadingText?: string;
}

const VARIANT_CONFIG: Record<
  ConfirmVariant,
  {
    icon: React.ReactNode;
    iconBg: string;
    confirmVariant: "destructive" | "default" | "success";
  }
> = {
  danger: {
    icon: <Trash2 className="h-6 w-6 text-red-500" />,
    iconBg: "bg-red-100 dark:bg-red-950/30",
    confirmVariant: "destructive",
  },
  warning: {
    icon: <AlertTriangle className="h-6 w-6 text-amber-500" />,
    iconBg: "bg-amber-100 dark:bg-amber-950/30",
    confirmVariant: "default",
  },
  success: {
    icon: <CheckCircle className="h-6 w-6 text-emerald-500" />,
    iconBg: "bg-emerald-100 dark:bg-emerald-950/30",
    confirmVariant: "success",
  },
};

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "danger",
  isLoading = false,
  loadingText = "Processing…",
}: ConfirmDialogProps) {
  const config = VARIANT_CONFIG[variant];

  return (
    <Modal open={open} onOpenChange={(v) => !v && onClose()}>
      <ModalContent className="max-w-md">
        <ModalHeader>
          <div
            className={`mb-3 flex h-12 w-12 items-center justify-center rounded-xl ${config.iconBg}`}
          >
            {config.icon}
          </div>
          <ModalTitle>{title}</ModalTitle>
          <ModalDescription>{description}</ModalDescription>
        </ModalHeader>
        <ModalFooter>
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            {cancelLabel}
          </Button>
          <Button
            variant={config.confirmVariant}
            onClick={onConfirm}
            isLoading={isLoading}
            loadingText={loadingText}
          >
            {confirmLabel}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}
