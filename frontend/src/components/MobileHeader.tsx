'use client';

import { usePathname } from 'next/navigation';

interface MobileHeaderProps {
  title?: string;
}

export function MobileHeader({ title }: MobileHeaderProps) {
  const pathname = usePathname();

  const getTitle = () => {
    if (title) return title;
    switch (pathname) {
      case '/dashboard':
        return 'ダッシュボード';
      case '/invoices':
        return '請求書管理';
      case '/delivery-notes':
        return '納品書管理';
      case '/masters':
        return 'マスタ管理';
      default:
        return '請求書管理システム';
    }
  };

  if (pathname === '/login') return null;

  return (
    <header className="sticky top-0 z-40 bg-gradient-to-r from-blue-600 to-blue-500 text-white shadow-md">
      <div className="px-4 py-4">
        <h1 className="text-xl font-bold">{getTitle()}</h1>
      </div>
    </header>
  );
}
