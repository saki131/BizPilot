'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Home, FileText, Package, Settings, LogOut } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export function MobileNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);

  const handleLogout = async () => {
    await apiClient.logout();
    router.push('/login');
  };

  const navItems = [
    { icon: Home, label: 'ホーム', path: '/dashboard' },
    { icon: FileText, label: '請求書', path: '/invoices' },
    { icon: Package, label: '納品書', path: '/delivery-notes' },
    { icon: Settings, label: 'マスタ', path: '/masters' },
  ];

  if (pathname === '/login') return null;

  return (
    <>
      <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-50 md:hidden">
        <div className="flex justify-around items-center h-16">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = pathname === item.path;
            return (
              <button
                key={item.path}
                onClick={() => router.push(item.path)}
                className={`flex flex-col items-center justify-center flex-1 h-full space-y-1 ${
                  isActive ? 'text-blue-600 font-semibold' : 'text-gray-600'
                }`}
              >
                <Icon className="w-6 h-6" />
                <span className="text-xs font-medium">{item.label}</span>
              </button>
            );
          })}
          <button
            onClick={() => setShowLogoutDialog(true)}
            className="flex flex-col items-center justify-center flex-1 h-full space-y-1 text-gray-600"
          >
            <LogOut className="w-6 h-6" />
            <span className="text-xs font-medium">終了</span>
          </button>
        </div>
      </nav>

      <Dialog open={showLogoutDialog} onOpenChange={setShowLogoutDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>ログアウト</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 pt-4">
            <p>ログアウトしてもよろしいですか？</p>
            <div className="flex gap-2">
              <Button
                variant="destructive"
                onClick={handleLogout}
                className="flex-1"
              >
                ログアウト
              </Button>
              <Button
                variant="outline"
                onClick={() => setShowLogoutDialog(false)}
                className="flex-1"
              >
                キャンセル
              </Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
