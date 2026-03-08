'use client';

import { usePathname, useRouter } from 'next/navigation';
import { Home, FileText, Package, Settings, LogOut, BarChart2, ShoppingCart } from 'lucide-react';
import { apiClient } from '@/lib/api';
import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export function MobileNav() {
  const pathname = usePathname();
  const router = useRouter();
  const [showLogoutDialog, setShowLogoutDialog] = useState(false);
  const [username, setUsername] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedUsername = localStorage.getItem('username');
      console.log('[MobileNav] Username from localStorage:', storedUsername);
      setUsername(storedUsername);
    }
  }, [pathname]);

  const handleLogout = async () => {
    setShowLogoutDialog(false);
    await apiClient.logout();
    router.push('/login');
  };

  const allNavItems = [
    { icon: Home, label: 'ホーム', path: '/dashboard' },
    { icon: Package, label: '納品書', path: '/delivery-notes' },
    { icon: FileText, label: '請求書', path: '/invoices' },
    { icon: ShoppingCart, label: '注文', path: '/customers' },
    { icon: BarChart2, label: '売上', path: '/sales' },
    { icon: Settings, label: 'マスタ', path: '/masters' },
  ];

  // admin以外のユーザーは納品書と請求書のみ表示
  const navItems = username === 'admin' 
    ? allNavItems
    : allNavItems.filter(item => item.path === '/delivery-notes' || item.path === '/invoices');
  
  console.log('[MobileNav] Current username:', username, 'isAdmin:', username === 'admin', 'navItems count:', navItems.length);

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
