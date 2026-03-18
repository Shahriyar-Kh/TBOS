import type { ReactNode } from "react";
import { buttonVariants } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { cn } from "@/lib/utils";

interface AppDropdownItem {
  label: string;
  onClick: () => void;
}

interface AppDropdownProps {
  triggerLabel: string;
  items: AppDropdownItem[];
  triggerIcon?: ReactNode;
}

export function AppDropdown({ triggerLabel, triggerIcon, items }: AppDropdownProps) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger className={cn(buttonVariants({ variant: "outline" }), "gap-2") }>
        {triggerIcon}
        {triggerLabel}
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end">
        {items.map((item) => (
          <DropdownMenuItem key={item.label} onClick={item.onClick}>
            {item.label}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
