import { useState } from 'react';

export interface SidebarState {
  isCollapsed: boolean;
  width: number;
  toggleCollapse: () => void;
  setSidebarWidth: (w: number) => void;
}

export const useSidebarController = (): SidebarState => {
  const [isCollapsed, setIsCollapsed] = useState<boolean>(false);
  const [width, setWidth] = useState<number>(240);

  const toggleCollapse = () => setIsCollapsed(prev => !prev);
  const setSidebarWidth = (w: number) => {
    if (w >= 180 && w <= 400) setWidth(w);
  };

  return {
    isCollapsed,
    width: isCollapsed ? 72 : width,
    toggleCollapse,
    setSidebarWidth,
  };
};
