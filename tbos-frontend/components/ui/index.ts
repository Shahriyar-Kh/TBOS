// ============================================================
// components/ui/index.ts — Barrel exports for all UI components
// Import from "@/components/ui" instead of individual files
// ============================================================

export { Avatar, AvatarImage, AvatarFallback } from "./Avatar";
export { Badge, badgeVariants } from "./Badge";
export { Button, buttonVariants } from "./Button";
export type { ButtonProps } from "./Button";
export {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "./Card";
export {
  Dropdown,
  DropdownTrigger,
  DropdownContent,
  DropdownItem,
  DropdownLabel,
  DropdownSeparator,
  DropdownGroup,
  DropdownPortal,
  DropdownSub,
  DropdownSubContent,
  DropdownSubTrigger,
  DropdownRadioGroup,
} from "./Dropdown";
export { Input } from "./Input";
export type { InputProps } from "./Input";
export {
  Modal,
  ModalTrigger,
  ModalContent,
  ModalHeader,
  ModalFooter,
  ModalTitle,
  ModalDescription,
  ModalClose,
} from "./Modal";
export { Progress } from "./Progress";
export {
  Select,
  SelectGroup,
  SelectValue,
  SelectTrigger,
  SelectContent,
  SelectLabel,
  SelectItem,
  SelectSeparator,
} from "./Select";
export { Tabs, TabsList, TabsTrigger, TabsContent } from "./Tabs";
export { Textarea } from "./Textarea";
export type { TextareaProps } from "./Textarea";
export { Skeleton } from "./Badge"; // Skeleton exported from Badge.tsx
